# Marmur Czarnego Orka (70108) — modul MT2009_NASZE_MARMUR_CZARNY_ORK_V1

## Co
- Nowy przedmiot 70108 „Marmur Czarnego Orka” (kopia 70104 + flaga STACKABLE).
  Zawsze przemienia w Czarnego Orka (mob 636, poz. 46); socket0 = 636.
- Drop z metinow (IsStone) od poziomu 40, bez Wielkanocnych (8041–8050):
  - Dolina Orkow (mapa bazowa 64, map_n_threeway): 1%,
  - pozostale mapy: 0,5%.
  Stala szansa, bez bonusow dropu i roznicy poziomow. Dotyczy tez botow.
- Zwykly 70104 bez zmian (0,08% z mobow z polymorph_item, bez stackowania).
- Osobny vnum, bo laczenie stosow porownuje tylko vnum — stack 70104 mieszalby rozne potwory.

## Gdzie
| Plik | Zmiana |
|---|---|
| game/src/custom_marmur_czarny_ork.h | nowy: szanse i stale |
| game/src/item_manager.cpp | include + drop za `SharedFinalBossDrops` (glowna sciezka CreateDropItem) |
| game/src/char_item.cpp | ItemProcess_Polymorph: 70108 → 636, `case 70108` |
| seban-panel/m2clientpack/custom_marmur_czarny_ork_client.py | nowy: eksport 70108 do item_proto/item_list/itemdesc klienta |
| seban-panel/m2clientpack/dbsource.py | blok na koncu lancucha client_files |
| world.item_proto, player.item_proto | rekord 70108 |

Ikona: istniejaca `icon/item/70104.tga` — nie trzeba plikow z Windows.

## Uzycie (takze po aktualizacji serwera)
    python3 modul.py --check     # JEST / BRAK / KONFLIKT, nic nie zmienia
    python3 modul.py --apply     # wgrywa brakujace czesci + kopia w /opt/metin2/kopie-naszych-zmian/
    python3 modul.py --revert    # usuwa bloki ze zrodel i panelu
Po --apply: kompilacja obrazu game + restart, potem odswiezenie dbdata/ZIP w panelu
(/root/odswiez-pelny-zip.py), pobranie klienta, test w grze.

## Status (aktualizuj)
- [ ] zrodla wgrane  - [ ] baza  - [ ] kompilacja  - [ ] wdrozenie  - [ ] dbdata/ZIP  - [ ] test w grze

## Test w grze
1. Zbij metin 40+ w Dolinie (8008/8009) — /item lub log: drop 70108 ~1%.
2. Metin 40+ poza Dolina ~0,5%; metin < 40 i Wielkanocny — brak.
3. Dwa marmury lacza sie w stos; dymek pokazuje „Czarny Ork”.
4. Uzycie: przemiana w Czarnego Orka, z stosu znika 1 szt.
