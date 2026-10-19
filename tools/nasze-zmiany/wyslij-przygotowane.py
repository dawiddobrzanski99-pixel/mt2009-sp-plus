from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import signal
import subprocess
import sys

os.umask(0o077)
base = Path(__file__).resolve().parent
work = Path(sys.argv[1]).resolve()
candidate = work / 'do-repo'
repo = base / 'repo'
scanner = base / 'narzedzia/gitleaks-8.24.2/gitleaks'
anchor = '8e4763076a4f90a1d70a8f76f7e89281b3af810f'
state_file = work / 'wynik-wyslania.json'

if not candidate.is_dir() or not scanner.is_file():
    raise SystemExit('STOP: brak przygotowanego zestawu lub skanera.')

env = dict(os.environ)
env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
env['GIT_INDEX_FILE'] = str(work / ('indeks-wyslania-' + stamp))

def git(*args, allow=(0,), timeout=60):
    process = subprocess.Popen(
        ['git', '--git-dir', str(repo / '.git'),
         '--work-tree', str(candidate), *args],
        cwd=candidate, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
    if timed_out or process.returncode not in allow:
        log = work / ('git-blad-' + stamp + '.txt')
        log.write_bytes(stderr)
        print('Operacja:', args[0])
        print('Diagnostyka:', log)
        print('\n'.join(stderr.decode('utf-8', 'replace').splitlines()[-12:]))
        raise SystemExit(
            'STOP: przekroczony czas.' if timed_out else 'STOP: blad Git.'
        )
    return process.returncode, stdout

def output(*args, **kwargs):
    return git(*args, **kwargs)[1]

# Ten skrypt jest przeznaczony do konkretnego przygotowanego zestawu.
files = sorted(p for p in candidate.rglob('*') if p.is_file())
names = []
digest = hashlib.sha256()
for path in files:
    if path.is_symlink():
        raise SystemExit('STOP: dowiazanie w zestawie.')
    name = path.relative_to(candidate).as_posix()
    if (
        path.name.lower() in
        {'.env', 'metin2-accounts.txt', 'mt2009_private_protocol_keys.h'}
        or path.name.lower().startswith(('id_ed25519', 'id_rsa'))
        or path.suffix.lower() in {'.pem', '.key'}
    ):
        raise SystemExit('STOP: niedozwolony plik: ' + name)
    if path.stat().st_size >= 95 * 1024 * 1024:
        raise SystemExit('STOP: za duzy pojedynczy plik: ' + name)
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    digest.update(name.encode('utf-8') + b'\0' + h.digest())
    names.append(name)
snapshot_hash = digest.hexdigest()

if state_file.is_file():
    previous = json.loads(state_file.read_text(encoding='utf-8'))
    if previous.get('snapshot_sha256') != snapshot_hash:
        raise SystemExit('STOP: zestaw zmienil sie od poprzedniej proby.')
    if previous.get('pushed'):
        print('Ten zestaw zostal juz wyslany.')
        print('Link:', previous['url'])
        raise SystemExit(0)
else:
    previous = None

print('Sprawdzanie zestawu...', flush=True)
native = 'customizations/server-source-snapshot/docker/game/src/server/game/src/'
expected = {
    ('customizations/client-packs/root/uiquestbonuspreview.py', 103),
    (native + 'playerbot_minigames.h', 140),
    (native + 'playerbot_minigames.h', 473),
    (native + 'text_file_loader.cpp', 436),
    (native + 'text_file_loader.h', 57)
}
report = work / ('kontrola-przed-push-' + stamp + '.json')
with (work / ('kontrola-przed-push-' + stamp + '.log')).open('wb') as log:
    scan = subprocess.run(
        [str(scanner), 'dir', str(candidate), '--no-banner', '--redact=100',
         '--report-format', 'json', '--report-path', str(report),
         '--log-level', 'error'],
        stdin=subprocess.DEVNULL, stdout=log, stderr=log, timeout=240
    )
if scan.returncode not in (0, 1) or not report.is_file():
    raise SystemExit('STOP: skan nie zakonczyl sie poprawnie.')
hits = json.loads(report.read_text(encoding='utf-8'))
found = set()
for hit in hits:
    path = Path(hit['File'])
    if not path.is_absolute():
        path = candidate / path
    relative = path.resolve().relative_to(candidate.resolve()).as_posix()
    item = (relative, int(hit['StartLine']))
    if hit.get('RuleID') != 'generic-api-key' or item not in expected:
        raise SystemExit('STOP: nowe trafienie do przegladu: ' + relative)
    found.add(item)
if found != expected or len(hits) != 5:
    raise SystemExit('STOP: wynik skanu rozni sie od przejrzanego zestawu.')

print('Pobieranie metadanych main przez skonfigurowane SSH 443...', flush=True)
git('fetch', '--filter=blob:none', '--no-tags', '--no-recurse-submodules',
    '--no-auto-maintenance', 'origin', 'refs/heads/main', timeout=60)
parent = output('rev-parse', 'FETCH_HEAD').decode().strip()

if previous:
    if parent == previous['commit']:
        previous['pushed'] = True
        state_file.write_text(json.dumps(previous, indent=2), encoding='utf-8')
        print('Potwierdzono zapis na main.')
        print('Link:', previous['url'])
        raise SystemExit(0)
    if parent != previous['parent']:
        raise SystemExit('STOP: main zmienilo sie od poprzedniej proby.')
    state = previous
else:
    rc, _ = git('merge-base', '--is-ancestor', anchor, parent, allow=(0, 1))
    if rc:
        raise SystemExit('STOP: potrzebny przeglad zmienionej historii main.')
    if parent != anchor:
        remote_paths = {
            p.decode('utf-8') for p in output(
                'diff', '--no-renames', '--name-only', '-z', anchor, parent
            ).split(b'\0') if p
        }
        conflicts = sorted(remote_paths.intersection(names))
        if conflicts:
            print('\n'.join(conflicts[:30]))
            raise SystemExit('STOP: kolizja ze zmianami na main.')

    modes = {}
    for entry in output('ls-tree', '-r', '-z', parent).split(b'\0'):
        if entry:
            meta, name = entry.split(b'\t', 1)
            modes[name.decode('utf-8')] = meta.split()[0]
    for path, name in zip(files, names):
        if modes.get(name) == b'100755':
            path.chmod(0o700)

    git('read-tree', parent)
    paths = work / ('sciezki-' + stamp + '.nul')
    paths.write_bytes(b''.join(n.encode('utf-8') + b'\0' for n in names))
    git('--literal-pathspecs', 'add',
        '--pathspec-from-file=' + str(paths), '--pathspec-file-nul',
        timeout=120)

    deleted = output('diff-index', '--cached', '--no-renames',
                     '--diff-filter=D', '--name-only', '-z', parent)
    if deleted:
        raise SystemExit('STOP: nieoczekiwane usuniecia.')
    changed = {
        p.decode('utf-8') for p in output(
            'diff-index', '--cached', '--no-renames',
            '--name-only', '-z', parent
        ).split(b'\0') if p
    }
    if not changed:
        raise SystemExit('Brak nowych zmian do commita.')
    if not changed.issubset(set(names)):
        raise SystemExit('STOP: pliki spoza sprawdzonego zestawu.')

    tree = output('write-tree').decode().strip()
    body = work / ('opis-' + stamp + '.txt')
    body.write_text(
        'Preserve VPS custom sources, client assets and recovery instructions\n\n'
        'Save reviewed sources, readable client packs and recovery documentation.\n'
        'Keep private protocol constants outside Git.\n'
        'Document remaining recovery gaps in STAN-ZAPISU.md.\n',
        encoding='utf-8'
    )
    author = output('config', 'user.name', allow=(0, 1)).decode().strip()
    email = output('config', 'user.email', allow=(0, 1)).decode().strip()
    commit = output(
        '-c', 'user.name=' + (author or 'MT2009 VPS archive'),
        '-c', 'user.email=' + (email or 'mt2009-vps@localhost'),
        'commit-tree', tree, '-p', parent, '-F', str(body)
    ).decode().strip()
    branch = 'refs/heads/zapis-vps-' + stamp
    git('update-ref', branch, commit, '')
    state = {
        'commit': commit, 'parent': parent, 'branch': branch,
        'target': 'main', 'changed_files': len(changed),
        'snapshot_sha256': snapshot_hash, 'pushed': False,
        'url': 'https://github.com/dawiddobrzanski99-pixel/mt2009-sp-plus/commit/' + commit
    }
    state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

print('Commit lokalny:', state['commit'], flush=True)
print('Wysylanie okolo 109 MB plikow przed kompresja. Bez force push...', flush=True)
git('push', 'origin', state['branch'] + ':refs/heads/main', timeout=240)
state['pushed'] = True
state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

print('\n=== ZAPIS NA GITHUB ZAKONCZONY ===')
print('Galaz: main')
print('Pliki dodane lub zmienione:', state['changed_files'])
print('Commit:', state['commit'])
print('Link:', state['url'])
print('Wynik:', state_file)
print('Braki pozostaja opisane w docs/nasze-zmiany/STAN-ZAPISU.md.')
print('Nie zmieniono dzialajacej gry, bazy ani paczek panelu.')
