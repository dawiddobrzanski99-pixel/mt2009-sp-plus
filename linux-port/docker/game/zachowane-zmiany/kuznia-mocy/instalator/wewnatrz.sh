#!/bin/sh
# Kuznia Mocy: czesc instalatora uruchamiana w kontenerze (python + patch), wspolna dla VPS i PC.
#   /srv = folder linux-port serwera, /pkg = paczka Kuzni, /kopie = kopie zapasowe
set -e
export DEBIAN_FRONTEND=noninteractive
command -v patch >/dev/null 2>&1 || { apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq patch >/dev/null 2>&1; }
GAME=/srv/docker/game/src/server/game/src
PANEL=/srv/docker/seban-panel
[ -d "$GAME" ] || { echo "BLAD: nie ma $GAME - to nie jest folder serwera MT2009 (linux-port)"; exit 2; }
[ -f "$PANEL/dbeditor/__init__.py" ] || { echo "BLAD: nie ma panelu Seban w $PANEL"; exit 2; }
T=$(date +%Y%m%d-%H%M%S)
echo "==> Kopia zapasowa: kopie/kuznia-przed-$T.tgz"
tar -czf "/kopie/kuznia-przed-$T.tgz" --exclude='*.o' --exclude='__pycache__' -C /srv docker/game/src/server/game/src docker/seban-panel
echo "==> Ranking tygodnia: bonusy z gry tego serwera"
W="$GAME/playerbot_weekly_rank.h"; [ -f "$GAME/.kuznia-oryginal/playerbot_weekly_rank.h" ] && grep -q 'SebanWeekly' "$W" && W="$GAME/.kuznia-oryginal/playerbot_weekly_rank.h"
python3 /pkg/czytaj_ranking.py "$W" /tmp/ranking-serwera.json || true
echo "==> Silnik gry: latki Kuzni"
if ! sh /pkg/naloz_latki.sh /pkg/silnik "$GAME"; then
  echo "BLAD: czesc latek silnika nie weszla (wyzej). Nic nie budowano. Przywrocenie: rozpakuj kopie z folderu kopie/."
  exit 3
fi
echo "==> Panel: moduly Kuzni"
python3 /pkg/instaluj_panel.py /pkg/panel "$PANEL"
[ -f /tmp/ranking-serwera.json ] && cp /tmp/ranking-serwera.json "$PANEL/m2clientpack/kuznia_dodatki/ranking-serwera.json"
echo "==> Pliki gotowe"
