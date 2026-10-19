# Kolo Fortuny - dracaryS's "Wheel of Fortune" window (the operator, 28
# September), its layout and graphics as they were (mt2009_ui/wheel/), on
# our chat-command protocol instead of the mod's (no exe change). The server
# decides everything (playerbot_wheel.h, "/kolo"); this window only shows it:
#   WOF info <enabled> <ticket vnum> <tickets per spin> <tickets held>
#   WOF poolbegin <sum of weights> / WOF pool <vnum>|<count>|<rare>|<chance/10000>#... / WOF poolend
#   WOF items <spin id> <vnum>|<count>|<rare>#... (ten slots)
#   WOF spin <spin id> <slot 0-9>   - turn the wheel, then "/kolo odbierz <id>"
#   WOF gift <vnum> <count> <rare>  - the reward is in the inventory
#   WOF fail                        - the spin was refused
# F12 or uiwheel.ToggleWindow() opens it.
#
# MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion] - "spin N times" (the row 1, 2, 5, 10, 25, 50 under
# the status line). One turn of the wheel, N spins paid and N rewards given:
#   "/kolo krec <n>"                - n > 1 (one spin stays "/kolo krec")
#   WOF items / WOF spin <id> <slot> [<n>] - as before: the one turn shown
#   "/kolo odbierz <id>"            - the server gives all n rewards, and says
#   WOF giftsbegin <n> / WOF gifts <vnum>|<count>|<rare>#... / WOF giftsend
# (several "gifts" lines when one is too long). n plain "WOF gift" lines work
# too: the window gathers them. Either way one list of the rewards is shown.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import grp
import item
import net
import ui
import uiToolTip
import uiminigameutil

IMG = 'mt2009_ui/wheel/'
SLOTS = 10
SPIN_SECONDS = 6.0

TITLE = 'Ko\xb3o Fortuny'
TEXT_SKIP = 'Pomi\xf1 animacj\xea'
TEXT_TICKETS = 'Bilety: %d   |   Koszt obrotu: %d x %s'
TEXT_OFF = 'Ko\xb3o Fortuny jest teraz wy\xb3\xb9czone.'
TEXT_HINT = 'Kliknij \x9crodek ko\xb3a, aby zakr\xeaci\xe6.'
TEXT_REWARD_TITLE = 'Nagroda'
TEXT_REWARD = 'Otrzymujesz'
TEXT_REWARD_IN = 'Nagroda jest w ekwipunku.'
TEXT_JACKPOT = 'JACKPOT!'
TEXT_ODDS = 'Szanse na nagrody'
TEXT_ODDS_EMPTY = 'Brak nagr\xf3d.'
TEXT_SPECIAL = 'Nagroda specjalna'
TEXT_OK = 'OK'
TEXT_GOT = 'Ko\xb3o Fortuny: otrzymujesz %s.'
TEXT_REWARDS_TITLE = 'Nagrody (losowa\xf1: %d)'
TEXT_REWARDS_PAGE = 'Strona %d/%d'

WINDOW_WIDTH = 449
WINDOW_HEIGHT = 508	# 480 and the row of the spin counts
COUNT_BAR_Y = 474
GIFT_WAIT_SECONDS = 1.5	# plain "gift" lines: shown when no more come

GOLD = grp.GenerateColor(1.0, 0.7843, 0.0, 1.0)
LIGHT = grp.GenerateColor(0.9490, 0.9058, 0.7568, 1.0)

# Where the ten slots sit on the wheel (from the top, clockwise), and where
# the lit segment goes for each (x, y, rotation) - the mod's own numbers.
ITEM_POS = ((205, 65), (275, 90), (320, 160), (320, 235), (275, 290), (205, 320), (130, 295), (90, 235), (85, 160), (130, 90))
SINGLE_POS = ((164, 38, 0), (230, 63, 35), (270, 120, 70), (266, 188, 110), (226, 241, 142), (160, 262, 180), (98, 243, 215), (56, 189, 250), (53, 119, 285), (96, 61, 324))
SLOT_ANGLE = (0, 20, 58, 94, 126, 160, 196, 232, 268, 304, 341)

# MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]: the reward windows' texts in the Auction House's
# font (uiauctionhouse.FontName): the game's large font, bold ("b" after the
# size). It has to be set before the line's first text.
def BoldFontName():
	try:
		import gamefont
		return gamefont.GetCurrentFontLarge() + 'b'
	except Exception:
		return ''


def BoldTextLine(parent, x, y):
	line = ui.TextLine()
	line.SetParent(parent)
	font = BoldFontName()
	if font:
		try:
			line.SetFontName(font)
		except Exception:
			pass
	line.SetPosition(x, y)
	line.SetHorizontalAlignCenter()
	return line


_data = {'window': None, 'info': (1, 0, 1, 0), 'pool': [], 'poolIn': [], 'giftsIn': [], 'giftsSpins': 0}


# The ticket by name even before the client's item_proto knows it.
KNOWN_NAMES = {80030: 'Bilet Ko\xb3a Fortuny'}


def ItemName(vnum):
	if vnum in KNOWN_NAMES:
		return KNOWN_NAMES[vnum]
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except Exception:
		return str(vnum)


def ItemIcon(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetIconImageFileName()
	except Exception:
		return ''


def ParseItems(text):
	out = []
	for part in text.split('#'):
		fields = part.split('|')
		if len(fields) < 2:
			continue
		try:
			vnum = int(fields[0])
			count = int(fields[1])
			rare = len(fields) > 2 and int(fields[2]) != 0
			chance = int(fields[3]) if len(fields) > 3 else 0
		except ValueError:
			continue
		out.append((vnum, count, rare, chance))
	return out


def RotationToSlot(rotation):
	rotation = rotation % 360
	if rotation >= 341 or rotation <= 20:
		return 0
	for slot in xrange(9, 0, -1):
		if rotation >= SLOT_ANGLE[slot] + 1:
			return slot
	return 0


def SlotRotation(slot):
	if slot == 0:
		if app.GetRandom(0, 1) == 0:
			return 341 + app.GetRandom(4, 18)
		return app.GetRandom(4, 19)
	return SLOT_ANGLE[slot] + app.GetRandom(4, 28)


def GiftName(vnum, count):
	name = ItemName(vnum)
	if count > 1:
		name = '%dx %s' % (count, name)
	return name


def MergeGifts(gifts):
	"""The rewards of many spins as one list: an item once with its counts
	summed, the special ones first."""
	order = []
	total = {}
	for gift in gifts:
		(vnum, count, rare) = gift[:3]
		if vnum not in total:
			total[vnum] = [0, False]
			order.append(vnum)
		total[vnum][0] += max(1, count)
		total[vnum][1] = total[vnum][1] or bool(rare)
	out = [(vnum, total[vnum][0], total[vnum][1]) for vnum in order]
	out.sort(key=lambda e: (not e[2], -e[1]))
	return out


class RewardListWindow(ui.BoardWithTitleBar):
	"""The rewards of N spins: a page of lines, Prev / Next when there are more."""

	WIDTH = 280
	ROWS = 12
	ROW_STEP = 18	# the bold large font's line
	ROW_Y = 58

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.children = []
		self.rows = []
		self.entries = []
		self.page = 0
		self.pageText = None
		self.prevButton = None
		self.nextButton = None

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Button(self, image, text, event):
		button = ui.Button()
		button.SetParent(self)
		button.SetUpVisual('d:/ymir work/ui/public/%s_button_01.sub' % image)
		button.SetOverVisual('d:/ymir work/ui/public/%s_button_02.sub' % image)
		button.SetDownVisual('d:/ymir work/ui/public/%s_button_03.sub' % image)
		button.SetText(text)
		button.SetEvent(event)
		self.children.append(button)
		return button

	def Load(self, entries, spins):
		self.children = []
		self.rows = []
		self.entries = list(entries)
		self.page = 0
		bottom = self.ROW_Y + self.ROWS * self.ROW_STEP
		self.SetTitleName(TEXT_REWARDS_TITLE % spins)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetSize(self.WIDTH, bottom + 60)
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetCenterPosition()

		head = BoldTextLine(self, self.WIDTH / 2, 36)
		head.SetText(TEXT_REWARD_IN)
		head.SetPackedFontColor(LIGHT)
		head.Show()
		self.children.append(head)

		for i in xrange(self.ROWS):
			line = BoldTextLine(self, self.WIDTH / 2, self.ROW_Y + i * self.ROW_STEP)
			line.Hide()
			self.rows.append(line)

		page = BoldTextLine(self, self.WIDTH / 2, bottom + 4)
		page.SetPackedFontColor(LIGHT)
		self.pageText = page

		self.prevButton = self.__Button('small', '<', ui.__mem_func__(self.__Prev))
		self.prevButton.SetPosition(20, bottom + 26)
		self.nextButton = self.__Button('small', '>', ui.__mem_func__(self.__Next))
		self.nextButton.SetPosition(self.WIDTH - 20 - self.nextButton.GetWidth(), bottom + 26)
		ok = self.__Button('middle', TEXT_OK, ui.__mem_func__(self.Close))
		ok.SetPosition(self.WIDTH / 2 - ok.GetWidth() / 2, bottom + 26)
		ok.Show()

		self.__Refresh()
		self.Show()
		self.SetTop()

	def __Pages(self):
		return max(1, (len(self.entries) + self.ROWS - 1) // self.ROWS)

	def __Refresh(self):
		start = self.page * self.ROWS
		for i, line in enumerate(self.rows):
			if start + i < len(self.entries):
				(vnum, count, rare) = self.entries[start + i]
				line.SetText(GiftName(vnum, count))
				line.SetPackedFontColor(GOLD if rare else LIGHT)
				line.Show()
			else:
				line.Hide()
		pages = self.__Pages()
		if pages > 1:
			self.pageText.SetText(TEXT_REWARDS_PAGE % (self.page + 1, pages))
			self.pageText.Show()
			self.prevButton.Show()
			self.nextButton.Show()
		else:
			self.pageText.Hide()
			self.prevButton.Hide()
			self.nextButton.Hide()

	def __Prev(self):
		if self.page > 0:
			self.page -= 1
			self.__Refresh()

	def __Next(self):
		if self.page + 1 < self.__Pages():
			self.page += 1
			self.__Refresh()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class RewardWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.children = []

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Load(self, vnum, count, rare):
		self.children = []
		self.SetTitleName(TEXT_REWARD_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetSize(230, 198)
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetCenterPosition()
		name = ItemName(vnum)
		if count > 1:
			name = '%dx %s' % (count, name)
		lines = [TEXT_REWARD, name, TEXT_REWARD_IN]
		if rare:
			lines.insert(0, TEXT_JACKPOT)
		y = 36
		for i, text in enumerate(lines):
			line = BoldTextLine(self, 115, y)
			line.SetPackedFontColor(GOLD if (rare and i == 0) else LIGHT)
			line.SetText(text)
			line.Show()
			self.children.append(line)
			y += 18
		icon = ui.ImageBox()
		icon.SetParent(self)
		icon.LoadImage(ItemIcon(vnum))
		icon.SetPosition(115 - icon.GetWidth() / 2, y + 4)
		icon.Show()
		self.children.append(icon)
		if count > 1:
			number = ui.NumberLine()
			number.SetParent(icon)
			number.SetNumber(str(count))
			number.SetPosition(20, max(0, icon.GetHeight() - 12))
			number.Show()
			self.children.append(number)
		ok = ui.Button()
		ok.SetParent(self)
		ok.SetUpVisual('d:/ymir work/ui/public/middle_button_01.sub')
		ok.SetOverVisual('d:/ymir work/ui/public/middle_button_02.sub')
		ok.SetDownVisual('d:/ymir work/ui/public/middle_button_03.sub')
		ok.SetText(TEXT_OK)
		ok.SetEvent(ui.__mem_func__(self.Close))
		ok.SetPosition(115 - ok.GetWidth() / 2, 163)
		ok.Show()
		self.children.append(ok)
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class WheelSlot(ui.Window):
	"""One of the ten slots: an item icon (with its count), or while the
	wheel stands idle the pool's items in turn, fading."""

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = owner
		self.items = []
		self.index = 0
		self.alpha = 1.0
		self.fadingOut = False
		self.sleepUntil = 0.0
		img = ui.ImageBox()
		img.SetParent(self)
		img.SAFE_SetStringEvent('MOUSE_OVER_IN', self.__OverIn)
		img.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.__OverOut)
		self.img = img
		number = ui.NumberLine()
		number.SetParent(img)
		number.SetPosition(20, 20)
		self.number = number

	def __del__(self):
		ui.Window.__del__(self)

	def SetItems(self, items):
		self.items = list(items)
		self.index = 0
		self.alpha = 1.0
		self.fadingOut = False
		self.sleepUntil = app.GetTime() + app.GetRandom(0, 20) / 10.0
		self.__Show()

	def Current(self):
		if not self.items:
			return None
		return self.items[self.index % len(self.items)]

	def __Show(self):
		cur = self.Current()
		if not cur:
			self.img.Hide()
			return
		icon = ItemIcon(cur[0])
		if not icon:
			self.img.Hide()
			return
		self.img.LoadImage(icon)
		self.img.SetPosition(0, 0)
		self.img.SetAlpha(self.alpha)
		self.img.Show()
		if cur[1] > 1:
			self.number.SetNumber(str(cur[1]))
			self.number.Show()
		else:
			self.number.Hide()

	def __OverIn(self):
		cur = self.Current()
		if cur:
			self.owner.ShowItemToolTip(cur[0], cur[2])

	def __OverOut(self):
		self.owner.HideItemToolTip()

	def OnUpdate(self):
		if len(self.items) <= 1 or self.sleepUntil > app.GetTime():
			return
		if self.fadingOut:
			self.alpha -= 0.05
			if self.alpha <= 0.3:
				self.alpha = 0.3
				self.fadingOut = False
				self.index = (self.index + 1) % len(self.items)
				self.__Show()
		else:
			self.alpha += 0.05
			if self.alpha >= 1.0:
				self.alpha = 1.0
				self.fadingOut = True
				self.sleepUntil = app.GetTime() + 2.0
		self.img.SetAlpha(self.alpha)


class WheelWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.tooltipOdds = uiToolTip.ToolTip(300)
		self.tooltipOdds.HideToolTip()
		self.reward = None
		self.slots = []
		self.spinId = 0
		self.spinning = False
		self.waiting = False
		self.hasResult = False
		self.skipAnimation = False
		self.skipChosen = False	# the box as the player left it for one spin
		self.start = 0.0
		self.startRotation = 0.0
		self.target = 0.0
		self.rotation = 0.0
		# spin N times: the count chosen, asked for, being turned; the rewards
		# still to come after "/kolo odbierz"
		self.playCount = 1
		self.requestCount = 1
		self.spinCount = 1
		self.giftExpect = 0
		self.giftList = []
		self.giftTime = 0.0
		self.countBar = None
		self.__Build()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Build(self):
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.SetTitleName(TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetCenterPosition()

		board = ui.ImageBox()
		board.SetParent(self)
		board.LoadImage(IMG + 'wallpaper.tga')
		board.SetPosition(6, 30)
		board.Show()
		self.board = board

		info = ui.Button()
		info.SetParent(board)
		info.SetUpVisual(IMG + 'info_0.tga')
		info.SetOverVisual(IMG + 'info_1.tga')
		info.SetDownVisual(IMG + 'info_2.tga')
		info.SetPosition(402, 5)
		info.SAFE_SetStringEvent('MOUSE_OVER_IN', self.__ShowOdds)
		info.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.__HideOdds)
		info.SetEvent(ui.__mem_func__(self.__ShowOdds))
		info.Show()
		self.info = info

		fortune = ui.ImageBox()
		fortune.SetParent(board)
		fortune.AddFlag('not_pick')
		fortune.LoadImage(IMG + 'fortune.tga')
		fortune.SetPosition(28, 23)
		fortune.Show()
		self.fortune = fortune

		single = ui.ExpandedImageBox()
		single.SetParent(board)
		single.AddFlag('not_pick')
		single.LoadImage(IMG + 'single.tga')
		single.SetPosition(SINGLE_POS[0][0], SINGLE_POS[0][1])
		single.Show()
		self.single = single

		circle = ui.ExpandedImageBox()
		circle.SetParent(board)
		circle.AddFlag('not_pick')
		circle.LoadImage(IMG + 'circle.tga')
		circle.SetPosition(155, 136)
		circle.Show()
		self.circle = circle

		spin = ui.Button()
		spin.SetParent(board)
		spin.SetUpVisual(IMG + 'wheel_0.tga')
		spin.SetOverVisual(IMG + 'wheel_1.tga')
		spin.SetDownVisual(IMG + 'wheel_2.tga')
		spin.SetPosition(160, 155)
		spin.SetEvent(ui.__mem_func__(self.__OnSpin))
		spin.Show()
		self.spinButton = spin

		for i in xrange(SLOTS):
			slot = WheelSlot(self)
			slot.SetParent(board)
			slot.SetPosition(ITEM_POS[i][0], ITEM_POS[i][1])
			slot.SetSize(32, 32)
			slot.Show()
			self.slots.append(slot)

		# "Skip the animation": the guild window's check box.
		check = ui.ImageBox()
		check.SetParent(board)
		check.LoadImage('d:/ymir work/ui/public/Parameter_Slot_01.sub')
		check.SetPosition(10, 10)
		check.SetEvent(ui.__mem_func__(self.__ToggleSkip), 'mouse_click')
		check.Show()
		self.check = check
		mark = ui.ImageBox()
		mark.SetParent(check)
		mark.AddFlag('not_pick')
		mark.LoadImage('d:/ymir work/ui/public/check_image.sub')
		mark.SetWindowHorizontalAlignCenter()
		mark.SetWindowVerticalAlignCenter()
		mark.Hide()
		self.checkMark = mark
		skip = ui.TextLine()
		skip.SetParent(board)
		skip.SetPosition(10 + check.GetWidth() + 6, 12)
		skip.SetText(TEXT_SKIP)
		skip.SetOutline()
		skip.Show()
		self.skipText = skip

		status = ui.TextLine()
		status.SetParent(self)
		status.SetPosition(224, 452)
		status.SetHorizontalAlignCenter()
		status.SetPackedFontColor(LIGHT)
		status.Show()
		self.status = status

		# "spin N times": the row of counts under the status line.
		# MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]: no "Liczba gier:" label here - the
		# buttons alone, centred in the window.
		bar = uiminigameutil.PlayCountBar(self, 0, COUNT_BAR_Y, ui.__mem_func__(self.__OnPlayCount), label = None)
		bar.SetPosition((WINDOW_WIDTH - bar.GetWidth()) / 2, COUNT_BAR_Y)
		self.countBar = bar
		self.RefreshInfo()

	# ------------------------------------------------------------------ open

	def Open(self):
		self.waiting = False
		self.hasResult = False
		self.Show()
		self.SetTop()
		net.SendChatPacket('/kolo')

	def Close(self):
		self.__FinishSpin()
		self.__FlushGifts()
		self.HideItemToolTip()
		self.__HideOdds()
		self.Hide()

	def Destroy(self):
		self.HideItemToolTip()
		self.__HideOdds()
		if self.countBar:
			self.countBar.Destroy()
		self.countBar = None
		self.giftList = []
		if self.reward:
			self.reward.Hide()
		self.reward = None
		self.slots = []
		self.tooltipItem = None
		self.tooltipOdds = None
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# -------------------------------------------------------------- tooltips

	def ShowItemToolTip(self, vnum, rare):
		if not self.tooltipItem:
			return
		self.tooltipItem.SetItemToolTip(vnum)
		if rare:
			self.tooltipItem.AppendTextLine(TEXT_SPECIAL, GOLD)
		self.tooltipItem.ShowToolTip()

	def HideItemToolTip(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __ShowOdds(self):
		tip = self.tooltipOdds
		if not tip:
			return
		tip.ClearToolTip()
		tip.SetTitle(TEXT_ODDS)
		tip.AppendSpace(4)
		pool = sorted(_data['pool'], key=lambda p: -p[3])
		if not pool:
			tip.AppendTextLine(TEXT_ODDS_EMPTY)
		for vnum, count, rare, chance in pool[:40]:
			name = ItemName(vnum)
			if count > 1:
				name = '%dx %s' % (count, name)
			text = '%s - %d.%02d%%' % (name, chance / 100, chance % 100)
			tip.AppendTextLine(text, GOLD if rare else tip.FONT_COLOR)
		tip.ShowToolTip()

	def __HideOdds(self):
		if self.tooltipOdds:
			self.tooltipOdds.HideToolTip()

	# ----------------------------------------------------------------- state

	def __ToggleSkip(self, *args):
		self.__SetSkip(not self.skipAnimation)
		if self.playCount <= 1:
			self.skipChosen = self.skipAnimation

	def __SetSkip(self, skip):
		self.skipAnimation = bool(skip)
		if self.skipAnimation:
			self.checkMark.Show()
		else:
			self.checkMark.Hide()

	def RefreshInfo(self):
		enabled, vnum, count, have = _data['info']
		if not enabled:
			self.status.SetText(TEXT_OFF)
		elif vnum:
			self.status.SetText(TEXT_TICKETS % (have, count * self.playCount, ItemName(vnum)))
		else:
			self.status.SetText(TEXT_HINT)

	def RefreshPool(self):
		if self.spinning or self.waiting or self.hasResult:
			return
		pool = _data['pool']
		if not pool:
			for slot in self.slots:
				slot.SetItems([])
			return
		for i, slot in enumerate(self.slots):
			items = []
			for k in xrange(10):
				p = pool[app.GetRandom(0, len(pool) - 1)]
				items.append((p[0], p[1], p[2]))
			slot.SetItems(items)

	def __OnPlayCount(self, count):
		# MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]: more than one spin ticks "Pomin animacje"
		# (it can be unticked); back at one spin the box is as it was left there.
		if count > 1:
			self.__SetSkip(True)
		elif self.playCount > 1:
			self.__SetSkip(self.skipChosen)
		self.playCount = count
		self.RefreshInfo()

	def __OnSpin(self):
		if self.spinning or self.waiting:
			return
		self.waiting = True
		self.hasResult = False
		self.requestCount = self.playCount
		if self.requestCount > 1:
			net.SendChatPacket('/kolo krec %d' % self.requestCount)
		else:
			net.SendChatPacket('/kolo krec')

	def OnFail(self):
		self.waiting = False

	def OnItems(self, spinId, items):
		self.waiting = False
		self.hasResult = True
		for i, slot in enumerate(self.slots):
			if i < len(items):
				slot.SetItems([items[i][:3]])
			else:
				slot.SetItems([])

	def OnSpin(self, spinId, slot, count = 0):
		self.waiting = False
		self.spinId = spinId
		# the server's count when it says one, else what was asked for
		self.spinCount = count if count > 0 else self.requestCount
		self.requestCount = 1
		final = SlotRotation(max(0, min(SLOTS - 1, slot)))
		if self.skipAnimation or not self.IsShow():
			self.spinning = True
			self.target = final
			self.__FinishSpin()
			return
		base = self.rotation % 360
		self.rotation = base
		self.target = base + 360.0 * app.GetRandom(4, 6) + ((final - base) % 360)
		self.startRotation = base
		self.start = app.GetTime()
		self.spinning = True

	def __SetRotation(self, rotation):
		self.rotation = rotation
		self.circle.SetRotation(rotation % 360)
		slot = RotationToSlot(rotation)
		x, y, angle = SINGLE_POS[slot]
		self.single.SetRotation(angle)
		self.single.SetPosition(x, y)

	def __FinishSpin(self):
		if not self.spinning:
			return
		self.spinning = False
		self.__SetRotation(self.target % 360)
		if self.spinId:
			self.__FlushGifts()
			if self.spinCount > 1:
				self.giftExpect = self.spinCount
				self.giftTime = app.GetTime()
			net.SendChatPacket('/kolo odbierz %d' % self.spinId)
		self.spinId = 0
		self.spinCount = 1

	def OnUpdate(self):
		# plain "gift" lines of a spin of many: fewer than asked for came
		if self.giftList and app.GetTime() - self.giftTime > GIFT_WAIT_SECONDS:
			self.__FlushGifts()
		if not self.spinning:
			return
		t = (app.GetTime() - self.start) / SPIN_SECONDS
		if t >= 1.0:
			self.__FinishSpin()
			return
		ease = 1.0 - (1.0 - t) ** 3
		self.__SetRotation(self.startRotation + (self.target - self.startRotation) * ease)

	def __FlushGifts(self):
		gifts = self.giftList
		self.giftList = []
		self.giftExpect = 0
		if gifts:
			self.__ShowGifts(gifts, len(gifts))

	def __ShowGifts(self, gifts, spins):
		entries = MergeGifts(gifts)
		if not entries:
			return
		if not self.IsShow():
			for (vnum, count, rare) in entries:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_GOT % GiftName(vnum, count))
			return
		if self.reward:
			self.reward.Hide()
		self.reward = RewardListWindow()
		self.reward.Load(entries, max(1, spins))

	def OnGifts(self, gifts, spins):
		"""WOF giftsbegin / gifts / giftsend: all the rewards of a spin of many."""
		self.giftList = []
		self.giftExpect = 0
		self.__ShowGifts(gifts, spins or len(gifts))

	def OnGift(self, vnum, count, rare):
		# one of the rewards of a spin of many: gathered into one list
		if self.giftExpect > 1 and self.IsShow():
			self.giftList.append((vnum, count, rare))
			self.giftTime = app.GetTime()
			if len(self.giftList) >= self.giftExpect:
				self.__FlushGifts()
			return
		if not self.IsShow():
			chat.AppendChat(chat.CHAT_TYPE_INFO, TEXT_GOT % ((('%dx ' % count) if count > 1 else '') + ItemName(vnum)))
			return
		if self.reward:
			self.reward.Hide()
		self.reward = RewardWindow()
		self.reward.Load(vnum, count, rare)


def GetWindow():
	if not _data['window']:
		_data['window'] = WheelWindow()
	return _data['window']


def ToggleWindow():
	wnd = GetWindow()
	if wnd.IsShow():
		wnd.Close()
	else:
		wnd.Open()


def OpenWindow():
	wnd = GetWindow()
	if not wnd.IsShow():
		wnd.Open()


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Destroy()
	_data['window'] = None


def _Int(value, default=0):
	try:
		return int(value)
	except (ValueError, TypeError):
		return default


# game.py "WOF": the server's answers.
def OnCommand(sub='', *args):
	if sub == 'info':
		values = [_Int(a) for a in args[:4]]
		while len(values) < 4:
			values.append(0)
		_data['info'] = tuple(values)
		if _data['window']:
			_data['window'].RefreshInfo()
	elif sub == 'poolbegin':
		_data['poolIn'] = []
	elif sub == 'pool':
		if args:
			_data['poolIn'].extend(ParseItems(args[0]))
	elif sub == 'poolend':
		_data['pool'] = _data['poolIn']
		_data['poolIn'] = []
		if _data['window']:
			_data['window'].RefreshPool()
	elif sub == 'items':
		if len(args) >= 2:
			GetWindow().OnItems(_Int(args[0]), ParseItems(args[1]))
	elif sub == 'spin':
		if len(args) >= 2:
			GetWindow().OnSpin(_Int(args[0]), _Int(args[1]), _Int(args[2]) if len(args) > 2 else 0)
	elif sub == 'gift':
		if len(args) >= 2:
			GetWindow().OnGift(_Int(args[0]), max(1, _Int(args[1], 1)), len(args) > 2 and _Int(args[2]) != 0)
	elif sub == 'giftsbegin':
		_data['giftsIn'] = []
		_data['giftsSpins'] = _Int(args[0]) if args else 0
	elif sub == 'gifts':
		if args:
			_data['giftsIn'].extend(ParseItems(args[0]))
	elif sub == 'giftsend':
		gifts = _data['giftsIn']
		_data['giftsIn'] = []
		GetWindow().OnGifts(gifts, _data['giftsSpins'])
	elif sub == 'fail':
		if _data['window']:
			_data['window'].OnFail()
