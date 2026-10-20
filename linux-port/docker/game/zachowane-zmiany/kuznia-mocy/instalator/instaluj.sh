#!/bin/sh
# Kuznia Mocy - instalator na VPS / Linux.  Uzycie:  sudo sh instaluj.sh [FOLDER_SERWERA]
# FOLDER_SERWERA = folder z linux-port (domyslnie szukany: /opt/metin2, /root/metin2, biezacy).
# Mozna uruchamiac wiele razy, np. po kazdej aktualizacji serwera - zaczyna od oryginalow autora.
set -e
PKG=$(cd "$(dirname "$0")" && pwd)
S=${1:-}
if [ -z "$S" ]; then
  for c in /opt/metin2 /root/metin2 "$PWD" "$PWD/.."; do [ -f "$c/linux-port/docker/docker-compose.yml" ] && { S=$c; break; }; done
fi
[ -n "$S" ] && [ -f "$S/linux-port/docker/docker-compose.yml" ] || { echo "Nie znaleziono serwera. Podaj folder: sh instaluj.sh /sciezka/do/serwera"; exit 2; }
S=$(cd "$S" && pwd)
command -v docker >/dev/null || { echo "Brak Dockera."; exit 2; }
echo "==> Kuznia Mocy $(cat "$PKG/WERSJA" 2>/dev/null) -> $S"
mkdir -p "$PKG/kopie"
docker run --rm -v "$S/linux-port":/srv -v "$PKG":/pkg:ro -v "$PKG/kopie":/kopie python:3.12-slim sh /pkg/wewnatrz.sh
echo "==> Budowa gry i panelu (pierwszy raz kilkanascie minut)"
cd "$S/linux-port/docker"
docker compose build game seban-panel
docker compose up -d
echo
echo "GOTOWE. Panel -> Kuznia Mocy. Dalej:"
echo " 1) Kuznia Mocy: wszystkie systemy startuja od zera - ustaw je po swojemu."
echo " 2) Przeglad -> Klient (ROOT): wgraj swoj root.index + root.data, pobierz gotowy ROOT i podmien w kliencie."
