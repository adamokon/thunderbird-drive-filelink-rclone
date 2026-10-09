# Security policy

Wersja 0.1.x jest wczesną wersją projektu; brak gwarancji niezależnego audytu.
Poprawki bezpieczeństwa trafiają na gałąź main. Nie używaj publicznych linków
do danych wymagających uwierzytelnienia odbiorców.

Zgłoszenia luk należy przesyłać prywatnie przez GitHub **Security → Report a vulnerability**,
jeśli funkcja jest dostępna. Jeżeli nie jest, otwórz zgłoszenie proszące o prywatny
kanał kontaktu, bez szczegółów umożliwiających wykorzystanie luki.

Nie dołączaj tokenów, rclone.conf, client secret, treści prywatnych plików,
rzeczywistych linków udostępniania ani eksportu profilu Thunderbird.
Podaj wersję programu i syntetyczne kroki odtworzenia błędu.

W modelu zagrożeń ufamy lokalnemu systemowi, Pythonowi, zainstalowanej binarce
rclone oraz Google. Kod repozytorium nie zawiera danych uwierzytelniających.
Złośliwy proces uruchomiony jako ten sam użytkownik może odczytać konfigurację
i przechwycić dane; prawa plików nie chronią przed takim procesem.

Repozytorium wyklucza konfiguracje OAuth i lokalne dane. Przed publikacją działa
kontrola wybranych plików Git. Automatyczny skan nie zastępuje przeglądu zmian.
