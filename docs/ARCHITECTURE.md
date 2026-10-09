# Architektura i granice zaufania

Thunderbird cloudFile → Native Messaging → pomocnik Python → rclone → Google Drive.

Każdy upload ma osobne połączenie lokalne. Wiadomości JSON mają nagłówek długości
zgodny z protokołem Mozilla. Dodatek przekazuje dane po 256 KiB z oczekiwaniem
na potwierdzenie. Cały plik nie jest kodowany jednocześnie w pamięci dodatku.
Pomocnik buforuje go w prywatnym katalogu tymczasowym, kontroluje wielkość,
nazwę oraz zgodność otrzymanej liczby bajtów i uruchamia rclone bez powłoki.

Pomocnik przyjmuje wyłącznie `status`, `start`, `chunk`, `finish`, `reauthorize`.
Nie przyjmuje dowolnych ścieżek lokalnych, poleceń rclone, adresów sieciowych ani
tokenów. Polecenia rclone mają stałą konfigurację i remote. Zmienne środowiskowe
`RCLONE_*` nie mogą podmienić konfiguracji w pomocniku.

Świeży zakres `drive.file`, nowy katalog UUID oraz brak root_folder_id/Shared Drive
oddzielają upload od istniejących katalogów użytkownika. Pomocnik nie udostępnia
folderu nadrzędnego. rclone tworzy dla pliku uprawnienie `reader` typu `anyone`.

Anulowanie rozłącza port i zatrzymuje lokalny proces. Katalog tymczasowy jest
sprzątany przy zakończeniu, EOF oraz obsługiwanych sygnałach. Wymuszone zabicie
procesu/systemu może pozostawić lokalny plik tymczasowy. Przerwanie operacji
sieciowej może pozostawić już przesłany plik/publiczne uprawnienie w chmurze.
Nie ma automatycznego kasowania chmury, ponieważ link mógł zostać wykorzystany.

Ponowne logowanie otwiera stały, lokalny skrypt `.command` w Terminalu. rclone
obsługuje OAuth; pomocnik i dodatek nie parsują tokenów. Status używa redacted
config, nie zwraca treści konfiguracji do dodatku i nie dowodzi ważności tokenu.

Native Messaging na macOS Thunderbird szuka manifestu w
`~/Library/Mozilla/NativeMessagingHosts/`. Instalator zapisuje tam manifest
z `allowed_extensions` ograniczonym do identyfikatora tego dodatku.
Nie modyfikuje ustawień ochrony Thunderbirda ani certyfikatów TLS.
