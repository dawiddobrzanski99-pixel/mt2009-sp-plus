# FOCUSED_EGZO_RADA_STACK_TRADE_V1: no changes to equipment or other items.
from . import clientfiles
IDS=(39008,39030,71001,71094,71201)
CLEAR=(1<<8)|(1<<13)|(1<<15)|(1<<16)
def extend(files):
 name='gamedata/item_proto'
 if name not in files:return files
 version,stride,records=clientfiles.read_item_proto(files[name])
 for vnum in IDS:
  if vnum not in records:continue
  record=records[vnum]
  clientfiles.set_field(record,'stack',200)
  clientfiles.set_field(record,'flag',clientfiles.get_field(record,'flag')|4)
  clientfiles.set_field(record,'antiflag',clientfiles.get_field(record,'antiflag')&~CLEAR)
 files[name]=clientfiles.write_item_proto(version,stride,records)
 return files
