# MT2009_NASZE_KUZNIA_DODATKI_V1: brakujace w cudzym ROOT moduly, grafiki i podpiecia Kuzni Mocy.
# Niczego nie wymaga: czego klient nie ma - dokladane w calosci; podpiecie bez znanej kotwicy - pomijane (raport).
import json
from pathlib import Path

BASE = Path(__file__).with_name('kuznia_dodatki')
LAST_REPORT = []  # raport ostatniego budowania ROOT
RAW_SEEN = set()  # dokladne nazwy wpisow budowanego ROOT (male litery)
FORCE_NEW = set()  # pliki do dodania jako nowy wpis pod wlasciwa nazwa


def fresh():
    """MT2009_NASZE_SWIEZY_START_V1: panel z instalatora (znacznik w paczce) -> domyslnie zero bonusow."""
    return (BASE / 'swiezy-start').is_file()


# MT2009_NASZE_OKNO_CTRLN_V2: grafiki okna Ctrl+N - zawsze z paczki (nowa wersja zastepuje stara w ROOT),
# a wlasne grafiki serwera (panel -> Kolekcjoner -> Wyglad okna) leza w spoolu i przezywaja ponowna instalacje.
OKNO = 'ymir work/ui/game/kuznia_okno/'


def own_art_dir():
    import os
    return Path(os.environ.get('M2PANEL_RATES_SPOOL') or '/opt/m2spool') / 'systems' / 'okno' / 'grafika'


def _files():
    root = BASE / 'pliki'
    if not root.is_dir(): return {}
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    own = own_art_dir()
    if own.is_dir():
        for p in own.glob('*.tga'):
            if OKNO + p.name in files: files[OKNO + p.name] = p
    # MT2009_NASZE_KOLEKCJE_V1: wlasne ikony kategorii Kolekcjonera (panel) -> kat_<klucz>.tga
    icons = own.parent.parent / 'kolekcje' / 'ikony'
    if icons.is_dir():
        for p in icons.glob('k*.tga'):
            files[OKNO + 'kat_' + p.name] = p
    return files


def _hooks():
    p = BASE / 'hooks.json'
    return json.loads(p.read_text(encoding='latin-1')) if p.is_file() else {}


def raw_name(name):
    """Nazwa nowego wpisu ROOT taka jak u autora Kuzni (np. z "d:/"), inaczej podana."""
    p = BASE / 'nazwy.json'
    default = 'd:/' + name if name.startswith(OKNO) else name  # grafiki okna: klient szuka ich pod "d:/ymir work/..."
    try:
        return json.loads(p.read_text(encoding='latin-1')).get(name, default) if p.is_file() else default
    except ValueError:
        return default


def packaged(name):
    """Pelny plik Kuzni z paczki (wersja autora Kuzni) albo None."""
    p = _files().get(name)
    return p.read_bytes() if p else None


def window():
    """MT2009_NASZE_OKNO_CTRLN_V2: nowe okno Ctrl+N (Misje + Kolekcjoner) - zawsze zamiast uimissionpanel.py klienta."""
    p = BASE / 'okno' / 'uimissionpanel.py'
    return p.read_bytes() if p.is_file() else None


# MT2009_NASZE_INNE_IKONY_V1: plik "icon/..." klient bierze najpierw z paczki "icon" (pierwszy folder sciezki), wiec ikony
# o tej samej nazwie nie da sie podmienic z ROOT ani z dbdata. Dziala: ikona pod wlasna nazwa w gamedata + wpis
# item_list.txt (gamedata) wskazujacy na nia - patch_gamedata() przy budowaniu ROOT (gdy wgrano tez gamedata).
# Ikony z ROOT z poprzedniej proby (INNE_ICONS) sa usuwane.
INNE_ICONS = {'skrzynka_ku': ('icon/item/50035.tga', '50035.tga'), 'klepsydra': ('icon/item/71102.tga', '71102.tga')}
INNE_LOOK = {'skrzynka_ku': (50035, 'icon/item/50035.tga', 'icon/item/kuznia_skrzynia_ku_50035.tga', '50035.tga'),
             'klepsydra': (71102, 'icon/item/71102.tga', 'icon/item/kuznia_klepsydra_71102.tga', '71102.tga')}


def patch_gamedata(index, data):
    """(index, data, raport) gamedata klienta z ikonami wlaczonych opcji Inne (wylaczone - oryginalna ikona)."""
    import re, zlib
    from . import eterpack
    ver, entries = eterpack.read_index_bytes(index)
    by = {}
    for e in entries:
        by.setdefault(e.name.replace('\\', '/').lower(), e)
    if 'gamedata/item_list.txt' not in by:
        raise ValueError('To nie jest gamedata klienta (brak item_list.txt).')
    on, report = inne_on(), []
    lst = eterpack.read_entry(data, by['gamedata/item_list.txt'])
    files = {}
    for key, (vnum, orig, mine, fname) in INNE_LOOK.items():
        want = mine if key in on else orig
        pat = re.compile(rb'(?m)^([ \t]*%d\t[^\t\r\n]+\t)([^\t\r\n]+)' % vnum)
        m = pat.search(lst)
        if not m:
            report.append('brak wpisu %d w item_list.txt - ikona pominięta' % vnum); continue
        if m.group(2).decode('latin-1').lower() in (orig, mine) and m.group(2).decode('latin-1').lower() != want:
            lst = lst[:m.start(2)] + want.encode('ascii') + lst[m.end(2):]
            report.append('%s: ikona %s' % ('włączone' if key in on else 'wyłączone', want))
        if key in on:
            files[mine] = (BASE.parent / 'kuznia_inne' / fname).read_bytes()
    files['gamedata/item_list.txt'] = lst
    out, changed = bytearray(data), False
    for name, raw in files.items():
        e = by.get(name)
        if e is not None and eterpack.read_entry(data, e) == raw: continue
        changed = True
        if e is None:
            e = eterpack.Entry(bytes(192)); e.id = max((x.id for x in entries), default=-1) + 1
            e.name = name; e.fcrc = eterpack.name_crc(name); e.ctype = 2; entries.append(e); by[name] = e
        blob = eterpack.encode_entry(raw, e.ctype)
        e.pos = len(out); e.size = len(blob); e.real = (e.size + 255) // 256 * 256; e.dcrc = zlib.crc32(blob) & 0xffffffff
        out.extend(blob); out.extend(b'\0' * (e.real - e.size))
    if not changed:
        return index, data, report or ['gamedata bez zmian']
    ni = eterpack.write_index_bytes(ver, entries); nd = bytes(out)
    for e in eterpack.read_index_bytes(ni)[1]:
        n = e.name.replace('\\', '/').lower()
        if n in files and eterpack.read_entry(nd, e) != files[n]: raise ValueError('Błąd weryfikacji gamedata.')
    return ni, nd, report


def inne_on():
    try:
        state = json.loads((own_art_dir().parent.parent / 'inne' / 'stan.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    return {k for k, v in state.items() if k in INNE_ICONS and (v or {}).get('on')}


def needed():
    """Nazwy wpisow ROOT, ktore budowanie musi odczytac (sprawdzenie obecnosci + pliki z podpieciami)."""
    return set(_files()) | set(_hooks()) | {n for n, _f in INNE_ICONS.values()}


def _hook(raw, rules, report, name):
    nl = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('latin-1').replace('\r\n', '\n')
    for r in rules:
        # Stare, bledne wersje podpiecia z wczesniejszego ROOT (np. "KC": lambda) - usuwane przed dopisaniem nowego.
        for bad in r.get('usun', []):
            if bad in text:
                text = ''.join(x for x in text.splitlines(keepends=True) if bad not in x)
                report.append('usunięto stare podpięcie %s: %s' % (name, bad))
        if r['marker'] in text: continue
        if r.get('need') and r['need'] not in text:
            report.append('pominięto podpięcie %s (%s): brak %s' % (name, r['marker'], r['need'])); continue
        L = text.splitlines(keepends=True)
        k = next((i for i, x in enumerate(L) if x.startswith(r['anchor'])), None)
        if k is None:
            report.append('pominięto podpięcie %s (%s): nieznana wersja pliku' % (name, r['marker'])); continue
        L.insert(k + 1 if r['where'] == 'po' else k, r['block'])
        text = ''.join(L)
        report.append('dodano podpięcie %s: %s' % (name, r['marker']))
    return text.replace('\n', nl).encode('latin-1')


def apply(decoded):
    """decoded: {nazwa: bajty} z ROOT (tylko needed()). Zwraca (zamiany, raport); zmienia decoded na miejscu,
    zeby dalsze latki Kuzni (np. wyglad okna misji) widzialy dolozone pliki."""
    out, report = {}, []
    FORCE_NEW.clear()
    for name, path in sorted(_files().items()):
        if name not in decoded:
            decoded[name] = out[name] = path.read_bytes()
            if name.endswith('.py'): report.append('dodano moduł %s' % name)
        elif name.startswith(OKNO):
            raw = path.read_bytes()
            if decoded[name] != raw: decoded[name] = out[name] = raw
        elif RAW_SEEN and raw_name(name).lower() not in RAW_SEEN:
            # Jest pod inna nazwa (np. bez "d:/" z wczesniejszej wersji) - klient jej nie widzi: dodaj pod wlasciwa.
            out[name] = path.read_bytes(); FORCE_NEW.add(name)
    for key, (name, fname) in INNE_ICONS.items():
        # Ikona z poprzedniej proby (w ROOT nie dziala - patrz patch_gamedata): tylko nasza kopia jest usuwana.
        if name in decoded and decoded[name] == (BASE.parent / 'kuznia_inne' / fname).read_bytes():
            out[name] = None; report.append('usunięto z ROOT starą próbę ikony: %s' % name)
    gfx = sum(1 for n, raw in out.items() if raw is not None and not n.endswith('.py'))
    if gfx: report.append('dodano grafik: %d' % gfx)
    for name, rules in _hooks().items():
        if name not in decoded:
            report.append('brak %s w ROOT - podpięcia pominięte' % name); continue
        raw = _hook(decoded[name], rules, report, name)
        if raw != decoded[name]: decoded[name] = out[name] = raw
    return out, report
