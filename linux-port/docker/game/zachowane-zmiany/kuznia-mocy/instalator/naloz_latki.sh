#!/bin/sh
# Kuznia Mocy: naklada latki silnika na zrodla gry. Uzycie: naloz_latki.sh KATALOG_SILNIKA(latki+nowe+kotwice) KATALOG_ZRODEL_GRY
# Konce linii CRLF w plikach autora sa zamieniane na LF (kompilator to przyjmuje, patch inaczej sie gubi).
# Oryginaly autora trzymane w .kuznia-oryginal/: ponowne uruchomienie zaczyna od nich (latki nie wchodza dwa razy);
# plik bez sladu Kuzni (np. po aktualizacji serwera) staje sie nowym oryginalem.
S=$1; G=$2; bad=0; O="$G/.kuznia-oryginal"
mkdir -p "$O"
cp "$S"/nowe/* "$G"/
for p in "$S"/latki/*.diff; do
  n=$(basename "$p" .diff); f="$G/$n"; k="$S/kotwice/$n.json"
  [ -f "$f" ] || { echo "BLAD latki: brak pliku $n"; bad=1; continue; }
  # Plik dokladnie taki, jak go zostawila poprzednia instalacja -> zaczynamy od oryginalu autora.
  if [ -f "$O/$n" ] && [ -f "$O/$n.po" ] && [ "$(sha256sum < "$f")" = "$(cat "$O/$n.po")" ]; then
    cp "$O/$n" "$f"
  else
    cp "$f" "$O/$n"
  fi
  sed -i 's/\r$//' "$f"
  if patch -s -p1 -l -F3 -N -d "$G" < "$p" >/dev/null; then :
  elif [ -f "$k" ] && python3 "$(dirname "$0")/kotwice.py" "$k" "$f"; then echo "latka $n: czesc przez kotwice - OK"
  else echo "BLAD latki: $n"; bad=1; fi
  sha256sum < "$f" > "$O/$n.po"
done
find "$G" -maxdepth 1 \( -name '*.rej' -o -name '*.orig' \) -delete
exit $bad
