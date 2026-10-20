# Rejestr naszych zmian MT2009 — stan 2026-10-20

Katalog: `/opt/metin2/linux-port/docker/game/zachowane-zmiany/REJESTR/`
(zbierany automatycznie przez `zapisz-mt2009`).

Podstawa porownania: czysta paczka autora `zaxerrrr-dot/mt2009-sp-plus`, tag `v2.32.0`
(commit 73c2f8b0, 12.10.2026) + ZIP wydania serwera 2.32.0, rozpakowane w
`/root/porownanie-autor-v2.32.0/` (`autor/` = repo, `zip/` = paczka serwera).
Zainstalowana wersja na VPS: 2.32.0 (`/opt/metin2/VERSION`). Autor ma juz 2.35.0 — nie instalowac
bez decyzji wlasciciela (nowe systemy, ktorych na razie nie chcemy).

Ograniczenie: ZIP autora zawiera tylko pliki, ktore sam zmienia. Bazowy silnik
(oficjalne Playerbots Tieru 2.2.0) i `serverfiles` nie sa dostepne — w tych plikach nasze
zmiany rozpoznajemy po znacznikach `CUSTOM_*_V*`, `MT2009_*`, `HORSE_*`, `GUILD_*` itd.,
kopiach `.bak` i katalogu `/opt/metin2/kopie-naszych-zmian/`.

## 1. Co nadpisze aktualizacja autora (update.sh rozpakowuje ZIP na linux-port)

Plik `pliki-zmienione-wzgledem-autora.txt` — 68 plikow, ktore autor tez zmienia.
Po kazdej aktualizacji TE pliki trzeba sprawdzic i ponownie dopisac nasze bloki.
Szczegoly (liczba linii roznicy i nasze znaczniki): `porownanie-z-autorem-v2.32.0.txt`, sekcja A.

Najwazniejsze:
| Plik | Nasze zmiany (znaczniki) |
|---|---|
| game/src/item_manager.cpp | drop: CHEST50122_*, CUSTOM_COR_PROGRESSION, CUSTOM_DROP_CLEANUP_*, CUSTOM_MAP_MATERIAL_CHESTS, CUSTOM_METIN_WEIGHTED_QUANTITY_V3, CUSTOM_NORMAL_KU_TO_BOX, CUSTOM_RECIPE_BOX_*, CUSTOM_TEMPLE_*, CUSTOM_WUKONG_EXTRA_DROP, METIN_KU_KD_*, SharedFinalBossDrops, MT2009_NASZE_MARMUR_CZARNY_ORK_V1 |
| game/src/char.cpp / char.h | gildia (CUSTOM_GUILD_COMBAT_REWARDS, GUILD_STATS_REFRESH), polimorfia (POLYMORPH_ACTIVE_REWARDS), SEBAN_HORSE_V2 |
| game/src/char_battle.cpp | obrazenia mobow/bossow (CUSTOM_MONSTER_DAMAGE_X18_BOSS_X14_V6), bossy bez przepychania, HUD dmg dungeonu, kon bez bossow |
| game/src/char_affect.cpp | GUILD_LOGIN_POINTS, POLYMORPH_DURATION_G30_P60, MISSION_PANEL_DEATH_PERSIST, WEEKLY_AFFECT_LOAD_FIX |
| game/src/char_item.cpp | PICKUP_ACTUAL_COUNT, MT2009_PLUS9_ORIGIN, marmur 70108 |
| game/src/char_state.cpp | CUSTOM_ALL_METIN_SPAWN_X15_V2 |
| game/src/dungeon.* , cmd.cpp | licznik czasu wyprawy, okno obrazen, liczniki mapy |
| game/src/guild.cpp | wejscie/wyjscie z gildii bez czekania |
| game/src/cube.cpp, bin/m2-cube | kategorie i receptury Ukrainki |
| game/src/playerbot_*.h | skrzynki botow, klepsydra min. 1,5 kk, rangi (RANK_CUMULATIVE_REWARDS_V4, MT2009_RANK_BADGES_V4), tygodniowe nagrody, kon30, kolekcjoner |
| game/src/questlua_pc.cpp | BIO_COLLECTOR_V1 |
| game/quest/*.quest (9) | dungeony: Biblioteka, Smok, Nemere, Razador, Atlantyda, Skorpion, Dzungla, Wukong; konie.quest |
| game/Dockerfile | Ukrainka (questy, receptury, obraz KD) |
| mariadb/playerbot/apply.sh | KD 28500, egzo/rada stack, zachowane przedmioty |
| seban-panel app.py, Dockerfile, m2clientpack/dbsource.py, dbdata.py | strona zmian, pobieranie paczek klienta, eksport ikon/skrzynek/Ukrainki/marmuru |
| panel/app/admin_panel.py | zmiany panelu administracyjnego |

## 2. Nasze nowe pliki (aktualizacja ich nie usuwa, ale trzeba pilnowac hookow w plikach z p. 1)
- Silnik: `chest50122_policy.h`, `custom_bot_chests.h`, `custom_cor_progression.h`, `custom_drop_cleanup.h`,
  `custom_guild_combat_rewards.h`, `custom_horse_polymorph_rewards.h`, `custom_map_counters.h`,
  `custom_marmur_czarny_ork.h`, `custom_material_chests.h`, `item_manager_private_types.h`,
  `seban_horse_live.h`, `seban_horse_rewards.h`, `seban_sha256.h`, prywatny `mt2009_private_protocol_keys.h` (NIE do Git).
- Questy: `klepsydra_biologa`, `ukrainka_wymiany`, `desert_first/second/third_quest`, `orcvalley_first_quest`,
  `shop_unlock_slots`, `skill_reset2`.
- Ukrainka: `docker/game/ukrainka/` (cube.native.txt, kd_recipes.txt, npc.a1/b1/c1, crafting_override.lua).
- Panel/klient: `m2clientpack/custom_material_*`, `custom_ukrainka_*`, `custom_windows_source/`, `appearance_pack.py`,
  `restored_item_appearance.py`, `scroll_client_patch.py`, `custom_marmur_czarny_ork_client.py`, `horse_*.py`,
  `dbeditor/systems_horse.py`, `templates/dbeditor/systems_horse.html`, `static/icons/*`.
- Moduly z kontrola/wgraniem: `zachowane-zmiany/marmur-czarny-ork/`, `zachowane-zmiany/horse-editor-*/`,
  `zachowane-zmiany/dt-egzo-ukrainka-*/`.

## 3. Edycje z panelu Seban (baza) — `panel-historia-edycji.tsv`
`player.web_dbeditor_history`: 2123 zmiany 06–15.10.2026, wszystkie zastosowane.
- world.mob_proto: 936 mobow, damage_min/damage_max.
- world.item_proto: 30 przedmiotow (KD +4/+5, mikstury, Peleryna Mestwa, Pierscien Teleportacji, Sakiewka KD, Skrzynia z KU, Karta Wedkarska, Ksiega Obrobki Kamienia...).
- world.skill_proto: Czarowane Ostrze, Jazda konna, Przywolanie konia, Silne Cialo, Zwiekszenie Ataku.
- world.shop_item: Handlarka Roznosci (10 pozycji); world.crafting_*: owoce; world.item_extra_apply: 6 KD;
  common.itemshop_items: 9 pozycji.
Migawka tabel world trafia do Git przez `zapisz-mt2009` (customizations/database/world).

## 4. Edycje z panelu w wolumenie spool — UWAGA, nie sa w Git
`/var/lib/docker/volumes/metin2_rates-spool/_data/` (w kontenerach `/opt/m2spool`):
drops (116 plikow), chests (28), cube (55), regen (160), spawns (277), quests (295), systems, dragonsoul,
fishing, crafting, custom-changes, dbeditor. Przy starcie gry `entrypoint.sh` naklada je na dane gry
(m2-regen, m2-dragonsoul, spawny, drop). Przetrwaja aktualizacje i przebudowe obrazu (wolumen),
Od 20.10.2026 `zapisz-mt2009` zapisuje je do `customizations/panel-spool/` (blok MT2009_NASZE_ZAPIS_SPOOL_V1;
kopia skryptu sprzed zmiany: /opt/metin2/kopie-naszych-zmian/zapis-spool-20261020-171703). Pominiete:
custom-changes (logowanie panelu, sqlite), logi, paczki .data/.index/.zip, katalogi dbdata-sprawdzone-*.
Z custom-ui-work zapisywane sa grafiki (.tga/.png/.jpg/.dds) i zrodla okien klienta (.py) — ikony, ramki, okna.

## 5. Klient
- dbdata (item_proto, itemdesc, item_list, ikony) generuje panel z bazy + `m2clientpack` → zawsze odswiezac
  publikatorem `/root/odswiez-pelny-zip.py`; gracz pobiera z panelu.
- root, etc, locale i grafiki: aktualizacja klienta autora je nadpisuje. Aktualne pliki sa na Windows wlasciciela —
  przed zmiana trzeba je od niego dostac, poprawic i odeslac. Odczytane kopie: repo `customizations/client-packs/`.
- Nasze zmiany klienta: okna (ramki, kontrast, panel misji, zlote ikony questow), liczniki mapy, okno obrazen,
  licznik czasu wyprawy, Yang k/kk/kkk, ekrany ladowania, tlo wyboru postaci, flagi krolestw, cyfry obrazen,
  ikony skrzynek/materialow/receptur/klepsydry, model Remy (Ukrainka).

## 6. Stan wdrozenia (20.10.2026 17:09)
- Dziala: binarka gry podmieniona w kontenerze przez czat edytora konia (kompilacja 16:52–16:56) — zawiera
  wspolny fix z 19.10 i edytor konia; NIE zawiera marmuru 70108. Obraz `metin2/game:mt2009` (17.10) jest starszy —
  odtworzenie kontenera przywrocilby stara gre.
- Przygotowane, nieskompilowane: marmur Czarnego Orka (70108).
- Do testu w grze: edytor konia, wspolny fix (Ukrainka, Cory, Seon-Hae, dungeony, drop z bossow).

## 7. Po aktualizacji autora — kolejnosc
1. Przed: `zapisz-mt2009 "przed aktualizacja X"`, kopia `/opt/metin2/linux-port` i wolumenu spool.
2. Aktualizacja, BEZ automatycznej kompilacji.
3. Dla kazdego pliku z p. 1: porownac z wersja sprzed aktualizacji, dopisac nasze bloki (po znacznikach).
4. Moduly: `python3 zachowane-zmiany/<modul>/modul.py --check` i `--apply`.
5. Kompilacja obrazu game, restart, odswiezenie dbdata/ZIP, pobranie klienta, test w grze.
6. Klient po aktualizacji klienta autora (OBOWIAZKOWO):
   a. Wlasciciel wysyla z Windows nowe paczki: root, etc, locale (index+data) i inne zmienione.
   b. Porownac wpis po wpisie z naszymi zapisanymi: repo `customizations/client-packs/` (root, gamedata, dbdata)
      oraz grafikami w `customizations/panel-spool/custom-ui-work/` i `m2clientpack/custom_*_assets`.
   c. Wpis zmieniony przez autora, w ktorym byla nasza zmiana → dopisac nasza zmiane do nowej wersji
      (okna .py: po znacznikach; grafiki/ikony: nasza wersja). Nowe wpisy autora zostaja.
   d. Sprawdzic ikony z item_list (skrzynki 50033/50035/50122/50124, 59001–59011, klepsydra 71102, marmur 70108)
      i model Remy (Ukrainka).
   e. Odeslac poprawione paczki wlascicielowi, odswiezyc dbdata/ZIP w panelu, test w grze.
   f. Paczki etc i locale nie sa jeszcze zapisane w Git — przy pierwszej okazji odczytac i dodac.
