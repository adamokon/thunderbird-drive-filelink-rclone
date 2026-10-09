import base64
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import subprocess

spec = importlib.util.spec_from_file_location("host", Path(__file__).resolve().parents[1] / "native/host.py")
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        config = self.folder / 'rclone.conf'
        config.write_text('[tbdrive]\ntype = drive\n')
        config.chmod(0o600)
        self.bridge = host.Bridge({'config': str(config), 'rclone': '/unused'})
        self.calls = []
        self.scope = 'drive.file'
        self.extra = ''
        self.link = 'https://drive.google.com/open?id=synthetic_123'
        def fake_run(args, timeout=1800):
            self.calls.append(args)
            if args[:3] == ['config', 'redacted', 'tbdrive']:
                return f'[tbdrive]\ntype = drive\nscope = {self.scope}\nclient_id = XXX\ntoken = XXX\n{self.extra}'
            if args[0] == 'copyto':
                self.assertEqual(Path(args[1]).read_bytes(), b'hello')
                self.assertTrue(args[2].startswith('tbdrive:Thunderbird-Filelink/'))
                self.assertIn('--immutable', args)
            if args[0] == 'link':
                return self.link
            return ''
        self.bridge.run = fake_run

    def tearDown(self):
        self.bridge.cleanup()
        self.temp.cleanup()

    def start(self, **extra):
        return self.bridge.dispatch({'action': 'start', 'name': 'example space.txt', 'size': 5, 'public': True, **extra})

    def test_upload_order_bytes_and_link(self):
        self.start()
        tmp = self.bridge.temp.name
        self.bridge.dispatch({'action': 'chunk', 'data': base64.b64encode(b'hello').decode()})
        result = self.bridge.dispatch({'action': 'finish'})
        self.assertEqual(result['url'], self.link)
        self.assertFalse(Path(tmp).exists())
        self.assertEqual([c[0] for c in self.calls], ['config', 'copyto', 'link'])

    def test_scope_and_existing_parent_rejected(self):
        self.scope = 'drive'
        self.assertFalse(self.bridge.configured())
        self.scope = 'drive.file'
        self.extra = 'root_folder_id = existing-parent\n'
        self.assertFalse(self.bridge.configured())

    def test_permission_file_required(self):
        Path(self.bridge.settings['config']).chmod(0o644)
        with self.assertRaises(host.UserError): self.bridge.configured()

    def test_public_consent_required(self):
        with self.assertRaises(host.UserError): self.start(public=False)

    def test_path_and_size_rejected(self):
        for name in ('../secret', '/etc/passwd', 'a\\b', '..', 'a\x00b'):
            with self.assertRaises(host.UserError): self.start(name=name)
        for size in (-1, host.MAX_FILE + 1, True):
            with self.assertRaises(host.UserError): self.start(size=size)

    def test_chunks_and_incomplete_file_rejected(self):
        self.start()
        with self.assertRaises(host.UserError): self.bridge.dispatch({'action': 'finish'})
        with self.assertRaises(host.UserError): self.bridge.dispatch({'action': 'chunk', 'data': '***'})
        with self.assertRaises(host.UserError): self.bridge.dispatch({'action': 'chunk', 'data': base64.b64encode(b'too long').decode()})

    def test_no_arbitrary_operation(self):
        with self.assertRaises(host.UserError): self.bridge.dispatch({'action': 'delete', 'path': '/etc/passwd'})

    def test_rclone_is_killed_when_host_is_interrupted(self):
        bridge = host.Bridge(self.bridge.settings)
        process = unittest.mock.Mock()
        process.communicate.side_effect = SystemExit(0)
        process.poll.return_value = None
        process.pid = 99999
        with patch.object(host.subprocess, 'Popen', return_value=process), patch.object(host.os, 'killpg') as kill:
            with self.assertRaises(SystemExit): bridge.run(['copyto', 'synthetic', 'tbdrive:synthetic'])
            kill.assert_called_once_with(99999, host.signal.SIGTERM)
            self.assertIsNone(bridge.process)

    def test_protocol_subprocess_no_tokens_in_status(self):
        helper = self.folder / 'host.py'
        helper.write_text(Path(host.__file__).read_text())
        mock = self.folder / 'mock-rclone'
        mock.write_text('#!/bin/sh\nprintf "[tbdrive]\\ntype = drive\\nscope = drive.file\\nclient_id = XXX\\ntoken = XXX\\n"\n')
        mock.chmod(0o700)
        (self.folder / 'runtime.json').write_text(json.dumps({'config': self.bridge.settings['config'], 'rclone': str(mock)}))
        payload = io.BytesIO()
        host.write_message(payload, {'id': 7, 'action': 'status'})
        result = subprocess.run([host.sys.executable, str(helper)], input=payload.getvalue(), capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        response = host.read_message(io.BytesIO(result.stdout))
        self.assertTrue(response['configured'])
        self.assertNotIn(b'XXX', result.stdout)

    def test_untrusted_link_rejected(self):
        self.start()
        self.bridge.dispatch({'action': 'chunk', 'data': base64.b64encode(b'hello').decode()})
        self.link = 'https://evil.invalid/?token=synthetic'
        with self.assertRaises(host.UserError): self.bridge.dispatch({'action': 'finish'})

    def test_protocol_framing_and_limits(self):
        output = io.BytesIO()
        host.write_message(output, {'id': 1, 'ok': True, 'name': 'zażółć'})
        output.seek(0)
        self.assertEqual(host.read_message(output)['name'], 'zażółć')
        self.assertIsNone(host.read_message(output))
        for payload in (struct.pack('=I', host.MAX_MESSAGE + 1), b'\x01', struct.pack('=I', 5) + b'{}'):
            with self.assertRaises(host.UserError): host.read_message(io.BytesIO(payload))


if __name__ == '__main__':
    unittest.main()
