# MT2009_NASZE_MARMUR_CZARNY_ORK_V1: additive client export of item 70108, preserves prior edits.
from pathlib import Path

VNUM = 70108
ICON = 'icon/item/70104.tga'
NAME = u'Marmur Czarnego Orka'
DESC = u'Przemienia w Czarnego Orka. Możesz zamienić się w potwora ukrytego w marmurze.'


def extend(query, base, files, summary):
 from . import clientfiles, dbdata
 rows = query('SELECT *, CAST(name AS BINARY) AS name_bytes, CAST(locale_name AS BINARY) AS locale_name_bytes FROM world.item_proto WHERE vnum=%s', (VNUM,))
 if len(rows) != 1:
  raise ValueError('Brak 70108 w world.item_proto; najpierw instalacja bazy (marmur-czarny-ork).')
 row = dict(rows[0])
 for col in ('name', 'locale_name'):
  value = row.pop(col + '_bytes', None)
  if value is not None:
   row[col] = value
 notes = summary.setdefault('notes', [])
 blob, _ = clientfiles.patch_item_proto(files.get('gamedata/item_proto', base.file('gamedata/item_proto')),
                                        {VNUM: set(clientfiles.ITEM_FIELDS)}, {VNUM: row}, notes)
 files['gamedata/item_proto'] = blob
 item_list = 'gamedata/item_list.txt'
 if item_list in files:
  source = files[item_list]
 elif item_list in base.names():
  source = base.file(item_list)
 else:
  source = (Path(__file__).resolve().parent / 'custom_material_item_list.base.txt').read_bytes()
 dbdata.OPTIONAL_FILES[item_list] = 2
 files[item_list] = clientfiles.patch_tab_text(source, {VNUM: {1: 'ETC', 2: ICON}}, 3)[0]
 desc = 'locale/pl/itemdesc.txt'
 files[desc] = clientfiles.patch_tab_text(files.get(desc, base.file(desc)), {VNUM: {1: NAME, 2: DESC, 3: ''}}, 4)[0]
 summary['marmur_czarny_ork'] = VNUM
 return files, summary
