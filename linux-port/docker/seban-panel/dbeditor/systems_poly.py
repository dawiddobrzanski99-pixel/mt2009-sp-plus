"""MT2009_NASZE_POLIMORFIA_V1: Kuźnia Mocy -> Polimorfia (bonusy i czas przemiany wg poziomu umiejetnosci)."""
import hashlib
import json
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, jsonify, abort
from dbeditor import common_items as common
from dbeditor.systems_store import SystemStore

SCHEMA = 'SEBAN_POLY_V1'
REQUEST_MAGIC = 'SEBAN_POLY_REQUEST_V1'
KEYS = ['attack', 'defense', 'monster', 'resist_monster', 'boss', 'stone', 'speed', 'move', 'duration']
LABELS = ['Wartość ataku', 'Obrona', 'Silny przeciw potworom %', 'Odporność na potwory %', 'Silny przeciw bossom %',
          'Silny przeciw metinom %', 'Szybkość ataku', 'Szybkość ruchu', 'Czas przemiany (s, 0 = z gry)']
SHORT = ['Atak', 'Obrona', 'Potwory %', 'Odp. potwory %', 'Bossy %', 'Metiny %', 'Szyb. ataku', 'Szyb. ruchu', 'Czas (s)']
LIMITS = [1000, 1000, 100, 100, 100, 100, 100, 200, 86400]
# MT2009_NASZE_BONUSY_WSZYSTKIE_V1: poza podstawowymi polami - kazdy bonus z gry (POINT_*), wiersze "B" w silniku.
NATIVE_POINTS = {95, 96, 53, 142, 150, 149, 17, 19}
EXTRA_LIMIT = 100000


def extra_points():
    from m2clientpack.systems_client import point_labels
    return {p: v for p, v in point_labels().items() if p not in NATIVE_POINTS}


def level_name(n):
    if n >= 40: return 'P'
    if n >= 30: return 'G%d' % (n - 29)
    if n >= 20: return 'M%d' % (n - 19)
    return str(n)


def default_row(level):
    # Identyczne z CustomPolyForLevel / CustomPolyDuration (custom_horse_polymorph_rewards.h).
    r = dict.fromkeys(KEYS, 0)
    if level >= 40:
        r.update(attack=150, defense=150, monster=15, resist_monster=15, boss=30, stone=30, speed=15, move=65, duration=3600)
    elif level <= 29:
        r['attack'] = level * 50 // 29; r['defense'] = level * 50 // 29
        if level >= 20: r['speed'] = 5
    else:
        g = level - 29
        r.update(attack=50 + g * 3, defense=50 + g * 2, monster=g, resist_monster=g, speed=5 + g // 2, duration=1800)
    from m2clientpack import kuznia_dodatki
    if kuznia_dodatki.fresh():  # MT2009_NASZE_SWIEZY_START_V1: bez bonusow, czas przemiany jak w grze
        r = {k: (v if k == 'duration' else 0) for k, v in r.items()}
    return r


def defaults():
    return {'schema': SCHEMA, 'master_enabled': True, 'enabled': True,
            'levels': [dict(level=n, values=default_row(n)) for n in range(1, 41)], 'extra': {}}


def validate(cfg):
    if not isinstance(cfg, dict): raise ValueError('Nieprawidłowa konfiguracja.')
    levels = cfg.get('levels')
    if not isinstance(levels, list) or len(levels) != 40: raise ValueError('Wymagane 40 poziomów.')
    out = []
    for i, row in enumerate(levels, 1):
        if not isinstance(row, dict) or row.get('level') != i: raise ValueError('Nieprawidłowa kolejność poziomów.')
        values = {}
        for k, limit in zip(KEYS, LIMITS):
            v = row.get('values', {}).get(k, 0)
            if type(v) is not int or not 0 <= v <= limit: raise ValueError('Poziom %s: wartość „%s” poza zakresem 0–%d.' % (level_name(i), k, limit))
            values[k] = v
        out.append(dict(level=i, values=values))
    allowed = extra_points(); extra = {}
    raw_extra = cfg.get('extra') or {}
    if not isinstance(raw_extra, dict): raise ValueError('Nieprawidłowe dodatkowe bonusy.')
    for lvl, points in raw_extra.items():
        if not str(lvl).isdigit() or not 1 <= int(lvl) <= 40 or not isinstance(points, dict): raise ValueError('Nieprawidłowy poziom dodatkowych bonusów.')
        row = {}
        for p, v in points.items():
            if not str(p).isdigit() or int(p) not in allowed: raise ValueError('Poziom %s: nieznany bonus #%s.' % (level_name(int(lvl)), p))
            if type(v) is not int or not 0 <= v <= EXTRA_LIMIT: raise ValueError('Poziom %s: wartość bonusu „%s” poza zakresem 0–%d.' % (level_name(int(lvl)), allowed[int(p)][0], EXTRA_LIMIT))
            if v: row[str(int(p))] = v
        if row: extra[str(int(lvl))] = row
    return {'schema': SCHEMA, 'master_enabled': bool(cfg.get('master_enabled')), 'enabled': bool(cfg.get('enabled')), 'levels': out, 'extra': extra}


def canonical(cfg):
    return json.dumps(validate(cfg), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(cfg):
    return hashlib.sha256(canonical(cfg)).hexdigest()


def engine_body(cfg):
    cfg = validate(cfg)
    lines = ['%d %d' % (int(cfg['master_enabled']), int(cfg['enabled']))]
    for row in cfg['levels']:
        lines.append(' '.join([str(row['level'])] + [str(row['values'][k]) for k in KEYS]))
    for lvl in sorted(cfg['extra'], key=int):
        for p in sorted(cfg['extra'][lvl], key=int):
            lines.append('B %s %s %d' % (lvl, p, cfg['extra'][lvl][p]))
    return ('\n'.join(lines) + '\n').encode('ascii')


def engine_revision(cfg):
    return hashlib.sha256(engine_body(cfg)).hexdigest()


def command(cfg, operation):
    body = engine_body(cfg)
    return ('%s %s\n%s %s\n' % (REQUEST_MAGIC, operation, SCHEMA, hashlib.sha256(body).hexdigest())).encode('ascii') + body


class _Codec:
    pass


codec = _Codec()
for _n in ('SCHEMA', 'REQUEST_MAGIC', 'defaults', 'validate', 'canonical', 'revision', 'engine_revision', 'command'):
    setattr(codec, _n, globals()[_n])


def parse_form(store):
    cfg = store.read()
    cfg['master_enabled'] = request.form.get('master_enabled') == '1'
    cfg['enabled'] = request.form.get('enabled') == '1'
    bonus_keys = [k for k in KEYS if k != 'duration']
    allowed = extra_points(); cfg['extra'] = {}
    for row in cfg['levels']:
        n = row['level']; name = level_name(n)
        raw = request.form.get('v_%d_duration' % n, '0').strip() or '0'
        if not raw.isdigit(): raise ValueError('Poziom %s: czas musi być liczbą.' % name)
        row['values'] = dict.fromkeys(KEYS, 0); row['values']['duration'] = int(raw)
        keys = request.form.getlist('bk_%d' % n); values = request.form.getlist('bv_%d' % n)
        def known(k): return k in bonus_keys or (k[:1] == 'p' and k[1:].isdigit() and int(k[1:]) in allowed)
        if len(keys) != len(values) or len(set(keys)) != len(keys) or not all(known(k) for k in keys):
            raise ValueError('Poziom %s: nieprawidłowy lub powtórzony bonus.' % name)
        for k, v in zip(keys, values):
            v = v.strip() or '0'
            if not v.isdigit(): raise ValueError('Poziom %s: wartość „%s” musi być liczbą.' % (name, v))
            if k in bonus_keys: row['values'][k] = int(v)
            elif int(v): cfg['extra'].setdefault(str(n), {})[k[1:]] = int(v)
    return validate(cfg)


def install(bp, ctx):
    store = SystemStore(Path(ctx['spool']) / 'systems/polimorfia', codec, ctx.get('boot_plan'))
    login = ctx['login_required']

    @bp.route('/systemy/polimorfia', methods=['GET', 'POST'])
    @login
    def systems_polimorfia():
        if request.method == 'POST':
            if not common.check_csrf(): abort(403)
            try:
                expected = request.form.get('revision', ''); action = request.form.get('action')
                if action in ('save', 'save_apply'):
                    cfg = parse_form(store)
                    if action == 'save_apply':
                        store.save_apply(cfg, expected)
                        flash('Zapisano i przekazano do kanałów. Czekamy na potwierdzenia — bez restartu.', 'info')
                    else:
                        store.save(cfg, expected); flash('Zapisano projekt. Serwer jeszcze go nie zastosował.', 'info')
                elif action == 'apply':
                    store.apply(expected); flash('Przekazano konfigurację do kanałów.', 'info')
                elif action == 'defaults':
                    store.save(defaults(), expected); flash('Przywrócono wartości domyślne do projektu. Zastosuj, aby działały w grze.', 'success')
                elif action == 'undo':
                    store.undo(expected); flash('Przywrócono poprzedni projekt. Zastosuj, aby działał w grze.', 'success')
                else: abort(400)
            except (ValueError, KeyError) as exc: flash(str(exc), 'error')
            except Exception:
                ctx['app'].logger.exception('Polymorph editor failed'); flash('Operacja nie została potwierdzona. Sprawdź logi panelu.', 'error')
            return redirect(url_for('dbeditor.systems_polimorfia'))
        with store.locked(): cfg = store.read()
        groups = [('Poziomy 1–19', cfg['levels'][0:19]), ('Mistrz (M1–M10)', cfg['levels'][19:29]),
                  ('Arcymistrz (G1–G10)', cfg['levels'][29:39]), ('Perfekcja (P)', cfg['levels'][39:40])]
        cfg = validate(cfg)
        opts = [dict(k=k, s=s, l=l, m=m) for k, s, l, m in zip(KEYS, SHORT, LABELS, LIMITS) if k != 'duration']
        opts += [dict(k='p%d' % p, s=n, l=n + (' (%s)' % u.replace('‰', '‰ = 1/10 %') if u else ''), m=EXTRA_LIMIT, all=1)
                 for p, (n, u) in sorted(extra_points().items(), key=lambda x: x[1][0])]
        init = {r['level']: [[k, r['values'][k]] for k in KEYS if k != 'duration' and r['values'][k]]
                + [['p' + p, v] for p, v in sorted(cfg['extra'].get(str(r['level']), {}).items(), key=lambda x: int(x[0]))]
                for r in cfg['levels']}
        return render_template('dbeditor/systems_poly.html', config=cfg, groups=groups, revision=revision(cfg),
                               bonus_opts=opts, bonus_init=init,
                               cols=list(zip(KEYS, SHORT, LABELS, LIMITS)), level_name=level_name,
                               status=store.status(), dbe_csrf=common.csrf_token(), sys_active='polimorfia')

    @bp.route('/systemy/polimorfia/status')
    @login
    def systems_polimorfia_status():
        return jsonify(store.status())
