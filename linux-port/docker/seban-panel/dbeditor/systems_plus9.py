"""MT2009_NASZE_PLUS9_USTAWIENIA_V1: Kuznia Mocy -> +9 Origin: ogloszenie na czacie "kto ulepszyl na +9 jako N."
i nicki autorow na przedmiocie (MT2009_PLUS9_ORIGIN_V1). Ustawienia w systems/plus9/config.txt - gra czyta je przy
kazdym ulepszeniu na +9, bez restartu. Opis na przedmiocie pokazuje klient (plus9origin.py w ROOT)."""
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, abort
from dbeditor import common_items as common
from dbeditor.systems_store import atomic

DEFAULT_TEXT = '[Ulepszenie +9] {gracz} ulepszyl {przedmiot} jako {nr}. osoba na serwerze!'


def read(root):
    cfg = dict(enabled=True, announce=True, first=0, text=DEFAULT_TEXT)
    path = root / 'config.txt'
    if path.exists():
        for line in path.read_text(encoding='ascii', errors='replace').splitlines():
            k, _s, v = line.partition(' ')
            if k == 'enabled': cfg['enabled'] = v.strip() != '0'
            elif k == 'announce': cfg['announce'] = v.strip() == '1'
            elif k == 'first' and v.strip().isdigit(): cfg['first'] = int(v)
            elif k == 'text':
                try: cfg['text'] = bytes.fromhex(v.strip()).decode('cp1250')
                except ValueError: pass
    return cfg


def install(bp, ctx):
    root = Path(ctx['spool']) / 'systems/plus9'
    login = ctx['login_required']

    def rows(sql, params=()):
        return common.ctx()['rows'](sql, params)

    @bp.route('/systemy/plus9', methods=['GET', 'POST'])
    @login
    def systems_plus9():
        if request.method == 'POST':
            if not common.check_csrf(): abort(403)
            try:
                if request.form.get('action') == 'defaults':
                    cfg = dict(enabled=True, announce=True, first=0, text=DEFAULT_TEXT)
                else:
                    first = request.form.get('first', '0').strip() or '0'
                    if not first.isdigit() or int(first) > 1000000: raise ValueError('„Tylko pierwszych” musi być liczbą 0–1 000 000.')
                    text = request.form.get('text', '').strip()
                    if not text or len(text) > 200 or any(ord(c) < 32 for c in text): raise ValueError('Treść: 1–200 znaków.')
                    text.encode('cp1250')
                    cfg = dict(enabled=request.form.get('enabled') == '1', announce=request.form.get('announce') == '1', first=int(first), text=text)
                body = 'enabled %d\nannounce %d\nfirst %d\ntext %s\n' % (int(cfg['enabled']), int(cfg['announce']), cfg['first'], cfg['text'].encode('cp1250').hex())
                root.mkdir(parents=True, exist_ok=True); atomic(root / 'config.txt', body.encode('ascii'))
                flash('Zapisano. Działa od następnego ulepszenia na +9 — bez restartu.', 'success')
            except UnicodeEncodeError:
                flash('Treść zawiera znaki, których gra nie wyświetli (dozwolone polskie litery).', 'error')
            except ValueError as exc:
                flash(str(exc), 'error')
            return redirect(url_for('dbeditor.systems_plus9'))
        cfg = read(root)
        try:
            recent = rows('SELECT i.vnum, i.ordinal, CAST(i.author_name AS BINARY) AS who, CAST(p.locale_name AS BINARY) AS item FROM player.mt2009_plus9_items i '
                          'LEFT JOIN world.item_proto p ON p.vnum=i.vnum WHERE i.historical_seed=0 ORDER BY i.item_id DESC LIMIT 15')
            recent = [dict(vnum=int(r['vnum']), nr=int(r['ordinal']), who=common.text_of(r['who']) or '?', item=common.text_of(r['item']) or ('#%s' % r['vnum'])) for r in recent]
            total = rows('SELECT COUNT(*) AS n FROM player.mt2009_plus9_items')[0]['n']
        except Exception:
            recent, total = [], None
        return render_template('dbeditor/systems_plus9.html', cfg=cfg, recent=recent, total=total, default_text=DEFAULT_TEXT,
                               dbe_csrf=common.csrf_token(), sys_active='plus9', system=None)
