Pracujemy nad moim serwerem Metin2 (MT2009 SP+, Playerbots) na VPS Debian 12, Docker.
Polacz sie z VPS po SSH (root, klucz) i NAJPIERW przeczytaj na serwerze:
1. /opt/metin2/linux-port/docker/game/zachowane-zmiany/REJESTR/REJESTR-ZMIAN.md  ← glowny spis moich zmian
2. ten sam katalog: pliki-zmienione-wzgledem-autora.txt, porownanie-z-autorem-v2.32.0.txt, panel-historia-edycji.tsv
3. repo GitHub dawiddobrzanski99-pixel/mt2009-sp-plus (main): AGENTS.md, docs/nasze-zmiany/START-TUTAJ.md
   (kopia repo na VPS: /root/mt2009-git-20261019-203457-8wnhzjlu/repo, czytaj przez git show origin/main:<plik>)

Najwazniejsze zasady:
- Instalacja: /opt/metin2/linux-port. Pracuj na niej, nie tworz drugiego serwera. Kopie z data tylko zmienianych
  plikow i rekordow SQL (/opt/metin2/kopie-naszych-zmian/). Zachowuj kodowanie plikow i Python 2 klienta.
- Aktualizacje autora (zaxerrrr-dot/mt2009-sp-plus, tools/update.sh) NADPISUJA 68 plikow z
  pliki-zmienione-wzgledem-autora.txt — po aktualizacji trzeba w nich dopisac moje bloki ponownie
  (po znacznikach CUSTOM_*_V*, MT2009_*, HORSE_*, GUILD_* itd.). Nie instaluj nowej wersji autora bez mojej zgody.
- Nowe zmiany rob jako moduly w docker/game/zachowane-zmiany/<nazwa>/ z modul.py --check/--apply/--revert
  i blokami oznaczonymi MT2009_NASZE_<NAZWA>_V1 (wzor: marmur-czarny-ork).
- Klient: dbdata (item_proto, itemdesc, item_list, ikony) generuje panel — po zmianie odswiez /root/odswiez-pelny-zip.py,
  ja pobieram z panelu. root / etc / locale / grafiki mam na Windows — zanim je zmienisz, poproś mnie o aktualne pliki,
  potem je poprawiasz i odsylasz. Aktualizacja klienta autora tez nadpisuje te pliki — po kazdej
  aktualizacji klienta przejdz procedure z REJESTR-ZMIAN.md p. 7.6 (porownanie wpis po wpisie z
  customizations/client-packs i zapisanymi grafikami/ikonami, dopisanie naszych zmian).
- Edycje z panelu Seban: baza (player.web_dbeditor_history) i wolumen /var/lib/docker/volumes/metin2_rates-spool/_data
  (drops, chests, cube, regen, spawns, quests...). zapisz-mt2009 zapisuje je do customizations/panel-spool/
  razem z grafikami i oknami z custom-ui-work (bez custom-changes — tam jest logowanie panelu).
- Kompilacja/restart gry: tylko po uzgodnieniu ze mna i gdy zaden inny czat nie pracuje na zrodlach.
  Obraz game buduje sie ze WSZYSTKICH zrodel naraz. Sprawdz, czy dzialajaca binarka nie jest podmieniona w kontenerze
  (docker diff metin2-game) — wtedy odtworzenie kontenera cofa gre.
- Rozrozniaj: przygotowany kod / kompilacja / wdrozenie / test w grze. Nie zgaduj wartosci — czytaj zrodla.
- Anulowane, NIE przywracac: globalne stackowanie wyposazenia, ogolna zmiana szans ulepszania.
- Nie dodawaj do Git hasel, kluczy, danych kont ani prywatnego naglowka protokolu. Nie otwieraj /root/metin2-accounts.txt.
- Zapis: gdy napisze „dziala”, podaj komende `zapisz-mt2009 "konkretny opis zmian"`. Nie mow, ze zapisano,
  dopoki wynik nie potwierdzi push.

Stan na 20.10.2026: dziala binarka z edytorem konia + wspolnym fixem (podmieniona w kontenerze 17:08, do testu);
marmur Czarnego Orka 70108 przygotowany w zrodlach i bazie, nieskompilowany.

Teraz chce: <tu wpisz zadanie>
