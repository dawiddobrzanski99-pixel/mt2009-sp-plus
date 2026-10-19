# START TUTAJ — nasze zmiany MT2009

## Status zapisu
Ten dokument przygotowano na podstawie prywatnego zapisu na VPS.
Nie potwierdza on wykonania commita, push ani wdrozenia oczekujacego fixa.
Nie wszystkie historyczne zmiany zostaly jeszcze zweryfikowane.

## Najpierw przeczytaj
1. WYMAGANIA-ZAPISU.md.
2. MAPE-PLIKOW.json oraz manifesty zachowanych plikow.
3. Rejestry historycznych zmian i wyniki sprawdzen.
4. Instrukcje odtworzenia oraz aktualizacji klienta.

## Instalacja
Projekt: /opt/metin2/linux-port.
Pracuj na istniejacym serwerze. Nie tworz drugiej instalacji.
Kopie wykonuj tylko dla zmienianych plikow i rekordow.
Zachowuj pozostale modyfikacje i kodowanie plikow.

## Klient i panel
Po zmianach wplywajacych na klienta aktualizuj trwale zrodla generatora.
Aktualne dbdata musi byc dostepne do pobrania z panelu.
Pary index/data oraz dbdata_stamp.txt musza pochodzic ze zgodnego eksportu.
Komplet ZIP musi zawierac te same opublikowane paczki.
Nie utozsamiaj zgodnosci ZIP z potwierdzeniem zgodnosci z aktualna baza.
Istniejacy publikator: /root/odswiez-pelny-zip.py.

## Potwierdzone dotychczas
Zachowano prywatnie 108 zmienionych plikow sledzonych przez Git.
Osobno zachowano 579 plikow zrodel natywnych, 81 nowych zrodel i zasobow,
23 dokumenty oraz publikator.
Pary ROOT, dbdata i gamedata sa kompletne i identyczne z plikami w ZIP.
Nie potwierdzono jeszcze zachowania wszystkich grafik z etc i locale.
Nie potwierdzono kompletnego odtworzenia zmian w bazie.

## Zasady
Oddzielaj stan wdrozony, zmienione zrodla i przygotowane poprawki.
Nie przywracaj anulowanych zmian.
Nie zmieniaj bonusow, blokad i zawartosci przedmiotow na podstawie domyslow.
Nie wysylaj sekretow, danych kont, zrzutow bazy ani kopii kontenerow.
