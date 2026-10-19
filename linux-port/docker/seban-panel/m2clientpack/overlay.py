"""The client data overlay: the database editor's changes as a few small
files the player's launcher lays onto the released client's packs.

Why not a pack of its own that overrides the base entries: the client keeps
every pack's entries in one boost::unordered_multimap keyed by crc32(name)
(EterPack.cpp CEterFileDict::InsertItem) and takes the FIRST match of
equal_range (GetItem). Boost 1.83 (Extern/include/boost/version.hpp)
inserts an equal key right after the group's first node
(fca.hpp insert_node_hint) and every rehash pushes each node to the front of
its new bucket (implementation.hpp transfer_node/rehash_impl), reversing the
group - so which of two packs wins depends on how many times the table grew
after the second insert, i.e. on the entry counts of every pack of the
release. Not something to build on.

So the overlay leaves no duplicate names: for each pack it touches
(gamedata, locale) it ships
  <pack>.index  the release's index with the changed entries pointing past
                the end of the release's <pack>.data (new names appended),
  <pack>.tail   the bytes that go there: the new entries, 256-aligned.
The launcher keeps the release's .index, cuts <pack>.data back to the
release's length, appends the tail and puts the new index in place; undoing
it is the same two steps back. The base (the release's index, its data
length and the few files that get patched) is in base/<client version>/,
written by make_base.py when a client is released.
"""
import hashlib
import json
import os
import shutil
import struct
import time
import zlib

from . import eterpack

SLOT = 256
SCHEMA = 1
BASE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'base')


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


class Base(object):
    """base/<version>/: base.json, <pack>.index, files/<entry name>."""

    def __init__(self, path):
        self.path = path
        with open(os.path.join(path, 'base.json'), encoding='utf-8') as f:
            self.meta = json.load(f)
        self.version = self.meta['client']

    def index_bytes(self, pack):
        with open(os.path.join(self.path, pack + '.index'), 'rb') as f:
            data = f.read()
        if sha256(data) != self.meta['packs'][pack]['indexSha256']:
            raise ValueError('base %s/%s.index differs from base.json' % (self.version, pack))
        return data

    def file(self, name):
        with open(os.path.join(self.path, 'files', *name.split('/')), 'rb') as f:
            data = f.read()
        if sha256(data) != self.meta['files'][name]['sha256']:
            # e.g. a checkout that turned the line ends round (base/.gitattributes)
            raise ValueError('base %s/%s differs from base.json' % (self.version, name))
        return data

    def has_file(self, name):
        return name in self.meta.get('files', {})

    def pack_of(self, name):
        return self.meta['files'][name]['pack']


def latest_base(root=BASE_ROOT):
    """The newest base/<version>/ (numeric compare)."""
    versions = []
    for name in os.listdir(root) if os.path.isdir(root) else []:
        if os.path.isfile(os.path.join(root, name, 'base.json')):
            versions.append(name)
    if not versions:
        raise FileNotFoundError('no client base in %s' % root)
    versions.sort(key=lambda v: [int(p) if p.isdigit() else 0 for p in v.split('.')])
    return Base(os.path.join(root, versions[-1]))


def build_pack(base, pack, files):
    """(index bytes, tail bytes, entry names) of one pack: files = {entry
    name: new bytes}. A name the base index lacks becomes a new entry (a copy
    of the last entry, the next id, crc32 of the name)."""
    meta = base.meta['packs'][pack]
    ver, entries = eterpack.read_index_bytes(base.index_bytes(pack))
    by_name = dict((e.name, e) for e in entries)
    next_id = max([e.id for e in entries] + [0]) + 1
    tail = bytearray()
    pos = int(meta['dataSize'])
    if pos % SLOT:
        raise ValueError('%s.data of the base is not %d-aligned' % (pack, SLOT))
    for name in sorted(files):
        entry = by_name.get(name)
        if entry is None:
            entry = eterpack.Entry(entries[-1].raw)
            entry.id = next_id
            next_id += 1
            entry.name = name
            entry.fcrc = eterpack.name_crc(name)
            entry.ctype = 2 if name.endswith('.txt') else 0
            entries.append(entry)
            by_name[name] = entry
        blob = eterpack.encode_entry(files[name], entry.ctype)
        slot = (len(blob) + SLOT - 1) // SLOT * SLOT
        entry.pos = pos + len(tail)
        entry.size = len(blob)
        entry.real = slot
        entry.dcrc = zlib.crc32(blob) & 0xffffffff
        tail += blob + b'\0' * (slot - len(blob))
    return eterpack.write_index_bytes(ver, entries), bytes(tail), sorted(files)


def verify_pack(base, pack, index_blob, tail, files):
    """Reads the built pack back the way the client will see it: every
    entry of the base index unchanged except the patched ones, which decode
    to exactly the new bytes."""
    meta = base.meta['packs'][pack]
    data_size = int(meta['dataSize'])
    _, old = eterpack.read_index_bytes(base.index_bytes(pack))
    _, new = eterpack.read_index_bytes(index_blob)
    old_by = dict((e.name, e) for e in old)
    names = [e.name for e in new]
    if len(set(names)) != len(names) or len(set(e.id for e in new)) != len(new):
        raise AssertionError('%s: duplicate entry' % pack)
    for e in new:
        if e.fcrc != eterpack.name_crc(e.name):
            raise AssertionError('%s: crc of %s' % (pack, e.name))
        if e.name in files:
            if e.pos < data_size:
                raise AssertionError('%s: %s inside the base data' % (pack, e.name))
            blob = tail[e.pos - data_size:e.pos - data_size + e.size]
            if len(blob) != e.size or zlib.crc32(blob) & 0xffffffff != e.dcrc:
                raise AssertionError('%s: %s stored badly' % (pack, e.name))
            if eterpack.decode_entry(blob, e.ctype) != files[e.name]:
                raise AssertionError('%s: %s reads back differently' % (pack, e.name))
        elif old_by.get(e.name) is None or old_by[e.name].raw != e.raw:
            raise AssertionError('%s: %s changed although not patched' % (pack, e.name))
    if set(old_by) - set(names):
        raise AssertionError('%s: an entry went missing' % pack)


def build(base, files, out_dir, summary=None, keep=3):
    """Builds the overlay of files ({entry name: new bytes}, only those that
    differ from the base) into out_dir: <stamp>/<pack>.index|.tail and
    manifest.json (written last, atomically). Returns the manifest."""
    by_pack = {}
    for name, data in files.items():
        if base.has_file(name) and base.file(name) == data:
            continue
        pack = base.pack_of(name) if base.has_file(name) else name.split('/', 1)[0]
        if pack not in base.meta['packs']:
            raise ValueError('no base pack for %s' % name)
        by_pack.setdefault(pack, {})[name] = data
    built = []
    for pack in sorted(by_pack):
        index_blob, tail, names = build_pack(base, pack, by_pack[pack])
        verify_pack(base, pack, index_blob, tail, by_pack[pack])
        built.append((pack, index_blob, tail, names))
    digest = hashlib.sha256(base.version.encode())
    for pack, index_blob, tail, names in built:
        digest.update(pack.encode() + b'\0' + index_blob + b'\0' + tail)
    stamp = digest.hexdigest()[:16] if built else 'oryginal'
    os.makedirs(out_dir, exist_ok=True)
    manifest = {
        'schema': SCHEMA, 'stamp': stamp, 'client': base.version,
        'built': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'packs': [], 'summary': summary or {},
    }
    if built:
        stamp_dir = os.path.join(out_dir, stamp)
        tmp_dir = stamp_dir + '.tmp'
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir)
        for pack, index_blob, tail, names in built:
            meta = base.meta['packs'][pack]
            with open(os.path.join(tmp_dir, pack + '.index'), 'wb') as f:
                f.write(index_blob)
            with open(os.path.join(tmp_dir, pack + '.tail'), 'wb') as f:
                f.write(tail)
            manifest['packs'].append({
                'name': pack,
                'baseIndexSha256': meta['indexSha256'], 'baseIndexSize': meta['indexSize'],
                'baseDataSize': meta['dataSize'],
                'index': {'file': stamp + '/' + pack + '.index', 'size': len(index_blob), 'sha256': sha256(index_blob)},
                'tail': {'file': stamp + '/' + pack + '.tail', 'size': len(tail), 'sha256': sha256(tail)},
                'entries': names,
            })
        shutil.rmtree(stamp_dir, ignore_errors=True)
        os.replace(tmp_dir, stamp_dir)
    tmp = os.path.join(out_dir, 'manifest.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(out_dir, 'manifest.json'))
    # the older builds a launcher may still be downloading stay a while
    olds = sorted((d for d in os.listdir(out_dir)
                   if os.path.isdir(os.path.join(out_dir, d)) and d != stamp and not d.endswith('.tmp')),
                  key=lambda d: os.path.getmtime(os.path.join(out_dir, d)))
    for d in olds[:max(0, len(olds) - (keep - 1))]:
        shutil.rmtree(os.path.join(out_dir, d), ignore_errors=True)
    return manifest


def apply_to_folder(manifest, out_dir, pack_dir):
    """What the launcher does, in Python (tests, and a Linux client): lays
    the overlay onto pack_dir (release packs). Returns the packs applied."""
    done = []
    for p in manifest['packs']:
        idx = os.path.join(pack_dir, p['name'] + '.index')
        dat = os.path.join(pack_dir, p['name'] + '.data')
        with open(idx, 'rb') as f:
            if sha256(f.read()) != p['baseIndexSha256']:
                raise ValueError('%s.index is not the base the overlay was built for' % p['name'])
        if os.path.getsize(dat) < p['baseDataSize']:
            raise ValueError('%s.data is shorter than the base' % p['name'])
        with open(os.path.join(out_dir, p['tail']['file']), 'rb') as f:
            tail = f.read()
        with open(dat, 'r+b') as f:
            f.truncate(p['baseDataSize'])
            f.seek(p['baseDataSize'])
            f.write(tail)
        shutil.copyfile(os.path.join(out_dir, p['index']['file']), idx)
        done.append(p['name'])
    return done


def entry_count(index_blob):
    return struct.unpack_from('<I', eterpack.mcoz_decode(index_blob, eterpack.IDX_KEY), 8)[0]
