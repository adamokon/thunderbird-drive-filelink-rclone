#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import shutil
home = Path.home()
install = home / '.local/share/thunderbird-drive-filelink'
for name in ('tb-drive-configure', 'tb-drive-upload'):
    target = home / '.local/bin' / name
    if target.is_symlink() and target.resolve().is_relative_to(install):
        target.unlink()
manifest = home / 'Library/Mozilla/NativeMessagingHosts/org.thunderbird.drive_filelink_rclone.json'
manifest.unlink(missing_ok=True)
if install.exists():
    shutil.rmtree(install)
print('Usunięto pomocnik. Usuń dodatek w Thunderbird. Zachowano konfigurację OAuth i pliki w Drive.')
PY
