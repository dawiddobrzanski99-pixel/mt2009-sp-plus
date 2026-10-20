#!/bin/sh
# Kuznia Mocy: sklada paczke instalatora z dzialajacego serwera autora Kuzni.
# Uzycie: zbuduj_paczke.sh CZYSTE_ZRODLA_GRY_AUTORA ROOT_AUTORA [WYJSCIE]
#   CZYSTE_ZRODLA_GRY_AUTORA - game/src czystej wersji autora serwera (baza roznic)
#   ROOT_AUTORA - katalog z oryginalnym root.index + root.data autora Kuzni
set -e
H=$(cd "$(dirname "$0")" && pwd)
C=$1; R=$2; OUT=${3:-$H/paczka}
LIVE=/opt/metin2/linux-port/docker
W=$(date +%Y.%m.%d-%H%M)
P="$OUT/kuznia-mocy"
rm -rf "$OUT"; mkdir -p "$P"
python3 "$H/zbuduj_latki.py" "$C" "$LIVE/game/src/server/game/src" "$P/silnik" > "$P/RAPORT-silnik.txt"
sh "$H/spakuj_panel.sh" "${PANEL_SRC:-$LIVE/seban-panel}" /var/lib/docker/volumes/metin2_rates-spool/_data/systems "$R" "$P/panel"
for f in naloz_latki.sh kotwice.py instaluj_panel.py czytaj_ranking.py wewnatrz.sh instaluj.sh instaluj.ps1; do sed 's/\r$//' "$H/$f" > "$P/$f"; done
sed 's/\r$//; s/$/\r/' "$H/instaluj.bat" > "$P/instaluj.bat"
sed 's/\r$//; s/$/\r/' "$H/CZYTAJ.txt" > "$P/CZYTAJ.txt"
echo "$W" > "$P/WERSJA"
cd "$OUT"; rm -f kuznia-mocy-*.zip
python3 -c "import shutil,sys; shutil.make_archive(sys.argv[1],'zip','.', 'kuznia-mocy')" "kuznia-mocy-$W"
echo "PACZKA: $OUT/kuznia-mocy-$W.zip ($(du -h "$OUT/kuznia-mocy-$W.zip" | cut -f1))"
