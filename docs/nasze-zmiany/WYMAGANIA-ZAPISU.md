# Wymagania zachowania naszych zmian MT2009

Status: wymagania przygotowane do dokumentacji repozytorium.
Ten dokument nie potwierdza wdrozenia poprawki ani wykonania push.

## Zakres
Zachowac wszystkie odzyskane i zweryfikowane zmiany serwera, klienta,
ROOT, questow, receptur, migracji SQL, generatorow, ikon, modeli,
grafik, opisow, bonusow, dzialania i blokad przedmiotow oraz skrzynek.
Uwzglednic rowniez zmiany z poprzedniego tygodnia.
Braki oznaczac jawnie. Nie uznawac samej sciezki lub wspomnienia
w rozmowie za dowod zachowania pliku.

## Sposob pracy
Pracowac na istniejacej instalacji /opt/metin2/linux-port.
Nie tworzyc drugiego serwera i nie kopiowac calego serwera przy poprawkach.
Robic datowane kopie tylko zmienianych plikow i konkretnych rekordow SQL.
Zmieniac aktualne pliki selektywnie, zachowujac pozostale modyfikacje,
kodowanie i zgodnosc klienta z Pythonem 2.
Zachowywac powtarzalne patche, migracje i instrukcje odtworzenia.

## Klient i dbdata dostepne z panelu
Po zmianach wplywajacych na klienta poprawiac trwale zrodla generatora,
mapowania oraz zasoby, a nie tylko jednorazowy wygenerowany plik.
Eksportowac aktualne dbdata z aktualnej bazy i poprawionego generatora.
Publikowac zgodne dbdata.index, dbdata.data i dbdata_stamp.txt
w istniejacym mechanizmie pobierania panelu.
Sprawdzac pliki faktycznie udostepniane przez panel, ich sumy kontrolne
i zgodnosc z eksportem. Samo utworzenie plikow roboczych nie wystarcza.
Jesli panel udostepnia komplet klienta, aktualizowac takze odpowiednie
paczki i komplet ZIP, aby pobranie nie przywracalo starych danych.
Pary index/data podmieniac razem; nie wymyslac formatu stempla.
Najpierw odczytac istniejacy publikator /root/odswiez-pelny-zip.py.
Nie publikowac starych albo niespojnych paczek jako aktualnych.

## Dokumentacja na GitHub
Przygotowac docs/nasze-zmiany/START-TUTAJ.md i rejestr zmian,
mape plikow, liste grafik, zachowanie i blokady przedmiotow,
bonusy, instrukcje aktualizacji oraz wyniki weryfikacji.
W instrukcji dla agentow wskazac dokument START-TUTAJ.
Rozrozniac: zrodlo, przygotowany patch, build, wdrozenie,
eksport klienta i test w grze.
Dla kazdej zmiany opisac co, gdzie, dlaczego, jak odtworzyc i jak sprawdzic.

## Zapis Git
Repozytorium: dawiddobrzanski99-pixel/mt2009-sp-plus.
Zachowac historie. Bez force push.
Dodawac konkretne przejrzane pliki i potrzebne zasoby.
Nie wysylac kluczy, hasel, tokenow, danych kont, zrzutow bazy,
logow, cache ani kopii calej instalacji.
Duzych wymaganych zasobow nie pomijac po cichu; ustalic sposob przechowywania.

## Tekst dla nowego czatu po zakonczeniu zapisu
Pracuj z repozytorium dawiddobrzanski99-pixel/mt2009-sp-plus.
Najpierw przeczytaj AGENTS.md i docs/nasze-zmiany/START-TUTAJ.md,
a nastepnie wskazane rejestry, mape plikow i instrukcje odtworzenia.
Zachowaj nasze dotychczasowe zmiany. Pracuj na istniejacej instalacji.
Po zmianach klienta zadbaj o aktualne paczki dostepne do pobrania z panelu.
