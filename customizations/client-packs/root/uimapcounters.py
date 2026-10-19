# CUSTOM_MAP_COUNTERS_V1 - large colored live-map counters under the coordinates.
import app
import background
import net
import ui
import wndMgr

_state = {'window': None, 'received': -20.0, 'request': -20.0,
          'mapName': None, 'values': None}

def AnchorY(minimap):
    if not minimap: return 184
    x, y = minimap.GetGlobalPosition()
    bottom = y + minimap.GetHeight()
    for name in ('positionInfo', 'FPSInfo', 'observerCount'):
        line = getattr(minimap, name, None)
        if line and line.IsShow() and line.GetText():
            lx, ly = line.GetGlobalPosition()
            bottom = max(bottom, ly + max(16, line.GetHeight()))
    return bottom + 2

class CounterWindow(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('not_pick')
        self.SetSize(164, 36)
        self.bossIcon = self.MakeIcon('custom/map_counters/boss.tga', 0)
        self.stoneIcon = self.MakeIcon('custom/map_counters/metin.tga', 85)
        self.boss = self.MakeLine(18, 0)
        self.stone = self.MakeLine(103, 0)
        self.guild = self.MakeLine(82, 18, True)
        self.Hide()

    def MakeIcon(self, path, x):
        icon = ui.ImageBox()
        icon.SetParent(self)
        icon.AddFlag('not_pick')
        icon.LoadImage(path)
        icon.SetPosition(x, 0)
        icon.Show()
        return icon

    def MakeLine(self, x, y, centered=False):
        line = ui.TextLine()
        line.SetParent(self)
        line.SetPosition(x, y)
        line.SetFontName('Tahoma:12')
        if centered: line.SetHorizontalAlignCenter()
        line.SetOutline()
        line.AddFlag('not_pick')
        line.Show()
        return line

    def Refresh(self):
        values = _state['values']
        if values is None:
            self.Hide(); return
        mapIndex, bosses, stones, guild = values
        self.boss.SetText('|cffff7777Bossy: %d|r' % bosses)
        self.stone.SetText('|cff75ceffMetiny: %d|r' % stones)
        self.guild.SetText('|cff83ef8fGildia na mapie: %d|r' % guild)
        self.Show()

    def Follow(self, minimap):
        if minimap:
            x, y = minimap.GetGlobalPosition()
            x += (minimap.GetWidth() - self.GetWidth()) // 2
        else: x = wndMgr.GetScreenWidth() - self.GetWidth() - 8
        self.SetPosition(max(0, min(x, wndMgr.GetScreenWidth() - self.GetWidth())),
                         max(0, min(AnchorY(minimap), wndMgr.GetScreenHeight() - self.GetHeight())))

def OnCounters(mapIndex, bosses, stones, members):
    try: values = tuple(max(0, int(v)) for v in (mapIndex, bosses, stones, members))
    except (ValueError, TypeError): return
    _state['values'] = values
    _state['received'] = app.GetTime()
    if _state['window']: _state['window'].Refresh()

def Update(minimap=None):
    if not __import__('warpsafe').InGame(): return
    now = app.GetTime()
    mapName = background.GetCurrentMapName()
    if mapName != _state['mapName']:
        _state['mapName'] = mapName
        _state['values'] = None
        _state['request'] = -20.0
        if _state['window']: _state['window'].Hide()
    if now - _state['request'] >= 5.0:
        _state['request'] = now
        net.SendChatPacket('/map_counters')
    if _state['window'] is None:
        _state['window'] = CounterWindow()
    window = _state['window']
    window.Follow(minimap)
    if _state['values'] is not None and now - _state['received'] <= 12.0:
        window.Refresh()
    else: window.Hide()

def GetBottom(minimap=None):
    window = _state['window']
    if window and window.IsShow():
        x, y = window.GetGlobalPosition()
        return y + window.GetHeight() + 6
    return AnchorY(minimap)

def Destroy():
    if _state['window']: _state['window'].Hide()
    _state.update({'window': None, 'received': -20.0, 'request': -20.0,
                   'mapName': None, 'values': None})
