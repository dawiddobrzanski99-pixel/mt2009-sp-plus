#!/usr/bin/env python3
"""Kuznia Mocy: doklada moduly Kuzni do panelu Seban (seban-panel autora).
Uzycie: instaluj_panel.py PAKIET_PANELU KATALOG_SEBAN_PANEL
PAKIET_PANELU = pliki/ (drzewo jak w seban-panel) + init.txt (linie install) + nav.txt (grupa menu).
Ponowne uruchomienie: pliki nadpisane nowa wersja, wpisy nie dublowane (po znacznikach MT2009_NASZE_)."""
import re, shutil, sys
from pathlib import Path

pkg, dst = Path(sys.argv[1]), Path(sys.argv[2])
# Dodatki ROOT i dawne ustawienia autora z poprzedniej instalacji: tylko to, co jest w tej paczce.
shutil.rmtree(dst / 'm2clientpack' / 'kuznia_dodatki', ignore_errors=True)
n = 0
for f in (pkg / 'pliki').rglob('*'):
    if f.is_file():
        t = dst / f.relative_to(pkg / 'pliki')
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, t); n += 1
print('pliki panelu: %d' % n)

# dbeditor/__init__.py: linie install przed rejestracja blueprintu (stare wpisy Kuzni zastapione).
init = dst / 'dbeditor' / '__init__.py'
text = init.read_text(encoding='utf-8')
mine = (pkg / 'init.txt').read_text(encoding='utf-8').splitlines(keepends=True)
names = [re.search(r'"(dbeditor\.\w+)"', x).group(1) for x in mine]
L = [x for x in text.splitlines(keepends=True) if not any('"%s"' % nm in x for nm in names)]
k = next(i for i, x in enumerate(L) if 'app.register_blueprint(bp)' in x)
L[k:k] = mine
init.write_text(''.join(L), encoding='utf-8')
print('dbeditor/__init__.py: %d modulow' % len(mine))

# templates/_nav.html: grupa "Kuznia Mocy" przed grupa Ustawienia (albo na koncu listy).
nav = dst / 'templates' / '_nav.html'
text = nav.read_text(encoding='utf-8')
block = (pkg / 'nav.txt').read_text(encoding='utf-8')
mark = re.search(r"'mark': '(\w+)'", block).group(1)
L = text.splitlines(keepends=True)
if mark in text:  # stara wersja grupy: wytnij do jej ']},'
    i = next(i for i, x in enumerate(L) if mark in x)
    j = next(j for j in range(i, len(L)) if L[j].strip() == ']},')
    del L[i:j + 1]
k = next((i for i, x in enumerate(L) if "{'id': 'ustawienia'" in x), None)
if k is None:
    k = max(i for i, x in enumerate(L) if x.strip() == ']},') + 1
L[k:k] = [block if block.endswith('\n') else block + '\n']
nav.write_text(''.join(L), encoding='utf-8')
print('menu: grupa Kuznia Mocy')
