# Kuźnia Mocy — instalator dla innych serwerów (notatki dla nowego czatu)

Stan: 2026-10-21. Ostatnia paczka rozesłana ludziom: `kuznia-mocy-2026.10.21-0123.zip` (użytkownik potwierdził „działa”).

## Co to jest
Kuźnia Mocy to zakładka w panelu Seban (`/db/systemy`): koń, gildia, polimorfia, rangi, ranking tygodnia,
misje Ctrl+N, ulepszanie, Sława (+9), skan serwera, kopia ustawień. Instalator dokłada ją (i systemy silnika
pod nią) do CZYSTEGO serwera MT2009 autora (testowane na 2.32 i 2.36) na VPS lub PC (Docker Desktop).

## Gdzie co leży
- VPS, katalog roboczy: `/root/kuznia-instalator/` (skrypty, `paczka-nowa/` = ostatnia paczka, `.panel.env` = env panelu, NIE commitować).
- Kopia panelu ze WSZYSTKIMI zmianami Kuźni (z niej budowana paczka): `/root/kuznia-test-live-panel/`.
  UWAGA: działający panel użytkownika (`/opt/metin2/linux-port/docker/seban-panel`) NIE ma części nowych zmian.
- Baza różnic silnika: `/root/kuznia-baza-232` (czyste 2.32 = `/root/test-czysty-232` + `/root/autor-2.32-czysty`).
- Czyste serwery autora: `/root/test-czysty-autor/serwer` (2.36), `/root/test-czysty-232/serwer`.
- ROOT: użytkownika `/root/root-uzytkownika/` (oryginał, źródło dodatków klienta), czysty klient autora `/root/root-czysty-klient/`.
- Na PC: `Desktop\MEITN2 CHAT WAZNE\seban-systemy\instalator\` (skrypty + `paczka\`), `seban-systemy\panel\` (kopie zmienionych plików).
- W repo: `linux-port/docker/game/zachowane-zmiany/kuznia-mocy/` (ten plik, skrypty, pliki panelu).

## Budowa paczki (na VPS)
```
cd /root/kuznia-instalator
PANEL_SRC=/root/kuznia-test-live-panel sh zbuduj_paczke.sh /root/kuznia-baza-232 /root/root-uzytkownika /root/kuznia-instalator/paczka-nowa
```
Skrypty:
- `zbuduj_latki.py` — diff czyste↔nasze źródła gry; zostawia tylko bloki Kuźni (regex KEEP); `fixups()` dopasowuje
  linie zależne od innych naszych zmian; `ANCHORS` → `silnik/kotwice/*.json` (gdy łatka nie wejdzie, np. 2.36 Sync rankingu).
  `seban_rank_rewards.h`: DefaultRow pusty (świeży start bez bonusów rang).
- `naloz_latki.sh` — CRLF→LF, oryginały w `.kuznia-oryginal/` + suma `.po` (ponowne uruchomienie zaczyna od oryginału), `kotwice.py`.
- `spakuj_panel.sh` — moduły `dbeditor/systems_*`, szablony, `m2clientpack/{systems_client,horse_editor,horse_publication,horse_pair_installer,kuznia_dodatki}.py`,
  `init.txt`/`nav.txt`; uruchamia `spakuj_klient.py` (dodatki ROOT); tworzy znacznik `kuznia_dodatki/swiezy-start`.
- `spakuj_klient.py` — z ROOT autora: 12 modułów (uimissionpanel, customrewardtooltip, rankpoints, rankbadges, uiweeklyrank, …),
  49 grafik (custom_windows/final, mission_background, ranktitles), `hooks.json` (podpięcia game.py/keybind/uiguild/uitooltip),
  `nazwy.json` (dokładne nazwy wpisów, np. `d:/ymir work/...` — bez tego klient nie widzi grafiki → ZeroDivisionError w Ctrl+N).
- `instaluj_panel.py` — kopiuje pliki, czyści `kuznia_dodatki`, dopisuje install-lines i grupę menu (bez duplikatów).
- `czytaj_ranking.py` — bonusy rankingu tygodnia z `playerbot_weekly_rank.h` serwera docelowego → `ranking-serwera.json`.
- `wewnatrz.sh` (w kontenerze python:3.12-slim), `instaluj.sh` (VPS), `instaluj.ps1`/`instaluj.bat` (PC) → `docker compose build game seban-panel; up -d`.
- Testy: `kompiluj_test.sh KATALOG` (builder `metin2/game:horse-v2-builder-cache-20261020-164141`), `test_dodatki.py` (pełne budowanie ROOT jak w panelu).

## Zasady zachowania (ważne decyzje użytkownika)
- U innych WSZYSTKO od zera: koń/gildia/polimorfia/rangi bez bonusów; ranking tygodnia = bonusy z gry ich serwera;
  misje Ctrl+N = zestaw użytkownika (wbudowany w silnik). BRAK „Ustawień autora” i odznak rang.
- `kuznia_dodatki.fresh()` (znacznik `swiezy-start`) przełącza: zerowe defaults, jednorazowy reset (`systems_hub.fresh_start_once`,
  znaczniki `.swiezy-start-zrobiony`, `.swiezy-ranking-v2` w spool), rangi jako napis, ukryte odznaki, dymek rangi tylko z Kuźni.
- Serwer użytkownika ma znacznik `spool/systems/.autor-kuzni` → u niego nic się nie zeruje.
- Rangi u innych: silnik autora (Waleczny… od 21000), panel bierze rangi z `status/defaults.txt` gry; poniżej 1. rangi tytuł dobroci.
  Czysty exe nie ma `chrmgr.SetRankTitle`/`textTail.GetPosition` → ranga jako kolorowy napis odnawiany co 1 s (dopisek w rankbadges.py).
- Klient: niczego nie wymagać; brakujące pliki dokładać, nieznane wersje → podmiana na wersję Kuźni albo pominięcie z raportem
  (`kuznia_dodatki.LAST_REPORT`, żółty komunikat na Przeglądzie). ZIP ROOT = tylko `pack/` + `CZYTAJ.txt`. Zakładka ROOT tylko na Przeglądzie.
- Ctrl+N: pełny rozmiar 860×660 (zmniejszanie wycofane), nagrody ciemne pogrubione (styl nakładany po każdym DrawRewards).

## Do zrobienia
- Osobny instalator tylko dla użytkownika (bez świeżego startu, z jego ustawieniami i odznakami).
- Wgrać nowe zmiany panelu (czytelne nagrody Ctrl+N, „Zapisz i zastosuj” w Ulepszaniu, prosty ZIP ROOT, raport dodatków) na jego serwer.
