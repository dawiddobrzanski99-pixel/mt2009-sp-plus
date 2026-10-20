"""MT2009_NASZE_GILDIA_V1: Kuźnia Mocy -> Gildia (bonusy czlonkow wg poziomu gildii 1-20, dowolne bonusy z gry)."""
import hashlib
import json
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, jsonify, abort
from dbeditor import common_items as common
from dbeditor.systems_store import SystemStore

SCHEMA = 'SEBAN_GUILD_V1'
REQUEST_MAGIC = 'SEBAN_GUILD_REQUEST_V1'
MAX_LEVEL = 20
LIMIT = 100000


def points():
    from m2clientpack.systems_client import point_labels
    return point_labels()


def default_level(level):
    # Identyczne z CustomGuildCombatBonus (custom_guild_combat_rewards.h).
    from m2clientpack import kuznia_dodatki
    if kuznia_dodatki.fresh(): return {}  # MT2009_NASZE_SWIEZY_START_V1
    row = {}
    for p in (53, 150, 149, 178, 179, 180, 181, 182, 183): row[str(p)] = level // 2
    row['84'] = level // 4
    for p in (12, 13, 14, 15, 54, 55, 56, 57, 59, 60, 61, 62): row[str(p)] = level
    return {p: v for p, v in row.items() if v}


def defaults():
    return {'schema': SCHEMA, 'master_enabled': True, 'enabled': True,
            'levels': {str(n): default_level(n) for n in range(1, MAX_LEVEL + 1)}}


def validate(cfg):
    if not isinstance(cfg, dict) or not isinstance(cfg.get('levels'), dict): raise ValueError('Nieprawidłowa konfiguracja gildii.')
    allowed = points(); levels = {}
    for lvl, row in cfg['levels'].items():
        if not str(lvl).isdigit() or not 1 <= int(lvl) <= MAX_LEVEL or not isinstance(row, dict): raise ValueError('Nieprawidłowy poziom gildii.')
        out = {}
        for p, v in row.items():
            if not str(p).isdigit() or int(p) not in allowed: raise ValueError('Poziom %s: nieznany bonus #%s.' % (lvl, p))
            if type(v) is not int or not 0 <= v <= LIMIT: raise ValueError('Poziom %s: „%s” poza zakresem 0–%d.' % (lvl, allowed[int(p)][0], LIMIT))
            if v: out[str(int(p))] = v
        levels[str(int(lvl))] = out
    for n in range(1, MAX_LEVEL + 1): levels.setdefault(str(n), {})
    return {'schema': SCHEMA, 'master_enabled': bool(cfg.get('master_enabled')), 'enabled': bool(cfg.get('enabled')), 'levels': levels}


def canonical(cfg):
    return json.dumps(validate(cfg), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(cfg):
    return hashlib.sha256(canonical(cfg)).hexdigest()


def engine_body(cfg):
    cfg = validate(cfg)
    lines = ['%d %d' % (int(cfg['master_enabled']), int(cfg['enabled']))]
    for lvl in sorted(cfg['levels'], key=int):
        for p in sorted(cfg['levels'][lvl], key=int): lines.append('B %s %s %d' % (lvl, p, cfg['levels'][lvl][p]))
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
    cfg['levels'] = {}
    for n in range(1, MAX_LEVEL + 1):
        keys = request.form.getlist('bk_%d' % n); values = request.form.getlist('bv_%d' % n)
        if len(keys) != len(values) or len(set(keys)) != len(keys) or not all(k.isdigit() and int(k) in allowed for k in keys):
            raise ValueError('Poziom %d: nieprawidłowy lub powtórzony bonus.' % n)
        row = {}
        for k, v in zip(keys, values):
            v = v.strip() or '0'
            if not v.isdigit(): raise ValueError('Poziom %d: wartość „%s” musi być liczbą.' % (n, v))
            if int(v): row[k] = int(v)
        cfg['levels'][str(n)] = row
    return validate(cfg)


def install(bp, ctx):
    store = SystemStore(Path(ctx['spool']) / 'systems/gildia', codec, ctx.get('boot_plan'))
    login = ctx['login_required']

    @bp.route('/systemy/gildia', methods=['GET', 'POST'])
    @login
    def systems_gildia():
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
                ctx['app'].logger.exception('Guild editor failed'); flash('Operacja nie została potwierdzona. Sprawdź logi panelu.', 'error')
            return redirect(url_for('dbeditor.systems_gildia'))
        with store.locked(): cfg = store.read()
        labels = points()
        opts = [dict(k=str(p), l=n + (' (%s)' % u.replace('‰', '‰ = 1/10 %') if u else ''), s=n) for p, (n, u) in sorted(labels.items(), key=lambda x: x[1][0])]
        init = {n: [[p, v] for p, v in sorted(cfg['levels'][str(n)].items(), key=lambda x: int(x[0]))] for n in range(1, MAX_LEVEL + 1)}
        return render_template('dbeditor/systems_guild.html', config=cfg, revision=revision(cfg), opts=opts, init=init,
                               limit=LIMIT, levels=list(range(1, MAX_LEVEL + 1)), status=store.status(),
                               dbe_csrf=common.csrf_token(), sys_active='gildia', system=None)

    @bp.route('/systemy/gildia/status')
    @login
    def systems_gildia_status():
        return jsonify(store.status())
