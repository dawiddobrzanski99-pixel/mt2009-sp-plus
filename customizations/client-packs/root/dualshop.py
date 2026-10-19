# PLAYER_SHOP_TWO_BLOCKS_KEYS2_V1
# Python 2 client: keep wire positions 0..79 and 80..159 unchanged.
import ui
import shop
import item
import wndMgr

PAGE = shop.SHOP_PLAYER_WIDTH * shop.SHOP_PLAYER_HEIGHT
OLD_KEYS = shop.SHOP_PLAYER_LOCKED_Y_END - shop.SHOP_PLAYER_LOCKED_Y_START + 1

def Physical(cell):
    return (cell % PAGE // shop.SHOP_PLAYER_WIDTH) * (shop.SHOP_PLAYER_WIDTH * 2) + cell % shop.SHOP_PLAYER_WIDTH + (cell // PAGE) * shop.SHOP_PLAYER_WIDTH

def Logical(cell):
    w = shop.SHOP_PLAYER_WIDTH
    return (cell % (w * 2) // w) * PAGE + cell // (w * 2) * w + cell % w

def Fits(cell, height):
    return 0 <= cell < PAGE * 2 and height > 0 and cell % PAGE // shop.SHOP_PLAYER_WIDTH + height <= shop.SHOP_PLAYER_HEIGHT

def Locked(cell, progress):
    if cell < 0 or cell >= PAGE * 2:
        return True
    if cell < PAGE:
        x = cell % shop.SHOP_PLAYER_WIDTH
        y = cell // shop.SHOP_PLAYER_WIDTH
        return shop.SHOP_PLAYER_LOCKED_X_START <= x <= shop.SHOP_PLAYER_LOCKED_X_END and shop.SHOP_PLAYER_LOCKED_Y_START + progress <= y <= shop.SHOP_PLAYER_LOCKED_Y_END
    local = cell - PAGE
    group = (local // shop.SHOP_PLAYER_WIDTH) * 2 + (local % shop.SHOP_PLAYER_WIDTH) // 5
    return group >= max(0, progress - OLD_KEYS)

def Premium(cell):
    if not 0 <= cell < PAGE:
        return False
    x, y = cell % shop.SHOP_PLAYER_WIDTH, cell // shop.SHOP_PLAYER_WIDTH
    return shop.SHOP_PLAYER_PREMIUM_X_START <= x <= shop.SHOP_PLAYER_PREMIUM_X_END and shop.SHOP_PLAYER_PREMIUM_Y_START <= y <= shop.SHOP_PLAYER_PREMIUM_Y_END

class DualGrid(ui.GridSlotWindow):
    def __init__(self):
        ui.GridSlotWindow.__init__(self)
        self.ArrangeSlot(0, shop.SHOP_PLAYER_WIDTH * 2, shop.SHOP_PLAYER_HEIGHT, 32, 32, 0, 0)

    def SetItemSlot(self, cell, *args, **kwargs):
        return ui.GridSlotWindow.SetItemSlot(self, Physical(cell), *args, **kwargs)

    def ClearSlot(self, cell):
        return ui.GridSlotWindow.ClearSlot(self, Physical(cell))

    def ActivateSlot(self, cell, *args):
        return ui.GridSlotWindow.ActivateSlot(self, Physical(cell), *args)

    def DeactivateSlot(self, cell):
        return ui.GridSlotWindow.DeactivateSlot(self, Physical(cell))

    def GetSlotBindedItemIndex(self, cell):
        return ui.GridSlotWindow.GetSlotBindedItemIndex(self, Physical(cell))

    def FindEmptySlot(self, neededItemSize=1, startIndex=0):
        busy = set()
        for cell in range(PAGE * 2):
            vnum = self.GetSlotBindedItemIndex(cell)
            if vnum:
                item.SelectItem(vnum)
                height = item.GetItemSize()[1]
                busy.update(cell + i * shop.SHOP_PLAYER_WIDTH for i in range(height))
        for cell in range(max(0, startIndex), PAGE * 2):
            if not Fits(cell, neededItemSize):
                continue
            if any(cell + i * shop.SHOP_PLAYER_WIDTH in busy for i in range(neededItemSize)):
                continue
            if self.checkSlotEvent is not None and not self.checkSlotEvent(cell, neededItemSize):
                continue
            return cell
        return -1

# Native wndMgr events report physical cells; callbacks receive logical wire cells.
def _event(name):
    def dispatch(self, cell):
        return getattr(ui.GridSlotWindow, name)(self, Logical(cell))
    return dispatch
for _name in ('OnSelectEmptySlot', 'OnSelectItemSlot', 'OnUnselectEmptySlot', 'OnUnselectItemSlot', 'OnUseSlot', 'OnOverInItem', 'OnPressedSlotButton'):
    setattr(DualGrid, _name, _event(_name))

def WidenBuilder(window):
    width, height = window.GetWidth() + shop.SHOP_PLAYER_WIDTH * 32, window.GetHeight()
    window.SetSize(width, height)
    window.board.SetSize(width, height)
    window.titleBar.SetWidth(width - 15)
    x, y = window.GetGlobalPosition()
    window.SetPosition(max(0, min(x, wndMgr.GetScreenWidth() - width)), y)
