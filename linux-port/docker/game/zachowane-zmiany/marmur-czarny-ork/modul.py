#!/usr/bin/env python3
"""MT2009_NASZE_MARMUR_CZARNY_ORK_V1 - modul: Marmur Czarnego Orka (70108).

  python3 modul.py --check            stan: jest / brak / konflikt (nic nie zmienia)
  python3 modul.py --apply            wgrywa brakujace czesci (zrodla, panel, baza); bez kompilacji
  python3 modul.py --revert           usuwa bloki modulu ze zrodel i panelu, rekord 70108 zostaje

Zmiany wstawiane sa w miejsca kotwic, wiec dzialaja tez na nowszej wersji pliku autora.
Kazde --apply/--revert robi kopie zmienianych plikow w /opt/metin2/kopie-naszych-zmian/.
"""
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = Path('/opt/metin2/linux-port/docker')
SRC = PROJECT / 'game/src/server/game/src'
PANEL = PROJECT / 'seban-panel/m2clientpack'
PANEL_CONTAINER = 'metin2-seban-panel'
PANEL_IN_CONTAINER = '/app/m2clientpack/'
TAG = b'MT2009_NASZE_MARMUR_CZARNY_ORK_V1'
BEGIN = b'// ' + TAG + b'_BEGIN'
END = b'// ' + TAG + b'_END'

# (plik, kotwica, tekst wstawiany ZA kotwica)
PATCHES = [
    (SRC / 'item_manager.cpp',
     b'#include "chest50122_policy.h"\n',
     BEGIN + b'\n#include "custom_marmur_czarny_ork.h"\n' + END + b'\n'),
    (SRC / 'item_manager.cpp',
     b'\n\tSharedFinalBossDrops(pkChr,vec_item);\n',
     b'\t' + BEGIN + b'\n'
     b'\t{\n'
     b'\t\tconst int marblePct = custom_marmur_czarny_ork::ChancePer10000(pkChr, Mt2009PlusBaseMap(pkChr));\n'
     b'\t\tif (marblePct > 0 && number(1, 10000) <= marblePct)\n'
     b'\t\t{\n'
     b'\t\t\tLPITEM marble = CreateItem(custom_marmur_czarny_ork::ItemVnum, 1, 0, true);\n'
     b'\t\t\tif (marble)\n'
     b'\t\t\t{\n'
     b'\t\t\t\tmarble->SetSocket(0, custom_marmur_czarny_ork::RaceVnum);\n'
     b'\t\t\t\tvec_item.emplace_back(marble);\n'
     b'\t\t\t}\n'
     b'\t\t}\n'
     b'\t}\n'
     b'\t' + END + b'\n'),
    (SRC / 'char_item.cpp',
     b'\n\tDWORD dwVnum = item->GetSocket(0);\n',
     b'\t' + BEGIN + b'\n'
     b'\tif (item->GetVnum() == 70108)\n'
     b'\t\tdwVnum = 636; // Marmur Czarnego Orka zawsze przemienia w Czarnego Orka\n'
     b'\t' + END + b'\n'),
    (SRC / 'char_item.cpp',
     b'\t\tcase 70107 :\n',
     b'\t\t' + BEGIN + b'\n\t\tcase 70108 :\n\t\t' + END + b'\n'),
]
PY_BEGIN = b'# ' + TAG + b'_BEGIN'
PY_END = b'# ' + TAG + b'_END'
DBSOURCE_BLOCK = (b'\n' + PY_BEGIN + b'\n'
    b'_marmur_czarny_ork_previous = client_files\n'
    b'def client_files(*args, **kwargs):\n'
    b'    files, summary = _marmur_czarny_ork_previous(*args, **kwargs)\n'
    b"    query = args[0] if args else kwargs['query']\n"
    b"    base = args[1] if len(args) > 1 else kwargs['base']\n"
    b'    from .custom_marmur_czarny_ork_client import extend\n'
    b'    return extend(query, base, files, summary)\n'
    + PY_END + b'\n')
NEW_FILES = [
    (HERE / 'custom_marmur_czarny_ork.h', SRC / 'custom_marmur_czarny_ork.h'),
    (HERE / 'custom_marmur_czarny_ork_client.py', PANEL / 'custom_marmur_czarny_ork_client.py'),
]
SQL_CHECK = "SELECT (SELECT COUNT(*) FROM world.item_proto WHERE vnum=70108),(SELECT COUNT(*) FROM player.item_proto WHERE vnum=70108);"


def sql(query):
    out = subprocess.run(['docker', 'exec', '-i', 'metin2-db', 'sh', '-c',
                          'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -uroot -N'],
                         input=query.encode(), stdout=subprocess.PIPE, check=True).stdout
    return out.decode().strip()


def patch_state(raw, anchor, block):
    if block in raw:
        return 'jest'
    return 'brak' if raw.count(anchor) == 1 else 'konflikt (kotwica x%d)' % raw.count(anchor)


def report():
    rows, ok = [], True
    for path, anchor, block in PATCHES:
        state = patch_state(path.read_bytes(), anchor, block) if path.is_file() else 'konflikt (brak pliku)'
        rows.append((path, 'blok kodu', state))
    raw = (PANEL / 'dbsource.py').read_bytes()
    rows.append((PANEL / 'dbsource.py', 'eksport klienta', 'jest' if PY_BEGIN in raw else 'brak'))
    for src, dst in NEW_FILES:
        state = 'brak' if not dst.is_file() else ('jest' if dst.read_bytes() == src.read_bytes() else 'konflikt (inna tresc)')
        rows.append((dst, 'nowy plik', state))
    world, player = sql(SQL_CHECK).split()
    rows.append(('world.item_proto', '70108', 'jest' if world == '1' else 'brak'))
    rows.append(('player.item_proto', '70108', 'jest' if player == '1' else 'brak'))
    for path, what, state in rows:
        print('%-10s %-16s %s' % (state.split()[0].upper(), what, path))
        ok = ok and not state.startswith('konflikt')
    return rows, ok


def backup_dir():
    d = Path('/opt/metin2/kopie-naszych-zmian/marmur-czarny-ork-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    d.mkdir(parents=True)
    d.chmod(0o700)
    return d


def save_copy(backup, path):
    if path.is_file():
        dest = backup / str(path).lstrip('/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def write(path, raw):
    tmp = path.with_name(path.name + '.marmur-new')
    tmp.write_bytes(raw)
    if path.exists():
        shutil.copystat(path, tmp)
    else:
        tmp.chmod(0o644)
    tmp.replace(path)


def to_panel_container(path):
    subprocess.run(['docker', 'cp', str(path), PANEL_CONTAINER + ':' + PANEL_IN_CONTAINER + path.name], check=True)


def apply():
    rows, ok = report()
    if not ok:
        raise SystemExit('STOP: konflikt - nic nie zmieniono.')
    backup = backup_dir()
    touched = sorted({p for p, _, _ in PATCHES} | {PANEL / 'dbsource.py'} | {d for _, d in NEW_FILES}, key=str)
    for path in touched:
        save_copy(backup, path)
    (backup / 'item_proto-70104-przed.sql').write_text(sql(
        "SELECT * FROM world.item_proto WHERE vnum IN (70104,70108); SELECT * FROM player.item_proto WHERE vnum IN (70104,70108);"))
    for src, dst in NEW_FILES:
        if not dst.is_file():
            write(dst, src.read_bytes())
            print('Dodano:', dst)
    for path, anchor, block in PATCHES:
        raw = path.read_bytes()
        if block in raw:
            continue
        write(path, raw.replace(anchor, anchor + block, 1))
        print('Zmieniono:', path)
    raw = (PANEL / 'dbsource.py').read_bytes()
    if PY_BEGIN not in raw:
        write(PANEL / 'dbsource.py', raw.rstrip(b'\n') + b'\n' + DBSOURCE_BLOCK)
        print('Zmieniono:', PANEL / 'dbsource.py')
    for name in ('dbsource.py', 'custom_marmur_czarny_ork_client.py'):
        to_panel_container(PANEL / name)
    subprocess.run(['docker', 'exec', PANEL_CONTAINER, 'python3', '-m', 'py_compile',
                    PANEL_IN_CONTAINER + 'dbsource.py', PANEL_IN_CONTAINER + 'custom_marmur_czarny_ork_client.py'], check=True)
    for db in ('world', 'player'):
        sql("CREATE TEMPORARY TABLE %s.tmp_marmur AS SELECT * FROM %s.item_proto WHERE vnum=70104;"
            "UPDATE %s.tmp_marmur SET vnum=70108, locale_name='Marmur Czarnego Orka', flag=flag|4;"
            "INSERT IGNORE INTO %s.item_proto SELECT * FROM %s.tmp_marmur;" % ((db,) * 5))
    print('Kopia:', backup)
    print('Gotowe w zrodlach, panelu i bazie. NIE skompilowano gry i NIE odswiezono dbdata.')
    report()


def revert():
    backup = backup_dir()
    for path in sorted({p for p, _, _ in PATCHES}, key=str):
        raw = path.read_bytes()
        save_copy(backup, path)
        for _, anchor, block in PATCHES:
            raw = raw.replace(block, b'')
        write(path, raw)
    db = PANEL / 'dbsource.py'
    save_copy(backup, db)
    write(db, db.read_bytes().replace(DBSOURCE_BLOCK, b''))
    to_panel_container(db)
    print('Usunieto bloki modulu. Kopia:', backup)
    print('Rekord 70108 i nowe pliki zostaja (nieuzywane). Gra wymaga ponownej kompilacji.')


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '--check'
    {'--check': lambda: report(), '--apply': apply, '--revert': revert}[arg]()
