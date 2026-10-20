"""MT2009_NASZE_RANKING_V1: Kuźnia Mocy -> Ranking tygodnia (bonusy tytulow: 8 kategorii x miejsca 1-3, dowolne bonusy z gry).
Slot = (kategoria-1)*3 + miejsce (1-24). Gracz z kilkoma tytulami dostaje sume ich bonusow."""
import hashlib
import json
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, jsonify, abort
from dbeditor import common_items as common
from dbeditor.systems_store import SystemStore

SCHEMA = 'SEBAN_WEEKLY_V1'
REQUEST_MAGIC = 'SEBAN_WEEKLY_REQUEST_V1'
SLOTS = 24
LIMIT = 100000
CATEGORIES = [('Łowca', 'Potwory', '🐺'), ('Niszczyciel', 'Metiny', '🪨'), ('Pogromca Bossów', 'Bossy', '👹'), ('Zabójca', 'Gracze', '⚔️'),
              ('Podróżnik', 'Wyprawy', '🗺️'), ('Kowal', 'Ulepszenia', '🔨'), ('Alchemik', 'Alchemia', '⚗️'), ('Mistrz Poziomów', 'Poziom', '📈')]
ROMAN = ['', 'I', 'II', 'III']


def slot_name(n):
    cat, place = (n - 1) // 3, (n - 1) % 3 + 1
    return '%s %s (%s, miejsce %d)' % (CATEGORIES[cat][0], ROMAN[place], CATEGORIES[cat][1], place)


def points():
    from m2clientpack.systems_client import point_labels
    return point_labels()


def default_slot(n):
    # Identyczne z Bonus() w playerbot_weekly_rank.h (CUSTOM_WEEKLY_REWARDS_V2).
    cat, place = (n - 1) // 3 + 1, (n - 1) % 3 + 1
    from m2clientpack import kuznia_dodatki
    if kuznia_dodatki.fresh():
        # MT2009_NASZE_SWIEZY_START_V1: bonusy z gry tego serwera (instalator czyta playerbot_weekly_rank.h),
        # a bez tego pliku - jak w grze autora serwera.
        try:
            import json
            row = json.loads((kuznia_dodatki.BASE / 'ranking-serwera.json').read_text()).get(str(n))
            if row is not None: return dict(row)
        except (OSError, ValueError):
            pass
        pct, hp = [0, 15, 8, 4][place], [0, 2500, 2000, 1500][place]
        return dict({1: {'53': pct}, 2: {'53': pct}, 5: {'53': pct}, 3: {'150': pct}, 4: {'43': pct},
                     8: {'53': pct, '43': pct}, 6: {'6': hp}, 7: {'95': 75}}[cat])
    pve, pct, hp = [0, 10, 5, 3][place], [0, 15, 8, 4][place], [0, 2500, 2000, 1500][place]
    return dict({1: {'53': pve}, 2: {'53': pve}, 5: {'53': pve}, 3: {'150': pve}, 4: {'43': pct},
                 8: {'53': pct, '43': pct}, 6: {'6': hp}, 7: {'95': 50}}[cat])


def defaults():
    return {'schema': SCHEMA, 'master_enabled': True, 'enabled': True, 'slots': {str(n): default_slot(n) for n in range(1, SLOTS + 1)}}


def validate(cfg):
    if not isinstance(cfg, dict) or not isinstance(cfg.get('slots'), dict): raise ValueError('Nieprawidłowa konfiguracja rankingu.')
    allowed = points(); slots = {}
    for lvl, row in cfg['slots'].items():
        if not str(lvl).isdigit() or not 1 <= int(lvl) <= SLOTS or not isinstance(row, dict): raise ValueError('Nieprawidłowy tytuł rankingu.')
        out = {}
        for p, v in row.items():
            if not str(p).isdigit() or int(p) not in allowed: raise ValueError('%s: nieznany bonus #%s.' % (slot_name(int(lvl)), p))
            if type(v) is not int or not 0 <= v <= LIMIT: raise ValueError('%s: „%s” poza zakresem 0–%d.' % (slot_name(int(lvl)), allowed[int(p)][0], LIMIT))
            if v: out[str(int(p))] = v
        slots[str(int(lvl))] = out
    for n in range(1, SLOTS + 1): slots.setdefault(str(n), {})
    return {'schema': SCHEMA, 'master_enabled': bool(cfg.get('master_enabled')), 'enabled': bool(cfg.get('enabled')), 'slots': slots}


def canonical(cfg):
    return json.dumps(validate(cfg), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(cfg):
    return hashlib.sha256(canonical(cfg)).hexdigest()


def engine_body(cfg):
    cfg = validate(cfg)
    lines = ['%d %d' % (int(cfg['master_enabled']), int(cfg['enabled']))]
    for lvl in sorted(cfg['slots'], key=int):
        for p in sorted(cfg['slots'][lvl], key=int): lines.append('B %s %s %d' % (lvl, p, cfg['slots'][lvl][p]))
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
    cfg = store.read(); allowed = points()
    cfg['master_enabled'] = request.form.get('master_enabled') == '1'
    cfg['enabled'] = request.form.get('enabled') == '1'
    cfg['slots'] = {}
    for n in range(1, SLOTS + 1):
        keys = request.form.getlist('bk_%d' % n); values = request.form.getlist('bv_%d' % n)
        if len(keys) != len(values) or len(set(keys)) != len(keys) or not all(k.isdigit() and int(k) in allowed for k in keys):
            raise ValueError('%s: nieprawidłowy lub powtórzony bonus.' % slot_name(n))
        row = {}
        for k, v in zip(keys, values):
            v = v.strip() or '0'
            if not v.isdigit(): raise ValueError('%s: wartość „%s” musi być liczbą.' % (slot_name(n), v))
            if int(v): row[k] = int(v)
        cfg['slots'][str(n)] = row
    return validate(cfg)


def install(bp, ctx):
    store = SystemStore(Path(ctx['spool']) / 'systems/ranking', codec, ctx.get('boot_plan'))
    login = ctx['login_required']

    @bp.route('/systemy/ranking', methods=['GET', 'POST'])
    @login
    def systems_ranking():
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
                ctx['app'].logger.exception('Weekly editor failed'); flash('Operacja nie została potwierdzona. Sprawdź logi panelu.', 'error')
            return redirect(url_for('dbeditor.systems_ranking'))
        with store.locked(): cfg = store.read()
        opts = [dict(k=str(p), l=n + (' (%s)' % u.replace('‰', '‰ = 1/10 %') if u else ''), s=n) for p, (n, u) in sorted(points().items(), key=lambda x: x[1][0])]
        init = {n: [[p, v] for p, v in sorted(cfg['slots'][str(n)].items(), key=lambda x: int(x[0]))] for n in range(1, SLOTS + 1)}
        groups = [(c, [dict(n=i * 3 + pl, place=pl, roman=ROMAN[pl], name=slot_name(i * 3 + pl)) for pl in (1, 2, 3)]) for i, c in enumerate(CATEGORIES)]
        return render_template('dbeditor/systems_weekly.html', config=cfg, revision=revision(cfg), opts=opts, init=init,
                               limit=LIMIT, groups=groups, status=store.status(), dbe_csrf=common.csrf_token(), sys_active='ranking', system=None)

    @bp.route('/systemy/ranking/status')
    @login
    def systems_ranking_status():
        return jsonify(store.status())
