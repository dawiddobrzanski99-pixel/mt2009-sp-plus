"""MT2009_NASZE_ULEPSZANIE_V1: Kuznia Mocy -> Ulepszanie: katalog wszystkich ulepszalnych przedmiotow
(bronie, zbroje, helmy, tarcze, bizuteria...) z kosztem, szansa i materialami kazdego +N.
Edycja w istniejacym edytorze kowala (dbeditor/refine.py: historia, szablony, rozdzielanie wspolnych przepisow).
Gra czyta refine_proto przy starcie - zmiana dziala po "Zastosuj" (restart kanalow) w panelu."""
from collections import OrderedDict
from flask import render_template, request, url_for, redirect, abort, current_app
from dbeditor import common_items as common
from dbeditor import refine as rf
from dbeditor.shops import load_items

CATEGORIES = OrderedDict([
    ('miecze', ('⚔️', 'Miecze', 'type=1 AND subtype=0')), ('sztylety', ('🗡️', 'Sztylety', 'type=1 AND subtype=1')),
    ('luki', ('🏹', 'Łuki', 'type=1 AND subtype=2')), ('dwureczne', ('🪓', 'Bronie dwuręczne', 'type=1 AND subtype=3')),
    ('dzwony', ('🔔', 'Dzwony', 'type=1 AND subtype=4')), ('wachlarze', ('🪭', 'Wachlarze', 'type=1 AND subtype=5')),
    ('bronie_inne', ('✴️', 'Inne bronie', 'type=1 AND subtype NOT IN (0,1,2,3,4,5)')),
    ('zbroje', ('🛡️', 'Zbroje', 'type=2 AND subtype=0')), ('helmy', ('⛑️', 'Hełmy', 'type=2 AND subtype=1')),
    ('tarcze', ('🔰', 'Tarcze', 'type=2 AND subtype=2')), ('bransolety', ('📿', 'Bransolety', 'type=2 AND subtype=3')),
    ('buty', ('👢', 'Buty', 'type=2 AND subtype=4')), ('naszyjniki', ('💠', 'Naszyjniki', 'type=2 AND subtype=5')),
    ('kolczyki', ('💎', 'Kolczyki', 'type=2 AND subtype=6')), ('zbroje_inne', ('🔮', 'Inne (talizmany, dodatki)', 'type=2 AND subtype NOT IN (0,1,2,3,4,5,6)')),
    ('inne', ('📦', 'Pozostałe (kostiumy, kamienie, pasy...)', 'type NOT IN (1,2)')),
])
PER_PAGE = 40


def families(rows, where, params, query):
    found = rf.item_rows(rows, where, params)
    groups = OrderedDict()
    for item in found:
        stem = rf.LEVEL.sub('', item['name']).strip() or item['name']
        if query and query.lower() not in item['name'].lower() and query != str(item['vnum']): continue
        groups.setdefault((stem, item['vnum'] // 10), {'name': stem, 'items': []})['items'].append(item)
    out = []
    for fam in groups.values():
        items = sorted(fam['items'], key=lambda i: i['vnum'])
        if not any(i['refined_vnum'] for i in items): continue
        fam['vnum'] = items[0]['vnum']; fam['steps'] = [i for i in items if i['refined_vnum']]
        out.append(fam)
    return out


def install(bp, ctx):
    login = ctx['login_required']

    def rows(sql, params=()):
        return common.ctx()['rows'](sql, params)

    @bp.route('/systemy/ulepszanie')
    @login
    def systems_ulepszanie():
        cat = request.args.get('kat', 'miecze')
        if cat not in CATEGORIES: cat = 'miecze'
        query = (request.args.get('q') or '').strip()
        page = max(1, int(request.args.get('s', '1')) if request.args.get('s', '1').isdigit() else 1)
        icon, title, where = CATEGORIES[cat]
        if query:
            params = (int(query), '%' + query + '%') if query.isdigit() else ('%' + query + '%',)
            fams = families(rows, ('(vnum=%s OR locale_name LIKE %s)' if query.isdigit() else 'locale_name LIKE %s') + ' AND (refined_vnum>0 OR refine_set>0)', params, '')
            title = 'Wyniki: „%s”' % query
        else:
            fams = families(rows, where + ' AND (refined_vnum>0 OR refine_set>0)', (), '')
        total = len(fams); pages = max(1, (total + PER_PAGE - 1) // PER_PAGE); page = min(page, pages)
        fams = fams[(page - 1) * PER_PAGE: page * PER_PAGE]
        recipes = rf.load_recipes(rows, [s['refine_set'] for f in fams for s in f['steps']])
        mats = load_items(rows, [v for r in recipes.values() for v, _c in rf.materials_of(rf.normalized(r))])
        for f in fams:
            f['rows'] = []
            for n, s in enumerate(f['steps'], 1):
                r = recipes.get(s['refine_set'])
                v = rf.normalized(r) if r else None
                lvl = rf.level_of(s)
                f['rows'].append(dict(frm=lvl if lvl is not None else n - 1, set=s['refine_set'], cost=v['cost'] if v else None,
                                      prob=v['prob'] if v else None,
                                      mats=[(mats.get(m, {'name': 'Przedmiot %d' % m})['name'], c) for m, c in rf.materials_of(v)] if v else []))
        try: pending = common.pending_context()
        except Exception: pending = {'pending_total': 0}
        return render_template('dbeditor/systems_refine.html', edit_endpoint='dbeditor.systems_ulepszanie_edit', cats=CATEGORIES, cat=cat, icon=icon, title=title, query=query,
                               fams=fams, total=total, page=page, pages=pages, sys_active='ulepszanie', system=None, **pending)

    @bp.route('/systemy/ulepszanie/<int:vnum>', methods=['GET', 'POST'])
    @login
    def systems_ulepszanie_edit(vnum):
        # MT2009_NASZE_ULEPSZANIE_V2: nowy wyglad; zapis przez sprawdzony edytor kowala (refine.py: historia, klony przepisow).
        if request.method == 'POST':
            # Stary edytor przy bledzie renderuje swoja strone (to zjada komunikaty) - tu tylko zapis, komunikaty zostaja.
            original = rf.render_template; rf.render_template = lambda *a, **k: ''
            try: current_app.view_functions['dbeditor.refine_edit'](vnum=vnum)
            finally: rf.render_template = original
            # MT2009_NASZE_ULEPSZANIE_ZASTOSUJ_V1: "Zapisz i zastosuj" = jak "Zastosuj" w panelu (restart rdzeni) + pliki klienta.
            if request.form.get('zastosuj') == '1':
                from flask import flash
                from dbeditor import common_items
                queue = ctx.get('queue_restart')
                try:
                    if queue is None: raise RuntimeError('ten panel nie ma funkcji restartu gry')
                    queue()
                    try: common_items.mark_applied()
                    except Exception: pass
                    flash('Zapisano i zlecono restart kanałów — zmiany ulepszania działają po starcie (ok. minuty). Pliki klienta pobierają się poniżej.', 'success')
                    return redirect(url_for('dbeditor.systems_ulepszanie_edit', vnum=vnum, pobierz=1))
                except FileExistsError:
                    flash('Zapisano, ale poprzedni restart jeszcze trwa — kliknij „Zapisz i zastosuj” ponownie za chwilę.', 'warning')
                except (OSError, RuntimeError) as exc:
                    flash('Zapisano, ale nie udało się zlecić restartu: %s' % exc, 'error')
            return redirect(url_for('dbeditor.systems_ulepszanie_edit', vnum=vnum))
        chain = rf.load_chain(rows, vnum)
        if chain is None: abort(404)
        ids = [it['refine_set'] for it in chain if it['refined_vnum']]
        recipes = rf.load_recipes(rows, ids); users = rf.recipe_users(rows, ids)
        inchain = {it['vnum'] for it in chain}
        steps = []
        for i, it in enumerate(chain):
            if not it['refined_vnum']: continue
            result = chain[i + 1] if i + 1 < len(chain) and chain[i + 1]['vnum'] == it['refined_vnum'] else None
            r = recipes.get(it['refine_set']); v = rf.normalized(r) if r else None
            lvl = rf.level_of(result) if result and rf.level_of(result) is not None else len(steps) + 1
            outside = [u for u in users.get(it['refine_set'], []) if u['vnum'] not in inchain]
            steps.append(dict(index=len(steps), item=it, result=result, set=it['refine_set'], vals=v, level=lvl, outside=outside,
                              mats=rf.materials_of(v) if v else []))
        names = load_items(rows, [m for s in steps for m, _c in s['mats']])
        try:
            from dbeditor import dropfiles as df
            for v in names: names[v]['icon'] = df.icon_url(v)
        except Exception: pass
        shared = sorted({s['set'] for s in steps if s['vals'] and s['outside']})
        try: pending = common.pending_context()
        except Exception: pending = {'pending_total': 0}
        return render_template('dbeditor/systems_refine_edit.html', chain=chain, steps=steps, names=names, shared=shared, slots=rf.SLOTS,
                               family=rf.LEVEL.sub('', chain[0]['name']).strip() or chain[0]['name'], vnum=vnum,
                               dbe_csrf=common.csrf_token(), sys_active='ulepszanie', system=None, **pending)
