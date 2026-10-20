"""MT2009_NASZE_KLIENT_Z_SERWERA_V1: jednorazowa wtyczka ROOT (sebansystems.py).

Serwer (seban_client_sync.h) wysyla przy wejsciu do gry i po "Zastosuj" w panelu tabele systemow:
  SebanSys B | SebanSys L <kon|poli> <poziom> p:v,p:v | SebanSys E
p to numer POINT_* z silnika; 1000 = odpornosc na bossy (promile), 1001 = czas przemiany (s).
Klient pokazuje te wartosci w opisach konia i polimorfii, wiec zmiana bonusow w panelu nie wymaga
nowego ROOT. Nowy ROOT jest potrzebny tylko przy nowej grafice (np. ikony poziomow konia) albo po
aktualizacji klienta autora, ktora nadpisze te pliki.
"""
import hashlib

MARK = b'# SEBAN_SYSTEMS_V1'
SEAL = b'# SEBAN_SYSTEMS_SHA256 '
POLY_HOOK = b'# SEBAN_SYSTEMS_POLY_HOOK_V1'
GAME_HOOK = b'MT2009_NASZE_KLIENT_Z_SERWERA_V1'
EXTRA_LABELS = {
    178: ('Moc żywiołu: błyskawica', '%'), 179: ('Moc żywiołu: ogień', '%'), 180: ('Moc żywiołu: lód', '%'),
    181: ('Moc żywiołu: wiatr', '%'), 182: ('Moc żywiołu: ziemia', '%'), 183: ('Moc żywiołu: mrok', '%'),
}


def _lit(text):
    return "'" + ''.join('\\x%02x' % b for b in text.encode('cp1250', 'replace')) + "'"


def point_labels():
    """Wszystkie bonusy, ktore panel pozwala wybrac (numer POINT_* -> (nazwa, jednostka))."""
    from dbeditor.items import POINT_LABELS, TECHNICAL_POINTS
    out = {p: v for p, v in POINT_LABELS.items() if p and p not in TECHNICAL_POINTS}
    out.update(EXTRA_LABELS)
    return out


def seal(raw):
    return raw + SEAL + hashlib.sha256(raw).hexdigest().encode('ascii') + b'\n'


def verify(raw):
    before, sep, digest = raw.rpartition(SEAL)
    return bool(sep and before.startswith(MARK) and digest == hashlib.sha256(before).hexdigest().encode('ascii') + b'\n')


def module():
    names = ',\n'.join('    %d: (%s, %s)' % (p, _lit(n), _lit(u.replace('‰', '%'))) for p, (n, u) in sorted(point_labels().items()))
    src = '''# SEBAN_SYSTEMS_V1; MT2009_NASZE_KLIENT_Z_SERWERA_V1 - wartosci systemow przychodza z serwera.
NAMES = {
%s,
}
DIVIDE = {142: 10, 1000: 10}
CLASSES = (59, 60, 61, 62)
ELEMENTS = (178, 179, 180, 181, 182, 183)
DATA = {}
_stage = [None]

def OnCommand(*args):
    try:
        op = args[0] if args else ''
        if op == 'B':
            _stage[0] = {}
        elif op == 'L' and _stage[0] is not None and len(args) >= 4:
            row = _stage[0].setdefault(args[1], {}).setdefault(int(args[2]), {})
            if args[3] != '-':
                for part in args[3].split(','):
                    p, v = part.split(':')
                    row[int(p)] = row.get(int(p), 0) + int(v)
        elif op == 'E' and _stage[0] is not None:
            DATA.clear()
            DATA.update(_stage[0])
            _stage[0] = None
            _rank_thresholds()
    except (ValueError, IndexError):
        _stage[0] = None

class _Commands(object):
    # stringCommander.SAFE_RegisterCallBack wymaga metody obiektu (im_func), nie zwyklej funkcji.
    def OnCommand(self, *args):
        OnCommand(*args)

COMMANDS = _Commands()

def values(system, level):
    table = DATA.get(system)
    if table is None:
        return None
    return dict(table.get(int(level), {}))

def _rank_thresholds():
    # progi rang z serwera -> rankpoints.py (tytul i "Nastepna ranga" w oknie postaci)
    table = DATA.get('rangi')
    if not table:
        return
    try:
        import rankpoints
        for tier, row in table.items():
            if tier in rankpoints.TIERS and 1002 in row:
                rankpoints.TIERS[tier] = (row[1002],) + tuple(rankpoints.TIERS[tier][1:])
        # Tyle progow, ile rang (np. 8 u autora serwera) - nie na sztywno 12 (zera = indeks poza REWARD_NAMES).
        count = len(getattr(rankpoints, 'REWARD_NAMES', ())) or len(table)
        tiers = sorted(t for t in table if 1 <= t <= count)
        rankpoints.REWARD_THRESHOLDS = tuple(table[t].get(1002, 0) for t in tiers)
    except Exception:
        pass

def append_rank(tip, total):
    table = DATA.get('rangi')
    if table is None:
        return False
    add = getattr(tip, 'AutoAppendTextLine', None) or tip.AppendTextLine
    green = getattr(tip, 'POSITIVE_COLOR', 0xff6cff6c)
    red = getattr(tip, 'NEGATIVE_COLOR', 0xffff6666)
    stage = 0
    if total >= 0:
        for tier, row in table.items():
            if total >= row.get(1002, 0) and tier > stage:
                stage = tier
    now = dict(table.get(stage, {})) if stage else {}
    add('Obecne bonusy rangi:', green)
    if [x for k, x in now.items() if k != 1002 and x]:
        append_points(tip, now, green, add)
    else:
        add('Brak bonusow rangi', green)
    following = table.get(stage + 1)
    if following is not None:
        try:
            import rankpoints
            name = rankpoints.REWARD_NAMES[stage]
        except Exception:
            name = 'Ranga %%d' %% (stage + 1)
        add('Nastepna: %%s (%%d pkt)' %% (name, following.get(1002, 0)), red)
        delta = dict((k, following.get(k, 0) - now.get(k, 0)) for k in set(now.keys()) | set(following.keys()) if k != 1002)
        delta = dict((k, x) for k, x in delta.items() if x > 0)
        if delta:
            append_points(tip, delta, red, add)
    else:
        add('Osiagnieto najwyzsza range')
    return True

def _lines(values):
    v = dict(values)
    v.pop(1001, None)
    v.pop(1002, None)
    out = []
    for keys, label, unit in ((CLASSES, 'Odpornosc na kazda z 4 klas', '%%'), ((54, 55, 56, 57), 'Silny na kazda z 4 klas', '%%'),
                              (ELEMENTS, 'Silny na kazdy z 6 zywiolow', '%%'), ((12, 13, 14, 15), 'SIL / WIT / ZR / INT po', '')):
        got = [v.get(k, 0) for k in keys]
        if got[0] and got.count(got[0]) == len(got):
            for k in keys:
                v.pop(k)
            out.append((label, got[0], unit, 1))
    for p in sorted(v.keys()):
        if not v[p]:
            continue
        if p == 1000:
            out.append(('Odpornosc na bossy', v[p], '%%', 10))
        else:
            name, unit = NAMES.get(p, ('Bonus #%%d' %% p, ''))
            out.append((name, v[p], unit, DIVIDE.get(p, 1)))
    return out

def _texts(values):
    out = []
    for label, value, unit, div in _lines(values):
        text = str(value) if div == 1 else ('%%g' %% (value / float(div)))
        out.append('%%s %%s%%s%%s' %% (label, '+' if value > 0 else '', text, unit))
    return out

def weekly_short(cat, place):
    row = values('tydzien', (int(cat) - 1) * 3 + int(place))
    if row is None:
        return None
    return ', '.join(_texts(row)) or 'bez bonusu'

def weekly_long(cat, original):
    if DATA.get('tydzien') is None:
        return original
    parts = []
    for place in (1, 2, 3):
        parts.append('%%s: %%s' %% ('I' * place, weekly_short(cat, place)))
    return ' | '.join(parts)

def append_points(tip, values, color, add=None):
    add = add or tip.AppendTextLine
    for label, value, unit, div in _lines(values):
        text = str(value) if div == 1 else ('%%g' %% (value / float(div)))
        add('%%s: %%s%%s%%s' %% (label, '+' if value > 0 else '', text, unit), color)

def append_next(tip, current, following, title, color):
    following = following or {}
    keys = set(current.keys()) | set(following.keys())
    delta = dict((k, following.get(k, 0) - current.get(k, 0)) for k in keys if k != 1001)
    tip.AppendSpace(5)
    tip.AppendTextLine(title, color)
    if [x for x in delta.values() if x]:
        append_points(tip, delta, color)
    else:
        tip.AppendTextLine('Bez wzrostu bonusow na tym poziomie', color)

def append_poly(tip, grade, rawlevel):
    level = 40 if grade >= 3 else max(0, int(rawlevel) + (19 if grade == 1 else 29 if grade == 2 else 0))
    now = values('poli', level)
    if now is None:
        return False
    tip.AppendSpace(5)
    tip.AppendTextLine('Dziala tylko podczas przemiany', tip.NORMAL_COLOR)
    append_points(tip, now, tip.POSITIVE_COLOR)
    seconds = now.get(1001, 0)
    if seconds:
        if seconds %% 60:
            tip.AppendTextLine('Czas przemiany: %%d s' %% seconds, tip.POSITIVE_COLOR)
        else:
            tip.AppendTextLine('Czas przemiany: %%d minut' %% (seconds // 60), tip.POSITIVE_COLOR)
    if level < 40:
        append_next(tip, now, values('poli', level + 1), 'Bonus nastepnego poziomu:', tip.NEGATIVE_COLOR)
    return True
''' % names
    return seal(src.encode('ascii'))


def _nl(raw):
    return b'\r\n' if b'\r\n' in raw else b'\n'


def patch_tooltip(raw):
    """customrewardtooltip.py: append_poly najpierw pyta wtyczke; bez danych z serwera - stary opis."""
    head = b'def append_poly(tip, grade, rawlevel):'
    if raw.count(head) != 1:
        raise ValueError('Konflikt customrewardtooltip.py: brak znanej funkcji polimorfii.')
    nl = _nl(raw)
    hook = nl.join((head, b'    ' + POLY_HOOK, b'    import sebansystems',
                    b'    if sebansystems.append_poly(tip,grade,rawlevel): return'))
    if POLY_HOOK in raw:
        if raw.count(hook) != 1:
            raise ValueError('Konflikt zmienionego hooka polimorfii w customrewardtooltip.py.')
        return raw
    return raw.replace(head, hook, 1)


RANK_LOOK = b'# SEBAN_SYSTEMS_RANK_LOOK_V2'
RANK_SPOOL = '/opt/m2spool/systems/rangi'


def _rank_cfg():
    import json, os
    # MT2009_NASZE_RANGI_SWIEZE_V1: zawsze wyglad z panelu (projekt albo rangi gry tego serwera), zeby klient
    # pokazywal to samo co panel - takze po podmianie rankpoints.py na wersje Kuzni.
    from dbeditor import systems_rank
    path = os.path.join(RANK_SPOOL, 'draft.json')
    if os.path.exists(path):
        return systems_rank.validate(json.loads(open(path, 'rb').read()))
    return systems_rank.defaults()


def rank_needed():
    """Wpisy ROOT, ktore panel moze podmienic dla wlasnych rang (odznaki)."""
    cfg = _rank_cfg()
    if not cfg:
        return set()
    return {'rankbadges.py'} | {'ranktitles/rank%02d.tga' % i for i, r in enumerate(cfg['ranks'], 1) if r['badge']}


def _cp(text):
    return "'" + ''.join(c if 32 <= ord(c) < 127 and c not in "'\\" else ''.join('\\x%02x' % b for b in c.encode('cp1250')) for c in text) + "'"


def rank_look(files):
    """rankpoints.py (TIERS, REWARD_NAMES, REWARD_THRESHOLDS) i rankbadges.py (SIZES) + odznaki TGA wlasnych rang."""
    cfg = _rank_cfg()
    if not cfg or 'rankpoints.py' not in files or 'rankbadges.py' not in files:
        return {}
    import re
    from dbeditor import systems_rank
    out = {}
    rp = files['rankpoints.py']; nl = _nl(rp)
    m = re.search(rb'\nTIERS = \{\r?\n.*?\r?\n\}\r?\n', rp, re.S)
    if not m or rp.count(b'\nREWARD_THRESHOLDS = (') != 1 or rp.count(b'\nREWARD_NAMES = (') != 1:
        raise ValueError('Konflikt rankpoints.py: brak znanej tabeli rang.')
    rows = []
    for i, r in enumerate(cfg['ranks'], 1):
        c = r['color']; rgb = (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
        rows.append('\t%d: (%d, %s, %s, (%d, %d, %d)),' % ((i, cfg['from'][i - 1], _cp(r['name']), _cp(r['name'])) + rgb))
    block = nl + nl.join([b'TIERS = {'] + [x.encode('ascii') for x in rows] + [b'}']) + nl
    rp = rp[:m.start()] + block + rp[m.end():]
    thr = b'\nREWARD_THRESHOLDS = (' + ', '.join(str(x) for x in cfg['from']).encode() + b',)'
    nms = b'\nREWARD_NAMES = (' + ', '.join(_cp(r['name']) for r in cfg['ranks']).encode('ascii') + b',)'
    rp = re.sub(rb'\nREWARD_THRESHOLDS = \([^\n]*', lambda _m: thr, rp, count=1)  # lambda: \x.. w nazwach to nie kod regex
    rp = re.sub(rb'\nREWARD_NAMES = \([^\n]*', lambda _m: nms, rp, count=1)
    out['rankpoints.py'] = rp
    rb = files['rankbadges.py']
    sm = re.search(rb'\nSIZES = \{[^\n]*\}', rb)
    if not sm: raise ValueError('Konflikt rankbadges.py: brak tabeli rozmiarow odznak.')
    old = dict((int(a), (int(b), int(c))) for a, b, c in re.findall(rb'(\d+): \((\d+), (\d+)\)', sm.group(0)))
    from m2clientpack import kuznia_dodatki
    fresh = kuznia_dodatki.fresh()
    sizes = {}
    for i, r in enumerate(cfg['ranks'], 1):
        if r['badge']:
            blob = open(RANK_SPOOL + '/assets/' + r['badge'], 'rb').read()
            sizes[i] = systems_rank.badge_size(blob); out['ranktitles/rank%02d.tga' % i] = blob
        elif i in old and not fresh:
            sizes[i] = old[i]
        elif fresh:
            continue  # MT2009_NASZE_RANGI_TEKST_V1: u innych bez odznaki z panelu - napis z nazwa (nie obrazki autora Kuzni)
        else:
            raise ValueError('Ranga %d („%s”): wgraj odznakę TGA (nowa ranga nie ma grafiki w grze).' % (i, r['name']))
    out['rankbadges.py'] = rb[:sm.start()] + b'\nSIZES = {' + ', '.join('%d: (%d, %d)' % (i, w, h) for i, (w, h) in sorted(sizes.items())).encode() + b'}  ' + RANK_LOOK + rb[sm.end():]
    return out


MISSIONS_LOOK = b'# MT2009_NASZE_MISJE_CZYTELNOSC_V2'
MISSIONS_LOOK_OLD = b'# MT2009_NASZE_MISJE_CZYTELNOSC_V1'
MISSIONS_BLOCK = r'''
# MT2009_NASZE_MISJE_CZYTELNOSC_V2: czytelniejsze okno Ctrl+N (ciemne, wieksze napisy bez podkladow,
# tytul na srodku gornego paska, licznik etapow miedzy strzalkami) i model potwora obrocony przodem.
_SEBAN_S=1.0  # MT2009_NASZE_MISJE_ROZMIAR_V1: pelny rozmiar (zmniejszanie okna wycofane)
def _SebanF(n):return max(12,int(round(n*_SEBAN_S)))
def _SebanScale(self):
    S=_SEBAN_S
    self.width=int(860*S);self.height=int(660*S);self.SetSize(self.width,self.height)
    try:self.skin.SetScale(S,S)
    except Exception:pass
    els=[self.title,self.closeButton,self.left,self.selector,self.previous,self.next,self.number,self.middle,self.name,self.progress,
         self.target,self.targetName,self.location,self.level,self.status,self.bonuses,self.rewardScroll,self.startButton,self.bioTeleport,self.bioTimer]
    els+=list(self.buttons.values())+list(self.rewardLines)
    if self.model:els.append(self.model)
    if hasattr(self,"_finalRewardTitle"):els.append(self._finalRewardTitle)
    for el in els:
        try:x,y=el.GetLocalPosition();el.SetPosition(int(x*S),int(y*S))
        except Exception:pass
    for el in (self.left,self.selector,self.middle,self.target,self.bonuses):
        el.SetSize(int(el.GetWidth()*S),int(el.GetHeight()*S))
    if self.model:self.model.SetSize(int(280*S),int(250*S))
    self.rewardScroll.SetScrollBarSize(int(280*S))
    _FinalButtonArt(self.previous,"previous",int(38*S),int(38*S))
    _FinalButtonArt(self.next,"next",int(38*S),int(38*S))
    for button in (self.startButton,self.bioTeleport):_FinalButtonArt(button,"mission_action",int(320*S),int(48*S),True,_SebanF(18))
    self.SetCenterPosition()
_SebanLayoutBase=_FinalMissionLayout
def _FinalMissionLayout(self):
    _SebanLayoutBase(self)
    self.title.SetPosition(430,60)
    self.name.SetPosition(165,8)
    self.previous.SetPosition(2,8);self.next.SetPosition(150,8);self.number.SetPosition(96,17)
    if _SEBAN_S!=1.0:_SebanScale(self)
    _FinalMissionStyle(self)
_SebanStyleBase=_FinalMissionStyle
def _FinalMissionStyle(self):
    _SebanStyleBase(self)
    _FinalFont(self.title,28,0xff5e1410,True)
    _FinalFont(self.name,22,0xff4a0f0a,True)
    _FinalFont(self.targetName,20,0xff2a1206,True)
    for line in (self.location,self.level,self.status):_FinalFont(line,15,0xff1e1206)
    _FinalFont(self.progress,16,0xff2a1206)
    _FinalFont(self.number,15,0xfffff1d0)
    self.number.SetOutline()
    if hasattr(self,"_finalRewardTitle"):_FinalFont(self._finalRewardTitle,22,0xff4a0f0a,True)
    _SebanRewards(self)
def _SebanRewards(self):
    for line in self.rewardLines:
        text=line.GetText()
        if text.endswith(" Yang") and text[:-5].isdigit() and len(text[:-5])>3:
            n=text[:-5];text=" ".join([n[max(0,i-3):i] for i in range(len(n),0,-3)][::-1])+" Yang";line.SetText(text)
        size=13 if len(text)>34 else (14 if len(text)>27 else 16)
        _FinalFont(line,size,0xff2a0805,True)
        line.SetOutline(False)
# Gra po przewinieciu nagrod rysuje je od nowa (cienka Tahoma) - po kazdym rysowaniu nasz styl.
_SebanDrawBase=MissionPanel.DrawRewards
def _SebanDraw(self,*args,**kwargs):
    result=_SebanDrawBase(self,*args,**kwargs)
    _SebanRewards(self)
    return result
MissionPanel.DrawRewards=_SebanDraw
_SebanRefreshBase=MissionPanel.Refresh
def _SebanRefresh(self,*args,**kwargs):
    result=_SebanRefreshBase(self,*args,**kwargs)
    if getattr(self,"modelReady",False) and self.renderedRace and getattr(self,"_sebanRotated",0)!=self.renderedRace:
        self._sebanRotated=self.renderedRace
        if hasattr(player,"Mt2009ModelRotation"):
            try:player.Mt2009ModelRotation(180.0)
            except Exception:pass
    return result
MissionPanel.Refresh=_SebanRefresh
'''


MISSIONS_SKIN = '/opt/m2spool/systems/misje/assets'


def missions_skin():
    """Wlasna grafika okna Ctrl+N z panelu (Misje -> Wyglad okna) -> wpisy ROOT do podmiany."""
    import os
    from dbeditor.systems_missions import SKIN_DIR, SKIN_SLOTS, skin_check
    out = {}
    for key, w, h, _label in SKIN_SLOTS:
        path = os.path.join(MISSIONS_SKIN, key + '.tga')
        if os.path.exists(path):
            raw = open(path, 'rb').read(); skin_check(raw, w, h); out[SKIN_DIR + key + '.tga'] = raw
    return out


def missions_skin_needed():
    return set(missions_skin())


def patch_missions_look(raw):
    """uimissionpanel.py: blok czytelnosci na koncu pliku (raz)."""
    # Blok jest dopisany na koncu pliku: kazda wczesniejsza wersja (V1, V2...) jest zastepowana aktualna.
    nl0 = _nl(raw)
    wanted = raw  # placeholder
    start = raw.find(b'# MT2009_NASZE_MISJE_CZYTELNOSC_')
    if start >= 0:
        base = raw[:start].rstrip()
        current = base + nl0 + MISSIONS_BLOCK.replace('\n', nl0.decode()).encode('ascii') + nl0
        return current
    if b'# CUSTOM_READABLE_WINDOWS_FIX_V2' not in raw or b'def _FinalMissionLayout(self):' not in raw:
        raise ValueError('Konflikt uimissionpanel.py: nieznana wersja okna misji.')
    nl = _nl(raw)
    return raw.rstrip() + nl + MISSIONS_BLOCK.replace('\n', nl.decode()).encode('ascii') + nl


WEEKLY_HOOK = b'# SEBAN_SYSTEMS_WEEKLY_HOOK_V1'


def patch_weekly(raw):
    """uiweeklyrank.py: opisy bonusow tytulow z serwera; bez danych - stare opisy."""
    nl = _nl(raw)
    head = b'def BonusShort(cat, place):'
    hook = nl.join((head, b'\t' + WEEKLY_HOOK, b'\tlive = __import__("sebansystems").weekly_short(cat, place)', b'\tif live is not None: return live'))
    old_long = b'self.bonusLine.SetText(BONUS_LONG.get(cat, ""))'
    new_long = b'self.bonusLine.SetText(__import__("sebansystems").weekly_long(cat, BONUS_LONG.get(cat, "")))'
    if WEEKLY_HOOK in raw:
        if raw.count(hook) != 1 or raw.count(new_long) != 1: raise ValueError('Konflikt zmienionego hooka w uiweeklyrank.py.')
        return raw
    if raw.count(head) != 1 or raw.count(old_long) != 1: raise ValueError('Konflikt uiweeklyrank.py: brak znanych opisow bonusow.')
    return raw.replace(head, hook, 1).replace(old_long, new_long, 1)


RANK_HOOK = b'# SEBAN_SYSTEMS_RANK_HOOK_V1'


def patch_rank(raw):
    """rankpoints.py: bonusy rangi w oknie postaci z serwera; bez danych - stary opis."""
    nl = _nl(raw)
    head = b'def AppendRankRewards(toolTip, total):'
    hook = nl.join((head, b'\t' + RANK_HOOK, b'\timport sebansystems', b'\tif sebansystems.append_rank(toolTip, total): return'))
    if RANK_HOOK in raw:
        if raw.count(hook) != 1: raise ValueError('Konflikt zmienionego hooka w rankpoints.py.')
        return raw
    if raw.count(head) != 1: raise ValueError('Konflikt rankpoints.py: brak znanej funkcji bonusow rangi.')
    return raw.replace(head, hook, 1)


GUILD_HOOK = b'# SEBAN_SYSTEMS_GUILD_HOOK_V1'


def patch_guild(raw):
    """customguildtooltip.py: opis bonusow gildii z serwera; bez danych - stary opis."""
    nl = _nl(raw)
    anchor = nl.join((b"            return", b"        self.tooltip.AppendSpace(5)", b"        self.tooltip.AppendTextLine('OBECNE BONUSY',0xff80d690)"))
    hook = nl.join((b"            return", b"        " + GUILD_HOOK, b"        import sebansystems",
                    b"        live=sebansystems.values('gildia',level)",
                    b"        if live is not None:",
                    b"            self.tooltip.AppendSpace(5)",
                    b"            self.tooltip.AppendTextLine('OBECNE BONUSY',0xff80d690)",
                    b"            sebansystems.append_points(self.tooltip,live,0xff80d690)",
                    b"            if level<MAX_LEVEL: sebansystems.append_next(self.tooltip,live,sebansystems.values('gildia',level+1),'Poziom %d:' % (level+1),0xffffcf75)",
                    b"            else: self.tooltip.AppendTextLine('Maksymalny poziom gildii.',0xffffcf75)",
                    b"            self.tooltip.AppendTextLine('Po wyjsciu z gildii bonusy znikaja.',0xffb0b0b0)",
                    b"            return",
                    b"        self.tooltip.AppendSpace(5)", b"        self.tooltip.AppendTextLine('OBECNE BONUSY',0xff80d690)"))
    if GUILD_HOOK in raw:
        if raw.count(hook) != 1: raise ValueError('Konflikt zmienionego hooka w customguildtooltip.py.')
        return raw
    if raw.count(anchor) != 1: raise ValueError('Konflikt customguildtooltip.py: brak znanego opisu bonusow gildii.')
    return raw.replace(anchor, hook, 1)


def patch_game(raw):
    """game.py: rejestracja polecenia serwera SebanSys."""
    anchor = b'\t\tfor serverCommandItem in serverCommandList.items():'
    line = b'\t\tserverCommandList["SebanSys"] = __import__("sebansystems").COMMANDS.OnCommand # ' + GAME_HOOK
    old = b'\t\tserverCommandList["SebanSys"] = __import__("sebansystems").OnCommand # ' + GAME_HOOK
    if raw.count(old) == 1:
        return raw.replace(old, line, 1)  # poprawka wczesniejszej wersji (gra nie wstawala: brak im_func)
    if GAME_HOOK in raw:
        if raw.count(line) != 1:
            raise ValueError('Konflikt zmienionego wpisu SebanSys w game.py.')
        return raw
    if raw.count(anchor) != 1:
        raise ValueError('Konflikt game.py: brak znanej listy polecen serwera.')
    return raw.replace(anchor, line + _nl(raw) + anchor, 1)
