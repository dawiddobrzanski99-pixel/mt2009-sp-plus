# Pelne budowanie ROOT (jak w panelu) na podanych ROOT-ach; zapis zmienionych .py do /out/<nazwa> (test py2.7).
import os, sys
from pathlib import Path
sys.path.insert(0, '/app')
from m2clientpack import eterpack as ep, kuznia_dodatki as kd, horse_editor as he
import dbeditor.systems_horse as sh
store = sh.Store(Path('/opt/m2spool/systems/horse'))
cfg = store.read()
assets = {r['icon']: (store.root / 'assets' / Path(r['icon']).name).read_bytes() for r in cfg['levels'] if r['icon']}
for d in sys.argv[1:]:
    print('===', d)
    idx = open(d + '/root.index', 'rb').read(); dat = open(d + '/root.data', 'rb').read()
    try:
        ni, nd, man = he.patch_pack(idx, dat, cfg, assets)
    except Exception as x:
        print('BLAD:', type(x).__name__, x); continue
    print('zmienione/dodane wpisy:', len(man))
    for r in kd.LAST_REPORT: print('  ' + r)
    ver, ents = ep.read_index_bytes(ni)
    tag = os.path.basename(d)
    for e in ents:
        n = e.name.replace('\\', '/').lower()
        if n.endswith('.py') and any(m['path'] == n for m in man):
            p = '/out/%s/%s' % (tag, n); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').write(ep.read_entry(nd, e))
