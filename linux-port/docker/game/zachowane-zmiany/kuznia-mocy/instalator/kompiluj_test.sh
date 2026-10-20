#!/bin/sh
# Kompilacja probna drzewa testowego (game-src + common) w osobnym kontenerze buildera. Uzycie: kompiluj_test.sh KATALOG
T=$1; N=kuznia-test-build
docker rm -f $N >/dev/null 2>&1
docker run -d --name $N --entrypoint sleep metin2/game:horse-v2-builder-cache-20261020-164141 infinity >/dev/null
for d in game/src common; do docker exec $N sh -c "find /src/Server/$d -maxdepth 1 -type f \( -name '*.cpp' -o -name '*.h' -o -name '*.hpp' -o -name '*.inc' \) -delete"; done
docker cp $T/game-src/. $N:/src/Server/game/src/
docker cp $T/common/. $N:/src/Server/common/
docker exec $N sh -c 'rm -f /src/Server/game/src/.obj/*.o /src/Server/game/src/.obj/*.d; cd /src/Server && make -k -C game/src -j4 $M2_MAKE' > $T/kompilacja.log 2>&1
echo "kod=$?"
grep -E 'error' $T/kompilacja.log | grep -v 'Error 1' | sort -u | head -40
tail -2 $T/kompilacja.log
docker rm -f $N >/dev/null
