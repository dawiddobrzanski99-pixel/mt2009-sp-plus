"""Horse editor schema and append-only patches of the user's own ROOT pair."""
import copy
import hashlib
import json
import re
import struct
import zlib
from . import eterpack

KEYS = ('attack', 'hp', 'monster', 'boss', 'stone', 'move', 'classes', 'human',
        'elements', 'resistMonster', 'resistBoss', 'defense', 'speed', 'strength', 'vitality', 'dexterity', 'intelligence', 'crit', 'penetrate', 'drop', 'exp', 'yang')
LABELS = ('Wartość ataku', 'Maksymalne PZ', 'Silny na potwory %', 'Silny na bossy %',
          'Silny na metiny %', 'Szybkość ruchu', 'Odporność na klasy %', 'Silny na ludzi %',
          'Siła żywiołów %', 'Odporność na potwory ‰', 'Odporność na bossy ‰', 'Obrona', 'Szybkość ataku %', 'Siła', 'Witalność', 'Zręczność', 'Inteligencja', 'Szansa na krytyka %', 'Szansa na przeszywkę %', 'Dodatkowy drop %', 'Szansa na podwójny EXP %', 'Szansa na podwójny Yang %')
LIMITS = (1000, 50000, 100, 100, 100, 100, 90, 100, 100, 900, 900, 1000, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100)
SCHEMA = 'SEBAN_HORSE_V2'
ICON_PREFIX = 'd:/ymir work/ui/sebanhorse/'


def defaults():
    levels = []
    for n in range(31):
        growth = lambda maximum, last: max(0, min(n, last)-10)*maximum//(last-10)
        vals = (min(n, 10)*2, min(n, 10)*100, growth(5, 30), 0, 0,
                growth(20, 21), max(0, min(n, 20)-11)*15//9, 10 if n >= 21 else 0,
                5 if n >= 23 else 2 if n == 22 else 0, growth(5, 30)*10,
                growth(5, 30)*10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        levels.append(dict(level=n, name='Koń — poziom %d' % n, color='#FFD36A', icon='',
                           bonuses=dict(zip(KEYS, vals))))
    return dict(schema=SCHEMA, master_enabled=True, enabled=True, client_enabled=True, levels=levels)


def validate(value):
    if not isinstance(value, dict) or set(value) != {'schema','master_enabled','enabled','client_enabled','levels'}:
        raise ValueError('Nieprawidłowe pola konfiguracji.')
    if value['schema'] != SCHEMA or type(value['master_enabled']) is not bool or type(value['enabled']) is not bool or type(value['client_enabled']) is not bool:
        raise ValueError('Nieprawidłowy format lub przełączniki.')
    if not isinstance(value['levels'], list) or len(value['levels']) != 31:
        raise ValueError('Wymagane poziomy 0–30.')
    for n, row in enumerate(value['levels']):
        if not isinstance(row, dict) or set(row) != {'level','name','color','icon','bonuses'} or type(row['level']) is not int or row['level'] != n:
            raise ValueError('Nieprawidłowa kolejność poziomów.')
        name = row['name']
        if not isinstance(name, str) or not name or len(name) > 60 or any(ord(c)<32 for c in name) or '|' in name:
            raise ValueError('Nazwa: 1–60 znaków, bez kodów formatowania.')
        name.encode('cp1250')
        if not isinstance(row['color'], str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', row['color']):
            raise ValueError('Kolor musi mieć format #RRGGBB.')
        if not isinstance(row['icon'], str) or (row['icon'] and not re.fullmatch(re.escape(ICON_PREFIX)+r'[a-f0-9]{64}\.tga',row['icon'])):
            raise ValueError('Nieprawidłowa ścieżka grafiki.')
        if not isinstance(row['bonuses'], dict) or set(row['bonuses']) != set(KEYS):
            raise ValueError('Nieprawidłowa lista bonusów.')
        for key, limit in zip(KEYS, LIMITS):
            v = row['bonuses'][key]
            if type(v) is not int or not 0 <= v <= limit or (n == 0 and v != 0):
                raise ValueError('Nieprawidłowy bonus %s na poziomie %d.' % (key,n))
    return copy.deepcopy(value)


def canonical(config):
    return json.dumps(validate(config), ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(config):
    return hashlib.sha256(canonical(config)).hexdigest()


def runtime_body(config):
    config=validate(config)
    lines=['%d %d' % (config['master_enabled'],config['enabled'])]
    lines += [' '.join(map(str,[row['level']]+[row['bonuses'][k] for k in KEYS])) for row in config['levels'][1:]]
    return ('\n'.join(lines)+'\n').encode('ascii')


def engine_revision(config):
    return hashlib.sha256(runtime_body(config)).hexdigest()


def runtime(config):
    body=runtime_body(config)
    return (SCHEMA+' '+hashlib.sha256(body).hexdigest()+'\n').encode('ascii')+body


def command(config, operation):
    if not re.fullmatch('[a-f0-9]{32}',operation):raise ValueError('Invalid operation id')
    return ('SEBAN_HORSE_REQUEST_V2 '+operation+'\n').encode('ascii')+runtime(config)


def client_revision(config):
    return hashlib.sha256(client_module(config)).hexdigest()


def validate_tga(raw):
    if not 18 <= len(raw) <= 256*256*4+273:
        raise ValueError('Grafika: nieskompresowany TGA 24/32-bit, do 256×256.')
    ident,cmap,kind = raw[:3]
    width,height = struct.unpack_from('<HH',raw,12)
    bits=raw[16]
    if cmap or kind != 2 or not 1 <= width <= 256 or not 1 <= height <= 256 or bits not in (24,32) or raw[17]&0xc0:
        raise ValueError('Grafika: nieskompresowany TGA 24/32-bit, do 256×256.')
    if len(raw) < 18+ident+width*height*(bits//8):
        raise ValueError('Niekompletna grafika TGA.')
    return ICON_PREFIX+hashlib.sha256(raw).hexdigest()+'.tga'


def seal_module(raw):
    return raw+b'# SEBAN_HORSE_SHA256 '+hashlib.sha256(raw).hexdigest().encode('ascii')+b'\n'


def verify_module(raw):
    marker=b'# SEBAN_HORSE_SHA256 '
    before,sep,digest=raw.rpartition(marker)
    return bool(sep and digest==hashlib.sha256(before).hexdigest().encode('ascii')+b'\n')


def client_module(config):
    cfg=validate(config)
    if not cfg['master_enabled'] or not cfg['client_enabled']:
        return seal_module(b'# SEBAN_HORSE_V2; hidden preview\ndef icon(level,original):return original\ndef append_level(tip,level):pass\ndef append_horse(tip,grade,rawlevel):pass\n')
    # ASCII source with explicit CP1250 byte escapes: embedded client Python 2.
    rows=[]
    for r in cfg['levels']:
        rows.append((r['name'].encode('cp1250'),int('FF'+r['color'][1:],16),r['icon'],{key:r['bonuses'][key] for key in KEYS}))
    def byte_literal(raw):
        return "'" + "".join("\\x%02x" % b for b in raw) + "'"
    literals="["+",".join("(%s,%d,%r,%r)" % (byte_literal(n),c,i,v) for n,c,i,v in rows)+"]"
    labels="("+",".join("(%r,%s)"%(key,byte_literal(label.removesuffix(' ‰').removesuffix(' %').encode('cp1250'))) for key,label in zip(KEYS,LABELS))+",)"
    return seal_module(('''# SEBAN_HORSE_V2; generated from the operator's configuration.
ENABLED = %r
VISIBLE = %r
ROWS = %s
LABELS = %s

def icon(level, original):
    if not VISIBLE: return original
    return ROWS[max(0,min(30,int(level)))][2] or original

def append_values(tip, values, color):
    for key,label in LABELS:
        value=values.get(key,0)
        if value:
            if key in ('resistMonster','resistBoss'): text=('%%g' %% (value/10.0))+'%%%%'
            else: text=str(value)+('%%%%' if key in ('monster','boss','stone','classes','human','elements','speed','crit','penetrate','drop','exp','yang') else '')
            tip.AppendTextLine(label+': '+('+' if value>0 else '')+text,color)

def append_level(tip, level):
    if not VISIBLE: return
    level=max(0,min(30,int(level)))
    name,color,image,values=ROWS[level]
    tip.AppendSpace(5)
    tip.AppendTextLine(name,color)
    if not ENABLED:
        tip.AppendTextLine('Bonusy konia wylaczone',color)
        return
    append_values(tip,values,color)
    if level<30:
        following=ROWS[level+1][3]
        delta=dict((key,following.get(key,0)-values.get(key,0)) for key,label in LABELS)
        tip.AppendSpace(5)
        tip.AppendTextLine('Nastepny poziom: %%d' %% (level+1),color)
        if any(delta.values()): append_values(tip,delta,color)
        else: tip.AppendTextLine('Bez wzrostu bonusow na tym poziomie',color)

def append_horse(tip,grade,rawlevel):
    level=30 if grade>=3 else int(rawlevel)+(19 if grade==1 else 29 if grade==2 else 0)
    append_level(tip,level)
''' % (cfg['enabled'],cfg['client_enabled'],literals,labels)).encode('ascii'))


def replace_one(raw, old, new):
    if raw.count(old) != 1:
        raise ValueError('Konflikt klienta: oczekiwany fragment występuje inaczej.')
    return raw.replace(old,new,1)


def client_patches(files, config):
    """Only targeted bonus blocks; unrelated modules and surrounding edits survive."""
    result={}
    raw=files['customrewardtooltip.py']
    if b'# SEBAN_HORSE_HOOK_V1' not in raw:
        start=raw.find(b'def append_horse(');end=raw.find(b'\ndef append_poly(',start)
        if start<0 or end<0 or raw.count(b'def append_horse(')!=1:
            raise ValueError('Konflikt customrewardtooltip.py: brak znanej funkcji konia.')
        if hashlib.sha256(raw[start:end]).hexdigest() != '2e4acc6a6c9e47bfe54759fc56a28dc05ffbe42ce19839a4e04319dd6449d70c':
            raise ValueError('Konflikt: funkcja bonusow konia zostala zmieniona przez uzytkownika.')
        nl=b'\r\n' if b'\r\n' in raw else b'\n'
        body=nl.join((b'def append_horse(tip, grade, rawlevel):',b'    # SEBAN_HORSE_HOOK_V1',b'    import sebanhorseclient',b'    sebanhorseclient.append_horse(tip,grade,rawlevel)',b''))
        raw=raw[:start]+body+raw[end:]
    else:
        nl=b'\r\n' if b'\r\n' in raw else b'\n'
        start=raw.find(b'def append_horse(');end=raw.find(b'\ndef append_poly(',start)
        expected=nl.join((b'def append_horse(tip, grade, rawlevel):',b'    # SEBAN_HORSE_HOOK_V1',b'    import sebanhorseclient',b'    sebanhorseclient.append_horse(tip,grade,rawlevel)',b''))
        if start<0 or end<0 or raw.count(b'# SEBAN_HORSE_HOOK_V1')!=1 or raw[start:end]!=expected:
            raise ValueError('Konflikt zmodyfikowanego hooka klienta.')
    result['customrewardtooltip.py']=raw
    raw=files['uiaffectbar.py']
    if b'# SEBAN_HORSE_AFFECT_V1' not in raw:
        start=raw.find(b'\t\t# HORSE_PERMANENT_REWARDS_V1')
        end=raw.find(b'\t\tself.tooltip.ShowToolTip()',start)
        if start<0 or end<0 or raw.count(b'\t\t# HORSE_PERMANENT_REWARDS_V1')!=1:
            raise ValueError('Konflikt uiaffectbar.py: brak znanego bloku bonusów konia.')
        if hashlib.sha256(raw[start:end]).hexdigest() != '025c81b8b9d5f4338d8362aae50cdafd5d611fffad35101a1d353b4833aa6396':
            raise ValueError('Konflikt: blok bonusow przy ikonie konia zostal zmieniony.')
        nl=b'\r\n' if b'\r\n' in raw else b'\n'
        body=nl.join((b'\t\t# SEBAN_HORSE_AFFECT_V1',b'\t\timport sebanhorseclient',b'\t\tsebanhorseclient.append_level(self.tooltip,self.level)',b''))
        raw=raw[:start]+body+raw[end:]
        old=b'\t\tfileName = self.FILE_DICT[health * 10 + battery]'
        new=old+nl+b'\t\timport sebanhorseclient'+nl+b'\t\tfileName = sebanhorseclient.icon(level,fileName)'
        raw=replace_one(raw,old,new)
    else:
        nl=b'\r\n' if b'\r\n' in raw else b'\n'
        start=raw.find(b'\t\t# SEBAN_HORSE_AFFECT_V1');end=raw.find(b'\t\tself.tooltip.ShowToolTip()',start)
        expected=nl.join((b'\t\t# SEBAN_HORSE_AFFECT_V1',b'\t\timport sebanhorseclient',b'\t\tsebanhorseclient.append_level(self.tooltip,self.level)',b''))
        icon=b'\t\tfileName = self.FILE_DICT[health * 10 + battery]'+nl+b'\t\timport sebanhorseclient'+nl+b'\t\tfileName = sebanhorseclient.icon(level,fileName)'
        if start<0 or end<0 or raw.count(b'# SEBAN_HORSE_AFFECT_V1')!=1 or raw[start:end]!=expected or raw.count(icon)!=1:
            raise ValueError('Konflikt hooka ikony konia.')
    result['uiaffectbar.py']=raw
    result['sebanhorseclient.py']=client_module(config)
    return result


def _patch_pack(index,data,config,assets=None):
    if len(index)>32*1024*1024 or len(data)>256*1024*1024:
        raise ValueError('Przekroczony limit ROOT.')
    if index[:4]!=b'EPKD' and (len(index)<16 or struct.unpack_from('<I',index,12)[0]>32*1024*1024):
        raise ValueError('Nieprawidłowy rozmiar indeksu.')
    ver,entries=eterpack.read_index_bytes(index)
    if ver!=2 or len(entries)>50000: raise ValueError('Nieobsługiwany indeks ROOT.')
    groups={};decoded={};total=0
    needed_names={'customrewardtooltip.py','uiaffectbar.py','sebanhorseclient.py'}
    needed_names.update(r['icon'][3:] for r in validate(config)['levels'] if r['icon'])
    for e in entries:
        name=e.name.replace('\\','/').lower()
        if name.startswith('d:/'):name=name[3:]
        if name.startswith('/') or '..' in name.split('/') or not name:
            raise ValueError('Niebezpieczna nazwa wpisu.')
        if e.ctype not in (0,1,2) or min(e.pos,e.size,e.real)<0 or e.size>16*1024*1024 or e.pos+e.size>len(data):
            raise ValueError('Nieobsługiwany lub uszkodzony wpis ROOT.')
        blob=data[e.pos:e.pos+e.size]
        if zlib.crc32(blob)&0xffffffff!=e.dcrc:raise ValueError('Niezgodne CRC pary ROOT.')
        if e.ctype and (len(blob)<16 or struct.unpack_from('<I',blob,12)[0]>16*1024*1024):
            raise ValueError('Za duży wpis ROOT.')
        total+=struct.unpack_from('<I',blob,12)[0] if e.ctype else len(blob)
        if total>512*1024*1024:raise ValueError('Limit rozpakowania ROOT.')
        if name in needed_names:
            raw=eterpack.read_entry(data,e)
            if name in decoded and decoded[name]!=raw:raise ValueError('Sprzeczne duplikaty ROOT.')
            decoded[name]=raw
        elif name in groups:
            previous=groups[name][0];old_blob=data[previous.pos:previous.pos+previous.size]
            if blob!=old_blob and eterpack.read_entry(data,e)!=eterpack.read_entry(data,previous):raise ValueError('Sprzeczne duplikaty ROOT.')
        groups.setdefault(name,[]).append(e)
    needed=('customrewardtooltip.py','uiaffectbar.py')
    if any(n not in decoded for n in needed):raise ValueError('Brak modułów wymaganych w aktualnym ROOT.')
    if 'sebanhorseclient.py' in decoded and (not decoded['sebanhorseclient.py'].startswith(b'# SEBAN_HORSE_V2;') or not verify_module(decoded['sebanhorseclient.py'])):
        raise ValueError('Kolizja sebanhorseclient.py: obcy, zmieniony lub nieobsługiwany moduł.')
    replacements=client_patches(decoded,config)
    for row in validate(config)['levels']:
        if row['icon']:
            source=row['icon'];name=source[3:]
            asset=(assets or {}).get(source)
            if asset is None or validate_tga(asset)!=source:raise ValueError('Brak zgodnej grafiki: '+source)
            if name in decoded and decoded[name]!=asset:raise ValueError('Kolizja zawartosci grafiki ROOT.')
            replacements[name]=asset
    output=bytearray(data)
    manifest=[]
    for name,raw in replacements.items():
        existing=groups.get(name,[])
        if existing and decoded[name]==raw:continue
        if not existing:
            e=eterpack.Entry(bytes(192));e.id=max((x.id for x in entries),default=-1)+1
            e.name=name;e.fcrc=eterpack.name_crc(name)
            if any(x.fcrc==e.fcrc for x in entries):raise ValueError('Kolizja CRC nazwy nowego wpisu ROOT.')
            e.ctype=2;entries.append(e);existing=[e]
        for e in existing:
            blob=eterpack.encode_entry(raw,e.ctype)
            e.pos=len(output);e.size=len(blob);e.real=(e.size+255)//256*256;e.dcrc=zlib.crc32(blob)&0xffffffff
            output.extend(blob);output.extend(b'\0'*(e.real-e.size))
        manifest.append(dict(path=name,before=hashlib.sha256(decoded[name]).hexdigest() if name in decoded else None,after=hashlib.sha256(raw).hexdigest()))
    if not manifest:return index,data,[]
    out_index=eterpack.write_index_bytes(ver,entries);out_data=bytes(output)
    # Verify all replacements and exact byte identity of every untouched record.
    reread=eterpack.read_index_bytes(out_index)[1]
    for e in reread:
        name=e.name.replace('\\','/').lower()
        if name.startswith('d:/'):name=name[3:]
        if name in replacements and eterpack.read_entry(out_data,e)!=replacements[name]:raise ValueError('Błąd weryfikacji ROOT.')
    return out_index,out_data,manifest


def patch_pack(index,data,config,assets=None):
    try:
        return _patch_pack(index,data,config,assets)
    except (struct.error,IndexError,OverflowError) as exc:
        raise ValueError('Uszkodzona lub nieobslugiwana para ROOT.') from exc
