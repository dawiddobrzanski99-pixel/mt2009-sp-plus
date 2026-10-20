"""Immutable client editions from uploaded packs and the existing dbdata publisher.

Never replace the operator's global ROOT with a different user's uploaded ROOT.
The editor publishes a complete, pinned ZIP through its own authenticated routes.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import time
import uuid
import zipfile
import zlib
from . import horse_editor as horse, dbdata, eterpack

PACKS=('root.index','root.data','gamedata.index','gamedata.data','dbdata.index','dbdata.data')
ALLOWED=set(PACKS)|{'dbdata_stamp.txt','klient-komplet.zip','manifest.json'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def validate_pair(index,data):
    if len(index)>32*1024*1024 or len(data)>512*1024*1024:raise ValueError('Przekroczony limit paczki.')
    if index[:4]!=b'EPKD' and (len(index)<16 or struct.unpack_from('<I',index,12)[0]>32*1024*1024):raise ValueError('Nieprawidłowy indeks.')
    version,entries=eterpack.read_index_bytes(index)
    if version!=2 or len(entries)>50000:raise ValueError('Nieobsługiwany indeks paczki.')
    total=0
    for entry in entries:
        name=entry.name.replace('\\','/')
        if name.startswith('/') or '..' in name.split('/') or not name:raise ValueError('Niebezpieczna nazwa wpisu.')
        if entry.ctype not in (0,1,2) or min(entry.pos,entry.size,entry.real)<0 or entry.pos+entry.size>len(data) or entry.size>32*1024*1024:raise ValueError('Uszkodzony lub nieobsługiwany wpis paczki.')
        blob=data[entry.pos:entry.pos+entry.size]
        if zlib.crc32(blob)&0xffffffff!=entry.dcrc:raise ValueError('Niezgodna para index/data: CRC.')
        if entry.ctype and (len(blob)<16 or struct.unpack_from('<I',blob,12)[0]>32*1024*1024):raise ValueError('Przekroczony limit wpisu.')
        total+=struct.unpack_from('<I',blob,12)[0] if entry.ctype else len(blob)
        if total>1024*1024*1024:raise ValueError('Przekroczony limit rozpakowania.')

def current_dbdata(publisher):
    if publisher is None:raise ValueError('Brak skonfigurowanego eksportera dbdata.')
    if not publisher.refresh():raise ValueError('Nie udało się odświeżyć znacznika dbdata.')
    entry=publisher.current();blobs={}
    for name in ('dbdata.index','dbdata.data'):
        path,size,digest=entry['files'][name]
        if int(size)>512*1024*1024:raise ValueError('Przekroczony limit dbdata.')
        raw=Path(path).read_bytes()
        if len(raw)!=size or sha(raw).upper()!=digest.upper():raise ValueError('Niezgodna suma eksportu '+name)
        blobs[name]=raw
    validate_pair(blobs['dbdata.index'],blobs['dbdata.data'])
    actual=dbdata.pack_stamp(publisher.latest_base(),blobs['dbdata.index'],blobs['dbdata.data'])
    if actual!=entry['stamp'] or publisher.current_stamp()!=actual:raise ValueError('Eksport dbdata nie odpowiada znacznikowi serwera.')
    blobs['dbdata_stamp.txt']=dbdata.stamp_text_sizes(actual,len(blobs['dbdata.index']),len(blobs['dbdata.data']))
    return blobs,actual

def token(root):
    path=Path(root)/'last-client-publication.json'
    return sha(path.read_bytes()) if path.exists() else ''

def build(root,config,index,data,game_index,game_data,publisher,assets=None):
    """Prepare a private immutable edition; does not change its published pointer."""
    validate_pair(game_index,game_data)
    new_index,new_data,changes=horse.patch_pack(index,data,config,assets)
    blobs,stamp=current_dbdata(publisher)
    blobs.update({'root.index':new_index,'root.data':new_data,'gamedata.index':game_index,'gamedata.data':game_data})
    releases=Path(root)/'releases';releases.mkdir(parents=True,exist_ok=True,mode=0o2770)
    stage=Path(tempfile.mkdtemp(prefix='.building-',dir=releases))
    release=uuid.uuid4().hex
    try:
        meta=dict(schema=horse.SCHEMA,release=release,created=time.time(),config_revision=horse.revision(config),client_revision=horse.client_revision(config),stamp=stamp,changes=changes,
                  before={'root.index':sha(index),'root.data':sha(data)},files={name:dict(sha256=sha(raw),size=len(raw)) for name,raw in blobs.items()})
        for name,raw in blobs.items():(stage/name).write_bytes(raw)
        manifest=json.dumps(meta,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
        (stage/'manifest.json').write_bytes(manifest)
        before=stage/'before';before.mkdir(mode=0o700)
        (before/'root.index').write_bytes(index);(before/'root.data').write_bytes(data)
        archive=stage/'klient-komplet.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
            for name in PACKS:z.writestr('pack/'+name,blobs[name])
            z.writestr('dbdata_stamp.txt',blobs['dbdata_stamp.txt']);z.writestr('manifest.json',manifest)
            z.writestr('INSTALACJA.txt','Zamknij gre. Zachowaj aktualne zmieniane pliki. Podmien obie czesci kazdej z trzech paczek w pack/. dbdata_stamp.txt umiesc obok pliku uruchamiajacego gre.\nROOT pochodzi z przeslanej pary; gamedata zachowano bez zmian. dbdata pochodzi z aktualnego eksportera serwera.\nPobranie nie potwierdza podmiany ani testu w grze. Pozniejsze zmiany paczek wymagaja ponownego scalenia.\n')
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:raise ValueError('Uszkodzony wynikowy ZIP.')
            for name in PACKS:
                if sha(z.read('pack/'+name))!=meta['files'][name]['sha256']:raise ValueError('Niezgodna zawartość ZIP.')
            if z.read('dbdata_stamp.txt')!=blobs['dbdata_stamp.txt']:raise ValueError('Niezgodny znacznik ZIP.')
        for name,entry in meta['files'].items():
            if sha((stage/name).read_bytes())!=entry['sha256']:raise ValueError('Błąd zapisu plików wydania.')
        meta['manifest_sha256']=sha(manifest)
        meta['archive_sha256']=sha(archive.read_bytes());meta['archive_size']=archive.stat().st_size
        if publisher.current_stamp()!=stamp:raise ValueError('Dane serwera zmieniły się podczas eksportu. Spróbuj ponownie.')
        final=releases/release;os.rename(stage,final)
        return final,meta
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True)
        raise

def verify_prepared(root,meta):
    release=meta.get('release','')
    if not re.fullmatch('[0-9a-f]{32}',release):raise ValueError('Nieprawidłowe wydanie.')
    folder=Path(root)/'releases'/release
    if folder.is_symlink():raise ValueError('Nieprawidłowy katalog wydania.')
    manifest=folder/'manifest.json'
    if sha(manifest.read_bytes())!=meta.get('manifest_sha256'):raise ValueError('Niezgodny manifest przed publikacją.')
    if set(meta.get('files',{}))!=set(PACKS)|{'dbdata_stamp.txt'}:raise ValueError('Niepełne wydanie.')
    for name,record in meta['files'].items():
        path=folder/name
        if path.is_symlink() or path.stat().st_size!=record['size'] or sha(path.read_bytes())!=record['sha256']:raise ValueError('Plik wydania został zmieniony przed publikacją.')
    archive=folder/'klient-komplet.zip'
    if archive.is_symlink() or archive.stat().st_size!=meta['archive_size'] or sha(archive.read_bytes())!=meta['archive_sha256']:raise ValueError('Niezgodny ZIP przed publikacją.')
    return folder

def verified_file(root,release,name):
    if not re.fullmatch('[0-9a-f]{32}',release) or name not in ALLOWED:raise ValueError('Nieprawidłowe wydanie lub nazwa.')
    folder=Path(root)/'releases'/release
    if folder.is_symlink():raise ValueError('Nieprawidłowy katalog wydania.')
    manifest=folder/'manifest.json'
    receipt=json.loads((Path(root)/'publications'/(release+'.json')).read_bytes())
    if sha(manifest.read_bytes())!=receipt.get('manifest_sha256'):raise ValueError('Manifest po publikacji został zmieniony.')
    meta=json.loads(manifest.read_bytes())
    if meta.get('release')!=release:raise ValueError('Niezgodny manifest wydania.')
    path=folder/name
    if path.is_symlink():raise ValueError('Nieprawidłowy plik wydania.')
    if name in meta['files']:
        item=meta['files'][name]
        if path.stat().st_size!=item['size'] or sha(path.read_bytes())!=item['sha256']:raise ValueError('Plik po publikacji został zmieniony.')
    elif name=='klient-komplet.zip':
        # Verify the pinned ZIP digest and each embedded member.
        if path.stat().st_size!=receipt.get('archive_size') or sha(path.read_bytes())!=receipt.get('archive_sha256'):raise ValueError('ZIP po publikacji został zmieniony.')
        with zipfile.ZipFile(path) as z:
            if z.read('manifest.json')!=manifest.read_bytes() or z.testzip() is not None:raise ValueError('Niezgodny ZIP.')
            for file,entry in meta['files'].items():
                key='pack/'+file if file in PACKS else file
                if sha(z.read(key))!=entry['sha256']:raise ValueError('Niezgodna zawartość opublikowanego ZIP.')
    return path
