#!/usr/bin/env python3
"""Kuznia Mocy - instalator: z roznic serwera wzgledem czystego autora wybiera TYLKO zmiany systemow Kuzni
(i systemow pod nia) i zapisuje je jako latki (unified diff) + liste nowych plikow.

Uzycie: zbuduj_latki.py CZYSTY_SRC NASZ_SRC WYJSCIE
Blok zmian (ciag linii +/-) jest brany w calosci, gdy ktorakolwiek jego linia pasuje do KEEP; inaczej
linie '-' wracaja jako kontekst, a '+' sa pomijane (czyli zostaje wersja autora)."""
import difflib, json, re, shutil, sys
from pathlib import Path

KEEP = re.compile(r'MT2009_NASZE_(?!MARMUR)|SEBAN_|Seban[A-Z]|seban_|POLYMORPH_|CustomPoly|custom_horse_polymorph|'
                  r'CUSTOM_GUILD_COMBAT|GetGuildCombatBonus|CustomGuildCombat|custom_guild_combat|GUILD_STATS_REFRESH|GUILD_LOGIN_POINTS|'
                  r'CUSTOM_GUILD_DOUBLE_LOOT|HORSE_BOSS_RESIST|HORSE_NO_BOSS_STONE|HORSE_TRAINING_NO_MONSTER|'
                  r'mission_panel|MISSION_PANEL|QUEST_BONUS_PREVIEW|quest_bonus_preview|plus9|PLUS9|'
                  r'WEEKLY_AFFECT_LOAD_FIX|WEEKLY_TITLE_REWARDS|CUSTOM_WEEKLY_REWARDS|WEEKLY_MONSTER_DIAG|weekly_monster_diag|'
                  r'combat_bonus_diag|COMBAT_DYNAMIC_BONUS_STORAGE|do_diag_dmg|do_diag_potwory|do_quest_bonus_styles')
LIST_LINE = re.compile(r'^\s*(#include\b|ACMD\(|\{\s*"|//)')
# Nowe pliki (nie ma u autora), ktore naleza do Kuzni i systemow pod nia.
NEW_FILES = re.compile(r'^(seban_.*\.h|mission_panel(_impl)?\.h|hunt-data\.inc|master-data\.inc|boss-extra-data\.inc|'
                       r'legacy-boss-data-v15\.inc|quest_bonus_preview(_impl)?\.h|custom_guild_combat_rewards\.h|'
                       r'custom_horse_polymorph_rewards\.h|plus9_origin\.h|weekly_monster_diag\.h|combat_bonus_diag\.h)$')


def lines(p):
    return p.read_text(encoding='latin-1').replace('\r\n', '\n').splitlines(keepends=True)


def filtered(a, b):
    """Wersja 'b' z zachowanymi tylko blokami Kuzni (reszta jak w 'a')."""
    out, kept, dropped = [], 0, 0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            out.extend(a[i1:i2]); continue
        block = a[i1:i2] + b[j1:j2]
        if any(KEEP.search(x) for x in block):
            # Listy jednolinijkowe (#include, ACMD, wpisy tabeli komend): tylko linie Kuzni, reszta jak u autora.
            new = b[j1:j2]
            first = next((x for x in new if x.strip()), '')
            if first and LIST_LINE.match(first) and all(LIST_LINE.match(x) or not x.strip() for x in a[i1:i2]):
                out.extend(a[i1:i2])  # wpisy autora zostaja
                old = set(a[i1:i2])
                # Dopisany blok zlozony z wpisow (#include / ACMD / wpis tabeli + ewentualna tresc do nastepnego wpisu):
                # bierzemy tylko wpisy Kuzni.
                groups, cur = [], []
                for x in new:
                    if LIST_LINE.match(x) and cur: groups.append(cur); cur = []
                    cur.append(x)
                if cur: groups.append(cur)
                for g in groups:
                    if any(KEEP.search(x) for x in g): out.extend(x for x in g if x not in old)
            else:
                out.extend(new)
            kept += 1
        else:
            out.extend(a[i1:i2]); dropped += 1
    return out, kept, dropped


def fixups(name, text, clean):
    """Dopasowanie linii Kuzni do serwera bez innych naszych zmian (czego autor nie ma)."""
    if name == 'seban_rank_rewards.h':
        # Swiezy start u innych: rangi bez bonusow, dopoki nie ustawia ich w panelu (nie nasze progi/wartosci).
        text = text.replace(' out.clear();\n for (int i = 0; i < 16; ++i) {',
                            ' out.clear(); (void)stage; (void)points; return; // instalator: swiezy start bez bonusow\n for (int i = 0; i < 16; ++i) {', 1)
    if name == 'mission_panel_impl.h':
        col = clean / 'playerbot_collector.h'
        if not (col.exists() and 'WarmRefine' in col.read_text(encoding='latin-1')):
            text = text.replace(' playerbot_collector::WarmRefine(ch);\n', '')
    if name == 'playerbot_rank_points.h' and 'RewardStage(' in text and 'int RewardStage(' not in text:
        # Rangi autora (bez naszej przerobki RANK_CUMULATIVE): Kuznia liczy na jego progach (tier).
        text = text.replace('const int stage = Enabled() ? RewardStage(KnownPoints(ch)) : 0;',
                            'const int stage = Enabled() ? TierOf(KnownPoints(ch)) : 0;')
    if name == 'playerbot_rank_points.h' and 'TIERS[tier].bonus[i]' in text:
        # Petla autora (tier) zostala, linia Kuzni liczy stage: oba dostepne.
        text = text.replace('\t\tconst int stage = Enabled() ? RewardStage(KnownPoints(ch)) : 0;\n\t\tif (SebanRank',
                            '\t\tconst int tier = Enabled() ? TierOf(KnownPoints(ch)) : 0;\n'
                            '\t\tconst int stage = Enabled() ? RewardStage(KnownPoints(ch)) : 0;\n\t\tif (SebanRank', 1)
    return text


# Kotwice: gdy latka nie wejdzie (autor przepisal funkcje), blok Kuzni wstawiany jest przed/po stalej linii.
# (plik, poczatek bloku, koniec bloku [nie wlacznie], linia-kotwica, 'przed'|'po')
ANCHORS = [
    ('playerbot_weekly_rank.h', '\t// MT2009_NASZE_RANKING_V1: bonusy tytulow', '\t// One character\'s bonuses', '\tvoid Sync(LPCHARACTER ch', 'przed'),
    ('playerbot_weekly_rank.h', '\t\tif (SebanWeekly::Installed())', None, '\t\tstatic const DWORD types[5] = { AFF_MONSTER', 'przed'),
]


def anchors(name, text):
    out = []
    for f, start, end, anchor, where in ANCHORS:
        if f != name: continue
        L = text.splitlines(keepends=True)
        i = next(k for k, x in enumerate(L) if x.startswith(start))
        j = i + 1 if end is None else next(k for k in range(i, len(L)) if L[k].startswith(end))
        out.append({'anchor': anchor, 'where': where, 'block': ''.join(L[i:j]), 'marker': L[i].strip()})
    return out


def main():
    clean, ours, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    if dst.exists(): shutil.rmtree(dst)
    (dst / 'latki').mkdir(parents=True); (dst / 'nowe').mkdir()
    report = []
    for f in sorted(ours.iterdir()):
        if not f.is_file() or re.search(r'\.(bak|orig|o|d)$|\.bak-|\.orig-', f.name): continue
        c = clean / f.name
        if not c.exists():
            if NEW_FILES.match(f.name):
                (dst / 'nowe' / f.name).write_text(fixups(f.name, f.read_text(encoding='latin-1'), clean), encoding='latin-1')
                report.append('NOWY   %s' % f.name)
            continue
        a, b = lines(c), lines(f)
        if a == b: continue
        res, kept, dropped = filtered(a, b)
        res = fixups(f.name, ''.join(res), clean).splitlines(keepends=True)
        if kept:
            diff = difflib.unified_diff(a, res, 'a/' + f.name, 'b/' + f.name, n=3)
            (dst / 'latki' / (f.name + '.diff')).write_text(''.join(diff), encoding='latin-1')
            an = anchors(f.name, ''.join(res))
            if an:
                (dst / 'kotwice').mkdir(exist_ok=True)
                (dst / 'kotwice' / (f.name + '.json')).write_text(json.dumps(an, indent=1), encoding='latin-1')
            report.append('LATKA  %-32s blokow Kuzni: %d (pominietych innych: %d)' % (f.name, kept, dropped))
    (dst / 'RAPORT.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print('\n'.join(report))


main()
