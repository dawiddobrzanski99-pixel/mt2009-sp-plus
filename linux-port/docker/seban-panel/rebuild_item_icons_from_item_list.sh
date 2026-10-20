#!/bin/bash
# Rebuilds static/item_icons.json using the CLIENT's own authoritative
# vnum -> icon file mapping (gamedata/item_list.txt, extracted from
# Klient/pack/gamedata.data), instead of guessing the icon filename from the
# vnum itself.
#
# Why this exists: the guess ("exact vnum.png, else floor-to-ten") is wrong
# for a real chunk of items -- refine-tier soul stones, "Bez" (50725 -> icon
# 50705), skill books that share a generic cover (book_11/book_12), chests
# that reuse another chest's art (50194 -> 50187), and named (non-numeric)
# icons like WarriorsAmulet.tga. item_list.txt is the client's own answer for
# every one of these; matching against it directly fixes them all at once
# instead of one report at a time.
#
# BEFORE RUNNING: upload item_list.txt next to this script, e.g.
#   scp item_list.txt deploy... ubuntu@57.128.176.139:/opt/seban-panel-custom/
# It only needs to sit wherever you run this script FROM (see ITEM_LIST_PATH
# below) -- it is read once and not copied anywhere permanent, though keeping
# it in /opt/seban-panel-custom for next time costs nothing (270 KB).
set -euo pipefail

PANEL_DIR="/opt/seban-panel-custom"
ICONS_DIR="$PANEL_DIR/static/icons"
JSON_PATH="$PANEL_DIR/static/item_icons.json"
ITEM_LIST_PATH="${1:-$PANEL_DIR/item_list.txt}"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -f "$ITEM_LIST_PATH" ]; then
  echo "BLAD: brak $ITEM_LIST_PATH -- wgraj tam item_list.txt albo podaj sciezke jako argument." >&2
  exit 1
fi

echo "== 0/3: kopia zapasowa =="
[ -f "$JSON_PATH" ] && cp -a "$JSON_PATH" "$PANEL_DIR/static/item_icons.json.bak-$STAMP"

echo "== 1/3: pobieranie listy vnumow z world.item_proto =="
cd /opt/metin2-mt2009/Serwer/linux-port/docker
docker compose exec -T mariadb sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B -e "SELECT vnum FROM world.item_proto"' > /tmp/m2_item_vnums.txt
VNUM_COUNT=$(wc -l < /tmp/m2_item_vnums.txt)
echo "OK: $VNUM_COUNT vnumow"

echo "== 2/3: przebudowa item_icons.json z item_list.txt (+ dawny fallback) =="
python3 - "$JSON_PATH" /tmp/m2_item_vnums.txt "$ICONS_DIR" "$ITEM_LIST_PATH" << 'PYEOF'
import json, sys, os

json_path, vnums_path, icons_dir, item_list_path = sys.argv[1:5]

available = set(os.listdir(icons_dir))
# case-insensitive lookup: item_list.txt spells some icon names differently
# (e.g. "WarriorsAmulet.tga") than the extracted files on disk
# ("warriorsamulet.png") -- match by lowercased stem.
by_lower = {}
for name in available:
    stem = os.path.splitext(name)[0].lower()
    by_lower.setdefault(stem, name)

# vnum -> icon stem, straight from the client's own table.
client_icon = {}
with open(item_list_path, encoding="utf-8", errors="replace") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3 or not parts[0].isdigit():
            continue
        vnum = int(parts[0])
        icon_path = parts[2]
        stem = os.path.splitext(os.path.basename(icon_path))[0].lower()
        client_icon[vnum] = stem

with open(vnums_path, encoding="utf-8") as f:
    vnums = [int(line.strip()) for line in f if line.strip().isdigit()]

new_map = {}
matched_client = matched_exact = matched_floor10 = 0
missing = []

for vnum in vnums:
    key = str(vnum)
    stem = client_icon.get(vnum)
    if stem and stem in by_lower:
        new_map[key] = by_lower[stem]
        matched_client += 1
        continue
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

print(f"OK: item_icons.json zapisany -- {len(new_map)} wpisow "
      f"(z item_list.txt={matched_client} exact={matched_exact} floor10={matched_floor10})")
if missing:
    print(f"UWAGA: {len(missing)} vnumow nadal bez zadnej ikony (pierwsze 30): {missing[:30]}")
PYEOF

echo "== 3/3: rebuild + restart panelu =="
docker compose build seban-panel
docker compose up -d seban-panel
echo "Gotowe. Sprawdz http://57.128.176.139:7790/items w oknie incognito."
