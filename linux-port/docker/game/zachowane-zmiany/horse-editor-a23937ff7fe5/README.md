# Seban — edytor konia, przygotowana wersja 2

Baza przeglądu: commit 345b76fcb07804b2f6d54a5d5cf9bf1eeacf4103.
STATUS: lokalnie sprawdzone komponenty i instalator źródeł. Brak wdrożenia na VPS,
pełnej kompilacji/linkowania silnika i testu w grze. Nie instaluj jako potwierdzonej
wersji produkcyjnej. Najpierw uruchom kontrolę zgodności na aktualnych źródłach.

## Jeden plik Python
`seban-edytor-instalator.py` zawiera kompletny pakiet; nie pobiera kodu z sieci.
Python 3.9+, bez dodatkowych bibliotek do samej kontroli/instalacji źródeł.

Kontrola bez zapisu źródeł:

    python3 /root/seban-edytor-instalator.py --check

Dokładny diff aktualnej instalacji:

    python3 /root/seban-edytor-instalator.py --check --diff /root/seban-kon.diff

Zapis wyłącznie sprawdzonych źródeł, dopiero po przeglądzie wyniku:

    python3 /root/seban-edytor-instalator.py --apply

Instalator sprawdza wszystkie miejsca integracji przed pierwszym zapisem, zachowuje
zmiany poza zakresem hooków, zapisuje małe kopie zmienianych plików i dziennik.
Ponowne uruchomienie identycznego pakietu nie dubluje hooków. Obcy plik o nazwie
modułu, inny blok konia lub nowsza nieznana wersja powoduje konflikt.

Wycofanie źródeł:

    python3 /root/seban-edytor-instalator.py --rollback /katalog/kopii-z-wyniku

Cofnięcie sprawdza wszystkie pliki przed zapisem i odmawia nadpisania późniejszych
modyfikacji. Cofnięcie źródeł nie zmienia wcześniej wdrożonej binarki ani stanu rdzeni.

Pakiet nie kopiuje całego serwera, nie zmienia Compose, nie instaluje gry, nie rusza
kont/postaci, nie buduje obrazów, nie restartuje gry i nie wykonuje push.
Jednorazowe włączenie obsługi wymaga osobnego zbudowania i wdrożenia panelu oraz
silnika w obecnym projekcie z jego aktualnymi argumentami i cache. Nie dołączono
ślepej komendy wdrożenia: trzeba najpierw sprawdzić bieżące pliki i konfigurację VPS.
Zapisanie źródeł NIE oznacza, że edytor już działa na serwerze.

## Formularz i działanie
Zakładka `/db/systemy/kon`: poziomy 1–30, wybór spośród 22 rodzajów bonusów,
dodawanie/usuwanie pozycji, nazwa, kolor, grafika TGA i podgląd. Pozostałe zamówione
systemy są kolejnymi etapami, a nie atrapami gotowych zakładek.

Domyślne wartości odpowiadają sprawdzonemu blokowi konia w bazowym commicie.
Dodatkowe rodzaje bonusów mają początkowo zero. Na 30 poziomie m.in.: atak 20,
HP 1000, potwory 5%, bossy/metiny 0%, ruch 20, klasy 15%, ludzie 10%, żywioły 5%,
odporności na potwory/bossy 50 promili. Instalator wymaga także zerowych starych
nagród questa i botów, aby nie sumować dwóch mechanizmów.

Zapis projektu nie zmienia aktywnej tabeli. „Zapisz i zastosuj” zapisuje historię,
a następnie atomowo przekazuje kompletną tabelę wraz z UUID i SHA256. Nie ma SQL
zmieniającego konta, postępy, odebrane nagrody, Yang ani przedmioty.
Silnik sam sprawdza sumę, kolejność poziomów, zakresy i kompletność danych.
Przeliczenie używa istniejącego ComputePoints, zamiast dopisywać trwałe nagrody.
Każdy proces gry ma osobny zegar uruchamiany z StartWorldClock przed ścieżką botów.
Obsługa nie wymaga graczy ani botów i nie kończy się po uruchomieniu ich pętli.
Przelicza do 200 postaci na przebieg i potwierdza dopiero zakończenie całej partii.
Panel czyta rzeczywisty boot-plan z istniejącego montowania game-var tylko do odczytu.
Potrzebne są świeże potwierdzenia wszystkich planowanych rdzeni gry, z właściwym
UUID, rewizją i zakończoną liczbą postaci. Brak/stary heartbeat lub zmieniony plan
nie oznacza sukcesu. Panel nie otrzymuje dostępu do Dockera.

Przełączniki modułu i konia zerują wkład bonusów dopiero po zastosowaniu. Nie kasują
konfiguracji, historii ani poziomów konia. Podgląd klienta ma osobny przełącznik.
Zmiany zwykłych ustawień po pierwszym wdrożeniu nie wymagają kompilacji/restartu.

## Paczki klienta
Prywatny eksport samego ROOT wymaga aktualnej własnej pary root.index/root.data.
Zmiany dopisywane są do danych i indeksu; pozostałe wpisy pozostają nietknięte.
Nieznana zmiana w funkcji konia zatrzymuje operację. Obsługiwane EterPack v2,
typy wpisów 0/1/2; CRC, limity i sprzeczne duplikaty są sprawdzane. Generowany kod
jest ASCII z jawnie zapisanymi bajtami CP1250 i składnią zgodną z Pythonem 2.

ZIP prywatnej pary zawiera pack/, before/, manifest i install-root.py. Zamknij grę:

    python install-root.py --pack "C:\metin2 mod\MT2009PLUSSINGLEPLAYERKLIENT\pack"

Cofnięcie własnej pary z kontrolą późniejszych zmian:

    python install-root.py --pack "C:\metin2 mod\MT2009PLUSSINGLEPLAYERKLIENT\pack" --undo

Pełne wydanie w edytorze wymaga dodatkowo własnej pary gamedata; jest ona zachowana
bez zmiany bajtów. dbdata i jego znacznik pochodzą z istniejącego eksportera panelu.
Sprawdzane są rozmiary, SHA256, rzeczywisty stamp paczki oraz bieżący stamp serwera.
ZIP zawiera dokładnie te same sześć plików i znacznik, które opublikowano w wydaniu.
Każde wydanie ma niezmienny adres, manifest i zachowane oryginały zmienianego ROOT.
Pobieranie ponownie sprawdza faktyczne pliki. Konflikt konfiguracji lub równoległa
nowsza publikacja blokuje przełączenie opublikowanego wydania.

Ważne: osobiste wydania są dostępne w zakładce konia za logowaniem. NIE zastępują
starego globalnego `/paczki-klienta/klient-komplet.zip` ani ROOT innych użytkowników.
Dotychczasowy publikator `/root/odswiez-pelny-zip.py` pozostaje bez zmian. To jawne
ograniczenie zakresu: wspólna automatyczna promocja do globalnego zestawu wymaga
osobnego uzgodnienia i kontroli zgodności, zamiast bezwarunkowego nadpisywania.
Pobranie/publikacja nie oznacza podmiany plików Windows ani testu w grze.

## Trwałe pliki i zapis
Spool `/opt/m2spool/systems/horse`: draft.json, request.txt, history/, operations/,
status/, assets/, releases/, publications/ i last-client-publication.json.
Nowy m2-systems przygotowuje katalog i grupę m2spool przed spadkiem uprawnień.
Przed zapisem GitHub wyeksportuj konfigurację i zmienione wpisy klienta:

    python3 /root/seban-edytor-instalator.py --export-state

To ta sama funkcja co dołączony export-state.py.
Instalator zachowuje też własny pakiet odtworzeniowy pod
`docker/game/zachowane-zmiany/horse-editor-<hash>` — katalog zbierany przez obecną
komendę zapisu. Sprawdź jej zakres na swoim VPS; pakiet jej nie rekonfiguruje.
Eksport konfiguracji nie jest dowodem zastosowania w grze i nie wykonuje push.
ROOT na Windows wymaga osobnej kopii: zapisz-mt2009 nie pobiera plików z komputera.

## Weryfikacja i pozostałe ograniczenia
Testy lokalne obejmują protokół Python/C++, walidację, domyślne wartości,
przełączniki, każdy rdzeń, stare/missing ACK, równoległe wersje, formularz/CSRF,
konflikty ROOT, zachowanie innych wpisów, publikację ZIP, stamp i uszkodzone pliki,
instalację/idempotencję/cofnięcie oraz awarię w połowie zapisu.
Osobny test rzeczywistego nagłówka zegara z atrapami interfejsów gry sprawdza
450 postaci, pracę bez graczy i brak ponownego przeliczania tego samego UUID.
Atrapy nie zastępują pełnej kompilacji i linkowania gry.
Nie wykonano: uruchomienia na VPS, testu UI w przeglądarce/Windows, natywnego
klienta Python 2 ani testu rzeczywistych bonusów i relogowania w grze.
W testach dbdata użyto istniejącego algorytmu stamp i eksportera zastępczego;
połączenie z aktualną bazą VPS nie było dostępne. Znany test ogólny autodbdata
wykazywał błąd „no dbdata stamp” także na niezmienionej bazie repozytorium.
