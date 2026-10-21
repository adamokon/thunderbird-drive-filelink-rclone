# Zweryfikowany test działania

Data: **2026-10-21**. Środowisko: macOS na Apple Silicon, Thunderbird 157.0.1,
rclone 1.75.0, dodatek 0.1.0. Test wykorzystał prawdziwe konto Google z osobnym
klientem OAuth typu Desktop app oraz zakresem `drive.file`.

## Sprawdzony przebieg

1. Zainstalowany pomocnik Native Messaging potwierdził poprawną konfigurację OAuth.
2. W ustawieniach Filelink dodano usługę Google Drive (rclone), sprawdzono konfigurację
   i zapisano zgodę na publiczne linki do wybranych plików.
3. W Thunderbird utworzono wiadomość z konta testującego do tego samego konta.
   Dodano plik tekstowy **158 bajtów**, zawierający wyłącznie sztuczne dane testowe.
4. Z menu załącznika wybrano **Przekształć… → Google Drive (rclone)**.
5. Dodatek przesłał plik i otrzymał link Google Drive. Thunderbird automatycznie
   wstawił ten link do treści wiadomości, także przy redagowaniu zwykłego tekstu.
6. Wiadomość wysłano z Thunderbirda. W Gmailu potwierdzono jej obecność w Odebranych,
   właściwego nadawcę i treść zawierającą ten sam link.
7. Plik pobrano anonimowo, bez tokenu OAuth i bez cookies. Zawartość była identyczna
   bajtowo z oryginałem. Suma MD5 zwrócona przez API Drive również była zgodna.
8. API Drive potwierdziło `anyone / reader` dla pliku. Zarówno folder UUID zawierający
   plik, jak i nadrzędny folder aplikacji nie miały uprawnień `anyone` ani `domain`.

Wiadomość może zawierać mały załącznik HTML będący reprezentacją odnośnika Filelink
utworzoną przez Thunderbird. Nie jest to kopia przesłanego pliku.

## Co ten wynik potwierdza

Integracja z Thunderbirdem, rzeczywisty upload OAuth, wygenerowanie publicznego
linku, dostarczenie e-maila i pobranie przez odbiorcę działały w tym środowisku.
Nadanie uprawnień plikowi nie udostępniło jego folderów nadrzędnych.

Nie sprawdzono jeszcze rzeczywistych uploadów bliskich limitowi 5 GiB, wszystkich
odmian Google Workspace, długoterminowego odświeżania tokenów ani wszystkich wersji
Thunderbirda. Mały plik potwierdza przebieg funkcjonalny, nie wydajność dużych plików.
Anulowanie i błędy są objęte testami automatycznymi z atrapami.

Pierwszy upload przeprowadzono w trybie OAuth **Testing**. Następnie tego samego
dnia przełączono aplikację na **In production** i zakończono ponowną autoryzację.
Po zapisaniu nowego tokenu potwierdzono zakres `drive.file`, dostęp przez API do
pliku testowego oraz gotowość pomocnika Native Messaging. Siedmiodniowy limit
trybu Testing nie dotyczy już tego nowego połączenia. Token nadal może zostać
cofnięty lub wygasnąć z innych przyczyn; patrz [GOOGLE_AUTH.md](GOOGLE_AUTH.md).

Adres konta, rzeczywisty URL pliku, identyfikatory Google Cloud, logi OAuth i zrzuty
ekranu z prywatnego konta celowo pozostawiono poza publicznym repozytorium.
