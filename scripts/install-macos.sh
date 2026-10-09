#!/usr/bin/env bash
set -euo pipefail
umask 077
[[ "$(uname -s)" = Darwin ]] || { echo 'Ten instalator obsługuje macOS.' >&2; exit 1; }
task_root=$(cd "$(dirname "$0")/.." && pwd)
task_python=$(command -v python3)
task_rclone=$(command -v rclone)
[[ -n "$task_python" && -n "$task_rclone" ]] || { echo 'Wymagane python3 i rclone.' >&2; exit 1; }
"$task_python" "$task_root/scripts/build.py"
"$task_python" - "$task_root" "$task_python" "$task_rclone" <<'PY'
import json, os, shlex, shutil, sys
from pathlib import Path
root, python, rclone = map(Path, sys.argv[1:])
home = Path.home()
install = home / '.local/share/thunderbird-drive-filelink'
install.mkdir(parents=True, exist_ok=True, mode=0o700)
install.chmod(0o700)
shutil.copy2(root / 'native/host.py', install / 'host.py')
cli = install / 'cli'
cli.mkdir(exist_ok=True, mode=0o700)
for source in (root / 'alternative').glob('*.sh'):
    shutil.copy2(source, cli / source.name)
    (cli / source.name).chmod(0o700)
config = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config'))) / 'thunderbird-drive-cli/rclone.conf'
(install / 'runtime.json').write_text(json.dumps({'rclone': str(rclone.resolve()), 'config': str(config)}, indent=2) + '\n')
(install / 'runtime.json').chmod(0o600)
launcher = install / 'launch-host.sh'
launcher.write_text('#!/bin/sh\nexec ' + shlex.quote(str(python.resolve())) + ' ' + shlex.quote(str(install / 'host.py')) + '\n')
launcher.chmod(0o700)
reconnect = install / 'reauthorize.command'
reconnect.write_text('#!/bin/bash\nset -euo pipefail\numask 077\n' +
    shlex.quote(str(rclone.resolve())) + ' --config ' + shlex.quote(str(config)) +
    ' config reconnect tbdrive: --drive-scope drive.file\n' +
    'chmod 600 ' + shlex.quote(str(config)) + '\n' +
    'echo "Logowanie zakończone. W dodatku kliknij Sprawdź połączenie."\n')
reconnect.chmod(0o700)
hosts = home / 'Library/Mozilla/NativeMessagingHosts'
hosts.mkdir(parents=True, exist_ok=True, mode=0o700)
manifest = {'name': 'org.thunderbird.drive_filelink_rclone', 'description': 'Local rclone Google Drive Filelink bridge',
            'path': str(launcher), 'type': 'stdio', 'allowed_extensions': ['drive-filelink-rclone@local.invalid']}
target = hosts / 'org.thunderbird.drive_filelink_rclone.json'
target.write_text(json.dumps(manifest, indent=2) + '\n')
target.chmod(0o600)
binary = home / '.local/bin'
binary.mkdir(parents=True, exist_ok=True)
for name, script in [('tb-drive-configure', 'configure.sh'), ('tb-drive-upload', 'upload.sh')]:
    dest = binary / name
    if dest.exists() or dest.is_symlink():
        owned_link = dest.is_symlink() and dest.resolve() == (cli / script).resolve()
        owned_wrapper = not dest.is_symlink() and dest.is_file() and '# Managed by thunderbird-drive-filelink' in dest.read_text()
        if not owned_link and not owned_wrapper:
            raise SystemExit(f'Refusing to replace existing command: {name}')
        dest.unlink()
    dest.write_text('#!/bin/sh\n# Managed by thunderbird-drive-filelink\nexec ' + shlex.quote(str(cli / script)) + ' "$@"\n')
    dest.chmod(0o700)
print('Zainstalowano lokalny pomocnik i komendy tb-drive-configure / tb-drive-upload.')
print('XPI: ' + str(next((root / 'dist').glob('*.xpi'))))
PY
