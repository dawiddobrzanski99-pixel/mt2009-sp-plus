"""MT2009_NASZE_RANGI_V1/V2: Kuźnia Mocy -> Rangi (Punkty Rangi): wlasne rangi (1-40) - prog, nazwa, kolor,
odznaka (grafika TGA nad nickiem) i dowolne bonusy z gry. Nazwy/kolory/odznaki trafiaja do ROOT
(Kon -> Klient), progi i bonusy dzialaja od razu po "Zastosuj"."""
import hashlib
import json
import re
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, jsonify, abort, send_file
from dbeditor import common_items as common
from dbeditor.systems_store import SystemStore, atomic

SCHEMA = 'SEBAN_RANK_V1'
REQUEST_MAGIC = 'SEBAN_RANK_REQUEST_V1'
MAX_TIERS = 40
LIMIT = 100000
DEFAULT_FROM = [0, 1000, 3000, 6000, 10000, 16000, 30000, 50000, 80000, 110000, 150000, 200000]
NAMES = ['Turysta z M1', 'Klepacz Dzików', 'Sąsiad Kowala', 'Sponsor Kowala', 'Czytelnik Nieudanych KU', 'Młot na Metiny',
         'Stały Klient Dozorcy', 'Lokator Lochów', 'Windykator Bossów', 'Postrach Serwera', 'Ostatni Przed Emeryturą', 'Emeryt Olimpu']
COLORS = ['#d7e1eb', '#64ffa0', '#50ebeb', '#64a5ff', '#c8a5ff', '#b473ff', '#ff87b9', '#ffaf50', '#ff6969', '#ffc35a', '#ffdc64', '#fff0a5']
DEFAULT_POINTS = [96, 75, 133, 78, 134, 76, 135, 179, 180, 181, 182, 178, 183, 17, 19, 149]
BADGE_RE = re.compile(r'[a-f0-9]{64}\.tga')
BADGE_HEIGHT_MAX = 64
BADGE_WIDTH_MAX = 256


def points():
    from m2clientpack.systems_client import point_labels
    return point_labels()


def default_tier(stage):
    # Identyczne z RewardValue (playerbot_rank_points.h, RANK_CUMULATIVE_REWARDS_V4).
    row = {}
    for i, p in enumerate(DEFAULT_POINTS):
        v = stage * 30 // 12 if i == 0 else stage * 20 // 12 if i <= 12 else (stage // 2) * 10 // 6 if i <= 14 else stage // 2
        if v > 0: row[str(p)] = v
    return row


ENGINE_DEFAULTS = '/opt/m2spool/systems/rangi/status/defaults.txt'


def engine_defaults():
    """MT2009_NASZE_RANGI_SWIEZE_V1: rangi wkompilowane w gre tego serwera (eksport silnika) albo None."""
    try:
        raw = open(ENGINE_DEFAULTS, 'rb').read().decode('latin-1')
    except OSError:
        return None
    frm, names, tiers = [], {}, {}
    for line in raw.splitlines():
        p = line.split()
        if not p: continue
        if p[0] == 'F': frm = [int(x) for x in p[1:]]
        elif p[0] == 'N' and len(p) == 3: names[int(p[1])] = '' if p[2] == '-' else bytes.fromhex(p[2]).decode('cp1250', 'replace')
        elif p[0] == 'B' and len(p) == 4: tiers.setdefault(p[1], {})[p[2]] = int(p[3])
    if not frm or not 1 <= len(frm) <= MAX_TIERS: return None
    ranks = [dict(name=(names.get(i) or 'Ranga %d' % i)[:60], color=COLORS[(i - 1) % len(COLORS)], badge='') for i in range(1, len(frm) + 1)]
    return {'schema': SCHEMA, 'master_enabled': True, 'enabled': True, 'from': frm, 'ranks': ranks,
            'tiers': {str(i): tiers.get(str(i), {}) for i in range(1, len(frm) + 1)}}


def defaults():
    eng = engine_defaults()
    if eng: return eng
    return {'schema': SCHEMA, 'master_enabled': True, 'enabled': True, 'from': list(DEFAULT_FROM),
            'ranks': [dict(name=n, color=c, badge='') for n, c in zip(NAMES, COLORS)],
            'tiers': {str(n): default_tier(n) for n in range(1, 13)}}


def badge_size(raw):
    """Wymiary odznaki TGA (nieskompresowana 24/32-bit) albo ValueError z dokladnym wymaganiem."""
    if len(raw) < 18 or raw[2] != 2 or raw[16] not in (24, 32) or raw[1] != 0:
        raise ValueError('Odznaka: wymagany plik TGA nieskompresowany 32-bit (z przezroczystością) albo 24-bit.')
    w, h = raw[12] | raw[13] << 8, raw[14] | raw[15] << 8
    if not (8 <= w <= BADGE_WIDTH_MAX and 8 <= h <= BADGE_HEIGHT_MAX):
        raise ValueError('Odznaka: rozmiar %d×%d px — dozwolone szerokość 8–%d px, wysokość 8–%d px (zalecane jak obecne: wysokość 22 px, szerokość 60–120 px).' % (w, h, BADGE_WIDTH_MAX, BADGE_HEIGHT_MAX))
    if len(raw) < 18 + raw[0] + w * h * (raw[16] // 8): raise ValueError('Odznaka: niekompletny plik TGA.')
    return w, h


def validate(cfg):
    # MT2009_NASZE_RANGI_SWIEZE_V1: zapisane stare rangi autora Kuzni (z wczesniejszej instalacji) na serwerze,
    # ktorego gra ma inne rangi -> rangi tej gry (od zera).
    try:
        if [r.get('name') for r in cfg.get('ranks') or []] == NAMES:
            eng = engine_defaults()
            if eng and [r['name'] for r in eng['ranks']] != NAMES: cfg = eng
    except (AttributeError, TypeError):
        pass
    if not isinstance(cfg, dict) or not isinstance(cfg.get('tiers'), dict): raise ValueError('Nieprawidłowa konfiguracja rang.')
    frm = cfg.get('from')
    if not isinstance(frm, list) or not 1 <= len(frm) <= MAX_TIERS or any(type(v) is not int or not 0 <= v <= 200000 for v in frm):
        raise ValueError('Rangi: od 1 do %d rang, progi 0–200 000.' % MAX_TIERS)
    n = len(frm)
    ranks = cfg.get('ranks')
    if ranks is None: ranks = [dict(name=NAMES[i] if i < 12 else 'Ranga %d' % (i + 1), color=COLORS[i] if i < 12 else '#ffffff', badge='') for i in range(n)]
    if not isinstance(ranks, list) or len(ranks) != n: raise ValueError('Rangi: niezgodna liczba nazw i progów.')
    out_ranks = []
    for i, r in enumerate(ranks):
        name = r.get('name') if isinstance(r, dict) else None
        if not isinstance(name, str) or not name.strip() or len(name) > 40 or '%' in name or any(ord(c) < 32 for c in name): raise ValueError('Ranga %d: nazwa 1–40 znaków, bez %%.' % (i + 1))
        name.encode('cp1250')
        color = r.get('color', '#ffffff')
        if not isinstance(color, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', color): raise ValueError('Ranga %d: kolor #RRGGBB.' % (i + 1))
        badge = r.get('badge', '')
        if badge and not BADGE_RE.fullmatch(badge): raise ValueError('Ranga %d: nieprawidłowa odznaka.' % (i + 1))
        out_ranks.append(dict(name=name.strip(), color=color.lower(), badge=badge))
    for i in range(1, n):
        if frm[i] < frm[i - 1]: raise ValueError('Próg rangi „%s” nie może być niższy niż poprzedniej.' % out_ranks[i]['name'])
    allowed = points(); tiers = {}
    for lvl, row in cfg['tiers'].items():
        if not str(lvl).isdigit() or not isinstance(row, dict): raise ValueError('Nieprawidłowa ranga.')
        if int(lvl) > n: continue
        out = {}
        for p, v in row.items():
            if not str(p).isdigit() or int(p) not in allowed: raise ValueError('%s: nieznany bonus #%s.' % (out_ranks[int(lvl) - 1]['name'], p))
            if type(v) is not int or not 0 <= v <= LIMIT: raise ValueError('%s: „%s” poza zakresem 0–%d.' % (out_ranks[int(lvl) - 1]['name'], allowed[int(p)][0], LIMIT))
            if v: out[str(int(p))] = v
        tiers[str(int(lvl))] = out
    for k in range(1, n + 1): tiers.setdefault(str(k), {})
    return {'schema': SCHEMA, 'master_enabled': bool(cfg.get('master_enabled')), 'enabled': bool(cfg.get('enabled')), 'from': list(frm), 'ranks': out_ranks, 'tiers': tiers}


def canonical(cfg):
    return json.dumps(validate(cfg), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(cfg):
    return hashlib.sha256(canonical(cfg)).hexdigest()


def engine_body(cfg):
    cfg = validate(cfg)
    lines = ['%d %d' % (int(cfg['master_enabled']), int(cfg['enabled'])), 'F ' + ' '.join(map(str, cfg['from']))]
    for i, r in enumerate(cfg['ranks'], 1): lines.append('N %d %s' % (i, r['name'].encode('cp1250').hex()))
    for lvl in sorted(cfg['tiers'], key=int):
        for p in sorted(cfg['tiers'][lvl], key=int): lines.append('B %s %s %d' % (lvl, p, cfg['tiers'][lvl][p]))
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
    order = [x for x in request.form.get('order', '').split(',') if x]
    if not order or len(order) > MAX_TIERS or len(set(order)) != len(order): raise ValueError('Nieprawidłowa lista rang.')
    cfg['tiers'] = {}; frm = []; ranks = []
    for pos, key in enumerate(order, 1):
        if not re.fullmatch(r'[a-z0-9]{1,12}', key): raise ValueError('Nieprawidłowa ranga.')
        name = request.form.get('name_' + key, '').strip()
        raw = request.form.get('from_' + key, '').strip()
        if not raw.isdigit(): raise ValueError('%s: próg musi być liczbą.' % (name or 'Ranga %d' % pos))
        frm.append(int(raw))
        badge = request.form.get('badge_' + key, '')
        f = request.files.get('badgefile_' + key)
        if f and f.filename:
            blob = f.read(BADGE_WIDTH_MAX * BADGE_HEIGHT_MAX * 4 + 4096); badge_size(blob)
            badge = hashlib.sha256(blob).hexdigest() + '.tga'; atomic(store.root / 'assets' / badge, blob)
        if request.form.get('clearbadge_' + key) == '1': badge = ''
        ranks.append(dict(name=name, color=request.form.get('color_' + key, '#ffffff'), badge=badge))
        keys = request.form.getlist('bk_' + key); values = request.form.getlist('bv_' + key)
        if len(keys) != len(values) or len(set(keys)) != len(keys) or not all(k.isdigit() and int(k) in allowed for k in keys):
            raise ValueError('%s: nieprawidłowy lub powtórzony bonus.' % (name or 'Ranga %d' % pos))
        row = {}
        for k, v in zip(keys, values):
            v = v.strip() or '0'
            if not v.isdigit(): raise ValueError('%s: wartość „%s” musi być liczbą.' % (name, v))
            if int(v): row[k] = int(v)
        cfg['tiers'][str(pos)] = row
    cfg['from'] = frm; cfg['ranks'] = ranks
    return validate(cfg)


def install(bp, ctx):
    store = SystemStore(Path(ctx['spool']) / 'systems/rangi', codec, ctx.get('boot_plan'))
    login = ctx['login_required']

    @bp.route('/systemy/rangi', methods=['GET', 'POST'])
    @login
    def systems_rangi():
        if request.method == 'POST':
            if not common.check_csrf(): abort(403)
            try:
                expected = request.form.get('revision', ''); action = request.form.get('action')
                if action in ('save', 'save_apply'):
                    cfg = parse_form(store)
                    if action == 'save_apply':
                        store.save_apply(cfg, expected)
                        flash('Zapisano i przekazano do kanałów. Progi i bonusy działają od razu; nazwy, kolory i odznaki — po nowym ROOT (Przegląd → Klient (ROOT)).', 'info')
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
                ctx['app'].logger.exception('Rank editor failed'); flash('Operacja nie została potwierdzona. Sprawdź logi panelu.', 'error')
            return redirect(url_for('dbeditor.systems_rangi'))
        with store.locked(): cfg = store.read()
        opts = [dict(k=str(p), l=n + (' (%s)' % u.replace('‰', '‰ = 1/10 %') if u else ''), s=n) for p, (n, u) in sorted(points().items(), key=lambda x: x[1][0])]
        tiers = []
        for i, r in enumerate(cfg['ranks'], 1):
            size = None
            if r['badge']:
                try: size = badge_size((store.root / 'assets' / r['badge']).read_bytes())
                except (OSError, ValueError): size = None
            tiers.append(dict(n=i, key='r%d' % i, name=r['name'], color=r['color'], frm=cfg['from'][i - 1], badge=r['badge'], size=size,
                              init=[[p, v] for p, v in sorted(cfg['tiers'][str(i)].items(), key=lambda x: int(x[0]))]))
        from m2clientpack import kuznia_dodatki  # MT2009_NASZE_RANGI_BEZ_ODZNAK_V1: u innych bez odznak (ich exe ich nie rysuje)
        return render_template('dbeditor/systems_rank.html', no_badges=kuznia_dodatki.fresh(), config=cfg, revision=revision(cfg), opts=opts, limit=LIMIT, tiers=tiers,
                               max_tiers=MAX_TIERS, status=store.status(), dbe_csrf=common.csrf_token(), sys_active='rangi', system=None)

    @bp.route('/systemy/rangi/odznaka/<name>')
    @login
    def systems_rangi_badge(name):
        if not BADGE_RE.fullmatch(name): abort(404)
        path = store.root / 'assets' / name
        if not path.exists(): abort(404)
        return send_file(str(path), mimetype='image/x-tga')

    @bp.route('/systemy/rangi/status')
    @login
    def systems_rangi_status():
        return jsonify(store.status())
