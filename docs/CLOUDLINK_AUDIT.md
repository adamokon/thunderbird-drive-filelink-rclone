# Audyt oryginalnego CloudLink

Data: 2026-10-09. Pakiet najnowszej wersji wskazanej przez API ATN: **1.0**,
file ID **1037830**, 14960 bajtów.

SHA-256: `a893d1fad512940f83ceb91af1c179ec3615c62b5cfe5e0ffd8fc9324855e427`.
Lokalna suma jest zgodna z aktualnym API katalogu. XPI nie instalowano.

- Manifest V2: `permissions: ["compose"]`; bez host permissions i dostępów do hostów.
- Dwa krótkie pliki JS; brak fetch, XMLHttpRequest, WebSocket, OAuth2 i tokenów.
- Brak zaciemnienia kodu, dynamicznego ładowania kodu lub zdalnych skryptów.
- Implementacja tylko wstawia ręcznie podany link do wiadomości; brak uploadu
  do Drive i brak providera cloudFile.
- Hasło jest wpisywane jawnie do wiadomości, data wygaśnięcia jest tekstem.
- Link i hasło są interpolowane w HTML bez escapowania (`compose_action.js:11–18`).
  Pozwala to wstawić obcy markup. Skutek zależy od sanitizacji i ustawień klienta.

Wniosek: brak oznak malware w statycznie przejrzanym pakiecie, lecz brak podstaw
do rekomendacji jako uploader Google Drive Filelink. Nie jest to audyt dynamiczny,
certyfikacja ani ocena późniejszych wersji. Nowy projekt nie kopiuje jego kodu.

Powtarzalne inventory: `python3 audit/scan.py /ścieżka/do/pakietu.xpi`.
Regex scan wymaga ręcznego przeglądu kodu, nie dowodzi samodzielnie bezpieczeństwa.
Surowy pakiet, źródła i raport z lokalnymi ścieżkami nie są publikowane.

Źródła: [ATN](https://addons.thunderbird.net/pl/thunderbird/addon/thunderbird-cloudlink/),
[API ATN](https://addons.thunderbird.net/api/v4/addons/addon/thunderbird-cloudlink/),
[repozytorium autora](https://github.com/BialySztorm/Thunderbird-CloudLink).
