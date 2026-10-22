# MT2009_NASZE_INNE_KLIENT_V1: Kuznia Mocy -> "Inne" w plikach klienta (dbdata).
# Wlaczona opcja: wyglad przedmiotu (ikona pod oryginalna nazwa z item_list.txt klienta + opis w itemdesc).
# item_list.txt klienta zostaje nietkniety (lista panelu jest niepelna - podmiana zepsulaby inne ikony).
# Wylaczona opcja: nic nie dokladane - paczka dbdata wraca do oryginalu (gracz pobiera nowe pliki / patcher sam).
import json
from pathlib import Path

ICONS = Path(__file__).resolve().parent / 'kuznia_inne'
LOOK = {
    'sakiewka_kd': {27999: ('Sakiewka Kamieni Dusz', 'Zawiera losowy Kamień Duszy +0 do +4.', None)},
    'skrzynka_ku': {50035: ('Skrzynia z KU', 'Zawiera jedną losową Księgę Umiejętności.', 'icon/item/50035.tga')},
    'klepsydra': {71102: ('Klepsydra Biologa', 'Zeruje czas oczekiwania u Biologa. Wypada z Metinów i bossów (2%).',
                          'icon/item/71102.tga')},
}


def enabled():
    try:
        from dbeditor import dropfiles
        spool = Path(dropfiles.spool_dir())
    except Exception:
        import os
        spool = Path(os.environ.get('M2_RATES_SPOOL') or '/opt/m2spool')
    try:
        state = json.loads((spool / 'systems' / 'inne' / 'stan.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    return [k for k in LOOK if (state.get(k) or {}).get('on')]


def extend(base, files, summary):
    from . import clientfiles, dbdata
    keys = enabled()
    if not keys:
        return files, summary
    desc, done = {}, []
    for key in keys:
        for vnum, (name, text, icon) in LOOK[key].items():
            desc[vnum] = {1: name, 2: text, 3: ''}
            if icon and (ICONS / ('%d.tga' % vnum)).is_file():
                files[icon] = (ICONS / ('%d.tga' % vnum)).read_bytes()
                dbdata.OPTIONAL_FILES.setdefault(icon, 2)
            done.append(vnum)
    name = 'locale/pl/itemdesc.txt'
    files[name], _ = clientfiles.patch_tab_text(files.get(name, base.file(name)), desc, 4)
    summary['kuznia_inne'] = sorted(done)
    return files, summary
