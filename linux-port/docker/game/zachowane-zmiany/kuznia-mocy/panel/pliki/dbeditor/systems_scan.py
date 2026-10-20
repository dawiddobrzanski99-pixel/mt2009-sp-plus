"""MT2009_NASZE_SKAN_V1: Kuznia Mocy -> Skanuj serwer: co zmienilo sie w bazie (przedmioty, potwory, metiny, bossy,
przepisy ulepszen) od ostatniego skanu. Nic nie nadpisuje - tylko raport i wskazowki, co odswiezyc dla klienta."""
import hashlib
import json
import time
from pathlib import Path
from flask import flash, redirect, render_template, request, url_for, abort
from dbeditor import common_items as common
from dbeditor.systems_store import atomic

QUERIES = {
    'items': ('Przedmioty', "SELECT vnum AS k, CAST(locale_name AS BINARY) AS n, CONCAT_WS('|', type, subtype, refined_vnum, refine_set, gold, shop_buy_price) AS h FROM world.item_proto"),
    'mobs': ('Potwory, metiny i bossy', "SELECT vnum AS k, CAST(locale_name AS BINARY) AS n, CONCAT_WS('|', type, `rank`, level) AS h FROM world.mob_proto"),
    'refine': ('Przepisy ulepszeń', "SELECT id AS k, CAST(id AS CHAR) AS n, CONCAT_WS('|', cost, prob, vnum0, count0, vnum1, count1, vnum2, count2, vnum3, count3, vnum4, count4) AS h FROM world.refine_proto"),
}


def snapshot(rows):
    out = {}
    for key, (_title, sql) in QUERIES.items():
        data = {}
        for r in rows(sql):
            name = common.text_of(r['n']) if isinstance(r['n'], (bytes, bytearray)) else str(r['n'] or '')
            data[str(r['k'])] = [hashlib.sha1(str(r['h']).encode()).hexdigest()[:12], (name or '').strip()[:40]]
        out[key] = data
    return out


def diff(old, new):
    res = {}
    for key, (title, _sql) in QUERIES.items():
        a, b = old.get(key, {}), new.get(key, {})
        added = [(k, b[k][1]) for k in b if k not in a]
        removed = [(k, a[k][1]) for k in a if k not in b]
        changed = [(k, b[k][1]) for k in b if k in a and a[k][0] != b[k][0]]
        res[key] = dict(title=title, total=len(b), added=added, removed=removed, changed=changed)
    return res


def install(bp, ctx):
    root = Path(ctx['spool']) / 'systems/skan'
    login = ctx['login_required']

    def rows(sql, params=()):
        return common.ctx()['rows'](sql, params)

    @bp.route('/systemy/skan', methods=['GET', 'POST'])
    @login
    def systems_skan():
        path = root / 'ostatni.json'
        if request.method == 'POST':
            if not common.check_csrf(): abort(403)
            snap = snapshot(rows)
            atomic(path, json.dumps(dict(time=time.time(), data=snap), ensure_ascii=False).encode('utf-8'))
            flash('Zapisano stan bazy jako punkt odniesienia dla następnego skanu.', 'success')
            return redirect(url_for('dbeditor.systems_skan'))
        try:
            now = snapshot(rows); error = None
        except Exception as exc:
            now, error = {}, str(exc)
        last = json.loads(path.read_bytes()) if path.exists() else None
        result = diff(last['data'], now) if last and now else None
        need_dbdata = bool(result and (result['items']['added'] or result['items']['changed'] or result['items']['removed']))
        need_restart = bool(result and any(result[k]['added'] or result[k]['changed'] or result[k]['removed'] for k in ('refine', 'mobs')))
        counts = {k: len(v) for k, v in now.items()}
        return render_template('dbeditor/systems_scan.html', result=result, last=last, counts=counts, error=error,
                               need_dbdata=need_dbdata, need_restart=need_restart, titles={k: v[0] for k, v in QUERIES.items()},
                               dbe_csrf=common.csrf_token(), sys_active='skan', system=None,
                               when=time.strftime('%Y-%m-%d %H:%M', time.localtime(last['time'])) if last else None)
