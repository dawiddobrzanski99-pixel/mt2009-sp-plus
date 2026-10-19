# CUSTOM_MAP_MATERIAL_CHESTS_V1: additive client export, preserves prior edits.
from pathlib import Path
import json

def extend(query, base, files, summary):
 from . import clientfiles, dbdata
 root=Path(__file__).resolve().parent
 config=json.loads((root/'custom_material_boxes.json').read_text(encoding='utf-8'))
 ids=sorted(int(v) for v in config)
 marks=','.join(['%s']*len(ids))
 found={int(r['vnum']):dict(r) for r in query('SELECT *, CAST(name AS BINARY) AS name_bytes, CAST(locale_name AS BINARY) AS locale_name_bytes FROM world.item_proto WHERE vnum IN ('+marks+')',tuple(ids))}
 if set(found)!=set(ids): raise ValueError('Brakuje nowych skrzynek w item_proto; najpierw instalacja bazy.')
 for row in found.values():
  for col in ('name','locale_name'):
   value=row.pop(col+'_bytes',None)
   if value is not None:row[col]=value
 notes=summary.setdefault('notes',[])
 blob,changed=clientfiles.patch_item_proto(files.get('gamedata/item_proto',base.file('gamedata/item_proto')),{v:set(clientfiles.ITEM_FIELDS) for v in ids},found,notes)
 files['gamedata/item_proto']=blob
 summary['material_boxes']=ids
 item_list='gamedata/item_list.txt'
 if item_list in files:source=files[item_list]
 elif item_list in base.names():source=base.file(item_list)
 else:source=(root/'custom_material_item_list.base.txt').read_bytes()
 dbdata.OPTIONAL_FILES[item_list]=2
 replacement={v:{1:'ETC',2:config[str(v)]['icon']} for v in ids}
 files[item_list]=clientfiles.patch_tab_text(source,replacement,3)[0]
 desc='locale/pl/itemdesc.txt'
 files[desc]=clientfiles.patch_tab_text(files.get(desc,base.file(desc)),{v:{1:config[str(v)]['name'],2:config[str(v)]['description'],3:''} for v in ids},4)[0]
 for p in (root/'custom_material_assets').iterdir():
  if not p.is_file() or p.name not in {str(v)+'.tga' for v in ids}:continue
  name='icon/item/'+p.name
  dbdata.OPTIONAL_FILES[name]=2
  files[name]=p.read_bytes()
 return files,summary
