# Zmiana bonusow - the bonus switcher (MT2009_PLUS_BONUS_SWITCH_V1, Autor: Vekirion; Patryk,
# 5 October: "an UI window where a user puts in an item ... chooses which
# bonuses they want to target and at which values minimum ... the choice
# limited to the bonuses that an item can possess ... uses 39028, 71084, 71284,
# 76014 ... 76014 before the others ... the speed easily adjustable"; later the
# same day: a tab per item, right click puts an item in, a key for the window,
# "Wszystkie" / "Co najmniej X z", "Zmien raz" after a confirmation).
#
# The window is only a form: the server (playerbot_bonus_switch.h) checks the
# item and the bonuses, uses up one change item a change (76014 first), paces
# the changes by the speed sent here and stops by itself. Nothing here uses an
# item; the item's new bonuses arrive as the ordinary item updates.
#
# Five tabs: the five item slots at the top. Each holds its own item, bonus
# rows, mode and run; a click on a slot selects its tab, an item dropped on a
# slot (or right-clicked in the inventory, into the selected tab) is that tab's
# item, a right click on the slot takes it out. Several tabs may run at once.
#
#   window -> "/bonus_switch info <cell>" (an item put in), "/bonus_switch items",
#             "/bonus_switch start <cell> <speed> <need> <apply>:<min> ...",
#             "/bonus_switch once <cell>", "/bonus_switch stop <cell>"
#   server -> "BSW attrs <cell> <vnum> <apply>:<max> ...", "BSW items <76014> <others>",
#             "BSW state <cell> <0|1>", "BSW progress <cell> <changes> <76014> <others>",
#             "BSW done <cell> <reason> <changes> <76014 used> <others used>",
#             "BSW changed <cell>", "BSW msg <id> <data>" (game.py passes them here)
#
# The bonus picker is the flea market's (customfleamarket.py): one shared
# ListBox raised over the rows - ui.ComboBox does not draw above its board -
# and no lambda as an event (ui.__mem_func__ needs a bound method).
# Opened by the inventory sidebar's button (uiinventory.SidebarWindow) and the
# "bonus_switch" key (keybind.py, none by default).
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import grp
import item
import net
import player
import ui
import uiCommon
import uiToolTip
import mouseModule
import localeinfo_point

import warpsafe

TABS = 5
ROWS = 5
COSTUME_ROWS = 3	# a costume has 1-3 bonuses
COSTUME_RESET_VNUM = 70063
COSTUME_CHANGE_VNUM = 70064
SPEED_MIN = 1
SPEED_MAX = 20
SPEED_DEFAULT = 10
SPEED_KEY = "zmiana_bonusow_szybkosc"
SLOT_BASE = "d:/ymir work/ui/public/slot_base.sub"
CHECK_IMAGE = "d:/ymir work/ui/public/check_image.sub"

MODE_ALL = 0
MODE_AT_LEAST = 1

TEXT_TITLE = "Zmiana bonus\xf3w"
TEXT_DROP = "Przeci\xb9gnij bro\xf1, zbroj\xea lub kostium do jednego z p\xf3l u g\xf3ry."
TEXT_PICK = "Wybierz bonusy i minimalne warto\x9cci:"
TEXT_ALL = "Wszystkie"
TEXT_AT_LEAST = "Co najmniej"
TEXT_OF = "z"
TEXT_NONE = "- brak -"
TEXT_SPEED = "Szybko\x9c\xe6: %d zmian/s"
TEXT_ITEMS = "Zmianki (B): %d    Pozosta\xb3e: %d"
TEXT_CHANGES = "Wykonane zmiany: %d"
TEXT_RUNNING = "Zmienianie..."
TEXT_START = "Start"
TEXT_STOP = "Stop"
TEXT_CLEAR = "Wyczy\x9c\xe6"
TEXT_ONCE = "Zmie\xf1 raz"
TEXT_ONCE_ASK = "Zmieni\xe6 bonusy tego przedmiotu jeden raz?"
TEXT_ONCE_ASK2 = "Zu\xbfyje to 1 zmiank\xea (najpierw z (B))."
TEXT_HINT = "Zmianki z (B) s\xb9 u\xbfywane jako pierwsze"
TEXT_MAX = "%s (maks.)"
TEXT_COUNT = "Liczba bonus\xf3w na kostiumie (co najmniej):"
TEXT_COUNT_ANY = "Dowolna"
TEXT_COSTUME_ITEMS = "%s: %d    %s: %d"
TEXT_COSTUME_HINT = "Kostium: %s, dop\xf3ki brakuje bonus\xf3w, potem %s"
TEXT_COSTUME_ONCE = "Zu\xbfyje to 1 przedmiot (%s, a bez bonus\xf3w %s)."
TEXT_COSTUME_EMPTY = "Wybierz bonusy albo liczb\xea bonus\xf3w."
TEXT_TAB_BUSY = "Ten przedmiot jest w\xb3a\x9cnie zmieniany - zatrzymaj go najpierw."
TEXT_NEED = "Wpisz, ile bonus\xf3w ma si\xea zgadza\xe6 (1-%d)."
TEXT_SLOT_TIP = "Pole %d - PPM wyjmuje przedmiot"

MESSAGES = {
	1: "Zmiana bonus\xf3w jest teraz wy\xb3\xb9czona.",
	2: "Zamknij najpierw inne okna (handel, sklep, magazyn...).",
	3: "Tego przedmiotu nie mo\xbfna tu zmienia\xe6 (tylko bro\xf1, zbroje i kostiumy z ekwipunku).",
	4: "Ten przedmiot nie ma bonus\xf3w do zmiany.",
	5: "Przedmiot jest za\xb3o\xbfony, zablokowany albo w handlu.",
	6: "Wybierz przynajmniej jeden bonus.",
	7: "Za du\xbfo bonus\xf3w - przedmiot ma ich %d.",
	8: "Ten przedmiot nie mo\xbfe mie\xe6 tego bonusu.",
	9: "Za wysoka warto\x9c\xe6: %s.",
	10: "Nie masz przedmiot\xf3w do zmiany bonus\xf3w.",
	11: "Przedmiot ma ju\xbf wybrane bonusy.",
	12: TEXT_TAB_BUSY,
	13: "\"Co najmniej\" musi by\xe6 od 1 do %d.",
	14: "Naraz mo\xbfna zmienia\xe6 najwy\xbfej %d przedmiot\xf3w.",
	15: "Kostium mo\xbfe mie\xe6 od 1 do %d bonus\xf3w.",
	16: "Losowanie nie wysz\xb3o - bonusy wr\xf3ci\xb3y, przedmiot nie zosta\xb3 zu\xbfyty.",
}

DONE = {
	1: "Pole %d: gotowe! Wybrane bonusy wylosowane (zmian: %d).",
	2: "Pole %d: sko\xf1czy\xb3y si\xea przedmioty do zmiany bonus\xf3w (zmian: %d).",
	3: "Pole %d: zmiana bonus\xf3w zatrzymana (zmian: %d).",
	4: "Pole %d: przedmiot zosta\xb3 przesuni\xeaty albo zablokowany - zatrzymano (zmian: %d).",
	5: "Pole %d: zatrzymano - otwarte inne okno albo posta\xe6 nie mo\xbfe teraz u\xbfywa\xe6 przedmiot\xf3w (zmian: %d).",
}

COLOR_DIM = 0xffa0a0a0
COLOR_ATTR = 0xffc8c8c8
COLOR_OK = 0xff9be27c
COLOR_WARN = 0xffff6060
COLOR_HINT = 0xffd4b46c
COLOR_GREEN = 0xff5fc25f
COLOR_SELECTED = 0xc0d4b46c
COLOR_RUNNING = 0xc05fc25f

_state = {
	'window': None,
}


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def AppendChat(text):
	chat.AppendChat(chat.CHAT_TYPE_INFO, text)


def Send(command):
	# MT2009_PLUS_SIDEKICK_WARP_SAFE_V1: only in the game phase (warpsafe.py).
	if not warpsafe.InGame():
		return False
	net.SendChatPacket("/bonus_switch " + command)
	return True


def ApplyText(apply, value):
	try:
		text = localeinfo_point.GetApplyString(apply, value)
	except Exception:
		text = None
	return text or ("Bonus %d: %d" % (apply, value))


def IsCostume(vnum):
	"""A costume 70063/70064 take: body, hair, weapon (char_item.cpp)."""
	if not vnum:
		return False
	item.SelectItem(vnum)
	if item.GetItemType() != item.ITEM_TYPE_COSTUME:
		return False
	subTypes = [item.COSTUME_TYPE_BODY, item.COSTUME_TYPE_HAIR]
	if hasattr(item, 'COSTUME_TYPE_WEAPON'):
		subTypes.append(item.COSTUME_TYPE_WEAPON)
	return item.GetItemSubType() in subTypes


def IsSwitchable(vnum):
	if not vnum:
		return False
	item.SelectItem(vnum)
	return item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR) or IsCostume(vnum)


def ItemName(vnum, default):
	try:
		item.SelectItem(vnum)
		return item.GetItemName() or default
	except Exception:
		return default


def LoadSpeed():
	try:
		import uiwindowpos
		value = uiwindowpos.GetValue(SPEED_KEY, SPEED_DEFAULT)
	except Exception:
		value = SPEED_DEFAULT
	return max(SPEED_MIN, min(SPEED_MAX, ToInt(value, SPEED_DEFAULT)))


def SaveSpeed(value):
	try:
		import uiwindowpos
		uiwindowpos.SetValue(SPEED_KEY, value)
	except Exception:
		pass


class Tab(object):
	def __init__(self):
		self.Clear()

	def Clear(self):
		self.pos = -1
		self.vnum = 0
		self.options = []			# [(apply, max)] the item can roll
		self.rows = [(-1, "")] * ROWS	# (option index, min text)
		self.mode = MODE_ALL
		self.need = ""
		self.costume = False
		self.count = 0				# a costume's bonuses at least, 0 = any
		self.running = False
		self.changes = 0


class SeparatedListBox(ui.ListBox):
	"""The bonus list with a thin line between its rows."""
	LINE_COLOR = grp.GenerateColor(0.55, 0.47, 0.32, 0.55)

	def OnRender(self):
		ui.ListBox.OnRender(self)
		x, y = self.GetGlobalPosition()
		grp.SetColor(self.LINE_COLOR)
		for i in xrange(1, self.showLineCount):
			grp.RenderLine(x + 2, y + i * self.stepSize + 1, self.width - 4, 0)


class GreaterEqualSign(ui.Window):
	"""">=" drawn as lines: the point of > level with the middle of =."""
	COLOR = grp.GenerateColor(0.63, 0.63, 0.63, 1.0)

	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag('not_pick')
		self.SetSize(14, 8)

	def OnRender(self):
		x, y = self.GetGlobalPosition()
		grp.SetColor(self.COLOR)
		grp.RenderLine(x, y + 1, 5, 3)
		grp.RenderLine(x, y + 7, 5, -3)
		grp.RenderLine(x + 8, y + 2, 6, 0)
		grp.RenderLine(x + 8, y + 5, 6, 0)


class CheckMark(ui.Window):
	"""A tick inside a size x size box, two pixels thick."""
	COLOR = grp.GenerateColor(0.45, 0.85, 0.45, 1.0)

	def __init__(self, size):
		ui.Window.__init__(self)
		self.AddFlag('not_pick')
		self.SetSize(size, size)

	def OnRender(self):
		x, y = self.GetGlobalPosition()
		grp.SetColor(self.COLOR)
		for d in (0, 1):
			grp.RenderLine(x + 3, y + 6 + d, 3, 3)
			grp.RenderLine(x + 6, y + 9 + d, 5, -6)


class CheckBox(ui.Window):
	SIZE = 14

	def __init__(self, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.checked = False
		self.hover = False
		self.SetSize(self.SIZE, self.SIZE)
		self.border = self.__Bar(0, 0, self.SIZE, self.SIZE)
		self.fill = self.__Bar(1, 1, self.SIZE - 2, self.SIZE - 2)
		# check_image.sub is 24 x 16 and stuck out of the box: a tick drawn to fit
		self.mark = CheckMark(self.SIZE)
		self.mark.SetParent(self)
		self.mark.SetPosition(0, 0)
		self.__Refresh()

	def __Bar(self, x, y, width, height):
		bar = ui.Bar()
		bar.SetParent(self)
		bar.SetPosition(x, y)
		bar.SetSize(width, height)
		bar.AddFlag('not_pick')
		bar.Show()
		return bar

	def SetChecked(self, checked):
		self.checked = bool(checked)
		self.__Refresh()

	def __Refresh(self):
		self.border.SetColor(COLOR_GREEN if self.checked or self.hover else 0xff8a8a8a)
		self.fill.SetColor(0xff1e3a26 if self.checked else 0xff0a0a0a)
		if self.checked:
			self.mark.Show()
		else:
			self.mark.Hide()

	def OnMouseOverIn(self):
		self.hover = True
		self.__Refresh()

	def OnMouseOverOut(self):
		self.hover = False
		self.__Refresh()

	def OnMouseLeftButtonUp(self):
		if self.event:
			self.event(*self.args)
		return True


class BonusSwitchWindow(ui.BoardWithTitleBar):
	WIDTH = 470
	LEFT = 16
	SLOT_Y = 40
	SLOT_GAP = 30
	ROWS_Y = 196
	ROW_H = 28
	PICK_WIDTH = 180
	PICK_HEIGHT = 25
	EDIT_WIDTH = 56
	LINE_H = 17
	TEXT_H = 14
	SLIDER_W = 175	# sliderbar.sub
	BUTTON_W = 88	# large_button

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.widgets = []
		self.rows = []
		self.tabs = [Tab() for i in xrange(TABS)]
		self.current = 0
		self.slotMarks = []
		self.slotLabels = []
		self.activeRow = -1
		self.countPriority = -1
		self.countOther = -1
		self.countReset = 0
		self.countChange = 0
		self.speed = LoadSpeed()
		self.itemToolTip = None
		self.textToolTip = None
		self.questionDialog = None

		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName(TEXT_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.__Build()
		self.SetCenterPosition()

	## building

	def __Label(self, x, y, text, color=None):
		line = ui.TextLine()
		line.SetParent(self)
		line.SetPosition(x, y)
		line.SetText(text)
		if color is not None:
			line.SetPackedFontColor(color)
		line.AddFlag('not_pick')
		line.Show()
		self.widgets.append(line)
		return line

	def __Button(self, x, y, text, size, event, *args):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % size)
		button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % size)
		button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % size)
		button.SetText(text)
		button.SAFE_SetEvent(event, *args)
		button.Show()
		self.widgets.append(button)
		return button

	def __Bar(self, x, y, width, height, color):
		bar = ui.Bar()
		bar.SetParent(self)
		bar.SetPosition(x, y)
		bar.SetSize(width, height)
		bar.SetColor(color)
		bar.AddFlag('not_pick')
		self.widgets.append(bar)
		return bar

	def __EditBox(self, x, y, width, maxLen):
		bar = ui.SlotBar()
		bar.SetParent(self)
		bar.SetPosition(x, y)
		bar.SetSize(width, 20)
		bar.AddFlag('not_pick')
		bar.Show()
		self.widgets.append(bar)
		edit = ui.EditLine()
		edit.SetParent(bar)
		edit.SetPosition(4, 3)
		edit.SetSize(width - 8, 16)
		edit.SetMax(maxLen)
		edit.SetNumberMode()
		edit.Show()
		self.widgets.append(edit)
		return bar, edit

	def __Build(self):
		# the five item slots - the tabs
		slotsWidth = TABS * 32 + (TABS - 1) * self.SLOT_GAP
		slotsX = (self.WIDTH - slotsWidth) / 2
		for i in xrange(TABS):
			x = slotsX + i * (32 + self.SLOT_GAP)
			self.slotMarks.append(self.__Bar(x - 3, self.SLOT_Y - 3, 38, 102, COLOR_SELECTED))
			for j in xrange(3):
				base = ui.ImageBox()
				base.SetParent(self)
				base.SetPosition(x, self.SLOT_Y + 32 * j)
				base.LoadImage(SLOT_BASE)
				base.AddFlag('not_pick')
				base.Show()
				self.widgets.append(base)
			label = self.__Label(x + 16, self.SLOT_Y + 100, "%d" % (i + 1), COLOR_DIM)
			label.SetHorizontalAlignCenter()
			self.slotLabels.append(label)
		# after the frames, so the icons draw over them
		slot = ui.SlotWindow()
		slot.SetParent(self)
		slot.SetPosition(slotsX, self.SLOT_Y)
		slot.SetSize(slotsWidth, 96)
		for i in xrange(TABS):
			slot.AppendSlot(i, i * (32 + self.SLOT_GAP), 0, 32, 96)
		slot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__SelectEmptySlot))
		slot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectItemSlot))
		slot.SetUnselectItemSlotEvent(ui.__mem_func__(self.__UnselectItemSlot))
		slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
		slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		slot.Show()
		self.slot = slot
		self.widgets.append(slot)

		# the heading and the mode, in the middle of the band above the rows
		bandTop = self.SLOT_Y + 100 + self.TEXT_H
		textY = bandTop + (self.ROWS_Y - bandTop - self.TEXT_H) / 2
		self.__Label(self.LEFT, textY, TEXT_PICK, COLOR_DIM)
		x = 236
		self.checkAll = CheckBox(ui.__mem_func__(self.OnClickModeAll))
		self.checkAll.SetParent(self)
		self.checkAll.SetPosition(x, textY)
		self.checkAll.Show()
		self.widgets.append(self.checkAll)
		self.__Label(x + 18, textY, TEXT_ALL)
		x += 82
		self.checkAtLeast = CheckBox(ui.__mem_func__(self.OnClickModeAtLeast))
		self.checkAtLeast.SetParent(self)
		self.checkAtLeast.SetPosition(x, textY)
		self.checkAtLeast.Show()
		self.widgets.append(self.checkAtLeast)
		self.__Label(x + 18, textY, TEXT_AT_LEAST)
		self.needBar, self.needEdit = self.__EditBox(x + 86, textY - 3, 26, 1)
		self.needOf = self.__Label(x + 116, textY, TEXT_OF)

		# the bonus rows, centred under the slots
		rowsWidth = 16 + self.PICK_WIDTH + 30 + self.EDIT_WIDTH
		rowsX = (self.WIDTH - rowsWidth) / 2
		self.rowsX = rowsX
		y = self.ROWS_Y
		for i in xrange(ROWS):
			number = self.__Label(rowsX, y + 6, "%d." % (i + 1), COLOR_DIM)
			pick = self.__Button(rowsX + 16, y, TEXT_NONE, 'xlarge', self.OpenPicker, i)
			sign = GreaterEqualSign()
			sign.SetParent(self)
			sign.SetPosition(rowsX + 16 + self.PICK_WIDTH + 8, y + 9)
			sign.Show()
			self.widgets.append(sign)
			bar, edit = self.__EditBox(rowsX + 16 + self.PICK_WIDTH + 30, y + 2, self.EDIT_WIDTH, 5)
			self.rows.append({'option': -1, 'button': pick, 'edit': edit, 'parts': (number, pick, sign, bar)})
			y += self.ROW_H

		# a costume has 1-3 bonuses: its last two rows give way to the number
		# of bonuses wanted (rolled by 70063)
		countY = self.ROWS_Y + COSTUME_ROWS * self.ROW_H + 4
		self.countParts = [self.__Label(rowsX, countY, TEXT_COUNT, COLOR_DIM)]
		self.countChecks = []
		x = rowsX
		for value, text in ((0, TEXT_COUNT_ANY), (1, "1"), (2, "2"), (3, "3")):
			check = CheckBox(ui.__mem_func__(self.OnClickCount), value)
			check.SetParent(self)
			check.SetPosition(x, countY + 22)
			self.widgets.append(check)
			label = self.__Label(x + 18, countY + 22, text)
			self.countChecks.append((value, check))
			self.countParts += [check, label]
			x += 18 + (60 if value == 0 else 22)

		y += 6
		self.speedLine = self.__Label(self.LEFT, y, "")
		self.slider = ui.SliderBar()
		self.slider.SetParent(self)
		self.slider.SetPosition(self.WIDTH - self.LEFT - self.SLIDER_W, y + 2)
		self.slider.SetEvent(ui.__mem_func__(self.OnChangeSpeed))
		self.slider.Show()
		self.widgets.append(self.slider)
		self.slider.SetSliderPos(float(self.speed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN))
		y += 22
		self.itemsLine = self.__Label(self.LEFT, y, "")
		y += 17
		self.statusLine = self.__Label(self.LEFT, y, "")
		y += 22
		self.onceButton = self.__Button((self.WIDTH - self.BUTTON_W) / 2, y, TEXT_ONCE, 'large', self.OnClickOnce)
		y += 32
		buttonsX = (self.WIDTH - 3 * self.BUTTON_W - 2 * 8) / 2
		self.startButton = self.__Button(buttonsX, y, TEXT_START, 'large', self.OnClickStart)
		self.stopButton = self.__Button(buttonsX + self.BUTTON_W + 8, y, TEXT_STOP, 'large', self.OnClickStop)
		self.clearButton = self.__Button(buttonsX + 2 * (self.BUTTON_W + 8), y, TEXT_CLEAR, 'large', self.OnClickClear)
		y += 32
		self.hintLine = self.__Label(self.LEFT, y, TEXT_HINT, COLOR_HINT)
		self.SetSize(self.WIDTH, y + 26)

		# the bonus list - one for every row, raised over them when shown
		self.pickerBackground = ui.SlotBar()
		self.pickerBackground.SetParent(self)
		self.pickerBackground.SetPosition(rowsX + 12, 32)
		self.pickerBackground.SetSize(self.PICK_WIDTH + 70, 1)
		self.pickerBackground.AddFlag('not_pick')
		self.pickerBackground.Hide()
		self.pickerList = SeparatedListBox()
		self.pickerList.SetParent(self.pickerBackground)
		self.pickerList.SetPosition(4, 3)
		self.pickerList.SetSize(self.PICK_WIDTH + 62, 1)
		self.pickerList.SetTextCenterAlign(False)
		self.pickerList.SetEvent(ui.__mem_func__(self.OnPickerSelect))
		self.pickerList.Hide()

		self.itemToolTip = uiToolTip.ItemToolTip()
		self.itemToolTip.HideToolTip()
		self.textToolTip = uiToolTip.ToolTip()
		self.textToolTip.HideToolTip()
		self.questionDialog = uiCommon.QuestionDialog2()
		self.questionDialog.Close()

		self.__RefreshSpeed()
		self.__LoadTab()

	def Destroy(self):
		self.Close()
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()
		if self.textToolTip:
			self.textToolTip.HideToolTip()
		self.itemToolTip = None
		self.textToolTip = None
		self.questionDialog = None
		self.rows = []
		self.slotMarks = []
		self.slotLabels = []
		self.widgets = []
		self.slot = None
		self.slider = None
		self.checkAll = None
		self.checkAtLeast = None
		self.countParts = []
		self.countChecks = []
		self.pickerList = None
		self.pickerBackground = None

	## tabs

	def __Tab(self):
		return self.tabs[self.current]

	def TabByPos(self, pos):
		for i, tab in enumerate(self.tabs):
			if tab.pos == pos and pos >= 0:
				return i
		return -1

	def __SaveTab(self):
		tab = self.__Tab()
		tab.rows = [(row['option'], row['edit'].GetText()) for row in self.rows]
		tab.need = self.needEdit.GetText()

	def __LoadTab(self):
		tab = self.__Tab()
		self.__ClosePicker()
		self.pickerList.ClearItem()
		# the list's first line empties a row; the bonuses are 1..n (option + 1)
		self.pickerList.InsertItem(0, TEXT_NONE)
		for index, (apply, top) in enumerate(tab.options):
			self.pickerList.InsertItem(index + 1, TEXT_MAX % ApplyText(apply, top))
		for i, row in enumerate(self.rows):
			option, text = tab.rows[i]
			if option < 0 or option >= len(tab.options):
				option = -1
			row['option'] = option
			row['button'].SetText(ApplyText(*tab.options[option]) if option >= 0 else TEXT_NONE)
			row['edit'].SetText(text)
		self.needEdit.SetText(tab.need)
		self.__RefreshMode()
		self.__RefreshCostume()
		self.__Refresh()

	# A costume tab: three rows, then the number of bonuses; its own items
	# and hint. Any other tab: the five rows.
	def __RefreshCostume(self):
		tab = self.__Tab()
		for i, row in enumerate(self.rows):
			for part in row['parts']:
				if tab.costume and i >= COSTUME_ROWS:
					part.Hide()
				else:
					part.Show()
		for part in self.countParts:
			if tab.costume:
				part.Show()
			else:
				part.Hide()
		for value, check in self.countChecks:
			check.SetChecked(value == tab.count)
		if tab.costume:
			self.hintLine.SetText(TEXT_COSTUME_HINT % (ItemName(COSTUME_RESET_VNUM, "70063"), ItemName(COSTUME_CHANGE_VNUM, "70064")))
		else:
			self.hintLine.SetText(TEXT_HINT)

	def OnClickCount(self, value):
		tab = self.__Tab()
		if tab.running:
			return
		tab.count = value
		self.__RefreshCostume()

	def SelectTab(self, index):
		if index == self.current or index < 0 or index >= TABS:
			return
		self.__SaveTab()
		self.current = index
		self.__LoadTab()
		self.__AskInfo(self.__Tab())

	def __AskInfo(self, tab):
		if tab.pos >= 0:
			Send("info %d" % tab.pos)

	def __PutItem(self, index, pos):
		"""An inventory item into a tab; True when it was taken."""
		vnum = player.GetItemIndex(pos)
		if not IsSwitchable(vnum):
			AppendChat(MESSAGES[3])
			return False
		other = self.TabByPos(pos)
		if other >= 0:
			self.SelectTab(other)	# already in a tab: that tab
			return True
		tab = self.tabs[index]
		if tab.running:
			AppendChat(TEXT_TAB_BUSY)
			return True
		self.SelectTab(index)
		tab.Clear()
		tab.pos = pos
		tab.vnum = vnum
		tab.costume = IsCostume(vnum)
		self.__LoadTab()
		Send("info %d" % pos)
		return True

	def TakeInventoryItem(self, pos):
		"""The inventory's right click while the window is open."""
		if not IsSwitchable(player.GetItemIndex(pos)):
			return False
		self.__PutItem(self.current, pos)
		return True

	def __RemoveItem(self, index):
		tab = self.tabs[index]
		if tab.running:
			AppendChat(TEXT_TAB_BUSY)
			return
		tab.Clear()
		if index == self.current:
			self.__LoadTab()
		else:
			self.__RefreshSlots()

	## the slots

	def __SelectEmptySlot(self, slotIndex):
		if not mouseModule.mouseController.isAttached():
			self.SelectTab(slotIndex)
			return
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedPos = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		if player.SLOT_TYPE_INVENTORY != attachedType:
			return
		self.__PutItem(slotIndex, attachedPos)

	def __SelectItemSlot(self, slotIndex):
		if mouseModule.mouseController.isAttached():
			self.__SelectEmptySlot(slotIndex)	# another item dropped on it
			return
		self.SelectTab(slotIndex)

	def __UnselectItemSlot(self, slotIndex):
		self.__OverOutItem()
		self.__RemoveItem(slotIndex)

	def __OverInItem(self, slotIndex):
		tab = self.tabs[slotIndex]
		if tab.pos >= 0 and self.itemToolTip:
			self.itemToolTip.SetInventoryItem(tab.pos)

	def __OverOutItem(self):
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()

	## the server

	def SetOptions(self, pos, vnum, options):
		index = self.TabByPos(pos)
		if index < 0 or self.tabs[index].vnum != vnum:
			return
		tab = self.tabs[index]
		if index == self.current:
			self.__SaveTab()
		# the table may have changed (the server reads it live): the rows keep
		# their bonus, wherever it now is in the list, and show its new max
		applies = [tab.options[o][0] if 0 <= o < len(tab.options) else None for o, text in tab.rows]
		where = dict((apply, i) for i, (apply, top) in enumerate(options))
		tab.rows = [(where.get(apply, -1) if apply is not None else -1, text) for apply, (o, text) in zip(applies, tab.rows)]
		tab.options = options
		if index == self.current:
			reopen = self.activeRow
			self.__LoadTab()
			if reopen >= 0:
				self.OpenPicker(reopen, False)

	def SetItems(self, priority, other, reset=0, change=0):
		self.countPriority = priority
		self.countOther = other
		self.countReset = reset
		self.countChange = change
		self.__RefreshItems()

	def SetRunning(self, pos, running):
		index = self.TabByPos(pos)
		if index < 0:
			return
		tab = self.tabs[index]
		if running and not tab.running:
			tab.changes = 0
		tab.running = running
		self.__RefreshSlots()
		self.__RefreshStatus()

	def SetProgress(self, pos, changes):
		index = self.TabByPos(pos)
		if index >= 0:
			self.tabs[index].changes = changes
		self.__RefreshStatus()

	def OnDone(self, pos, reason, changes):
		index = self.TabByPos(pos)
		if index >= 0:
			self.tabs[index].changes = changes
			self.tabs[index].running = False
		text = DONE.get(reason)
		if text:
			AppendChat(text % ((index + 1) if index >= 0 else 0, changes))
		self.__RefreshSlots()
		self.__RefreshStatus()

	def MaxOf(self, apply):
		for tab in self.tabs:
			for a, top in tab.options:
				if a == apply:
					return top
		return 0

	## the rows

	def OpenPicker(self, rowIndex, ask=True):
		tab = self.__Tab()
		if tab.running or not tab.options:
			return
		if ask:
			self.__AskInfo(tab)	# the newest maximums; the list refreshes when they come
		self.activeRow = rowIndex
		height = (len(tab.options) + 1) * self.LINE_H + 6
		self.pickerList.SetSize(self.PICK_WIDTH + 62, height - 6)
		self.pickerList.LocateItem()
		self.pickerBackground.SetSize(self.PICK_WIDTH + 70, height)
		top = self.ROWS_Y + rowIndex * self.ROW_H + self.PICK_HEIGHT
		self.pickerBackground.SetPosition(self.rowsX + 12, max(32, min(top, self.GetHeight() - height - 8)))
		self.pickerBackground.Show()
		self.pickerList.Show()
		self.pickerBackground.SetTop()
		self.pickerList.SetTop()

	def __ClosePicker(self):
		if self.pickerList:
			self.pickerList.Hide()
			self.pickerList.ClearSelection()
		if self.pickerBackground:
			self.pickerBackground.Hide()
		self.activeRow = -1

	def OnPickerSelect(self, lineIndex, name):
		rowIndex = self.activeRow
		self.__ClosePicker()
		options = self.__Tab().options
		if rowIndex < 0:
			return
		if lineIndex == 0:
			# "- brak -": the row is emptied, its value too
			row = self.rows[rowIndex]
			row['option'] = -1
			row['button'].SetText(TEXT_NONE)
			row['edit'].SetText("")
			self.__SaveTab()
			return
		optionIndex = lineIndex - 1
		if optionIndex < 0 or optionIndex >= len(options):
			return
		# one bonus in one row only
		for i, row in enumerate(self.rows):
			if i != rowIndex and row['option'] == optionIndex:
				row['option'] = -1
				row['button'].SetText(TEXT_NONE)
		row = self.rows[rowIndex]
		row['option'] = optionIndex
		apply, top = options[optionIndex]
		row['button'].SetText(ApplyText(apply, top))
		if not row['edit'].GetText():
			row['edit'].SetText(str(top))
		self.__SaveTab()

	def OnClickClear(self):
		if self.__Tab().running:
			return
		self.__ClosePicker()
		for row in self.rows:
			row['option'] = -1
			row['button'].SetText(TEXT_NONE)
			row['edit'].SetText("")
		self.__SaveTab()

	def __Targets(self):
		"""[(apply, min, max)] of the rows with a bonus; a row's empty value is 1."""
		tab = self.__Tab()
		options = tab.options
		targets = []
		for i, row in enumerate(self.rows):
			if tab.costume and i >= COSTUME_ROWS:
				break	# hidden for a costume
			if row['option'] < 0 or row['option'] >= len(options):
				continue
			apply, top = options[row['option']]
			targets.append((apply, max(1, ToInt(row['edit'].GetText(), 1)), top))
		return targets

	## the mode

	def OnClickModeAll(self):
		self.__Tab().mode = MODE_ALL
		self.__RefreshMode()

	def OnClickModeAtLeast(self):
		self.__Tab().mode = MODE_AT_LEAST
		self.__RefreshMode()
		self.needEdit.SetFocus()

	def __RefreshMode(self):
		atLeast = self.__Tab().mode == MODE_AT_LEAST
		self.checkAll.SetChecked(not atLeast)
		self.checkAtLeast.SetChecked(atLeast)
		if atLeast:
			self.needBar.Show()
			self.needOf.Show()
		else:
			self.needEdit.KillFocus()
			self.needBar.Hide()
			self.needOf.Hide()

	## speed

	def OnChangeSpeed(self):
		pos = self.slider.GetSliderPos()
		self.speed = max(SPEED_MIN, min(SPEED_MAX, int(round(SPEED_MIN + pos * (SPEED_MAX - SPEED_MIN)))))
		self.__RefreshSpeed()

	def __RefreshSpeed(self):
		self.speedLine.SetText(TEXT_SPEED % self.speed)

	## start / stop / once

	def OnClickStart(self):
		self.__ClosePicker()
		self.__SaveTab()
		tab = self.__Tab()
		if tab.running:
			return
		if tab.pos < 0:
			AppendChat(TEXT_DROP)
			return
		targets = self.__Targets()
		count = tab.count if tab.costume else 0
		if not targets and not count:
			AppendChat(TEXT_COSTUME_EMPTY if tab.costume else MESSAGES[6])
			return
		for apply, value, top in targets:
			if value > top:
				AppendChat(MESSAGES[9] % (TEXT_MAX % ApplyText(apply, top)))
				return
		need = 0
		if tab.mode == MODE_AT_LEAST and targets:
			need = ToInt(tab.need, 0)
			if need < 1 or need > len(targets):
				AppendChat(TEXT_NEED % len(targets))
				return
		SaveSpeed(self.speed)
		parts = ["%d:%d" % (apply, value) for apply, value, top in targets]
		Send(("start %d %d %d %d %s" % (tab.pos, self.speed, need, count, " ".join(parts))).strip())

	def OnClickStop(self):
		tab = self.__Tab()
		if tab.pos >= 0:
			Send("stop %d" % tab.pos)

	def OnClickOnce(self):
		self.__ClosePicker()
		tab = self.__Tab()
		if tab.pos < 0:
			AppendChat(TEXT_DROP)
			return
		if tab.running:
			AppendChat(TEXT_TAB_BUSY)
			return
		self.questionDialog.SetText1(TEXT_ONCE_ASK)
		if tab.costume:
			self.questionDialog.SetText2(TEXT_COSTUME_ONCE % (ItemName(COSTUME_CHANGE_VNUM, "70064"), ItemName(COSTUME_RESET_VNUM, "70063")))
		else:
			self.questionDialog.SetText2(TEXT_ONCE_ASK2)
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__AcceptOnce))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__CancelDialog))
		self.questionDialog.Open()

	def __AcceptOnce(self):
		self.questionDialog.Close()
		tab = self.__Tab()
		if tab.pos >= 0 and not tab.running:
			Send("once %d" % tab.pos)

	def __CancelDialog(self):
		self.questionDialog.Close()

	## drawing

	def __Refresh(self):
		self.__RefreshSlots()
		self.__RefreshItems()
		self.__RefreshStatus()

	def __RefreshSlots(self):
		for i, tab in enumerate(self.tabs):
			if tab.pos >= 0 and tab.vnum:
				self.slot.SetItemSlot(i, tab.vnum, 0)
			else:
				self.slot.ClearSlot(i)
			mark = self.slotMarks[i]
			label = self.slotLabels[i]
			if tab.running:
				mark.SetColor(COLOR_RUNNING)
				label.SetPackedFontColor(COLOR_OK)
			elif i == self.current:
				mark.SetColor(COLOR_SELECTED)
				label.SetPackedFontColor(COLOR_HINT)
			else:
				label.SetPackedFontColor(COLOR_DIM)
			if tab.running or i == self.current:
				mark.Show()
			else:
				mark.Hide()
		self.slot.RefreshSlot()

	def __RefreshItems(self):
		if self.countPriority < 0:
			self.itemsLine.SetText("")
			return
		if self.__Tab().costume:
			self.itemsLine.SetText(TEXT_COSTUME_ITEMS % (ItemName(COSTUME_RESET_VNUM, "70063"), self.countReset,
				ItemName(COSTUME_CHANGE_VNUM, "70064"), self.countChange))
			self.itemsLine.SetPackedFontColor(COLOR_OK if self.countReset + self.countChange > 0 else COLOR_WARN)
			return
		self.itemsLine.SetText(TEXT_ITEMS % (self.countPriority, self.countOther))
		self.itemsLine.SetPackedFontColor(COLOR_OK if self.countPriority + self.countOther > 0 else COLOR_WARN)

	def __RefreshStatus(self):
		tab = self.__Tab()
		if tab.running:
			self.statusLine.SetText("%s  %s" % (TEXT_RUNNING, TEXT_CHANGES % tab.changes))
			self.statusLine.SetPackedFontColor(COLOR_HINT)
		elif tab.changes:
			self.statusLine.SetText(TEXT_CHANGES % tab.changes)
			self.statusLine.SetPackedFontColor(COLOR_ATTR)
		else:
			self.statusLine.SetText("")

	## every frame

	def OnUpdate(self):
		# an item moved, sold or used: its tab lets it go (and its run stops)
		for i, tab in enumerate(self.tabs):
			if tab.pos >= 0 and player.GetItemIndex(tab.pos) != tab.vnum:
				if tab.running:
					Send("stop %d" % tab.pos)
					tab.running = False
				tab.Clear()
				if i == self.current:
					self.__LoadTab()
				else:
					self.__RefreshSlots()

	def Open(self):
		self.Show()
		self.SetTop()
		self.__Refresh()
		Send("items")
		for tab in self.tabs:
			self.__AskInfo(tab)

	def Close(self):
		self.__ClosePicker()
		self.__OverOutItem()
		if self.questionDialog:
			self.questionDialog.Close()
		if self.rows:
			self.__SaveTab()
		self.Hide()

	def OnPressEscapeKey(self):
		if self.activeRow >= 0:
			self.__ClosePicker()
		else:
			self.Close()
		return True


def __ParseOptions(args):
	options = []
	for arg in args:
		if ':' not in arg:
			continue
		apply, top = arg.split(':', 1)
		apply, top = ToInt(apply), ToInt(top)
		if apply > 0 and top > 0:
			options.append((apply, top))
	return options


def OnCommand(*args):
	if not args:
		return
	sub, rest = args[0], args[1:]
	window = _state['window']
	try:
		if sub == 'attrs':
			if window is not None and len(rest) >= 2:
				window.SetOptions(ToInt(rest[0], -1), ToInt(rest[1]), __ParseOptions(rest[2:]))
		elif sub == 'items':
			if window is not None and len(rest) >= 2:
				window.SetItems(ToInt(rest[0]), ToInt(rest[1]),
					ToInt(rest[2]) if len(rest) > 2 else 0, ToInt(rest[3]) if len(rest) > 3 else 0)
		elif sub == 'state':
			if window is not None and len(rest) >= 2:
				window.SetRunning(ToInt(rest[0], -1), ToInt(rest[1]) == 1)
		elif sub == 'progress':
			if window is not None and len(rest) >= 2:
				window.SetProgress(ToInt(rest[0], -1), ToInt(rest[1]))
		elif sub == 'done':
			pos = ToInt(rest[0], -1) if rest else -1
			reason = ToInt(rest[1]) if len(rest) > 1 else 0
			changes = ToInt(rest[2]) if len(rest) > 2 else 0
			if window is not None:
				window.OnDone(pos, reason, changes)
			else:
				text = DONE.get(reason)
				if text:
					AppendChat(text % (0, changes))
		elif sub == 'changed':
			pass	# the item's own update shows the new bonuses
		elif sub == 'msg':
			msgId = ToInt(rest[0]) if rest else 0
			data = ToInt(rest[1]) if len(rest) > 1 else 0
			text = MESSAGES.get(msgId)
			if not text:
				return
			if msgId in (7, 13, 14, 15):
				text = text % data
			elif msgId == 9:
				top = window.MaxOf(data) if window is not None else 0
				text = text % (TEXT_MAX % ApplyText(data, top) if top else str(data))
			AppendChat(text)
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uibonusswitch.OnCommand %s: %s' % (str(args), str(sys.exc_info()[1])))


def IsOpen():
	window = _state['window']
	return window is not None and window.IsShow()


def TakeInventoryItem(pos):
	"""uiinventory's right click: with the window open a weapon or an armour
	goes into the selected tab instead of being put on. True when taken."""
	window = _state['window']
	if window is None or not window.IsShow():
		return False
	try:
		# the equipment's own slots come here too: those still take things off
		if pos >= getattr(player, 'EQUIPMENT_SLOT_START', 180) or player.IsEquipmentSlot(pos) or player.IsCostumeSlot(pos):
			return False
		return window.TakeInventoryItem(pos)
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uibonusswitch.TakeInventoryItem: %s' % str(sys.exc_info()[1]))
		return False


def ToggleWindow():
	window = _state['window']
	if window is None:
		import uiminigameutil
		window = uiminigameutil.SafeCreate(BonusSwitchWindow, TEXT_TITLE)
		if window is None:
			return
		_state['window'] = window
	if window.IsShow():
		window.Close()
	else:
		window.Open()


def DestroyWindow():
	window = _state['window']
	_state['window'] = None
	if window is not None:
		window.Destroy()
