#!/usr/bin/env python3
"""Kuznia Mocy: bonusy rankingu tygodnia z plikow gry serwera (przed latkami) -> domyslne w panelu.
Uzycie: czytaj_ranking.py playerbot_weekly_rank.h WYJSCIE.json"""
import json, re, sys

src = open(sys.argv[1], encoding='latin-1').read()


def table(name, default):
    m = re.search(r'%s\s*\[[^\]]*\]\s*=\s*\{([^}]*)\}' % name, src)
    try:
        v = [int(x) for x in m.group(1).split(',')]
        return v if len(v) >= 4 else default
    except (AttributeError, ValueError):
        return default

pct = table('PCT_BY_PLACE', [0, 15, 8, 4])
hp = table('HP_BY_PLACE', [0, 2500, 2000, 1500])
att = table('ATT_BY_PLACE', [0, 75, 75, 75])
slots = {}
for n in range(1, 25):
    cat, place = (n - 1) // 3 + 1, (n - 1) % 3 + 1
    row = {1: {'53': pct[place]}, 2: {'53': pct[place]}, 5: {'53': pct[place]}, 3: {'150': pct[place]},
           4: {'43': pct[place]}, 8: {'53': pct[place], '43': pct[place]}, 6: {'6': hp[place]}, 7: {'95': att[place]}}[cat]
    slots[str(n)] = {p: v for p, v in row.items() if v}
json.dump(slots, open(sys.argv[2], 'w'), indent=1)
print('ranking tygodnia z gry serwera: %% %s, HP %s, atak %s' % (pct[1:4], hp[1:4], att[1:4]))
