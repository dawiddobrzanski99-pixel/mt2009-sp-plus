#!/usr/bin/env python3
"""Export only this module's config and changed client entries for the existing save command."""
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=Path,default=Path('/opt/metin2/linux-port'))
parser.add_argument('--spool',type=Path)
args=parser.parse_args()
spool=args.spool
if spool is None:
    mounts=json.loads(subprocess.check_output(['docker','inspect','metin2-seban-panel','--format','{{json .Mounts}}']))
    spool=next(Path(m['Source']) for m in mounts if m['Destination']=='/opt/m2spool')
source=spool/'systems/horse'
if not (source/'draft.json').is_file():raise SystemExit('STOP: no saved horse configuration')
sys.path.insert(0,str(args.project/'docker/seban-panel'))
from m2clientpack import horse_editor as horse, horse_publication as publication, eterpack

def sha(raw):return hashlib.sha256(raw).hexdigest()
with (source/'editor.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    config=horse.validate(json.loads((source/'draft.json').read_bytes()))
    raw_files={'draft.json':horse.canonical(config)}
    configurations=[config]
    for name in ('request.txt','last-request.json','last-client-publication.json'):
        path=source/name
        if path.is_file():
            if path.is_symlink():raise SystemExit('STOP: symlink source')
            raw_files[name]=path.read_bytes()
    # Keep the small history of configurations, not core heartbeats or player data.
    for path in (source/'history').glob('*.json'):
        if path.is_symlink():raise SystemExit('STOP: symlink history')
        configurations.append(horse.validate(json.loads(path.read_bytes())))
        raw_files['history/'+path.name]=path.read_bytes()
    for row in [row for value in configurations for row in value['levels']]:
        if row['icon']:
            name=Path(row['icon']).name;path=source/'assets'/name
            if path.is_symlink():raise SystemExit('STOP: symlink asset')
            raw=path.read_bytes()
            if horse.validate_tga(raw)!=row['icon']:raise SystemExit('STOP: asset checksum mismatch')
            raw_files['assets/'+name]=raw
    if 'last-client-publication.json' in raw_files:
        meta=json.loads(raw_files['last-client-publication.json'])
        release=meta['release']
        publication.verified_file(source,release,'klient-komplet.zip')
        for name in ('manifest.json','root.index','root.data'):
            publication.verified_file(source,release,name)
        folder=source/'releases'/release
        raw_files['client-edition/manifest.json']=(folder/'manifest.json').read_bytes()
        raw_files['client-edition/receipt.json']=raw_files['last-client-publication.json']
        # Preserve only changed entries in readable form; never snapshot the full client.
        desired={entry['path'].replace('\\','/').lower() for entry in meta['changes']}
        data=(folder/'root.data').read_bytes()
        for entry in eterpack.read_index_bytes((folder/'root.index').read_bytes())[1]:
            name=entry.name.replace('\\','/');normalized=name.lower()
            if normalized.startswith('d:/'):normalized=normalized[3:]
            if normalized not in desired:continue
            relative=Path(normalized)
            if relative.is_absolute() or '..' in relative.parts:raise SystemExit('STOP: unsafe client entry')
            raw_files['client-edition/changed-root/'+relative.as_posix()]=eterpack.read_entry(data,entry)
    dest=args.project/'docker/game/zachowane-zmiany'/('horse-editor-state-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
    dest.mkdir(parents=True,mode=0o700)
    for name,raw in raw_files.items():
        target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    (dest/'SHA256.json').write_text(json.dumps({n:sha(r) for n,r in raw_files.items()},indent=2))
    (dest/'README.txt').write_text('Only horse editor configuration and its changed client entries. No full client, account or character data.\nCompare with current source/config before selective replay. No build, runtime application or Git push performed.\nWindows ROOT and other client packs need a separate backup.\n')
print('Prepared for existing save command:',dest)
print('Windows ROOT needs separate protection. No Git commit or push performed.')
