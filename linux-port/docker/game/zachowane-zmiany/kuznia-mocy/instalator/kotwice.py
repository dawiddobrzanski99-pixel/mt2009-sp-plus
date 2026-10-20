#!/usr/bin/env python3
"""Kuznia Mocy: dla pliku, ktorego latka nie weszla w calosci, dokleja brakujace bloki Kuzni przy stalych liniach.
Uzycie: kotwice.py PLIK_KOTWIC.json PLIK_ZRODLA   (kod 0 = wszystko jest, 1 = nie znaleziono kotwicy)"""
import json, sys

rules = json.load(open(sys.argv[1], encoding='latin-1'))
path = sys.argv[2]
text = open(path, encoding='latin-1').read()
bad = 0
for r in rules:
    if r['marker'] in text:
        continue  # blok juz jest (latka weszla)
    L = text.splitlines(keepends=True)
    k = next((i for i, x in enumerate(L) if x.startswith(r['anchor'])), None)
    if k is None:
        print('BRAK KOTWICY: %s -> %s' % (path, r['anchor'].strip())); bad = 1; continue
    if r['where'] == 'po': k += 1
    L.insert(k, r['block'])
    text = ''.join(L)
    print('KOTWICA OK: %s' % r['marker'][:60])
open(path, 'w', encoding='latin-1').write(text)
sys.exit(bad)
