"""MT2009_PLUS_DB_EDITOR_CUBE_V1: "Wytwarzanie (Seon-Pyeong)" - the recipes of
the old cube window. Only Seon-Pyeong (20091) opens it in this game; the
"Wytwarzanie" window of Kowal, Baek-Go, Heuk-Young and the others is another
system (world.crafting_proto, dbeditor/crafting.py) - their sections in
cube.txt are leftovers the game never shows, so the page lists only the NPCs
whose quest opens the cube window (MT2009_PLUS_DB_EDITOR_CRAFTING_V1).

Where it lives: share/locale/poland/cube.txt in the game image (the package's
file with Seon-Pyeong's recipes, cube.seon_pyeong.txt, appended by the game
Dockerfile). Every core reads it while it boots (cube.cpp Cube_init /
Cube_load) - blocks of
    section / npc <vnum> / item <vnum> <count> (up to 5) /
    reward <vnum> <count> / percent <0-100> / gold <yang> / end
and builds the window's recipe lists from it (Cube_InformationInitialize).
The client asks the server for them ("/cube r_info" -> "cube r_list" /
"cube m_info"), so no client file is involved; its window shows at most five
ingredients per recipe (game.py materialList).

The panel keeps the whole file: unchanged recipes stay byte for byte (EUC-KR
comments included), a changed or new recipe is written as plain tab-separated
lines. It goes into the spool both containers mount:
    <spool>/cube/cube.custom.txt
The game's m2-cube (bin/m2-cube, run by m2-supervise before the cores boot)
puts it in place of the live cube.txt after checking it (structure, numbers,
every item in item_proto, every NPC in mob_proto); a file that fails is not
used and <spool>/cube/status says why. The image's file comes back as
cube/cube.base.txt and the NPCs whose quest opens the window as
cube/cube_npcs.txt; until a game with m2-cube has run, the panel shows its
snapshot (dbeditor/cube.snapshot.txt).

Live reload: the engine has "/reload c" (Cube_init, with the window lists
rebuilt - MT2009_PLUS_DIGI_FIXES_V1), but it reloads only the one core the GM
stands on (six game cores here) and only re-reads the file that core already
has; the panel's file reaches the cores through m2-cube before a boot. So the
recipes go live with "Zastosuj" (restart), like the other file parts.

Backups, history (with undo), "pending" and the game's report use
dropfiles.py's machinery (key "cube"), so /db/apply lists it and the config
export / import (config.py, part "cube") carries and reverts it.
"""
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

from flask import Response, flash, g, redirect, render_template, request, url_for

from dbeditor import dropfiles as df
from dbeditor import tables_common

MARK = "MT2009_PLUS_DB_EDITOR_CUBE_V1"
KEY = "cube"
FOLDER = "cube"
SNAPSHOT = Path(__file__).resolve().parent / "cube.snapshot.txt"   # the image's file, 6 Oct 2026
COMMENT_ENCODING = "euc_kr"
MAX_BYTES = 512 * 1024
MAX_LINE = 254              # Cube_load reads with fgets(one_line, 256): a longer line is cut in two
MAX_MATERIALS = 5           # the client's cube window (game.py: materialList = [[], [], [], [], []])
COUNT_RANGE = (1, 200)      # a stack of the game
PERCENT_RANGE = (0, 100)    # Cube_make: number(1, 100) <= percent
GOLD_RANGE = (0, 2000000000)  # the window's text prints it with %d
NPC_RANGE = (1, 65535)      # CUBE_DATA::npc_vnum is a WORD
VNUM_MAX = 4294967295
RLIST_WARN = 480            # Cube_request_result_list drops a list longer than CHAT_MAX_LEN (512)
HISTORY_KEEP = 300
# The NPCs whose quest opens the cube window (command("cube open")) when the
# game has not published cube_npcs.txt yet: Seon-Pyeong only (6 Oct 2026).
DEFAULT_OPENERS = frozenset({20091})
TOKENS = ("section", "npc", "item", "reward", "percent", "gold", "end")
_LINE_RE = re.compile(r"[^\n]*\n|[^\n]+$")
_SPLIT_RE = re.compile(r"[ \t\r\n]+")


# ----------------------------------------------------------------- parsing ---
def decode(data):
    """The file's bytes -> text whose characters are its bytes (latin-1):
    the numbers are ASCII, the Korean comments stay byte for byte."""
    return data.decode("latin-1") if isinstance(data, (bytes, bytearray)) else (data or "")


def encode(text):
    return decode(text).encode("latin-1")


def tokens(line):
    """The tokens Cube_load sees in one line ([] for a comment / blank)."""
    if line.startswith("#"):
        return []
    return [t for t in _SPLIT_RE.split(line) if t]


def _number(raw):
    """str_to_number: digits (a sign allowed) or None for something else."""
    if raw is None:
        return None
    return int(raw) if re.fullmatch(r"[+-]?\d{1,12}", raw) else None


def new_recipe():
    return {"lead": "", "raw": "", "npcs": [], "items": [], "rewards": [], "percent": 0, "gold": 0,
            "has_gold": False, "has_percent": False, "unknown": [], "bad_numbers": [], "closed": True,
            "line": 0, "dirty": False}


def parse(data):
    """cube.txt -> {"recipes": [recipe], "tail": text, "eol", "problems"}.
    A recipe keeps the text in front of it ("lead": blank lines and its
    comment) and its own lines ("raw"), so an unchanged file is rebuilt byte
    for byte by serialize()."""
    text = decode(data)
    eol = "\r\n" if "\r\n" in text else "\n"
    recipes, problems, lead, cur = [], [], [], None

    def close(recipe, closed):
        recipe["raw"] = "".join(recipe.pop("_lines"))
        recipe["closed"] = closed
        recipes.append(recipe)

    for n, line in enumerate(_LINE_RE.findall(text), 1):
        t = tokens(line)
        word = t[0].lower() if t else ""
        if cur is None:
            if word == "section":
                cur = new_recipe()
                cur.update(lead="".join(lead), line=n, _lines=[line])
                lead = []
                continue
            if word in TOKENS:
                problems.append(f"Linia {n}: „{t[0]}” poza sekcją (przed „section”) – gra by się wyłożyła.")
            lead.append(line)
            continue
        cur["_lines"].append(line)
        if not word:
            continue
        a = _number(t[1]) if len(t) > 1 else None
        b = _number(t[2]) if len(t) > 2 else None
        if word == "section":
            cur["_lines"].pop()
            problems.append(f"Linia {cur['line']}: sekcja bez „end” (następna zaczyna się w linii {n}).")
            close(cur, False)
            cur = new_recipe()
            cur.update(line=n, _lines=[line])
        elif word == "npc":
            cur["npcs"].append(a if a is not None else 0)
            if a is None:
                cur["bad_numbers"].append(n)
        elif word in ("item", "reward"):
            cur["items" if word == "item" else "rewards"].append((a if a is not None else 0, b if b is not None else 0))
            if a is None or b is None:
                cur["bad_numbers"].append(n)
        elif word == "percent":
            cur["percent"], cur["has_percent"] = (a if a is not None else 0), True
            if a is None:
                cur["bad_numbers"].append(n)
        elif word == "gold":
            cur["gold"], cur["has_gold"] = (a if a is not None else 0), True
            if a is None:
                cur["bad_numbers"].append(n)
        elif word == "end":
            close(cur, True)
            cur = None
        else:
            cur["unknown"].append(t[0])
    if cur is not None:
        problems.append(f"Linia {cur['line']}: sekcja bez „end” na końcu pliku.")
        close(cur, False)
    return {"recipes": recipes, "tail": "".join(lead), "eol": eol, "problems": problems}


def render_body(recipe, eol):
    lines = ["section"]
    lines += [f"npc\t{v}" for v in recipe["npcs"]]
    lines += [f"item\t{v}\t{c}" for v, c in recipe["items"]]
    lines += [f"reward\t{v}\t{c}" for v, c in recipe["rewards"]]
    lines.append(f"percent\t{recipe['percent']}")
    if recipe["gold"] or recipe.get("has_gold"):
        lines.append(f"gold\t{recipe['gold']}")
    lines.append("end")
    return "".join(line + eol for line in lines)


def serialize(doc):
    """The doc back to bytes: every untouched recipe as it was read."""
    out = []
    for r in doc["recipes"]:
        out.append(r["lead"])
        out.append(render_body(r, doc["eol"]) if r.get("dirty") else r["raw"])
    out.append(doc["tail"])
    return encode("".join(out))


def sha(data):
    return hashlib.sha256(data).hexdigest()[:16]


# ---------------------------------------------------------------- comments ---
def _lead_split(lead):
    """lead -> (before, own): own = the run of "#" lines right above "section"."""
    lines = _LINE_RE.findall(lead)
    k = len(lines)
    while k and lines[k - 1].startswith("#"):
        k -= 1
    return "".join(lines[:k]), "".join(lines[k:])


def comment_of(recipe):
    """The recipe's own comment as text (the package's are EUC-KR)."""
    _before, own = _lead_split(recipe["lead"])
    parts = []
    for line in _LINE_RE.findall(own):
        raw = line.lstrip("#").strip(" \t\r\n")
        try:
            raw = raw.encode("latin-1").decode(COMMENT_ENCODING)
        except (UnicodeError, ValueError):
            pass
        if raw:
            parts.append(raw)
    return " / ".join(parts)


def set_comment(recipe, text, eol):
    """A new comment line (plain ASCII - the core reads bytes) above the recipe."""
    before, _own = _lead_split(recipe["lead"])
    text = df.ascii_comment(text)
    recipe["lead"] = before + (f"# {text}{eol}" if text else "")


# ----------------------------------------------------------------- editing ---
def npc_of(recipe):
    return recipe["npcs"][0] if recipe["npcs"] else 0


def insert_at(doc, npc, after=None):
    """Where a new recipe goes: after the given one, else after the NPC's
    last recipe (its window lists them in file order), else at the end."""
    if after is not None and 0 <= after < len(doc["recipes"]):
        return after + 1
    last = None
    for i, r in enumerate(doc["recipes"]):
        if npc_of(r) == npc:
            last = i
    return len(doc["recipes"]) if last is None else last + 1


def add_recipe(doc, values, comment="", after=None):
    """values: {npcs, items, rewards, percent, gold} -> index of the new recipe."""
    eol = doc["eol"]
    recipe = new_recipe()
    recipe.update(values, dirty=True, has_gold=bool(values.get("gold")))
    set_comment(recipe, comment, eol)
    recipe["lead"] = eol + recipe["lead"]
    index = insert_at(doc, npc_of(recipe), after)
    if index == len(doc["recipes"]) and doc["recipes"]:
        prev = doc["recipes"][-1]
        body = prev["raw"] if not prev.get("dirty") else render_body(prev, eol)
        if body and not body.endswith("\n") and not doc["tail"]:
            recipe["lead"] = eol + recipe["lead"]
    doc["recipes"].insert(index, recipe)
    return index


def update_recipe(doc, index, values, comment=None):
    recipe = doc["recipes"][index]
    recipe.update(values, dirty=True)
    if comment is not None and comment.strip() != comment_of(recipe):
        set_comment(recipe, comment, doc["eol"])


def delete_recipe(doc, index):
    """Drops the recipe with its own comment; blank lines in front of it go too
    (the next recipe keeps its own)."""
    recipe = doc["recipes"].pop(index)
    before, _own = _lead_split(recipe["lead"])
    if before.strip(" \t\r\n"):
        if index < len(doc["recipes"]):
            doc["recipes"][index]["lead"] = before + doc["recipes"][index]["lead"]
        else:
            doc["tail"] = before + doc["tail"]


def values_of(recipe):
    return {k: recipe[k] for k in ("npcs", "items", "rewards", "percent", "gold")}


# -------------------------------------------------------------- validation ---
def rlist_length(recipes):
    """The length of an NPC's "cube r_list" text (one entry per reward; the
    engine folds +N variants of one reward together - this counts them once)."""
    seen, length = set(), 0
    for r in recipes:
        if len(r["rewards"]) != 1:
            continue
        v, c = r["rewards"][0]
        if v in seen:
            continue
        seen.add(v)
        length += len(f"{v},{c}") + 1
    return max(0, length - 1)


def validate(data_or_doc, known_items=None, known_mobs=None):
    """(errors, warnings) in Polish. errors: what the game would refuse or
    crash on; known_items / known_mobs: the VNUMs the database has (None =
    not checked)."""
    if isinstance(data_or_doc, dict):
        doc, data = data_or_doc, serialize(data_or_doc)
    else:
        data = bytes(data_or_doc)
        doc = parse(data)
    errors, warnings = list(doc["problems"]), []
    if len(data) > MAX_BYTES:
        errors.append(f"Plik jest większy niż {MAX_BYTES // 1024} KB.")
    for n, line in enumerate(_LINE_RE.findall(decode(data)), 1):
        if len(line.rstrip("\r\n")) > MAX_LINE:
            errors.append(f"Linia {n} jest dłuższa niż {MAX_LINE} znaków – gra przeczyta ją w kawałkach.")
            break
    if not doc["recipes"]:
        errors.append("Plik nie ma żadnego przepisu.")
    by_npc = {}
    for i, r in enumerate(doc["recipes"], 1):
        where = f"Przepis {i} (linia {r['line']})" if r["line"] else f"Przepis {i}"
        if r["bad_numbers"]:
            errors.append(f"{where}: w linii {r['bad_numbers'][0]} jest coś, co nie jest liczbą.")
        if not r["npcs"]:
            errors.append(f"{where}: brak NPC („npc”) – gra by się wyłożyła.")
        for v in r["npcs"]:
            if not NPC_RANGE[0] <= v <= NPC_RANGE[1]:
                errors.append(f"{where}: NPC {v} – dozwolone {NPC_RANGE[0]}–{NPC_RANGE[1]}.")
            elif known_mobs is not None and v not in known_mobs and not (v in (65000,65001) and 30099 in known_mobs):
                errors.append(f"{where}: NPC {v} nie istnieje w grze (mob_proto).")
        if len(r["npcs"]) > 1:
            warnings.append(f"{where}: kilku NPC – okno pokaże przepis tylko u pierwszego ({r['npcs'][0]}).")
        if not r["items"]:
            errors.append(f"{where}: brak składników.")
        if len(r["items"]) > MAX_MATERIALS:
            errors.append(f"{where}: {len(r['items'])} składników – okno wytwarzania mieści najwyżej {MAX_MATERIALS}.")
        seen = set()
        for v, c in r["items"] + r["rewards"]:
            if not 1 <= v <= VNUM_MAX:
                errors.append(f"{where}: przedmiot „{v}” to nie numer przedmiotu.")
            elif known_items is not None and v not in known_items:
                errors.append(f"{where}: przedmiotu {v} nie ma w grze (item_proto).")
            if not COUNT_RANGE[0] <= c <= COUNT_RANGE[1]:
                errors.append(f"{where}: ilość {c} przy przedmiocie {v} – dozwolone {COUNT_RANGE[0]}–{COUNT_RANGE[1]}.")
        for v, _c in r["items"]:
            if v in seen:
                warnings.append(f"{where}: przedmiot {v} jest dwa razy wśród składników – gra liczy każdą linię "
                                "osobno (wystarczy większa z ilości). Połącz je w jedną linię.")
            seen.add(v)
        if not r["rewards"]:
            errors.append(f"{where}: brak wyniku („reward”).")
        elif len(r["rewards"]) > 1:
            warnings.append(f"{where}: {len(r['rewards'])} możliwe wyniki – gra losuje jeden, ale okno wytwarzania "
                            "nie pokaże tego przepisu na liście.")
        if not PERCENT_RANGE[0] <= r["percent"] <= PERCENT_RANGE[1]:
            errors.append(f"{where}: szansa {r['percent']}% – dozwolone 0–100.")
        elif r["percent"] == 0:
            warnings.append(f"{where}: szansa 0% – ten przepis nigdy się nie uda.")
        if not GOLD_RANGE[0] <= r["gold"] <= GOLD_RANGE[1]:
            errors.append(f"{where}: koszt {r['gold']} Yang – dozwolone 0–{GOLD_RANGE[1]:,}.".replace(",", " "))
        if r["unknown"]:
            warnings.append(f"{where}: gra pomija nieznane linie: {', '.join(sorted(set(r['unknown']))[:5])}.")
        if r["npcs"]:
            by_npc.setdefault(r["npcs"][0], []).append((i, r))
    for npc, recipes in by_npc.items():
        if rlist_length([r for _i, r in recipes]) > RLIST_WARN:
            warnings.append(f"NPC {npc}: lista wyników jest za długa dla okna (ponad {RLIST_WARN} znaków) – gra "
                            "może jej nie wysłać. Przenieś część przepisów do innego NPC.")
        # Cube_make takes the FIRST recipe whose ingredients are in the window:
        # a later one that needs the same and more is never reached.
        for k, (i, r) in enumerate(recipes):
            need = {}
            for v, c in r["items"]:
                need[v] = max(need.get(v, 0), c)
            for j, earlier in recipes[:k]:
                if earlier["items"] and all(need.get(v, 0) >= c for v, c in earlier["items"]):
                    warnings.append(f"Przepis {i}: nigdy nie zadziała – przepis {j} (wyżej, ten sam NPC) potrzebuje "
                                    "tylko części tych składników i gra wybierze jego.")
                    break
    return errors, warnings


def form_values(form, prefix=""):
    """The recipe form -> (values, comment, errors)."""
    errors, items = [], []

    def number(name, label, low, high, default=None):
        raw = (form.get(prefix + name) or "").strip().replace(" ", "")
        if raw == "" and default is not None:
            return default
        if not re.fullmatch(r"\d{1,12}", raw):
            errors.append(f"{label}: „{raw}” to nie liczba całkowita – wybierz przedmiot z listy (VNUM).")
            return 0
        value = int(raw)
        if not low <= value <= high:
            errors.append(f"{label}: dozwolone {low}–{high}.")
        return value

    npc = number("npc", "NPC", *NPC_RANGE)
    for k in range(MAX_MATERIALS):
        raw = (form.get(f"{prefix}mv_{k}") or "").strip()
        if not raw:
            continue
        v = number(f"mv_{k}", f"Składnik {k + 1}", 1, VNUM_MAX)
        c = number(f"mc_{k}", f"Składnik {k + 1} – ilość", *COUNT_RANGE, default=1)
        items.append((v, c))
    if not items:
        errors.append("Przepis potrzebuje co najmniej jednego składnika.")
    rv = number("reward_v", "Wynik", 1, VNUM_MAX)
    rc = number("reward_c", "Wynik – ilość", *COUNT_RANGE, default=1)
    percent = number("percent", "Szansa %", *PERCENT_RANGE)
    gold = number("gold", "Koszt (Yang)", *GOLD_RANGE, default=0)
    values = {"npcs": [npc], "items": items, "rewards": [(rv, rc)], "percent": percent, "gold": gold}
    return values, (form.get(prefix + "comment") or "").strip(), errors


# ------------------------------------------------------------------- files ---
def register_file():
    """The file in dropfiles' table: custom path, status, backups and the
    "pending" list of /db/apply come with it."""
    df.FILES.setdefault(KEY, (FOLDER, "cube.custom.txt", "status", "Wytwarzanie (cube.txt)"))
    df.BASES.setdefault(KEY, (FOLDER, "cube.base.txt"))


def base_bytes(spool):
    try:
        return df.base_path(spool, KEY).read_bytes(), "game"
    except OSError:
        return SNAPSHOT.read_bytes(), "snapshot"


def current_bytes(spool):
    try:
        data = df.custom_path(spool, KEY).read_bytes()
        if re.search(rb"(?m)^section", data):
            return data, "custom"
    except OSError:
        pass
    return base_bytes(spool)


def history_path(spool):
    return Path(spool) / FOLDER / "history.jsonl"


def read_history(spool, limit=40):
    try:
        lines = history_path(spool).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        e["when"] = datetime.fromtimestamp(int(e.get("time") or 0))
        out.append(e)
        if len(out) >= limit:
            break
    return out


def _log(spool, entry):
    path = history_path(spool)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-(HISTORY_KEEP - 1):]
    except OSError:
        lines = []
    lines.append(json.dumps(entry, ensure_ascii=False))
    try:
        tmp = path.parent / f".history.new{os.getpid()}"
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o664)
        os.replace(tmp, path)
    except OSError:
        pass


def save(spool, data, reason, note=""):
    """Writes the panel's file (None or the image's own bytes: no file) and a
    history line; the backup holds the state before - "Cofnij" restores it."""
    base, _source = base_bytes(spool)
    if data is not None and data == base:
        data = None
    backup = df.write_custom(spool, KEY, data, df.ascii_comment(note or reason))
    _log(spool, {"time": int(datetime.now().timestamp()), "what": reason, "note": note, "backup": backup})
    return backup


# ------------------------------------------------------------------- pages ---
def install(bp, ctx):
    import dbeditor
    register_file()
    df.register(bp)
    tables_common.register(bp)
    rows, game_text, login_required = ctx["rows"], ctx["game_text"], ctx["login_required"]

    def back(npc=None):
        return redirect(url_for("dbeditor.cube", npc=npc) if npc else url_for("dbeditor.cube"))

    def mob_names(vnums):
        if "dbc_mobs" not in g:
            g.dbc_mobs = None
            try:
                g.dbc_mobs = {v: m["name"] for v, m in df.mob_table(rows, game_text).items()}
            except Exception:
                pass
        known = g.dbc_mobs or {}
        return {v: known.get(v) for v in vnums}, g.dbc_mobs is not None

    def item_info(vnums):
        try:
            return df.item_names(rows, game_text, sorted(set(vnums))), True
        except Exception:
            return {}, False

    def known_sets(doc):
        """(items, mobs) the database has for the doc's VNUMs (None: not checked)."""
        items = {v for r in doc["recipes"] for v, _c in r["items"] + r["rewards"]}
        mobs = {v for r in doc["recipes"] for v in r["npcs"]}
        found, ok = item_info(items)
        known_items = set(found) if ok and rows is not None else None
        names, ok = mob_names(mobs)
        known_mobs = {v for v, n in names.items() if n is not None} if ok else None
        return known_items, known_mobs

    def opening_npcs(spool):
        """The NPCs whose quest opens the window (m2-cube publishes them), or None."""
        try:
            text = (Path(spool) / FOLDER / "cube_npcs.txt").read_text(encoding="utf-8")
        except OSError:
            return None
        result = {int(t) for t in text.split() if t.isdigit()}
        if 30099 in result:
            result.update((65000,65001))
        return result

    def decorate(doc, names):
        out = []
        for i, r in enumerate(doc["recipes"]):
            def item(v, c):
                known = names.get(v)
                return {"vnum": v, "count": c, "name": known["name"] if known else "NIEZNANY PRZEDMIOT",
                        "bad": known is None and bool(names), "icon": df.icon_url(v)}
            out.append({"index": i, "npc": npc_of(r), "npcs": r["npcs"],
                        "mats": [item(v, c) for v, c in r["items"]],
                        "rewards": [item(v, c) for v, c in r["rewards"]],
                        "percent": r["percent"], "gold": r["gold"], "comment": comment_of(r),
                        "closed": r["closed"]})
        return out

    def page_state():
        spool = df.spool_dir()
        data, source = current_bytes(spool)
        doc = parse(data)
        return spool, data, source, doc

    @bp.route("/wytwarzanie")
    @login_required
    def cube():
        spool, data, source, doc = page_state()
        _base, base_source = base_bytes(spool)
        names, _ok = item_info([v for r in doc["recipes"] for v, _c in r["items"] + r["rewards"]])
        recipes = decorate(doc, names)
        npc_vnums = []
        for r in recipes:
            if r["npc"] not in npc_vnums:
                npc_vnums.append(r["npc"])
        # Only the NPCs whose quest opens the cube window (m2-cube's
        # cube_npcs.txt, Seon-Pyeong when the game has not said): the other
        # crafting NPCs use the "Wytwarzanie przedmiotów" window (crafting.py),
        # their cube.txt sections are never shown in game.
        openers = opening_npcs(spool) or set(DEFAULT_OPENERS)
        hidden = sum(1 for r in recipes if r["npc"] not in openers)
        npc_vnums = [v for v in npc_vnums if v in openers] + sorted(v for v in openers if v not in npc_vnums)
        mobs, _ok = mob_names(npc_vnums)
        npcs = [{"vnum": v, "name": {65000: "Ukrainka - Alchemia", 65001: "Ukrainka - Zmianki"}.get(v) or mobs.get(v) or f"NPC {v}", "count": sum(1 for r in recipes if r["npc"] == v),
                 "opens": True} for v in npc_vnums]
        try:
            selected = int(request.args.get("npc", ""))
        except ValueError:
            selected = npc_vnums[0] if npc_vnums else 0
        known_items, known_mobs = known_sets(doc)
        errors, warnings = validate(doc, known_items, known_mobs)
        state = df.live_state(spool, KEY)
        return render_template("dbeditor/cube.html", npcs=npcs, selected=selected,
                               selected_name=mobs.get(selected) or mob_names([selected])[0].get(selected) or f"NPC {selected}",
                               recipes=[r for r in recipes if r["npc"] == selected], total=len(recipes),
                               source=source, base_source=base_source, errors=errors, warnings=warnings,
                               status=state, pending=[1] if state["pending"] else [],
                               backups=df.list_backups(spool, [KEY], 20), history=read_history(spool),
                               openers=openers, hidden=hidden, sha=sha(data), csrf=df.csrf_token(), num=tables_common.num_text)

    def form_page(doc, data, index=None, values=None, comment="", after=None, raw=None):
        names, _ok = item_info([v for v, _c in (values or {}).get("items", []) + (values or {}).get("rewards", [])])
        npc = (values or {}).get("npcs", [0])[0] if values else 0
        mobs, _ok = mob_names([r for r in {npc_of(x) for x in doc["recipes"]}] + [npc])
        cube_npcs = sorted(opening_npcs(df.spool_dir()) or DEFAULT_OPENERS)
        return render_template("dbeditor/cube_edit.html", index=index, values=values, comment=comment, after=after,
                               raw=raw or {}, names=names, icon=df.icon_url, slots=MAX_MATERIALS,
                               npc=npc, npc_name=mobs.get(npc), cube_npcs=[(v, mobs.get(v) or f"NPC {v}") for v in cube_npcs],
                               sha=sha(data), csrf=df.csrf_token(), count_max=COUNT_RANGE[1], gold_max=GOLD_RANGE[1])

    @bp.get("/wytwarzanie/przepis/<int:index>")
    @login_required
    def cube_recipe(index):
        _spool, data, _source, doc = page_state()
        if not 0 <= index < len(doc["recipes"]):
            flash("Nie ma takiego przepisu (plik zmienił się w międzyczasie?).", "error")
            return back()
        r = doc["recipes"][index]
        return form_page(doc, data, index=index, values=values_of(r), comment=comment_of(r))

    @bp.get("/wytwarzanie/nowy")
    @login_required
    def cube_new():
        _spool, data, _source, doc = page_state()
        copy = request.args.get("kopia", "")
        if copy.isdigit() and int(copy) < len(doc["recipes"]):
            r = doc["recipes"][int(copy)]
            return form_page(doc, data, values=values_of(r), comment=comment_of(r), after=int(copy))
        try:
            npc = int(request.args.get("npc", "0"))
        except ValueError:
            npc = 0
        values = {"npcs": [npc] if npc else [0], "items": [], "rewards": [], "percent": 100, "gold": 0}
        return form_page(doc, data, values=values)

    @bp.post("/wytwarzanie")
    @login_required
    def cube_save():
        spool = df.spool_dir()
        form = request.form
        if not df.csrf_ok(form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return back()
        action = form.get("action", "save")
        note = (form.get("note") or "").strip()[:120]
        try:
            if action == "reset":
                save(spool, None, "przywrócono przepisy z obrazu gry", note)
                flash("Wytwarzanie wróci do przepisów z obrazu gry po restarcie (Zastosuj).", "success")
                return back()
            if action in ("restore", "undo"):
                name = form.get("name", "")
                if action == "undo":
                    backups = df.list_backups(spool, [KEY], 1)
                    if not backups:
                        flash("Nie ma czego cofać.", "info")
                        return back()
                    name = backups[0]["name"]
                path = df.backup_file(spool, KEY, name)
                if path is None:
                    raise ValueError("Nie ma takiej kopii.")
                raw = path.read_bytes()
                save(spool, None if raw.startswith(df.NO_CHANGES_MARK) else raw,
                     f"cofnięto do stanu sprzed zapisu {name.rsplit('.', 2)[-2]}", note)
                flash("Przywrócono wcześniejsze przepisy. Działają po restarcie (Zastosuj).", "success")
                return back()
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się: {exc}", "error")
            return back()

        data, _source = current_bytes(spool)
        if form.get("sha") != sha(data):
            flash("Przepisy zmieniły się w międzyczasie (inny zapis albo nowa wersja gry) – odśwież stronę i "
                  "wprowadź zmiany jeszcze raz.", "error")
            return back()
        doc = parse(data)
        index = form.get("index", "")
        index = int(index) if index.isdigit() and int(index) < len(doc["recipes"]) else None
        if action == "delete":
            if index is None:
                flash("Nie ma takiego przepisu.", "error")
                return back()
            npc = npc_of(doc["recipes"][index])
            what = "usunięto przepis: " + describe(doc["recipes"][index], item_info)
            delete_recipe(doc, index)
        else:
            values, comment, errors = form_values(form)
            if errors:
                for e in errors[:12]:
                    flash(e, "error")
                flash("Nic nie zapisano – popraw przepis.", "error")
                _s, d2, _src, doc2 = page_state()
                return form_page(doc2, d2, index=index, values=values, comment=comment,
                                 after=int(form["after"]) if form.get("after", "").isdigit() else None, raw=form)
            npc = values["npcs"][0]
            if index is None:
                after = form.get("after", "")
                after = int(after) if after.isdigit() else None
                if after is not None and npc_of(doc["recipes"][min(after, len(doc["recipes"]) - 1)]) != npc:
                    after = None
                index = add_recipe(doc, values, comment, after)
                what = "nowy przepis: " + describe(doc["recipes"][index], item_info)
            else:
                if values_of(doc["recipes"][index]) == values and comment == comment_of(doc["recipes"][index]):
                    flash("Nic się nie zmieniło.", "info")
                    return back(npc)
                update_recipe(doc, index, values, comment)
                what = "zmiana przepisu: " + describe(doc["recipes"][index], item_info)
        new = serialize(doc)
        known_items, known_mobs = known_sets(doc)
        errors, _warnings = validate(new, known_items, known_mobs)
        if errors:
            for e in errors[:12]:
                flash(e, "error")
            flash("Nic nie zapisano – gra nie wczytałaby takich przepisów.", "error")
            if action != "delete":
                _s, d2, _src, doc2 = page_state()
                return form_page(doc2, d2, index=None if form.get("index", "") == "" else index, values=values,
                                 comment=comment, raw=form)
            return back(npc)
        try:
            save(spool, new, what, note)
        except OSError as exc:
            flash(f"Nie udało się zapisać pliku w wolumenie spool: {exc}", "error")
            return back(npc)
        flash(f"Zapisano ({what}). Gra wczyta przepisy po restarcie (Zastosuj).", "success")
        return back(npc)

    @bp.get("/wytwarzanie/plik")
    @login_required
    def cube_file():
        data, _source = current_bytes(df.spool_dir())
        return Response(data, mimetype="text/plain; charset=euc-kr",
                        headers={"Content-Disposition": "attachment; filename=cube.txt"})

    dbeditor.add_section("dbeditor.cube", "⚗️", "Wytwarzanie (Seon-Pyeong)",
                         "okno kostki (cube) u Seon-Pyeong: składniki, wynik, szansa, koszt")


def describe(recipe, item_info=None):
    """'Miecz+9 x1 + ... -> Miecz Trytona+0 (NPC 20091)' for the history."""
    names = {}
    if item_info is not None:
        names, _ok = item_info([v for v, _c in recipe["items"] + recipe["rewards"]])

    def one(v, c):
        name = names.get(v, {}).get("name") if names.get(v) else str(v)
        return f"{name}" + (f" x{c}" if c != 1 else "")
    reward = ", ".join(one(v, c) for v, c in recipe["rewards"]) or "?"
    return f"{reward} u NPC {npc_of(recipe)} ({len(recipe['items'])} skł., {recipe['percent']}%)"
