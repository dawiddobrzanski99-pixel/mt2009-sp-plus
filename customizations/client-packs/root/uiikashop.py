# cpython modules
import app
import player
import item
import net
import dbg
import wndMgr
import ikashop
import chr

# m2 python modules
import localeInfo as locale
import mouseModule as mouse

import eventManager
import ui
import uicommon
import uitooltip

# python modules
import datetime
from _weakref import proxy
from random import shuffle

AUCTION_MIN_RAISE_PERCENTAGE = 10
RESTORE_DURATION_COST = 1000000
MOVE_SHOP_ENTITY_COST = 100000
SLOT_SIZE = 32
MIN_OFFER_PCT = 30 # private offer min % of selling price
YANG_PER_CHEQUE = 100000000

ENABLE_DEFAULT_UI_BOARD = 1
ENABLE_CHEQUE_SYSTEM = getattr(app, "ENABLE_CHEQUE_SYSTEM", 0)

def debug(fmt, *args):
	if args:
		fmt = fmt.format(*args)
	dbg.Tracen(fmt)

def debugStack():
	import traceback
	s = traceback.format_stack()
	for line in s[:-1]:
		debug(line)

def RomeNumber(num):
	nums = {
		1 : "I",		2 : "II",		3 : "III",
		4 : "IV",		5 : "V",		6 : "VI",
		7 : "VII",		8 : "VIII",		9 : "IX",
	}
	return nums.get(num, "X")

def DatetimeFormat(timestamp):
	try:
		# make datetime object
		dts = datetime.datetime.fromtimestamp(timestamp)
		# make today datetime object
		dtn = datetime.datetime.now()
		# checking for today
		if dts.date() == dtn.date():
			return locale.IKASHOP_DATETIME_TODAY.format(dts.hour, dts.minute)
		# checking for yesterday
		dty = dtn - datetime.timedelta(days=1)
		if dty.date() == dts.date():
			return locale.IKASHOP_DATETIME_YESTERDAY.format(dts.hour, dts.minute)
		# checking for tomorrow
		dty = dtn + datetime.timedelta(days=1)
		if dty.date() == dts.date():
			return locale.IKASHOP_DATETIME_TOMORROW.format(dts.hour, dts.minute)
		# formatting dd/mm/yy hh:mm
		return "{:02d}/{:02d}/{:02d} {:02d}:{:02d}".format(
			dts.day, dts.month, dts.year%100, dts.hour, dts.minute)
	except Exception as e:
		dbg.TraceError("{}: {}".format(e, timestamp))

def GetScreenSize():
	return wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()

class ProxyPrototype(object):
	pass

def IsProxy(obj):
	if not hasattr(IsProxy, "test"):
		fakeInstance = ProxyPrototype()
		IsProxy.test = proxy(fakeInstance)
	return type(obj) == type(IsProxy.test)

def SelfDestroyObject(instance):
	def DestroyValue(value):
		if IsProxy(value):
			return True
		if isinstance(value, ui.Window):
			if isinstance(value, IkarusShopWindow):
				value.Destroy()
			else:
				SelfDestroyObject(value)
			return True
		elif type(value) in (list, tuple, dict, set):
			values = value if type(value) != dict else value.values()
			ret = [DestroyValue(val) for val in values]
			return any(ret)
		elif callable(value) and hasattr(value, '__self__'):
			return True
		return False

	def MakeEmptyValue(value):
		if type(value) in (list, tuple, dict, set):
			return type(value)()
		return None

	# skipping all non-window instances
	if not isinstance(instance, ui.Window):
		return

	# skipping all instances already destroyed
	if getattr(instance, "_SelfDestroyed", False):
		return

	# desroying the instance
	instance._SelfDestroyed = True
	for name, value in vars(instance).items():
		if value and DestroyValue(value):
			setattr(instance, name, MakeEmptyValue(value))

def IsPressingCTRL():
	return app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)

def IsPressingSHIFT():
	return app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT)

def GetInventoryItemHash(win, pos):
	vnum = player.GetItemIndex(win, pos)
	count = player.GetItemCount(win, pos)
	sockets = tuple(player.GetItemMetinSocket(win, pos, i) for i in xrange(player.METIN_SOCKET_MAX_NUM))
	attrs = tuple(player.GetItemAttribute(win, pos, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM))
	return ikashop.GetItemHash(vnum, count, sockets, attrs)

from localeinfo_point import AFFECT_DICT as AFFECT_DICT_OFFSHOP
def GetAttributeSettings():
	def NoFormat(str):
		removingStrings = ["%", "0", "+", ":"]
		for value in removingStrings:
			str = str.replace(value, "")
		return str.strip()

	values = []
	attributeDict = AFFECT_DICT_OFFSHOP
	for apply, text in attributeDict.items():
		if not isinstance(text, str):
			text = text(0)
		values.append((apply, NoFormat(text)))
	values.sort(key = lambda t : t[1])
	values = [(0, locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT),] + values
	return values

def IsUsingFilter(filters):
	for filter in filters:
		if isinstance(filter, tuple):
			if IsUsingFilter(filter):
				return True
		elif filter:
			return True
	return False

def ExtractInputPrice(dialog):
	if ENABLE_CHEQUE_SYSTEM:
		cheque = dialog.GetCheque()
		cheque = cheque.lower().replace("k", "000")
		cheque = int(cheque) if cheque and cheque.isdigit() else 0

	# extracting value
	value = dialog.GetText()
	value = value.lower().replace("k", "000")
	value = long(value) if value and value.isdigit() else 0

	if ENABLE_CHEQUE_SYSTEM:
		if cheque == 0 and value == 0:
			return False, None
		price = value, cheque
	else:
		if value == 0:
			return False, None
		price = value,
	return True, price

class IkarusShopWindow(ui.Window):

	HALIGN_SETTER = {
		"center" : ui.Window.SetWindowHorizontalAlignCenter,
		"right" : ui.Window.SetWindowHorizontalAlignRight,
	}

	VALIGN_SETTER = {
		"center" : ui.Window.SetWindowVerticalAlignCenter,
		"bottom" : ui.Window.SetWindowVerticalAlignBottom,
	}

	def _ApplyWidgetAlignments(self, child, halign, valign):
		if halign in self.HALIGN_SETTER:
			self.HALIGN_SETTER[halign](child)
		if valign in self.VALIGN_SETTER:
			self.VALIGN_SETTER(child)

	def _RegisterDialog(self, dialog):
		if not hasattr(self, "_dialogs"):
			self._dialogs = []
		self._dialogs.append(dialog)

	def SetTop(self):
		super(IkarusShopWindow, self).SetTop()
		if hasattr(self, "_dialogs"):
			for dialog in self._dialogs:
				dialog.SetTop()

	def Hide(self):
		super(IkarusShopWindow, self).Hide()
		if hasattr(self, "_dialogs"):
			for window in self._dialogs:
				window.Hide()

	def CreateWidget(self, type, x = 0, y = 0, show = True, pos = None, size = None, parent = None, halign = None, valign = None):
		child = type()
		child.SetParent(parent if parent else self)
		if show:
			child.Show()
		if size:
			child.SetSize(*size)
		self._ApplyWidgetAlignments(child, halign, valign)
		if pos:
			x,y = pos
		child.SetPosition(x,y)
		return child

	def Destroy(self):
		super(IkarusShopWindow, self).Destroy()
		# cleaning shitty undestroyable widgets
		if hasattr(self, "questionDialog"):
			SelfDestroyObject(self.questionDialog)
			del self.questionDialog
		if hasattr(self, "popupDialog"):
			SelfDestroyObject(self.popupDialog)
			del self.popupDialog
		if hasattr(self, "moneyInputDialog"):
			SelfDestroyObject(self.moneyInputDialog)
			del self.moneyInputDialog
		if hasattr(self, "itemToolTip"):
			SelfDestroyObject(self.itemToolTip)
			del self.itemToolTip
		# cleaning itself
		SelfDestroyObject(self)

	def OpenQuestionDialog(self, question, acceptEvent, denyEvent = None):
		if getattr(self, "questionDialog", None) == None:
			self.questionDialog = uicommon.QuestionDialog()
			self.questionDialog.SetAcceptText(locale.IKASHOP_QUESTION_DIALOG_CONTINUE_TEXT)
			self.questionDialog.SetCancelText(locale.IKASHOP_QUESTION_DIALOG_CANCEL_TEXT)
			self._RegisterDialog(self.questionDialog)
		self.questionDialog.SetText(question)
		self.questionDialog.SetWidth(self.questionDialog.textLine.GetTextSize()[0] + 40)
		self.questionDialog.SetAcceptEvent(acceptEvent)
		self.questionDialog.SetCancelEvent(denyEvent if denyEvent else self.questionDialog.Hide)
		self.questionDialog.Open()

	def OpenPopupDialog(self, message, seconds = 6):
		if getattr(self, "popupDialog", None) == None:
			self.popupDialog = uicommon.PopupDialog()
			self._RegisterDialog(self.popupDialog)
		self.popupDialog.SetText(message)
		self.popupDialog.SetWidth(self.popupDialog.message.GetTextSize()[0] + 40)
		self.popupDialog.Open()
		self.popupDialog.SetAutoClose(seconds)

	def OpenMoneyInputDialog(self, acceptEvent, denyEvent = None, value = 0, cheque = 0, nocheque = 0):
		# checking for gold overflow
		if ENABLE_CHEQUE_SYSTEM:
			if not nocheque:
				yangmax = 2**31
				while yangmax <= value:
					cheque += 1
					value -= ikashop.YANG_PER_CHEQUE

		if getattr(self, "moneyInputDialog", None) == None:
			self.moneyInputDialog = uicommon.MoneyInputDialog()
			self.moneyInputDialog.SetTitle(locale.IKASHOP_MONEY_INPUT_DIALOG_TITLE)
			self._RegisterDialog(self.moneyInputDialog)

		if ENABLE_CHEQUE_SYSTEM:
			self.moneyInputDialog.HideCheque() if nocheque \
				else self.moneyInputDialog.ShowCheque()

		self.moneyInputDialog.Open()
		self.moneyInputDialog.SetAcceptEvent(acceptEvent)
		self.moneyInputDialog.SetCancelEvent(denyEvent if denyEvent else self.moneyInputDialog.Hide)
		self.moneyInputDialog.SetValue(value if value != 0 else "")
		if ENABLE_CHEQUE_SYSTEM:
			self.moneyInputDialog.SetCheque(cheque if cheque != 0 else "")

	def GetToolTip(self):
		if getattr(self, "itemToolTip", None) == None:
			self.itemToolTip = uitooltip.ItemToolTip()
			self.itemToolTip.itemVnum = 1
			self._RegisterDialog(self.itemToolTip)
		return self.itemToolTip

	def Toggle(self):
		self.Close() if self.IsShow()\
			else self.Open()

	def ShowExclamationMark(self, pos = None):
		rpos = pos if pos else (self.GetWidth() - 14, 1)
		if not hasattr(self, "_ExclamationMark"):
			self._ExclamationMark = self.CreateWidget(ui.ImageBox, pos = rpos )
			self._ExclamationMark.LoadImage("ikashop/lite/mark.png")
		self._ExclamationMark.Show()

	def HideExclamationMark(self):
		if hasattr(self, '_ExclamationMark'):
			self._ExclamationMark.Hide()

if ENABLE_DEFAULT_UI_BOARD:
	class IkashopBoardWithTitleBar(IkarusShopWindow):
		def __init__(self):
			super(IkashopBoardWithTitleBar, self).__init__()
			self._LoadIkashopBoardWithTitleBar()

		def _LoadIkashopBoardWithTitleBar(self):
			self._internalBoard = self.CreateWidget(ui.BoardWithTitleBar, pos = (-2, -2))
			self._internalBoard.SetSize(self.GetWidth()+6, self.GetHeight()+4)

		def _UpdateView(self):
			if hasattr(self, "_internalBoard"):
				self._internalBoard.SetSize(self.GetWidth()+6, self.GetHeight()+4)

		def SetSize(self, w, h):
			super(IkashopBoardWithTitleBar, self).SetSize(w,h)
			self._UpdateView()

		def SetTitleName(self, title):
			self._internalBoard.SetTitleName(title)

		def SetCloseEvent(self, event, *args):
			self._internalBoard.SetCloseEvent(ui.__mem_func__(event, *args))

		def OnPressEscapeKey(self):
			if self.IsShow():
				self.Close()
				return True
			return False

else:
	class IkashopBoardWithTitleBar(IkarusShopWindow):

		SIDE_MARGIN = 16

		def __init__(self):
			super(IkashopBoardWithTitleBar, self).__init__()
			self._LoadIkashopBoardWithTitleBar()

		def _LoadIkashopBoardWithTitleBar(self):
			# loading center
			self.centerImage = self.CreateWidget(ui.ExpandedImageBox, x = 3, y = 30)
			self.centerImage.LoadImage("ikashop/lite/common/board/center.png")
			self.centerImage.AddFlag("not_pick")

			# loading sides
			self.leftSide = self.CreateWidget(ui.ExpandedImageBox, y = self.SIDE_MARGIN)
			self.leftSide.LoadImage("ikashop/lite/common/board/left.png")
			self.leftSide.AddFlag("not_pick")

			self.rightSide = self.CreateWidget(ui.ExpandedImageBox, y = self.SIDE_MARGIN)
			self.rightSide.LoadImage("ikashop/lite/common/board/right.png")
			self.rightSide.AddFlag("not_pick")

			self.bottomSide = self.CreateWidget(ui.ExpandedImageBox, x = self.SIDE_MARGIN)
			self.bottomSide.LoadImage("ikashop/lite/common/board/bottom.png")
			self.bottomSide.AddFlag("not_pick")

			# loading corners
			self.leftBottomCorner = self.CreateWidget(ui.ImageBox)
			self.leftBottomCorner.LoadImage("ikashop/lite/common/board/lb_corner.png")
			self.leftBottomCorner.AddFlag("not_pick")

			self.rightBottomCorner = self.CreateWidget(ui.ImageBox)
			self.rightBottomCorner.LoadImage("ikashop/lite/common/board/rb_corner.png")
			self.rightBottomCorner.AddFlag("not_pick")

			# loading titlebar
			self.titleLeft = self.CreateWidget(ui.ImageBox)
			self.titleLeft.LoadImage("ikashop/lite/common/board/titlebar/left.png")
			self.titleLeft.AddFlag("not_pick")

			self.titleRight = self.CreateWidget(ui.ImageBox)
			self.titleRight.LoadImage("ikashop/lite/common/board/titlebar/right.png")
			self.titleRight.AddFlag("not_pick")

			self.titleCenter = self.CreateWidget(ui.ExpandedImageBox, x = self.titleLeft.GetWidth())
			self.titleCenter.LoadImage("ikashop/lite/common/board/titlebar/center.png")
			self.titleCenter.AddFlag("not_pick")

			self.closeButton = self.CreateWidget(ui.Button, y = 3)
			self.closeButton.SetUpVisual("ikashop/lite/common/board/titlebar/close/default.png")
			self.closeButton.SetDownVisual("ikashop/lite/common/board/titlebar/close/default.png")
			self.closeButton.SetOverVisual("ikashop/lite/common/board/titlebar/close/hover.png")

			self.titleText = self.CreateWidget(ui.TextLine)
			self.titleText.SetHorizontalAlignCenter()
			self.titleText.SetFontName("Tahoma:20")
			self.titleText.SetPackedFontColor(0xFFFFFFFF)
			self.titleText.SetOutline(1)
			self.titleText.AddFlag("not_pick")

		def _UpdateView(self):
			if getattr(self, "centerImage", None) == None:
				return

			width = float(self.GetWidth())
			height = float(self.GetHeight())

			# updating center
			centerWidth = width - 6
			centerHeight = height - 33
			centerHorizontalScale = centerWidth / self.centerImage.GetWidth()
			centerVerticalScale = centerHeight / self.centerImage.GetHeight()
			self.centerImage.SetRenderingRect(0.0, 0.0, centerHorizontalScale - 1.0, centerVerticalScale - 1.0)

			# updating sides
			sideVerticalScale = (height - self.SIDE_MARGIN*2) / self.leftSide.GetHeight()
			self.leftSide.SetRenderingRect(0.0, 0.0, 0.0, sideVerticalScale - 1.0)
			sideVerticalScale = (height - self.SIDE_MARGIN*2) / self.rightSide.GetHeight()
			self.rightSide.SetRenderingRect(0.0, 0.0, 0.0, sideVerticalScale - 1.0)
			self.rightSide.SetPosition(width - self.rightSide.GetWidth(), self.SIDE_MARGIN)
			sideHorizontalScale = (width - self.SIDE_MARGIN*2) / self.bottomSide.GetWidth()
			self.bottomSide.SetRenderingRect(0.0, 0.0, sideHorizontalScale - 1.0, 0.0)
			self.bottomSide.SetPosition(self.SIDE_MARGIN, height - self.bottomSide.GetHeight())

			# updating corner positions
			self.leftBottomCorner.SetPosition(0, height - self.leftBottomCorner.GetHeight())
			self.rightBottomCorner.SetPosition(width - self.rightBottomCorner.GetWidth(), height - self.rightBottomCorner.GetHeight())

			# updating titlebar
			titlebarCenterWidth = width - self.titleLeft.GetWidth() - self.titleRight.GetWidth()
			titlebarCenterWidth = max(10, titlebarCenterWidth)
			titlebarCenterScale = titlebarCenterWidth / self.titleCenter.GetWidth()
			self.titleCenter.SetScale(titlebarCenterScale, 1.0)
			self.titleRight.SetPosition(titlebarCenterWidth + self.titleLeft.GetWidth(), 0)
			self.closeButton.SetPosition(width - self.closeButton.GetWidth() - 6, self.closeButton.GetLocalPosition()[1])
			self.titleText.SetPosition(width/2, 3)

		def SetSize(self, w, h):
			super(IkashopBoardWithTitleBar, self).SetSize(w,h)
			self._UpdateView()

		def SetTitleName(self, title):
			self.titleText.SetText(title)

		def SetCloseEvent(self, event, *args):
			self.closeButton.SetEvent(event, *args)

		def OnPressEscapeKey(self):
			if self.IsShow():
				self.Close()
				return True
			return False


class IkarusShopSafeboxBoard(IkashopBoardWithTitleBar):

	GRID_COLUMNS = ikashop.SAFEBOX_GRID_WIDTH
	GRID_ROWS = ikashop.SAFEBOX_GRID_HEIGHT
	PAGE_COUNT = ikashop.SAFEBOX_PAGE_COUNT


	def __init__(self):
		super(IkarusShopSafeboxBoard, self).__init__()
		self.items = []
		self._SettingUpBoard()
		self._LoadIkarusShopSafeboxBoard()

	def _SettingUpBoard(self):
		sw, sh = GetScreenSize()
		self.SetSize(324, 438)
		self.SetTitleName(locale.IKASHOP_SAFEBOX_BOARD_TITLE)
		self.SetCloseEvent(self.Close)
		self.SetPosition(sw/2 - self.GetWidth(), sh / 2 - self.GetHeight()/2)
		self.AddFlag("movable")
		self.AddFlag("float")

	def _LoadIkarusShopSafeboxBoard(self):
		# making slot box
		self.slotBox = self.CreateWidget(ui.ImageBox, pos = (11, 35))
		self.slotBox.LoadImage("ikashop/lite/safebox/slot_box.png")

		self.slotWindow = self.CreateWidget(ui.GridSlotWindow, parent = self.slotBox, pos = (6,6))
		self.slotWindow.ArrangeSlot(0, self.GRID_COLUMNS, self.GRID_ROWS, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slotWindow.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slotWindow.SetOverInItemEvent(self._ShowToolTipOnItemSlot)
		self.slotWindow.SetOverOutItemEvent(self._HideToolTipOnItemSlot)
		self.slotWindow.SetSelectItemSlotEvent(self._OnClickItemSlot)

		# making money box
		self.moneyBox = self.CreateWidget(ui.ImageBox, pos = (11, 404))
		self.moneyBox.LoadImage("ikashop/lite/safebox/money_box.png")
		mx, my = self.moneyBox.GetLocalPosition()

		self.moneyText = self.CreateWidget(ui.TextLine, parent = self.moneyBox, pos = (23, 4))
		self.moneyText.SetFontName("Tahoma:11")
		self.moneyText.SetPackedFontColor(0xFFFFFFFF)
		self.moneyText.SetText(locale.NumberToString(2**31))

		self.moneyClaimButton = self.CreateWidget(ui.Button, pos = (mx + self.moneyBox.GetWidth() + 2, my))
		self.moneyClaimButton.SetUpVisual("ikashop/lite/safebox/buttons/claim_money/default.png")
		self.moneyClaimButton.SetOverVisual("ikashop/lite/safebox/buttons/claim_money/hover.png")
		self.moneyClaimButton.SetDownVisual("ikashop/lite/safebox/buttons/claim_money/default.png")
		self.moneyClaimButton.SetToolTipText(locale.IKASHOP_SAFEBOX_CLAIM_MONEY_BUTTON_TEXT)
		self.moneyClaimButton.SetEvent(self._OnClickClaimMoneyButton)

		# making page selection box
		self.selectPageButtons = []
		for i in xrange(self.PAGE_COUNT):
			selectPageButton = self.CreateWidget(ui.Button, pos = (158 + i*41, 405))
			selectPageButton.SetUpVisual("ikashop/lite/safebox/buttons/select_page/default.png")
			selectPageButton.SetDownVisual("ikashop/lite/safebox/buttons/select_page/default.png")
			selectPageButton.SetOverVisual("ikashop/lite/safebox/buttons/select_page/hover.png")
			selectPageButton.SetDisableVisual("ikashop/lite/safebox/buttons/select_page/disabled.png")
			selectPageButton.SetText(RomeNumber(i+1))
			selectPageButton.SAFE_SetEvent(self._OnSelectPage, i)
			self.selectPageButtons.append(selectPageButton)

		# making claim items button
		self.itemsClaimButton = self.CreateWidget(ui.Button, pos = (158 + self.PAGE_COUNT*41 + 2, 405))
		self.itemsClaimButton.SetUpVisual("ikashop/lite/safebox/buttons/claim_items/default.png")
		self.itemsClaimButton.SetDownVisual("ikashop/lite/safebox/buttons/claim_items/default.png")
		self.itemsClaimButton.SetOverVisual("ikashop/lite/safebox/buttons/claim_items/hover.png")
		self.itemsClaimButton.SetToolTipText(locale.IKASHOP_SAFEBOX_CLAIM_ITEMS_BUTTON_TEXT)
		self.itemsClaimButton.SAFE_SetEvent(self._OnClickClaimAllItemsButton)

		# default opening first page
		self._OnSelectPage(0)

	def _OnSelectPage(self, num):
		for button in self.selectPageButtons:
			button.Enable()
		self.selectPageButtons[num].Disable()
		self.currentPage = num
		self._RefreshPage()

	def _RefreshPage(self):
		cells = self.GRID_COLUMNS * self.GRID_ROWS
		srange = cells * self.currentPage
		erange = srange + cells

		for i in xrange(srange, erange):
			local = i - srange
			if not i in self.items:
				self.slotWindow.ClearSlot(local)
				continue
			data = self.items[i]
			count = data['count'] if data['count'] > 1 else 0
			self.slotWindow.SetItemSlot(local, data['vnum'], count)

		self.slotWindow.RefreshSlot()

	def _RefreshItems(self, items):
		self.items = {item['cell'] : item for item in items}
		self._RefreshPage()

	def _ShowToolTipOnItemSlot(self, slot):
		slot = slot + self.currentPage * (self.GRID_COLUMNS * self.GRID_ROWS)
		if slot in self.items:
			data = self.items[slot]
			tooltip = self.GetToolTip()
			tooltip.ClearToolTip()
			tooltip.AddItemData(data['vnum'], data['sockets'], data['attrs'])
			tooltip.AppendTextLine(locale.IKASHOP_SAFEBOX_CLAIM_ITEM_TOOLTIP)
			tooltip.ShowToolTip()

	def _HideToolTipOnItemSlot(self, slot=0):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	def _OnClickItemSlot(self, cell):
		cell = cell + self.currentPage * (self.GRID_COLUMNS * self.GRID_ROWS)
		if cell in self.items:
			data = self.items[cell]
			ikashop.SendSafeboxGetItem(data['id'])

	def _OnClickClaimAllItemsButton(self):
		self.OpenQuestionDialog(
			locale.IKASHOP_SAFEBOX_CLAIM_ALL_ITEMS_QUESTION, self._OnAcceptClaimAllItemsQuestion)

	def _OnClickClaimMoneyButton(self):


		ikashop.SendSafeboxGetValutes()

	def _OnAcceptClaimAllItemsQuestion(self):
		self.questionDialog.Hide()
		for item in self.items.values():
			ikashop.SendSafeboxGetItem(item['id'])

	def Open(self):
		self.SetTop()
		if not self.IsShow():
			ikashop.SendSafeboxOpen()

	def Setup(self, yang, items):
		if not self.IsShow():
			self.Show()
			self.SetTop()

		self.moneyText.SetText(locale.NumberToString(yang))
		self._RefreshItems(items)

	def RemoveItem(self, itemid):
		items = [data for data in self.items.values() if data['id'] != itemid]
		self._RefreshItems(items)

	def AddItem(self, item):
		items = list(self.items.values()) + [item,]
		self._RefreshItems(items)

	def Destroy(self):
		super(IkarusShopSafeboxBoard, self).Destroy()

	def Close(self):
		ikashop.SendSafeboxClose()
		self.Hide()

class IkarusCreateAuctionDialog(IkashopBoardWithTitleBar):

	def __init__(self):
		super(IkarusCreateAuctionDialog, self).__init__()
		self._LoadIkarusCreateAuctionDialog()
		self._InsertedItem = None
		self._ItemInfo = None

	def _LoadIkarusCreateAuctionDialog(self):
		self._SettingUpBoard()

		# loading slot
		self.slot = self.CreateWidget(ui.GridSlotWindow, pos = (self.GetWidth()/2- 17, 45))
		self.slot.ArrangeSlot(0, 1, 3, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetSelectEmptySlotEvent(self._OnClickEmptySlot)
		self.slot.SetSelectItemSlotEvent(self._OnClickItemSlot)
		self.slot.SetOverInItemEvent(self._ShowToolTipOnItemSlot)
		self.slot.SetOverOutItemEvent(self._HideToolTipOnItemSlot)

		# loading continue button
		self.proceedButton = self.CreateWidget(ui.Button, pos = (self.GetWidth() / 2 - 53, self.GetHeight() - 40))
		self.proceedButton.SetUpVisual("ikashop/lite/auction/raise_button/default.png")
		self.proceedButton.SetDownVisual("ikashop/lite/auction/raise_button/default.png")
		self.proceedButton.SetOverVisual("ikashop/lite/auction/raise_button/hover.png")
		self.proceedButton.SetText(locale.IKASHOP_ACUTION_CREATE_CREATE_BUTTON)
		self.proceedButton.SAFE_SetEvent(self._OnClickCreateAuction)
		self.proceedButton.Show()
		self.proceedButton.ButtonText.SetPosition(self.proceedButton.GetWidth()/2 + 12, self.proceedButton.GetHeight()/2-1)

	def _SettingUpBoard(self):
		sw, sh = GetScreenSize()
		self.SetSize(145, 195)
		self.SetTitleName(locale.IKASHOP_AUCTION_CREATE_BOARD_TITLE)
		self.SetCloseEvent(self.Close)
		self.SetPosition(sw/2 - self.GetWidth()/2, sh / 2 - self.GetHeight()/2)
		self.AddFlag("movable")
		self.AddFlag("float")

	def _Reset(self):
		# reset slots
		for i in xrange(3):
			self.slot.ClearSlot(i)
		self.slot.RefreshSlot()

		if hasattr(self, "moneyInputDialog"):
			self.moneyInputDialog.SoftClose()

		self._InsertedItem = None
		self._ItemInfo = None

	def _OnClickEmptySlot(self, slot):
		if self._InsertedItem != None:
			return
		if mouse.mouseController.isAttached():
			attachedType = mouse.mouseController.GetAttachedType()
			attachedItemIndex = mouse.mouseController.GetAttachedItemIndex()
			attachedItemSlotPos = mouse.mouseController.GetAttachedSlotNumber()
			mouse.mouseController.DeattachObject()
			# validating attached item
			if attachedType in (player.SLOT_TYPE_DRAGON_SOUL_INVENTORY, player.SLOT_TYPE_INVENTORY):
				win, pos = player.SlotTypeToInvenType(attachedType), attachedItemSlotPos
				if player.ITEM_MONEY != attachedItemIndex:
					self.InsertItemInSlot(win, pos)

	def _OnClickItemSlot(self, slot):
		if mouse.mouseController.isAttached():
			return
		self._Reset()

	def _ShowToolTipOnItemSlot(self, slot):
		win, pos = self._InsertedItem
		tooltip = self.GetToolTip()
		tooltip.SetInventoryItem(pos, win)
		tooltip.AppendTextLine(locale.IKASHOP_AUCTION_CREATE_REMOVE_ITEM)

	def _HideToolTipOnItemSlot(self, slot = 0):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	def _OnClickCreateAuction(self):
		self.OpenMoneyInputDialog(self._OnAcceptStartingPriceInput, nocheque = 1)
	def _OnAcceptStartingPriceInput(self):
		# extracting value
		value = self.moneyInputDialog.GetText()
		value = value.lower().replace("k", "000")
		self.moneyInputDialog.SoftClose()

		# validating value
		if not value or not value.isdigit():
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INVALID_ITEM_PRICE)
			return

		if self._InsertedItem is None:
			return

		win, pos = self._InsertedItem

		self.Close()
		ikashop.SendAuctionCreate(win, pos, long(value))
		return True

	def InsertItemInSlot(self, win, pos):
		vnum = player.GetItemIndex(win, pos)
		count = player.GetItemCount(win, pos)

		# checking item antifalg
		item.SelectItem(vnum)
		if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_CANNOT_SELL_ITEM)
			return

		self._InsertedItem = win, pos
		self._ItemInfo = vnum, count, GetInventoryItemHash(win, pos)

		self.slot.SetItemSlot(0, vnum, count if count > 1 else 0)
		self.slot.RefreshSlot()

	def Open(self):
		self._Reset()
		self.Show()
		self.SetTop()
		if app.EXTEND_IKASHOP_PRO:
			player.RefreshInventory()

	def Close(self):
		self.Hide()
		if app.EXTEND_IKASHOP_PRO:
			player.RefreshInventory()

	def OnUpdate(self):
		if self._ItemInfo != None:
			win, pos = self._InsertedItem
			vnum, count, hash = self._ItemInfo

			if vnum != player.GetItemIndex(win, pos):
				self._Reset()
			elif count != player.GetItemCount(win, pos):
				self._Reset()
			elif hash != GetInventoryItemHash(win, pos):
				self._Reset()


class IkarusShopAuctionOfferView(IkarusShopWindow):

	def __init__(self):
		super(IkarusShopAuctionOfferView, self).__init__()
		self._LoadIkarusShopAuctionOfferView()

	def _LoadIkarusShopAuctionOfferView(self):
		# making background and fitting its size
		self.background = self.CreateWidget(ui.ImageBox, pos = ())
		self.background.LoadImage("ikashop/lite/auction/offer_box.png")
		self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		# making name text
		self.nameText = self.CreateWidget(ui.TextLine, pos = (28, 5))
		self.nameText.SetPackedFontColor(0xFFFFFFFF)
		self.nameText.SetFontName("Tahoma:11")

		# making datetime
		self.datetimeText = self.CreateWidget(ui.TextLine, pos = (168 + 13, 5))
		self.datetimeText.SetPackedFontColor(0xFFFFFFFF)
		self.datetimeText.SetHorizontalAlignCenter()

		# making money text
		self.moneyText = self.CreateWidget(ui.TextLine, pos = (256 + 13, 5))
		self.moneyText.SetPackedFontColor(0xFFFFFFFF)

	def Setup(self, pos, data):
		name, datetime, price = data['buyername'], data['datetime'], data['price']
		self.nameText.SetText("{}. {}".format(pos, name))
		self.datetimeText.SetText(DatetimeFormat(datetime))
		self.moneyText.SetText(locale.NumberToString(price))
		self.Show()

class IkarusShopAuctionOwnerBoard(IkashopBoardWithTitleBar):
	OFFER_VIEW_COUNT = 6
	OFFER_VIEW_HEIGHT = 28
	RAISE_FACTOR = 1.0 + float(AUCTION_MIN_RAISE_PERCENTAGE) / 100.0

	def __init__(self):
		super(IkarusShopAuctionOwnerBoard, self).__init__()
		self._SettingUpBoard()
		self._LoadIkarusShopAuctionOwnerBoard()

	def _SettingUpBoard(self):
		sw, sh = GetScreenSize()
		self.SetSize(513 + 13, 249)
		self.SetTitleName(locale.IKASHOP_AUCTION_BOARD_TITLE)
		self.SetCloseEvent(self.Close)
		self.SetPosition(sw/2 - self.GetWidth(), sh / 2 - self.GetHeight()/2 + 100)
		self.AddFlag("movable")
		self.AddFlag("float")

	def _LoadIkarusShopAuctionOwnerBoard(self):
		# making info box
		self.infoBox = self.CreateWidget(ui.ImageBox, pos = (12, 36))
		self.infoBox.LoadImage("ikashop/lite/auction/info_box.png")
		self.infoBox.SetMouseWheelEvent(self._MouseWheelScrollOffers)

		self.minRaiseText = self.CreateWidget(ui.TextLine, pos = (458+13, 221-36), parent = self.infoBox)
		self.minRaiseText.SetPackedFontColor(0xFFFFFFFF)
		self.minRaiseText.SetHorizontalAlignRight()

		self.durationText = self.CreateWidget(ui.TextLine, pos = (141, 221-36), parent = self.infoBox)
		self.durationText.SetPackedFontColor(0xFFFFFFFF)

		# making slot
		self.slot = self.CreateWidget(ui.GridSlotWindow, pos = (36, 44), size = (32, 98), parent = self.infoBox)
		self.slot.ArrangeSlot(0, 1, 3, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetOverInItemEvent(self._OverInItem)
		self.slot.SetOverOutItemEvent(self._OverOutItem)

		# making scrollbar
		self.offerScrollbar = self.CreateWidget(ui.ScrollBar, pos = (470+13, 4), parent = self.infoBox)
		self.offerScrollbar.SetScrollBarSize(self.infoBox.GetHeight() - 35)
		self.offerScrollbar.SetScrollEvent(self._ScrollOffers)

		# making cancel auction button
		self.cancelAuctionButton = self.CreateWidget(ui.Button, pos = (12, self.GetHeight() - 33))
		self.cancelAuctionButton.SetUpVisual("ikashop/lite/auction/cancel_button/default.png")
		self.cancelAuctionButton.SetDownVisual("ikashop/lite/auction/cancel_button/default.png")
		self.cancelAuctionButton.SetOverVisual("ikashop/lite/auction/cancel_button/hover.png")
		self.cancelAuctionButton.SetText(locale.IKASHOP_ACUTION_CANCEL_AUCTION_BUTTON)
		self.cancelAuctionButton.SAFE_SetEvent(self._OnClickCancelAuction)
		self.cancelAuctionButton.Show()

		# making offers
		self.offerViews = []
		for i in xrange(self.OFFER_VIEW_COUNT):
			self.offerViews.append(self.CreateWidget(
				IkarusShopAuctionOfferView, pos = (115, 6 + i*self.OFFER_VIEW_HEIGHT), parent = self.infoBox))

	def _RefreshOffers(self):
		# calculating count difference
		diff = len(self.offers) - self.OFFER_VIEW_COUNT
		diff = max(diff, 0)

		# calculating ranges
		offset = self.offerScrollbar.GetPos()
		sindex = int(diff * offset)
		eindex = sindex + min(self.OFFER_VIEW_COUNT, len(self.offers))

		# iterating over views
		for i, view in enumerate(self.offerViews):
			ri = i + sindex
			view.Hide() if ri >= eindex \
				else view.Setup(ri+1, self.offers[ri])

		# updating scrollbar middlebar length
		viewHeight = self.OFFER_VIEW_HEIGHT
		self.offerScrollbar.UpdateScrollbarLenght(viewHeight * len(self.offers))

	def _MouseWheelScrollOffers(self, delta):
		if self.offerScrollbar.IsShow():
			self.offerScrollbar.OnDown() if delta < 0 \
				else self.offerScrollbar.OnUp()
		return True

	def _ScrollOffers(self):
		if self.offerScrollbar.IsShow():
			self._RefreshOffers()

	def _UpdateScrollbarState(self):
		self.offerScrollbar.SetPos(0)
		if len(self.offers) <= self.OFFER_VIEW_COUNT:
			self.offerScrollbar.Hide()
		else:
			self.offerScrollbar.Show()

	def _OverInItem(self, slot):
		data = self.auctionInfo
		tooltip = self.GetToolTip()
		tooltip.ClearToolTip()
		tooltip.AddItemData(data['vnum'], data['sockets'], data['attrs'])
		tooltip.ShowToolTip()

	def _OverOutItem(self, slot = 0):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	def _OnClickCancelAuction(self):
		if self.auctionInfo['offers']:
			self.OpenPopupDialog(locale.IKASHOP_AUCTION_CANNOT_CANCEL)
			return

		self.OpenQuestionDialog(locale.IKASHOP_AUCTION_CANCEL_AUCTION_QUESTION, self._OnAcceptCancelAuction)

	def _OnAcceptCancelAuction(self):
		ikashop.SendMyAuctionCancel()
		self.questionDialog.Close()
		self.Close()

	def SetOffers(self, offers):
		self.offers = sorted(offers, key = lambda val : val['datetime'], reverse=True)
		self._UpdateScrollbarState()
		self._RefreshOffers()
		self.RefreshMinRaise()

	def SetDuration(self, duration):
		self.durationText.SetText(locale.SecondToDHM(duration*60))

	def _GetMinRaise(self):
		if not self.offers:
			return self.auctionInfo['price']

		minraise = max([val['price'] for val in self.offers])
		if minraise < 1000:
			return minraise + 1000

		return minraise * (100+AUCTION_MIN_RAISE_PERCENTAGE) / 100

	def RefreshMinRaise(self):
		self.minRaise = self._GetMinRaise()
		self.minRaiseText.SetText(locale.IKASHOP_AUCTION_MIN_BID + '  ' + locale.NumberToString(self.minRaise))

	def Open(self):
		ikashop.SendMyAuctionOpen()

	def Close(self):
		self.Hide()
		ikashop.SendMyAuctionClose()

	def Setup(self, data):
		# storing data
		self.auctionInfo = data

		# refreshing duration
		seconds = data['duration'] * 60
		self.durationText.SetText(locale.SecondToDHM(seconds))

		# refreshing item
		vnum = data['vnum']
		count = data['count'] if data['count'] > 1 else 0
		item.SelectItem(vnum)
		size = item.GetItemSize()[1]
		self.slot.ArrangeSlot(0, 1, size, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetItemSlot(0, vnum, count)

		# refreshing offers
		self.SetOffers(data['offers'])

		if not self.IsShow():
			self.Show()
			self.SetTop()

class IkarusShopListBoard(IkashopBoardWithTitleBar):

	def _LoadIkarusShopListBoard(self):
		# making board box
		self.boardBox = self.CreateWidget(ui.ExpandedImageBox, pos = (11,36))
		self.boardBox.LoadImage("ikashop/lite/list_box.png")
		boardBoxHorizontalScale = float(self.GetWidth() - 22 - 16) / self.boardBox.GetWidth()
		boardBoxVerticalScale =  float(self.GetHeight() - 47) / self.boardBox.GetHeight()
		self.boardBox.SetScale(boardBoxHorizontalScale, boardBoxVerticalScale)
		self.boardBox.SetMouseWheelEvent(self._MouseWheelScrollElements)

		# making scrollbar
		self.elementScrollbar = self.CreateWidget(ui.ScrollBar, pos = (self.GetWidth() - 24, 36))
		self.elementScrollbar.SetScrollBarSize(self.boardBox.GetHeight())
		self.elementScrollbar.SetScrollEvent(self._ScrollElements)

		# making empty header
		self.emptyHeader = self.CreateWidget(ui.TextLine, pos = (self.GetWidth()/2, self.GetHeight()/2 - 10))
		self.emptyHeader.SetFontName("Tahoma:14")
		self.emptyHeader.SetPackedFontColor(0xFFFFFFFF)
		self.emptyHeader.SetOutline(1)
		self.emptyHeader.SetHorizontalAlignCenter()
		self.emptyHeader.SetVerticalAlignCenter()
		self.emptyHeader.SetText(locale.IKASHOP_GENERIC_LIST_EMPTY_HEADER)

	def _SettingUpBoard(self):
		sw, sh = GetScreenSize()
		self.SetCloseEvent(getattr(self, "Close", self.Hide))
		self.SetPosition(sw/2 + 20 - (self.GetWidth() - 200), sh / 2 - self.GetHeight()/2)
		self.AddFlag("movable")
		self.AddFlag("float")

	def _MakeListElements(self, type, viewCount):
		self.viewCount = viewCount
		# making notifiction boxes
		self.views = []
		for i in xrange(self.viewCount):
			view = self.CreateWidget(type, parent = self.boardBox)
			space = view.GetHeight()+2
			view.SetPosition(9, 7 + i * space)
			self.views.append(view)

	def _ScrollElements(self):
		if self.elementScrollbar.IsShow():
			self._RefreshElements()

	def _MouseWheelScrollElements(self, delta):
		if self.elementScrollbar.IsShow():
			self.elementScrollbar.OnDown() if delta < 0 \
				else self.elementScrollbar.OnUp()
		return True

	def _UpdateScrollbarState(self):
		if len(self.elements) <= self.viewCount:
			self.elementScrollbar.SetPos(0)
			self.elementScrollbar.Hide()
		else:
			self.elementScrollbar.Show()

	def _RefreshElements(self):
		# calculating count difference
		diff = len(self.elements) - self.viewCount
		diff = max(diff, 0)

		# calculating ranges
		offset = self.elementScrollbar.GetPos()
		sindex = int(diff * offset)
		eindex = sindex + min(self.viewCount, len(self.elements))

		# iterating over views
		for i, view in enumerate(self.views):
			ri = i + sindex
			if ri >= eindex:
				view.Hide()
			else:
				view.Setup(self.elements[ri])
				view.Show()

		# updating scrollbar middlebar length
		viewHeight = self.views[0].GetHeight()+2
		self.elementScrollbar.UpdateScrollbarLenght(viewHeight * len(self.elements))

	def SetElements(self, elements):
		self.elements = elements
		self._UpdateScrollbarState()
		self._RefreshElements()

		self.emptyHeader.Show() if not elements \
			else self.emptyHeader.Hide()


class IkarusShopOfferView(IkarusShopWindow):

	def __init__(self):
		super(IkarusShopOfferView, self).__init__()
		self._LoadIkarusShopOfferView()

	def _LoadIkarusShopOfferView(self):
		# making background
		self.background = self.CreateWidget(ui.ExpandedImageBox)
		self.background.LoadImage("ikashop/lite/search_shop/result_item_box.png")
		self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		# making textlines
		self.itemName = self.CreateWidget(ui.TextLine, pos = (60, 17 - 6))
		self.itemName.SetPackedFontColor(0xFFFFFFFF)
		self.sellerName = self.CreateWidget(ui.TextLine, pos = (78, 41 - 6))
		self.duration = self.CreateWidget(ui.TextLine, pos = (226, 41 - 6))
		self.price = self.CreateWidget(ui.TextLine, pos = (78, 58))

		# making buttons
		self.acceptOfferButton = self.CreateWidget(ui.Button, pos = (261, 84))
		self.acceptOfferButton.SetUpVisual("ikashop/lite/search_shop/buy_button/default.png")
		self.acceptOfferButton.SetDownVisual("ikashop/lite/search_shop/buy_button/default.png")
		self.acceptOfferButton.SetOverVisual("ikashop/lite/search_shop/buy_button/hover.png")
		self.acceptOfferButton.SAFE_SetEvent(self._OnClickAcceptOffer)
		self.acceptOfferButton.SetText(locale.IKASHOP_OFFER_LIST_ACCEPT_OFFER_BUTTON_TEXT)

		self.cancelOfferButton = self.CreateWidget(ui.Button, pos = (189, 84))
		self.cancelOfferButton.SetUpVisual("ikashop/lite/search_shop/offer_button/default.png")
		self.cancelOfferButton.SetDownVisual("ikashop/lite/search_shop/offer_button/default.png")
		self.cancelOfferButton.SetOverVisual("ikashop/lite/search_shop/offer_button/hover.png")
		self.cancelOfferButton.SAFE_SetEvent(self._OnClickCancelButton)
		self.cancelOfferButton.SetText(locale.IKASHOP_SEARCH_SHOP_OFFER_BUTTON_TEXT)

		# making slot item
		self.slot = self.CreateWidget(ui.GridSlotWindow, pos = (9, 7))
		self.slot.ArrangeSlot(0, 1, 3, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetOverInItemEvent(self._OverInItem)
		self.slot.SetOverOutItemEvent(self._OverOutItem)

	def _OverInItem(self, slot):
		tooltip = self.GetToolTip()
		tooltip.ClearToolTip()
		tooltip.AddItemData(self.itemData['vnum'], self.itemData['sockets'], self.itemData['attrs'])
		tooltip.ShowToolTip()

	def _OverOutItem(self):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	def _OnClickAcceptOffer(self):
		self.OpenQuestionDialog(locale.IKASHOP_OFFER_LIST_ACCEPT_OFFER_QUESTION, self._OnAcceptOffer)

	def _OnClickCancelButton(self):
		self.OpenQuestionDialog(locale.IKASHOP_OFFER_LIST_CANCEL_OFFER_QUESTION, self._OnCancelOffer)

	def _OnAcceptOffer(self):
		self.questionDialog.Hide()
		ikashop.SendOfferAccept(self.data['id'])

	def _OnCancelOffer(self):
		self.questionDialog.Hide()
		ikashop.SendOfferCancel(self.data['id'], self.data['ownerid'])

	def Setup(self, data):
		self.ShowExclamationMark() if data['incoming']\
			else self.HideExclamationMark()

		self.acceptOfferButton.Show() if data['incoming']\
			else self.acceptOfferButton.Hide()

		self.cancelOfferButton.SetText(locale.IKASHOP_OFFER_LIST_DENY_OFFER_BUTTON_TEXT) if data['incoming']\
			else self.cancelOfferButton.SetText(locale.IKASHOP_OFFER_LIST_CANCEL_OFFER_BUTTON_TEXT)

		self.cancelOfferButton.SetPosition(189, 84) if data['incoming']\
			else self.cancelOfferButton.SetPosition(261, 84)

		self.background.LoadImage("ikashop/lite/offer_list/incoming_offer.png") if data['incoming']\
			else self.background.LoadImage("ikashop/lite/offer_list/outcoming_offer.png")

		# setting itemname
		itemData = data['item']
		item.SelectItem(itemData['vnum'])
		itemName = item.GetItemName()
		self.itemName.SetText(itemName)

		# setting seller name
		self.sellerName.SetText(data['buyer_name']) if data['incoming']\
			else self.sellerName.SetText(data['name'])

		# setting duration
		self.duration.SetText(DatetimeFormat(data['datetime']))

		# setting price
		self.price.SetText(locale.NumberToString(data['price']))

		# setting slot
		itemcount = itemData['count'] if itemData['count'] > 1 else 0
		self.slot.ArrangeSlot(0, 1, item.GetItemSize()[1], SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetItemSlot(0, itemData['vnum'], itemcount)
		self.data = data
		self.itemData = itemData

class IkarusShopOffersBoard(IkarusShopListBoard):

	OFFER_VIEW_COUNT = 3

	def __init__(self):
		super(IkarusShopOffersBoard, self).__init__()
		self._SettingUpBoard()
		self._LoadIkarusShopOffersBoard()

	def _SettingUpBoard(self):
		self.SetSize(395, 399)
		self.SetTitleName(locale.IKASHOP_OFFER_LIST_BOARD_TITLE)
		super(IkarusShopOffersBoard, self)._SettingUpBoard()

	def _LoadIkarusShopOffersBoard(self):
		self._LoadIkarusShopListBoard()
		self._MakeListElements(IkarusShopOfferView, self.OFFER_VIEW_COUNT)

	def SetOffers(self, offers):
		self.offers = sorted(offers, key = lambda val : val['datetime'], reverse=True)
		self.SetElements(self.offers)
		self.Show()
		self.SetTop()

	def Open(self):
		ikashop.SendOfferListRequest()

	def Close(self):
		self.Hide()
		ikashop.SendOffersListClose()

if app.EXTEND_IKASHOP_PRO:
	class IkarusShopNotificationView(IkarusShopWindow):


		def __init__(self):
			super(IkarusShopNotificationView, self).__init__()
			self._LoadIkarusShopNotificationView()

		def _LoadIkarusShopNotificationView(self):
			# making background and fitting its size
			self.background = self.CreateWidget(ui.ImageBox)
			self.background.LoadImage("ikashop/pro/notification/notification_box.png")
			self.SetSize(self.background.GetWidth(), self.background.GetHeight())

			# making what
			self.whatText = self.CreateWidget(ui.TextLine, pos = (9, 5))
			self.whatText.SetPackedFontColor(0xFFFFFFFF)

			# making datetime
			self.datetimeText = self.CreateWidget(ui.TextLine, pos = (405-11, 5))
			self.datetimeText.SetPackedFontColor(0xFFFFFFFF)
			self.datetimeText.SetHorizontalAlignCenter()

		def Setup(self, data):
			def GetItemName(what):
				if what == 0:
					return ""
				item.SelectItem(what)
				return item.GetItemName()

			def extractPriceString(format):
				if ENABLE_CHEQUE_SYSTEM:
					s = format.split("|")
					money = long(s[0])
					cheque = long(s[1]) if len(s) > 1 else 0
					price = ""
					if money != 0:
						price += locale.NumberToMoneyString(money)
					if cheque != 0:
						if price:
							price += ', '
						price += locale.NumberToCheque(cheque)
					return price
				return locale.NumberToMoneyString(long(format))

			self.data = data
			itemname = GetItemName(data['what'])
			if data['type'] == ikashop.NOTIFICATION_SELLER_SELLER_SOLD_ITEM:
				price = extractPriceString(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_SOLD_ITEM.format(itemname, price)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_NEW_OFFER_ON_ITEM:
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_NEW_OFFER_ON_ITEM.format(itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_SHOP_EXPIRED:
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_SHOP_EXPIRED
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_ITEM_EXPIRED:
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_ITEM_EXPIRED.format(itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_AUCTION_NEW_OFFER:
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_AUCTION_NEW_OFFER.format(itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_AUCTION_EXPIRED:
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_AUCTION_EXPIRED.format(itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_AUCTION_SOLD:
				price = long(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_AUCTION_SOLD.format(itemname, data['who'], locale.NumberToMoneyString(price))
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_SELLER_OFFER_CANCELLED:
				message = locale.IKASHOP_PRO_NOTIFICATION_SELLER_OFFER_CANCELLED.format(itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_BUYER_OFFER_DENIED:
				price = long(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_BUYER_OFFER_DENIED.format(locale.NumberToMoneyString(price), itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_BUYER_OFFER_ACCEPTED:
				price = long(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_BUYER_OFFER_ACCEPTED.format(locale.NumberToMoneyString(price), itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_BUYER_OFFER_EXPIRED:
				price = long(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_BUYER_OFFER_EXPIRED.format(locale.NumberToMoneyString(price), itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_BUYER_AUCTION_BUY:
				price = long(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_BUYER_AUCTION_BUY.format(itemname, locale.NumberToMoneyString(price))
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_BUYER_AUCTION_RAISE:
				message = locale.IKASHOP_PRO_NOTIFICATION_BUYER_AUCTION_RAISE.format(data['who'], itemname)
				self.whatText.SetText(message)
			elif data['type'] == ikashop.NOTIFICATION_BUYER_AUCTION_LOST:
				price = long(data['format'])
				message = locale.IKASHOP_PRO_NOTIFICATION_BUYER_AUCTION_LOST.format(data['who'], itemname, locale.NumberToMoneyString(price))
				self.whatText.SetText(message)

			self.datetimeText.SetText(DatetimeFormat(data['datetime']))
			self.ShowExclamationMark() if not data['seen']\
				else self.HideExclamationMark()


	class IkarusShopNotificationBoard(IkarusShopListBoard):

		NOTIFICATION_VIEW_COUNT = 10

		def __init__(self):
			super(IkarusShopNotificationBoard, self).__init__()
			ikashop.LoadNotifications()
			self._SettingUpBoard()
			self._LoadIkarusShopNotificationBoard()

		def _SettingUpBoard(self):
			self.SetSize(494, 330)
			self.SetTitleName(locale.IKASHOP_PRO_NOTIFICATION_BOARD_TITLE)
			super(IkarusShopNotificationBoard, self)._SettingUpBoard()

		def _LoadIkarusShopNotificationBoard(self):
			self._LoadIkarusShopListBoard()
			self._MakeListElements(IkarusShopNotificationView, self.NOTIFICATION_VIEW_COUNT)

		def SetNotifications(self, notifications):
			cached = ikashop.GetNotifications()
			for i, notification in enumerate(notifications):
				type = notification['type']
				who = notification['who']
				what = notification['what']
				format = notification['format']
				datetime = notification['datetime']
				save = i == len(notifications)-1
				ikashop.RegisterNotification(type, who, what, format, datetime, save)
			notifications = cached + notifications
			self.notifications = sorted(notifications, key = lambda val : val['datetime'], reverse=True)
			self.SetElements(self.notifications)
			self.Show()
			self.SetTop()

		def Open(self):
			ikashop.SendNotificationListRequest()

		def Close(self):
			self.Hide()
			ikashop.SendNotificationListClose()

class IkarusShopCounter(IkarusShopWindow):
	def __init__(self):
		super(IkarusShopCounter, self).__init__()
		self._LoadIkarusShopCounter()

	def _LoadIkarusShopCounter(self):
		self.background = self.CreateWidget(ui.ImageBox)
		self.background.LoadImage("ikashop/lite/business/counter.png")

		self.counter = self.CreateWidget(ui.TextLine)
		self.counter.SetOutline(1)
		self.counter.SetPackedFontColor(0xFFFFFFFF)
		self.counter.SetPosition(self.background.GetWidth()/2, self.background.GetHeight()/2 - 1)
		self.counter.SetHorizontalAlignCenter()
		self.counter.SetVerticalAlignCenter()

	def SetCounter(self, count):
		if count == 0:
			self.Hide()
		else:
			self.counter.SetText(str(count) if count <= 9 else "9+")
			self.Show()

class IkarusShopBusinessBoard(IkashopBoardWithTitleBar):

	GRID_COLUMNS = ikashop.SHOP_GRID_WIDTH
	GRID_ROWS = ikashop.SHOP_GRID_HEIGHT
	PAGE_SIZE = GRID_COLUMNS * GRID_ROWS

	def __init__(self):
		super(IkarusShopBusinessBoard, self).__init__()
		if app.EXTEND_IKASHOP_PRO:
			self.editedMarkedInfo = None
			self.editedMarkedTime = None
			self.editedMarkedColor = None
			self.removingItemList = []
		self._SettingUpBoard()
		self._LoadLinkedBoards()
		self._LoadShopBusinessWindow()
		# ikashop.SetBusinessBoard(self)

	def __del__(self):
		super(IkarusShopBusinessBoard, self).__del__()
		ikashop.SetBusinessBoard(None)

	def _SettingUpBoard(self):
		self.SetSize(558, 404)
		self.SetTitleName(locale.IKASHOP_BUSINESS_BOARD_TITLE)
		self.SetCloseEvent(self.Close)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")

	def _LoadShopBusinessWindow(self):
		# making slot box
		self.slotBox = self.CreateWidget(ui.ImageBox, pos = (55,35 + 27))
		self.slotBox.LoadImage("ikashop/lite/business/slot_box.png")
		self.slotWindow = self.CreateWidget(ui.GridSlotWindow, parent = self.slotBox, pos = (6,6))
		self.slotWindow.ArrangeSlot(0, self.GRID_COLUMNS, self.GRID_ROWS, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slotWindow.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slotWindow.SetSelectEmptySlotEvent(self._OnClickEmptySlot)
		self.slotWindow.SetSelectItemSlotEvent(self._OnClickItemSlot)
		self.slotWindow.SetOverInItemEvent(self._ShowToolTipOnItemSlot)
		self.slotWindow.SetOverOutItemEvent(self._HideToolTipOnItemSlot)
		self.slotWindow.SetUnselectItemSlotEvent(self._OnRightClickItemSlot)

		# making duration box
		self.durationBox = self.CreateWidget(ui.ImageBox, pos = (55,35))
		self.durationBox.LoadImage("ikashop/lite/business/duration_box.png")

		self.durationText = self.CreateWidget(ui.TextLine, parent = self.durationBox, pos = (30, 4))
		self.durationText.SetPackedFontColor(0xFFFFFFFF)
		self.durationText.SetText("11d 22h 18m")

		self.durationExpiredIcon = self.CreateWidget(ui.ImageBox, pos = (168 - 49, 3), parent = self.durationBox)
		self.durationExpiredIcon.LoadImage("ikashop/lite/business/expired_icon.png")

		self.durationIncreaseButton = self.CreateWidget(ui.Button, parent = self.durationBox, pos = (189 - 49, 3))
		self.durationIncreaseButton.SetUpVisual("ikashop/lite/business/buttons/duration_up/default.png")
		self.durationIncreaseButton.SetDownVisual("ikashop/lite/business/buttons/duration_up/default.png")
		self.durationIncreaseButton.SetOverVisual("ikashop/lite/business/buttons/duration_up/hover.png")
		self.durationIncreaseButton.SetToolTipText(locale.IKASHOP_BUSINESS_DURATION_INCREASE_BUTTON_TEXT)
		self.durationIncreaseButton.SetEvent(self._OnClickDurationIncreaseButton)
		self.durationIncreaseButton.ToolTipText.SetOutline(1)

		# making bottom bar buttons
		self.cancelShopButton = self.CreateWidget(ui.Button, pos = (604 - 92, 35))
		self.cancelShopButton.SetUpVisual("ikashop/lite/business/buttons/cancel_shop/default.png")
		self.cancelShopButton.SetDownVisual("ikashop/lite/business/buttons/cancel_shop/default.png")
		self.cancelShopButton.SetOverVisual("ikashop/lite/business/buttons/cancel_shop/hover.png")
		self.cancelShopButton.SetToolTipText(locale.IKASHOP_BUSINESS_CANCEL_SHOP_BUTTON_TEXT)
		self.cancelShopButton.SAFE_SetEvent(self._OnClickCancelShopButton)
		self.cancelShopButton.ToolTipText.SetOutline(1)

		if app.EXTEND_IKASHOP_PRO:
			self.moveShopButton = self.CreateWidget(ui.Button, pos = (604 - 95 - self.cancelShopButton.GetWidth(), 35))
			self.moveShopButton.SetUpVisual("ikashop/lite/business/buttons/move_shop/default.png")
			self.moveShopButton.SetDownVisual("ikashop/lite/business/buttons/move_shop/default.png")
			self.moveShopButton.SetOverVisual("ikashop/lite/business/buttons/move_shop/hover.png")
			self.moveShopButton.SetToolTipText(locale.IKASHOP_PRO_BUSINESS_MOVE_SHOP_BUTTON_TEXT)
			self.moveShopButton.SAFE_SetEvent(self._OnClickMoveShopButton)
			self.moveShopButton.ToolTipText.SetOutline(1)

		# making sidebar buttons
		self.safeboxOpenButton = self.CreateWidget(ui.Button, pos = (7, 37))
		self.safeboxOpenButton.SetUpVisual("ikashop/lite/business/buttons/safebox/default.png")
		self.safeboxOpenButton.SetDownVisual("ikashop/lite/business/buttons/safebox/default.png")
		self.safeboxOpenButton.SetOverVisual("ikashop/lite/business/buttons/safebox/hover.png")
		self.safeboxOpenButton.SAFE_SetEvent(self.safeboxBoard.Toggle)
		self.safeboxOpenButton.SetToolTipText(locale.IKASHOP_BUSINESS_SAFEBOX_OPEN_BUTTON_TEXT)
		self.safeboxOpenButton.ToolTipText.SetOutline(1)

		self.privateOfferOpenButton = self.CreateWidget(ui.Button, pos = (7, 37 + 33))
		self.privateOfferOpenButton.SetUpVisual("ikashop/lite/business/buttons/offer/default.png")
		self.privateOfferOpenButton.SetDownVisual("ikashop/lite/business/buttons/offer/default.png")
		self.privateOfferOpenButton.SetOverVisual("ikashop/lite/business/buttons/offer/hover.png")
		self.privateOfferOpenButton.SAFE_SetEvent(self.offersBoard.Toggle)
		self.privateOfferOpenButton.SetToolTipText(locale.IKASHOP_BUSINESS_PRIVATE_OFFER_OPEN_BUTTON_TEXT)
		self.privateOfferOpenButton.ToolTipText.SetOutline(1)

		self.auctionOpenButton = self.CreateWidget(ui.Button, pos = (7, 37 + 33*2))
		self.auctionOpenButton.SetUpVisual("ikashop/lite/business/buttons/auction/default.png")
		self.auctionOpenButton.SetDownVisual("ikashop/lite/business/buttons/auction/default.png")
		self.auctionOpenButton.SetOverVisual("ikashop/lite/business/buttons/auction/hover.png")
		self.auctionOpenButton.SAFE_SetEvent(self.auctionBoard.Toggle)
		self.auctionOpenButton.SetToolTipText(locale.IKASHOP_BUSINESS_AUCTION_OPEN_BUTTON_TEXT)
		self.auctionOpenButton.ToolTipText.SetOutline(1)

		self.safeboxItemCounter = self.CreateWidget(IkarusShopCounter, pos = (25, 0), parent = self.safeboxOpenButton)
		self.privateOfferCounter = self.CreateWidget(IkarusShopCounter, pos = (25, 0), parent = self.privateOfferOpenButton)
		self.auctionOfferCounter = self.CreateWidget(IkarusShopCounter, pos = (25, 0), parent = self.auctionOpenButton)

		if app.EXTEND_IKASHOP_PRO:
			self.notificationOpenButton = self.CreateWidget(ui.Button, pos = (7, 352+12))
			self.notificationOpenButton.SetUpVisual("ikashop/pro/business/buttons/notification/default.png")
			self.notificationOpenButton.SetDownVisual("ikashop/pro/business/buttons/notification/default.png")
			self.notificationOpenButton.SetOverVisual("ikashop/pro/business/buttons/notification/hover.png")
			self.notificationOpenButton.SAFE_SetEvent(self.notificationBoard.Toggle)
			self.notificationOpenButton.SetToolTipText(locale.IKASHOP_PRO_BUSINESS_NOTIFICATION_OPEN_BUTTON_TEXT)
			self.notificationOpenButton.ToolTipText.SetOutline(1)

			self.notificationCounter = self.CreateWidget(IkarusShopCounter, pos = (25, 0), parent = self.notificationOpenButton)

	def _LoadLinkedBoards(self):
		self.safeboxBoard = IkarusShopSafeboxBoard()
		self.auctionBoard = IkarusShopAuctionOwnerBoard()
		self.offersBoard = IkarusShopOffersBoard()
		if app.EXTEND_IKASHOP_PRO:
			self.notificationBoard = IkarusShopNotificationBoard()

	# HANDLING DURATION RESTORE PROCESS
	def _OnClickDurationIncreaseButton(self):
		# checking cash
		if player.GetElk() < RESTORE_DURATION_COST:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INCREASE_DURATION_NO_MONEY)
			return

		# opening question
		question = locale.IKASHOP_BUSINESS_INCREASE_DURATION_QUESTION.format(locale.NumberToMoneyString(RESTORE_DURATION_COST))
		self.OpenQuestionDialog(question, self._OnIncreaseDurationQuestionAccept)

	def _OnIncreaseDurationQuestionAccept(self):
		ikashop.SendShopCreate()
		self.questionDialog.Hide()

	# HANDLING INSERT ITEM PROCESS
	def _OnClickEmptySlot(self, slot):
		if mouse.mouseController.isAttached():
			attachedType = mouse.mouseController.GetAttachedType()
			attachedItemIndex = mouse.mouseController.GetAttachedItemIndex()
			attachedItemSlotPos = mouse.mouseController.GetAttachedSlotNumber()
			mouse.mouseController.DeattachObject()

			# validating attached item
			if attachedType in (player.SLOT_TYPE_DRAGON_SOUL_INVENTORY, player.SLOT_TYPE_INVENTORY):
				win, pos = player.SlotTypeToInvenType(attachedType), attachedItemSlotPos
				if player.ITEM_MONEY != attachedItemIndex:
					self.InsertItemInSlot(win, pos, slot)

	def InsertItemInSlot(self, win, pos, slot = None):
		# checking shop isn't expired
		if self.shopInfo['duration'] <= 0:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_CANNOT_SELL_ITEM_EXPIRED_SHOP)
			return

		# checking item antiflags
		itemIndex = player.GetItemIndex(win, pos)
		itemCount = player.GetItemCount(win, pos)

		if itemIndex != 0:
			item.SelectItem(itemIndex)
			# checking item antifalg
			if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
				self.OpenPopupDialog(locale.IKASHOP_BUSINESS_CANNOT_SELL_ITEM)
				return

			# autodetecting price
			if app.EXTEND_IKASHOP_PRO:
				itemHash = GetInventoryItemHash(win, pos)
				detectedPrice = ikashop.GetItemPriceCache(itemIndex, itemHash, itemCount)
				isFastCall = slot == None # <- slot is None while calling it from inventory

			# autodetecting empty slot
			items = [(sitem['vnum'], sitem['cell']) for sitem in self.shopInfo['items'].values()]
			if slot == None:
				slot = ikashop.GetFirstEmptyCell(item.GetItemSize()[1], items)

				# checking for busy space
				if slot == None:
					self.OpenPopupDialog(locale.IKASHOP_BUSINESS_CANNOT_SELL_ITEM_NO_SPACE)

			# checking shop space
			else:
				if not ikashop.CheckShopSpace(items, itemIndex, slot):
					return

			# caching inserting item info
			self.insertingPriceInfo = slot, win, pos

			if app.EXTEND_IKASHOP_PRO:
				# checking price is already available
				if isFastCall and detectedPrice:
					price = detectedPrice['value'],
					if ENABLE_CHEQUE_SYSTEM:
						price += detectedPrice['cheque'],
					ikashop.SendAddItem(win, pos, slot, *price)
					return

				# opening money input dialog
				kargs = detectedPrice if detectedPrice else {}
				self.priceCacheInfo = itemIndex, itemHash, itemCount
				self.OpenMoneyInputDialog(self._OnAcceptInsertingItemPrice, **kargs)

			else:
				self.OpenMoneyInputDialog(self._OnAcceptInsertingItemPrice)

	def _OnAcceptInsertingItemPrice(self):
		self.moneyInputDialog.SoftClose()
		ok, price = ExtractInputPrice(self.moneyInputDialog)
		if not ok:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INVALID_ITEM_PRICE)
			return

		# sending add item
		dest, win, slot = self.insertingPriceInfo
		ikashop.SendAddItem(win, slot, dest, *price)
		if app.EXTEND_IKASHOP_PRO:
			# registering item price into price cache
			vnum, hash, count = self.priceCacheInfo
			ikashop.RegisterItemPriceCache(vnum, hash, count, *price)
		return True

	# HANDLING EDIT PRICE/ REMOVE ITEM
	def _OnClickItemSlot(self, slot):
		# checking item does exists
		if slot in self.shopInfo['items']:
			data = self.shopInfo['items'][slot]

			# checking for edit item request
			if IsPressingSHIFT():
				self.insertingPriceInfo = data
				if app.EXTEND_IKASHOP_PRO:
					self.insertingPriceAllSimilar = False
					detectPrice = ikashop.GetItemPriceCache(data['vnum'], data['hash'], data['count'])
					kargs = detectPrice if detectPrice else {}
					self.OpenMoneyInputDialog(self._OnAcceptEditingItemPrice, **kargs)
				else:
					self.OpenMoneyInputDialog(self._OnAcceptEditingItemPrice)
				return

			if app.EXTEND_IKASHOP_PRO:
				# checking for edit all similar items
				if IsPressingCTRL():
					self.insertingPriceInfo = data
					self.insertingPriceAllSimilar = True
					detectPrice = ikashop.GetItemPriceCache(data['vnum'], data['hash'], data['count'])
					kargs = detectPrice if detectPrice else {}
					self.OpenMoneyInputDialog(self._OnAcceptEditingItemPrice, **kargs)
					self.SetEditedMarkedSlotInfo(data['vnum'], data['count'], data['hash'], (0.7, 0.7, 0.7), infinite=1)
					return

	def _OnRightClickItemSlot(self, slot):
		# checking item does exists
		if slot in self.shopInfo['items']:
			data = self.shopInfo['items'][slot]

			# checking for remove all similar items
			if app.EXTEND_IKASHOP_PRO:
				if IsPressingCTRL():
					self.removingVnum = data['vnum']
					item.SelectItem(self.removingVnum)
					question = locale.IKASHOP_PRO_BUSINESS_REMOVE_ALL_SIMILAR_ITEMS_QUESTION.format(item.GetItemName())
					self.OpenQuestionDialog(question, self._OnAcceptRemoveAllSimilarItems)

					# marking all removing items
					for slot, data in self.shopInfo['items'].items():
						if data['vnum'] == self.removingVnum:
							self.AppendRemovingItemSlot(slot)
					self._RefreshItems()
					return

			# starting edit item price process
			ikashop.SendRemoveItem(data['id'])

	def _OnAcceptRemoveAllSimilarItems(self):
		self.questionDialog.Hide()
		for item in self.shopInfo['items'].values():
			if item['vnum'] == self.removingVnum:
				ikashop.SendRemoveItem(item['id'])

	def _OnAcceptEditingItemPrice(self):
		self.moneyInputDialog.SoftClose()
		ok, price = ExtractInputPrice(self.moneyInputDialog)
		if not ok:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INVALID_ITEM_PRICE)
			return

		# sending edit item
		data = self.insertingPriceInfo

		if app.EXTEND_IKASHOP_PRO:
			# registering price into price cache
			ikashop.RegisterItemPriceCache(data['vnum'], data['hash'], data['count'], *price)
			# editing all item prices
			if self.insertingPriceAllSimilar:
				for checkData in self.shopInfo['items'].values():
					if data['hash'] == checkData['hash'] and data['count'] == checkData['count'] and data['vnum'] == checkData['vnum']:
						if price[0] != checkData['price'] or (ENABLE_CHEQUE_SYSTEM and price[1] != checkData['cheque']):
							ikashop.SendEditItem(checkData['id'], *price)
				self.SetEditedMarkedSlotInfo(data['vnum'], data['count'], data['hash'], (0.5, 0.5, 0.1), price = price)
			else:
				ikashop.SendEditItem(data['id'], *price)

		else:
			ikashop.SendEditItem(data['id'], *price)

		return True

	# HANDLING TOOLTIP OVER IN OVER OUT
	def _ShowToolTipOnItemSlot(self, slot):
		if slot in self.shopInfo['items']:
			data = self.shopInfo['items'][slot]
			tooltip = self.GetToolTip()
			tooltip.ClearToolTip()
			tooltip.AddItemData(data['vnum'], data['sockets'], data['attrs'])
			if 'price' in data and data['price'] != 0:
				tooltip.AppendPrice(data['price'])
			if 'cheque' in data and data['cheque'] != 0:
				tooltip.AppendCheque(data['cheque'])

			# checking shop isn't expired
			tooltip.AppendTextLine(locale.IKASHOP_BUSINESS_EDIT_ITEM_TOOLTIP)
			if app.EXTEND_IKASHOP_PRO:
				tooltip.AppendTextLine(locale.IKASHOP_PRO_BUSINESS_EDIT_ALL_SIMILAR_ITEM_TOOLTIP)
			tooltip.AppendTextLine(locale.IKASHOP_BUSINESS_REMOVE_ITEM_TOOLTIP)
			if app.EXTEND_IKASHOP_PRO:
				tooltip.AppendTextLine(locale.IKASHOP_PRO_BUSINESS_REMOVE_ALL_SIMILAR_ITEM_TOOLTIP)
			tooltip.ShowToolTip()

	def _HideToolTipOnItemSlot(self, slot=0):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	# HANDLING CANCEL SHOP REQUEST
	def _OnClickCancelShopButton(self):
		self.OpenQuestionDialog(locale.IKASHOP_BUSINESS_CANCEL_SHOP_QUESTION, self._OnAcceptCancelShopQuestion)

	def _OnAcceptCancelShopQuestion(self):
		self.questionDialog.Hide()
		ikashop.SendForceCloseShop()

	if app.EXTEND_IKASHOP_PRO:
		# HANDLING MOVE SHOP REQUEST
		def _OnClickMoveShopButton(self):
			# checking money
			if player.GetElk() < MOVE_SHOP_ENTITY_COST:
				self.OpenPopupDialog(locale.IKASHOP_PRO_BUSINESS_MOVE_SHOP_NO_MONEY)
				return
			# sending question
			message = locale.IKASHOP_PRO_BUSINESS_MOVE_SHOP_QUESTION.format(locale.NumberToMoneyString(MOVE_SHOP_ENTITY_COST))
			self.OpenQuestionDialog(message, self._OnAcceptMoveShopQuestion)

		def _OnAcceptMoveShopQuestion(self):
			self.questionDialog.Hide()
			ikashop.SendMoveShopEntity()

	# HANDLING AUCTION CREATION
	def _OnAcceptCreateAuctionQuestion(self):
		self.questionDialog.Hide()

		if not hasattr(self, "createAuctionDialog"):
			self.createAuctionDialog = IkarusCreateAuctionDialog()
			self._RegisterDialog(self.createAuctionDialog)

		self.createAuctionDialog.Open()

	def _RefreshItems(self):
		# resetting slots
		for i in xrange(self.GRID_COLUMNS*self.GRID_ROWS):
			self.slotWindow.ClearSlot(i)
			if app.EXTEND_IKASHOP_PRO:
				self.slotWindow.DeactivateSlot(i)

		# setting up slots
		for item in self.shopInfo['items'].values():
			self.slotWindow.SetItemSlot(item['cell'], item['vnum'], item['count'] if item['count'] > 1 else 0)

		if app.EXTEND_IKASHOP_PRO:
			self._RefreshMarkedSlots()

		self.slotWindow.RefreshSlot()


	if app.EXTEND_IKASHOP_PRO:
		def _RefreshMarkedSlots(self):
			# marking edited items
			actualTime = app.GetTime()
			if self.editedMarkedInfo != None and self.editedMarkedTime != None:
				if self.editedMarkedTime > actualTime or self.editedMarkedTime == -1:
					vnum, count, hash, price = self.editedMarkedInfo
					for i in xrange(self.PAGE_SIZE):
						slot = i
						if slot in self.shopInfo['items']:
							data = self.shopInfo['items'][slot]
							if (data['vnum'], data['count'], data['hash']) == (vnum, count, hash):
								if ENABLE_CHEQUE_SYSTEM:
									itemPrice = (data['price'], data['cheque'])
								else:
									itemPrice = data['price'],
								if price is None or itemPrice == price:
									self.slotWindow.ActivateSlot(i, *self.editedMarkedColor)

			# marking removing items
			for slot in self.removingItemList:
				self.slotWindow.ActivateSlot(slot, 0.5, 0.1, 0.1)


	# PUBLIC INTERFACE
	def Open(self):
		ikashop.SendOpenShopOwner()
		if app.EXTEND_IKASHOP_PRO:
			player.RefreshInventory()

	def Close(self):
		self.Hide()
		ikashop.SendCloseMyShopBoard()
		if app.EXTEND_IKASHOP_PRO:
			player.RefreshInventory()

	if app.EXTEND_IKASHOP_PRO:
		def AppendRemovingItemSlot(self, slot):
			if not slot in self.removingItemList:
				self.removingItemList.append(slot)

		def SetEditedMarkedSlotInfo(self, vnum, count, hash, color, infinite = 0, price = None):
			self.editedMarkedInfo = vnum, count, hash, price
			self.editedMarkedTime = app.GetTime() + 20.0 if not infinite else -1
			self.editedMarkedColor = color
			self._RefreshItems()

		def OnUpdate(self):
			# checking for edited item list
			if self.editedMarkedTime != None and self.editedMarkedTime != -1 and self.editedMarkedTime < app.GetTime():
				self.editedMarkedTime = None
				self.editedMarkedInfo = None
				self._RefreshItems()

			# checking for closed money input dialog
			if self.editedMarkedInfo != None and self.editedMarkedTime == -1 and not self.moneyInputDialog.IsShow():
				self.editedMarkedTime = None
				self.editedMarkedInfo = None
				self._RefreshItems()

			# checking for removing item list
			if self.removingItemList:
				if not self.questionDialog.IsShow():
					self.removingItemList = []
					self._RefreshItems()

	def IsCreatingAuction(self):
		return hasattr(self, "createAuctionDialog") and self.createAuctionDialog.IsShow()

	# BINARY CALLS
	def OpenShopOwner(self, data):
		# refreshing duration
		if data['duration'] > 0:
			self.durationText.SetText(locale.SecondToDHM(data['duration']*60))
			self.durationExpiredIcon.Hide()
			self.durationIncreaseButton.Hide()
		else:
			self.durationText.SetText(locale.IKASHOP_BUSINESS_SHOP_EXPIRED_DURATION)
			self.durationExpiredIcon.Show()
			self.durationIncreaseButton.Show()

		# ordering items by cell and storing info
		data['items'] = { item['cell'] : item for item in data['items'] }
		self.shopInfo = data

		self._RefreshItems()

		if not self.IsShow():
			self.Show()
			self.SetTop()
		if app.EXTEND_IKASHOP_PRO:
			player.RefreshInventory()

	def OpenShopOwnerEmpty(self):
		# refreshing duration
		self.durationText.SetText(locale.IKASHOP_BUSINESS_SHOP_EXPIRED_DURATION)
		self.durationExpiredIcon.Show()
		self.durationIncreaseButton.Show()

		# resetting slots
		for i in xrange(self.GRID_COLUMNS*self.GRID_ROWS):
			self.slotWindow.ClearSlot(i)
		self.slotWindow.RefreshSlot()

		# making shop info data
		self.shopInfo = {'duration' : 0, 'items' : {}}
		if not self.IsShow():
			self.Show()
			self.SetTop()
		if app.EXTEND_IKASHOP_PRO:
			player.RefreshInventory()

	def ShopOwnerRemoveItem(self, itemid):
		if 'items' in self.shopInfo:
			self.shopInfo['items'] = {cell:item for cell,item in self.shopInfo['items'].items() if item['id'] != itemid}
			self._RefreshItems()

	def ShopOwnerEditItem(self, itemid, prices):
		if 'items' in self.shopInfo:
			for data in self.shopInfo['items'].values():
				if data['id'] == itemid:
					data['price'] = prices['price']
					if prices.has_key('cheque'):
						data['cheque'] = prices['cheque']
					self._RefreshItems()
					break

	def SetupSafebox(self, yang, items):
		self.safeboxBoard.Setup(yang, items)

	def SafeboxRemoveItem(self, itemid):
		self.safeboxBoard.RemoveItem(itemid)

	def SafeboxAddItem(self, item):
		self.safeboxBoard.AddItem(item)

	def SetupAcutionOwner(self, data):
		self.auctionBoard.Setup(data)

	def OpenCreateAuctionQuestion(self):
		question = locale.IKASHOP_BUSINESS_NO_AUCTION_CREATE_AUCTION_QUESTION
		self.OpenQuestionDialog(question, self._OnAcceptCreateAuctionQuestion)

	def AuctionInsertItemInSlot(self, win, pos):
		self.createAuctionDialog.InsertItemInSlot(win, pos)

	def SetOffers(self, offers):
		self.offersBoard.SetOffers(offers)

	def SetSafeboxCounter(self, count):
		self.safeboxItemCounter.SetCounter(count)

	def SetAuctionCounter(self, count):
		self.auctionOfferCounter.SetCounter(count)

	def SetOffersCounter(self, count):
		self.privateOfferCounter.SetCounter(count)

	if app.EXTEND_IKASHOP_PRO:
		def SetNotificationCounter(self, count):
			self.notificationCounter.SetCounter(count)

		def SetNotifications(self, notifications):
			self.notificationBoard.SetNotifications(notifications)

	def ServerPopupMessage(self, message):
		message = getattr(locale, message, message)
		self.OpenPopupDialog(message)

class IkarusShopGuestBoard(IkashopBoardWithTitleBar):

	GRID_COLUMNS = ikashop.SHOP_GRID_WIDTH
	GRID_ROWS = ikashop.SHOP_GRID_HEIGHT

	def __init__(self):
		super(IkarusShopGuestBoard, self).__init__()
		self.markedInfo = None
		self.vid = 0
		self._SettingUpBoard()
		self._LoadIkarusShopGuestBoard()

	def _SettingUpBoard(self):
		self.SetSize(508, 404)
		self.SetCloseEvent(self.Close)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetCenterPosition()
		x,y = self.GetLocalPosition()
		self.SetPosition(x+100,y)

	def _LoadIkarusShopGuestBoard(self):
		# making slot box
		self.slotBox = self.CreateWidget(ui.ImageBox, pos = (5,35 + 27))
		self.slotBox.LoadImage("ikashop/lite/business/slot_box.png")
		self.slotWindow = self.CreateWidget(ui.GridSlotWindow, parent = self.slotBox, pos = (6,6))
		self.slotWindow.ArrangeSlot(0, self.GRID_COLUMNS, self.GRID_ROWS, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slotWindow.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slotWindow.SetSelectItemSlotEvent(self._OnClickItemSlot)
		self.slotWindow.SetOverInItemEvent(self._ShowToolTipOnItemSlot)
		self.slotWindow.SetOverOutItemEvent(self._HideToolTipOnItemSlot)

		# making duration box
		self.durationBox = self.CreateWidget(ui.ImageBox, pos = (5,35))
		self.durationBox.LoadImage("ikashop/lite/business/duration_box.png")

		self.durationText = self.CreateWidget(ui.TextLine, parent = self.durationBox, pos = (30, 4))
		self.durationText.SetPackedFontColor(0xFFFFFFFF)
		self.durationText.SetText("11d 22h 18m")

	def _OnClickItemSlot(self, slot):
		if slot in self.shopInfo['items']:
			data = self.shopInfo['items'][slot]

			# making item name
			item.SelectItem(data['vnum'])
			itemName = item.GetItemName()
			if data['count'] > 1:
				itemName += "({})".format(data['count'])

			# making item price
			if ENABLE_CHEQUE_SYSTEM:
				itemPrice = ""
				if data['price'] != 0:
					itemPrice += locale.NumberToMoneyString(data['price'])
				if data['cheque'] != 0:
					if itemPrice:
						itemPrice += ', '
					itemPrice += locale.NumberToCheque(data['cheque'])
			else:
				itemPrice = locale.NumberToMoneyString(data['price'])


			if app.EXTEND_IKASHOP_PRO:
				if IsPressingCTRL():
					item.SelectItem(data['vnum'])

					# making message
					message = locale.IKASHOP_PRO_SHOP_GUEST_BUY_ALL_ITEMS_QUESTION.format(itemName, itemPrice)
					self.buyAllInfo = data['vnum'], data['count'], data['price']
					self.OpenQuestionDialog(message, self._OnAcceptBuyAllQuestion)
					return

			if IsPressingSHIFT():
				# checking offer min price
				if data['price'] + data.get('cheque', 0) * YANG_PER_CHEQUE < 10000:
					self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_MAKE_OFFER_ITEM_PRICE_TOO_LOW)
					return

				self.offerInfo = data['id'], data['price'], data.get('cheque', 0)
				self.OpenMoneyInputDialog(self._OnAcceptMakeOfferInput)
				return

			self.buyItemInfo = self.shopInfo['id'], data['id'], data['price'] + data.get('cheque', 0) * YANG_PER_CHEQUE
			message = locale.IKASHOP_SHOP_GUEST_BUY_ITEM_QUESTION.format(itemName, itemPrice)
			self.OpenQuestionDialog(message, self._OnAcceptBuyItemQuestion)

	if app.EXTEND_IKASHOP_PRO:
		def _OnAcceptBuyAllQuestion(self):
			self.questionDialog.Hide()
			for data in self.shopInfo['items'].values():
				if (data['vnum'], data['count'], data['price']) == self.buyAllInfo:
					ikashop.SendBuyItem(self.shopInfo['id'], data['id'], data['price'] + data.get('cheque', 0) * YANG_PER_CHEQUE)

	def _OnAcceptBuyItemQuestion(self):
		ikashop.SendBuyItem(*self.buyItemInfo)
		self.questionDialog.Hide()

	def _OnAcceptMakeOfferInput(self):
		self.moneyInputDialog.SoftClose()

		# validating value
		ok, value = ExtractInputPrice(self.moneyInputDialog)
		if not ok:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INVALID_ITEM_PRICE)
			return

		# checking for max offer price
		id, price, cheque = self.offerInfo

		if ENABLE_CHEQUE_SYSTEM:
			valueTotal = value[0] + value[1] * YANG_PER_CHEQUE
			priceTotal = price + cheque * YANG_PER_CHEQUE
			if valueTotal >= priceTotal:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_LOWER_THAN_PRICE)
				return True

			# checking for min offer price
			minoffer = priceTotal * MIN_OFFER_PCT / 100
			if valueTotal < minoffer:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_HIGHER_THAN_PCT_OF_PRICE.format(MIN_OFFER_PCT))
				return True

			# checking owned cash
			if value[0] > player.GetElk() or value[1] > player.GetCheque():
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_NOT_ENOUGH_MONEY)
				return True

		else:
			if value[0] >= price:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_LOWER_THAN_PRICE)
				return True

			# checking for min offer price
			minoffer = price * MIN_OFFER_PCT / 100
			if value[0] < minoffer:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_HIGHER_THAN_PCT_OF_PRICE.format(MIN_OFFER_PCT))
				return True

			# checking owned cash
			if value[0] > player.GetElk():
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_NOT_ENOUGH_MONEY)
				return True

		ikashop.SendOfferCreate(self.shopInfo['id'], id, *value)
		return True

	def _ShowToolTipOnItemSlot(self, slot):
		if slot in self.shopInfo['items']:
			data = self.shopInfo['items'][slot]
			tooltip = self.GetToolTip()
			tooltip.ClearToolTip()
			tooltip.AddItemData(data['vnum'], data['sockets'], data['attrs'])
			if 'price' in data and data['price'] != 0:
				tooltip.AppendPrice(data['price'])
			if 'cheque' in data and data['cheque'] != 0:
				tooltip.AppendCheque(data['cheque'])
			tooltip.AppendTextLine(locale.IKASHOP_SHOP_GUEST_BUY_ITEM_TOOLTIP)
			if app.EXTEND_IKASHOP_PRO:
				tooltip.AppendTextLine(locale.IKASHOP_PRO_SHOP_GUEST_BUY_ALL_ITEM_TOOLTIP)
			tooltip.AppendTextLine(locale.IKASHOP_SHOP_GUEST_OFFER_ITEM_TOOLTIP)
			tooltip.ShowToolTip()

	def _HideToolTipOnItemSlot(self, slot=0):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	def _RefreshItems(self):
		# resetting slots
		for i in xrange(self.GRID_COLUMNS*self.GRID_ROWS):
			self.slotWindow.ClearSlot(i)
			self.slotWindow.DeactivateSlot(i)

		# setting up slots
		for item in self.shopInfo['items'].values():
			self.slotWindow.SetItemSlot(item['cell'], item['vnum'], item['count'] if item['count'] > 1 else 0)

		self.slotWindow.RefreshSlot()
		self._RefreshMarkedSlots()

	def _RefreshMarkedSlots(self):
		if not self.markedInfo:
			return

		vnum, count, price = self.markedInfo
		for cell, data in self.shopInfo['items'].items():
			if (data['vnum'], data['count'], data['price']) == (vnum, count, price):
				self.slotWindow.ActivateSlot(cell, 0.4, 0.4, 0.1)
		self.slotWindow.RefreshSlot()

	def Open(self, data):
		# refreshing duration & title
		self.durationText.SetText(locale.SecondToDHM(data['duration']*60))
		self.SetTitleName(locale.IKASHOP_SHOP_NAME_FORMAT.format(data['name']))

		# ordering items by cell and storing info
		data['items'] = { item['cell'] : item for item in data['items'] }
		self.shopInfo = data

		print data['isOwnerOnline']

		self._RefreshItems()

		if not self.IsShow():
			self.Show()
		self.SetTop()

		self.vid = data['vid']
		eventManager.EventManager().send_event(eventManager.EVENT_MARK_SHOP_CURRENT, self.vid, True)

	def Close(self):
		self.Hide()
		ikashop.SendCloseShopGuestBoard()
		eventManager.EventManager().send_event(eventManager.EVENT_MARK_SHOP_VIEWED, self.vid, True)

	def MarkItems(self, vnum, count, price):
		self.markedInfo = vnum, count, price
		self._RefreshMarkedSlots()

	def CheckExpiring(self, id):
		if self.shopInfo['id'] == id:
			self.Close()
			self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_EXPIRED)

	def ShopGuestRemoveItem(self, itemid):
		if 'items' in self.shopInfo:
			self.shopInfo['items'] = { cell : data for cell, data in self.shopInfo['items'].items() if data['id'] != itemid}
			self._RefreshItems()

	def EditItem(self, itemid, prices):
		if 'items' in self.shopInfo:
			for data in self.shopInfo['items'].values():
				if data['id'] == itemid:
					data['price'] = prices['price']
					if 'cheque' in prices:
						data['cheque'] = prices['cheque']
					self._RefreshItems()
					break


class IkarusAuctionGuestBoard(IkashopBoardWithTitleBar):

	OFFER_VIEW_COUNT = 6
	OFFER_VIEW_HEIGHT = 28

	def __init__(self):
		super(IkarusAuctionGuestBoard, self).__init__()
		self._SettingUpBoard()
		self._LoadIkarusShopAuctionGuestBoard()

	def _SettingUpBoard(self):
		sw, sh = GetScreenSize()
		self.SetSize(513 + 13, 249)
		self.SetCloseEvent(self.Close)
		self.SetPosition(sw/2 + self.GetWidth() - 600, sh / 2 - self.GetHeight()/2 + 100)
		self.AddFlag("movable")
		self.AddFlag("float")

	def _LoadIkarusShopAuctionGuestBoard(self):
		# making info box
		self.infoBox = self.CreateWidget(ui.ImageBox, pos = (12, 36))
		self.infoBox.LoadImage("ikashop/lite/auction/info_box.png")
		self.infoBox.SetMouseWheelEvent(self._MouseWheelScrollOffers)

		self.minRaiseText = self.CreateWidget(ui.TextLine, pos = (458+13, 221-36), parent = self.infoBox)
		self.minRaiseText.SetPackedFontColor(0xFFFFFFFF)
		self.minRaiseText.SetHorizontalAlignRight()

		self.durationText = self.CreateWidget(ui.TextLine, pos = (141, 221-36), parent = self.infoBox)
		self.durationText.SetPackedFontColor(0xFFFFFFFF)

		# making slot
		self.slot = self.CreateWidget(ui.GridSlotWindow, pos = (36, 44), size = (32, 98), parent = self.infoBox)
		self.slot.ArrangeSlot(0, 1, 3, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetOverInItemEvent(self._OverInItem)
		self.slot.SetOverOutItemEvent(self._OverOutItem)

		# making scrollbar
		self.offerScrollbar = self.CreateWidget(ui.ScrollBar, pos = (470+13, 4), parent = self.infoBox)
		self.offerScrollbar.SetScrollBarSize(self.infoBox.GetHeight() - 35)
		self.offerScrollbar.SetScrollEvent(self._ScrollOffers)

		# making cancel auction button
		self.raiseButton = self.CreateWidget(ui.Button, pos = (12, self.GetHeight() - 33))
		self.raiseButton.SetUpVisual("ikashop/lite/auction/raise_button/default.png")
		self.raiseButton.SetDownVisual("ikashop/lite/auction/raise_button/default.png")
		self.raiseButton.SetOverVisual("ikashop/lite/auction/raise_button/hover.png")
		self.raiseButton.SetText(locale.IKASHOP_ACUTION_GUEST_RAISE_AUCTION_BUTTON)
		self.raiseButton.SAFE_SetEvent(self._OnClickRaiseAuction)
		self.raiseButton.Show()

		# making offers
		self.offerViews = []
		for i in xrange(self.OFFER_VIEW_COUNT):
			self.offerViews.append(self.CreateWidget(
				IkarusShopAuctionOfferView, pos = (115, 6 + i*self.OFFER_VIEW_HEIGHT), parent = self.infoBox))

	def _RefreshOffers(self):
		# calculating count difference
		diff = len(self.offers) - self.OFFER_VIEW_COUNT
		diff = max(diff, 0)

		# calculating ranges
		offset = self.offerScrollbar.GetPos()
		sindex = int(diff * offset)
		eindex = sindex + min(self.OFFER_VIEW_COUNT, len(self.offers))

		# iterating over views
		for i, view in enumerate(self.offerViews):
			ri = i + sindex
			view.Hide() if ri >= eindex \
				else view.Setup(ri+1, self.offers[ri])

		# update scrollbar's middlebar height
		self.offerScrollbar.UpdateScrollbarLenght(self.OFFER_VIEW_HEIGHT * len(self.offers))

	def _MouseWheelScrollOffers(self, delta):
		if self.offerScrollbar.IsShow():
			self.offerScrollbar.OnDown() if delta < 0 \
				else self.offerScrollbar.OnUp()
		return True

	def _ScrollOffers(self):
		if self.offerScrollbar.IsShow():
			self._RefreshOffers()

	def _UpdateScrollbarState(self):
		self.offerScrollbar.SetPos(0)
		if len(self.offers) <= self.OFFER_VIEW_COUNT:
			self.offerScrollbar.Hide()
		else:
			self.offerScrollbar.Show()

	def _OverInItem(self, slot):
		data = self.auctionInfo
		tooltip = self.GetToolTip()
		tooltip.ClearToolTip()
		tooltip.AddItemData(data['vnum'], data['sockets'], data['attrs'])
		tooltip.ShowToolTip()

	def _OverOutItem(self, slot = 0):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	def _OnClickRaiseAuction(self):
		self.OpenMoneyInputDialog(self._OnAcceptRaiseAuctionInput, value = self.minRaise)
	def _OnAcceptRaiseAuctionInput(self):
		self.moneyInputDialog.SoftClose()

		ok, value = ExtractInputPrice(self.moneyInputDialog)
		if not ok:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INVALID_ITEM_PRICE)
			return

		if ENABLE_CHEQUE_SYSTEM:
			valueTotal = value[0] + value[1] * YANG_PER_CHEQUE
			if self.minRaise > valueTotal:
				self.OpenPopupDialog(locale.IKASHOP_AUCTION_GUEST_MIN_RAISE_REQUIRED)
				return True

			if value[0] > player.GetElk() or value[1] > player.GetCheque():
				self.OpenPopupDialog(locale.IKASHOP_AUCTION_GUEST_NOT_ENOUGH_MONEY)
				return True

		else:
			if self.minRaise > value[0]:
				self.OpenPopupDialog(locale.IKASHOP_AUCTION_GUEST_MIN_RAISE_REQUIRED)
				return True

			if value[0] > player.GetElk():
				self.OpenPopupDialog(locale.IKASHOP_AUCTION_GUEST_NOT_ENOUGH_MONEY)
				return True

		ikashop.SendAuctionAddOffer(self.auctionInfo['owner'], *value)
		return True

	def SetOffers(self, offers):
		self.offers = sorted(offers, key = lambda val : val['datetime'], reverse=True)
		self._UpdateScrollbarState()
		self._RefreshOffers()
		self.RefreshMinRaise()

	def SetDuration(self, duration):
		self.durationText.SetText(locale.SecondToDHM(duration*60))

	def _GetMinRaise(self):
		if not self.offers:
			return self.auctionInfo['price']

		minraise = max([val['price'] for val in self.offers])
		if minraise < 1000:
			return minraise + 1000

		return minraise * (100+AUCTION_MIN_RAISE_PERCENTAGE) / 100

	def RefreshMinRaise(self):
		self.minRaise = self._GetMinRaise()
		self.minRaiseText.SetText(locale.IKASHOP_AUCTION_MIN_BID + '  ' + locale.NumberToString(self.minRaise))

	def Open(self, data):
		# storing data
		self.auctionInfo = data

		# refreshing duration & title
		seconds = data['duration'] * 60
		self.durationText.SetText(locale.SecondToDHM(seconds))
		self.SetTitleName(locale.IKASHOP_AUCTION_GUEST_NAME_FORMAT.format(data['ownername']))

		# refreshing item
		vnum = data['vnum']
		count = data['count'] if data['count'] > 1 else 0
		item.SelectItem(vnum)
		size = item.GetItemSize()[1]
		self.slot.ArrangeSlot(0, 1, size, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetItemSlot(0, vnum, count)

		# refreshing offers
		self.SetOffers(data['offers'])

		if not self.IsShow():
			self.Show()
			self.SetTop()

	def Close(self):
		self.Hide()
		ikashop.SendAuctionExitFrom(self.auctionInfo['owner'])


class IkarusAuctionListBoard(IkarusShopListBoard):

	AUCTION_VIEW_COUNT = 4

	def __init__(self):
		super(IkarusAuctionListBoard, self).__init__()
		self._SettingUpBoard()
		self._LoadIkarusAuctionListBoard()

	def _SettingUpBoard(self):
		self.SetSize(395, 510)
		self.SetTitleName(locale.IKASHOP_AUCTION_LIST_BOARD_TITLE)
		super(IkarusAuctionListBoard, self)._SettingUpBoard()

	def _LoadIkarusAuctionListBoard(self):
		self._LoadIkarusShopListBoard()
		self._MakeListElements(IkarusSearchShopItem, self.AUCTION_VIEW_COUNT)

	def SetAuctions(self, auctions):
		shuffle(auctions)
		self.auctions = auctions
		self.SetElements(self.auctions)
		self.Show()
		self.SetTop()

	def SetSearchShopBoard(self, board):
		pass
		# for view in self.views:
		# 	view.SetSearchShopBoard(board)

	def Open(self):
		ikashop.SendAuctionListRequest()

	def Close(self):
		self.Hide()

class IkarusShopHistoryFilterView(IkarusShopWindow):

	def __init__(self):
		super(IkarusShopHistoryFilterView, self).__init__()
		self._LoadIkarusShopHistoryFilterView()

	def _LoadIkarusShopHistoryFilterView(self):
		# making background and fitting its size
		self.background = self.CreateWidget(ui.ImageBox)
		self.background.LoadImage("ikashop/lite/history_search/box.png")
		self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		# making what
		self.whatText = self.CreateWidget(ui.TextLine, pos = (9, 5))
		self.whatText.SetPackedFontColor(0xFFFFFFFF)

		# making datetime
		self.datetimeText = self.CreateWidget(ui.TextLine, pos = (405-11, 5))
		self.datetimeText.SetPackedFontColor(0xFFFFFFFF)
		self.datetimeText.SetHorizontalAlignCenter()

		# info button
		self.infoButton = self.CreateWidget(ui.Button, pos = (294, 1))
		self.infoButton.SetUpVisual("ikashop/lite/history_search/info_button/default.png")
		self.infoButton.SetDownVisual("ikashop/lite/history_search/info_button/default.png")
		self.infoButton.SetOverVisual("ikashop/lite/history_search/info_button/hover.png")

		# search button
		self.searchButton = self.CreateWidget(ui.Button, pos = (294 + 27, 1))
		self.searchButton.SetUpVisual("ikashop/lite/search_shop/mini_search_button/default.png")
		self.searchButton.SetDownVisual("ikashop/lite/search_shop/mini_search_button/default.png")
		self.searchButton.SetOverVisual("ikashop/lite/search_shop/mini_search_button/hover.png")
		self.searchButton.SetToolTipText(locale.IKASHOP_SEARCH_SHOP_SEARCH_BUTTON_TEXT)

	def _ShowToolTip(self):
		tooltip = self.GetToolTip()
		tooltip.ClearToolTip()
		# adding item name
		tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_HISTORY_WHAT_FORMAT.format(self.data['name'], self.data['count']))
		# adding type/subtype
		if self.data['type'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_HEADER + ': ' + IkarusSearchShopBoard.ITEM_TYPES[self.data['type']])
			if self.data['subtype'] != 0:
				subtypes = IkarusSearchShopBoard.SUB_TYPES[self.data['type']]
				tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_HEADER + ': ' + subtypes[self.data['subtype']])
		# adding price min/max
		if self.data['price_min'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ITEM_PRICE_MIN_HEADER + ': ' + locale.NumberToString(self.data['price_min']))
		if self.data['price_max'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ITEM_PRICE_MAX_HEADER + ': ' + locale.NumberToString(self.data['price_max']))
		# adding level min/max
		if self.data['level_min'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ITEM_LEVEL_MIN_HEADER + ': ' + locale.NumberToString(self.data['level_min']))
		if self.data['level_max'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ITEM_LEVEL_MAX_HEADER + ': ' + locale.NumberToString(self.data['level_max']))
		# adding attributes
		tooltip.AppendAttributes(self.data['attrs'])
		# adding special filters
		if self.data['sash'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_SASH_ABSORB_HEADER + ': ' + IkarusSearchShopBoard.SASH_ABSORBS[self.data['sash']])
		if self.data['alchemy'] != 0:
			tooltip.AutoAppendTextLine(locale.IKASHOP_SEARCH_SHOP_ALCHEMY_GRADE_HEADER + ': ' + IkarusSearchShopBoard.ALCHEMY_GRADES[self.data['alchemy']])
		tooltip.ResizeToolTip()
		tooltip.ShowToolTip()

	def _RefreshToolTip(self):
		tooltip = self.GetToolTip()
		if tooltip.IsShow():
			if not self.infoButton.IsIn():
				tooltip.HideToolTip()
		else:
			if self.infoButton.IsIn():
				self._ShowToolTip()

	def Setup(self, data):
		self.data = data
		self.datetimeText.SetText(DatetimeFormat(data['datetime']))
		self.whatText.SetText(locale.IKASHOP_SEARCH_SHOP_HISTORY_WHAT_FORMAT.format(data['name'], data['count']))

	def SetSearchEvent(self, event):
		self.searchButton.SAFE_SetEvent(event, proxy(self))

	def OnUpdate(self):
		self._RefreshToolTip()

class IkarusHistoryFilterBoard(IkarusShopListBoard):

	HISTORY_FILTER_VIEW_COUNT = 10

	def __init__(self):
		super(IkarusHistoryFilterBoard, self).__init__()
		self._SettingUpBoard()
		self._LoadIkarusHistoryFilterBoard()

	def _SettingUpBoard(self):
		self.SetSize(494, 339)
		self.SetTitleName(locale.IKASHOP_HISTORY_FILTER_LIST_BOARD_TITLE)
		super(IkarusHistoryFilterBoard, self)._SettingUpBoard()

	def _LoadIkarusHistoryFilterBoard(self):
		self._LoadIkarusShopListBoard()
		self._MakeListElements(IkarusShopHistoryFilterView, self.HISTORY_FILTER_VIEW_COUNT)
		for view in self.views:
			view.SetSearchEvent(self._OnClickSearchOnHistoryElement)

	def _OnClickSearchOnHistoryElement(self, view):
		self.searchShopBoard.HistoryRedoSearch(view.data)
		self.Close()

	def SetSearchShopBoard(self, board):
		pass
		# self.searchShopBoard = proxy(board)

	def SetFilters(self, filters):
		self.filters = sorted(filters, key = lambda elm : elm['datetime'], reverse=True)
		self.SetElements(self.filters)

	def Open(self):
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()

class IkarusShopComboBox(IkarusShopWindow):

	DEFAULT_VIEW_COUNT = 5
	ELEMENT_HEIGHT = 14

	class ComboBoxView(ui.Button):
		def Destroy(self):
			SelfDestroyObject(self)

	def __init__(self):
		super(IkarusShopComboBox, self).__init__()
		self.viewCount = self.DEFAULT_VIEW_COUNT
		self.elementWidth = 0
		self.selectItemEvent = None
		self.views = []
		self.items = []
		self.elementImages = (
			"ikashop/lite/search_shop/combo_box_element/default.png",
			"ikashop/lite/search_shop/combo_box_element/default.png",
			"ikashop/lite/search_shop/combo_box_element/hover.png")
		self.selectedItem = 0
		self._LoadIkarusShopComboBox()

	def _LoadIkarusShopComboBox(self):
		self.SetMouseWheelEvent(self._MouseWheelScrollView)

		self.background = self.CreateWidget(ui.Bar3D)
		self.background.SetColor(0xFF999999, 0xFF000000, 0xFF777777)

		self.scrollbar = self.CreateWidget(ui.ScrollBar, show = False, parent = self.background)
		self.scrollbar.SetScrollEvent(self._ScrollView)

	def _MakeViews(self):
		for view in self.views:
			SelfDestroyObject(view)

		self.views = []
		images = self.elementImages
		for i in xrange(self.viewCount):
			view = self.CreateWidget(self.ComboBoxView, pos = (0, i*self.ELEMENT_HEIGHT), parent = self.background)
			view.SetUpVisual(images[0])
			view.SetDownVisual(images[1])
			view.SetOverVisual(images[2])
			self.elementWidth = max(self.elementWidth, view.GetWidth())
			self.views.append(view)

	def _MouseWheelScrollView(self, delta):
		if self.scrollbar.IsShow():
			self.scrollbar.OnDown() if delta < 0\
				else self.scrollbar.OnUp()
		return True

	def _ScrollView(self, delta=0):
		if self.scrollbar.IsShow():
			self._RefreshView()

	def _RefreshView(self):
		# making view if required
		if not self.views:
			self._MakeViews()

		# calculating sindex
		pos = self.scrollbar.GetPos() if self.scrollbar.IsShow() else 0.0
		diff = max(len(self.items) - self.viewCount, 0)
		sindex = int(diff * pos)
		eindex = sindex + min(len(self.items), self.viewCount)

		# hiding all views
		for view in self.views:
			view.Hide()

		# setting up and showing only used views
		for i in xrange(sindex, eindex):
			ri = i - sindex
			view = self.views[ri]
			view.SetText(self.items[i])
			view.ButtonText.SetPosition(view.GetWidth()/2, view.GetHeight() /2 -1)
			view.SAFE_SetEvent(self.SelectItem, i)
			view.Show()

			color = 0xFFFFFFFF if i != self.selectedItem else 0xFFFFFF88
			view.ButtonText.SetPackedFontColor(color)

		# updating scrollbar's middlebar length
		self.scrollbar.UpdateScrollbarLenght(len(self.items) * self.ELEMENT_HEIGHT)

	def _UpdateSize(self):
		viewHeight = self.ELEMENT_HEIGHT * min(len(self.items), self.viewCount)
		self.SetSize(self.GetWidth(), viewHeight)
		self.scrollbar.SetScrollBarSize(viewHeight)
		self.background.SetSize(self.GetWidth(), self.GetHeight())

	def _UpdateScrollbar(self):
		if len(self.items) > self.viewCount:
			self.scrollbar.Show()
			self.scrollbar.SetPos(0)
			self.scrollbar.SetPosition(self.elementWidth+1, 0)
			self.SetSize(self.elementWidth + 1 + self.scrollbar.GetWidth(), self.GetHeight())
			self.background.SetSize(self.GetWidth(), self.GetHeight())
		else:
			self.scrollbar.Hide()
			self.SetSize(self.elementWidth, self.GetHeight())
			self.background.SetSize(self.GetWidth(), self.GetHeight())
			# updating scrollbar's middlebar length
			self.scrollbar.UpdateScrollbarLenght(len(self.items) * self.ELEMENT_HEIGHT)

	def Open(self):
		self.Show()

	def Close(self):
		self.Hide()

	def GetSelectedItem(self):
		return self.selectedItem

	def SelectItem(self, index):
		self.selectedItem = index
		self._RefreshView()
		self.Close()
		if self.selectItemEvent:
			self.selectItemEvent(index, self.items[index])

	def SetSelectItemEvent(self, event):
		self.selectItemEvent = event

	def SetItems(self, items):
		self.items = items
		if not self.views:
			self._MakeViews()
		self._UpdateSize()
		self._UpdateScrollbar()
		self._RefreshView()

	def SetViewCount(self, count):
		self.viewCount = count
		self._UpdateSize()
		self._UpdateScrollbar()
		self._MakeViews()
		self._RefreshView()

	def ChangeElementImages(self, images):
		self.elementImages = images
		self._MakeViews()
		self._UpdateSize()
		self._UpdateScrollbar()
		self._RefreshView()

	# used to check via proxy ref
	def IsMe(self, combobox):
		return self is combobox


class IkarusSearchShopItem(IkarusShopWindow):

	def __init__(self):
		super(IkarusSearchShopItem, self).__init__()
		self.data = {'id':-1}
		self._LoadIkarusSearchShopItem()

	def _LoadIkarusSearchShopItem(self):
		# making background
		self.background = self.CreateWidget(ui.ExpandedImageBox)
		self.background.LoadImage("ikashop/lite/search_shop/result_item_box.png")
		self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		# making textlines
		self.itemName = self.CreateWidget(ui.TextLine, pos = (60, 17 - 6))
		self.sellerName = self.CreateWidget(ui.TextLine, pos = (78, 41 - 6))
		self.duration = self.CreateWidget(ui.TextLine, pos = (226, 41 - 6))
		self.price = self.CreateWidget(ui.TextLine, pos = (78, 58))

		if ENABLE_CHEQUE_SYSTEM:
			self.cheque = self.CreateWidget(ui.TextLine, pos = (128 + 70, 58))
			self.chequeIcon = self.CreateWidget(ui.ImageBox, pos = (110 + 70, 59))
			self.chequeIcon.LoadImage("d:/ymir work/ui/game/windows/cheque_icon.sub")

		# making buttons
		self.buyButton = self.CreateWidget(ui.Button, pos = (261, 84))
		self.buyButton.SetUpVisual("ikashop/lite/search_shop/buy_button/default.png")
		self.buyButton.SetDownVisual("ikashop/lite/search_shop/buy_button/default.png")
		self.buyButton.SetOverVisual("ikashop/lite/search_shop/buy_button/hover.png")
		self.buyButton.SAFE_SetEvent(self._OnClickBuyButton)
		self.buyButton.SetText(locale.IKASHOP_SEARCH_SHOP_BUY_BUTTON_TEXT)

		self.offerButton = self.CreateWidget(ui.Button, pos = (189, 84))
		self.offerButton.SetUpVisual("ikashop/lite/search_shop/offer_button/default.png")
		self.offerButton.SetDownVisual("ikashop/lite/search_shop/offer_button/default.png")
		self.offerButton.SetOverVisual("ikashop/lite/search_shop/offer_button/hover.png")
		self.offerButton.SAFE_SetEvent(self._OnClickOfferButton)
		self.offerButton.SetText(locale.IKASHOP_SEARCH_SHOP_OFFER_BUTTON_TEXT)

		self.openSellingBoard = self.CreateWidget(ui.Button, pos = (50, 84), show = False)
		self.openSellingBoard.SetUpVisual("ikashop/lite/search_shop/offer_button/default.png")
		self.openSellingBoard.SetDownVisual("ikashop/lite/search_shop/offer_button/default.png")
		self.openSellingBoard.SetOverVisual("ikashop/lite/search_shop/offer_button/hover.png")
		self.openSellingBoard.SAFE_SetEvent(self._OnClickOpenSellingBoardButton)

		if app.EXTEND_IKASHOP_PRO:
			self.messageSellerButton = self.CreateWidget(ui.Button)
			self.messageSellerButton.SetUpVisual("ikashop/ultimate/seller_message/default.png")
			self.messageSellerButton.SetOverVisual("ikashop/ultimate/seller_message/hover.png")
			self.messageSellerButton.SetDownVisual("ikashop/ultimate/seller_message/default.png")
			self.messageSellerButton.SAFE_SetEvent(self._OnClickMessageSeller)

		# making slot item
		self.slot = self.CreateWidget(ui.GridSlotWindow, pos = (9, 7))
		self.slot.ArrangeSlot(0, 1, 3, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetOverInItemEvent(self._OverInItem)
		self.slot.SetOverOutItemEvent(self._OverOutItem)

	def _OnClickBuyButton(self):
		item.SelectItem(self.data['vnum'])
		# making item name
		itemName = item.GetItemName()
		if self.data['count'] > 1:
			itemName += "({})".format(self.data['count'])

		# making item price
		if ENABLE_CHEQUE_SYSTEM:
			itemPrice = ""
			if self.data['price'] != 0:
				itemPrice += locale.NumberToMoneyString(self.data['price'])
			if self.data['cheque'] != 0:
				if itemPrice:
					itemPrice += ', '
				itemPrice += locale.NumberToCheque(self.data['cheque'])
		else:
			itemPrice = locale.NumberToMoneyString(self.data['price'])

		self.buyItemInfo = self.data['owner'], self.data['id'], self.data['price'] + self.data.get('cheque', 0) * YANG_PER_CHEQUE
		message = locale.IKASHOP_SHOP_GUEST_BUY_ITEM_QUESTION.format(itemName, itemPrice)
		self.OpenQuestionDialog(message, self._OnAcceptBuyItemQuestion)

	def _OnClickOfferButton(self):
		# checking offer min price
		if self.data['price'] + self.data.get('cheque', 0) * YANG_PER_CHEQUE < 10000:
			self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_MAKE_OFFER_ITEM_PRICE_TOO_LOW)
			return

		self.offerInfo = self.data['id'], self.data['price'], self.data.get('cheque', 0)
		self.OpenMoneyInputDialog(self._OnAcceptMakeOfferInput)
		return

	def _OnAcceptBuyItemQuestion(self):
		ikashop.SendBuyItem(*self.buyItemInfo)
		self.questionDialog.Hide()

	def _OnAcceptMakeOfferInput(self):
		self.moneyInputDialog.SoftClose()

		# validating value
		ok, value = ExtractInputPrice(self.moneyInputDialog)
		if not ok:
			self.OpenPopupDialog(locale.IKASHOP_BUSINESS_INVALID_ITEM_PRICE)
			return

		# checking for max offer price
		id, price, cheque = self.offerInfo

		if ENABLE_CHEQUE_SYSTEM:
			valueTotal = value[0] + value[1] * YANG_PER_CHEQUE
			priceTotal = price + cheque * YANG_PER_CHEQUE
			if valueTotal >= priceTotal:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_LOWER_THAN_PRICE)
				return True

			# checking for min offer price
			minoffer = priceTotal * MIN_OFFER_PCT / 100
			if valueTotal < minoffer:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_HIGHER_THAN_PCT_OF_PRICE.format(MIN_OFFER_PCT))
				return True

			# checking owned cash
			if value[0] > player.GetElk() or value[1] > player.GetCheque():
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_NOT_ENOUGH_MONEY)
				return True

		else:
			if value[0] >= price:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_LOWER_THAN_PRICE)
				return True

			# checking for min offer price
			minoffer = price * MIN_OFFER_PCT / 100
			if value[0] < minoffer:
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_MUST_BE_HIGHER_THAN_PCT_OF_PRICE.format(MIN_OFFER_PCT))
				return True

			# checking owned cash
			if value[0] > player.GetElk():
				self.OpenPopupDialog(locale.IKASHOP_SHOP_GUEST_OFFER_NOT_ENOUGH_MONEY)
				return True

		ikashop.SendOfferCreate(self.data['owner'], id, *value)
		return True

	def _OnClickOpenSellingBoardButton(self):
		if self.data['is_auction']:
			ikashop.SendAuctionOpenAuction(self.data['owner'])
	def _OverInItem(self, slot):
		tooltip = self.GetToolTip()
		tooltip.ClearToolTip()
		tooltip.AddItemData(self.data['vnum'], self.data['sockets'], self.data['attrs'])
		tooltip.ShowToolTip()

	def _OverOutItem(self):
		tooltip = self.GetToolTip()
		tooltip.HideToolTip()

	if app.EXTEND_IKASHOP_PRO:
		def _OnClickMessageSeller(self):
			self.searchShopBoard.OpenWhisper(self.sellerName.GetText())

	def SetSearchShopBoard(self, board):
		pass
		# self.searchShopBoard = proxy(board)

	def GetId(self):
		return self.data['id']

	def SetNotAvailable(self):
		if not self.data['is_auction']:
			self.slot.DisableSlot(0)
			self.itemName.SetPackedFontColor(0xFFFF8888)
			self.buyButton.Hide()
			self.offerButton.Hide()

	def SetAvailable(self):
		if not self.data['is_auction']:
			self.slot.EnableSlot(0)
			self.itemName.SetPackedFontColor(0xFFFFFFFF)
			self.buyButton.Show()
			self.offerButton.Show()

	def Setup(self, data):
		if data['is_auction']:
			self.buyButton.Hide()
			self.offerButton.Hide()
			self.background.LoadImage("ikashop/lite/search_shop/result_item_auction_box.png")
			self.openSellingBoard.SetText(locale.IKASHOP_SEARCH_SHOP_OPEN_AUCTION_BUTTON_TEXT)
			self.openSellingBoard.Show()
		else:
			self.buyButton.Show()
			self.offerButton.Show()
			self.background.LoadImage("ikashop/lite/search_shop/result_item_box.png")
			self.openSellingBoard.Hide()

		# setting itemname
		item.SelectItem(data['vnum'])
		itemName = item.GetItemName()
		if data['is_auction']:
			itemName += ' ' + locale.IKASHOP_SEARCH_SHOP_ITEM_NAME_AUCTION
		self.itemName.SetText(itemName)

		# setting seller name
		self.sellerName.SetText(data['seller_name'])

		if app.EXTEND_IKASHOP_PRO:
			sx, sy = self.sellerName.GetLocalPosition()
			self.messageSellerButton.SetPosition(sx + self.sellerName.GetTextSize()[0] + 10, sy)

		# setting duration
		self.duration.SetText(locale.SecondToDHM(data['duration']*60))

		# setting price
		self.price.SetText(locale.NumberToString(data['price']))

		if ENABLE_CHEQUE_SYSTEM:
			self.cheque.Show() if data['cheque'] != 0 else self.cheque.Hide()
			self.chequeIcon.Show() if data['cheque'] != 0 else self.chequeIcon.Hide()
			self.cheque.SetText(locale.NumberToString(data['cheque']))

		# setting slot
		itemcount = data['count'] if data['count'] > 1 else 0
		self.slot.ArrangeSlot(0, 1, item.GetItemSize()[1], SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage("ikashop/lite/common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetItemSlot(0, data['vnum'], itemcount)
		self.data = data


class IkarusSearchShopBoard(IkashopBoardWithTitleBar):

	RESULT_ITEM_VIEW_COUNT = 4

	ITEM_TYPES = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_WEAPON,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_ARMOR,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_JEWEL,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_COSTUME,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_PET,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_MOUNT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_ALCHEMY,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_BOOK,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_STONE,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_MINERALS,
		locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_FISH,
	)

	SUBTYPE_WEAPON = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_SWORD,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_TWOHANDED,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_BLADE,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_DAGGER,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_BOW,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_BELL,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_FAN,
	)

	if app.ENABLE_WOLFMAN_CHARACTER:
		SUBTYPE_WEAPON += (locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_WEAPON_CLAW,)

	SUBTYPE_ARMOR = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_ARMOR_WARRIOR,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_ARMOR_SURA,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_ARMOR_ASSASSIN,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_ARMOR_SHAMAN,
	)

	if app.ENABLE_WOLFMAN_CHARACTER:
		SUBTYPE_ARMOR += (locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_ARMOR_WOLFMAN,)

	SUBTYPE_JEWEL = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_JEWEL_HELM,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_JEWEL_SHIELD,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_JEWEL_EAR,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_JEWEL_NECK,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_JEWEL_WRIST,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_JEWEL_SHOES,
	)

	SUBTYPE_COSTUME = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_COSTUME_BODY,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_COSTUME_WEAPON,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_COSTUME_HAIR,
	)

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		SUBTYPE_COSTUME += (locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_COSTUME_SASH,)

	SUBTYPE_PET = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_PET_EGGS,
		locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_PET_SEALS,
	)

	SUBTYPE_MOUNT = (locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,)
	SUBTYPE_ALCHEMY = (locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,)
	SUBTYPE_BOOKS = (locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,)
	SUBTYPE_STONE = (locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,)
	SUBTYPE_MINERAL = (locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,)
	SUBTYPE_FISH = (locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,)

	SUB_TYPES = (
		(locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,),
		SUBTYPE_WEAPON,
		SUBTYPE_ARMOR,
		SUBTYPE_JEWEL,
		SUBTYPE_COSTUME,
		SUBTYPE_PET,
		SUBTYPE_MOUNT,
		SUBTYPE_ALCHEMY,
		SUBTYPE_BOOKS,
		SUBTYPE_STONE,
		SUBTYPE_MINERAL,
		SUBTYPE_FISH,
	)

	SASH_ABSORBS = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_SASH_GRADE_VALUE0,
		locale.IKASHOP_SEARCH_SHOP_SASH_GRADE_VALUE1,
		locale.IKASHOP_SEARCH_SHOP_SASH_GRADE_VALUE2,
		locale.IKASHOP_SEARCH_SHOP_SASH_GRADE_VALUE3,
	)

	ALCHEMY_GRADES = (
		locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,
		locale.IKASHOP_SEARCH_SHOP_DRAGON_SOUL_GRADE_NORMAL,
		locale.IKASHOP_SEARCH_SHOP_DRAGON_SOUL_GRADE_BRILLIANT,
		locale.IKASHOP_SEARCH_SHOP_DRAGON_SOUL_GRADE_RARE,
		locale.IKASHOP_SEARCH_SHOP_DRAGON_SOUL_GRADE_ANCIENT,
		locale.IKASHOP_SEARCH_SHOP_DRAGON_SOUL_GRADE_LEGENDARY,
	)

	def __init__(self):
		super(IkarusSearchShopBoard, self).__init__()
		# ikashop.SetSearchShopBoard(self)
		self.items = []
		self.lastOpen = 0
		self.markItemInfo = None
		self._MakeItemNameContainers()
		self._SettingUpBoard()
		self._LoadSearchShopWindow()

	def __del__(self):
		super(IkarusSearchShopBoard, self).__del__()
		# ikashop.SetSearchShopBoard(None)

	def _MakeItemNameContainers(self):
		names = ikashop.GetItemNames()
		self.itemNames = set()

		for name in names:
			f = name.find("+")
			if f != -1 and len(name)-1 != f and name[f+1:].isdigit():
				name = name[:f]
			self.itemNames.add(name.lower())

	def _SettingUpBoard(self):
		self.SetSize(604, 519)
		self.SetTitleName(locale.IKASHOP_SEARCH_SHOP_BOARD_TITLE)
		self.SetCloseEvent(self.Close)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")

	def _LoadLinkedBoard(self):
		self.shopGuestBoard = IkarusShopGuestBoard()
		self.auctionGuestBoard = IkarusAuctionGuestBoard()
		self.auctionListBoard = IkarusAuctionListBoard()
		self.historyFilterBoard = IkarusHistoryFilterBoard()

		# self.auctionListBoard.SetSearchShopBoard(self)
		# self.historyFilterBoard.SetSearchShopBoard(self)
		self.historyFilterBoard.SetFilters(ikashop.GetFilterHistory())

	def _LoadSearchShopWindow(self):
		self._LoadLinkedBoard()
		getBottom = lambda win : win.GetLocalPosition()[1] + win.GetHeight()
		getRight = lambda win : win.GetLocalPosition()[0] + win.GetWidth()

		largerComboBoxImages = (
			"ikashop/lite/search_shop/attribute_element/default.png",
			"ikashop/lite/search_shop/attribute_element/default.png",
			"ikashop/lite/search_shop/attribute_element/hover.png",
		)

		self.inputNameBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14,40))
		self.inputNameBox.LoadImage("ikashop/lite/search_shop/input_name.png")
		self.inputNameBox.SetScale(155.0 / self.inputNameBox.GetWidth(), 1.0)

		self.searchButton = self.CreateWidget(ui.Button, pos = (14 + self.inputNameBox.GetWidth() + 2, 42))
		self.searchButton.SetUpVisual("ikashop/lite/search_shop/mini_search_button/default.png")
		self.searchButton.SetDownVisual("ikashop/lite/search_shop/mini_search_button/default.png")
		self.searchButton.SetOverVisual("ikashop/lite/search_shop/mini_search_button/hover.png")
		self.searchButton.SAFE_SetEvent(self._OnClickSearchButton)
		self.searchButton.SetToolTipText(locale.IKASHOP_SEARCH_SHOP_SEARCH_BUTTON_TEXT)

		iw = self.inputNameBox.GetWidth() - self.searchButton.GetWidth() - 6
		ih = self.inputNameBox.GetHeight() - 6
		self.inputNameEdit = self.CreateWidget(ui.EditLine, pos = (6, 6), size = (iw, ih), parent=self.inputNameBox)
		self.inputNameEdit.SetMax(ikashop.FILTER_NAME_MAX_LEN)
		self.inputNameEdit.SetEscapeEvent(ui.__mem_func__(self.inputNameEdit.KillFocus))
		self.inputNameEdit.SetUpdateEvent(self._OnUpdateInputName)
		self.inputNameBox.SetOnMouseLeftButtonUpEvent(self.inputNameEdit.SetFocus)

		self.inputNameSuggestion = self.CreateWidget(IkarusShopComboBox, pos = (14, getBottom(self.inputNameBox)+2))
		self.inputNameSuggestion.SetSelectItemEvent(self._OnSelectSuggestedItemName)
		self.inputNameSuggestion.ChangeElementImages(largerComboBoxImages)
		self.inputNameSuggestion.SetViewCount(6)
		self.inputNameSuggestion.SetItems(["",])

		self.resetFilterButton = self.CreateWidget(ui.Button, pos = (getRight(self.searchButton) + 3, 42))
		self.resetFilterButton.SetUpVisual("ikashop/lite/search_shop/reset_filter_button/default.png")
		self.resetFilterButton.SetDownVisual("ikashop/lite/search_shop/reset_filter_button/default.png")
		self.resetFilterButton.SetOverVisual("ikashop/lite/search_shop/reset_filter_button/hover.png")
		self.resetFilterButton.SAFE_SetEvent(self._OnClickResetFilters)
		self.resetFilterButton.SetToolTipText(locale.IKASHOP_SEARCH_SHOP_RESET_FILTER_BUTTON_TEXT)

		# item type filter
		self.itemTypeFilterBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, 72))
		self.itemTypeFilterBox.LoadImage("ikashop/lite/search_shop/filter_box.png")

		self.itemTypeHeader = self.CreateWidget(ui.TextLine, pos = (6, 13), parent = self.itemTypeFilterBox)
		self.itemTypeHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ITEM_TYPE_HEADER)

		self.itemTypeSelectButton = self.CreateWidget(ui.Button, pos = (85, 8), parent = self.itemTypeFilterBox)
		self.itemTypeSelectButton.SetUpVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemTypeSelectButton.SetDownVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemTypeSelectButton.SetOverVisual("ikashop/lite/search_shop/combo_box_button/hover.png")
		self.itemTypeSelectButton.SAFE_SetEvent(self._OnClickItemTypeSelectButton)

		self.itemTypeSelectComboBox = self.CreateWidget(IkarusShopComboBox, pos = (14 + 85, 72 + 28))
		self.itemTypeSelectComboBox.SetItems(self.ITEM_TYPES)
		self.itemTypeSelectComboBox.SetSelectItemEvent(self._OnSelectItemType)

		# item subtype filter
		self.itemSubTypeHeader = self.CreateWidget(ui.TextLine, pos = (6, 39), parent = self.itemTypeFilterBox)
		self.itemSubTypeHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ITEM_SUBTYPE_HEADER)

		self.itemSubTypeSelectButton = self.CreateWidget(ui.Button, pos = (85, 8+26), parent = self.itemTypeFilterBox)
		self.itemSubTypeSelectButton.SetUpVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemSubTypeSelectButton.SetDownVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemSubTypeSelectButton.SetOverVisual("ikashop/lite/search_shop/combo_box_button/hover.png")
		self.itemSubTypeSelectButton.SAFE_SetEvent(self._OnClickItemSubTypeSelectButton)

		self.itemSubTypeSelectComboBox = self.CreateWidget(IkarusShopComboBox, pos = (14 + 86, 72 + 8 + 26 + 20))
		self.itemSubTypeSelectComboBox.SetSelectItemEvent(self._OnSelectItemSubType)
		self.itemSubTypeSelectComboBox.SetItems([locale.IKASHOP_SEARCH_SHOP_SELECT_AN_ELEMENT,])

		# item price filter
		self.itemPriceFilterBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, getBottom(self.itemTypeFilterBox) + 5))
		self.itemPriceFilterBox.LoadImage("ikashop/lite/search_shop/filter_box.png")

		self.itemPriceMinHeader = self.CreateWidget(ui.TextLine, pos = (6, 13), parent = self.itemPriceFilterBox)
		self.itemPriceMinHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ITEM_PRICE_MIN_HEADER)

		self.itemPriceMaxHeader = self.CreateWidget(ui.TextLine, pos = (6, 39), parent = self.itemPriceFilterBox)
		self.itemPriceMaxHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ITEM_PRICE_MAX_HEADER)

		self.itemPriceMinBox = self.CreateWidget(ui.ImageBox, pos = (64, 8), parent = self.itemPriceFilterBox)
		self.itemPriceMinBox.LoadImage("ikashop/lite/search_shop/input_box.png")

		self.itemPriceMaxBox = self.CreateWidget(ui.ImageBox, pos = (64, 8+26), parent = self.itemPriceFilterBox)
		self.itemPriceMaxBox.LoadImage("ikashop/lite/search_shop/input_box.png")

		self.itemPriceMinEdit = self.CreateWidget(ui.EditLine, pos = (6, 6), parent = self.itemPriceMinBox)
		self.itemPriceMinEdit.SetMax(12)
		self.itemPriceMinEdit.SetEscapeEvent(ui.__mem_func__(self.itemPriceMinEdit.KillFocus))
		self.itemPriceMinEdit.SetNumberMode()
		self.itemPriceMinBox.SetOnMouseLeftButtonUpEvent(self.itemPriceMinEdit.SetFocus)

		self.itemPriceMaxEdit = self.CreateWidget(ui.EditLine, pos = (6, 6), parent = self.itemPriceMaxBox)
		self.itemPriceMaxEdit.SetMax(12)
		self.itemPriceMaxEdit.SetEscapeEvent(ui.__mem_func__(self.itemPriceMaxEdit.KillFocus))
		self.itemPriceMaxEdit.SetNumberMode()
		self.itemPriceMaxBox.SetOnMouseLeftButtonUpEvent(self.itemPriceMaxEdit.SetFocus)

		# item level filter
		self.itemLevelFilterBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, getBottom(self.itemPriceFilterBox) + 5))
		self.itemLevelFilterBox.LoadImage("ikashop/lite/search_shop/filter_box.png")

		self.itemLevelMinHeader = self.CreateWidget(ui.TextLine, pos = (6, 13), parent = self.itemLevelFilterBox)
		self.itemLevelMinHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ITEM_LEVEL_MIN_HEADER)

		self.itemLevelMaxHeader = self.CreateWidget(ui.TextLine, pos = (6, 39), parent = self.itemLevelFilterBox)
		self.itemLevelMaxHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ITEM_LEVEL_MAX_HEADER)

		self.itemLevelMinBox = self.CreateWidget(ui.ImageBox, pos = (64, 8), parent = self.itemLevelFilterBox)
		self.itemLevelMinBox.LoadImage("ikashop/lite/search_shop/input_box.png")

		self.itemLevelMaxBox = self.CreateWidget(ui.ImageBox, pos = (64, 8+26), parent = self.itemLevelFilterBox)
		self.itemLevelMaxBox.LoadImage("ikashop/lite/search_shop/input_box.png")

		self.itemLevelMinEdit = self.CreateWidget(ui.EditLine, pos = (6, 6), parent = self.itemLevelMinBox)
		self.itemLevelMinEdit.SetMax(12)
		self.itemLevelMinEdit.SetEscapeEvent(ui.__mem_func__(self.itemLevelMinEdit.KillFocus))
		self.itemLevelMinEdit.SetNumberMode()
		self.itemLevelMinBox.SetOnMouseLeftButtonUpEvent(self.itemLevelMinEdit.SetFocus)

		self.itemLevelMaxEdit = self.CreateWidget(ui.EditLine, pos = (6, 6), parent = self.itemLevelMaxBox)
		self.itemLevelMaxEdit.SetMax(12)
		self.itemLevelMaxEdit.SetEscapeEvent(ui.__mem_func__(self.itemLevelMaxEdit.KillFocus))
		self.itemLevelMaxEdit.SetNumberMode()
		self.itemLevelMaxBox.SetOnMouseLeftButtonUpEvent(self.itemLevelMaxEdit.SetFocus)

		# item attributes filter
		self.attributeSettings = GetAttributeSettings()
		self.attributeBonusToItem = {bonus[0]:index for index, bonus in enumerate(self.attributeSettings)}

		self.itemAttrsFilterBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, getBottom(self.itemLevelFilterBox) + 5))
		self.itemAttrsFilterBox.LoadImage("ikashop/lite/search_shop/filter_box.png")
		self.itemAttrsFilterBox.SetScale(1.0, 126.0 / self.itemAttrsFilterBox.GetHeight())

		self.attrSelectButtons = []
		self.attrComboBoxes = []
		self.attrValueBoxes = []
		self.attrValueEdits = []

		for i in xrange(ikashop.FILTER_ATTRIBUTE_NUM):
			# select button
			attrSelectButton = self.CreateWidget(ui.Button, pos = (6, 6 + i*23), parent = self.itemAttrsFilterBox)
			attrSelectButton.SetUpVisual("ikashop/lite/search_shop/attribute_select_button/default.png")
			attrSelectButton.SetDownVisual("ikashop/lite/search_shop/attribute_select_button/default.png")
			attrSelectButton.SetOverVisual("ikashop/lite/search_shop/attribute_select_button/hover.png")
			attrSelectButton.SAFE_SetEvent(self._OnClickAttributeSelectButton, i)
			attrSelectButton.SetText("")
			bx, by = attrSelectButton.ButtonText.GetLocalPosition()
			attrSelectButton.ButtonText.SetPosition(bx - 10, by)
			self.attrSelectButtons.append(attrSelectButton)

			attrComboBox = self.CreateWidget(IkarusShopComboBox, pos = (14 + 6, self.itemAttrsFilterBox.GetLocalPosition()[1] + 5 + i*23 + 20))
			attrComboBox.SetSelectItemEvent(lambda id, text, _self = proxy(self), _num = i : _self._OnSelectAttributeItem(_num, id, text))
			attrComboBox.ChangeElementImages(largerComboBoxImages)
			attrComboBox.SetViewCount(7)
			attrComboBox.SetItems([text for apply, text in self.attributeSettings])
			self.attrComboBoxes.append(attrComboBox)

			attrValueBox = self.CreateWidget(ui.ImageBox, pos = (148, 6 + i*23), parent = self.itemAttrsFilterBox)
			attrValueBox.LoadImage("ikashop/lite/search_shop/attribute_value_box.png")
			self.attrValueBoxes.append(attrValueBox)

			attrValueEdit = self.CreateWidget(ui.EditLine, pos = (9, 6), parent = attrValueBox)
			attrValueEdit.SetMax(4)
			attrValueEdit.SetEscapeEvent(ui.__mem_func__(attrValueEdit.KillFocus))
			attrValueEdit.SetNumberMode()
			attrValueBox.SetOnMouseLeftButtonUpEvent(attrValueEdit.SetFocus)
			self.attrValueEdits.append(attrValueEdit)

		# special filters
		self.itemSpecialFilterBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, getBottom(self.itemAttrsFilterBox) + 5))
		self.itemSpecialFilterBox.LoadImage("ikashop/lite/search_shop/filter_box.png")

		self.itemAlchemyGradeHeader = self.CreateWidget(ui.TextLine, pos = (6, 13), parent = self.itemSpecialFilterBox)
		self.itemAlchemyGradeHeader.SetText(locale.IKASHOP_SEARCH_SHOP_ALCHEMY_GRADE_HEADER)

		self.itemAlchemyGradeSelectButton = self.CreateWidget(ui.Button, pos = (85, 8), parent = self.itemSpecialFilterBox)
		self.itemAlchemyGradeSelectButton.SetUpVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemAlchemyGradeSelectButton.SetDownVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemAlchemyGradeSelectButton.SetOverVisual("ikashop/lite/search_shop/combo_box_button/hover.png")
		self.itemAlchemyGradeSelectButton.SAFE_SetEvent(self._OnClickAlchemyGradeSelectButton)

		self.itemAlchemyGradeSelectComboBox = self.CreateWidget(IkarusShopComboBox, pos = (14 + 85, getBottom(self.itemAttrsFilterBox) + 5 + 8 + 20))
		self.itemAlchemyGradeSelectComboBox.SetSelectItemEvent(self._OnSelectAlchemyGradeType)
		self.itemAlchemyGradeSelectComboBox.SetItems(self.ALCHEMY_GRADES)

		self.itemSashAbsHeader = self.CreateWidget(ui.TextLine, pos = (6, 39), parent = self.itemSpecialFilterBox)
		self.itemSashAbsHeader.SetText(locale.IKASHOP_SEARCH_SHOP_SASH_ABSORB_HEADER)

		self.itemSashAbsSelectButton = self.CreateWidget(ui.Button, pos = (85, 8+26), parent = self.itemSpecialFilterBox)
		self.itemSashAbsSelectButton.SetUpVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemSashAbsSelectButton.SetDownVisual("ikashop/lite/search_shop/combo_box_button/default.png")
		self.itemSashAbsSelectButton.SetOverVisual("ikashop/lite/search_shop/combo_box_button/hover.png")
		self.itemSashAbsSelectButton.SAFE_SetEvent(self._OnClickSashGradeSelectButton)

		self.itemSashAbsSelectComboBox = self.CreateWidget(IkarusShopComboBox, pos = (14 + 86, getBottom(self.itemAttrsFilterBox) + 5 + 8 + 26 + 20))
		self.itemSashAbsSelectComboBox.SetItems(self.SASH_ABSORBS)
		self.itemSashAbsSelectComboBox.SetSelectItemEvent(self._OnSelectSashGrade)
		self.itemSashAbsSelectComboBox.SetViewCount(4)

		# buttons on the bottom
		self.auctionListButton = self.CreateWidget(ui.Button, pos = (14, getBottom(self.itemSpecialFilterBox) + 6))
		self.auctionListButton.SetUpVisual("ikashop/lite/search_shop/auction_list_button/default.png")
		self.auctionListButton.SetDownVisual("ikashop/lite/search_shop/auction_list_button/default.png")
		self.auctionListButton.SetOverVisual("ikashop/lite/search_shop/auction_list_button/hover.png")
		self.auctionListButton.SAFE_SetEvent(self._OnClickAuctionListButton)
		self.auctionListButton.SetText(locale.IKASHOP_SEARCH_SHOP_AUCTION_LIST_BUTTON_TEXT)
		tx, ty = self.auctionListButton.ButtonText.GetLocalPosition()
		self.auctionListButton.ButtonText.SetPosition(tx + 5, ty)
		self.auctionListButton.ButtonText.SetPackedFontColor(0xFFFFFFFF)

		hpos = (14 + self.itemSpecialFilterBox.GetWidth() - self.auctionListButton.GetWidth(), getBottom(self.itemSpecialFilterBox) + 6)
		self.historyButton = self.CreateWidget(ui.Button, pos = hpos)
		self.historyButton.SetUpVisual("ikashop/lite/search_shop/history_button/default.png")
		self.historyButton.SetDownVisual("ikashop/lite/search_shop/history_button/default.png")
		self.historyButton.SetOverVisual("ikashop/lite/search_shop/history_button/hover.png")
		self.historyButton.SAFE_SetEvent(self._OnClickHistoryButton)
		self.historyButton.SetText(locale.IKASHOP_SEARCH_SHOP_HISTORY_BUTTON_TEXT)
		tx, ty = self.historyButton.ButtonText.GetLocalPosition()
		self.historyButton.ButtonText.SetPosition(tx + 5, ty)
		self.historyButton.ButtonText.SetPackedFontColor(0xFFFFFFFF)

		self.resultBox = self.CreateWidget(ui.ExpandedImageBox, pos = (227, 40))
		self.resultBox.LoadImage("ikashop/lite/search_shop/result_box.png")
		self.resultBox.SetMouseWheelEvent(self._OnScrollMouseWheelResultItems)
		hs = float(self.resultBox.GetWidth() - 10) / self.resultBox.GetWidth()
		vs = 469.0 / self.resultBox.GetHeight()
		self.resultBox.SetScale(hs, vs)

		# making result items
		self.resultItems = []
		for i in xrange(self.RESULT_ITEM_VIEW_COUNT):
			item = self.CreateWidget(IkarusSearchShopItem, pos = (5, 4 + 116*i), parent = self.resultBox)
			# item.SetSearchShopBoard(self)
			self.resultItems.append(item)

		# making result item scrollbar
		self.resultItemScrollBar = self.CreateWidget(ui.ScrollBar, pos = (self.resultBox.GetWidth() - 19, 3), parent = self.resultBox)
		self.resultItemScrollBar.SetScrollEvent(self._OnScrollResultItems)
		self.resultItemScrollBar.SetScrollBarSize(self.resultBox.GetHeight() - 6)

		# making automatically close the combo box
		# and setting them on top, with 0th element selected
		self.comboBoxes = []
		for value in vars(self).values() + self.attrComboBoxes:
			if isinstance(value, IkarusShopComboBox):
				value.AddFlag("float")
				value.SetTop()
				value.SelectItem(0)
				self._RegisterDialog(value)
				self.comboBoxes.append(proxy(value))

	def _ExtractFilterTypes(self):
		return \
			self.itemTypeSelectComboBox.GetSelectedItem(),\
			self.itemSubTypeSelectComboBox.GetSelectedItem()

	def _ExtractFilterPrice(self):
		minPrice = self.itemPriceMinEdit.GetText()
		minPrice = minPrice.lower().replace("k", "000")
		minPrice = long(minPrice) if minPrice and minPrice.isdigit() else long(0)
		maxPrice = self.itemPriceMaxEdit.GetText()
		maxPrice = maxPrice.lower().replace("k", "000")
		maxPrice = long(maxPrice) if maxPrice and maxPrice.isdigit() else long(0)
		return minPrice, maxPrice

	def _ExtractFilterLevel(self):
		minLevel = self.itemLevelMinEdit.GetText()
		minLevel = int(minLevel) if minLevel and minLevel.isdigit() else 0
		maxLevel = self.itemLevelMaxEdit.GetText()
		maxLevel = int(maxLevel) if maxLevel and maxLevel.isdigit() else 0
		return minLevel, maxLevel

	def _ExtractFilterAttributes(self):
		def extractOne(combo, edit):
			if combo.GetSelectedItem() == 0:
				return 0,0
			bonus = self.attributeSettings[combo.GetSelectedItem()][0]
			value = edit.GetText()
			value = int(value) if value and value.isdigit() else 0
			return bonus, value

		ret = tuple(extractOne(self.attrComboBoxes[i], self.attrValueEdits[i]) for i in xrange(ikashop.FILTER_ATTRIBUTE_NUM))
		return ret

	def _ExtractFilterSpecial(self):
		sashAbs = self.itemSashAbsSelectComboBox.GetSelectedItem()
		dssGrade = self.itemAlchemyGradeSelectComboBox.GetSelectedItem()
		return sashAbs, dssGrade

	def _ExtractFilterSettings(self):
		# getting values
		inputName = self.inputNameEdit.GetText()
		type, subtype = self._ExtractFilterTypes()
		prices = self._ExtractFilterPrice()
		levels = self._ExtractFilterLevel()
		attributes = self._ExtractFilterAttributes()
		specials = self._ExtractFilterSpecial()
		# making arg tuple
		args = (inputName, type, subtype, prices, levels, attributes, specials)
		if not IsUsingFilter(args):
			return None
		return args

	def _OnClickSearchButton(self):
		self.inputNameEdit.KillFocus()
		filters = self._ExtractFilterSettings()
		if filters is None:
			self.OpenPopupDialog(locale.IKASHOP_SEARCH_SHOP_NO_FILTER_USED)
			return
		ikashop.SendFilterRequest(*filters)

	def _OnClickAuctionListButton(self):
		self.auctionListBoard.Toggle()

	def _OnClickItemTypeSelectButton(self):
		for combo in self.comboBoxes:
			if not combo.IsMe(self.itemTypeSelectComboBox) and combo.IsShow():
				combo.Close()
		self.itemTypeSelectComboBox.Toggle()

	def _OnClickItemSubTypeSelectButton(self):
		for combo in self.comboBoxes:
			if not combo.IsMe(self.itemSubTypeSelectComboBox) and combo.IsShow():
				combo.Close()
		self.itemSubTypeSelectComboBox.Toggle()

	def _OnSelectItemType(self, index, text):
		self.itemTypeSelectButton.SetText(text)
		self.itemSubTypeSelectComboBox.SetItems(self.SUB_TYPES[index])
		self.itemSubTypeSelectComboBox.SelectItem(0)

	def _OnSelectItemSubType(self, index, text):
		self.itemSubTypeSelectButton.SetText(text)

	def _OnSelectAttributeItem(self, num, index, text):
		usingButton = self.attrSelectButtons[num]
		for i in xrange(100):
			btext = text[:-i] if i > 0 else text
			if i != 0:
				btext += ".."
			usingButton.SetText(btext)
			if usingButton.ButtonText.GetTextSize()[0] + 35 < usingButton.GetWidth():
				break

	def _OnClickAttributeSelectButton(self, num):
		usingComboBox = self.attrComboBoxes[num]
		for combo in self.comboBoxes:
			if not combo.IsMe(usingComboBox) and combo.IsShow():
				combo.Close()
		usingComboBox.Toggle()

	def _OnClickSashGradeSelectButton(self):
		for combo in self.comboBoxes:
			if not combo.IsMe(self.itemSashAbsSelectComboBox) and combo.IsShow():
				combo.Close()
		self.itemSashAbsSelectComboBox.Toggle()

	def _OnSelectSashGrade(self, index, text):
		self.itemSashAbsSelectButton.SetText(text)

	def _OnClickAlchemyGradeSelectButton(self):
		for combo in self.comboBoxes:
			if not combo.IsMe(self.itemAlchemyGradeSelectComboBox) and combo.IsShow():
				combo.Close()
		self.itemAlchemyGradeSelectComboBox.Toggle()

	def _OnSelectAlchemyGradeType(self, index, text):
		self.itemAlchemyGradeSelectButton.SetText(text)

	def _OnUpdateInputName(self, isFocus):
		if not isFocus or len(self.inputNameEdit.GetText()) < 3:
			self.inputNameSuggestion.Close()
			return

		text = self.inputNameEdit.GetText().lower()
		most_relevant = []
		less_relevant = []

		for name in self.itemNames:
			if name.startswith(text):
				most_relevant.append(name)
			elif text in name:
				less_relevant.append(name)

		most_relevant = sorted(most_relevant)
		less_relevant = sorted(less_relevant)
		suggestions = most_relevant + less_relevant

		self.inputNameSuggestion.SetItems(suggestions)
		if suggestions:
			self.inputNameSuggestion.Open()
		else:
			self.inputNameSuggestion.Close()

	def _OnSelectSuggestedItemName(self, index, name):
		self.inputNameEdit.SetText(name)
		self.inputNameEdit.KillFocus()

	def _OnClickResetFilters(self):
		# selecting 0 item on each combo box
		for combo in self.comboBoxes:
			if not combo.IsMe(self.inputNameSuggestion):
				combo.SelectItem(0)
		# resetting edit line values
		self.itemPriceMinEdit.SetText("")
		self.itemPriceMaxEdit.SetText("")
		self.itemLevelMinEdit.SetText("")
		self.itemLevelMaxEdit.SetText("")
		self.inputNameEdit.SetText("")
		for edit in self.attrValueEdits:
			edit.SetText("")

	def _OnClickHistoryButton(self):
		self.historyFilterBoard.Toggle()

	def _OnScrollResultItems(self):
		self._RefreshResultItem()

	def _OnScrollMouseWheelResultItems(self, delta):
		self.resultItemScrollBar.OnDown() if delta < 0\
			else self.resultItemScrollBar.OnUp()
		return True

	def _RefreshResultItem(self):
		# calculating sindex
		pos = self.resultItemScrollBar.GetPos() if self.resultItemScrollBar.IsShow() else 0.0
		diff = max(len(self.items) - self.RESULT_ITEM_VIEW_COUNT, 0)
		sindex = int(diff * pos)
		eindex = sindex + min(len(self.items), self.RESULT_ITEM_VIEW_COUNT)

		# hiding all views
		for view in self.resultItems:
			view.Hide()

		# setting up and showing only used views
		for i in xrange(sindex, eindex):
			ri = i - sindex
			data = self.items[i]
			view = self.resultItems[ri]
			view.Setup(data)
			view.Show()
			view.SetAvailable() if data.get('deleted', 0) == 0 \
				else view.SetNotAvailable()

		# updating scrollbar's middlebar length
		self.resultItemScrollBar.UpdateScrollbarLenght(4 + 116*len(self.items))

	def _UpdateScrollbarState(self):
		self.resultItemScrollBar.Show() if self.RESULT_ITEM_VIEW_COUNT < len(self.items)\
			else self.resultItemScrollBar.Hide()
		self.resultItemScrollBar.SetPos(0)

	def _ApplySearchFilterSettings(self, settings):
		# setting up name
		self.inputNameEdit.SetText(settings['name'])
		# setting up prices
		self.itemPriceMaxEdit.SetText(str(settings['price_max']) if settings['price_max'] != 0 else "")
		self.itemPriceMinEdit.SetText(str(settings['price_min']) if settings['price_min'] != 0 else "")
		# setting up levels
		self.itemLevelMaxEdit.SetText(str(settings['level_max']) if settings['level_max'] != 0 else "")
		self.itemLevelMinEdit.SetText(str(settings['level_min']) if settings['level_min'] != 0 else "")
		# setting up comboboxes
		self.itemTypeSelectComboBox.SelectItem(settings['type'])
		self.itemSubTypeSelectComboBox.SelectItem(settings['subtype'])
		self.itemSashAbsSelectComboBox.SelectItem(settings['sash'])
		self.itemAlchemyGradeSelectComboBox.SelectItem(settings['alchemy'])
		# setting up attributes
		for attrComboBox, attrEdit, sett in zip(self.attrComboBoxes, self.attrValueEdits, settings['attrs']):
			type, value = sett
			attrEdit.SetText(str(value) if value != 0 else "")
			attrComboBox.SelectItem(self.attributeBonusToItem[type])

	def HistoryRedoSearch(self, settings):
		self._ApplySearchFilterSettings(settings)
		self._OnClickSearchButton()

	def Open(self):
		now = app.GetTime()
		if self.lastOpen == 0 or now - self.lastOpen > 60 or len(self.items) == 0:
			ikashop.SendRandomSearchFillRequest()
			self._IsRandomFilling = True
			return

		self.lastOpen = now
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()
		self.inputNameEdit.KillFocus()

	def DeleteSearchResultItem(self, id):
		for item in self.items:
			if item['id'] == id:
				item['deleted'] = 1

		for view in self.resultItems:
			if view.GetId() == id:
				view.SetNotAvailable()

	# BINARY CALLS
	def SetSearchResultItems(self, items):
		shuffle(items)
		self.items = items
		self._UpdateScrollbarState()
		self._RefreshResultItem()
		if self.IsShow() == False:
			self.Show()
			self.SetTop()
			self.lastOpen = app.GetTime()
		if not self._IsRandomFilling:
			self.RegisterHistoryFilter()
		self._IsRandomFilling = False

	def OpenShopGuest(self, data):
		self.shopGuestBoard.Open(data)
		if self.markItemInfo:
			vnum, count, price = self.markItemInfo
			self.shopGuestBoard.MarkItems(vnum, count, price)

	def ShopExpiredGuesting(self, id):
		self.shopGuestBoard.CheckExpiring(id)

	def ShopGuestRemoveItem(self, itemid):
		self.shopGuestBoard.ShopGuestRemoveItem(itemid)

	def ShopGuestEditItem(self, itemid, price):
		self.shopGuestBoard.EditItem(itemid, price)

	def OpenAuctionGuest(self, data):
		self.auctionGuestBoard.Open(data)

	def SetAuctionList(self, auctions):
		self.auctionListBoard.SetAuctions(auctions)

	def RegisterHistoryFilter(self):
		filter = self._ExtractFilterSettings()
		ikashop.RegisterFilterHistory(len(self.items), *filter)
		self.historyFilterBoard.SetFilters(ikashop.GetFilterHistory())

	if app.EXTEND_IKASHOP_PRO:
		def SetOpenWhisper(self, event):
			self.openWhisperEvent = event

		def OpenWhisper(self, name):
			self.openWhisperEvent(name)

