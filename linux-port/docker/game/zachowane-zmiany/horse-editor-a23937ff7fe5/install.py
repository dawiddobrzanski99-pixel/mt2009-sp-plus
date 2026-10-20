#!/usr/bin/env python3
"""Portable source installer. Explicit apply; never builds, restarts or pushes."""
import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone


def sha(raw):return hashlib.sha256(raw).hexdigest()


def safe(root, relative):
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe relative path')
    current=root
    if root.is_symlink():raise ValueError('Symlink root')
    for part in p.parts:
        current=current/part
        if current.is_symlink():raise ValueError('Symlink conflict: '+str(current))
    return current


def atomic(path,raw,mode):
    fd,temp=tempfile.mkstemp(prefix='.horse-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            os.fchmod(f.fileno(),mode);f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def once(raw,old,new):
    if raw.count(old)!=1:raise ValueError('Conflict: expected exactly one source anchor')
    return raw.replace(old,new,1)


def source_patches(root,bundle):
    spec=json.loads((bundle/'bundle.json').read_text())
    for rule in spec.get('constraints',[]):
        raw=safe(root,rule['path']).read_bytes()
        if rule['contains'].encode() not in raw:raise ValueError('Legacy horse bonus conflict: '+rule['path'])
    changes=[]
    for entry in spec['files']:
        path=safe(root,entry['path']);old=path.read_bytes() if path.exists() else None
        payload=safe(bundle,entry['payload']).read_bytes()
        if sha(payload)!=entry['sha256']:raise ValueError('Corrupt installer payload')
        if entry['kind']=='add':
            if old is not None and old!=payload:raise ValueError('File collision: '+str(path))
            new=payload
        elif entry['kind']=='splice':
            if old is None:raise ValueError('Missing source: '+str(path))
            data=json.loads(payload)
            new=old
            for patch in data:
                before=bytes.fromhex(patch['before']);after=bytes.fromhex(patch['after'])
                if new.count(after)==1:
                    if before in after and new.count(before)!=after.count(before):raise ValueError('Ambiguous source anchor: '+str(path))
                elif before in new:new=once(new,before,after)
                else:raise ValueError('Source conflict: '+str(path))
        else:raise ValueError('Unknown patch kind')
        if entry['path'].endswith('.py'):ast.parse(new)
        if old!=new:changes.append((entry['path'],old,new))
    # Keep a small replayable installer in a directory already collected by zapisz-mt2009.
    archive=Path('docker/game/zachowane-zmiany')/('horse-editor-'+sha((bundle/'bundle.json').read_bytes())[:12])
    replay={'install.py','export-state.py','bundle.json','README.md','DIFF.txt','REPORT.txt'}
    replay.update(row['payload'] for row in spec['files'])
    for name in sorted(replay):
        source=safe(bundle,name)
        if not source.is_file():continue
        relative=(archive/source.relative_to(bundle)).as_posix();path=safe(root,relative);raw=source.read_bytes()
        old=path.read_bytes() if path.exists() else None
        if old is not None and old!=raw:raise ValueError('Installer archive conflict: '+str(path))
        if old is None:changes.append((relative,None,raw))
    return changes


def apply(root,changes,state):
    if state.exists():raise ValueError('State directory already exists')
    state.mkdir(parents=True,mode=0o700)
    plan=[]
    for i,(relative,old,new) in enumerate(changes):
        path=safe(root,relative)
        row=dict(path=relative,before=sha(old) if old is not None else None,after=sha(new),mode=path.stat().st_mode&0o777 if old is not None else 0o644,backup=str(i)+'.before',installed=False)
        if old is not None:(state/row['backup']).write_bytes(old)
        plan.append(row)
    journal=state/'state.json'
    def save():atomic(journal,json.dumps(dict(root=str(root),files=plan),indent=2).encode(),0o600)
    save()
    try:
        for row,(_,old,new) in zip(plan,changes):
            path=safe(root,row['path'])
            current=path.read_bytes() if path.exists() else None
            if current!=old:raise ValueError('File changed during install: '+str(path))
            path.parent.mkdir(parents=True,exist_ok=True)
            # Persist intent first; rollback accepts either preimage or postimage.
            row['installed']=True;save()
            atomic(path,new,row['mode'])
            if sha(path.read_bytes())!=row['after']:raise ValueError('Write verification failed')
        save()
    except BaseException:
        rollback(state)
        raise


def rollback(state):
    journal=state/'state.json';plan=json.loads(journal.read_text());root=Path(plan['root'])
    for row in plan['files']:
        if not row['installed']:continue
        p=safe(root,row['path']);current=sha(p.read_bytes()) if p.exists() else None
        if current not in (row['before'],row['after']):raise ValueError('Rollback conflict, later change: '+str(p))
        if row['before'] is not None and sha((state/row['backup']).read_bytes())!=row['before']:raise ValueError('Damaged backup')
    for row in reversed(plan['files']):
        if not row['installed']:continue
        p=safe(root,row['path']);current=sha(p.read_bytes()) if p.exists() else None
        if current==row['after']:
            if row['before'] is None:p.unlink()
            else:atomic(p,(state/row['backup']).read_bytes(),row['mode'])
        row['installed']=False
        atomic(journal,json.dumps(plan,indent=2).encode(),0o600)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path('/opt/metin2/linux-port'))
    parser.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true')
    mode.add_argument('--check',action='store_true',help='Check current sources; write no source files')
    parser.add_argument('--diff',type=Path,help='Write exact proposed byte-preserving unified diff')
    parser.add_argument('--state',type=Path)
    parser.add_argument('--rollback',type=Path)
    args=parser.parse_args()
    if args.rollback:
        rollback(args.rollback);print('Rolled back only this installation. No runtime deployment.');return
    root=args.project.absolute()
    changes=source_patches(root,args.bundle)
    for relative,old,new in changes:print(relative,sha(old) if old is not None else 'NEW','->',sha(new))
    print('Files:',len(changes))
    if args.diff:
        parts=[]
        for relative,old,new in changes:
            parts.extend(difflib.unified_diff((old or b'').decode('latin1').splitlines(True),new.decode('latin1').splitlines(True),fromfile='a/'+relative if old is not None else '/dev/null',tofile='b/'+relative))
        normalized=[line if line.endswith('\n') else line+'\n\\ No newline at end of file\n' for line in parts]
        args.diff.write_bytes(''.join(normalized).encode('latin1'))
        print('Proposed diff:',args.diff)
    if args.apply:
        if not changes:
            print('Already installed; no file changes or new backups.')
            return
        state=args.state or root.parent/'kopie-naszych-zmian'/('horse-editor-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f'))
        apply(root,changes,state)
        print('SOURCE FILES WRITTEN. Backup/journal:',state)
        print('NOT built, NOT deployed, NOT pushed. Runtime game and client require separate deployment.')
    else:print('DRY RUN. No source changes.')


if __name__=='__main__':main()
