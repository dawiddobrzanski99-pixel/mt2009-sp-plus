"""Restore five approved item icons in the user's current GAMEDATA pack.

Only the icon column and the five image files change.  This module is
installed inside m2clientpack and uses its existing EterPack implementation.
"""
import re
import zlib

from . import eterpack


ICON_PATHS = {
    50033: 'icon/item/custom_chest_50033.tga',
    50035: 'icon/item/custom_chest_50035.tga',
    50122: 'icon/item/custom_chest_50122.tga',
    50124: 'icon/item/skrzynia_zielone_bonusy_50124.tga',
    71102: 'icon/item/klepsydra_biologa_71102.tga',
}
ITEM_LIST = 'gamedata/item_list.txt'


def patch_item_list(raw, mapping):
    """Replace icon paths without changing other columns, rows or newlines.

    Every requested VNUM must occur exactly once.  Tab columns are required
    by the client's LoadItemList parser.  A malformed or duplicate target
    row raises before any pack is produced.
    """
    if not isinstance(raw, bytes):
        raise TypeError('item_list must be bytes')
    normalized = {}
    for vnum, path in mapping.items():
        number = int(vnum)
        if number <= 0 or number in normalized:
            raise ValueError('Invalid or repeated icon VNUM: %s' % vnum)
        encoded = path.encode('ascii') if isinstance(path, str) else bytes(path)
        if not encoded.startswith(b'icon/item/') or re.search(rb'[\s\x00]', encoded):
            raise ValueError('Invalid icon path for %s' % vnum)
        normalized[number] = encoded

    seen = dict((vnum, 0) for vnum in normalized)
    out = []
    for line in raw.splitlines(keepends=True):
        head = line.lstrip(b' \t').split(None, 1)
        if not head or not head[0].isdigit() or int(head[0]) not in normalized:
            out.append(line)
            continue
        vnum = int(head[0])
        seen[vnum] += 1
        match = re.match(rb'^([ \t]*[0-9]+\t[^\t\r\n]+\t)([^\t\r\n]*)(.*)$', line, re.DOTALL)
        if not match or not match.group(2):
            raise ValueError('Malformed item_list row for %s' % vnum)
        out.append(match.group(1) + normalized[vnum] + match.group(3))
    bad = dict((vnum, count) for vnum, count in seen.items() if count != 1)
    if bad:
        raise ValueError('Expected one item_list row for each VNUM: %r' % bad)
    return b''.join(out)


def patch_pack(index, data, icon_payload):
    """Return (new index, new data, item_list) based on the current pair.

    icon_payload is a dict of the five ICON_PATHS values to approved image
    bytes.  Unrelated index records and all original data bytes are retained.
    Calling this again on an already corrected pair returns that exact pair.
    """
    if set(icon_payload) != set(ICON_PATHS.values()):
        raise ValueError('Expected the five approved icon paths')
    if not all(isinstance(blob, bytes) and blob for blob in icon_payload.values()):
        raise ValueError('Each icon payload must contain nonempty bytes')
    version, entries = eterpack.read_index_bytes(index)
    if version != 2:
        raise ValueError('Unsupported EterPack version: %s' % version)
    by_name = {}
    for entry in entries:
        if entry.name in by_name:
            raise ValueError('Duplicate pack entry: %s' % entry.name)
        if entry.pos < 0 or entry.size < 0 or entry.pos + entry.size > len(data):
            raise ValueError('Invalid pack entry bounds: %s' % entry.name)
        if zlib.crc32(data[entry.pos:entry.pos + entry.size]) & 0xffffffff != entry.dcrc:
            raise ValueError('Mismatched or corrupt pack pair: %s' % entry.name)
        by_name[entry.name] = entry
    if ITEM_LIST not in by_name:
        raise ValueError('Current GAMEDATA has no item_list.txt')
    original_list = eterpack.read_entry(data, by_name[ITEM_LIST])
    item_list = patch_item_list(original_list, ICON_PATHS)
    replacements = dict(icon_payload)
    replacements[ITEM_LIST] = item_list
    out = bytearray(data)
    changed = False
    for name, raw in replacements.items():
        entry = by_name.get(name)
        if entry is not None and eterpack.read_entry(data, entry) == raw:
            continue
        changed = True
        if entry is None:
            entry = eterpack.Entry(bytes(eterpack.ENTRY))
            entry.id = max((e.id for e in entries), default=-1) + 1
            entry.name = name
            entry.fcrc = eterpack.name_crc(name)
            entry.ctype = 2
            entries.append(entry)
            by_name[name] = entry
        blob = eterpack.encode_entry(raw, entry.ctype)
        entry.pos = len(out)
        entry.size = len(blob)
        entry.real = (len(blob) + 255) // 256 * 256
        entry.dcrc = zlib.crc32(blob) & 0xffffffff
        out.extend(blob)
        out.extend(b'\0' * (entry.real - len(blob)))
    if not changed:
        return index, data, item_list
    new_index = eterpack.write_index_bytes(version, entries)
    new_data = bytes(out)
    # Validate the resulting pair before any caller writes it to disk.
    for entry in eterpack.read_index_bytes(new_index)[1]:
        if entry.name in replacements:
            if eterpack.read_entry(new_data, entry) != replacements[entry.name]:
                raise ValueError('Pack verification failed: %s' % entry.name)
    return new_index, new_data, item_list
