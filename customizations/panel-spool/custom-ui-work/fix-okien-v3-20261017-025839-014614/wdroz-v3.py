from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil
import subprocess
import zipfile
import zlib

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

info = json.loads(subprocess.check_output(
    ['docker','inspect','metin2-seban-panel'], text=True
))[0]
spool = next(
    Path(m['Source']) for m in info['Mounts']
    if m['Destination'] == '/opt/m2spool'
)
work = spool / 'custom-ui-work'
stage = work / 'fix-okien-v3-20261017-025839-014614'
prepared = stage / 'prepared'
downloads = work / 'downloads'
updater = Path('/root/odswiez-pelny-zip.py')

manifest = json.loads((stage/'manifest.json').read_text())
if manifest.get('status') != 'prepared-not-installed':
    raise SystemExit('STOP: ta poprawka nie oczekuje na instalacje.')

for name, field in (
    ('root.index','base_root_index_sha256'),
    ('root.data','base_root_data_sha256'),
):
    if sha(downloads/name) != manifest[field]:
        raise SystemExit('STOP: od przygotowania zmieniono '+name)
    if not (prepared/name).is_file():
        raise SystemExit('STOP: brak przygotowanego '+name)

if not updater.is_file():
    raise SystemExit('STOP: brak sprawdzonego generatora pelnego ZIP-a.')

archive = downloads/'klient-komplet.zip'
if not archive.is_file():
    raise SystemExit('STOP: brak obecnego pelnego ZIP-a.')

# Sprawdzamy zapisane paczki przed podmiana.
check = r"""
from pathlib import Path
import json
import sys
sys.path.insert(0,'/app')
from m2clientpack import eterpack

stage=Path(sys.argv[1])
prepared=stage/'prepared'
base=Path('/opt/m2spool/custom-ui-work/downloads')

def unpack(folder):
    _,entries=eterpack.read_index_bytes((folder/'root.index').read_bytes())
    data=(folder/'root.data').read_bytes()
    lookup={}
    for entry in entries:
        name=entry.name.replace('\\','/').lower()
        if name in lookup:
            raise SystemExit('STOP: zdublowany wpis '+name)
        lookup[name]=entry
    return data,lookup

old,old_entries=unpack(base)
new,new_entries=unpack(prepared)
manifest=json.loads((stage/'manifest.json').read_text())

for name in manifest['changed_entries']:
    key=name.replace('\\','/').lower()
    raw=eterpack.read_entry(new,new_entries[key])
    if not raw:
        raise SystemExit('STOP: pusty wpis '+name)

for name in (
    'uiskillbookexchange.py',
    'uiukrainkabookexchange.py',
    'playersettingmodule.py',
):
    before=eterpack.read_entry(old,old_entries[name])
    after=eterpack.read_entry(new,new_entries[name])
    if before!=after:
        raise SystemExit('STOP: zmieniono chroniony modul '+name)

print('OK: paczki odczytane; KU i model zachowane.')
"""
container_stage = '/opt/m2spool/custom-ui-work/' + stage.name
subprocess.run([
    'docker','exec','-i','metin2-seban-panel',
    'python3','-',container_stage
], input=check, text=True, check=True)

backup = Path('/opt/metin2/kopie-naszych-zmian') / (
    'okna-v2-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')
)
backup.mkdir(parents=True)

targets = {
    downloads/'root.index': prepared/'root.index',
    downloads/'root.data': prepared/'root.data',
}

# Zachowujemy zgodnosc istniejacych kopii roboczych.
for folder in (
    work/'prepared',
    Path('/root/ukrainka-przygotowanie/klient'),
):
    if folder.is_dir():
        for name in ('root.index','root.data'):
            if (folder/name).is_file():
                targets[folder/name] = prepared/name

canonical = Path(
    '/opt/metin2/linux-port/docker/seban-panel/'
    'm2clientpack/custom_windows_source'
)
if canonical.is_dir():
    for name in ('uimissionpanel.py','uidungeoninfo.py'):
        if (canonical/name).is_file():
            targets[canonical/name] = prepared/name

# ZIP, prototypy i metadane generatora tez maja kopie.
protected = set(targets)
for path in downloads.iterdir():
    if path.is_file() and (
        path.suffix.lower() in ('.index','.data','.json','.zip')
        or path.name == 'dbdata_stamp.txt'
    ):
        protected.add(path)

copies = {}
needed = sum(p.stat().st_size for p in protected if p.is_file())
if shutil.disk_usage(backup).free < needed + archive.stat().st_size:
    raise SystemExit('STOP: za malo miejsca na kopie i nowy ZIP.')

for number,path in enumerate(sorted(protected, key=str)):
    if path.is_file():
        saved = backup/('%04d-'%number + path.name)
        shutil.copy2(path,saved)
        copies[path] = saved

(backup/'files.json').write_text(json.dumps({
    str(path):str(saved) for path,saved in copies.items()
},indent=2))

state = {
    'status':'installing',
    'backup':str(backup),
    'model_rotation':'not-fixed',
}
(stage/'deployment-state.json').write_text(json.dumps(state,indent=2))

try:
    # Ponownie kontrolujemy baze po wykonaniu kopii.
    for name,field in (
        ('root.index','base_root_index_sha256'),
        ('root.data','base_root_data_sha256'),
    ):
        if sha(downloads/name) != manifest[field]:
            raise RuntimeError('W trakcie przygotowania zmieniono '+name)

    for target,source in targets.items():
        shutil.copy2(source,target)

    print('Przebudowuje pelny ZIP...',flush=True)
    subprocess.run(['python3',str(updater)],check=True)

    # Potwierdzamy, ze pelny ZIP zawiera nowy ROOT.
    with zipfile.ZipFile(archive) as zipped:
        for name in ('root.index','root.data'):
            matches = [
                item for item in zipped.infolist()
                if item.filename.replace('\\','/').split('/')[-1] == name
            ]
            if len(matches) != 1:
                raise RuntimeError('Niejednoznaczny '+name+' w ZIP-ie.')
            expected = (prepared/name).read_bytes()
            item = matches[0]
            if (
                item.file_size != len(expected)
                or item.CRC != (zlib.crc32(expected)&0xffffffff)
            ):
                raise RuntimeError('ZIP zawiera inny '+name)

    state['status'] = 'installed-awaiting-client-test'
    state['zip'] = str(archive)
    (stage/'deployment-state.json').write_text(
        json.dumps(state,indent=2)
    )
    print('OK: wdrozono poprawke obu okien.')
    print('OK: pelny ZIP zawiera nowy ROOT.')
    print('Kopia poprzednich plikow:',backup)
    print('ZIP:',archive)
    print('Nie restartowano gry ani panelu.')
    print('Obrot modeli pozostaje do poprawienia.')

except BaseException:
    errors = []
    for target,saved in copies.items():
        try:
            shutil.copy2(saved,target)
        except Exception as error:
            errors.append(str(target)+': '+str(error))
    state['status'] = 'rollback-incomplete' if errors else 'rolled-back'
    state['errors'] = errors
    (stage/'deployment-state.json').write_text(
        json.dumps(state,indent=2)
    )
    print('Przywrocono kopie plikow.' if not errors else
          'UWAGA: przywracanie wymaga sprawdzenia deployment-state.json.')
    raise
