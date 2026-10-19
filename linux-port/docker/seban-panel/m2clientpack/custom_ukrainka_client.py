
"""CUSTOM_UKRAINKA_CLIENT_V1: persistent NPC assets and client records."""
from pathlib import Path
import struct
from . import eterpack

MOB_KEY=(4813894,18955,552631,6822045)
NPC=30099
NAME=b'Ukrainka'
ASSETS=Path(__file__).resolve().parent/'custom_ukrainka_assets'
MODEL_FILES=(
    'dane_remy_npc.msm','dane_remy_npc.gr2','motlist.txt',
    'wait.msa','wait.gr2','walk.msa','walk.gr2','a0002_1a.tga'
)

def patch_mob_proto(blob):
    if len(blob)<12 or blob[:4]!=b'MMPT':
        raise ValueError('Unsupported mob_proto header: '+blob[:16].hex())
    count,size=struct.unpack_from('<II',blob,4)
    if not count or size!=len(blob)-12:
        raise ValueError('Unsupported mob_proto header layout: '+blob[:16].hex())
    raw=eterpack.mcoz_decode(blob[12:],MOB_KEY)
    if len(raw)%count:
        raise ValueError('Invalid mob_proto record count.')
    stride=len(raw)//count
    if not 55<=stride<=1024:
        raise ValueError('Unsupported mob_proto record size: '+str(stride))
    records={}
    for offset in range(0,len(raw),stride):
        rec=raw[offset:offset+stride]
        vnum=struct.unpack_from('<I',rec,0)[0]
        if vnum in records:
            raise ValueError('Duplicate mob_proto VNUM: '+str(vnum))
        records[vnum]=rec
    if 9003 not in records:
        raise ValueError('Missing merchant template 9003.')
    template=records[9003]
    # Standard client fields: VNUM, internal name[25], locale name[25], type.
    for start in (4,29):
        field=template[start:start+25]
        if b'\0' not in field or not field.split(b'\0',1)[0]:
            raise ValueError('Unsupported NPC name layout.')
    if template[54]!=1:
        raise ValueError('Merchant record does not have the expected NPC type.')
    if NPC in records:
        existing=records[NPC]
        if all(existing[s:s+25].split(b'\0',1)[0]==NAME for s in (4,29)):
            return blob, count, stride
        raise ValueError('Client NPC number 30099 is already occupied.')
    rec=bytearray(template)
    struct.pack_into('<I',rec,0,NPC)
    for start in (4,29):
        rec[start:start+25]=NAME.ljust(25,b'\0')
    records[NPC]=bytes(rec)
    new_raw=b''.join(records[v] for v in sorted(records))
    payload=eterpack.mcoz_encode(new_raw,MOB_KEY)
    if eterpack.mcoz_decode(payload,MOB_KEY)!=new_raw:
        raise ValueError('NPC compression verification failed.')
    result=b'MMPT'+struct.pack('<II',len(records),len(payload))+payload
    return result,len(records),stride

def patch_npc_list(raw):
    rows=raw.decode('latin1').splitlines()
    found=[s.split() for s in rows if s.split() and s.split()[0]=='30099']
    if found:
        if found!=[['30099','dane_remy_npc']]:
            raise ValueError('NPC registration 30099 is occupied.')
        return raw
    return raw.rstrip(b'\r\n')+b'\r\n30099\tdane_remy_npc\r\n'

def extend(base,files,summary):
    from . import dbdata
    def current(name,fallback):
        if name in files:
            return files[name]
        if name in base.names():
            return base.file(name)
        return (ASSETS/fallback).read_bytes()

    name='gamedata/mob_proto'
    files[name]=patch_mob_proto(current(name,'mob_proto.base'))[0]
    dbdata.OPTIONAL_FILES[name]=2

    name='gamedata/npclist.txt'
    files[name]=patch_npc_list(current(name,'npclist.base.txt'))
    dbdata.OPTIONAL_FILES[name]=2

    prefix='d:/ymir work/npc/dane_remy_npc/'
    for filename in MODEL_FILES:
        name=prefix+filename
        files[name]=(ASSETS/filename).read_bytes()
        dbdata.OPTIONAL_FILES[name]=2

    name='icon/item/59011.tga'
    files[name]=(ASSETS/'59011.tga').read_bytes()
    dbdata.OPTIONAL_FILES[name]=2
    summary['ukrainka_npc']=NPC
    summary.setdefault('notes',[]).append(
        'Ukrainka: dane NPC, rejestracja modelu, animacje i ikona skrzyni.'
    )
    return files,summary
