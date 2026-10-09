# Drive Filelink via rclone

Dodatek Thunderbird przesyłający załączniki do Google Drive przez lokalny rclone.
Thunderbird automatycznie wstawia link do pliku w treści e-maila.

**Status: wersja 0.1.0, wczesna wersja dla macOS.** Testy używają danych syntetycznych
i atrap rclone. Pełny test z Google Drive wymaga konfiguracji własnego konta OAuth.
Projekt nie jest powiązany z Google ani zespołem Thunderbird.

## Jak działa

1. W Thunderbird wybierasz załącznik i przekształcasz go w Filelink.
2. Dodatek przekazuje dane blokami do lokalnego pomocnika Native Messaging.
3. rclone zapisuje plik w nowym katalogu `Thunderbird-Filelink/<UUID>/` na Drive.
4. Dla **tego jednego pliku** tworzy uprawnienie do odczytu dla każdego posiadającego link.
5. Thunderbird wstawia otrzymany URL do treści wiadomości. Odbiorca nie musi się logować.

Pozostałe pliki i katalogi Drive nie są udostępniane. Folder nadrzędny nie jest
udostępniany publicznie. Wymagany zakres OAuth `drive.file` ogranicza aplikację do
utworzonych przez nią plików oraz plików jawnie udostępnionych tej aplikacji.

Publiczny link nie ma hasła ani automatycznej daty wygaśnięcia. Nie służy do
udostępniania plików wymagających kontroli tożsamości odbiorcy. Konto organizacji
może blokować udostępnianie publiczne.

## Instalacja na macOS

Wymagania: Thunderbird 128+, Python 3.10+, rclone, wolne miejsce na tymczasową
kopię pliku. Maksymalny rozmiar załącznika: 5 GiB. Node.js jest potrzebny tylko do testów.

```bash
bash scripts/test.sh
bash scripts/install-macos.sh
```

W Thunderbird otwórz **Dodatki i motywy → koło zębate → Zainstaluj dodatek z pliku**
i wybierz `dist/drive-filelink-rclone-0.1.0.xpi`. To lokalny pakiet, bez recenzji ATN.

Następnie wykonaj [konfigurację Google OAuth](docs/GOOGLE_AUTH.md).
W **Ustawienia → Tworzenie → Załączniki → Dodaj usługę Filelink** wybierz
**Google Drive (rclone)**. Sprawdź konfigurację, zaznacz zgodę na udostępnianie
wybranych plików osobom posiadającym link i kliknij **Zapisz**.

W oknie wiadomości dodaj załącznik, następnie wybierz dla niego **Przekształć w →
Google Drive (rclone)**. Nie trzeba ręcznie kopiować linku.

## Logowanie i ponowne logowanie

Hasło konta podajesz wyłącznie na stronie Google w przeglądarce.
rclone przechowuje lokalnie token odświeżający i zwykle sam odnawia dostęp.
W ustawieniach konta Filelink znajduje się przycisk **Ponownie zaloguj do Google Drive**:
otwiera Terminal, uruchamia OAuth rclone i logowanie w przeglądarce.
Po zakończeniu kliknij **Sprawdź połączenie**. Sprawdzenie w panelu weryfikuje
lokalną konfigurację; dopiero upload sprawdza ważność zgody i łączność z Google.

## Prywatność i bezpieczeństwo

- Tokeny i klient OAuth znajdują się poza repozytorium, w osobnej konfiguracji rclone.
- Dodatek otrzymuje URL pliku; nie otrzymuje tokenów OAuth ani hasła.
- Uprawnienia dodatku: `nativeMessaging`, `storage`; bez host permissions,
  dostępu do skrzynki, treści wiadomości ani `compose.send`.
- Native Messaging zezwala wyłącznie na identyfikator tego dodatku. Protokół
  nie przyjmuje ścieżek do lokalnych plików ani dowolnych komend.
- Nie ma telemetrii ani serwera pośredniczącego. Dane pliku obsługują lokalny
  pomocnik, rclone oraz Google Drive.
- Tokeny są w pliku z prawami `0600`, katalog konfiguracji ma `0700`. To ochrona
  systemowymi uprawnieniami, a nie szyfrowany sejf. Procesy Twojego użytkownika
  mogą mieć dostęp do tego pliku.
- Bloki pliku są kodowane base64 dla lokalnego protokołu. Nie jest to szyfrowanie
  ani obfuscation. HTTPS do Google obsługuje rclone.

Szczegóły: [SECURITY.md](SECURITY.md) i [architektura](docs/ARCHITECTURE.md).

## Cofnięcie udostępnienia i przechowywanie

W Google Drive: **Udostępnij → Dostęp ogólny → Ograniczony**. Sprawdź także
inne nadane lub odziedziczone uprawnienia. Cofnięcie dostępu nie usuwa kopii
już pobranych przez odbiorców.

Usunięcie załącznika albo konta Filelink w Thunderbird **nie usuwa** pliku z
Drive — link mógł już zostać wysłany. Nie ma automatycznego sprzątania chmury.
Przerwany upload może pozostawić plik w Drive. Błąd tworzenia linku po uploadzie
również może pozostawić plik; sprawdź katalog `Thunderbird-Filelink`.
W rclone 1.75.0 backend Drive ignoruje `link --unlink` i `--expire`.

## Wariant CLI

Instalator udostępnia też polecenia:

```bash
~/.local/bin/tb-drive-configure
~/.local/bin/tb-drive-upload --public "/pełna/ścieżka/do/pliku.pdf"
```

Druga komenda drukuje URL i kopiuje go do schowka macOS. Można wkleić go do dowolnej wiadomości.

## Odinstalowanie

Usuń dodatek w Thunderbird i uruchom `bash scripts/uninstall-macos.sh`.
Konfiguracja OAuth oraz pliki w Drive pozostają. Zgodę Google możesz cofnąć w
ustawieniach bezpieczeństwa konta Google.

## Rozwój

`bash scripts/test.sh` uruchamia testy protokołu, kontroli dostępu i przesyłania
bloków oraz buduje powtarzalny XPI. Budowanie nie korzysta z danych użytkownika.
Zmiany: [CHANGELOG.md](CHANGELOG.md). Wkład: [CONTRIBUTING.md](CONTRIBUTING.md).
Kod nowego projektu jest na licencji MIT. Badany dodatek CloudLink nie jest
dołączany ani instalowany. [Podsumowanie jego audytu](docs/CLOUDLINK_AUDIT.md).

## Źródła

- [Thunderbird cloudFile API](https://webextension-api.thunderbird.net/en/mv2/cloudFile.html)
- [Thunderbird Native Messaging](https://developer.thunderbird.net/add-ons/mailextensions/supported-webextension-api)
- [rclone Google Drive](https://rclone.org/drive/)
- [Google: zakresy OAuth Drive](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- [Google: ważność tokenów odświeżających](https://developers.google.com/identity/protocols/oauth2#expiration)
