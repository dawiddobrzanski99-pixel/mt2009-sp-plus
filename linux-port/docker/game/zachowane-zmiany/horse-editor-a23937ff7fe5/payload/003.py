#!/usr/bin/env python3
"""Install/undo only this ROOT pair; refuses to overwrite later client edits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def write(p,raw):
    fd,temp=tempfile.mkstemp(prefix='.horse-',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,p)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def operate(bundle,pack,undo=False):
    manifest=json.loads((bundle/'manifest.json').read_text())
    source='before' if undo else 'pack'
    wanted=manifest['before' if undo else 'after']
    expected=manifest['after' if undo else 'before']
    names=('root.index','root.data')
    for name in names:
        if sha(bundle/source/name)!=wanted[name]:raise ValueError('Damaged bundle: '+name)
        if (pack/name).is_symlink():raise ValueError('Symlink conflict')
        allowed=(expected[name],wanted[name]) if undo else (expected[name],)
        if sha(pack/name) not in allowed:raise ValueError('Conflict: current '+name+' is different. No files changed.')
    # Keep originals inside the bundle; restore on an interrupted second write.
    old={name:(pack/name).read_bytes() for name in names}
    try:
        for name in names:write(pack/name,(bundle/source/name).read_bytes())
        if any(sha(pack/name)!=wanted[name] for name in names):raise ValueError('Verification failed')
    except BaseException:
        for name in names:write(pack/name,old[name])
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pack',type=Path,required=True,help='Existing client pack directory; close game first')
    p.add_argument('--undo',action='store_true')
    args=p.parse_args()
    operate(Path(__file__).resolve().parent,args.pack,args.undo)
    print('ROOT pair restored.' if args.undo else 'ROOT pair installed. Game test still required.')
