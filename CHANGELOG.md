# Changelog

## Dokumentacja — 2026-10-21

- Potwierdzono rzeczywisty upload do Drive, dostarczenie e-maila do tego samego konta,
  anonimowe pobranie identycznego pliku oraz prywatne uprawnienia folderów nadrzędnych.
- Dodano zasady przetwarzania danych i opis ograniczeń weryfikacji.
- Potwierdzono przejście OAuth na In production, ponowną autoryzację z zakresem
  drive.file oraz poprawny dostęp do pliku testowego po wymianie tokenu.
- Doprecyzowano, że Node.js jest potrzebny tylko do opcjonalnych testów.

## 0.1.0 — 2026-10-09

- Provider Thunderbird Filelink dla Google Drive poprzez lokalny rclone.
- Przesyłanie blokami, ograniczony protokół Native Messaging i scope drive.file.
- Jawna zgoda na publiczne linki i ponowne logowanie z panelu dodatku.
- Instalator macOS, wariant CLI, testy, dokumentacja i podsumowanie audytu CloudLink.
