# CUSTOM_GUILD_COMBAT_REWARDS_V1 - Python 2 compatible, text in CP1250 escapes.
import ui
import guild
import uiToolTip
import wndMgr

MAX_LEVEL = 20
BONUS_LABELS = (
    'Silny na wszystkie klasy',
    'Odporno\x9c\xe6 na wszystkie klasy',
    'Silny na wszystkie \xbfywio\xb3y',
    'Silny na potwory',
    'Silny na bossy',
    'Silny na metiny',
    'Szansa na podw\xf3jny drop',
    'Szansa na podw\xf3jny Yang',
)

def GuildValue(label,level):
    if label in ('Silny na potwory','Silny na bossy','Silny na metiny') or label==BONUS_LABELS[2]:return level//2
    if label in BONUS_LABELS[6:8]:return level//4
    return level

def BonusRows(level):
    rows=[]
    for label in BONUS_LABELS:
        value=GuildValue(label,level)
        rows.append('%s: +%d%%'%(label,value))
    for stat in ('WIT','INT','SIL','ZR'):
        rows.append('%s: +%d'%(stat,level))
    return rows

class GuildBonusHover(ui.Window):
    def __init__(self, parent, target):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.page = parent
        self.target = target
        self.AddFlag("not_pick")
        self.SetPosition(0, 0)
        self.SetSize(1, 1)
        self.tooltip = uiToolTip.ToolTip(360)
        self.lastLevel = -1
        self.Show()

    def __Build(self):
        level = max(0, min(MAX_LEVEL, int(guild.GetGuildLevel())))
        self.lastLevel = level
        self.tooltip.ClearToolTip()
        self.tooltip.SetTitle('Bonusy gildii - poziom %d' % level)
        if level < 1:
            self.tooltip.AppendTextLine('Brak aktywnych bonus\xf3w gildii.')
            return
        self.tooltip.AppendSpace(5)
        self.tooltip.AppendTextLine('OBECNE BONUSY',0xff80d690)
        for label in BONUS_LABELS:
            value=GuildValue(label,level)
            self.tooltip.AppendTextLine('%s: +%d%%'%(label,value),0xff80d690)
        self.tooltip.AppendTextLine('WIT / INT / SIL / ZR: po +%d'%level,0xff80d690)
        self.tooltip.AppendSpace(5)
        if level<MAX_LEVEL:
            self.tooltip.AppendTextLine('Poziom %d: staty +%d, PvE/zywioly %d%%'%(level+1,level+1,(level+1)//2),0xffffcf75)
        else:self.tooltip.AppendTextLine('Maksymalny poziom gildii.',0xffffcf75)
        self.tooltip.AppendTextLine('Klasy i zywioly: bonus dla kazdego.',0xffb0b0b0)
        self.tooltip.AppendTextLine('Po wyjsciu z gildii bonusy znikaja.',0xffb0b0b0)

    def OnMouseOverIn(self):
        self.__Build()
        self.tooltip.ShowToolTip()

    def OnMouseOverOut(self):
        self.tooltip.HideToolTip()

    def OnUpdate(self):
        # TextLine mouse events are not reliable; use the actual slot rectangle.
        if not self.page.IsShow():
            self.tooltip.HideToolTip()
            return
        x, y = self.target.GetGlobalPosition()
        mx, my = wndMgr.GetMousePosition()
        inside = x <= mx < x + self.target.GetWidth() and y <= my < y + self.target.GetHeight()
        if inside:
            if not self.tooltip.IsShow() or int(guild.GetGuildLevel()) != self.lastLevel:
                self.__Build()
                self.tooltip.ShowToolTip()
        else:
            self.tooltip.HideToolTip()
