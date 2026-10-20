"""MT2009_NASZE_MISJE_V1: Kuźnia Mocy -> Misje (Ctrl+N): Polowania, Metinologia, Bossologia.

Etapy w kolejnosci (gracz robi je po kolei), cele, ilosci, wymagany poziom, bonusy i nagrody.
Postep graczy jest liczony po id etapu - panel nadaje id nowym etapom i nie zmienia istniejacych.
Wartosci domyslne = tabele wkompilowane w gre (silnik zapisuje je w systems/misje/status/defaults.txt).
Biolog to questy (collect_quest_lv*) - jego bonusy zmienia sie w edytorze questow.
"""
import hashlib
import json
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, jsonify, abort
from dbeditor import common_items as common
from dbeditor.systems_store import SystemStore

SCHEMA = 'SEBAN_MISSIONS_V1'
REQUEST_MAGIC = 'SEBAN_MISSIONS_REQUEST_V1'
KINDS = ('hunts', 'metin', 'boss')
GIFTS = (('bless', 25040, 'Zwój Błogosławieństwa'), ('change', 71284, 'Zaczarowanie Przedmiotu'),
         ('add', 71285, 'Wzmocnienie Przedmiotu'), ('coupons', 80017, 'Kupon 50 SM'))
MAPS = {1: 'M1 (Shinsoo)', 3: 'M2 (Shinsoo)', 21: 'M1 (Chunjo)', 41: 'M1 (Jinno)', 61: 'Góra Sohan', 62: 'Ognista Kraina',
        63: 'Pustynia', 64: 'Dolina Orków', 65: 'Świątynia Hwang', 67: 'Las Duchów', 68: 'Czerwony Las', 71: 'V2 (loch pająków)',
        73: 'Grota Wygnańców I', 104: 'V1 (loch pająków)', 301: 'Przylądek Smoczego Ognia', 304: 'Góry Grzmotu'}
_spool = {'root': None}


def points():
    from m2clientpack.systems_client import point_labels
    return point_labels()


def _unhex(s):
    return '' if s == '-' else bytes.fromhex(s).decode('cp1250', 'replace')


def _hex(s):
    raw = s.encode('cp1250')
    return raw.hex() if raw else '-'


def _bonus_in(s):
    out = {}
    if s != '-':
        for part in s.split(','):
            p, v = part.split(':'); out[str(int(p))] = out.get(str(int(p)), 0) + int(v)
    return out


def _bonus_out(b):
    items = [(int(p), v) for p, v in b.items() if v]
    return ','.join('%d:%d' % (p, v) for p, v in sorted(items)) or '-'


def parse_body(text):
    cfg = {'schema': SCHEMA, 'master_enabled': True, 'enabled': True, 'hunts': [], 'metin': [], 'boss': [], 'final': {'metin': {}, 'boss': {}}}
    lines = text.splitlines(); extras = {}; rewards = {}
    first = lines[0].split(); cfg['master_enabled'], cfg['enabled'] = first[0] == '1', first[1] == '1'
    cfg['bots'] = len(first) < 3 or first[2] == '1'
    for line in lines[1:]:
        f = line.split()
        if not f: continue
        if f[0] == 'H':
            cfg['hunts'].append(dict(id=int(f[1]), level=int(f[2]), race=int(f[3]), map=int(f[4]), kills=int(f[5]), name=_unhex(f[6]),
                                     location=_unhex(f[7]), label=_unhex(f[8]), bonus=_bonus_in(f[9])))
        elif f[0] == 'M':
            cfg[f[1]].append(dict(id=int(f[2]), level=int(f[3]), race=int(f[4]), target=int(f[5]), kills=int(f[6]), name=_unhex(f[7]),
                                  location=_unhex(f[8]), bonus=_bonus_in(f[9]), yang=0, bless=0, change=0, add=0, coupons=0))
        elif f[0] == 'X':
            extras[(f[1], int(f[2]))] = dict(yang=int(f[3]), bless=int(f[4]), change=int(f[5]), add=int(f[6]), coupons=int(f[7]))
        elif f[0] == 'F':
            cfg['final'][f[1]] = _bonus_in(f[2])
        elif f[0] == 'R':  # MT2009_NASZE_MISJE_V2
            items = [] if f[4] == '-' else [[int(a), int(b)] for a, b in (p.split(':') for p in f[4].split(','))]
            rewards[('hunts' if f[1] == 'hunting' else f[1], int(f[2]))] = dict(ryang=int(f[3]), items=items)
    for kind in ('metin', 'boss'):
        for row in cfg[kind]: row.update(extras.get((kind, row['id']), {}))
    for kind in KINDS:
        for row in cfg[kind]: row.update(rewards.get((kind, row['id']), dict(ryang=0, items=[])))
    return cfg


def defaults():
    path = Path(_spool['root'] or '/opt/m2spool') / 'systems/misje/status/defaults.txt'
    if not path.exists():
        raise ValueError('Brak wartości domyślnych z gry — gra jeszcze nie zapisała systems/misje/status/defaults.txt (wymagana nowa wersja gry).')
    return parse_body(path.read_text(encoding='ascii'))


def _int(v, lo, hi, what):
    if type(v) is not int or not lo <= v <= hi: raise ValueError('%s: wartość spoza zakresu %d–%d.' % (what, lo, hi))
    return v


def _bonus(b, what, allowed):
    if not isinstance(b, dict) or len([1 for v in b.values() if v]) > 8: raise ValueError('%s: najwyżej 8 bonusów.' % what)
    out = {}
    for p, v in b.items():
        if not str(p).isdigit() or int(p) not in allowed: raise ValueError('%s: nieznany bonus #%s.' % (what, p))
        _int(v, 0, 1000000, what)
        if v: out[str(int(p))] = v
    return out


def _text(s, what, limit=40):
    if not isinstance(s, str) or len(s) > limit or any(ord(c) < 32 for c in s): raise ValueError('%s: tekst do %d znaków.' % (what, limit))
    s.encode('cp1250'); return s


def validate(cfg):
    if not isinstance(cfg, dict): raise ValueError('Nieprawidłowa konfiguracja misji.')
    allowed = points(); out = {'schema': SCHEMA, 'master_enabled': bool(cfg.get('master_enabled')), 'enabled': bool(cfg.get('enabled')), 'bots': bool(cfg.get('bots', True))}
    for kind in KINDS:
        rows = cfg.get(kind) or []; seen = set(); res = []
        if not isinstance(rows, list) or len(rows) > 200: raise ValueError('Za dużo etapów.')
        for i, r in enumerate(rows, 1):
            what = {'hunts': 'Polowanie', 'metin': 'Metinologia', 'boss': 'Bossologia'}[kind] + ' – etap %d' % i
            x = dict(id=_int(r.get('id'), 1, 99998, what + ' (id)'), level=_int(r.get('level'), 0, 250, what + ' (poziom)'),
                     race=_int(r.get('race'), 0, 99999999, what + ' (potwór)'), kills=_int(r.get('kills'), 1, 1000000, what + ' (ilość)'),
                     name=_text(r.get('name', ''), what + ' (nazwa)'), location=_text(r.get('location', ''), what + ' (miejsce)'),
                     bonus=_bonus(r.get('bonus') or {}, what, allowed))
            if x['id'] in seen: raise ValueError(what + ': powtórzone id etapu.')
            seen.add(x['id'])
            if kind == 'hunts':
                x.update(map=_int(r.get('map'), 0, 99999, what + ' (mapa)'), label=_text(r.get('label', ''), what + ' (opis)', 90))
                if x['race'] < 1: raise ValueError(what + ': wybierz potwora.')
            else:
                x.update(target=_int(r.get('target', 0), 0, 250, what + ' (poziom metina)'), yang=_int(r.get('yang', 0), 0, 2000000000, what + ' (Yang)'))
                for key, _v, name in GIFTS: x[key] = _int(r.get(key, 0), 0, 200, what + ' (' + name + ')')
                if kind == 'metin' and x['target'] < 1: raise ValueError(what + ': podaj poziom metinów.')
                if kind == 'boss' and x['race'] < 1: raise ValueError(what + ': wybierz bossa.')
            # MT2009_NASZE_MISJE_V2: dowolne nagrody jednorazowe (Yang dla Polowan + do 10 przedmiotow).
            x['ryang'] = _int(r.get('ryang', 0), 0, 2000000000, what + ' (Yang - nagroda)')
            items = r.get('items') or []
            if not isinstance(items, list) or len(items) > 10: raise ValueError(what + ': najwyżej 10 przedmiotów w nagrodzie.')
            x['items'] = []
            for it in items:
                if not isinstance(it, list) or len(it) != 2: raise ValueError(what + ': nieprawidłowy przedmiot nagrody.')
                v = _int(it[0], 1, 4294967295, what + ' (przedmiot)'); c = _int(it[1], 1, 200, what + ' (ilość przedmiotu)')
                if any(o[0] == v for o in x['items']): raise ValueError(what + ': przedmiot #%d powtórzony w nagrodzie.' % v)
                x['items'].append([v, c])
            res.append(x)
        out[kind] = res
    fin = cfg.get('final') or {}
    out['final'] = {k: _bonus(fin.get(k) or {}, 'Nagroda za całą ścieżkę (' + k + ')', allowed) for k in ('metin', 'boss')}
    return out


def canonical(cfg):
    return json.dumps(validate(cfg), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(cfg):
    return hashlib.sha256(canonical(cfg)).hexdigest()


def engine_body(cfg):
    c = validate(cfg)
    lines = ['%d %d %d' % (int(c['master_enabled']), int(c['enabled']), int(c['bots']))]
    for h in c['hunts']:
        lines.append('H %d %d %d %d %d %s %s %s %s' % (h['id'], h['level'], h['race'], h['map'], h['kills'], _hex(h['name']), _hex(h['location']), _hex(h['label']), _bonus_out(h['bonus'])))
    for kind in ('metin', 'boss'):
        for m in c[kind]:
            lines.append('M %s %d %d %d %d %d %s %s %s' % (kind, m['id'], m['level'], m['race'], m['target'], m['kills'], _hex(m['name']), _hex(m['location']), _bonus_out(m['bonus'])))
        for m in c[kind]:
            if m['yang'] or any(m[k] for k, _v, _n in GIFTS):
                lines.append('X %s %d %d %d %d %d %d' % (kind, m['id'], m['yang'], m['bless'], m['change'], m['add'], m['coupons']))
        lines.append('F %s %s' % (kind, _bonus_out(c['final'][kind])))
    for kind in KINDS:
        for r in c[kind]:
            if r['ryang'] or r['items']:
                lines.append('R %s %d %d %s' % ('hunting' if kind == 'hunts' else kind, r['id'], r['ryang'],
                                                ','.join('%d:%d' % (v, n) for v, n in r['items']) or '-'))
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


# MT2009_NASZE_MISJE_WYGLAD_V1: wlasna grafika okna Ctrl+N (podmieniana w ROOT przy budowaniu na Przegladzie).
SKIN_DIR = 'ymir work/ui/game/custom_windows/final/'
SKIN_SLOTS = [('mission_frame', 860, 660, 'Tło i ramka całego okna')] + \
    [('mission_tab_%d_%s' % (i, st), 190, 66, 'Zakładka „%s” — %s' % (n, 'zaznaczona' if st == 'selected' else 'zwykła'))
     for i, n in enumerate(('Biolog', 'Polowanie', 'Metinologia', 'Bossologia')) for st in ('normal', 'selected')] + \
    [('mission_action', 320, 48, 'Przycisk akcji (Rozpocznij / Teleportuj)'), ('previous', 38, 38, 'Strzałka w lewo'), ('next', 38, 38, 'Strzałka w prawo')]


def skin_check(raw, w, h):
    if len(raw) < 18 or raw[2] != 2 or raw[1] != 0 or raw[16] != 32:
        raise ValueError('wymagany plik TGA nieskompresowany 32-bit (z przezroczystością).')
    rw, rh = raw[12] | raw[13] << 8, raw[14] | raw[15] << 8
    if (rw, rh) != (w, h): raise ValueError('rozmiar %d×%d px — wymagany dokładnie %d×%d px.' % (rw, rh, w, h))
    if len(raw) < 18 + raw[0] + w * h * 4: raise ValueError('niekompletny plik TGA.')


def mob_search(q, stones=False):
    from dbeditor.crafting import _rows
    q = (q or '').strip()
    where, params = ('vnum = %s', [int(q)]) if q.isdigit() else ('CAST(locale_name AS BINARY) LIKE %s', [b'%' + q.encode('cp1250', 'replace') + b'%'])
    kind = ' AND type = 2' if stones else ' AND type = 0'
    try:
        rows = _rows('SELECT vnum, level, rank, CAST(locale_name AS BINARY) AS n FROM player.mob_proto WHERE ' + where + kind + ' ORDER BY level, vnum LIMIT 40', params)
    except Exception:
        return []
    out = []
    for r in rows:
        raw = r['n'] if isinstance(r['n'], (bytes, bytearray)) else str(r['n'] or '').encode('latin-1', 'replace')
        out.append(dict(vnum=int(r['vnum']), level=int(r['level'] or 0), rank=int(r['rank'] or 0), name=bytes(raw).split(b'\0')[0].decode('cp1250', 'replace').strip()))
    return out


def install(bp, ctx):
    _spool['root'] = ctx['spool']
    store = SystemStore(Path(ctx['spool']) / 'systems/misje', codec, ctx.get('boot_plan'))
    login = ctx['login_required']

    def current():
        with store.locked():
            path = store.root / 'draft.json'
            if path.exists(): return validate(json.loads(path.read_bytes()))
        return defaults()

    @bp.route('/systemy/misje', methods=['GET', 'POST'])
    @login
    def systems_misje():
        if request.method == 'POST':
            if not common.check_csrf(): abort(403)
            try:
                expected = request.form.get('revision', ''); action = request.form.get('action')
                if action in ('save', 'save_apply'):
                    cfg = validate(json.loads(request.form.get('payload') or '{}'))
                    if action == 'save_apply':
                        store.save_apply(cfg, expected); flash('Zapisano i przekazano do kanałów. Czekamy na potwierdzenia — bez restartu.', 'info')
                    else:
                        store.save(cfg, expected); flash('Zapisano projekt. Serwer jeszcze go nie zastosował.', 'info')
                elif action == 'apply':
                    store.apply(expected); flash('Przekazano konfigurację do kanałów.', 'info')
                elif action == 'defaults':
                    store.save(defaults(), expected); flash('Przywrócono wartości z gry do projektu. Zastosuj, aby działały.', 'success')
                elif action == 'undo':
                    store.undo(expected); flash('Przywrócono poprzedni projekt. Zastosuj, aby działał w grze.', 'success')
                else: abort(400)
            except (ValueError, KeyError, TypeError) as exc: flash(str(exc), 'error')
            except Exception:
                ctx['app'].logger.exception('Missions editor failed'); flash('Operacja nie została potwierdzona. Sprawdź logi panelu.', 'error')
            return redirect(url_for('dbeditor.systems_misje', tab=request.args.get('tab', 'hunts')))
        try:
            cfg = current(); error = None
        except ValueError as exc:
            cfg = validate({'master_enabled': True, 'enabled': True}); error = str(exc)
        labels = points()
        opts = [dict(k=str(p), l=n + (' (%s)' % u.replace('‰', '‰ = 1/10 %') if u else '')) for p, (n, u) in sorted(labels.items(), key=lambda x: x[1][0])]
        try:
            from dbeditor.shops import load_items
            from dbeditor.crafting import _rows
            item_names = {v: i['name'] for v, i in load_items(_rows, [it[0] for k in KINDS for r in cfg[k] for it in r['items']]).items()}
        except Exception:
            item_names = {}
        skins = [dict(key=k, w=w, h=h, label=l, custom=(store.root / 'assets' / (k + '.tga')).exists()) for k, w, h, l in SKIN_SLOTS]
        return render_template('dbeditor/systems_missions.html', config=cfg, item_names=item_names, skins=skins, revision=revision(cfg), opts=opts, maps=MAPS, gifts=GIFTS,
                               error=error, status=store.status(), dbe_csrf=common.csrf_token(), sys_active='misje', system=None,
                               tab=request.args.get('tab', 'hunts'))

    @bp.route('/systemy/misje/wyglad', methods=['POST'])
    @login
    def systems_misje_skin():
        if not common.check_csrf(): abort(403)
        assets = store.root / 'assets'; done = []
        for key, w, h, label in SKIN_SLOTS:
            f = request.files.get('skin_' + key)
            try:
                if f and f.filename:
                    raw = f.read(w * h * 4 + 65536); skin_check(raw, w, h)
                    with store.locked():
                        from dbeditor.systems_store import atomic
                        atomic(assets / (key + '.tga'), raw)
                    done.append(label)
                elif request.form.get('clear_' + key) == '1' and (assets / (key + '.tga')).exists():
                    (assets / (key + '.tga')).unlink(); done.append(label + ' (przywrócono z gry)')
            except ValueError as exc:
                flash('%s: %s' % (label, exc), 'error')
        if done: flash('Zapisano grafikę: ' + ', '.join(done) + '. Teraz zbuduj ROOT na Przeglądzie i podmień go w kliencie.', 'success')
        return redirect(url_for('dbeditor.systems_misje', tab='wyglad'))

    @bp.route('/systemy/misje/wyglad/<key>.tga')
    @login
    def systems_misje_skin_file(key):
        if key not in [s[0] for s in SKIN_SLOTS]: abort(404)
        path = store.root / 'assets' / (key + '.tga')
        if not path.exists(): abort(404)
        from flask import send_file
        return send_file(str(path), mimetype='image/x-tga', max_age=0)

    @bp.route('/systemy/misje/status')
    @login
    def systems_misje_status():
        return jsonify(store.status())

    @bp.route('/systemy/misje/potwory')
    @login
    def systems_misje_mobs():
        return jsonify(mob_search(request.args.get('q', ''), request.args.get('kamienie') == '1'))
