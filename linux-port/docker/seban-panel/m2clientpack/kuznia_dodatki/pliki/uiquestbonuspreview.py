# ASCII source; Polish UI bytes escaped for embedded Python without cp1250 codec.
# QUEST_BONUS_PREVIEW_V1: server-read values; no reward claims.
import app
import net
import uiToolTip
import wndMgr
import gamefont

_data = None
_pending = None
_revision = 0
_nextRequest = 0.0

def Reset():
    global _data, _pending, _revision, _nextRequest
    _data = None
    _pending = None
    _revision += 1
    _nextRequest = 0.0

def OnBegin():
    global _pending
    _pending = {}

def OnRow(point, earned, remaining, key):
    if _pending is None:
        return
    try:
        point = int(point)
        if point < 0 or point > 1024 or len(_pending) > 256:
            return
        _pending[point] = (str(key), long(earned), max(0, long(remaining)))
    except (TypeError, ValueError):
        pass

def OnEnd():
    global _data, _pending, _revision
    if _pending is not None:
        _data = _pending
        _pending = None
        _revision += 1

def Request():
    global _nextRequest
    now = app.GetTime()
    if now >= _nextRequest:
        _nextRequest = now + 3.0
        net.SendChatPacket('/quest_bonus_preview')

# Labels key off symbolic server names, so server-only element point IDs are safe.
LABELS = {
    'POINT_HP_REGEN':'Regeneracja PZ', 'POINT_SP_REGEN':'Regeneracja many',
    'POINT_STEAL_HP':'Kradziez PZ', 'POINT_STEAL_SP':'Kradziez many',
    'POINT_MAX_HP': 'Maksymalne PZ', 'POINT_MAX_SP': 'Maksymalne PE',
    'POINT_MAX_STAMINA': 'Wytrzymalosc',
    'POINT_ST': 'Sila', 'POINT_HT': 'Witalnosc',
    'POINT_DX': 'Zrecznosc', 'POINT_IQ': 'Inteligencja',
    'POINT_DEF_GRADE': 'Obrona', 'POINT_DEF_GRADE_BONUS': 'Dodatkowa obrona',
    'POINT_ATT_GRADE': 'Atak', 'POINT_ATT_GRADE_BONUS': 'Wartosc ataku',
    'POINT_MAGIC_ATT_GRADE_BONUS': 'Wartosc magicznego ataku',
    'POINT_MAGIC_DEF_GRADE_BONUS': 'Magiczna obrona',
    'POINT_MOV_SPEED': 'Szybkosc ruchu', 'POINT_ATT_SPEED': 'Szybkosc ataku',
    'POINT_CASTING_SPEED': 'Szybkosc zaklecia',
    'POINT_CRITICAL_PCT': 'Szansa na krytyka', 'POINT_PENETRATE_PCT': 'Szansa na przeszywke',
    'POINT_ATT_BONUS': 'Atak', 'POINT_DEF_BONUS': 'Obrona',
    'POINT_ATTBONUS_HUMAN': 'Silny na ludzi', 'POINT_ATTBONUS_MONSTER': 'Silny na potwory',
    'POINT_ATTBONUS_STONE': 'Silny na metiny', 'POINT_ATTBONUS_BOSS': 'Silny na bossy',
    'POINT_ATTBONUS_ANIMAL': 'Silny na zwierzeta', 'POINT_ATTBONUS_ORC': 'Silny na orki',
    'POINT_ATTBONUS_DESERT': 'Silny na pustynne potwory',
    'POINT_ATTBONUS_INSECT': 'Silny na owady', 'POINT_ATTBONUS_TREE': 'Silny na lesne potwory',
    'POINT_ATTBONUS_FIRE': 'Silny na ogniste potwory', 'POINT_ATTBONUS_ICE': 'Silny na lodowe potwory',
    'POINT_ATTBONUS_UNDEAD': 'Silny na nieumarlych', 'POINT_ATTBONUS_DEVIL': 'Silny na diably',
    'POINT_ATTBONUS_MILGYO': 'Silny na ezoteryczne',
    'POINT_ATTBONUS_WARRIOR': 'Silny na wojownika', 'POINT_ATTBONUS_ASSASSIN': 'Silny na ninje',
    'POINT_ATTBONUS_SURA': 'Silny na sure', 'POINT_ATTBONUS_SHAMAN': 'Silny na szamana',
    'POINT_RESIST_WARRIOR': 'Odpornosc na wojownika', 'POINT_RESIST_ASSASSIN': 'Odpornosc na ninje',
    'POINT_RESIST_SURA': 'Odpornosc na sure', 'POINT_RESIST_SHAMAN': 'Odpornosc na szamana',
    'POINT_RESIST_HUMAN': 'Odpornosc na ludzi', 'POINT_RESIST_MONSTER_1000PCT': 'Odpornosc na potwory',
    'POINT_RESIST_CRITICAL': 'Odpornosc na krytyka', 'POINT_RESIST_PENETRATE': 'Odpornosc na przeszywke',
    'POINT_SKILL_DEFEND_BONUS': 'Odpornosc na umiejetnosci',
    'POINT_NORMAL_HIT_DEFEND_BONUS': 'Odpornosc na zwykle hity',
    'POINT_NORMAL_HIT_DAMAGE_BONUS': 'Srednie obrazenia',
    'POINT_SKILL_DAMAGE_BONUS': 'Obrazenia umiejetnosci',
    'POINT_RESIST_NORMAL_DAMAGE': 'Odporno\x9c\xe6 na zwykle obrazenia',
    'POINT_BLOCK': 'Blok ciosow', 'POINT_DODGE': 'Unik strzal',
    'POINT_POISON_PCT': 'Szansa na zatrucie', 'POINT_STUN_PCT': 'Szansa na omdlenie',
    'POINT_SLOW_PCT': 'Szansa na spowolnienie',
    'POINT_POISON_REDUCE': 'Odpornosc na trucizne',
    'POINT_MAX_HP_PCT': 'Maksymalne PZ', 'POINT_MAX_SP_PCT': 'Maksymalne PE',
    'POINT_EXP_DOUBLE_BONUS': 'Szansa na dodatkowy EXP',
    'POINT_GOLD_DOUBLE_BONUS': 'Szansa na podwojny Yang',
    'POINT_ITEM_DROP_BONUS': 'Szansa na drop przedmiotow',
}
for suffix, label in (('FIRE','ogien'),('ELECT','blyskawice'),('ELEC','blyskawice'),('ICE','lod'),('WIND','wiatr'),('EARTH','ziemie'),('DARK','mrok'),('MAGIC','magie')):
    LABELS['POINT_ENCHANT_' + suffix] = 'Silny na ' + label
    LABELS['POINT_RESIST_' + suffix] = 'Odpornosc na ' + label
PLAIN = set(('POINT_MAX_HP','POINT_MAX_SP','POINT_MAX_STAMINA','POINT_ST','POINT_HT','POINT_DX','POINT_IQ','POINT_DEF_GRADE','POINT_DEF_GRADE_BONUS','POINT_ATT_GRADE','POINT_ATT_GRADE_BONUS','POINT_MAGIC_ATT_GRADE','POINT_MAGIC_ATT_GRADE_BONUS','POINT_MAGIC_DEF_GRADE','POINT_MAGIC_DEF_GRADE_BONUS'))

def FormatRow(point, key, value):
    if key not in LABELS:key={32:"POINT_HP_REGEN",33:"POINT_SP_REGEN",63:"POINT_STEAL_HP",64:"POINT_STEAL_SP"}.get(point,key)
    label = LABELS.get(key, 'Bonus #%d' % point)
    sign = '+' if value >= 0 else ''
    if key == 'POINT_RESIST_MONSTER_1000PCT':
        text = ('%.1f' % (value / 10.0)).rstrip('0').rstrip('.').replace('.', ',')
    else:
        text = str(value)
    unit = '' if key in PLAIN else '%'
    return '%s: %s%s%s' % (label, sign, text, unit)

class QuestBonusToolTip(uiToolTip.ToolTip):
    def __init__(self):
        uiToolTip.ToolTip.__init__(self, 370)
        self.TEXT_LINE_HEIGHT = 18
        self._page=0;self._pages=1;self._keyHeld=False
        self._seen = -1
        self._hover = False
        self.HideToolTip()

    def ShowQuest(self):
        self._hover = True
        self._page=0
        Request()
        self._seen = -1
        self.Refresh()
        self.ShowToolTip()

    def HideQuest(self):
        self._hover = False
        self.HideToolTip()

    def Refresh(self):
        self.ClearToolTip()
        self.SetDefaultFontName(gamefont.GetCurrentFontLarge())
        self.SetThinBoardSize(370)
        self.AppendTextLine('BONUSY Z MISJI',0xfff3d080)
        if _data is None:
            self.AppendTextLine('Pobieranie bonusow...',self.NORMAL_COLOR)
        else:
            have=[(p,d) for p,d in sorted(_data.items()) if d[1]!=0]
            left=[(p,d) for p,d in sorted(_data.items()) if d[2]>0]
            count=max(4,min(10,(wndMgr.GetScreenHeight()-150)//36))
            self._pages=max(1,(max(len(have),len(left))+count-1)//count);self._page=min(self._page,self._pages-1)
            self.AppendSpace(4);self.AppendTextLine('OTRZYMANE - LACZNIE',0xff77ee88)
            for point,(key,earned,remaining) in have[self._page*count:(self._page+1)*count]:self.AppendTextLine(FormatRow(point,key,earned),0xff77ee88,False)
            if not have:self.AppendTextLine('Brak przyznanych bonusow.',self.NORMAL_COLOR)
            self.AppendSpace(6);self.AppendTextLine('DO ZDOBYCIA - LACZNIE',0xffff9090)
            for point,(key,earned,remaining) in left[self._page*count:(self._page+1)*count]:self.AppendTextLine(FormatRow(point,key,remaining),0xffff9090,False)
            if not left:self.AppendTextLine('Wszystkie bonusy zdobyte.',0xffff9090)
            if self._pages>1:self.AppendSpace(5);self.AppendTextLine('Strona %d / %d - PgUp / PgDn'%(self._page+1,self._pages),0xff70d6ed)
        # Font chosen before AppendTextLine; never change the glyph atlas after GetTextSize.
        self._seen=_revision
        self.ResizeToolTip()

    def OnUpdate(self):
        if self._hover:
            up=app.IsPressed(getattr(app,'DIK_PRIOR',201));down=app.IsPressed(getattr(app,'DIK_NEXT',209))
            if (up or down) and not self._keyHeld:
                self._page=max(0,min(self._pages-1,self._page+(1 if down else -1)));self.Refresh()
            self._keyHeld=bool(up or down)
            Request()
            if self._seen != _revision:
                self.Refresh()
        uiToolTip.ToolTip.OnUpdate(self)
