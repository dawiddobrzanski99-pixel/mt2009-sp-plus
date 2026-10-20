#!/bin/sh
# Kuznia Mocy: zbiera pakiet panelu z dzialajacego serwera (u autora Kuzni).
# Uzycie: spakuj_panel.sh SEBAN_PANEL SPOOL_SYSTEMS ROOT_AUTORA WYJSCIE
#   ROOT_AUTORA = katalog z root.index + root.data (oryginalny ROOT, z ktorego biora sie dodatki klienta)
set -e
L=$1; SP=$2; R=$3; P=$4; H=$(cd "$(dirname "$0")" && pwd)
rm -rf "$P"; mkdir -p "$P/pliki/dbeditor" "$P/pliki/templates/dbeditor" "$P/pliki/m2clientpack/kuznia_dodatki"
P=$(cd "$P" && pwd); L=$(cd "$L" && pwd); R=$(cd "$R" && pwd)
cp "$L"/dbeditor/systems_*.py "$P/pliki/dbeditor/"
cp "$L"/templates/dbeditor/systems_*.html "$L/templates/dbeditor/_systems_nav.html" "$P/pliki/templates/dbeditor/"
for f in systems_client horse_editor horse_publication horse_pair_installer kuznia_dodatki; do cp "$L/m2clientpack/$f.py" "$P/pliki/m2clientpack/"; done
grep -E '__import__\("dbeditor\.systems_' "$L/dbeditor/__init__.py" > "$P/init.txt"
awk "/'mark': 'MT2009_NASZE_SYSTEMY_V1'/{f=1} f{print} f&&/^  \]\},/{exit}" "$L/templates/_nav.html" > "$P/nav.txt"
# Dodatki ROOT (moduly, grafiki, podpiecia) z ROOT autora - w obrazie panelu (eterpack).
docker run --rm -v "$R":/root-src:ro -v "$H":/k:ro -v "$L":/app:ro -v "$P/pliki/m2clientpack/kuznia_dodatki":/wyj \
  --entrypoint python metin2/seban-panel:latest /k/spakuj_klient.py /root-src /wyj
# Bez ustawien autora Kuzni: kazdy zaczyna od zera (karta "Ustawienia autora" sie nie pokazuje).
# Znacznik swiezego startu: domyslnie zero bonusow + jednorazowe wyzerowanie po instalacji.
echo 1 > "$P/pliki/m2clientpack/kuznia_dodatki/swiezy-start"
echo "pakiet panelu: $(find "$P/pliki" -type f | wc -l) plikow, $(wc -l < "$P/init.txt") modulow"
