#!/usr/bin/env python3
"""Bounded native messaging bridge. No tokens or arbitrary local paths in protocol."""
import base64
import configparser
import json
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import uuid

MAX_MESSAGE = 512 * 1024
MAX_CHUNK = 256 * 1024
MAX_FILE = 5 * 1024**3


class UserError(Exception):
    pass


def read_exact(stream, size):
    data = bytearray()
    while len(data) < size:
        part = stream.read(size - len(data))
        if not part:
            if not data:
                return None
            raise UserError("Niepełna wiadomość lokalna.")
        data.extend(part)
    return bytes(data)


def read_message(stream):
    header = read_exact(stream, 4)
    if header is None:
        return None
    length = struct.unpack("=I", header)[0]
    if length > MAX_MESSAGE or length == 0:
        raise UserError("Nieprawidłowy rozmiar wiadomości.")
    payload = read_exact(stream, length)
    if payload is None:
        raise UserError("Niepełna wiadomość lokalna.")
    message = json.loads(payload)
    if not isinstance(message, dict):
        raise UserError("Nieprawidłowa wiadomość.")
    return message


def write_message(stream, message):
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    stream.write(struct.pack("=I", len(payload)) + payload)
    stream.flush()


def safe_name(name):
    if not isinstance(name, str) or not name or len(name.encode("utf-8")) > 240:
        raise UserError("Nieprawidłowa nazwa pliku.")
    if name in (".", "..") or any(ch in name for ch in ("/", "\\")) or any(ord(ch) < 32 for ch in name):
        raise UserError("Nazwa pliku zawiera niedozwolone znaki.")
    return name


class Bridge:
    def __init__(self, settings):
        self.settings = settings
        self.temp = None
        self.handle = None
        self.process = None
        self.expected = self.received = 0
        self.name = None
        # Prevent inherited environment from overriding the dedicated remote.
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("RCLONE_")}

    def run(self, arguments, timeout=1800):
        self.process = subprocess.Popen(
            [self.settings["rclone"], "--config", self.settings["config"], *arguments],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=self.env, start_new_session=True)
        try:
            output, _ = self.process.communicate(timeout=timeout)
            if self.process.returncode:
                raise UserError("Operacja rclone nie powiodła się. Sprawdź zgodę Google, sieć, miejsce i politykę udostępniania.")
            return output.decode("utf-8").strip()
        except subprocess.TimeoutExpired:
            self.stop_process()
            raise UserError("Przekroczono czas operacji rclone.") from None
        except BaseException:
            self.stop_process()
            raise
        finally:
            self.process = None

    def configured(self):
        path = Path(self.settings["config"])
        if not path.is_file():
            return False
        if path.stat().st_mode & 0o077:
            raise UserError("Konfiguracja rclone wymaga uprawnień 0600.")
        c = configparser.ConfigParser(interpolation=None)
        c.read_string(self.run(["config", "redacted", "tbdrive"], timeout=30))
        if not c.has_section("tbdrive"):
            return False
        remote = c["tbdrive"]
        # No shared drive, existing parent, alternate credentials or permission presets.
        forbidden = ("root_folder_id", "team_drive", "service_account_file", "service_account_credentials", "impersonate", "metadata", "metadata_mapper")
        token = remote.get("token", "")
        return (remote.get("type") == "drive" and remote.get("scope") == "drive.file"
                and bool(remote.get("client_id")) and bool(token)
                and not any(remote.get(key) for key in forbidden))

    def dispatch(self, message):
        action = message.get("action")
        if action == "status":
            ready = self.configured()
            return {"configured": ready, "message": "Uruchom konfigurację OAuth: tbdrive, drive.file, własny client_id, bez Shared Drive i root_folder_id."}
        if action == "reauthorize":
            if not self.configured():
                raise UserError("Najpierw utwórz konfigurację OAuth.")
            command = Path(__file__).resolve().parent / "reauthorize.command"
            subprocess.run(["/usr/bin/open", "-a", "Terminal", str(command)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            return {"opened": True}
        if action == "start":
            if self.temp is not None:
                raise UserError("Przesyłanie jest już rozpoczęte.")
            if message.get("public") is not True:
                raise UserError("Wymagana jawna zgoda na publiczny link.")
            if not self.configured():
                raise UserError("Najpierw skonfiguruj Google Drive.")
            size = message.get("size")
            if type(size) is not int or not 0 <= size <= MAX_FILE:
                raise UserError("Maksymalny rozmiar pliku to 5 GiB.")
            self.name = safe_name(message.get("name"))
            if shutil.disk_usage(tempfile.gettempdir()).free < size + 100 * 1024**2:
                raise UserError("Brak miejsca na tymczasową kopię pliku.")
            self.expected = size
            self.temp = tempfile.TemporaryDirectory(prefix="tb-drive-filelink-")
            self.handle = open(Path(self.temp.name) / "payload", "wb")
            os.chmod(self.handle.name, 0o600)
            return {}
        if action == "chunk":
            if self.handle is None:
                raise UserError("Nie rozpoczęto przesyłania.")
            try:
                data = base64.b64decode(message.get("data", ""), validate=True)
            except (ValueError, TypeError):
                raise UserError("Nieprawidłowy blok danych.") from None
            if len(data) > MAX_CHUNK or self.received + len(data) > self.expected:
                raise UserError("Przekroczony rozmiar danych.")
            self.handle.write(data)
            self.received += len(data)
            return {}
        if action == "finish":
            if self.handle is None or self.received != self.expected:
                raise UserError("Rozmiar pliku nie zgadza się z deklaracją.")
            self.handle.close()
            self.handle = None
            remote = f"tbdrive:Thunderbird-Filelink/{uuid.uuid4()}/{self.name}"
            local = str(Path(self.temp.name) / "payload")
            common = ["--drive-scope", "drive.file", "--drive-shared-with-me=false", "--drive-skip-shortcuts", "--drive-metadata-permissions", "off"]
            self.run(["copyto", local, remote, "--immutable", *common])
            url = self.run(["link", remote, *common], timeout=120)
            if not re.fullmatch(r"https://drive\.google\.com/(?:open\?id=[A-Za-z0-9_-]+|file/d/[A-Za-z0-9_-]+/view(?:\?[^\s]*)?)", url):
                raise UserError("Nieoczekiwany link Google Drive.")
            self.cleanup()
            return {"url": url}
        raise UserError("Nieobsługiwana operacja.")

    def stop_process(self):
        if self.process and self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()

    def cleanup(self):
        self.stop_process()
        if self.handle:
            self.handle.close()
            self.handle = None
        if self.temp:
            self.temp.cleanup()
            self.temp = None
        self.received = self.expected = 0


def main():
    os.umask(0o077)
    settings_path = Path(__file__).resolve().parent / "runtime.json"
    bridge = Bridge(json.loads(settings_path.read_text()))
    def terminate(_signum, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        while True:
            message = read_message(sys.stdin.buffer)
            if message is None:
                break
            try:
                result = bridge.dispatch(message)
                write_message(sys.stdout.buffer, {"id": message.get("id"), "ok": True, **result})
            except (UserError, OSError, ValueError, configparser.Error, subprocess.SubprocessError):
                bridge.cleanup()
                # Do not forward exceptions, command output or credentials to Thunderbird.
                write_message(sys.stdout.buffer, {"id": message.get("id"), "ok": False,
                    "error": "Lokalna operacja nie powiodła się. Sprawdź instalację, konfigurację OAuth, nazwę pliku i połączenie Google."})
    finally:
        bridge.cleanup()


if __name__ == "__main__":
    main()
