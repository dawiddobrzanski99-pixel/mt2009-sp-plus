#!/bin/bash
# Deploys 2 new real in-game map images (Shinsoo & Jinno guild maps, extracted
# and stitched from Klient/pack minimap.dds tiles, same technique as the
# existing chunjo-m1.png etc.) plus the frontend wiring needed to show them:
#   - Dashboard "Mapa świata botów" map dropdown
#   - /maps heatmap dropdown
#   - Background image lookup (heatmap.js, live-widget.js, live-overrides.css)
#
# This adds 4 NEW selectable maps (bounds already existed in app.py, only the
# frontend was missing them), reusing existing easy-monkey.png for the two
# Monkey Dungeon entries since the terrain is identical across kingdoms, only
# entered from a different port -- per the operator's own instruction:
#   - Ziemia Klanu Shinsoo  (kingdom guild map, index 4)  -> shinsoo-guild.png (NEW)
#   - Loch Małp Shinsoo     (index 5)                     -> easy-monkey.png (reused)
#   - Ziemia Klanu Jinno    (kingdom guild map, index 44) -> jinno-guild.png (NEW)
#   - Loch Małp Jinno       (index 45)                    -> easy-monkey.png (reused)
# Also fixes Świątynia Hwang (index 65) missing from both dropdowns even
# though its image and bounds already existed.
#
# Shinsoo M1/M2 and Jinno M1/M2 (Yongan, Jayang, Pyongmoo, Bakra) are NOT in
# this package -- their source client folders (OutdoorA1/OutdoorA3/OutdoorC1/
# OutdoorC3) were not available this round; those come in a follow-up once
# they're extracted the same way.
#
# BEFORE RUNNING:
#   1) Upload nowe_mapy_gildii.zip next to this script on the VPS, e.g.
#      /opt/seban-panel-custom/nowe_mapy_gildii.zip
#   2) Run: bash /opt/seban-panel-custom/deploy_new_maps.sh
set -euo pipefail

PANEL_DIR="/opt/seban-panel-custom"
ZIP_PATH="${1:-$PANEL_DIR/nowe_mapy_gildii.zip}"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -f "$ZIP_PATH" ]; then
  echo "BLAD: brak $ZIP_PATH -- wgraj tam nowe_mapy_gildii.zip albo podaj sciezke jako argument." >&2
  exit 1
fi

echo "== 0/3: kopia zapasowa nadpisywanych plikow =="
mkdir -p "$PANEL_DIR/static/maps.bak-$STAMP" "$PANEL_DIR/static/bak-$STAMP" "$PANEL_DIR/templates/bak-$STAMP"
for f in static/heatmap.js static/live-widget.js static/live-overrides.css; do
  [ -f "$PANEL_DIR/$f" ] && cp -a "$PANEL_DIR/$f" "$PANEL_DIR/static/bak-$STAMP/$(basename "$f")"
done
for f in templates/dashboard.html templates/maps.html; do
  [ -f "$PANEL_DIR/$f" ] && cp -a "$PANEL_DIR/$f" "$PANEL_DIR/templates/bak-$STAMP/$(basename "$f")"
done
echo "OK: kopie w static/bak-$STAMP i templates/bak-$STAMP"

echo "== 1/3: rozpakowywanie nowych plikow =="
TMP_EXTRACT="$(mktemp -d)"
unzip -oq "$ZIP_PATH" -d "$TMP_EXTRACT"
cp -f "$TMP_EXTRACT/static/maps/"*.png "$PANEL_DIR/static/maps/"
cp -f "$TMP_EXTRACT/static/heatmap.js" "$TMP_EXTRACT/static/live-widget.js" "$TMP_EXTRACT/static/live-overrides.css" "$PANEL_DIR/static/"
cp -f "$TMP_EXTRACT/templates/dashboard.html" "$TMP_EXTRACT/templates/maps.html" "$PANEL_DIR/templates/"
rm -rf "$TMP_EXTRACT"
echo "OK: pliki podmienione"

echo "== 2/3: rebuild + restart panelu =="
cd /opt/metin2-mt2009/Serwer/linux-port/docker
docker compose build seban-panel
docker compose up -d seban-panel

echo "== 3/3: gotowe =="
echo "Sprawdz http://57.128.176.139:7790/ (Dashboard) i http://57.128.176.139:7790/maps -- w oknie incognito."
echo "Nowe pozycje w liscie map: Ziemia Klanu Shinsoo, Loch Malp Shinsoo, Ziemia Klanu Jinno, Loch Malp Jinno, Swiatynia Hwang."
echo "Kopie zapasowe: static/bak-$STAMP, templates/bak-$STAMP"
