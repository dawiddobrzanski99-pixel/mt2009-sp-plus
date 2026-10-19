# CUSTOM_DUNGEON_DAMAGE_HUD_V1 - Python 2.7 / CP1250.
import app
import net
import player
import ui
import wndMgr

VISIBLE_ROWS = 6
_state = {'window': None, 'map': 0, 'rows': [], 'pending': None, 'request': -10.0, 'received': -10.0, 'clock': None, 'elapsed': 0, 'synced': 0.0}

def ShortDamage(value):
    value = max(0, int(value))
    for divisor, suffix in ((1000000000, 'kkk'), (1000000, 'kk'), (1000, 'k')):
        if value >= divisor:
            tenths = value * 10 // divisor
            whole, fraction = divmod(tenths, 10)
            return ('%d,%d' % (whole, fraction) if fraction else str(whole)) + suffix
    return str(value)

def Unhex(value):
    if value == '-': return '?'
    try: return ''.join(chr(int(value[i:i+2], 16)) for i in xrange(0, len(value), 2))
    except (ValueError, TypeError): return '?'

def OnBegin(mapIndex='0', *unused):
    try: mapIndex = int(mapIndex)
    except (ValueError, TypeError): mapIndex = 0
    _state['pending'] = {'map': mapIndex, 'rows': []}

def OnRow(pid='0', damage='0', name='-', *unused):
    pending = _state['pending']
    if pending is None: return
    try: pending['rows'].append((int(pid), Unhex(name), max(0, int(damage))))
    except (ValueError, TypeError): pass

def OnEnd(*unused):
    pending = _state['pending']
    if pending is None: return
    changed = _state['map'] != pending['map']
    _state['map'] = pending['map']
    _state['rows'] = sorted(pending['rows'], key=lambda row: (-row[2], row[0]))
    _state['pending'] = None
    _state['received'] = app.GetTime()
    if _state['window']:
        if changed: _state['window'].page = 0
        _state['window'].Refresh()

class DamageWindow(ui.ThinBoard):
    def __init__(self):
        ui.ThinBoard.__init__(self)
        self.SetSize(200, 54 + VISIBLE_ROWS * 19)
        self.page = 0
        self.title = ui.TextLine()
        self.title.SetParent(self)
        self.title.SetPosition(12, 9)
        self.title.SetText('Dungeon - zadane obra\xbfenia')
        self.title.SetPackedFontColor(0xffffcf75)
        self.title.Show()
        self.lines = []
        for i in xrange(VISIBLE_ROWS):
            name = ui.TextLine(); name.SetParent(self); name.SetPosition(12, 31 + i*19); name.SetLimitWidth(110); name.Show()
            amount = ui.TextLine(); amount.SetParent(self); amount.SetPosition(188, 31 + i*19)
            amount.SetHorizontalAlignRight(); amount.Show()
            self.lines.append((name, amount))
        self.footer = ui.TextLine(); self.footer.SetParent(self)
        self.footer.SetPosition(48, 34 + VISIBLE_ROWS * 19); self.footer.Show()
        self.previous = self.MakeButton(12, '<', -1)
        self.next = self.MakeButton(160, '>', 1)
        self.Hide()

    def MakeButton(self, x, text, direction):
        button = ui.Button(); button.SetParent(self)
        button.SetPosition(x, 30 + VISIBLE_ROWS * 19)
        button.SetUpVisual('d:/ymir work/ui/public/small_button_01.sub')
        button.SetOverVisual('d:/ymir work/ui/public/small_button_02.sub')
        button.SetDownVisual('d:/ymir work/ui/public/small_button_03.sub')
        button.SetText(text); button.SetEvent(ui.__mem_func__(self.ChangePage), direction); button.Show()
        return button

    def ChangePage(self, direction):
        pages = max(1, (len(_state['rows']) + VISIBLE_ROWS - 1) // VISIBLE_ROWS)
        self.page = max(0, min(pages - 1, self.page + direction))
        self.Refresh()

    def Refresh(self):
        if not _state['map']:
            self.Hide(); return
        rows = _state['rows']
        pages = max(1, (len(rows) + VISIBLE_ROWS - 1) // VISIBLE_ROWS)
        self.page = min(self.page, pages - 1)
        start = self.page * VISIBLE_ROWS
        own = player.GetName()
        for i, (name, amount) in enumerate(self.lines):
            if start + i < len(rows):
                pid, nick, damage = rows[start+i]
                name.SetText(nick); amount.SetText(ShortDamage(damage))
                color = 0xff80d690 if nick == own else 0xffeeeeee
                name.SetPackedFontColor(color); amount.SetPackedFontColor(color)
            else:
                name.SetText(''); amount.SetText('')
        self.footer.SetText('%d os. | %d/%d' % (len(rows), self.page + 1, pages))
        if pages > 1: self.previous.Show(); self.next.Show()
        else: self.previous.Hide(); self.next.Hide()
        self.Show()

    def Follow(self, minimap):
        if minimap:
            x, y = minimap.GetGlobalPosition()
            x = x + minimap.GetWidth() - self.GetWidth()
        else:
            x = wndMgr.GetScreenWidth() - self.GetWidth() - 8
        y = __import__('uimapcounters').GetBottom(minimap) + 80
        self.SetPosition(max(0, min(x, wndMgr.GetScreenWidth()-self.GetWidth())),
                         max(0, min(y, wndMgr.GetScreenHeight()-self.GetHeight())))

def Update(minimap=None):
    if not __import__('warpsafe').InGame(): return
    now = app.GetTime()
    UpdateClock(now)
    if now - _state['request'] >= 2.0:
        _state['request'] = now
        net.SendChatPacket('/dungeon_dmg')
    window = _state['window']
    if _state['map'] and window is None:
        window = DamageWindow(); _state['window'] = window; window.Refresh()
    if window:
        window.Follow(minimap)
        if now - _state['received'] > 8.0: window.Hide()

def Destroy():
    if _state['clock']: _state['clock'].Hide()
    if _state['window']: _state['window'].Hide()
    _state.update({'window': None, 'map': 0, 'rows': [], 'pending': None, 'request': -10.0, 'received': -10.0, 'clock': None, 'elapsed': 0, 'synced': 0.0})

# CUSTOM_DUNGEON_ELAPSED_TOP_V1: independent from the damage panel.
def OnTime(elapsed='0', *unused):
    try: elapsed = max(0, int(elapsed))
    except (ValueError, TypeError): return
    _state['elapsed'] = elapsed
    _state['synced'] = app.GetTime()

def UpdateClock(now):
    clock = _state['clock']
    if clock is None:
        clock = ui.TextLine()
        clock.SetOutline()
        clock.SetHorizontalAlignCenter()
        clock.SetPackedFontColor(0xffffd879)
        _state['clock'] = clock
    clock.SetPosition(wndMgr.GetScreenWidth() // 2, 12)
    if not _state['map'] or now - _state['received'] > 8.0:
        clock.Hide(); return
    seconds = max(0, _state['elapsed'] + int(now - _state['synced']))
    minutes, seconds = divmod(seconds, 60)
    clock.SetText('Czas wyprawy: %02d:%02d' % (minutes, seconds))
    clock.Show()
