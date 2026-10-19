# MT2009_PLUS_TELEPORT_MAP_V1: Mapa teleportacji pod TAB. Autor: Mur4s.
# TAB (without Ctrl) opens the world map with 18 points; a click sends
# "/tabteleport <key>" and the server's quest mapa_tab warps (free, no ring;
# the server takes only the key). Hell asks for the respawn kingdom first.
# Only while the server has it on: "MAPA_TAB 1|0" (quest mapa_tab, at login
# and within seconds of the panel's switch) sets IsEnabled(); off, game.py
# leaves TAB to what it did before (Slot 6).
# Python 2.7; UI strings use CP1250 escapes.
import app
import net
import ui
import wndMgr

# TAB_ATLAS_LOL_WOT_V2: pixel hitboxes match the approved 1672x941 artwork.
POINTS = (('Jinno M1', 'jinno1', 145, 597, 305, 642), ('Jinno M2', 'jinno2', 345, 738, 495, 776), ('Shinsoo M1', 'shinsoo1', 600, 660, 770, 699), ('Shinsoo M2', 'shinsoo2', 803, 772, 971, 810), ('Chunjo M1', 'chunjo1', 1062, 687, 1230, 725), ('Chunjo M2', 'chunjo2', 1333, 763, 1509, 803), ('Dolina Orkow', 'valley', 600, 486, 785, 525), ('Pustynia', 'desert', 1121, 482, 1280, 521), ('Gora Sohan', 'snow', 1036, 154, 1213, 194), ('Swiatynia', 'temple', 976, 313, 1131, 353), ('Dolina Cyklopow', 'cyclops', 1442, 384, 1652, 424), ('Pustkowie Faraona', 'pharaoh', 1419, 621, 1651, 662), ('Las Duchow', 'forest', 176, 240, 356, 279), ('Czerwony Las', 'redforest', 153, 421, 366, 460), ('Pieklo', 'hell', 1440, 149, 1555, 188), ('Wieza Demonow', 'tower', 558, 112, 768, 151), ('Loch Pajakow V1', 'spider', 561, 281, 771, 323), ('Kraina Gigantow', 'giants', 1237, 328, 1456, 368))
_window = None
_enabled = False

class MapHotspot(ui.Window):
    def __init__(self,parent,x,y,width,height,callback):
        ui.Window.__init__(self)
        self.SetParent(parent);self.SetPosition(x,y);self.SetSize(width,height)
        self.callback=callback
        self.hover=ui.Bar();self.hover.SetParent(self);self.hover.AddFlag('not_pick')
        self.hover.SetSize(width,height);self.hover.SetColor(0x35e7bf66);self.hover.Hide()
        self.Show()
    def OnMouseOverIn(self):self.hover.Show()
    def OnMouseOverOut(self):self.hover.Hide()
    def OnMouseLeftButtonDown(self):return True
    def OnMouseLeftButtonUp(self):self.callback();return True

class TeleportMap(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.AddFlag('movable')
        self.children = []
        self.dialog = None
        width = min(1200, wndMgr.GetScreenWidth() - 40)
        height = min(int(width * 941.0 / 1672), wndMgr.GetScreenHeight() - 100)
        width = int(height * 1672.0 / 941)
        self.SetSize(width, height)
        self.SetCenterPosition()
        self.image = ui.ExpandedImageBox()
        self.image.SetParent(self)
        self.image.SetPosition(0, 0)
        self.image.AddFlag('not_pick')
        self.image.LoadImage('teleport_world_map_18_points.png')
        self.image.SetScale(float(width) / self.image.GetWidth(), float(height) / self.image.GetHeight())
        self.image.Show()
        for name,key,left,top,right,bottom in POINTS:
            button=MapHotspot(self,int(left*width/1672.0),int(top*height/941.0),max(1,int((right-left)*width/1672.0)),max(1,int((bottom-top)*height/941.0)),lambda k=key,n=name:self.Select(k,n))
            self.children.append(button)
        self.closeButton=MapHotspot(self,int(1601*width/1672.0),int(25*height/941.0),max(1,int(43*width/1672.0)),max(1,int(46*height/941.0)),self.Close)
        self.children.append(self.closeButton)

    def Select(self, key, name):
        self.CloseDialog()
        if key == 'hell':
            self.dialog = ui.BoardWithTitleBar()
            self.dialog.AddFlag('float')
            self.dialog.SetSize(260, 165)
            self.dialog.SetTitleName('Piek\xb3o - wybierz respawn')
            self.dialog.SetCloseEvent(self.CloseDialog)
            self.dialog.SetCenterPosition()
            self.choices = []
            for index, kingdom in enumerate(('Shinsoo', 'Chunjo', 'Jinno')):
                b = ui.Button()
                b.SetParent(self.dialog)
                b.SetPosition(80, 40 + 34 * index)
                b.SetUpVisual('d:/ymir work/ui/public/large_button_01.sub')
                b.SetOverVisual('d:/ymir work/ui/public/large_button_02.sub')
                b.SetDownVisual('d:/ymir work/ui/public/large_button_03.sub')
                b.SetText(kingdom)
                b.SetEvent(ui.__mem_func__(self.Go), 'hell%d' % (index + 1))
                b.Show()
                self.choices.append(b)
            self.dialog.Show()
            self.dialog.SetTop()
            return
        self.Go(key)

    def Go(self, key):
        net.SendChatPacket('/tabteleport ' + key)
        self.Close()

    def CloseDialog(self):
        if self.dialog:
            self.dialog.Hide()
        self.dialog = None
        self.choices = []

    def Close(self):
        self.CloseDialog()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnKeyDown(self, key):
        if key == app.DIK_TAB:
            self.Close()
            return True
        return False

def ToggleWindow():
    global _window
    if _window is None:
        _window = TeleportMap()
    if _window.IsShow():
        _window.Close()
    else:
        _window.Show()
        _window.SetTop()

def DestroyWindow():
    global _window
    if _window:
        _window.Close()
    _window = None

def IsEnabled():
    return _enabled

def OnCommand(*args):
    # "MAPA_TAB 1" / "MAPA_TAB 0" from the server (quest mapa_tab).
    global _enabled
    _enabled = bool(args) and args[0] == '1'
    if not _enabled and _window:
        _window.Close()
