#!/usr/bin/env python3
"""Kuznia Mocy: ustawienia autora (jak "Pobierz kopie" w panelu) do paczki instalatora.
Uzycie: spakuj_ustawienia.py KATALOG_SPOOL/systems WYJSCIE.zip"""
import json, sys, time, zipfile
from pathlib import Path

# Bez 'rangi': kazdy zaczyna od rang wlasnej gry (rangi autora Kuzni nie sa rozdawane).
SYSTEMS = ['horse', 'polimorfia', 'gildia', 'ranking', 'misje']
spool, out = Path(sys.argv[1]), sys.argv[2]
meta = dict(schema='KUZNIA_MOCY_KOPIA_V1', created=time.strftime('%Y-%m-%d %H:%M:%S'), systems=[])
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for key in SYSTEMS:
        d = spool / key
        if (d / 'draft.json').exists():
            z.writestr('%s/draft.json' % key, (d / 'draft.json').read_bytes()); meta['systems'].append(key)
        if (d / 'assets').is_dir():
            for f in sorted((d / 'assets').iterdir()):
                if f.is_file() and f.suffix.lower() == '.tga' and f.stat().st_size <= 4 * 1024 * 1024:
                    z.writestr('%s/assets/%s' % (key, f.name), f.read_bytes())
    if (spool / 'plus9' / 'config.txt').exists():
        z.writestr('plus9/config.txt', (spool / 'plus9' / 'config.txt').read_bytes())
    z.writestr('kuznia-mocy.json', json.dumps(meta, ensure_ascii=False, indent=2))
print('ustawienia autora: %s' % ', '.join(meta['systems']))
