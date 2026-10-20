#!/bin/bash
# Deploys the item icons extracted from Sebastian's actual mt2009 client
# (Klient/pack/icon.data+icon.index) into the panel, replacing/augmenting the
# old r40250-era icon set, and regenerates static/item_icons.json against the
# server's real world.item_proto so every vnum that has a matching icon file
# actually gets shown.
#
# WHERE THIS LIVES: /opt/seban-panel-custom -- outside the m2-updater managed
# tree, so nothing here needs restore_after_tieru_update.sh. Run it once,
# after the new icon PNGs have been uploaded.
#
# BEFORE RUNNING:
#   1) Unzip nowe_ikony_przedmiotow.zip on your own PC.
#   2) Upload the *contents* of its icons_png/ folder (1915 .png files) into
#      a fresh folder on the VPS: /opt/seban-panel-custom/static/icons_new/
#      (e.g. with WinSCP/scp -- however you already get files onto this VPS).
#      So you should end up with files like:
#        /opt/seban-panel-custom/static/icons_new/00020.png
#        /opt/seban-panel-custom/static/icons_new/book_15.png
#        ... (1915 files total)
#   3) Then run this script from anywhere:
#        bash /opt/seban-panel-custom/deploy_new_item_icons.sh
#
# WHAT IT DOES:
#   - Backs up the current static/icons/ and item_icons.json (timestamped) --
#     just in case, even though the operator confirmed the old r40250 set
#     should go entirely.
#   - WIPES static/icons/ and replaces it with icons_new/ only. Nothing from
#     the old set survives; if a vnum has no icon in the new client extract,
#     it simply has no icon in the panel afterwards (reported at the end).
#   - Re-reads every vnum from world.item_proto and rebuilds item_icons.json
#     from scratch against the new set only: exact vnum match first, then the
#     item's own "floor to a multiple of ten" (matches app.py's own
#     refine-level fallback).
#   - Restarts the seban-panel container so it picks up the new json.
set -euo pipefail

PANEL_DIR="/opt/seban-panel-custom"
ICONS_DIR="$PANEL_DIR/static/icons"
ICONS_NEW_DIR="$PANEL_DIR/static/icons_new"
JSON_PATH="$PANEL_DIR/static/item_icons.json"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -d "$ICONS_NEW_DIR" ]; then
  echo "BLAD: brak $ICONS_NEW_DIR -- najpierw wgraj tam pliki .png z icons_png/ (patrz komentarz na gorze skryptu)." >&2
  exit 1
fi

NEW_COUNT=$(find "$ICONS_NEW_DIR" -maxdepth 1 -name '*.png' | wc -l)
echo "== Znaleziono $NEW_COUNT nowych plikow ikon w $ICONS_NEW_DIR =="

echo "== 1/4: kopia zapasowa =="
cp -a "$ICONS_DIR" "$PANEL_DIR/static/icons.bak-$STAMP"
[ -f "$JSON_PATH" ] && cp -a "$JSON_PATH" "$PANEL_DIR/static/item_icons.json.bak-$STAMP"
echo "OK: backup w static/icons.bak-$STAMP i item_icons.json.bak-$STAMP"

echo "== 2/4: kasowanie starych ikon r40250 i wgrywanie nowych z klienta mt2009 =="
rm -f "$ICONS_DIR"/*.png
cp -f "$ICONS_NEW_DIR"/*.png "$ICONS_DIR"/
echo "OK: $(find "$ICONS_DIR" -maxdepth 1 -name '*.png' | wc -l) plikow w static/icons/ teraz (tylko nowe)"

echo "== 3/4: pobieranie listy vnumow z world.item_proto =="
cd /opt/metin2-mt2009/Serwer/linux-port/docker
docker compose exec -T mariadb sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B -e "SELECT vnum FROM world.item_proto"' > /tmp/m2_item_vnums.txt
VNUM_COUNT=$(wc -l < /tmp/m2_item_vnums.txt)
echo "OK: $VNUM_COUNT vnumow"

echo "== 4/4: przebudowa item_icons.json =="
python3 - "$JSON_PATH" /tmp/m2_item_vnums.txt "$ICONS_DIR" << 'PYEOF'
import json, sys, os

json_path, vnums_path, icons_dir = sys.argv[1], sys.argv[2], sys.argv[3]

available = set(os.listdir(icons_dir))

with open(vnums_path, encoding="utf-8") as f:
    vnums = [int(line.strip()) for line in f if line.strip().isdigit()]

new_map = {}
matched_exact = matched_floor10 = 0
missing = []

for vnum in vnums:
    key = str(vnum)
    exact = f"{vnum:05d}.png"
    floor10 = f"{(vnum - vnum % 10):05d}.png"
    if exact in available:
        new_map[key] = exact
        matched_exact += 1
    elif floor10 in available:
        new_map[key] = floor10
        matched_floor10 += 1
    else:
        missing.append(vnum)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(new_map, f, ensure_ascii=False, indent=0, sort_keys=True)

print(f"OK: item_icons.json zapisany od zera -- {len(new_map)} wpisow "
      f"(exact={matched_exact} floor10={matched_floor10})")
if missing:
    print(f"UWAGA: {len(missing)} vnumow bez zadnej ikony w nowym zestawie (pierwsze 20): {missing[:20]}")
PYEOF

echo "== restart panelu =="
docker compose up -d --force-recreate seban-panel
echo "Gotowe. Sprawdz http://57.128.176.139:7790/items -- jesli cos nie wyglada dobrze,"
echo "kopie zapasowe leza w static/icons.bak-$STAMP i static/item_icons.json.bak-$STAMP."
