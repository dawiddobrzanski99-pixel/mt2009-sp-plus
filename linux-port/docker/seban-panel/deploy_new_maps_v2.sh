#!/bin/bash
# Round 2 of real in-game map images -- extracted and stitched from
# Klient/pack minimap.dds tiles (same technique as chunjo-m1.png), staged
# directly off the operator's PC this time.
#
# NEW maps (index had bounds already, only the frontend/select was missing):
#   - Shinsoo M1 -- Yongan   (index 1)  -> shinsoo-m1.png
#   - Shinsoo M2 -- Jayang   (index 3)  -> shinsoo-m2.png
#   - Jinno M1   -- Pyongmoo (index 41) -> jinno-m1.png
#   - Jinno M2   -- Bakra    (index 43) -> jinno-m2.png
#
# REPLACED (previously AI-generated from an earlier codex session, now
# swapped for the real extracted map -- same filenames, so no frontend
# wiring changes needed for these three, just new image bytes):
#   - Góra Sohan       (index 61)  -> mount-sohan.png
#   - Loch Pająków V1  (index 104) -> spider-dungeon-v1.png
#   - Świątynia Hwang  (index 65)  -> hwang-temple.png
#
# BEFORE RUNNING:
#   1) Upload nowe_mapy_v2.zip next to this script on the VPS, e.g.
#      /opt/seban-panel-custom/nowe_mapy_v2.zip
#   2) Run: bash /opt/seban-panel-custom/deploy_new_maps_v2.sh
set -euo pipefail

PANEL_DIR="/opt/seban-panel-custom"
ZIP_PATH="${1:-$PANEL_DIR/nowe_mapy_v2.zip}"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -f "$ZIP_PATH" ]; then
  echo "BLAD: brak $ZIP_PATH -- wgraj tam nowe_mapy_v2.zip albo podaj sciezke jako argument." >&2
  exit 1
fi

echo "== 0/3: kopia zapasowa nadpisywanych plikow =="
mkdir -p "$PANEL_DIR/static/bak-$STAMP" "$PANEL_DIR/templates/bak-$STAMP" "$PANEL_DIR/static/maps/bak-$STAMP"
for f in mount-sohan.png spider-dungeon-v1.png hwang-temple.png; do
  [ -f "$PANEL_DIR/static/maps/$f" ] && cp -a "$PANEL_DIR/static/maps/$f" "$PANEL_DIR/static/maps/bak-$STAMP/$f"
done
for f in static/heatmap.js static/live-widget.js static/live-overrides.css; do
  [ -f "$PANEL_DIR/$f" ] && cp -a "$PANEL_DIR/$f" "$PANEL_DIR/static/bak-$STAMP/$(basename "$f")"
done
for f in templates/dashboard.html templates/maps.html; do
  [ -f "$PANEL_DIR/$f" ] && cp -a "$PANEL_DIR/$f" "$PANEL_DIR/templates/bak-$STAMP/$(basename "$f")"
done
echo "OK: kopie w static/maps/bak-$STAMP, static/bak-$STAMP i templates/bak-$STAMP"

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
echo "Nowe: Shinsoo M1/M2, Jinno M1/M2. Podmienione na prawdziwe: Gora Sohan, Loch Pajakow V1, Swiatynia Hwang."
echo "Kopie zapasowe: static/maps/bak-$STAMP, static/bak-$STAMP, templates/bak-$STAMP"
