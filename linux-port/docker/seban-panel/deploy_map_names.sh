#!/bin/bash
# Renames the three "Ziemia Klanu X" map labels to the M1/M2-consistent
# "[Krolestwo] M3 -- Nazwa" style, everywhere they appear:
#   Ziemia Klanu Shinsoo -> Shinsoo M3 -- Jungrang
#   Ziemia Klanu Jinno   -> Jinno M3 -- Imha
#   Ziemia Klanu Chunjo  -> Chunjo M3 -- Waryong  (app.py backend only --
#     the frontend already said "Chunjo M3 -- Waryong", app.py's own
#     MAP_NAMES/MAP_RESPAWN_OPTIONS were the only place still saying
#     "Ziemia Klanu Chunjo")
#
# This patches app.py IN PLACE with sed rather than shipping a whole new
# app.py, since that file may have other changes made directly on the VPS
# since this repo mirror was last synced -- a full overwrite risks
# clobbering those. static/*.js and templates/*.html are shipped whole
# since they're small and self-contained.
#
# BEFORE RUNNING:
#   1) Upload nazwy_map_m3.zip next to this script, e.g.
#      /opt/seban-panel-custom/nazwy_map_m3.zip
#   2) Run: bash /opt/seban-panel-custom/deploy_map_names.sh
set -euo pipefail

PANEL_DIR="/opt/seban-panel-custom"
ZIP_PATH="${1:-$PANEL_DIR/nazwy_map_m3.zip}"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -f "$ZIP_PATH" ]; then
  echo "BLAD: brak $ZIP_PATH -- wgraj tam nazwy_map_m3.zip albo podaj sciezke jako argument." >&2
  exit 1
fi
if [ ! -f "$PANEL_DIR/app.py" ]; then
  echo "BLAD: brak $PANEL_DIR/app.py" >&2
  exit 1
fi

echo "== 0/3: kopia zapasowa =="
mkdir -p "$PANEL_DIR/static/bak-$STAMP" "$PANEL_DIR/templates/bak-$STAMP"
cp -a "$PANEL_DIR/static/heatmap.js" "$PANEL_DIR/static/bak-$STAMP/" 2>/dev/null || true
cp -a "$PANEL_DIR/static/live-widget.js" "$PANEL_DIR/static/bak-$STAMP/" 2>/dev/null || true
cp -a "$PANEL_DIR/templates/dashboard.html" "$PANEL_DIR/templates/bak-$STAMP/" 2>/dev/null || true
cp -a "$PANEL_DIR/templates/maps.html" "$PANEL_DIR/templates/bak-$STAMP/" 2>/dev/null || true
cp -a "$PANEL_DIR/app.py" "$PANEL_DIR/app.py.bak-$STAMP"
echo "OK: kopie w static/bak-$STAMP, templates/bak-$STAMP, app.py.bak-$STAMP"

echo "== 1/3: rozpakowywanie static/templates =="
TMP_EXTRACT="$(mktemp -d)"
unzip -oq "$ZIP_PATH" -d "$TMP_EXTRACT"
cp -f "$TMP_EXTRACT/static/heatmap.js" "$TMP_EXTRACT/static/live-widget.js" "$PANEL_DIR/static/"
cp -f "$TMP_EXTRACT/templates/dashboard.html" "$TMP_EXTRACT/templates/maps.html" "$PANEL_DIR/templates/"
rm -rf "$TMP_EXTRACT"

echo "== 2/3: podmiana nazw w app.py (sed, w miejscu) =="
sed -i 's/Ziemia Klanu Shinsoo/Shinsoo M3 — Jungrang/g; s/Ziemia Klanu Jinno/Jinno M3 — Imha/g; s/Ziemia Klanu Chunjo/Chunjo M3 — Waryong/g' "$PANEL_DIR/app.py"
grep -n "Jungrang\|Imha\|M3 — Waryong" "$PANEL_DIR/app.py" || echo "UWAGA: sed nic nie znalazl -- sprawdz czy app.py juz mial inne nazwy."

echo "== 3/3: rebuild + restart panelu =="
cd /opt/metin2-mt2009/Serwer/linux-port/docker
docker compose build seban-panel
docker compose up -d seban-panel

echo "Gotowe. Sprawdz http://57.128.176.139:7790/ i /maps -- w oknie incognito."
echo "Kopie zapasowe: static/bak-$STAMP, templates/bak-$STAMP, app.py.bak-$STAMP"
