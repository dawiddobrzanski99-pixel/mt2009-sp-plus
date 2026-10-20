# Zabezpieczenie zmian DT, egzo/rad i Ukrainki

DT: deviltower5_regen.txt, 37 wpisow 180s -> 36s.
Zrodlo: docker/game/src/serverfiles/share/data/dungeon/deviltower5_regen.txt.
Aktywny plik: /opt/metin2/share/data/dungeon/deviltower5_regen.txt.

Tabele custom odczytano z dzialajacego kontenera metin2-game:
/opt/m2spool/drops/mob_drop_item.custom.txt
/opt/m2spool/chests/special_item_group.custom.txt
Przy odtwarzaniu porownac aktualne tabele i scalic zmiany; nie nadpisywac nowszych.
Dotyczy 39008/39030 u bossow; grupy ilosci 90039008/90039030.
Wagi ilosci 1-5: 32000,30400,1560,39,1.
Razador i Nemere: zmienione zrodla questow sa zbierane z docker/game/quest.
Ukrainka: zrodla questow i receptur sa zbierane przez istniejaca komende.

UWAGA: ROOT zmieniony tylko na Windows nie jest pobierany przez zapis VPS.
Nie potwierdzono tutaj zgodnosci opublikowanego ROOT z poprawka Windows.
Ten etap nie kompiluje, nie wdraza i nie potwierdza testow w grze.
