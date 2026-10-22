"""MT2009_NASZE_INNE_V1: Kuznia Mocy -> "Inne" - dodatki wlaczane przelacznikiem (domyslnie wylaczone).

Wlaczenie = zmiany na serwerze (przedmioty przez edytor bazy z historia, zawartosc skrzynek przez
mechanizm "Szkatulki", flaga dla silnika w spool/systems/inne/flagi.txt) + restart kanalow.
Wylaczenie = wszystko z powrotem: zmiany przedmiotow cofniete z historii (revert), poprzednia
zawartosc skrzynek przywrocona, flaga zdjeta, restart. Stan: spool/systems/inne/stan.json.
"""
import json
import time
from pathlib import Path

from flask import flash, redirect, render_template, request, url_for, abort

SAKIEWKA, SKRZYNKA_KU, KU = 27999, 50035, 50300
KD_KINDS = range(28030, 28044)          # 14 rodzajow Kamieni Duszy
KD_GRADES = ((0, 5), (100, 4), (200, 3), (300, 2), (400, 1))   # +0..+4 i ich wagi


def _kd_entries(settings=None):
    """Zawartosc Sakiewki: wybrane rodzaje KD x ulepszenia +0..+4 z wagami (ustawienia z panelu albo domyslne)."""
    s = (settings or {}).get("sakiewka_zawartosc") or {}
    weights = s.get("wagi") or {}
    kinds = [k for k in (s.get("rodzaje") or list(KD_KINDS)) if k in KD_KINDS] or list(KD_KINDS)
    out = []
    for grade, default in KD_GRADES:
        try: weight = max(0, int(weights.get(str(grade // 100), default)))
        except (TypeError, ValueError): weight = default
        if weight:
            out += [{"item": str(kind + grade), "count": "1", "prob": str(weight), "rare": "0", "comment": ""} for kind in kinds]
    return out or [{"item": str(kind), "count": "1", "prob": "1", "rare": "0", "comment": ""} for kind in kinds]


OPTIONS = [
    {"key": "sakiewka_kd", "icon": "👛", "name": "Sakiewka z Kamieniami Dusz",
     "desc": "Sakiewka Kamieni Dusz wypada z każdego Metina na serwerze (także z nowych, dodanych później). Gdzie Metin "
             "miał KD w dropie – KD zamienia się w Sakiewkę z tą samą szansą; pozostałe Metiny mają szansę ustawioną niżej. "
             "W środku losowy KD +0…+4 (niższy częściej). Można ją handlować i trzymać w stosie, boty ją otwierają. "
             "KD znika z dropu i podglądu Metinów.",
     "items": [(SAKIEWKA, {"locale_name": "Sakiewka Kamieni Dusz", "type": 23, "subtype": 0,   # skrzynka (jak u autora)
                           "stack": 200, "antiflag": 0, "flag": 4})],
     "chests": {SAKIEWKA: {"name": "KuzniaSakiewkaKD", "type": "", "items": _kd_entries}}},
    {"key": "skrzynka_ku", "icon": "📦", "name": "Skrzynia z Księgą Umiejętności",
     "desc": "Księga Umiejętności z Metinów i bossów wypada jako Skrzynia z KU – z tą samą szansą, co KU w grze. "
             "W środku 1 Księga Umiejętności. Handel, stos, boty ją otwierają. KU znika z dropu i podglądu.",
     "items": [(SKRZYNKA_KU, {"locale_name": "Skrzynia z KU", "type": 23, "subtype": 0, "stack": 200, "antiflag": 0,
                              "flag": 4})],
     "chests": {SKRZYNKA_KU: {"name": "KuzniaSkrzyniaKU", "type": "",
                              "items": lambda s=None: [{"item": str(KU), "count": "1", "prob": "1", "rare": "0", "comment": ""}]}}},
    {"key": "ulepszacze", "icon": "🧰", "name": "Ulepszacze i przedmioty Biologa z Kolekcjonera",
     "desc": "Kowal bierze materiały do ulepszania najpierw z plecaka, a brakujące z Kolekcjonera. Tak samo Biolog "
             "przy oddawaniu przedmiotów do badań. Nie trzeba wyciągać materiałów z Kolekcjonera ręcznie.",
     "items": [], "chests": {}},
    {"key": "klepsydra", "icon": "⌛", "name": "Klepsydra Biologa",
     "desc": "Użycie Klepsydry (ID 71102) zeruje czas oczekiwania u Biologa (gdy nie trzeba czekać, nie zużywa się). "
             "Skąd wypada i z jaką szansą – ustawiasz niżej (domyślnie 2% z każdego Metina i bossa); widać to w podglądzie "
             "dropu. Można ją handlować i trzymać w stosie.",
     # przedmiot questowy (quest klepsydra_biologa, "when 71102.use"); bez wyrzucania i sprzedazy w sklepie, handel tak
     "items": [(71102, {"locale_name": "Klepsydra Biologa", "type": 18, "subtype": 0, "stack": 200, "antiflag": 384,
                        "flag": 4, "value0": 0, "value1": 0, "value2": 0, "value3": 0})], "chests": {}},
    {"key": "auto_kolekcjoner", "icon": "📥", "name": "Drop prosto do Kolekcjonera",
     "desc": "Wszystko, co gracz podniesie z ziemi, od razu trafia do jego Kolekcjonera (magazyn kolekcjonera) – "
             "bez zapychania plecaka. Na tych samych zasadach co ręczne odkładanie w magazynie: przedmioty questowe, "
             "nie do przechowania albo gdy Kolekcjoner jest pełny lub jeszcze się wczytuje – zostają w plecaku. "
             "Boty bez zmian. Gracze nic nie pobierają.",
     "items": [], "chests": {}, "autor": True},  # przelacznik takze na serwerze autora Kuzni
    {"key": "licznik", "icon": "🗺️", "name": "Licznik Metinów i bossów pod minimapą",
     "desc": "Pod minimapą pokazuje, ile Metinów i bossów żyje teraz na mapie (i ilu członków Twojej gildii na niej jest). "
             "Wymaga ROOT z Kuźni (Przegląd → Klient). Wyłączone – licznik znika.",
     "items": [], "chests": {}},
]
BY_KEY = {o["key"]: o for o in OPTIONS}


def install(bp, ctx):
    from dbeditor import common_items as common
    from dbeditor import dropfiles as df
    login = ctx["login_required"]
    root = Path(ctx["spool"]) / "systems" / "inne"
    # Serwer autora Kuzni: te dodatki sa u niego wbudowane na stale - przelaczniki ukryte.
    author = lambda: (Path(ctx["spool"]) / "systems" / ".autor-kuzni").exists()

    def load():
        try:
            return json.loads((root / "stan.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def chance(state):
        """Szansa Sakiewki z Metina bez KD w dropie, w 1/10000 (domyslnie 200 = 2%)."""
        try: return max(0, min(10000, int((state.get("ustawienia") or {}).get("sakiewka_szansa", 200))))
        except (TypeError, ValueError): return 200

    def hourglass(state):
        """Klepsydra Biologa: szansa (1/10000) z Metinow, z bossow i z wybranych potworow."""
        s = state.get("ustawienia") or {}
        def num(v, d):
            try: return max(0, min(10000, int(v)))
            except (TypeError, ValueError): return d
        moby = []
        for m in s.get("klepsydra_moby") or []:
            try: moby.append({"race": int(m["race"]), "chance": num(m["chance"], 0), "name": str(m.get("name") or "")})
            except (TypeError, ValueError, KeyError): pass
        return {"metin": num(s.get("klepsydra_metin"), 200), "boss": num(s.get("klepsydra_boss"), 200), "moby": moby}

    def mob_rows(sql, params):
        for table in ("player.mob_proto", "world.mob_proto"):
            try: return ctx["rows"](sql.replace("MOBS", table), params)
            except Exception: continue
        return []

    def save(state):
        root.mkdir(parents=True, exist_ok=True)
        tmp = root / "stan.json.tmp"
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(root / "stan.json")
        flags = "".join("%s=1\n" % k for k, v in sorted(state.items()) if k in BY_KEY and (v or {}).get("on"))
        flags += "sakiewka_szansa=%d\n" % chance(state)
        hg = hourglass(state)
        flags += "klepsydra_metin=%d\nklepsydra_boss=%d\n" % (hg["metin"], hg["boss"])
        flags += "".join("klepsydra_mob=%d:%d\n" % (m["race"], m["chance"]) for m in hg["moby"])
        tmp = root / "flagi.txt.tmp"
        tmp.write_text(flags, encoding="ascii")
        tmp.replace(root / "flagi.txt")

    def enable(opt, state):
        previous = {}
        if opt["chests"]:
            spool = df.spool_dir()
            custom = df.read_chest_custom(spool)
            for vnum, group in opt["chests"].items():
                previous[str(vnum)] = custom.get(vnum)
                custom[vnum] = {"name": group["name"], "vnum": vnum, "type": group["type"], "extras": [],
                                "items": group["items"](state.get("ustawienia") or {})}
            df.write_custom(spool, "chest", df.render_chest_custom(custom, "Kuznia Inne: " + opt["key"]), "Kuznia Inne: wlaczono " + opt["key"])
        batch = None
        updates = [(vnum, values) for vnum, values in opt["items"]]
        if updates:
            batch, _changed = common.save_rows("world.item_proto", updates, note="Kuźnia Mocy – Inne: " + opt["name"])
        state[opt["key"]] = {"on": True, "batch": batch, "chests": previous, "time": time.strftime("%Y-%m-%d %H:%M")}

    def disable(opt, state):
        st = state.get(opt["key"]) or {}
        if st.get("chests"):
            spool = df.spool_dir()
            custom = df.read_chest_custom(spool)
            for vnum, old in st["chests"].items():
                if old is None:
                    custom.pop(int(vnum), None)
                else:
                    custom[int(vnum)] = old
            df.write_custom(spool, "chest", df.render_chest_custom(custom, "Kuznia Inne: " + opt["key"]), "Kuznia Inne: wylaczono " + opt["key"])
        if st.get("batch"):
            common.revert(batch=st["batch"], force=True)
        state[opt["key"]] = {"on": False, "time": time.strftime("%Y-%m-%d %H:%M")}

    def current(vnum, cols):
        found = ctx["rows"]("SELECT " + ", ".join("CAST(`%s` AS BINARY) AS `%s`" % (c, c) for c in cols) +
                            " FROM world.item_proto WHERE vnum = %s", (vnum,))
        if not found: return None
        out = {}
        for c in cols:
            v = found[0][c]
            if isinstance(v, (bytes, bytearray)):
                try: v = bytes(v).decode("utf-8")
                except UnicodeDecodeError: v = bytes(v).decode("cp1250", "replace")
            out[c] = "" if v is None else str(v)
        return out

    def heal():
        """MT2009_NASZE_INNE_NAPRAWA_V1: wlaczone opcje po aktualizacji serwera / nowej bazie - przedmioty i skrzynki
        wracaja do wartosci opcji (aktualizacja nadpisala item_proto albo plik skrzynek). Zwraca naprawione nazwy."""
        state = load()
        fixed = []
        for opt in OPTIONS:
            st = state.get(opt["key"]) or {}
            if not st.get("on"): continue
            broken = False
            for vnum, values in opt["items"]:
                have = current(vnum, list(values))
                if have is not None and any(have[c] != str(v) for c, v in values.items()):
                    broken = True
            if broken:
                batch, _changed = common.save_rows("world.item_proto", list(opt["items"]), note="Kuźnia Mocy – Inne (naprawa po aktualizacji): " + opt["name"])
                if batch: st["batch"] = batch
            if opt["chests"]:
                spool = df.spool_dir()
                custom = df.read_chest_custom(spool)
                missing = [v for v, g in opt["chests"].items() if (custom.get(v) or {}).get("name") != g["name"]]
                if missing:
                    for vnum in missing:
                        group = opt["chests"][vnum]
                        st.setdefault("chests", {}).setdefault(str(vnum), None)
                        custom[vnum] = {"name": group["name"], "vnum": vnum, "type": group["type"], "extras": [], "items": group["items"](state.get("ustawienia") or {})}
                    df.write_custom(spool, "chest", df.render_chest_custom(custom, "Kuznia Inne: naprawa"), "Kuznia Inne: naprawa " + opt["key"])
                    broken = True
            if broken:
                state[opt["key"]] = st
                fixed.append(opt["name"])
        if fixed:
            save(state)
            try:
                if ctx.get("queue_restart"): ctx["queue_restart"]()
                common.mark_applied()
            except Exception:
                pass
        return fixed

    healed = {"done": False}

    @bp.before_app_request
    def systems_inne_heal_once():
        # Raz na uruchomienie panelu, przy pierwszym wejsciu w Kuznie (nie przy kazdym zapytaniu).
        if healed["done"] or author() or not request.path.startswith("/db/systemy"): return
        healed["done"] = True
        try:
            fixed = heal()
            if fixed:
                flash("Kuźnia Mocy – Inne: po aktualizacji serwera przywrócono włączone opcje: %s. Kanały gry restartują się." % ", ".join(fixed), "warning")
        except Exception as exc:
            healed["done"] = False
            flash("Kuźnia Mocy – Inne: nie udało się sprawdzić opcji po aktualizacji (%s) – spróbuję przy następnym wejściu." % exc, "warning")

    @bp.route("/systemy/inne", methods=["GET"])
    @login
    def systems_inne():
        state = load()
        rows = [dict(o, on=bool((state.get(o["key"]) or {}).get("on")), since=(state.get(o["key"]) or {}).get("time"))
                for o in OPTIONS]
        return render_template("dbeditor/systems_inne.html", options=rows, author=author(), dbe_csrf=common.csrf_token(),
                               sys_active="inne", system=None, szansa=chance(state) / 100.0, klepsydra=hourglass(state),
                               kd=pouch_view(state))

    def pouch_view(state):
        s = (state.get("ustawienia") or {}).get("sakiewka_zawartosc") or {}
        w = s.get("wagi") or {}
        chosen = set(s.get("rodzaje") or KD_KINDS)
        try:
            found = ctx["rows"]("SELECT vnum, CAST(locale_name AS BINARY) AS n FROM world.item_proto WHERE vnum BETWEEN 28030 AND 28043", ())
        except Exception:
            found = []
        names = {}
        for r in found:
            n = r["n"]
            if isinstance(n, (bytes, bytearray)):
                try: n = bytes(n).decode("utf-8")
                except UnicodeDecodeError: n = bytes(n).decode("cp1250", "replace")
            names[int(r["vnum"])] = str(n or "").replace("+0", "").strip()
        return {"wagi": [int(w.get(str(g), d)) for g, (_grade, d) in enumerate(KD_GRADES)],
                "rodzaje": [(k, names.get(k, "KD %d" % k), k in chosen) for k in KD_KINDS]}

    @bp.route("/systemy/inne/potwory", methods=["GET"])
    @login
    def systems_inne_mobs():
        from flask import jsonify
        q = (request.args.get("q") or "").strip()[:40]
        if not q: return jsonify([])
        if q.isdigit():
            got = mob_rows("SELECT vnum, CAST(locale_name AS BINARY) AS n, level FROM MOBS WHERE vnum = %s OR CAST(vnum AS CHAR) LIKE %s ORDER BY vnum LIMIT 40", (int(q), q + "%"))
        else:
            got = mob_rows("SELECT vnum, CAST(locale_name AS BINARY) AS n, level FROM MOBS WHERE LOWER(CONVERT(CAST(locale_name AS BINARY) USING utf8mb4)) LIKE %s "
                           "OR locale_name LIKE %s ORDER BY vnum LIMIT 40", ("%" + q.lower() + "%", "%" + q + "%"))
        out = []
        for r in got:
            n = r["n"]
            if isinstance(n, (bytes, bytearray)):
                try: n = bytes(n).decode("utf-8")
                except UnicodeDecodeError: n = bytes(n).decode("cp1250", "replace")
            out.append({"race": int(r["vnum"]), "name": str(n or ""), "level": int(r.get("level") or 0)})
        return jsonify(out)

    @bp.route("/systemy/inne/klepsydra", methods=["POST"])
    @login
    def systems_inne_hourglass():
        if not common.check_csrf() or author(): abort(403)
        def pct(v):
            value = int(round(float(str(v).replace(",", ".")) * 100))
            if value < 0 or value > 10000: raise ValueError
            return value
        try:
            metin, boss = pct(request.form.get("metin") or 0), pct(request.form.get("boss") or 0)
            moby, seen = [], set()
            for m in json.loads(request.form.get("moby") or "[]")[:100]:
                race = int(m["race"])
                if race <= 0 or race in seen: continue
                seen.add(race); moby.append({"race": race, "chance": pct(m["chance"]), "name": str(m.get("name") or "")[:40]})
        except (ValueError, TypeError, KeyError):
            flash("Klepsydra: podaj szanse od 0 do 100 (%).", "error")
            return redirect(url_for("dbeditor.systems_inne"))
        state = load()
        u = state.setdefault("ustawienia", {})
        u["klepsydra_metin"], u["klepsydra_boss"], u["klepsydra_moby"] = metin, boss, moby
        save(state)
        info = "Klepsydra: Metiny %g%%, bossy %g%%, wybranych potworów: %d." % (metin / 100.0, boss / 100.0, len(moby))
        if (state.get("klepsydra") or {}).get("on") and ctx.get("queue_restart"):
            try: ctx["queue_restart"](); common.mark_applied()
            except Exception: pass
            flash(info + " Kanały gry restartują się (ok. minuty).", "success")
        else:
            flash(info + " Zadziała po włączeniu Klepsydry.", "success")
        return redirect(url_for("dbeditor.systems_inne"))

    @bp.route("/systemy/inne/szansa-sakiewki", methods=["POST"])
    @login
    def systems_inne_chance():
        if not common.check_csrf() or author(): abort(403)
        try:
            value = int(round(float((request.form.get("szansa") or "").replace(",", ".")) * 100))
            if value < 0 or value > 10000: raise ValueError
        except ValueError:
            flash("Szansa Sakiewki: podaj liczbę od 0 do 100 (%).", "error")
            return redirect(url_for("dbeditor.systems_inne"))
        state = load()
        u = state.setdefault("ustawienia", {})
        u["sakiewka_szansa"] = value
        # Zawartosc Sakiewki: wagi ulepszen +0..+4 (w %) i wybrane rodzaje KD.
        try:
            wagi = {str(g): max(0, min(1000, int(round(float((request.form.get("w%d" % g) or "0").replace(",", ".")))))) for g in range(5)}
        except ValueError:
            flash("Zawartość Sakiewki: wagi +0…+4 muszą być liczbami.", "error")
            return redirect(url_for("dbeditor.systems_inne"))
        rodzaje = [int(v) for v in request.form.getlist("rodzaj") if v.isdigit() and int(v) in KD_KINDS]
        if not any(wagi.values()) or not rodzaje:
            flash("Zawartość Sakiewki: zaznacz co najmniej jeden rodzaj KD i daj szansę co najmniej jednemu ulepszeniu.", "error")
            return redirect(url_for("dbeditor.systems_inne"))
        u["sakiewka_zawartosc"] = {"wagi": wagi, "rodzaje": rodzaje}
        if (state.get("sakiewka_kd") or {}).get("on"):
            spool = df.spool_dir(); custom = df.read_chest_custom(spool)
            custom[SAKIEWKA] = {"name": "KuzniaSakiewkaKD", "vnum": SAKIEWKA, "type": "", "extras": [], "items": _kd_entries(u)}
            df.write_custom(spool, "chest", df.render_chest_custom(custom, "Kuznia Inne: zawartosc sakiewki"), "Kuznia Inne: zawartosc sakiewki")
        save(state)
        if (state.get("sakiewka_kd") or {}).get("on") and ctx.get("queue_restart"):
            try: ctx["queue_restart"](); common.mark_applied()
            except Exception: pass
            flash("Szansa Sakiewki z Metinów bez KD: %g%%. Kanały gry restartują się (ok. minuty)." % (value / 100.0), "success")
        else:
            flash("Szansa Sakiewki z Metinów bez KD: %g%% – zadziała po włączeniu Sakiewki." % (value / 100.0), "success")
        return redirect(url_for("dbeditor.systems_inne"))

    @bp.route("/systemy/inne/<key>", methods=["POST"])
    @login
    def systems_inne_toggle(key):
        opt = BY_KEY.get(key)
        if opt is None: abort(404)
        if not common.check_csrf() or (author() and not opt.get("autor")): abort(403)
        want = request.form.get("wlacz") == "1"
        state = load()
        if bool((state.get(key) or {}).get("on")) == want:
            return redirect(url_for("dbeditor.systems_inne"))
        try:
            (enable if want else disable)(opt, state)
            save(state)
        except Exception as exc:
            flash("Nie udało się %s „%s”: %s" % ("włączyć" if want else "wyłączyć", opt["name"], exc), "error")
            return redirect(url_for("dbeditor.systems_inne"))
        queue = ctx.get("queue_restart")
        try:
            if queue is None: raise RuntimeError("ten panel nie ma funkcji restartu gry")
            queue()
            try: common.mark_applied()
            except Exception: pass
            # MT2009_NASZE_INNE_POBIERANIE_V2: dbdata tylko przy opcjach zmieniajacych przedmioty, gamedata przy ikonach.
            if not opt["items"]:
                players = "Gracze nic nie pobierają."
            elif key in ("skrzynka_ku", "klepsydra"):
                players = ("Dla graczy: nowe dbdata (przyciski poniżej) i gamedata z ikoną – składasz ją na Przeglądzie "
                           "→ Klient (ROOT), wgrywając swoje gamedata; zip ma ROOT i gamedata, gracze podmieniają oba.")
            else:
                players = "Dla graczy: nowe dbdata (przyciski poniżej)."
            flash("„%s” %s. Kanały gry restartują się (ok. minuty). %s" % (
                      opt["name"], "włączone" if want else "wyłączone – serwer wrócił do stanu sprzed zmiany", players),
                  "success")
        except FileExistsError:
            flash("Zapisano, ale poprzedni restart jeszcze trwa – kliknij Zastosuj za chwilę.", "warning")
        except (OSError, RuntimeError) as exc:
            flash("Zapisano, ale nie zlecono restartu: %s – kliknij Zastosuj." % exc, "warning")
        return redirect(url_for("dbeditor.systems_inne"))
