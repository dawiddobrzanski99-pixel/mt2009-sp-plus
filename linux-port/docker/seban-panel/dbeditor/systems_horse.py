"""Horse stage of the systems editor. No automatic deploy, build or client publication."""
import contextlib
import fcntl
import grp
import hashlib
import io
import json
import os
import time
import uuid
import zipfile
from pathlib import Path
from flask import abort, flash, redirect, render_template, request, send_file, url_for, jsonify
from dbeditor import common_items as common
from m2clientpack import horse_editor as horse
from m2clientpack import horse_publication as publication


def atomic(path, raw):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o2770)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('xb') as f:
            os.chmod(temp,0o660);f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()


class Store:
    def __init__(self, root, plan=None):
        self.root=Path(root)
        self.plan=Path(plan or '/opt/metin2/var/boot-plan')
    @contextlib.contextmanager
    def locked(self):
        for directory in (self.root,self.root/'status',self.root/'assets'):
            directory.mkdir(parents=True,exist_ok=True,mode=0o2770)
            if (directory.stat().st_mode&0o2777)!=0o2770:
                os.chmod(directory,0o2770)
            try:gid=grp.getgrnam('m2spool').gr_gid
            except KeyError:gid=directory.stat().st_gid
            if directory.stat().st_gid!=gid:os.chown(directory,-1,gid)
        with (self.root/'editor.lock').open('a') as lock:
            os.chmod(self.root/'editor.lock',0o660)
            fcntl.flock(lock,fcntl.LOCK_EX)
            yield
    def read(self):
        path=self.root/'draft.json'
        return horse.validate(json.loads(path.read_bytes())) if path.exists() else horse.defaults()
    def topology(self):
        raw=self.plan.read_bytes()
        ports={}
        for line in raw.decode('utf-8').splitlines():
            parts=line.split('|')
            if len(parts)!=5:raise ValueError('Nieprawidłowy plan rdzeni.')
            name,directory,binary,port,kind=parts
            if kind!='game':continue
            port=int(port)
            if not 1<=port<=65535 or port in ports:raise ValueError('Konflikt identyfikatorów rdzeni.')
            ports[port]=name
        if not ports:raise ValueError('Brak rdzeni gry w planie uruchomienia.')
        return ports,hashlib.sha256(raw).hexdigest()
    def heartbeat(self,port):
        try:
            path=self.root/'status'/('%d.json'%port)
            if path.stat().st_size>4096:return None
            value=json.loads(path.read_bytes())
            if value.get('schema')!=horse.SCHEMA or value.get('port')!=port:return None
            if value.get('state') not in ('ready','applying','applied','error'):return None
            if any(type(value.get(k)) is not int for k in ('processed','total')):return None
            if not 0<=value['processed']<=value['total']:return None
            if not -5<=time.time()-float(value['updated'])<=15:return None
            import re
            if not re.fullmatch('[a-f0-9]{64}',str(value.get('instance',''))):return None
            return value
        except (OSError,ValueError,TypeError,KeyError):return None
    def _save(self,config,expected):
        current=self.read()
        if horse.revision(current)!=expected:raise ValueError('Konflikt: inna sesja zmieniła konfigurację. Odśwież stronę.')
        config=horse.validate(config)
        if horse.revision(config)==expected:
            if not (self.root/'draft.json').exists():atomic(self.root/'draft.json',horse.canonical(config))
            return
        atomic(self.root/'history'/(str(time.time_ns())+'.json'),horse.canonical(current))
        atomic(self.root/'draft.json',horse.canonical(config))
    def save(self,config,expected):
        with self.locked():self._save(config,expected)
    def _apply(self,config):
        ports,plan_hash=self.topology()
        missing=[name for port,name in ports.items() if self.heartbeat(port) is None]
        # MT2009_NASZE_KANALY_OFFLINE_V1: rdzen, ktory nie dziala, wezmie ustawienia przy starcie z request.txt.
        if len(missing)==len(ports):raise ValueError('Gra nie działa – żaden kanał nie odpowiada: '+', '.join(missing))
        if not (self.root/'draft.json').exists():atomic(self.root/'draft.json',horse.canonical(config))
        operation=uuid.uuid4().hex
        meta=dict(operation=operation,engine_revision=horse.engine_revision(config),config_revision=horse.revision(config),
                  client_revision=horse.client_revision(config),expected={str(p):n for p,n in ports.items()},plan_sha256=plan_hash,created=time.time(),offline=missing)
        # The single atomic request contains the complete SHA256-validated table.
        # A metadata-only or draft-only write can never change live bonuses.
        atomic(self.root/'operations'/(operation+'.json'),json.dumps(meta).encode())
        atomic(self.root/'last-request.json',json.dumps(meta).encode())
        if self.topology()[1]!=plan_hash:raise ValueError('Plan rdzeni zmienił się podczas operacji.')
        atomic(self.root/'request.txt',horse.command(config,operation))
        return operation
    def apply(self,expected,queue=None):
        with self.locked():
            config=self.read()
            if horse.revision(config)!=expected:raise ValueError('Konflikt wersji konfiguracji.')
            return self._apply(config)
    def save_apply(self,config,expected):
        with self.locked():
            self._save(config,expected)
            try:return self._apply(config)
            except ValueError as exc:raise ValueError('Konfiguracja zapisana. Nie zastosowano w grze: '+str(exc)) from exc
    def publish(self,config_revision,expected_publication,meta):
        with self.locked():
            config=self.read()
            if horse.revision(config)!=config_revision or meta.get('config_revision')!=config_revision or meta.get('client_revision')!=horse.client_revision(config):raise ValueError('Konfiguracja zmieniła się podczas eksportu. Wydanie nie zostało opublikowane.')
            publication.verify_prepared(self.root,meta)
            if publication.token(self.root)!=expected_publication:raise ValueError('Inna sesja opublikowała nowszą paczkę. Nie nadpisano publikacji.')
            current=self.root/'last-client-publication.json'
            if current.exists():atomic(self.root/'publication-history'/(str(time.time_ns())+'.json'),current.read_bytes())
            raw=json.dumps(meta,ensure_ascii=False,sort_keys=True).encode('utf-8')
            atomic(self.root/'publications'/(meta['release']+'.json'),raw)
            atomic(current,raw)

    def status(self):
        result=dict(state='not_requested',cores=[],client_required=False,operation=None)
        try:
            ports,plan_hash=self.topology()
            path=self.root/'last-request.json'
            meta=json.loads(path.read_bytes()) if path.exists() else None
            result['operation']=meta.get('operation') if meta else None
            if meta:
                expected={str(p):n for p,n in ports.items()}
                if meta.get('expected')!=expected or meta.get('plan_sha256')!=plan_hash:
                    result['state']='topology_changed'
                else:result['state']='waiting'
                command_path=self.root/'request.txt'
                if not command_path.exists() or not command_path.read_bytes().startswith(('SEBAN_HORSE_REQUEST_V2 '+meta['operation']+'\n').encode()):
                    result['state']='not_published'
            all_applied=bool(meta)
            any_error=False
            for port,name in ports.items():
                ack=self.heartbeat(port)
                state='missing' if ack is None else 'ready'
                if ack is None and meta and name in (meta.get('offline') or []):
                    result['cores'].append(dict(port=port,name=name,state='offline'));continue  # MT2009_NASZE_KANALY_OFFLINE_V1 (status)
                if meta and ack:
                    if ack.get('state')=='error':state='error';any_error=True
                    elif ack.get('operation')==meta['operation'] and ack.get('revision')==meta['engine_revision']:
                        state='applied' if ack.get('state')=='applied' and ack.get('processed')==ack.get('total') else 'applying'
                    else:state='waiting'
                all_applied=all_applied and state=='applied'
                result['cores'].append(dict(port=port,name=name,state=state,details=ack))
            if result['state']=='waiting':result['state']='error' if any_error else 'applied' if all_applied else 'waiting'
            publication=self.root/'last-client-publication.json'
            published=json.loads(publication.read_bytes()) if publication.exists() else {}
            result['client_required']=published.get('client_revision')!=horse.client_revision(self.read())
            result['engine_revision']=meta.get('engine_revision') if meta else None
            result['draft_pending']=not meta or meta.get('config_revision')!=horse.revision(self.read())
            result['client_publication']=published
        except (OSError,ValueError,KeyError,TypeError) as exc:
            result['state']='unavailable';result['error']=str(exc)
        return result


def parse_form(store):
    cfg=store.read()
    cfg['master_enabled']=request.form.get('master_enabled')=='1'
    cfg['enabled']=request.form.get('enabled')=='1'
    cfg['client_enabled']=request.form.get('client_enabled')=='1'
    for row in cfg['levels'][1:]:
        n=row['level'];row['name']=request.form['name_%d'%n];row['color']=request.form['color_%d'%n]
        keys=request.form.getlist('bonus_key_%d'%n);values=request.form.getlist('bonus_value_%d'%n)
        allowed=horse.extra_points()  # MT2009_NASZE_BONUSY_WSZYSTKIE_V1
        if n==1: cfg['extra']={}
        known=lambda k: k in horse.KEYS or (k[:1]=='p' and k[1:].isdigit() and int(k[1:]) in allowed)
        if len(keys)!=len(values) or len(set(keys))!=len(keys) or not all(known(k) for k in keys):
            raise ValueError('Nieprawidłowa lub powtórzona pozycja bonusu.')
        row['bonuses']={k:0 for k in horse.KEYS}
        for k,v in zip(keys,values):
            if k in horse.KEYS: row['bonuses'][k]=int(v)
            elif int(v): cfg['extra'].setdefault(str(n),{})[k[1:]]=int(v)
        image=request.files.get('icon_%d'%n)
        if image and image.filename:
            raw=image.read(263000);path=horse.validate_tga(raw)
            atomic(store.root/'assets'/Path(path).name,raw);row['icon']=path
        elif request.form.get('clear_icon_%d'%n)=='1':row['icon']=''
    return horse.validate(cfg)


def _kuznia_report():
    """MT2009_NASZE_KUZNIA_DODATKI_V1: co instalator dolozyl / pominal w ROOT tego klienta."""
    from m2clientpack import kuznia_dodatki
    rep=kuznia_dodatki.LAST_REPORT
    skipped=[r for r in rep if r.startswith('pominięto') or r.startswith('brak ')]
    done=[r for r in rep if r not in skipped]
    if done:flash('Kuźnia dołożyła do ROOT: '+'; '.join(done),'info')
    if skipped:flash('Kuźnia POMINĘŁA (inna wersja klienta): '+'; '.join(skipped),'warning')


def install(bp,ctx):
    store=Store(Path(ctx['spool'])/'systems/horse',ctx.get('boot_plan'))
    login=ctx['login_required']
    def view_status():
        result=store.status()
        publisher=ctx.get('dbdata_publisher')
        published=result.get('client_publication') or {}
        if published and publisher:
            try:
                if publisher.current_stamp()!=published.get('stamp'):
                    result['client_required']=True
                    result['client_reason']='Zmienił się znacznik dbdata serwera.'
            except Exception:
                result['client_required']=True
                result['client_reason']='Nie potwierdzono bieżącego znacznika dbdata.'
        return result
    @bp.route('/systemy/kon',methods=['GET','POST'])
    @login
    def systems_horse():
        if request.content_length and request.content_length>4*1024*1024:abort(413)
        if request.method=='POST':
            if not common.check_csrf():abort(403)
            try:
                expected=request.form.get('revision','')
                action=request.form.get('action')
                if action=='apply':
                    store.apply(expected)
                    flash('Przekazano konfigurację. Czekamy na potwierdzenia wszystkich rdzeni; bez restartu.','info')
                elif action in ('save','save_apply'):
                    cfg=parse_form(store)
                    if action=='save_apply':
                        store.save_apply(cfg,expected)
                        flash('Zapisano konfigurację i przekazano do rdzeni. Trwa oczekiwanie na przeliczenie wszystkich kanałów.','info')
                    else:
                        store.save(cfg,expected)
                        flash('Zapisano projekt. Serwer jeszcze go nie zastosował.','info')
                elif action=='undo':
                    with store.locked():
                        if horse.revision(store.read())!=expected:raise ValueError('Konflikt wersji.')
                        histories=sorted((store.root/'history').glob('[0-9]*.json'))
                        if not histories:raise ValueError('Brak wcześniejszej konfiguracji.')
                        wanted=horse.validate(json.loads(histories[-1].read_bytes()))
                    store.save(wanted,expected)
                    flash('Przywrócono poprzedni projekt. Zastosowanie w grze wymaga osobnego przycisku.','success')
                else:abort(400)
            except (ValueError,KeyError,UnicodeError) as exc:flash(str(exc),'error')
            except Exception:
                ctx['app'].logger.exception('Horse editor operation failed')
                flash('Operacja nie została potwierdzona. Sprawdź diagnostykę panelu.','error')
            return redirect(url_for('dbeditor.systems_horse'))
        with store.locked():
            cfg=store.read()
        cfg=horse.validate(cfg)
        extra_opts=[(('p%d'%p),n+(' (%s)'%u.replace('‰','‰ = 1/10 %') if u else ''),horse.EXTRA_LIMIT) for p,(n,u) in sorted(horse.extra_points().items(),key=lambda x:x[1][0])]
        bonus_init={r['level']:[[k,r['bonuses'][k]] for k in horse.KEYS if r['bonuses'][k]]+[['p'+p,v] for p,v in sorted(cfg.get('extra',{}).get(str(r['level']),{}).items(),key=lambda x:int(x[0]))] for r in cfg['levels']}
        return render_template('dbeditor/systems_horse.html',config=cfg,revision=horse.revision(cfg),keys=list(zip(horse.KEYS,horse.LABELS,horse.LIMITS)),extra_opts=extra_opts,bonus_init=bonus_init,status=view_status(),publication_revision=publication.token(store.root),dbe_csrf=common.csrf_token())

    @bp.route('/systemy/kon/status')
    @login
    def systems_horse_status():
        return jsonify(view_status())

    @bp.route('/systemy/kon/paczka',methods=['POST'])
    @login
    def systems_horse_pack():
        if request.content_length and request.content_length>850*1024*1024:abort(413)
        if not common.check_csrf():abort(403)
        try:
            with store.locked():
                cfg=store.read()
                if request.form.get('revision')!=horse.revision(cfg):raise ValueError('Konflikt wersji formularza.')
                assets={r['icon']:(store.root/'assets'/Path(r['icon']).name).read_bytes() for r in cfg['levels'] if r['icon']}
            index=request.files['root_index'].read(32*1024*1024+1)
            data=request.files['root_data'].read(256*1024*1024+1)
            if request.form.get('action')=='publish':
                game_index=request.files['gamedata_index'].read(32*1024*1024+1)
                game_data=request.files['gamedata_data'].read(512*1024*1024+1)
                if not game_index or not game_data:raise ValueError('Do pełnego wydania wymagana jest własna kompletna para gamedata.')
                from m2clientpack import kuznia_dodatki as _kd; game_index,game_data,_gr=_kd.patch_gamedata(game_index,game_data)  # MT2009_NASZE_INNE_IKONY_V1
                publisher=ctx.get('dbdata_publisher')
                folder,meta=publication.build(store.root,cfg,index,data,game_index,game_data,publisher,assets)
                try:
                    if publisher.current_stamp()!=meta['stamp']:raise ValueError('Znacznik serwera zmienił się przed publikacją.')
                    store.publish(horse.revision(cfg),request.form.get('publication_revision',''),meta)
                except BaseException:
                    # Keep the prepared edition for diagnostics; its receipt/pointer is not published.
                    raise
                flash('Opublikowano i zweryfikowano pełny ZIP oraz zgodne pary. Klient wymaga pobrania i podmiany plików; test w grze pozostaje osobnym krokiem.','success')
                _kuznia_report()
                return redirect(url_for('dbeditor.systems_index'))
            result_index,result_data,changes=horse.patch_pack(index,data,cfg,assets)
            gd=None  # MT2009_NASZE_INNE_IKONY_V1: gamedata (opcjonalnie) - ikony Skrzyni z KU i Klepsydry
            _gi=request.files.get('gamedata_index');_gdd=request.files.get('gamedata_data')
            if _gi and _gdd and _gi.filename and _gdd.filename:
                from m2clientpack import kuznia_dodatki as _kd
                gd=_kd.patch_gamedata(_gi.read(32*1024*1024+1),_gdd.read(512*1024*1024+1))
                for _line in gd[2]:flash('gamedata: '+_line,'info')
            _kuznia_report()
            manifest=dict(schema=horse.SCHEMA,config_revision=horse.revision(cfg),changes=changes,
                          before={'root.index':hashlib.sha256(index).hexdigest(),'root.data':hashlib.sha256(data).hexdigest()},
                          after={'root.index':hashlib.sha256(result_index).hexdigest(),'root.data':hashlib.sha256(result_data).hexdigest()})
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
                # MT2009_NASZE_ROOT_ZIP_PROSTY_V1: tylko to, co trzeba wgrac do klienta.
                z.writestr('pack/root.index',result_index);z.writestr('pack/root.data',result_data)
                if gd:z.writestr('pack/gamedata.index',gd[0]);z.writestr('pack/gamedata.data',gd[1])  # MT2009_NASZE_INNE_IKONY_V1
                z.writestr('CZYTAJ.txt','Zamknij gre. Zrob kopie swoich plikow pack/root.index i pack/root.data,\r\npotem skopiuj oba pliki z folderu pack tej paczki do folderu pack klienta (oba naraz).\r\n')
            stream.seek(0)
            return send_file(stream,as_attachment=True,download_name='kuznia-root-'+horse.revision(cfg)[:12]+'.zip',mimetype='application/zip',max_age=0)
        except (ValueError,KeyError,OSError,RuntimeError,zipfile.BadZipFile) as exc:
            flash('Nie przygotowano paczki: '+str(exc),'error')
            return redirect(url_for('dbeditor.systems_index'))
    @bp.route('/systemy/kon/grafika/<name>')
    @login
    def systems_horse_asset(name):
        import re
        if not re.fullmatch(r'[0-9a-f]{64}\.tga',name):abort(404)
        try:
            path=store.root/'assets'/name
            if path.is_symlink():abort(404)
            raw=path.read_bytes()
            if horse.validate_tga(raw)!=horse.ICON_PREFIX+name:abort(404)
            return send_file(io.BytesIO(raw),mimetype='image/x-tga',max_age=0)
        except (OSError,ValueError):abort(404)

    @bp.route('/systemy/kon/wydanie/<release>/<filename>')
    @login
    def systems_horse_download(release,filename):
        try:
            path=publication.verified_file(store.root,release,filename)
            response=send_file(path,as_attachment=True,download_name=filename,conditional=True,max_age=0)
            response.headers['Cache-Control']='no-store'
            return response
        except (ValueError,OSError,KeyError,zipfile.BadZipFile):abort(404)
    import dbeditor
    dbeditor.add_section('dbeditor.systems_horse','🐎','Systemy — koń','bonusy 1–30, przełączniki, nazwy, kolory i grafiki; paczka na podstawie Twojego ROOT')
