#!/usr/bin/env bash
set -euo pipefail
umask 077
TASK_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/thunderbird-drive-cli"
TASK_CONFIG="$TASK_CONFIG_DIR/rclone.conf"
command -v rclone >/dev/null || { echo 'Brak rclone. Zainstaluj z https://rclone.org/install/.' >&2; exit 1; }
drive_cli() { rclone --config "$TASK_CONFIG" "$@"; }
check_remote() {
  command -v python3 >/dev/null || { echo 'Brak python3 do sprawdzenia konfiguracji.' >&2; return 1; }
  drive_cli config redacted tbdrive | python3 -c '
import configparser, sys
c = configparser.ConfigParser(interpolation=None)
c.read_string(sys.stdin.read())
ok = (c.has_section("tbdrive") and c.get("tbdrive", "type", fallback="") == "drive"
      and c.get("tbdrive", "scope", fallback="") == "drive.file"
      and bool(c.get("tbdrive", "client_id", fallback=""))
      and bool(c.get("tbdrive", "token", fallback=""))
      and not any(c.get("tbdrive", k, fallback="") for k in
          ("root_folder_id", "team_drive", "service_account_file", "service_account_credentials", "impersonate", "metadata", "metadata_mapper")))
if not ok:
    sys.exit("Wymagany remote tbdrive typu drive, scope drive.file i własny client_id. Uruchom configure.sh.")
'
}
