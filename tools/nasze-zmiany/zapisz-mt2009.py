#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
from datetime import datetime
from zoneinfo import ZoneInfo
import ast
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile

os.umask(0o077)
BASE = Path('/root/mt2009-git-20261019-203457-8wnhzjlu')
PROJECT = Path('/opt/metin2/linux-port')
REPO = BASE / 'repo'
SCANNER = BASE / 'narzedzia/gitleaks-8.24.2/gitleaks'
PUBLISHER = Path('/root/odswiez-pelny-zip.py')
description = ' '.join(sys.argv[1:]).strip() or 'Zapis zmian VPS'
lock = (BASE / 'zapis-automatyczny.lock').open('a')
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit('STOP: inny zapis jest juz uruchomiony.')

now = datetime.now(ZoneInfo('Europe/Berlin'))
WORK = BASE / 'zapisy' / now.strftime('%Y%m%d-%H%M%S-%f')
DEST = WORK / 'do-repo'
PRIVATE = WORK / 'prywatne-NIE-WYSYLAC'
DEST.mkdir(parents=True, mode=0o700)
PRIVATE.mkdir(mode=0o700)
env = dict(os.environ)
env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')

def run(args, data=None, timeout=120):
    process = subprocess.Popen(
        args, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, start_new_session=True
    )
    timed = False
    try:
        stdout, stderr = process.communicate(data, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
    if timed or process.returncode:
        log = WORK / 'blad-operacji.txt'
        log.write_bytes(stderr)
        raise RuntimeError('Przekroczony czas lub blad operacji. Log: ' + str(log))
    return stdout

def git(*args):
    return run(['git', '-C', str(REPO), *args])

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

copied = {}
def put(relative, raw, source='wygenerowany', executable=False):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise RuntimeError('Nieprawidlowa sciezka docelowa.')
    target = DEST / relative
    if relative.as_posix().startswith('linux-port/') and target.name == '.env.example':
        raw = re.sub(
            rb'(?im)^([A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|PRIVATE_KEY)'
            rb'[A-Z0-9_]*[ \t]*=)[^\r\n]*',
            rb'\g<1>CHANGE_ME_LOCALLY', raw
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    if executable:
        target.chmod(0o700)
    copied[relative.as_posix()] = {
        'source': str(source), 'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest()
    }

def take(path, relative):
    if path.is_symlink() or not path.is_file():
        return
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('Plik zmienil sie podczas zapisu: ' + str(path))
    put(relative, raw, path, bool(before.st_mode & 0o111))

def walk(root):
    if not root.is_dir():
        return
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if d not in {'.git', '.obj', '__pycache__', '.cache', 'base', 'node_modules'}
            and not (Path(current)/d).is_symlink()
        ]
        for name in sorted(files):
            path = Path(current)/name
            if not path.is_symlink():
                yield path

try:
    print('Zapis lokalny:', WORK, flush=True)
    print('Pobieranie aktualnego main...', flush=True)
    git('fetch', '--filter=blob:none', '--no-tags', '--no-recurse-submodules',
        '--no-auto-maintenance', 'origin', 'refs/heads/main')
    parent = git('rev-parse', 'FETCH_HEAD').decode().strip()
    (WORK/'base-commit.txt').write_text(parent, encoding='ascii')
    paths = {
        p.decode('utf-8') for p in
        git('ls-tree', '-r', '--name-only', '-z', parent).split(b'\0') if p
    }

    print('Aktualizacja dbdata i ZIP dostepnych w panelu...', flush=True)
    if not PUBLISHER.is_file():
        raise RuntimeError('Brak publikatora: ' + str(PUBLISHER))
    (WORK/'publikacja-panelu.log').write_bytes(
        run(['python3', str(PUBLISHER)], timeout=600)
    )

    mounts = json.loads(run([
        'docker', 'inspect', '--format', '{{json .Mounts}}', 'metin2-seban-panel'
    ]))
    spool = next(
        Path(m['Source']) for m in mounts if m['Destination'] == '/opt/m2spool'
    )
    downloads = spool/'custom-ui-work/downloads'
    expected = {
        stem+suffix: digest(downloads/(stem+suffix))
        for stem in ('root', 'gamedata', 'dbdata')
        for suffix in ('.index', '.data')
    }

    print('Zbieranie aktualnych plikow projektu...', flush=True)
    for name in sorted(paths):
        if name.startswith('linux-port/'):
            path = PROJECT/Path(name).relative_to('linux-port')
            if path.resolve().is_relative_to(PROJECT.resolve()):
                take(path, name)
        elif name == 'AGENTS.md' or name.startswith('docs/nasze-zmiany/'):
            put(name, git('show', parent+':'+name), 'Git '+parent)

    extensions = {
        '.py','.sh','.ps1','.json','.sql','.quest','.lua','.txt',
        '.cpp','.c','.h','.hpp','.inc','.html','.css','.js','.yml','.yaml',
        '.tga','.png','.jpg','.jpeg','.dds','.sub','.msm','.msa','.gr2',
        '.md','.csv','.ttf','.otf'
    }
    roots = [
        'docker/game/quest','docker/game/ukrainka','docker/game/bin',
        'docker/game/arezzo','docker/game/atlantyda','docker/game/dungeons',
        'docker/game/ochao','docker/game/zodiak','docker/game/treasure_hunt',
        'docker/seban-panel/m2clientpack','docker/seban-panel/templates',
        'docker/seban-panel/dbeditor','docker/seban-panel/integration',
        'docker/seban-panel/updater','docker/mariadb/playerbot',
        'overlays/playerbot/src'
    ]
    for relative in roots:
        for path in walk(PROJECT/relative):
            if path.suffix.lower() in extensions or relative.endswith('/bin'):
                take(path, Path('linux-port')/path.relative_to(PROJECT))
    for path in (PROJECT/'docker/seban-panel').glob('*.py'):
        take(path, Path('linux-port')/path.relative_to(PROJECT))

    print('Zbieranie zrodel silnika...', flush=True)
    private_definitions = {}
    for relative in ('docker/game/src/server/game/src','docker/game/src/server/common'):
        for path in walk(PROJECT/relative):
            if path.name == 'mt2009_private_protocol_keys.h':
                take_private = PRIVATE/path.name
                shutil.copyfile(path, take_private)
                continue
            if path.suffix.lower() not in {'.cpp','.c','.h','.hpp','.inc','.lua','.quest'}:
                continue
            raw = path.read_bytes()
            original = raw
            text = raw.decode('latin1')
            substitutions = []
            if path.name in ('desc.cpp','input_main.cpp'):
                if path.name == 'desc.cpp':
                    specifications = [
                        (r'(thecore_memcpy\s*\(\s*m_adwEncryptionKey\s*,\s*)'
                         r'("(?:\\.|[^"\\])*")',
                         'MT2009_PRIVATE_'+'PROTOCOL_ENCRYPT'),
                        (r'(thecore_memcpy\s*\(\s*m_adwDecryptionKey\s*,\s*)'
                         r'("(?:\\.|[^"\\])*")',
                         'MT2009_PRIVATE_'+'PROTOCOL_DECRYPT')
                    ]
                else:
                    specifications = [
                        (r'(TPacketCGRequestInfoResponse[\s\S]{0,2000}?'
                         r'\bauto\s+key\s*=\s*)("(?:\\.|[^"\\])*")',
                         'MT2009_PRIVATE_'+'REQUEST_INFO_KEY')
                    ]
                for pattern, symbol in specifications:
                    matches = list(re.finditer(pattern, text))
                    if len(matches) == 1:
                        match = matches[0]
                        literal = match.group(2)
                        private_definitions[symbol] = literal
                        text = text[:match.start(2)] + symbol + text[match.end(2):]
                        substitutions.append((symbol, literal))
                    elif not matches and symbol in text:
                        if not (PROJECT/'docker/game/src/server/game/src/mt2009_private_protocol_keys.h').is_file():
                            raise RuntimeError('Brak lokalnego prywatnego naglowka.')
                    else:
                        raise RuntimeError('Inna skladnia stalej w '+path.name)
                if substitutions:
                    check = text
                    for symbol, literal in substitutions:
                        check = check.replace(symbol, literal)
                    if check.encode('latin1') != original:
                        raise RuntimeError('Nieudana kontrola odwracalnosci.')
                    if '#include "mt2009_private_protocol_keys.h"' not in text:
                        newline = '\r\n' if b'\r\n' in original else '\n'
                        text = '#include "mt2009_private_protocol_keys.h"'+newline+text
                    raw = text.encode('latin1')
            put(
                Path('customizations/server-source-snapshot')/path.relative_to(PROJECT),
                raw, path
            )
    if private_definitions:
        header = '#pragma once\n' + ''.join(
            '#define '+symbol+' '+literal+'\n'
            for symbol,literal in private_definitions.items()
        )
        existing = PRIVATE/'mt2009_private_protocol_keys.h'
        if existing.exists():
            existing = PRIVATE/'mt2009_private_protocol_keys-z-oryginalow.h'
        existing.write_bytes(header.encode('latin1'))
    for name in ('.env','docker-compose.override.yml'):
        source = PROJECT/'docker'/name
        if source.is_file():
            shutil.copyfile(source, PRIVATE/name)

    print('Odczyt aktualnych paczek klienta...', flush=True)
    worker = r"""
from pathlib import Path, PurePosixPath
import hashlib, io, json, sys, tarfile
from m2clientpack.eterpack import read_index_bytes, read_entry
source=Path('/opt/m2spool/custom-ui-work/downloads')
expected=json.loads(sys.argv[1])
for name,digest in expected.items():
    if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Paczki zmienily sie podczas zapisu')
seen={}
metadata=[]
total=0
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as archive:
    def emit(name,raw):
        global total
        total+=len(raw)
        if total>768*1024*1024: raise RuntimeError('Limit rozpakowania')
        info=tarfile.TarInfo(name)
        info.size=len(raw); info.mode=0o600
        archive.addfile(info,io.BytesIO(raw))
    for stem in ('root','gamedata','dbdata'):
        index=(source/(stem+'.index')).read_bytes()
        version,entries=read_index_bytes(index)
        data=(source/(stem+'.data')).read_bytes()
        emit('original-indexes/'+stem+'.index',index)
        for ordinal,entry in enumerate(entries):
            original=entry.name
            name=original.replace('\\','/').rstrip('\0')
            if len(name)>=3 and name[1:3]==':/': name=name[3:]
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or not p.parts:
                raise RuntimeError('Nieprawidlowa sciezka')
            target=stem+'/'+str(p)
            raw=read_entry(data,entry)
            digest=hashlib.sha256(raw).hexdigest()
            group=target.casefold()
            if group in seen:
                old_digest,old_target=seen[group]
                if old_digest!=digest: raise RuntimeError('Rozne wersje wpisu: '+target)
                target=old_target
            else:
                emit(target,raw)
                seen[group]=(digest,target)
            metadata.append({'pack':stem,'ordinal':ordinal,'original':original,
                             'saved':target,'sha256':digest})
    emit('METADANE-WPISOW.json',json.dumps(metadata,ensure_ascii=False,indent=2).encode())
    emit('dbdata_stamp.txt',(source/'dbdata_stamp.txt').read_bytes())
"""
    errors = (WORK/'odczyt-klienta.log').open('wb')
    process = subprocess.Popen(
        ['docker','exec','-i','-w','/app','metin2-seban-panel','python3','-c',
         worker,json.dumps(expected)],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=errors
    )
    try:
        total=0
        with tarfile.open(fileobj=process.stdout,mode='r|') as archive:
            for member in archive:
                relative=PurePosixPath(member.name)
                if not member.isfile() or relative.is_absolute() or '..' in relative.parts:
                    raise RuntimeError('Nieprawidlowy wpis klienta')
                total+=member.size
                if total>768*1024*1024: raise RuntimeError('Limit klienta')
                raw=archive.extractfile(member).read()
                put(Path('customizations/client-packs')/member.name,raw,
                    'opublikowana paczka klienta')
        process.stdout.close()
        if process.wait()!=0:
            raise RuntimeError('Blad odczytu klienta. Log: '+str(WORK/'odczyt-klienta.log'))
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    finally:
        errors.close()

    print('Zapis danych konfiguracyjnych gry z bazy — bez kont i postaci...',flush=True)
    def sql(query):
        return run([
            'docker','exec','-i','metin2-db','sh','-c',
            'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" exec mariadb -uroot '
            '--batch --raw --skip-column-names --default-character-set=utf8mb4'
        ],query.encode('utf-8')).decode('utf-8')
    tables = (
        'item_proto','mob_proto','crafting_proto','refine_proto',
        'skill_proto','shop','shop_item'
    )
    for table in tables:
        query=(
            "SELECT JSON_OBJECT('name',COLUMN_NAME,'type',DATA_TYPE,'key',COLUMN_KEY,'charset',CHARACTER_SET_NAME,'collation',COLLATION_NAME) "
            "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='world' "
            "AND TABLE_NAME='"+table+"' ORDER BY ORDINAL_POSITION;"
        )
        columns=[json.loads(line) for line in sql(query).splitlines() if line]
        if not columns:
            continue
        expressions=[]
        for col in columns:
            name=col['name']
            if not re.fullmatch(r'[A-Za-z0-9_]+',name):
                raise RuntimeError('Nieobslugiwana nazwa kolumny.')
            binary=col['type'] in {
                'binary','varbinary','tinyblob','blob','mediumblob','longblob','bit',
                'char','varchar','tinytext','text','mediumtext','longtext','enum','set'
            }
            col['hex_encoded']=binary
            value=('CONVERT(HEX(`'+name+'`) USING utf8mb4) COLLATE utf8mb4_bin' if binary else '`'+name+'`')
            expressions.extend(["CONVERT('"+name+"' USING utf8mb4) COLLATE utf8mb4_bin",value])
        order=[c['name'] for c in columns if c['key']=='PRI']
        if not order:
            order=[c['name'] for c in columns]
        query=(
            'SELECT JSON_OBJECT('+','.join(expressions)+') FROM `world`.`'+table+
            '` ORDER BY '+','.join('`'+n+'`' for n in order)+';'
        )
        rows=[json.loads(line) for line in sql(query).splitlines() if line]
        put(
            'customizations/database/world/'+table+'.json',
            json.dumps({'table':table,'columns':columns,'rows':rows},
                       ensure_ascii=False,indent=2).encode('utf-8'),
            'world.'+table
        )

    for name in ('zapisz-mt2009','wyslij-zestaw.py','przejrzane-konteksty.json'):
        source = Path('/usr/local/bin/zapisz-mt2009') if name=='zapisz-mt2009' else BASE/name
        destination = 'zapisz-mt2009.py' if name=='zapisz-mt2009' else name
        take(source,Path('tools/nasze-zmiany')/destination)
    take(PUBLISHER,'tools/nasze-zmiany/odswiez-pelny-zip.py')

    method = """# Jedna komenda zapisu VPS

Uruchom na skonfigurowanym VPS:
    zapisz-mt2009 "opis zmian"

Polecenie odswieza dbdata i ZIP przez istniejacy publikator panelu,
zbiera aktualne zrodla, odczytuje opublikowane ROOT/gamedata/dbdata,
zapisuje migawki wybranych tabel world bez kont i postaci,
sprawdza sekrety, tworzy commit i wykonuje zwykly push na main.

Kopie prywatnych ustawien i stalych protokolu pozostaja tylko na VPS.
Katalog kazdego uruchomienia: /root/mt2009-git-20261019-203457-8wnhzjlu/zapisy/.
W razie bledu nie usuwaj go: zawiera zapis i diagnostyke.

Zrodla i opublikowane paczki moga reprezentowac rozne etapy wdrozenia.
Polecenie nie kompiluje silnika ani nie przebudowuje ROOT/gamedata.
Zmiany klienta istniejace tylko na Windows trzeba osobno przeslac lub zachowac.
Paczki etc/locale nadal wymagaja osobnego zabezpieczenia.

customizations/database/world zawiera dane do porownania i selektywnego
odtworzenia. Kolumny oznaczone hex_encoded przechowuja HEX oryginalnych bajtow.
Nie importuj calej migawki na nowa wersje gry bez porownania i wyboru zmian.
STAN-ZAPISU.md nadal opisuje historyczne braki do uzupelnienia.

Przy nowym trafieniu skanera zapis zatrzyma sie z lokalnymi plikami.
Wyjatki obejmuja tylko znany, przejrzany kontekst kodu.
"""
    put('docs/nasze-zmiany/JEDNA-KOMENDA.md',method.encode('utf-8'))
    # MT2009_NEW_CHAT_SAVE_POLICY_V1
    save_policy = """
## Zapis po potwierdzeniu dzialania przez uzytkownika

Gdy uzytkownik potwierdzi, ze zmiana dziala, i poprosi o zapis,
podaj gotowa komende do PuTTY:
    zapisz-mt2009 "konkretny opis wykonanych zmian"

Sam uzupelnij opis rzeczywistymi zmianami.
Nie wymagaj ponownej konfiguracji GitHuba przy zwyklym zapisie.
Nie traktuj samego potwierdzenia dzialania jako dowodu wykonania zapisu.
Nie twierdz, ze zmiany sa na GitHubie, dopoki wynik nie potwierdzi push.
Przy bledzie zachowaj lokalny zapis i napraw konkretny problem.
Nie wpisuj hasel, kluczy ani danych kont do opisu.
"""
    agents = DEST/'AGENTS.md'
    if not agents.is_file():
        raise RuntimeError('Brak AGENTS.md do uzupelnienia.')
    current = agents.read_text(encoding='utf-8')
    if '## Zapis po potwierdzeniu dzialania przez uzytkownika' not in current:
        put('AGENTS.md',(current.rstrip()+'\n'+save_policy).encode('utf-8'))

    new_chat = """# Tekst do nowego czatu

Pracujemy nad repozytorium:
https://github.com/dawiddobrzanski99-pixel/mt2009-sp-plus
Galaz: main.

Najpierw przeczytaj AGENTS.md oraz docs/nasze-zmiany/START-TUTAJ.md,
WYMAGANIA-ZAPISU.md, STAN-ZAPISU.md, WERYFIKACJA.md,
JEDNA-KOMENDA.md, REJESTR-ZAPISOW.md i mape ostatniego zapisu.

Zrodla silnika: customizations/server-source-snapshot.
Opublikowany klient: customizations/client-packs.
Migawki danych gry: customizations/database/world.
Kod projektu: linux-port.
Narzedzia zapisu: tools/nasze-zmiany.

Pracuj na istniejacej instalacji VPS.
Zachowaj nasze dotychczasowe funkcje, grafiki, bonusy i blokady.
Nie zastepuj aktualnego klienta ani serwera starsza cala paczka.
Czytaj opisane braki; nie zakladaj, ze wszystkie historyczne zmiany
zostaly zweryfikowane albo ze przygotowany fix zostal wdrozony.

Po zmianach dotyczacych klienta uwzglednij aktualne pliki do pobrania
z panelu. Zachowuj zgodnosc paczek, dbdata i znacznika.
Zmiany tylko na Windows oraz etc/locale wymagaja osobnego zabezpieczenia.

Gdy napisze, ze dziala i chce zapis, podaj:
zapisz-mt2009 "opis rzeczywiscie wykonanych zmian"
Opis uzupelnij sam. Sukces potwierdz dopiero po udanym push.

Prywatne ustawienia i naglowek protokolu sa przechowywane poza GitHubem.
Migawki world sluza do porownania i selektywnego odtwarzania;
nie importuj ich hurtowo na nowsza wersje gry.
"""
    put('docs/nasze-zmiany/NOWY-CZAT.md',new_chat.encode('utf-8'))

    registry = DEST/'docs/nasze-zmiany/REJESTR-ZAPISOW.md'
    old=registry.read_text(encoding='utf-8') if registry.is_file() else '# Rejestr zapisow\n'
    put('docs/nasze-zmiany/REJESTR-ZAPISOW.md',
        (old+'\n- '+now.isoformat(timespec='seconds')+' — '+description+'\n').encode('utf-8'))
    put('docs/nasze-zmiany/MAPA-OSTATNIEGO-ZAPISU.json',
        json.dumps(copied,ensure_ascii=False,indent=2).encode('utf-8'))

    print('Oddzielanie plikow niezmienionych wzgledem GitHuba...',flush=True)
    baseline_entries = {}
    for entry in git('ls-tree','-r','-z',parent).split(b'\0'):
        if entry:
            meta, filename = entry.split(b'\t',1)
            filemode, kind, oid = meta.decode().split()
            if kind == 'blob':
                baseline_entries[filename.decode('utf-8')] = (filemode,oid)
    unchanged = WORK/'niezmienione-poza-commitem'
    moved = 0
    for path in sorted(DEST.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(DEST)
        name = relative.as_posix()
        old = baseline_entries.get(name)
        if not old:
            continue
        raw = path.read_bytes()
        oid = hashlib.sha1(
            b'blob '+str(len(raw)).encode()+b'\0'+raw
        ).hexdigest()
        filemode = '100755' if path.stat().st_mode & 0o111 else '100644'
        if old == (filemode,oid):
            target = unchanged/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            os.replace(path,target)
            moved += 1
    print('Niezmienione kopie pozostawione lokalnie:',moved,flush=True)

    print('Skanowanie zestawu...',flush=True)
    scan_report=WORK/'skan.json'
    with (WORK/'skan.log').open('wb') as log:
        result=subprocess.run([
            str(SCANNER),'dir',str(DEST),'--no-banner','--redact=100',
            '--report-format','json','--report-path',str(scan_report),'--log-level','error'
        ],stdin=subprocess.DEVNULL,stdout=log,stderr=log,timeout=240)
    if result.returncode not in (0,1) or not scan_report.is_file():
        raise RuntimeError('Blad skanera. Patrz skan.log.')
    approved=[]
    known=json.loads((BASE/'przejrzane-konteksty.json').read_text())
    allowed={(r['p'],r['c']) for r in known}
    for hit in json.loads(scan_report.read_text()):
        path=Path(hit['File'])
        if not path.is_absolute(): path=DEST/path
        relative=path.resolve().relative_to(DEST.resolve()).as_posix()
        number=int(hit['StartLine'])
        lines=path.read_bytes().splitlines()
        context=hashlib.sha256(b'\n'.join(lines[max(0,number-2):number+1])).hexdigest()
        if hit.get('RuleID')!='generic-api-key' or (relative,context) not in allowed:
            print('Do przegladu:',relative,'linia',number,hit.get('RuleID'))
            raise RuntimeError('Nowe trafienie. Nie wykonano automatycznej publikacji Git.')
        approved.append({'path':relative,'line':number})
    (WORK/'zaakceptowane-trafienia.json').write_text(
        json.dumps(approved),encoding='utf-8'
    )
    print('Tworzenie commita i push...',flush=True)
    result=subprocess.run(
        ['python3',str(BASE/'wyslij-zestaw.py'),str(WORK)],env=env
    )
    if result.returncode:
        raise RuntimeError('Wysylanie zatrzymane. Zapis lokalny pozostaje zachowany.')
    print('\nGOTOWE. Komenda na przyszlosc:')
    print('zapisz-mt2009 "opis zmian"')
    print('Zapis lokalny:',WORK)
    print('Prywatne ustawienia:',PRIVATE)
except Exception as exc:
    print('\nSTOP:',exc)
    print('Zachowany katalog:',WORK)
    print('Nie usuwaj go; na jego podstawie mozna dokonczyc zapis.')
    raise SystemExit(1)
