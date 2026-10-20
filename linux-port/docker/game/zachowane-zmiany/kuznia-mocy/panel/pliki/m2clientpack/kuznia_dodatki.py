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


def _files():
    root = BASE / 'pliki'
    if not root.is_dir(): return {}
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def _hooks():
    p = BASE / 'hooks.json'
    return json.loads(p.read_text(encoding='latin-1')) if p.is_file() else {}


def raw_name(name):
    """Nazwa nowego wpisu ROOT taka jak u autora Kuzni (np. z "d:/"), inaczej podana."""
    p = BASE / 'nazwy.json'
    try:
        return json.loads(p.read_text(encoding='latin-1')).get(name, name) if p.is_file() else name
    except ValueError:
        return name


def packaged(name):
    """Pelny plik Kuzni z paczki (wersja autora Kuzni) albo None."""
    p = _files().get(name)
    return p.read_bytes() if p else None


def needed():
    """Nazwy wpisow ROOT, ktore budowanie musi odczytac (sprawdzenie obecnosci + pliki z podpieciami)."""
    return set(_files()) | set(_hooks())


def _hook(raw, rules, report, name):
    nl = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('latin-1').replace('\r\n', '\n')
    for r in rules:
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
        elif RAW_SEEN and raw_name(name).lower() not in RAW_SEEN:
            # Jest pod inna nazwa (np. bez "d:/" z wczesniejszej wersji) - klient jej nie widzi: dodaj pod wlasciwa.
            out[name] = path.read_bytes(); FORCE_NEW.add(name)
    gfx = sum(1 for n in out if not n.endswith('.py'))
    if gfx: report.append('dodano grafik: %d' % gfx)
    for name, rules in _hooks().items():
        if name not in decoded:
            report.append('brak %s w ROOT - podpięcia pominięte' % name); continue
        raw = _hook(decoded[name], rules, report, name)
        if raw != decoded[name]: decoded[name] = out[name] = raw
    return out, report
