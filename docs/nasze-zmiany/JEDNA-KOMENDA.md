# Jedna komenda zapisu VPS

Uruchom na skonfigurowanym VPS:
    zapisz-mt2009 "opis zmian"

Polecenie odswieza dbdata i ZIP przez istniejacy publikator panelu,
zbiera aktualne zrodla, odczytuje opublikowane ROOT/gamedata/dbdata,
zapisuje migawki wybranych tabel world bez kont i postaci,
sprawdza sekrety, tworzy commit i wykonuje zwykly push na main.

Kopie prywatnych ustawien i stalych protokolu pozostaja tylko na VPS.
Katalog kazdego uruchomienia: /root/mt2009-git-20261019-203457-8wnhzjlu/zapisy/.
W razie bledu nie usuwaj go: zawiera zapis i diagnostyke.

Zrodla i opublikowane paczki moga reprezentowac rozne etapy wdrozenia.
Polecenie nie kompiluje silnika ani nie przebudowuje ROOT/gamedata.
Zmiany klienta istniejace tylko na Windows trzeba osobno przeslac lub zachowac.
Paczki etc/locale nadal wymagaja osobnego zabezpieczenia.

customizations/database/world zawiera dane do porownania i selektywnego
odtworzenia. Kolumny oznaczone hex_encoded przechowuja HEX oryginalnych bajtow.
Nie importuj calej migawki na nowa wersje gry bez porownania i wyboru zmian.
STAN-ZAPISU.md nadal opisuje historyczne braki do uzupelnienia.

Przy nowym trafieniu skanera zapis zatrzyma sie z lokalnymi plikami.
Wyjatki obejmuja tylko znany, przejrzany kontekst kodu.
