# Konfiguracja Google Drive

Nie umieszczaj danych konta, OAuth client secret ani tokenów w GitHub, zgłoszeniach
błędów, czacie lub zrzutach ekranu. Projekt nie potrzebuje hasła do Twojego konta.

## Pierwsze połączenie

1. W [Google Cloud Console](https://console.cloud.google.com/) utwórz osobny projekt
   dla tego narzędzia i włącz **Google Drive API**.
2. W **Google Auth Platform** skonfiguruj nazwę aplikacji i adres kontaktowy.
   W sekcji Audience wybierz właściwą grupę użytkowników. Dla prywatnego konta
   jest to zwykle External; podczas testów dodaj własne konto jako test user.
3. W Data Access zadeklaruj tylko zakres
   `https://www.googleapis.com/auth/drive.file` — nie pełny `drive`.
4. W Clients utwórz **OAuth client ID → Desktop app**.
   Zachowaj client ID i client secret lokalnie, poza katalogiem projektu.
   Nie używaj service account ani delegacji domenowej.
5. Uruchom:

   ```bash
   ~/.local/bin/tb-drive-configure
   ```

6. W rclone utwórz nowy remote o nazwie **tbdrive**, typ **drive**.
   Podaj własny client ID i client secret w interaktywnym formularzu Terminala.
   Wybierz **drive.file**. Pozostaw service account puste, Shared Drive: **nie**.
   Nie ustawiaj istniejącego `root_folder_id` ani innych niestandardowych opcji.
7. Wybierz logowanie przez przeglądarkę, zaloguj się na właściwe konto Google
   i sprawdź zakres zgody. rclone zapisze token w osobnej lokalnej konfiguracji.
8. Zakończ konfigurację, pozostawiając remote zapisany. Następnie skonfiguruj
   usługę Google Drive (rclone) w ustawieniach Filelink Thunderbirda.

Konfiguracja jest zapisywana w `~/.config/thunderbird-drive-cli/rclone.conf`
(lub pod `XDG_CONFIG_HOME` ustawionym podczas instalacji). Katalog ma prawa
`0700`, plik `0600`. Jest poza repozytorium.

## Czy wystarczy jednorazowo?

Zwykle tak: rclone używa refresh token do odnawiania krótkotrwałych access tokenów.
Ponowne logowanie może być potrzebne po cofnięciu zgody, długiej nieaktywności,
przekroczeniu limitów tokenów albo zmianie zasad administratora.

**External + Testing:** Google zwykle wydaje dla zakresu Drive refresh token
ważny tylko 7 dni. Dla trwałego osobistego użytku przełącz status aplikacji OAuth
na **In production**, zgodnie z wymaganiami Google. To zmiana statusu klienta
OAuth; nie oznacza publikacji Twoich plików ani kodu na GitHub. Wymogi weryfikacji
zależą od rodzaju aplikacji, zakresów i sposobu dystrybucji.

Po przełączeniu na **In production** wykonaj ponowne logowanie, aby otrzymać nowy
token zamiast polegać na tokenie wydanym podczas Testing.

W panelu Filelink kliknij **Ponownie zaloguj do Google Drive**. Pomocnik otworzy
Terminal z `rclone config reconnect tbdrive:`. Logowanie odbywa się w przeglądarce.
Po zakończeniu kliknij **Sprawdź połączenie**. Nie zmieniaj `drive.file` na `drive`.

Jeśli wcześniej nadałeś temu samemu klientowi szersze uprawnienia, sama zmiana
tekstu scope w pliku ich nie odbiera. Cofnij starą zgodę w koncie Google i
autoryzuj ponownie; najlepiej użyj osobnego klienta dla tego projektu.

## Co zobaczy odbiorca?

Odbiorca otrzyma URL konkretnego pliku i będzie mógł go otworzyć bez konta Google.
Publiczne uprawnienie jest nadawane plikowi, nie folderowi i nie całemu Drive.
Treść pliku, jego nazwa oraz metadane pokazywane przez Google mogą być widoczne
posiadaczowi linku. Każdy, komu przekazano link, również może go użyć.

Źródła: [rclone konfiguracja Drive](https://rclone.org/drive/#making-your-own-client-id),
[Google drive.file](https://developers.google.com/workspace/drive/api/guides/api-specific-auth),
[Google refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration).
