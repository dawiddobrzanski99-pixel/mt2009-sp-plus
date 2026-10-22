"""MT2009_NASZE_KOPIA_V1: Kuznia Mocy -> Kopia ustawien (eksport / import).

Eksport: jeden ZIP z ustawieniami wszystkich systemow (draft.json) i ich grafikami (odznaki rang, ikony konia,
grafika okna Ctrl+N), ustawieniami Slawy i punktem odniesienia skanu.
Import (np. po aktualizacji serwera i ponownej instalacji): baza jest czytana od nowa - etapy misji z potworami
i nagrody z przedmiotami, ktorych nowy serwer nie ma, sa pomijane i wypisane w raporcie; reszta wraca
i jest stosowana na serwerze (bez restartu)."""
import io
import json
import time
import zipfile
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, abort, send_file
from dbeditor import common_items as common
from dbeditor.systems_store import SystemStore, atomic

SCHEMA = 'KUZNIA_MOCY_KOPIA_V1'
SYSTEMS = [('horse', 'Koń'), ('polimorfia', 'Polimorfia'), ('gildia', 'Gildia'), ('rangi', 'Rangi'),
           ('ranking', 'Ranking tygodnia'), ('misje', 'Misje (Ctrl+N)')]
EXTRA_FILES = [('plus9', 'config.txt'), ('skan', 'ostatni.json')]
# Ustawienia autora Kuzni dolaczone przez instalator (kopia jego serwera); brak pliku = karta ukryta.
AUTHOR_ZIP = Path(__file__).resolve().parent.parent / 'm2clientpack' / 'kuznia_dodatki' / 'ustawienia-autora.zip'


def codec_of(key):
    if key == 'polimorfia':
        from dbeditor import systems_poly as m; return m.codec
    if key == 'gildia':
        from dbeditor import systems_guild as m; return m.codec
    if key == 'rangi':
        from dbeditor import systems_rank as m; return m.codec
    if key == 'ranking':
        from dbeditor import systems_weekly as m; return m.codec
    if key == 'misje':
        from dbeditor import systems_missions as m; return m.codec
    return None


# Postep graczy w player.quest: misje (Polowanie, Metinologia, Bossologia), nagrody, Biolog, Kolekcjoner.
PROGRESS_WHERE = "szName LIKE %s OR szName LIKE %s OR szName = %s"
PROGRESS_ARGS = ('custom\\_%', 'collect\\_quest%', 'kolekcje')


PLAYER_TABLES = ['mt2009_plus9_counters', 'mt2009_plus9_items', 'mt2009_plus9_people', 'mt2009_plus9_state',
                 'mt2009_rank_points', 'weekly_rank_score', 'weekly_rank_state', 'weekly_rank_title']


def cell(v):
    """Wartosc z bazy do JSON: bajty jako {"hex": ...}, daty jako tekst."""
    if isinstance(v, (bytes, bytearray)): return {'hex': bytes(v).hex()}
    if v is None or isinstance(v, (int, float, str)): return v
    return str(v)


def uncell(v):
    return bytes.fromhex(v['hex']) if isinstance(v, dict) and 'hex' in v else v


def text(v):
    if isinstance(v, (bytes, bytearray)):
        try: return bytes(v).decode('utf-8')
        except UnicodeDecodeError: return bytes(v).decode('latin-1')
    return '' if v is None else str(v)


def install(bp, ctx):
    spool = Path(ctx['spool']) / 'systems'
    login = ctx['login_required']

    def rows(sql, params=()):
        return common.ctx()['rows'](sql, params)

    def restore_tables(dumps, skipped):
        """Sława +9, rangi, ranking: INSERT IGNORE - dopisuje tylko brakujace wiersze, istniejacych nie zmienia."""
        have = {text(r['t']) for r in rows("SELECT table_name AS t FROM information_schema.tables WHERE table_schema = 'player'")}
        con = common._CTX['db'](); done = 0
        try:
            con.begin()
            with con.cursor() as cur:
                for table, data in dumps.items():
                    if table not in PLAYER_TABLES or not data: continue
                    if table not in have:
                        skipped.append('Dane graczy: tabeli %s nie ma na tym serwerze – pominięta' % table); continue
                    cols = list(data[0].keys())
                    cur.execute("SHOW COLUMNS FROM player.`%s`" % table)
                    known = {text(r[0] if isinstance(r, (list, tuple)) else r['Field']) for r in cur.fetchall()}
                    cols = [c for c in cols if c in known]
                    if not cols: continue
                    cur.executemany("INSERT IGNORE INTO player.`%s` (%s) VALUES (%s)" % (table, ', '.join('`%s`' % c for c in cols), ', '.join(['%s'] * len(cols))),
                                    [tuple(uncell(r.get(c)) for c in cols) for r in data])
                    done += len(data)
            con.commit()
        except Exception:
            con.rollback(); raise
        finally:
            try: con.close()
            except Exception: pass
        return 'Dane graczy (Sława +9, rangi, ranking): %d wierszy sprawdzonych, brakujące dopisane' % done

    def restore_progress(quest, chars, skipped):
        """Postep z kopii: tylko ta sama postac (numer + nick), wartosc nigdy mniejsza niz obecna."""
        now = {str(int(r['id'])): text(r['name']) for r in rows("SELECT id, name FROM player.player")}
        good = [q for q in quest if now.get(str(q[0])) is not None and now.get(str(q[0])) == chars.get(str(q[0]))]
        lost = len({q[0] for q in quest}) - len({q[0] for q in good})
        if lost: skipped.append('Postęp graczy: %d postaci z kopii nie ma na serwerze (albo mają inny nick) – pominięte' % lost)
        con = common._CTX['db']()
        try:
            con.begin()
            with con.cursor() as cur:
                cur.executemany("INSERT INTO player.quest (dwPID, szName, szState, lValue) VALUES (%s, %s, %s, %s) "
                                "ON DUPLICATE KEY UPDATE lValue = GREATEST(lValue, VALUES(lValue))",
                                [(int(a), b[:32], c[:64], int(d)) for a, b, c, d in good])
            con.commit()
        except Exception:
            con.rollback(); raise
        finally:
            try: con.close()
            except Exception: pass
        return 'Postęp graczy (%d wpisów, %d postaci) – najlepiej wgrywać, gdy nikt nie gra (gra zapisuje postęp zalogowanych postaci po swojemu)' % (len(good), len({q[0] for q in good}))

    @bp.route('/systemy/kopia', methods=['GET'])
    @login
    def systems_kopia():
        have = [(k, n, (spool / k / 'draft.json').exists()) for k, n in SYSTEMS]
        report = None
        p = spool / 'kopia-raport.json'
        if p.exists():
            try: report = json.loads(p.read_bytes())
            except ValueError: report = None
        author = None
        if AUTHOR_ZIP.is_file():
            try:
                with zipfile.ZipFile(AUTHOR_ZIP) as z:
                    meta = json.loads(z.read('kuznia-mocy.json'))
                    names = set(z.namelist())
                author = dict(created=meta.get('created', ''),
                              systems=[(k, n) for k, n in SYSTEMS if '%s/draft.json' % k in names] +
                                      ([('plus9', 'Sława')] if 'plus9/config.txt' in names else []))
            except (ValueError, KeyError, zipfile.BadZipFile, OSError):
                author = None
        return render_template('dbeditor/systems_backup.html', have=have, report=report, author=author, dbe_csrf=common.csrf_token(),
                               sys_active='kopia', system=None)

    @bp.route('/systemy/kopia/pobierz', methods=['POST'])
    @login
    def systems_kopia_export():
        if not common.check_csrf(): abort(403)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            meta = dict(schema=SCHEMA, created=time.strftime('%Y-%m-%d %H:%M:%S'), systems=[])
            for key, _name in SYSTEMS:
                d = spool / key
                if (d / 'draft.json').exists():
                    z.writestr('%s/draft.json' % key, (d / 'draft.json').read_bytes()); meta['systems'].append(key)
                if (d / 'assets').is_dir():
                    for f in sorted((d / 'assets').iterdir()):
                        if f.is_file() and f.suffix.lower() == '.tga' and f.stat().st_size <= 4 * 1024 * 1024:
                            z.writestr('%s/assets/%s' % (key, f.name), f.read_bytes())
            for key, name in EXTRA_FILES:
                if (spool / key / name).exists(): z.writestr('%s/%s' % (key, name), (spool / key / name).read_bytes())
            # MT2009_NASZE_KOLEKCJE_V1: Kolekcjoner; "Inne" - tylko ktore opcje byly wlaczone (do raportu).
            for key, name in (('kolekcje', 'dane.json'), ('inne', 'stan.json')):
                if (spool / key / name).exists(): z.writestr('%s/%s' % (key, name), (spool / key / name).read_bytes())
            for folder in ('okno/grafika', 'kolekcje/ikony'):  # wlasne grafiki okna Ctrl+N i ikony kategorii Kolekcjonera
                if (spool / folder).is_dir():
                    for f in sorted((spool / folder).glob('*.tga')):
                        if f.stat().st_size <= 8 * 1024 * 1024: z.writestr('%s/%s' % (folder, f.name), f.read_bytes())
            # MT2009_NASZE_KOPIA_POSTEPU_V1: postep graczy (misje, Biolog, Kolekcjoner, odebrane nagrody) + nicki postaci.
            try:
                quest = rows("SELECT dwPID, szName, szState, lValue FROM player.quest WHERE " + PROGRESS_WHERE, PROGRESS_ARGS)
                chars = rows("SELECT id, name FROM player.player")
                z.writestr('postep/quest.json', json.dumps([[int(r['dwPID']), text(r['szName']), text(r['szState']), int(r['lValue'])] for r in quest]))
                z.writestr('postep/postacie.json', json.dumps({str(int(r['id'])): text(r['name']) for r in chars}, ensure_ascii=False))
                meta['postep'] = len(quest)
            except Exception as exc:
                meta['postep_blad'] = str(exc)
            # Dane graczy systemow Kuzni w osobnych tabelach (Slawa +9, rangi, ranking tygodnia).
            have = {text(r['t']) for r in rows("SELECT table_name AS t FROM information_schema.tables WHERE table_schema = 'player'")}
            for table in PLAYER_TABLES:
                if table not in have: continue
                try:
                    data = rows("SELECT * FROM player.`%s`" % table)
                    z.writestr('postep/tabele/%s.json' % table, json.dumps([{k: cell(v) for k, v in r.items()} for r in data], ensure_ascii=False))
                    meta.setdefault('tabele', {})[table] = len(data)
                except Exception as exc:
                    meta.setdefault('tabele_bledy', {})[table] = str(exc)
            z.writestr('kuznia-mocy.json', json.dumps(meta, ensure_ascii=False, indent=2))
            z.writestr('CZYTAJ.txt', 'Kopia ustawien Kuzni Mocy. Wgraj ja w panelu: Kuznia Mocy -> Kopia ustawien -> Wgraj kopie.\n'
                                     'Nie rozpakowuj i nie zmieniaj plikow w srodku.\n')
        stream.seek(0)
        return send_file(stream, as_attachment=True, download_name='kuznia-mocy-kopia-%s.zip' % time.strftime('%Y%m%d-%H%M'),
                         mimetype='application/zip', max_age=0)

    @bp.route('/systemy/kopia/wgraj', methods=['POST'])
    @login
    def systems_kopia_import():
        if not common.check_csrf(): abort(403)
        f = request.files.get('kopia')
        return run_import(lambda: f.read(200 * 1024 * 1024 + 1) if f else b'', None, 'Wgrano kopię')

    # MT2009_NASZE_USTAWIENIA_AUTORA_V1: wybrane systemy z ustawien autora Kuzni (paczka instalatora);
    # niezaznaczone zostaja jak sa (swiezy start: puste bonusy, rangi z gry).
    @bp.route('/systemy/kopia/autor', methods=['POST'])
    @login
    def systems_kopia_author():
        if not common.check_csrf(): abort(403)
        only = set(request.form.getlist('systemy'))
        if not only:
            flash('Zaznacz co najmniej jeden system albo zostaw świeży start.', 'warning')
            return redirect(url_for('dbeditor.systems_kopia'))
        return run_import(lambda: AUTHOR_ZIP.read_bytes() if AUTHOR_ZIP.is_file() else b'', only, 'Wgrano ustawienia autora')

    def run_import(get_raw, only, title):
        report = dict(time=time.strftime('%Y-%m-%d %H:%M'), ok=[], skipped=[], errors=[])
        try:
            raw = get_raw()
            if not raw: raise ValueError('Wybierz plik kopii (.zip).')
            z = zipfile.ZipFile(io.BytesIO(raw))
            meta = json.loads(z.read('kuznia-mocy.json'))
            if meta.get('schema') != SCHEMA: raise ValueError('To nie jest kopia ustawień Kuźni Mocy.')
            names = set(z.namelist())
            # Baza czytana od nowa: co jest na tym serwerze teraz.
            mobs = {int(r['vnum']) for r in rows('SELECT vnum FROM player.mob_proto')}
            items = {int(r['vnum']) for r in rows('SELECT vnum FROM world.item_proto')}
            for key, name in SYSTEMS:
                if '%s/draft.json' % key not in names or (only is not None and key not in only): continue
                try:
                    cfg = json.loads(z.read('%s/draft.json' % key))
                    for n in sorted(names):
                        if n.startswith(key + '/assets/') and n.endswith('.tga') and '..' not in n:
                            atomic(spool / key / 'assets' / Path(n).name, z.read(n))
                    if key == 'misje':
                        for kind, label in (('hunts', 'Polowanie'), ('boss', 'Bossologia')):
                            keep = []
                            for r in cfg.get(kind) or []:
                                if r.get('race') and int(r['race']) not in mobs:
                                    report['skipped'].append('%s: etap „%s” — potwora #%s nie ma w bazie' % (label, r.get('name', ''), r['race']))
                                else: keep.append(r)
                            cfg[kind] = keep
                        for kind in ('hunts', 'metin', 'boss'):
                            for r in cfg.get(kind) or []:
                                good = [it for it in (r.get('items') or []) if int(it[0]) in items]
                                for it in r.get('items') or []:
                                    if int(it[0]) not in items: report['skipped'].append('Misje: nagroda #%s w etapie „%s” — przedmiotu nie ma w bazie' % (it[0], r.get('name', '')))
                                r['items'] = good
                    if key == 'horse':
                        from dbeditor.systems_horse import Store
                        from m2clientpack import horse_editor as horse
                        st = Store(spool / 'horse', ctx.get('boot_plan'))
                        with st.locked(): cur = st.read()
                        st.save_apply(horse.validate(cfg), horse.revision(cur))
                    else:
                        codec = codec_of(key)
                        st = SystemStore(spool / key, codec, ctx.get('boot_plan'))
                        with st.locked(): cur = st.read()
                        st.save_apply(codec.validate(cfg), codec.revision(cur))
                    report['ok'].append(name)
                except Exception as exc:
                    report['errors'].append('%s: %s' % (name, exc))
            for key, fname in EXTRA_FILES:
                n = '%s/%s' % (key, fname)
                if n in names and key != 'skan' and (only is None or key in only):
                    atomic(spool / key / fname, z.read(n)); report['ok'].append('Sława' if key == 'plus9' else key)
            # MT2009_NASZE_KOLEKCJE_V1: Kolekcjoner - przedmioty, ktorych nowy serwer nie ma, pominiete (raport).
            if 'kolekcje/dane.json' in names and (only is None or 'kolekcje' in only):
                try:
                    from dbeditor import systems_kolekcje
                    for n in sorted(names):
                        if n.startswith('kolekcje/ikony/') and n.endswith('.tga') and '..' not in n and n.count('/') == 2:
                            atomic(spool / 'kolekcje' / 'ikony' / Path(n).name, z.read(n))
                    data = json.loads(z.read('kolekcje/dane.json'))
                    systems_kolekcje.restore(spool / 'kolekcje', data, items, report['skipped'])
                    report['ok'].append('Kolekcjoner')
                except Exception as exc:
                    report['errors'].append('Kolekcjoner: %s' % exc)
            arts = [n for n in sorted(names) if n.startswith('okno/grafika/') and n.endswith('.tga') and '..' not in n and n.count('/') == 2]
            if arts and only is None:
                for n in arts: atomic(spool / 'okno' / 'grafika' / Path(n).name, z.read(n))
                report['ok'].append('Wygląd okna Ctrl+N (%d grafik)' % len(arts))
            if 'postep/quest.json' in names and only is None:
                try:
                    report['ok'].append(restore_progress(json.loads(z.read('postep/quest.json')),
                                                         json.loads(z.read('postep/postacie.json')), report['skipped']))
                except Exception as exc:
                    report['errors'].append('Postęp graczy: %s' % exc)
            tables = [n for n in sorted(names) if n.startswith('postep/tabele/') and n.endswith('.json')]
            if tables and only is None:
                try: report['ok'].append(restore_tables({Path(n).stem: json.loads(z.read(n)) for n in tables}, report['skipped']))
                except Exception as exc: report['errors'].append('Dane graczy (Sława, rangi, ranking): %s' % exc)
            if 'inne/stan.json' in names and only is None:
                try:
                    was = sorted(k for k, v in json.loads(z.read('inne/stan.json')).items() if (v or {}).get('on'))
                    if was: report['skipped'].append('Inne: w kopii były włączone: %s – włącz je ponownie w zakładce Inne '
                                                     '(włączenie zmienia bazę, więc kopia go nie przywraca sama).' % ', '.join(was))
                except (ValueError, AttributeError):
                    pass
            flash(title + ': %d systemów, pominięto %d pozycji, błędów %d. Szczegóły poniżej.' % (len(report['ok']), len(report['skipped']), len(report['errors'])),
                  'success' if not report['errors'] else 'warning')
        except (ValueError, KeyError, zipfile.BadZipFile) as exc:
            report['errors'].append(str(exc)); flash('Nie wgrano kopii: %s' % exc, 'error')
        atomic(spool / 'kopia-raport.json', json.dumps(report, ensure_ascii=False).encode('utf-8'))
        return redirect(url_for('dbeditor.systems_kopia'))
