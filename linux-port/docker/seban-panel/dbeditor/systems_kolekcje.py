"""MT2009_NASZE_KOLEKCJE_V1: Kuznia Mocy -> Kolekcjoner - kolekcje przedmiotow do oddawania (okno Ctrl+N w grze).

Dane panelu: spool/systems/kolekcje/dane.json; dla gry: spool/systems/kolekcje/config.txt (format opisany
w silniku: kuznia_kolekcje.h). Gra czyta plik ponownie po zmianie - zapis dziala od razu, bez restartu.
Postep graczy jest zapisany po kluczu kategorii i numerze przedmiotu, wiec zmiana kolejnosci, liczby
sztuk czy bonusow nie kasuje tego, co gracze juz oddali.
"""
import json
import re
import sys
import time
from pathlib import Path

from flask import abort, jsonify, render_template, request

COOLDOWNS = [(0, 'bez przerwy'), (300, '5 min'), (600, '10 min'), (1800, '30 min'), (3600, '1 godz.'), (7200, '2 godz.'),
             (21600, '6 godz.'), (43200, '12 godz.'), (86400, '24 godz.')]
START_ITEMS = [28437, 28436, 28431, 28442, 28430, 28438, 28432, 28441, 30006, 30015, 30050, 30165, 30166, 30167, 30168,
               27992, 27993, 27994, 27987, 25040, 71084, 71085, 50300, 27999, 50035, 71102]
LIMITS = {'cats': 20, 'items': 60, 'bonus': 6, 'name': 24, 'desc': 110}


def _hex(value):
    raw = value.replace('\t', ' ').encode('cp1250', 'replace')
    return raw.hex() if raw else '-'


def config_text(data):
    out = ['# MT2009_NASZE_KOLEKCJE_V1: z panelu (Kuznia Mocy -> Kolekcjoner) - nie edytuj recznie']
    for c in data['cats']:
        out.append('\t'.join(['cat', c['key'], str(c['icon']), str(c['level']), _hex(c['name']), _hex(c['desc'])]))
        out += ['\t'.join(['catbon', c['key'], str(b['point']), str(b['value'])]) for b in c['fin']]
        for it in c['items']:
            out.append('\t'.join(['item', c['key'], str(it['vnum']), str(it['need']), str(it['chance']), str(it['cooldown'])]))
            out += ['\t'.join(['itembon', c['key'], str(it['vnum']), str(b['point']), str(b['value'])]) for b in it['bonus']]
    return '\n'.join(out) + '\n'


def write_files(root, data):
    root.mkdir(parents=True, exist_ok=True)
    for name, body in (('dane.json', json.dumps(data, ensure_ascii=False, indent=1)), ('config.txt', config_text(data))):
        tmp = root / (name + '.tmp')
        tmp.write_text(body, encoding='utf-8' if name.endswith('.json') else 'ascii')
        tmp.replace(root / name)


# --- MT2009_NASZE_OKNO_CTRLN_V2: wlasne grafiki okna Ctrl+N (spool/systems/okno/grafika, przezywaja reinstalacje)
ART_LABELS = {'bg': 'Tło całego okna', 'stage': 'Tło pod modelem 3D', 'cat_biolog': 'Ikona: Badania Biologa',
              'cat_hunting': 'Ikona: Polowanie', 'cat_metin': 'Ikona: Metinologia', 'cat_boss': 'Ikona: Bossologia',
              'taskbar_0': 'Przycisk na pasku', 'taskbar_1': 'Przycisk na pasku (najechany)', 'taskbar_2': 'Przycisk na pasku (wciśnięty)',
              'btn_gold_0': 'Przycisk główny', 'btn_ghost_0': 'Przycisk „Teleport”', 'card': 'Karta kolekcji', 'card_act': 'Karta aktywna',
              'card_done': 'Karta ukończona', 'big': 'Kółko pod ikoną', 'row_on': 'Wybrana kategoria'}


def tga_info(raw):
    """(szerokosc, wysokosc) poprawnego TGA 24/32-bit (typ 2 albo 10), inaczej ValueError."""
    import struct
    if len(raw) < 18 or raw[2] not in (2, 10) or raw[16] not in (24, 32): raise ValueError('To nie jest plik TGA 24/32-bit.')
    w, h = struct.unpack('<HH', raw[12:16])
    if not w or not h or w > 2048 or h > 2048: raise ValueError('Nieprawidłowy rozmiar TGA.')
    return w, h


def tga_png(raw):
    import struct, zlib
    w, h = tga_info(raw)
    px, p = raw[16] // 8, 18 + raw[0]
    if raw[2] == 2:
        data = raw[p:p + w * h * px]
    else:
        out = bytearray()
        while len(out) < w * h * px and p < len(raw):
            c = raw[p]; p += 1
            if c & 0x80: out += raw[p:p + px] * ((c & 0x7f) + 1); p += px
            else: k = (c + 1) * px; out += raw[p:p + k]; p += k
        data = bytes(out)
    rows = []
    for y in range(h):
        r = data[y * w * px:(y + 1) * w * px]
        line = bytearray(b'\0')
        for x in range(w):
            q = r[x * px:(x + 1) * px]
            line += bytes((q[2], q[1], q[0], q[3] if px == 4 else 255)) if len(q) == px else b'\0\0\0\0'
        rows.append(bytes(line))
    if not raw[17] & 0x20: rows.reverse()
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(rows), 6)) + chunk(b'IEND', b'')


def restore(root, data, items, skipped):
    """Kopia ustawien: kategorie z kopii; przedmioty, ktorych serwer nie ma - pominiete (wpis do raportu)."""
    cats = []
    for c in data.get('cats') or []:
        if c.get('own_icon') and (root / 'ikony' / ('%s.tga' % c.get('key'))).is_file():
            pass  # wlasna ikona kategorii (plik z kopii)
        elif int(c.get('icon') or 0) not in items:
            skipped.append('Kolekcjoner: „%s” – ikony #%s nie ma w bazie, wybierz nową' % (c.get('name'), c.get('icon')))
            c['icon'] = next((i['vnum'] for i in c.get('items') or [] if int(i['vnum']) in items), 0)
        keep = []
        for it in c.get('items') or []:
            if int(it.get('vnum') or 0) in items: keep.append(it)
            else: skipped.append('Kolekcjoner: „%s” – przedmiotu #%s nie ma w bazie' % (c.get('name'), it.get('vnum')))
        c['items'] = keep
        if c['icon'] or c.get('own_icon'): cats.append(c)
    write_files(root, {'cats': cats})


def install(bp, ctx):
    from dbeditor import common_items as common
    login = ctx['login_required']
    rows = ctx['rows']
    root = Path(ctx['spool']) / 'systems' / 'kolekcje'

    def labels():
        from m2clientpack.systems_client import point_labels
        return {p: n + (' (%s)' % u if u else '') for p, (n, u) in point_labels().items() if 0 < int(p) < 256}

    def icon(vnum):
        fn = ctx.get('item_icon_url')
        if fn is None:
            for mod in (sys.modules.get('app'), sys.modules.get('__main__')):
                fn = getattr(mod, 'item_icon_url', None)
                if fn: break
        try:
            return fn(vnum) if fn else None
        except Exception:
            return None

    def text(value):
        if isinstance(value, (bytes, bytearray)):
            for enc in ('utf-8', 'cp1250'):
                try: return bytes(value).decode(enc)
                except UnicodeDecodeError: pass
            return bytes(value).decode('latin-1')
        return '' if value is None else str(value)

    def names(vnums):
        vnums = sorted({int(v) for v in vnums if int(v) > 0})
        if not vnums: return {}
        marks = ','.join(['%s'] * len(vnums))
        found = rows('SELECT vnum, CAST(locale_name AS BINARY) AS n FROM world.item_proto WHERE vnum IN (' + marks + ')', tuple(vnums))
        return {int(r['vnum']): text(r['n']) for r in found}

    def load():
        try:
            data = json.loads((root / 'dane.json').read_text(encoding='utf-8'))
            return data if isinstance(data.get('cats'), list) else {'cats': []}
        except (OSError, ValueError, AttributeError):
            return {'cats': []}

    def num(value, low, high, label):
        try: n = int(value)
        except (TypeError, ValueError): raise ValueError('%s: podaj liczbę.' % label)
        if n < low or n > high: raise ValueError('%s: od %d do %d.' % (label, low, high))
        return n

    def bonuses(raw, where, allowed):
        out = []
        for b in (raw or [])[:LIMITS['bonus']]:
            point = num(b.get('point'), 1, 255, where + ' – bonus')
            if point not in allowed: raise ValueError('%s: nieznany bonus #%d.' % (where, point))
            out.append({'point': point, 'value': num(b.get('value'), 1, 100000, where + ' – wartość bonusu')})
        return out

    def validate(data):
        allowed = labels()
        cats, keys = [], set()
        raw_cats = data.get('cats') or []
        if len(raw_cats) > LIMITS['cats']: raise ValueError('Najwięcej %d kategorii.' % LIMITS['cats'])
        all_vnums = {int(i.get('vnum') or 0) for c in raw_cats for i in (c.get('items') or [])} | {int(c.get('icon') or 0) for c in raw_cats}
        known = names(all_vnums)
        for c in raw_cats:
            name = str(c.get('name') or '').strip()[:LIMITS['name']]
            if not name: raise ValueError('Każda kategoria musi mieć nazwę.')
            key = str(c.get('key') or '')
            if not re.fullmatch(r'k[0-9]{1,6}', key) or key in keys:
                key = next('k%d' % n for n in range(1, 10 ** 6) if 'k%d' % n not in keys and not any(x.get('key') == 'k%d' % n for x in raw_cats))
            keys.add(key)
            icon_vnum = int(c.get('icon') or 0)
            own = bool(c.get('own_icon')) and (root / 'ikony' / (key + '.tga')).is_file()
            if own: icon_vnum = 0  # gra bierze wlasna ikone kat_<klucz>.tga z ROOT
            elif icon_vnum not in known: raise ValueError('„%s”: wybierz ikonę kategorii.' % name)
            items, seen = [], set()
            for it in (c.get('items') or [])[:LIMITS['items']]:
                vnum = int(it.get('vnum') or 0)
                if vnum not in known: raise ValueError('„%s”: nie ma przedmiotu %d w bazie.' % (name, vnum))
                if vnum in seen: raise ValueError('„%s”: przedmiot %s jest dodany dwa razy.' % (name, known[vnum]))
                seen.add(vnum)
                where = '„%s” → %s' % (name, known[vnum])
                cd = num(it.get('cooldown'), 0, 604800, where + ' – co ile')
                items.append({'vnum': vnum, 'need': num(it.get('need'), 1, 10000, where + ' – ile oddać'),
                              'chance': num(it.get('chance'), 1, 100, where + ' – szansa'), 'cooldown': cd,
                              'bonus': bonuses(it.get('bonus'), where, allowed)})
            cats.append({'key': key, 'name': name, 'desc': str(c.get('desc') or '').strip()[:LIMITS['desc']],
                         'icon': icon_vnum, 'own_icon': own, 'level': num(c.get('level') or 1, 1, 250, '„%s” – od poziomu' % name),
                         'fin': bonuses(c.get('fin'), '„%s” – nagroda końcowa' % name, allowed), 'items': items})
        return {'cats': cats}

    def write(data):
        write_files(root, data)

    def enrich(vnums):
        known = names(vnums)
        return {v: {'name': known.get(v, '#%d' % v), 'icon': icon(v)} for v in known}

    @bp.route('/systemy/kolekcjoner', methods=['GET'])
    @login
    def systems_kolekcje():
        data = load()
        vnums = {c['icon'] for c in data['cats']} | {i['vnum'] for c in data['cats'] for i in c['items']}
        return render_template('dbeditor/systems_kolekcje.html', data=data, items=enrich(vnums), labels=sorted(labels().items(), key=lambda x: x[1].lower()),
                               cooldowns=COOLDOWNS, limits=LIMITS, arts=arts()[2], dbe_csrf=common.csrf_token(), sys_active='kolekcje', system=None)

    @bp.route('/systemy/kolekcjoner/szukaj', methods=['GET'])
    @login
    def systems_kolekcje_search():
        q = (request.args.get('q') or '').strip()[:40]
        if not q:
            found = names(START_ITEMS)
            vnums = [v for v in START_ITEMS if v in found]
        elif q.isdigit():
            got = rows('SELECT vnum FROM world.item_proto WHERE vnum = %s OR CAST(vnum AS CHAR) LIKE %s ORDER BY vnum LIMIT 60', (int(q), q + '%'))
            vnums = [int(r['vnum']) for r in got]
        else:
            # Nazwy w bazie bywaja zapisane bajtami UTF-8 w kolumnie latin1 - porownanie po bajtach, bez wielkosci liter.
            got = rows('SELECT vnum FROM world.item_proto WHERE LOWER(CONVERT(CAST(locale_name AS BINARY) USING utf8mb4)) LIKE %s '
                       'OR locale_name LIKE %s ORDER BY vnum LIMIT 60', ('%' + q.lower() + '%', '%' + q + '%'))
            vnums = [int(r['vnum']) for r in got]
        info = enrich(vnums)
        return jsonify([{'vnum': v, 'name': info[v]['name'], 'icon': info[v]['icon']} for v in vnums if v in info])

    def arts():
        from m2clientpack import kuznia_dodatki as kd
        base = kd.BASE / 'pliki' / kd.OKNO
        own = kd.own_art_dir()
        out = []
        for p in sorted(base.glob('*.tga')) if base.is_dir() else []:
            try: w, h = tga_info(p.read_bytes())
            except ValueError: continue
            out.append({'name': p.stem, 'w': w, 'h': h, 'own': (own / p.name).is_file(), 'label': ART_LABELS.get(p.stem, '')})
        out.sort(key=lambda a: (a['name'] not in ART_LABELS, a['name']))
        return base, own, out

    @bp.route('/systemy/kolekcjoner/grafika/<name>.png', methods=['GET'])
    @login
    def systems_kolekcje_art(name):
        base, own, _ = arts()
        if not re.fullmatch(r'[a-z0-9_]+', name): abort(404)
        for p in (own / (name + '.tga'), base / (name + '.tga')):
            if p.is_file():
                from flask import Response
                return Response(tga_png(p.read_bytes()), mimetype='image/png', headers={'Cache-Control': 'no-store'})
        abort(404)

    @bp.route('/systemy/kolekcjoner/grafika/<name>', methods=['POST'])
    @login
    def systems_kolekcje_art_set(name):
        if not common.check_csrf(): abort(403)
        base, own, items = arts()
        art = next((a for a in items if a['name'] == name), None)
        if art is None: abort(404)
        if request.form.get('usun') == '1':
            (own / (name + '.tga')).unlink(missing_ok=True)
            return jsonify({'ok': True})
        f = request.files.get('plik')
        raw = f.read(8 * 1024 * 1024 + 1) if f else b''
        try:
            if len(raw) > 8 * 1024 * 1024: raise ValueError('Plik za duży (max 8 MB).')
            w, h = tga_info(raw)
            if (w, h) != (art['w'], art['h']): raise ValueError('Zły rozmiar: %d×%d, ma być %d×%d.' % (w, h, art['w'], art['h']))
            tga_png(raw)
        except (ValueError, IndexError) as exc:
            return jsonify({'ok': False, 'error': str(exc)}), 400
        own.mkdir(parents=True, exist_ok=True)
        tmp = own / (name + '.tga.tmp'); tmp.write_bytes(raw); tmp.replace(own / (name + '.tga'))
        return jsonify({'ok': True})

    icon_cache = {}

    def all_icons():
        """Kazda ikona z gry raz (pierwszy przedmiot, ktory jej uzywa) - lista liczona raz na uruchomienie panelu."""
        if 'list' not in icon_cache:
            seen, out = set(), []
            for r in rows('SELECT vnum FROM world.item_proto ORDER BY vnum'):
                v = int(r['vnum']); u = icon(v)
                if u and u not in seen: seen.add(u); out.append((v, u))
            icon_cache['list'] = out
        return icon_cache['list']

    @bp.route('/systemy/kolekcjoner/ikony', methods=['GET'])
    @login
    def systems_kolekcje_icons():
        per = 150
        try: page = max(0, int(request.args.get('strona') or 0))
        except ValueError: page = 0
        allv = all_icons()
        part = allv[page * per:(page + 1) * per]
        known = names([v for v, _u in part])
        return jsonify({'items': [{'vnum': v, 'name': known.get(v, '#%d' % v), 'icon': u} for v, u in part],
                        'more': (page + 1) * per < len(allv), 'total': len(allv)})

    # Wlasna ikona kategorii (TGA 32x32): spool/systems/kolekcje/ikony/<klucz>.tga -> ROOT kat_<klucz>.tga
    @bp.route('/systemy/kolekcjoner/ikona/<key>.png', methods=['GET'])
    @login
    def systems_kolekcje_icon(key):
        p = root / 'ikony' / (key + '.tga')
        if not re.fullmatch(r'k[0-9]{1,6}', key) or not p.is_file(): abort(404)
        from flask import Response
        return Response(tga_png(p.read_bytes()), mimetype='image/png', headers={'Cache-Control': 'no-store'})

    @bp.route('/systemy/kolekcjoner/ikona/<key>', methods=['POST'])
    @login
    def systems_kolekcje_icon_set(key):
        if not common.check_csrf(): abort(403)
        if not re.fullmatch(r'k[0-9]{1,6}', key): abort(404)
        p = root / 'ikony' / (key + '.tga')
        if request.form.get('usun') == '1':
            p.unlink(missing_ok=True); return jsonify({'ok': True})
        f = request.files.get('plik')
        raw = f.read(1024 * 1024 + 1) if f else b''
        try:
            if len(raw) > 1024 * 1024: raise ValueError('Plik za duży.')
            if tga_info(raw) != (32, 32): raise ValueError('Ikona musi mieć 32×32 (TGA 24/32-bit).')
            tga_png(raw)
        except (ValueError, IndexError) as exc:
            return jsonify({'ok': False, 'error': str(exc)}), 400
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix('.tmp'); tmp.write_bytes(raw); tmp.replace(p)
        return jsonify({'ok': True})

    @bp.route('/systemy/kolekcjoner/zapisz', methods=['POST'])
    @login
    def systems_kolekcje_save():
        if not common.check_csrf(): abort(403)
        try:
            data = validate(json.loads(request.form.get('dane') or '{}'))
            write(data)
        except ValueError as exc:
            return jsonify({'ok': False, 'error': str(exc)}), 400
        return jsonify({'ok': True, 'data': data, 'time': time.strftime('%H:%M:%S')})
