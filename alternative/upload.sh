#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/common.sh"
if [[ $# -ne 2 || "$1" != '--public' ]]; then
  echo 'Użycie: upload.sh --public /ścieżka/do/pliku' >&2
  echo 'Przesyła plik i udostępnia każdemu posiadającemu link; bez hasła i wygaśnięcia.' >&2
  exit 2
fi
[[ -f "$TASK_CONFIG" ]] || { echo 'Najpierw uruchom configure.sh.' >&2; exit 1; }
[[ -f "$2" && -r "$2" ]] || { echo 'Plik nie istnieje lub nie jest czytelny.' >&2; exit 1; }
check_remote
task_file="$2"
[[ "$task_file" = /* ]] || task_file="$PWD/$task_file"
task_uuid=$(uuidgen | tr '[:upper:]' '[:lower:]')
task_remote="tbdrive:Thunderbird-Filelink/$task_uuid/$(basename "$task_file")"
echo 'Przesyłanie do Google Drive; powstanie link dostępny dla każdego, kto go posiada.' >&2
drive_cli copyto "$task_file" "$task_remote" --immutable --drive-scope drive.file --drive-metadata-permissions off --drive-skip-shortcuts
echo "Ścieżka przesłanego pliku: $task_remote" >&2
if ! task_link=$(drive_cli link "$task_remote" --drive-scope drive.file); then
  echo 'Plik przesłano, ale tworzenie linku nie powiodło się. Sprawdź uprawnienia w Drive.' >&2
  exit 1
fi
case "$task_link" in
  https://drive.google.com/*) ;;
  *) echo 'Nieoczekiwany format linku; sprawdź udostępnienie w Drive.' >&2; exit 1 ;;
esac
printf '%s\n' "$task_link"
echo 'Cofnięcie dostępu: Google Drive → Udostępnij → Dostęp ogólny → Ograniczony.' >&2
if command -v pbcopy >/dev/null; then
  printf '%s' "$task_link" | pbcopy
  echo 'Link skopiowano do schowka. Wklej go do wiadomości w Thunderbird.' >&2
fi
