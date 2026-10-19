# Stan przygotowanego zapisu

To kandydat do commita, nie potwierdzenie push ani wdrozenia fixa.

## Zachowane zakresy
- Zmienione pliki projektu pod ich dotychczasowymi sciezkami.
- Nowe questy, receptury Ukrainki, generator i jego zasoby.
- Migawka zrodel game/src i common w customizations/server-source-snapshot.
- Odczytane ROOT, gamedata i dbdata w customizations/client-packs.
- Oryginalne indeksy paczek i metadane dziewieciu identycznych duplikatow.
- Publikator klienta i dokumentacja wymagan.

## Prywatne stale protokolu
W publikowanej migawce desc.cpp i input_main.cpp odwolania prowadza do
mt2009_private_protocol_keys.h. Trzy wartosci zachowano tylko lokalnie.
Sprawdzono bajtowo, ze odwrocenie tej zamiany odtwarza oryginalne pliki.
Przed odtwarzaniem tych zrodel nalezy bezpiecznie przywrocic prywatny
naglowek do docelowego katalogu game/src. Nie dodawac go do Git.
Dzialajace zrodla VPS nie zostaly zmienione.
Prywatny naglowek jest wymaganiem odtworzenia, nie zgubionym plikiem.

## Klient
ROOT, gamedata i dbdata byly zgodne z osobnymi paczkami w panelowym ZIP.
Zapis zawiera m.in. model Remy, ikony klepsydry 71102, skrzynek
50033/50035/50122/50124, skrzyni receptur 59010 i materialow 59001-59009.
Samo istnienie ikony nie potwierdza aktywnego przypisania ani dzialania przedmiotu.
Zgodnosc ZIP nie potwierdza zgodnosci eksportu z aktualna baza.

## Pozostale wymagania do sprawdzenia
- Paczki etc i locale oraz ewentualne zasoby pozostale tylko na Windows.
- Szczegolowy rejestr historycznych bonusow, funkcji i blokad przedmiotow.
- Migracje odtwarzajace niestandardowe rekordy bazy.
- Osobne zachowanie przygotowanych, niewdrozonych poprawek.
- Przeglad konfiguracji i pozostalych trafien skanera.
Nie oznaczac tych punktow jako wykonane bez dowodow.

## Wykluczone
Klucze SSH, prywatny naglowek, hasla, dane kont, zrzuty baz,
kopie kontenerow, cache i logi. Surowy ZIP i pliki data nie sa
dublowane w tym kandydacie; zachowano rozpakowana zawartosc.
