#!/usr/bin/env python3
"""Kuznia Mocy: z ROOT autora Kuzni (root.index + root.data) zbiera pliki klienta, ktore instalator doklada
cudzemu ROOT, jesli ich brakuje: cale moduly, grafiki okna misji i podpiecia (hooks.json, format jak kotwice).
Uruchamiane w obrazie seban-panel:  python spakuj_klient.py KATALOG_ROOT WYJSCIE"""
import json, os, re, sys
sys.path.insert(0, '/app')
from m2clientpack import eterpack as ep

MODULES = ['uimissionpanel', 'uiquestbonuspreview', 'uiqueststyle', 'gamefont', 'custom_window_theme',
           'customguildtooltip', 'customrewardtooltip','rankpoints', 'rankbadges', 'uiweeklyrank', 'uiminigameutil', 'warpsafe']
GFX = re.compile(r'custom_windows/final/|custom_windows/mission_background|ranktitles/')
GAME_DEFS = ['__MissionPanel', '__QuestPreviewBegin', '__QuestPreviewRow', '__QuestPreviewEnd',
             '__QuestStyleBegin', '__QuestStyleIndex', '__QuestStyleEnd']
GAME_CMDS = re.compile(r'self\.(__MissionPanel|__QuestPreview\w+|__QuestStyle\w+)\b')


def norm(n):
    n = (n.decode('latin-1') if isinstance(n, bytes) else n).replace('\\', '/').lower()
    return n[3:] if n.startswith('d:/') else n


def lines_of(raw):
    return raw.decode('latin-1').replace('\r\n', '\n').splitlines(keepends=True)


def def_block(L, name):
    i = next(k for k, x in enumerate(L) if x.startswith('\tdef %s(' % name))
    j = i + 1
    while j < len(L) and not L[j].startswith('\tdef ') and not (L[j].strip() and not L[j].startswith('\t\t')):
        j += 1
    return ''.join(L[i:j])


src, dst = sys.argv[1], sys.argv[2]
ver, ents = ep.read_index_bytes(open(src + '/root.index', 'rb').read())
data = open(src + '/root.data', 'rb').read()
by = {norm(e.name): e for e in ents}
py = {k.split('/')[-1]: k for k in by if k.endswith('.py')}
read = lambda name: ep.read_entry(data, by[name])
os.makedirs(dst + '/pliki', exist_ok=True)
files = {}
for m in MODULES:
    files[py[m + '.py']] = read(py[m + '.py'])
for k in by:
    if GFX.search(k): files[k] = read(k)
for k, raw in files.items():
    p = os.path.join(dst, 'pliki', k)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(raw)

g = lines_of(read(py['game.py']))
cmds = ''.join(x for x in g if GAME_CMDS.search(x) and x.lstrip().startswith('"'))
hooks = {
    'game.py': [
        {'marker': '"mission_panel":', 'anchor': '\t\t\t"quests"', 'where': 'po',
         'block': '\t\t\t"mission_panel": (lambda: __import__("uimissionpanel").ToggleWindow(), None),\n'},
        {'marker': 'def __MissionPanel(', 'anchor': '\tdef __ServerCommand_Build(self):', 'where': 'przed',
         'block': ''.join(def_block(g, n) for n in GAME_DEFS)},
        {'marker': '"MP": self.__MissionPanel', 'anchor': '\t\tserverCommandList={', 'where': 'po', 'block': cmds},
        {'marker': '__import__("uimissionpanel").DestroyWindow()', 'anchor': '\t\t__import__("uiweeklyrank").DestroyWindow()',
         'where': 'po', 'block': '\t\t__import__("uimissionpanel").DestroyWindow()\n'},
        # Odznaki rang przy nicku: rysowanie co klatke (czysty klient tego nie ma).
        {'marker': 'rankbadges").Update', 'anchor': '\t\ttextTail.ArrangeTextTail()', 'where': 'po',
         'block': '\t\t__import__("rankbadges").Update(self.__IsShowName(), getattr(self, "PickingCharacterIndex", 0), self.targetBoard.GetTargetVID()) # RANK_SIDE_GOTHIC_V1\n',
         'need': 'def __IsShowName('},
        {'marker': '__import__("uiquestbonuspreview").Reset()', 'anchor': '\t\tself.__ServerCommand_Build()', 'where': 'przed',
         'block': '\t\t__import__("uiquestbonuspreview").Reset()\n\t\t__import__("uiqueststyle").Reset()\n'},
    ],
    'uitooltip.py': [
        {'marker': 'import customrewardtooltip', 'anchor': 'import ', 'where': 'przed', 'block': 'import customrewardtooltip\n'},
        {'marker': 'customrewardtooltip.append_horse(', 'where': 'po', 'need': 'SKILL_INDEX_RIDING',
         'anchor': '\t\t\tself.AppendSupportSkillDefaultData(skillIndex, skillGrade, skillLevel, 30)',
         'block': '\t\t\tcustomrewardtooltip.append_horse(self, skillGrade, skillLevel)\n'},
        {'marker': 'customrewardtooltip.append_poly(', 'where': 'po',
         'anchor': '\t\t\tself.AppendSupportSkillDefaultData(skillIndex, skillGrade, skillLevel, 40)',
         'block': '\t\t\tcustomrewardtooltip.append_poly(self, skillGrade, skillLevel)\n'},
        # Klient bez osobnej galezi polimorfii: cala galaz przed galezia konia (ten sam lancuch elif).
        {'marker': 'customrewardtooltip.append_poly(', 'where': 'przed',
         'anchor': '\t\telif player.SKILL_INDEX_RIDING == skillIndex:',
         'block': '\t\telif skillIndex == 129: # SKILL_POLYMORPH (Kuznia Mocy)\n'
                  '\t\t\tself.AppendSupportSkillDefaultData(skillIndex, skillGrade, skillLevel, 40)\n'
                  '\t\t\tcustomrewardtooltip.append_poly(self, skillGrade, skillLevel)\n\n'},
    ],
    'keybind.py': [
        {'marker': "('mission_panel',", 'anchor': "\t\t('quests',", 'where': 'po',
         'block': "\t\t('mission_panel', 'Panel Misji', ((CTRL, 'DIK_N'),), False),\n"},
    ],
    'uiguild.py': [
        {'marker': 'customguildtooltip', 'anchor': '\t\t\tpage.guildLevelSlot = page.GetChild("GuildLevelValue")', 'where': 'po',
         'block': '\t\t\timport customguildtooltip\n\t\t\tpage.guildBonusHover = customguildtooltip.GuildBonusHover(page, page.GetChild("GuildLevelSlot"))\n'},
    ],
}
json.dump(hooks, open(dst + '/hooks.json', 'w', encoding='latin-1'), indent=1)
# Dokladne nazwy wpisow z ROOT autora (np. "d:/ymir work/..." - klient szuka grafik pod ta nazwa).
raw = {}
for e in ents:
    n = norm(e.name)
    if n in files:
        r = e.name.decode('latin-1') if isinstance(e.name, bytes) else e.name
        if n not in raw or r.lower().startswith('d:/'): raw[n] = r
json.dump(raw, open(dst + '/nazwy.json', 'w', encoding='latin-1'), indent=1)
print('modulow: %d, grafik: %d, podpiec: %d' % (len(MODULES), len(files) - len(MODULES), sum(len(v) for v in hooks.values())))
print('komendy MP/QP/QS w game.py: %d' % cmds.count('\n'))
