"""MT2009_NASZE_SYSTEMY_V1: wspolny magazyn konfiguracji systemow (wzor: kon V2).

Projekt (draft.json) + historia; "zastosuj" zapisuje jeden atomowy request.txt
z cala tabela i suma SHA256; kazdy rdzen gry potwierdza status/<port>.json.
Kodek systemu (codec) dostarcza: SCHEMA, REQUEST_MAGIC, defaults, validate,
canonical, revision, engine_revision, command.
"""
import contextlib
import fcntl
import grp
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path


def atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o2770)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as f:
            os.chmod(temp, 0o660); f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists(): temp.unlink()


class SystemStore:
    def __init__(self, root, codec, plan=None):
        self.root = Path(root); self.codec = codec
        self.plan = Path(plan or '/opt/metin2/var/boot-plan')

    @contextlib.contextmanager
    def locked(self):
        for directory in (self.root, self.root / 'status'):
            directory.mkdir(parents=True, exist_ok=True, mode=0o2770)
            if (directory.stat().st_mode & 0o2777) != 0o2770: os.chmod(directory, 0o2770)
            try: gid = grp.getgrnam('m2spool').gr_gid
            except KeyError: gid = directory.stat().st_gid
            if directory.stat().st_gid != gid: os.chown(directory, -1, gid)
        with (self.root / 'editor.lock').open('a') as lock:
            os.chmod(self.root / 'editor.lock', 0o660)
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def read(self):
        path = self.root / 'draft.json'
        return self.codec.validate(json.loads(path.read_bytes())) if path.exists() else self.codec.defaults()

    def topology(self):
        raw = self.plan.read_bytes(); ports = {}
        for line in raw.decode('utf-8').splitlines():
            parts = line.split('|')
            if len(parts) != 5: raise ValueError('Nieprawidłowy plan rdzeni.')
            name, directory, binary, port, kind = parts
            if kind != 'game': continue
            port = int(port)
            if not 1 <= port <= 65535 or port in ports: raise ValueError('Konflikt identyfikatorów rdzeni.')
            ports[port] = name
        if not ports: raise ValueError('Brak rdzeni gry w planie uruchomienia.')
        return ports, hashlib.sha256(raw).hexdigest()

    def heartbeat(self, port):
        try:
            path = self.root / 'status' / ('%d.json' % port)
            if path.stat().st_size > 4096: return None
            value = json.loads(path.read_bytes())
            if value.get('schema') != self.codec.SCHEMA or value.get('port') != port: return None
            if value.get('state') not in ('ready', 'applying', 'applied', 'error'): return None
            if any(type(value.get(k)) is not int for k in ('processed', 'total')): return None
            if not 0 <= value['processed'] <= value['total']: return None
            if not -5 <= time.time() - float(value['updated']) <= 15: return None
            if not re.fullmatch('[a-f0-9]{64}', str(value.get('instance', ''))): return None
            return value
        except (OSError, ValueError, TypeError, KeyError): return None

    def _save(self, config, expected):
        c = self.codec; current = self.read()
        if c.revision(current) != expected: raise ValueError('Konflikt: inna sesja zmieniła konfigurację. Odśwież stronę.')
        config = c.validate(config)
        if c.revision(config) == expected:
            if not (self.root / 'draft.json').exists(): atomic(self.root / 'draft.json', c.canonical(config))
            return
        atomic(self.root / 'history' / (str(time.time_ns()) + '.json'), c.canonical(current))
        atomic(self.root / 'draft.json', c.canonical(config))

    def save(self, config, expected):
        with self.locked(): self._save(config, expected)

    def _apply(self, config):
        c = self.codec; ports, plan_hash = self.topology()
        missing = [name for port, name in ports.items() if self.heartbeat(port) is None]
        # MT2009_NASZE_KANALY_OFFLINE_V1: rdzen, ktory nie dziala (np. kanal wylaczony), wezmie ustawienia przy starcie z request.txt.
        if len(missing) == len(ports): raise ValueError('Gra nie działa – żaden kanał nie odpowiada: ' + ', '.join(missing))
        if not (self.root / 'draft.json').exists(): atomic(self.root / 'draft.json', c.canonical(config))
        operation = uuid.uuid4().hex
        meta = dict(operation=operation, engine_revision=c.engine_revision(config), config_revision=c.revision(config),
                    expected={str(p): n for p, n in ports.items()}, plan_sha256=plan_hash, created=time.time(),
                    offline=missing)  # MT2009_NASZE_KANALY_OFFLINE_V1
        atomic(self.root / 'operations' / (operation + '.json'), json.dumps(meta).encode())
        atomic(self.root / 'last-request.json', json.dumps(meta).encode())
        if self.topology()[1] != plan_hash: raise ValueError('Plan rdzeni zmienił się podczas operacji.')
        atomic(self.root / 'request.txt', c.command(config, operation))
        return operation

    def apply(self, expected):
        with self.locked():
            config = self.read()
            if self.codec.revision(config) != expected: raise ValueError('Konflikt wersji konfiguracji.')
            return self._apply(config)

    def save_apply(self, config, expected):
        with self.locked():
            self._save(config, expected)
            try: return self._apply(config)
            except ValueError as exc: raise ValueError('Konfiguracja zapisana. Nie zastosowano w grze: ' + str(exc)) from exc

    def undo(self, expected):
        with self.locked():
            if self.codec.revision(self.read()) != expected: raise ValueError('Konflikt wersji.')
            histories = sorted((self.root / 'history').glob('[0-9]*.json'))
            if not histories: raise ValueError('Brak wcześniejszej konfiguracji.')
            wanted = self.codec.validate(json.loads(histories[-1].read_bytes()))
            self._save(wanted, expected)

    def status(self):
        result = dict(state='not_requested', cores=[], operation=None)
        try:
            ports, plan_hash = self.topology()
            path = self.root / 'last-request.json'
            meta = json.loads(path.read_bytes()) if path.exists() else None
            result['operation'] = meta.get('operation') if meta else None
            if meta:
                expected = {str(p): n for p, n in ports.items()}
                result['state'] = 'topology_changed' if (meta.get('expected') != expected or meta.get('plan_sha256') != plan_hash) else 'waiting'
                command_path = self.root / 'request.txt'
                if not command_path.exists() or not command_path.read_bytes().startswith((self.codec.REQUEST_MAGIC + ' ' + meta['operation'] + '\n').encode()):
                    result['state'] = 'not_published'
            all_applied = bool(meta); any_error = False
            for port, name in ports.items():
                ack = self.heartbeat(port)
                state = 'missing' if ack is None else 'ready'
                if ack is None and meta and name in (meta.get('offline') or []):
                    result['cores'].append(dict(port=port, name=name, state='offline')); continue  # MT2009_NASZE_KANALY_OFFLINE_V1
                if meta and ack:
                    if ack.get('state') == 'error': state = 'error'; any_error = True
                    elif ack.get('operation') == meta['operation'] and ack.get('revision') == meta['engine_revision']:
                        state = 'applied' if ack.get('state') == 'applied' and ack.get('processed') == ack.get('total') else 'applying'
                    else: state = 'waiting'
                all_applied = all_applied and state == 'applied'
                result['cores'].append(dict(port=port, name=name, state=state))
            if result['state'] == 'waiting': result['state'] = 'error' if any_error else 'applied' if all_applied else 'waiting'
            result['draft_pending'] = not meta or meta.get('config_revision') != self.codec.revision(self.read())
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result['state'] = 'unavailable'; result['error'] = str(exc)
        return result
