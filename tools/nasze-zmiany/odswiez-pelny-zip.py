from pathlib import Path
from datetime import datetime
import subprocess
import urllib.request
import urllib.parse
import hashlib
import json
import shutil
import tempfile
import zipfile

origin='http://127.0.0.1:7790'
manifest_url=origin+'/klient/dbdata/manifest.json'

def fetch(url):
    request=urllib.request.Request(
        url,headers={'Cache-Control':'no-cache'}
    )
    with urllib.request.urlopen(request,timeout=180) as response:
        return response.read()

info=json.loads(subprocess.check_output([
    'docker','inspect','metin2-seban-panel'
],text=True))[0]
spool=next(Path(m['Source']) for m in info['Mounts']
           if m['Destination']=='/opt/m2spool')
work=spool/'custom-ui-work'
downloads=work/'downloads'
prepared=Path('/root/ukrainka-przygotowanie')

names=[
    'root.index','root.data','gamedata.index','gamedata.data',
    'dbdata.index','dbdata.data'
]
for name in names[:4]:
    if not (downloads/name).is_file():
        raise SystemExit('STOP: brak '+str(downloads/name))

print('Pobieram aktualne dbdata z panelu...',flush=True)
manifest=json.loads(fetch(manifest_url))
if manifest.get('format')!='MT2009_PLUS_DBDATA_AUTO_V1':
    raise SystemExit('STOP: nieznany format manifestu.')

records={}
for entry in manifest.get('files',[]):
    if entry.get('name') in ('pack/dbdata.index','pack/dbdata.data'):
        name=entry['name'].split('/')[-1]
        if name in records:
            raise SystemExit('STOP: powtorzony wpis '+name)
        records[name]=entry
if set(records)!={'dbdata.index','dbdata.data'}:
    raise SystemExit('STOP: niepelny manifest dbdata.')

stage=Path(tempfile.mkdtemp(prefix='dbdata-sprawdzone-',dir=str(work)))
for name,entry in records.items():
    url=urllib.parse.urljoin(manifest_url,entry['url'])
    if urllib.parse.urlparse(url).netloc!=urllib.parse.urlparse(origin).netloc:
        raise SystemExit('STOP: adres pliku prowadzi poza lokalny panel.')
    blob=fetch(url)
    if len(blob)!=int(entry['size']):
        raise SystemExit('STOP: niezgodny rozmiar '+name)
    if hashlib.sha256(blob).hexdigest().upper()!=entry['sha256'].upper():
        raise SystemExit('STOP: niezgodna suma SHA256 '+name)
    (stage/name).write_bytes(blob)

stamp_file=manifest.get('stamp_file')
if not isinstance(stamp_file,str):
    raise SystemExit('STOP: brak znacznika w eksporcie panelu.')
(stage/'dbdata_stamp.txt').write_bytes(stamp_file.encode('ascii'))

container_stage='/opt/m2spool/'+str(stage.relative_to(spool))
check=r'''
from pathlib import Path
import sys
sys.path.insert(0,'/app')
from m2clientpack import dbdata
from dbeditor import clientdata

p=Path(sys.argv[1])
index=(p/'dbdata.index').read_bytes()
data=(p/'dbdata.data').read_bytes()
actual=dbdata.pack_stamp(dbdata.latest_base(),index,data)
expected=clientdata.read_server_stamp('/opt/m2spool')
included=dbdata.read_stamp_text((p/'dbdata_stamp.txt').read_bytes())
print('Paczka:',actual,flush=True)
print('Serwer:',expected,flush=True)
if not expected or actual!=expected or included!=actual:
    raise SystemExit('STOP: niezgodnosc danych i znacznika.')
# CUSTOM_VERIFY_UKRAINKA_PICK_V1
from m2clientpack import eterpack
expected_model=Path('/app/m2clientpack/custom_ukrainka_assets/dane_remy_npc.msm').read_bytes()
model_entries=[e for e in eterpack.read_index_bytes(index)[1] if e.name.replace(chr(92),"/").lower().endswith("/dane_remy_npc.msm") or e.name.lower()=="dane_remy_npc.msm"]
if not model_entries:
    raise SystemExit("STOP: eksport nie zawiera modelu Ukrainki.")
for entry in model_entries:
    if eterpack.read_entry(data,entry)!=expected_model:
        raise SystemExit("STOP: eksport zawiera starszy model Ukrainki.")
print('OK: dane, znacznik i serwer sa zgodne.',flush=True)
'''
subprocess.run([
    'docker','exec','-i','metin2-seban-panel',
    'python3','-',container_stage
],input=check,text=True,check=True)

archive=stage/'klient-komplet.zip'
with zipfile.ZipFile(
    archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1
) as z:
    for name in names:
        p=stage/name if name.startswith('dbdata.') else downloads/name
        z.write(p,'pack/'+name)
    z.write(stage/'dbdata_stamp.txt','dbdata_stamp.txt')
    z.writestr(
        'INSTALACJA.txt',
        'Zamknij gre.\n'
        'Podmien wszystkie 6 plikow w folderze pack klienta.\n'
        'dbdata_stamp.txt skopiuj do glownego folderu klienta, '
        'obok pliku uruchamiajacego gre.\n'
    )
with zipfile.ZipFile(archive) as z:
    bad=z.testzip()
    if bad:
        raise SystemExit('STOP: uszkodzony ZIP: '+bad)

backup=Path('/opt/metin2/kopie-naszych-zmian')/(
    'zip-dbdata-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')
)
backup.mkdir(parents=True)
for name in ('dbdata.index','dbdata.data','dbdata_stamp.txt','klient-komplet.zip'):
    if (downloads/name).is_file():
        shutil.copy2(downloads/name,backup/name)

client=prepared/'klient'
client.mkdir(parents=True,exist_ok=True)
for name in ('dbdata.index','dbdata.data','dbdata_stamp.txt'):
    shutil.copy2(stage/name,downloads/name)
    shutil.copy2(stage/name,client/name)
shutil.copy2(archive,downloads/'klient-komplet.zip')
shutil.copy2(archive,prepared/'klient-komplet.zip')

p=work/'installation-manifest.json'
if p.is_file():
    state=json.loads(p.read_text())
    state.setdefault('download_hashes',{}).update({
        name:hashlib.sha256((downloads/name).read_bytes()).hexdigest()
        for name in names+['dbdata_stamp.txt','klient-komplet.zip']
    })
    p.write_text(json.dumps(state,indent=2),encoding='utf-8')

print('GOTOWY ZIP:',prepared/'klient-komplet.zip',flush=True)
