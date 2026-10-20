"""MT2009_NASZE_SYSTEMY_V1: zakladka "Systemy" panelu Seban.

Przeglad systemow i strony kolejnych etapow edytora (gildia, polimorfia, rangi,
ranking tygodnia, misje Ctrl+N). Kon ma wlasny modul (systems_horse.py).
Strony "w przygotowaniu" niczego nie zapisuja - opisuja tylko, co bedzie edytowalne.
"""
from pathlib import Path
from flask import render_template, request

# klucz, endpoint, ikona, tytul, opis, gotowe?, plik z obecnymi wartosciami
SYSTEMS = [
    ('kon', 'dbeditor.systems_horse', '🐎', 'Koń',
     'Bonusy poziomów 1–30, nazwy, kolory i grafiki; paczka ROOT dla klienta.', True, 'seban_horse_rewards.h'),
    ('gildia', 'dbeditor.systems_gildia', '🛡️', 'Gildia',
     'Bonusy członków zależne od poziomu gildii 1–20 — dowolne bonusy z gry.', True,
     'custom_guild_combat_rewards.h'),
    ('polimorfia', 'dbeditor.systems_polimorfia', '🎭', 'Polimorfia',
     'Bonusy i czas przemiany dla każdego poziomu umiejętności polimorfii.', True,
     'custom_horse_polymorph_rewards.h'),
    ('rangi', 'dbeditor.systems_rangi', '🎖️', 'Rangi',
     'Progi Punktów Rangi i bonusy 12 rang — dowolne bonusy z gry.', True, 'playerbot_rank_points.h'),
    ('ranking', 'dbeditor.systems_ranking', '🏆', 'Ranking tygodnia',
     'Bonusy tytułów tygodnia: 8 kategorii × miejsca 1–3 — dowolne bonusy z gry.', True, 'playerbot_weekly_rank.h'),
    ('misje', 'dbeditor.systems_misje', '📜', 'Misje (Ctrl+N)',
     'Polowania, metinologia, bossologia: etapy, cele, ilości, kolejność, wymagania, bonusy i nagrody.', True,
     'hunt-data.inc + questy'),
    ('ulepszanie', 'dbeditor.systems_ulepszanie', '🔨', 'Ulepszanie',
     'Wszystkie bronie, zbroje i biżuteria: koszt w Yang, szansa i materiały każdego +.', True, 'refine_proto'),
    ('plus9', 'dbeditor.systems_plus9', '🏅', 'Sława',
     'Ogłoszenie na czacie, kto ulepszył przedmiot na +9 i którym był na serwerze; nicki autorów na przedmiocie.', True, 'plus9_origin.h'),
    ('skan', 'dbeditor.systems_skan', '🔄', 'Skanuj serwer',
     'Co zmieniło się w bazie (przedmioty, potwory, ulepszenia) i co odświeżyć dla klienta.', True, 'baza'),
    ('kopia', 'dbeditor.systems_kopia', '💾', 'Kopia ustawień',
     'Pobierz wszystkie ustawienia Kuźni przed aktualizacją serwera i wgraj je z powrotem po ponownej instalacji.', True, 'spool'),
]

MISSION_TABS = [
    ('polowania', '🏹', 'Polowania', [
        'wybór potworów dla każdego etapu i liczba zabójstw',
        'kolejność etapów i wymagany poziom',
        'stałe bonusy za ukończenie etapu',
        'nagrody: przedmioty, Yang, ochrona przed ponownym odbiorem']),
    ('metinologia', '🪨', 'Metinologia', [
        'które metiny liczą się do etapu i ile trzeba zniszczyć',
        'kolejność etapów i wymagania',
        'bonusy stałe i końcowe sumy bonusów',
        'nagrody: Yang, przedmioty, dodania i zmiany bonusów']),
    ('bossologia', '👹', 'Bossologia', [
        'które bossy liczą się do etapu i ile razy',
        'kolejność etapów',
        'bonusy stałe za etapy',
        'nagrody, w tym kupony SM']),
    ('biolog', '🧪', 'Biolog', [
        'wymagane przedmioty i ich liczba na etap',
        'szansa i czas oddania',
        'bonusy za etap (np. potwory, atak, średnie obrażenia)',
        'bez podwójnego naliczania po zmianie']),
]

PLANNED = {
    'gildia': ['tabela poziomów gildii z bonusami (dodawanie i usuwanie pozycji)',
               'przełącznik modułu bez kasowania konfiguracji',
               'zastosowanie bez restartu z potwierdzeniem wszystkich kanałów',
               'odświeżenie bonusów członków po zmianie'],
    'polimorfia': ['tabela poziomów umiejętności (M1–P) z bonusami',
                   'czas przemiany dla każdego progu',
                   'zastosowanie bez restartu, przeliczenie aktywnych przemian'],
    'rangi': ['progi punktów i kolejność rang', 'nazwy, kolory i grafiki rang (podgląd)',
              'bonusy za rangę', 'paczka ROOT, jeśli zmienia się wygląd w kliencie'],
    'ranking': ['zasady naliczania tygodnia', 'tytuły: nazwy, kolory, grafiki',
                'bonusy i nagrody za miejsca', 'bez ponownego wypłacania nagród'],
}


def install(bp, ctx):
    login = ctx['login_required']
    by_key = {s[0]: s for s in SYSTEMS}

    @bp.app_context_processor
    def systems_context():
        return {'sys_systems': SYSTEMS}

    def fresh_start_once():
        """MT2009_NASZE_SWIEZY_START_V1: raz po instalacji z paczki - kon, gildia, polimorfia, ranking i rangi
        od zera (takze ustawienia z wczesniejszej instalacji). Nie na serwerze autora (znacznik .autor-kuzni)."""
        from m2clientpack import kuznia_dodatki
        root = Path(ctx['spool']) / 'systems'
        done = root / '.swiezy-start-zrobiony'
        if not kuznia_dodatki.fresh() or (root / '.autor-kuzni').exists():
            return
        weekly_done = root / '.swiezy-ranking-v2'
        if done.exists() and not weekly_done.exists():
            # Wczesniejsze paczki zerowaly ranking tygodnia - raz: bonusy z gry tego serwera.
            from flask import flash
            from dbeditor.systems_backup import codec_of
            from dbeditor.systems_store import SystemStore, atomic
            try:
                codec = codec_of('ranking')
                st = SystemStore(root / 'ranking', codec, ctx.get('boot_plan'))
                with st.locked(): cur = st.read()
                st.save_apply(codec.validate(codec.defaults()), codec.revision(cur))
                atomic(weekly_done, b'1')
                flash('Kuźnia Mocy: ranking tygodnia ustawiony jak w grze tego serwera i zastosowany.', 'success')
            except Exception as exc:
                flash('Kuźnia Mocy: nie ustawiono rankingu tygodnia (spróbuję przy następnym wejściu): %s' % exc, 'warning')
            return
        if done.exists():
            return
        from flask import flash
        from dbeditor.systems_backup import codec_of
        from dbeditor.systems_store import SystemStore, atomic
        ok, bad = [], []
        for key in ('gildia', 'polimorfia', 'ranking', 'rangi'):
            try:
                codec = codec_of(key)
                st = SystemStore(root / key, codec, ctx.get('boot_plan'))
                with st.locked(): cur = st.read()
                st.save_apply(codec.validate(codec.defaults()), codec.revision(cur)); ok.append(key)
            except Exception as exc:
                bad.append('%s: %s' % (key, exc))
        try:
            from dbeditor.systems_horse import Store
            from m2clientpack import horse_editor as horse
            st = Store(root / 'horse', ctx.get('boot_plan'))
            with st.locked(): cur = st.read()
            st.save_apply(horse.validate(horse.defaults()), horse.revision(cur)); ok.append('kon')
        except Exception as exc:
            bad.append('kon: %s' % exc)
        if not bad:
            atomic(done, b'1'); atomic(root / '.swiezy-ranking-v2', b'1')
            flash('Kuźnia Mocy: świeży start — koń, gildia, polimorfia, ranking i rangi ustawione od zera i zastosowane w grze.', 'success')
        else:
            flash('Kuźnia Mocy: świeży start nie w pełni (spróbuję przy następnym wejściu; gra musi działać): ' + '; '.join(bad), 'warning')

    @bp.route('/systemy')
    @login
    def systems_index():
        fresh_start_once()
        # MT2009_NASZE_KLIENT_ROOT_PRZEGLAD_V1: budowanie ROOT (wszystkie wtyczki) prosto z Przegladu.
        from dbeditor import common_items as common
        try:
            from dbeditor.systems_horse import Store
            from m2clientpack import horse_editor as horse
            store = Store(Path(ctx['spool']) / 'systems/horse')
            horse_revision = horse.revision(store.read())
        except Exception:
            horse_revision = ''; store = None
        # Pelne wydanie (ROOT + gamedata + dbdata) tez z Przegladu.
        publication_revision, published = '', {}
        try:
            from m2clientpack import horse_publication as publication
            import json
            publication_revision = publication.token(store.root)
            p = store.root / 'last-client-publication.json'
            published = json.loads(p.read_bytes()) if p.exists() else {}
        except Exception:
            pass
        # MT2009_NASZE_STAN_MODULOW_V1: wlaczony / wylaczony (przelacznik modulu w projekcie systemu).
        import json as _json
        enabled = {}
        for key in ('kon', 'gildia', 'polimorfia', 'rangi', 'ranking', 'misje'):
            p = Path(ctx['spool']) / 'systems' / ('horse' if key == 'kon' else key) / 'draft.json'
            try:
                cfg = _json.loads(p.read_bytes()) if p.exists() else {}
                enabled[key] = bool(cfg.get('master_enabled', True)) and bool(cfg.get('enabled', True))
            except (OSError, ValueError):
                enabled[key] = True
        return render_template('dbeditor/systems_hub.html', systems=SYSTEMS, sys_active='przeglad', horse_revision=horse_revision,
                               publication_revision=publication_revision, published=published, enabled=enabled, dbe_csrf=common.csrf_token())

    @bp.route('/systemy/info')
    @login
    def systems_info():  # MT2009_NASZE_SYSTEMY_INFO_V1
        return render_template('dbeditor/systems_info.html', sys_active='info')

    def soon_view(key):
        def view():
            system = by_key[key]
            tabs, tab = None, None
            if key == 'misje':
                tabs = MISSION_TABS
                wanted = request.args.get('tab', 'polowania')
                tab = next((t for t in MISSION_TABS if t[0] == wanted), MISSION_TABS[0])
            return render_template('dbeditor/systems_soon.html', system=system, systems=SYSTEMS,
                                   planned=PLANNED.get(key, []), tabs=tabs, tab=tab, sys_active=key)
        return view

    for key in ():
        bp.add_url_rule('/systemy/' + key, 'systems_' + key, login(soon_view(key)))
