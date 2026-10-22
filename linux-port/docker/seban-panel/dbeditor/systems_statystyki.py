"""MT2009_NASZE_STATYSTYKI_BOTOW_V1: Kuznia Mocy -> Statystyki botow.

Zrodlo: log.log gry (wpisy BOSS_KILL i STONE_KILL: who = postac, what = potwor, hint = "imperium mapa").
Log jest czyszczony, wiec panel przy kazdym wejsciu dolicza nowe wpisy do wlasnych sum
(spool/systems/statystyki/zabicia.json) - sumy rosna na stale. Boty = konta "playerbot_...".
Dungeon = boss zabity na mapie-instancji (numer mapy >= 10000, mapa bazowa = numer // 10000).
"""
import json
import time
from pathlib import Path

from flask import render_template

PER_RUN = 300000  # najwiecej nowych wpisow logu na jedno wejscie (reszta przy nastepnym)


def install(bp, ctx):
    login = ctx['login_required']
    rows = ctx['rows']
    path = Path(ctx['spool']) / 'systems' / 'statystyki' / 'zabicia.json'

    def load():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {'od': None, 'ostatni': None, 'na_granicy': [], 'potwory': {}, 'dungeony': {}, 'dni': {}}

    def save(s):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(s, ensure_ascii=False), encoding='utf-8')
        tmp.replace(path)

    def bots():
        return {int(r['id']) for r in rows("SELECT p.id FROM player.player p JOIN account.account a ON a.id = p.account_id "
                                           "WHERE BINARY a.login LIKE BINARY %s", ('playerbot\\_%',))}

    def update():
        s = load()
        last = s.get('ostatni')
        where, args = "how IN ('BOSS_KILL', 'STONE_KILL')", ()
        if last:
            where += " AND time >= %s"; args = (last,)
        got = rows("SELECT time, who, what, how, hint FROM log.log WHERE " + where + " ORDER BY time LIMIT %d" % PER_RUN, args)
        if not got:
            return s, 0
        botset = bots()
        edge = set(s.get('na_granicy') or [])
        added, newest, new_edge = 0, last, set()
        for r in got:
            t = str(r['time'])
            key = '%s|%s|%s|%s' % (t, r['who'], r['what'], r['hint'])
            if last and t == last and key in edge:
                continue
            who = int(r['who'] or 0); vnum = int(r['what'] or 0)
            kind = 'boss' if r['how'] == 'BOSS_KILL' else 'metin'
            side = 'bot' if who in botset else 'gracz'
            m = s['potwory'].setdefault(str(vnum), {'rodzaj': kind, 'bot': 0, 'gracz': 0, 'ostatnio': ''})
            m[side] += 1; m['ostatnio'] = t
            day = t[:10]
            d = s['dni'].setdefault(day, {'boss_bot': 0, 'boss_gracz': 0, 'metin_bot': 0, 'metin_gracz': 0})
            d['%s_%s' % (kind, side)] += 1
            if kind == 'boss':
                try:
                    mapidx = int(str(r['hint'] or '').split()[1])
                except (IndexError, ValueError):
                    mapidx = 0
                if mapidx >= 10000:
                    g = s['dungeony'].setdefault(str(mapidx // 10000), {'bot': 0, 'gracz': 0, 'bossy': {}, 'ostatnio': ''})
                    g[side] += 1; g['ostatnio'] = t
                    g['bossy'][str(vnum)] = g['bossy'].get(str(vnum), 0) + 1
            if t != newest:
                newest, new_edge = t, set()
            new_edge.add(key)
            added += 1
        if newest == last:
            new_edge |= edge
        s['ostatni'] = newest
        s['na_granicy'] = sorted(new_edge)
        s['od'] = s.get('od') or str(got[0]['time'])
        s['dni'] = dict(sorted(s['dni'].items())[-60:])
        save(s)
        return s, added

    def names(vnums):
        vnums = sorted({int(v) for v in vnums})
        if not vnums: return {}
        marks = ','.join(['%s'] * len(vnums))
        for table in ('player.mob_proto', 'world.mob_proto'):
            try:
                found = rows('SELECT vnum, CAST(locale_name AS BINARY) AS n FROM ' + table + ' WHERE vnum IN (' + marks + ')', tuple(vnums))
                out = {}
                for r in found:
                    n = r['n']
                    if isinstance(n, (bytes, bytearray)):
                        try: n = bytes(n).decode('utf-8')
                        except UnicodeDecodeError: n = bytes(n).decode('cp1250', 'replace')
                    out[int(r['vnum'])] = str(n or '')
                return out
            except Exception:
                continue
        return {}

    @bp.route('/systemy/statystyki', methods=['GET'])
    @login
    def systems_statystyki():
        error = None
        try:
            s, added = update()
        except Exception as exc:
            s, added, error = load(), 0, str(exc)
        mobs = s.get('potwory') or {}
        name = names(list(mobs.keys()) + [b for g in (s.get('dungeony') or {}).values() for b in g['bossy']])
        def top(kind, side, limit=25):
            items = [(int(v), m) for v, m in mobs.items() if m['rodzaj'] == kind and m[side]]
            items.sort(key=lambda x: -x[1][side])
            return [{'vnum': v, 'name': name.get(v, '#%d' % v), 'n': m[side], 'inni': m['gracz' if side == 'bot' else 'bot'],
                     'ostatnio': m['ostatnio']} for v, m in items[:limit]]
        dung = sorted(((int(k), g) for k, g in (s.get('dungeony') or {}).items()), key=lambda x: -(x[1]['bot'] + x[1]['gracz']))
        dungeons = [{'map': k, 'bot': g['bot'], 'gracz': g['gracz'], 'ostatnio': g['ostatnio'],
                     'bossy': ', '.join('%s ×%d' % (name.get(int(b), '#' + b), n) for b, n in sorted(g['bossy'].items(), key=lambda x: -x[1])[:4])}
                    for k, g in dung[:20]]
        sums = {k: sum(m[side] for m in mobs.values() if m['rodzaj'] == kind) for k, kind, side in
                (('boss_bot', 'boss', 'bot'), ('boss_gracz', 'boss', 'gracz'), ('metin_bot', 'metin', 'bot'), ('metin_gracz', 'metin', 'gracz'))}
        days = list((s.get('dni') or {}).items())[-14:]
        top_day = max([1] + [d['boss_bot'] + d['metin_bot'] for _k, d in days])
        return render_template('dbeditor/systems_statystyki.html', sums=sums, bosses=top('boss', 'bot'), metins=top('metin', 'bot'),
                               dungeons=dungeons, days=days, top_day=top_day, since=s.get('od'), last=s.get('ostatni'),
                               added=added, error=error, sys_active='statystyki', system=None)
