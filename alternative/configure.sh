#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
mkdir -p "$TASK_CONFIG_DIR"
chmod 700 "$TASK_CONFIG_DIR"
cat <<'HELP'
Utwórz remote o nazwie tbdrive, typ Google Drive (drive).
Podaj własny OAuth client_id i client_secret (Desktop app).
Instrukcja: https://rclone.org/drive/#making-your-own-client-id
Wybierz scope drive.file (tylko pliki utworzone przez tę aplikację).
Nie wybieraj pełnego scope drive. Pozostaw service_account_file puste.
Shared Drive: nie. Nie ustawiaj root_folder_id ani zaawansowanych opcji.
Autoryzuj konto w przeglądarce. Nie wklejaj tokenów do czatu.
Konfiguracja jest osobna od istniejącej konfiguracji rclone.
HELP
drive_cli config
if [[ -f "$TASK_CONFIG" ]]; then chmod 600 "$TASK_CONFIG"; fi
drive_cli listremotes | /usr/bin/grep -qx 'tbdrive:' || { echo 'Nie utworzono tbdrive.' >&2; exit 1; }
check_remote
echo 'Konfiguracja zapisana. Przesyłanie: upload.sh --public /pełna/ścieżka/do/pliku'
