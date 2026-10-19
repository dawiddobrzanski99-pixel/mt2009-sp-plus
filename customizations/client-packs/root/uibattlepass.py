# Battle Pass - the window and the task bar's button (the operator, 28
# September): the Battle Pass window the operator chose, its layout and
# graphics as they were (uiscript/mt2009battlepass.py, mt2009_ui/battle_pass),
# fed by our server (playerbot_battlepass.h, "/battlepass"):
#   BPBegin <season YYYYMM> <days left> <final vnum> <final count> <final claimed> <missions>
#           [<final vnum 2> <count 2> <final vnum 3> <count 3>]
#   BPMission <id> <type> <target> <count> <progress> <claimed>
#             <vnum1> <count1> <vnum2> <count2> <vnum3> <count3> <name hex or ->
#             [<target level> <required mission> <locked>]
#     target level - only monsters/Metins of this level count (0 = any)
#     required mission, locked - the mission unlocks when that one is done
#   BPDesc <id> <description hex>          - "//" breaks a line
#   BPEnd <all done>
#   BPUpdate                               - something changed; the open window asks again
# A mission's rewards are given the moment it is done; the button below the
# summary takes the season's final reward ("/battlepass nagroda").
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import item
import net
import nonplayer
import ui
import uiToolTip
import wndMgr

IMG = 'mt2009_ui/battle_pass/'
ROWS = 6
REFRESH_SECONDS = 3.0

MONTHS = ('Stycze\xf1', 'Luty', 'Marzec', 'Kwiecie\xf1', 'Maj', 'Czerwiec', 'Lipiec',
		'Sierpie\xf1', 'Wrzesie\xf1', 'Pa\x9fdziernik', 'Listopad', 'Grudzie\xf1')

# For every mission type: its name, its icon, the text without a target and with one.
TYPES = {
	1: ('Zabij potwory', 'monster_icon.tga', 'Zabij %(n)s potwor\xf3w', 'Zabij %(n)s x %(what)s'),
	2: ('Zniszcz kamienie Metin', 'monster_damage.tga', 'Zniszcz %(n)s kamieni Metin', 'Zniszcz %(n)s x %(what)s'),
	3: ('Pokonaj boss\xf3w', 'deal_damage_category.tga', 'Pokonaj %(n)s boss\xf3w', 'Pokonaj %(n)s x %(what)s'),
	4: ('Z\xb3\xf3w ryby', 'catch_fish_category.tga', 'Z\xb3\xf3w %(n)s ryb', 'Z\xb3\xf3w %(n)s ryb'),
	5: ('Ulepszanie przedmiot\xf3w', 'craft_icon.tga', 'Ulepsz przedmiot %(n)s razy', 'Ulepsz przedmiot %(n)s razy'),
	6: ('Zbierz yang', 'spend_yang.tga', 'Zbierz %(n)s yang', 'Zbierz %(n)s yang'),
	7: ('Otw\xf3rz skrzynie', 'farm_item_category.tga', 'Otw\xf3rz %(n)s skrzy\xf1', 'Otw\xf3rz %(n)s skrzy\xf1'),
	8: ('Zbierz zio\xb3a', 'farm_item_category.tga', 'Zbierz %(n)s zi\xf3\xb3', 'Zbierz %(n)s zi\xf3\xb3'),
	9: ('Wydob\xb9d\x9f rud\xea', 'farm_item_category.tga', 'Wydob\xb9d\x9f %(n)s rudy', 'Wydob\xb9d\x9f %(n)s rudy'),
	10: ('Uko\xf1cz lochy', 'monster_damage.tga', 'Uko\xf1cz %(n)s loch\xf3w', 'Uko\xf1cz %(n)s loch\xf3w'),
	11: ('Ksi\xeagi Misji', 'design_info.tga', 'Wykonaj %(n)s Ksi\xb9g Misji', 'Wykonaj %(n)s Ksi\xb9g Misji'),
	12: ('Czas gry', 'open_battlepass.tga', 'Graj przez %(n)s min', 'Graj przez %(n)s min'),
	13: ('U\xbfyj przedmiotu', None, 'U\xbfyj %(n)s przedmiot\xf3w', 'U\xbfyj %(n)s x %(what)s'),
	14: ('Wo\xb3anie', 'design_info.tga', 'Napisz %(n)s razy na wo\xb3aj', 'Napisz %(n)s razy na wo\xb3aj'),
}

_data = {'begin': None, 'missions': [], 'pending': [], 'pending_begin': None, 'allDone': False, 'window': None}


def Money(n):
	text = str(n)
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return '.'.join(parts)


def ItemName(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except Exception:
		return str(vnum)


def MissionText(m):
	if m['name']:
		return m['name']
	info = TYPES.get(m['type'])
	if not info:
		return 'Misja %d' % m['id']
	n = Money(m['count']) if m['type'] == 6 else str(m['count'])
	level = m.get('level', 0)
	suffix = (' (poziom %d)' % level) if level and m['type'] in (1, 2, 3) else ''
	if not m['target']:
		return info[2] % {'n': n} + suffix
	if m['type'] in (1, 2, 3):
		try:
			what = nonplayer.GetMonsterName(m['target'])
		except Exception:
			what = str(m['target'])
	else:
		what = ItemName(m['target'])
	return info[3] % {'n': n, 'what': what} + suffix


def Request():
	net.SendChatPacket('/battlepass')


def OnBegin(season='0', days='0', finalVnum='0', finalCount='0', finalClaimed='0', count='0', *rest):
	try:
		_data['pending_begin'] = (int(season), int(days), int(finalVnum), int(finalCount), int(finalClaimed) != 0)
		finals = [(int(finalVnum), int(finalCount))]
		for k in range(2):
			if len(rest) >= k * 2 + 2:
				finals.append((int(rest[k * 2]), int(rest[k * 2 + 1])))
		_data['pending_finals'] = finals
	except ValueError:
		_data['pending_begin'] = None
	_data['pending'] = []


def OnMission(*args):
	try:
		values = [int(a) for a in args[:12]]
	except (ValueError, TypeError):
		return
	if len(values) < 12:
		return
	name = ''
	if len(args) > 12 and args[12] != '-':
		try:
			name = ''.join([chr(int(args[12][i:i + 2], 16)) for i in xrange(0, len(args[12]) - 1, 2)])
		except Exception:
			name = ''
	_data['pending'].append({'id': values[0], 'type': values[1], 'target': values[2], 'count': values[3],
			'progress': values[4], 'claimed': values[5] != 0,
			'rewards': [(values[6], values[7]), (values[8], values[9]), (values[10], values[11])],
			'name': name, 'desc': '', 'level': 0, 'requires': 0, 'locked': False})
	try:
		extra = [int(a) for a in args[13:16]]
	except (ValueError, TypeError):
		extra = []
	if len(extra) == 3:
		m = _data['pending'][-1]
		m['level'], m['requires'], m['locked'] = extra[0], extra[1], extra[2] != 0


def OnDesc(mid='0', text='', *rest):
	try:
		mid = int(mid)
		text = ''.join([chr(int(text[i:i + 2], 16)) for i in xrange(0, len(text) - 1, 2)])
	except Exception:
		return
	for m in _data['pending']:
		if m['id'] == mid:
			m['desc'] = text


def OnEnd(allDone='0', *rest):
	if not _data.get('pending_begin'):
		return
	_data['begin'] = _data['pending_begin']
	_data['finals'] = _data.get('pending_finals') or []
	_data['missions'] = _data['pending']
	_data['pending'] = []
	_data['allDone'] = allDone == '1'
	# The window asks only while it is open; an answer to a closed one is
	# "/battlepass" typed in the chat, which opens it.
	wnd = GetWindow()
	wnd.Refresh()
	if not wnd.IsShow():
		wnd.Show()
		wnd.SetTop()


def OnUpdate(*rest):
	wnd = _data['window']
	if wnd and wnd.IsShow():
		Request()


class BattlePassGauge(ui.Window):
	"""The window's own gauge (mt2009_ui/battle_pass/gauge)."""
	SLOT_WIDTH = 16
	SLOT_HEIGHT = 7
	GAUGE_TEMPORARY_PLACE = 12
	GAUGE_WIDTH = 16

	def __init__(self):
		ui.Window.__init__(self)
		self.width = 0

	def __del__(self):
		ui.Window.__del__(self)

	def MakeGauge(self, width):
		self.width = max(48, width)
		left = ui.ImageBox()
		left.SetParent(self)
		left.LoadImage(IMG + 'gauge/gauge_slot_left.tga')
		left.Show()
		right = ui.ImageBox()
		right.SetParent(self)
		right.LoadImage(IMG + 'gauge/gauge_slot_right.tga')
		right.SetPosition(width - self.SLOT_WIDTH, 0)
		right.Show()
		center = ui.ExpandedImageBox()
		center.SetParent(self)
		center.LoadImage(IMG + 'gauge/gauge_slot_center.tga')
		center.SetRenderingRect(0.0, 0.0, float((width - self.SLOT_WIDTH * 2) - self.SLOT_WIDTH) / self.SLOT_WIDTH, 0.0)
		center.SetPosition(self.SLOT_WIDTH, 0)
		center.Show()
		gauge = ui.ExpandedImageBox()
		gauge.SetParent(self)
		gauge.LoadImage(IMG + 'gauge/gauge_bpass.tga')
		gauge.SetRenderingRect(0.0, 0.0, 0.0, 0.0)
		gauge.SetPosition(self.GAUGE_TEMPORARY_PLACE, 0)
		gauge.Show()
		for img in (left, center, right):
			img.AddFlag('attach')
		self.parts = (left, right, center, gauge)
		self.imgGauge = gauge
		self.SetSize(width, self.SLOT_HEIGHT)

	def SetPercentage(self, curValue, maxValue):
		percentage = min(1.0, float(curValue) / float(maxValue)) if maxValue > 0 else 0.0
		size = -1.0 + float(self.width - self.GAUGE_TEMPORARY_PLACE * 2) * percentage / self.GAUGE_WIDTH
		self.imgGauge.SetRenderingRect(0.0, 0.0, size, 0.0)


class BattlePassScrollBar(ui.Window):
	"""The window's own scroll bar (mt2009_ui/battle_pass/scrollbar)."""
	SCROLLBAR_WIDTH = 13
	SCROLL_BTN_XDIST = 2
	SCROLL_BTN_YDIST = 2

	class MiddleBar(ui.DragButton):
		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag('movable')

		def MakeImage(self):
			parts = []
			for name, cls in (('scrollbar_middle_top.tga', ui.ImageBox), ('scrollbar_middle_topscale.tga', ui.ExpandedImageBox),
					('scrollbar_middle_bottom.tga', ui.ImageBox), ('scrollbar_middle_bottomscale.tga', ui.ExpandedImageBox),
					('scrollbar_middle_middle.tga', ui.ExpandedImageBox)):
				img = cls()
				img.SetParent(self)
				img.LoadImage(IMG + 'scrollbar/' + name)
				img.AddFlag('not_pick')
				img.Show()
				parts.append(img)
			self.top, self.topScale, self.bottom, self.bottomScale, self.middle = parts
			self.topScale.SetPosition(0, self.top.GetHeight())

		def SetSize(self, height):
			minHeight = self.top.GetHeight() + self.bottom.GetHeight() + self.middle.GetHeight()
			height = max(minHeight, height)
			ui.DragButton.SetSize(self, 10, height)
			scale = (height - minHeight) // 2
			extra = 1 if (height - minHeight) % 2 == 1 else 0
			self.topScale.SetRenderingRect(0, 0, 0, scale - 1)
			self.middle.SetPosition(0, self.top.GetHeight() + scale)
			self.bottomScale.SetPosition(0, self.top.GetHeight() + scale + self.middle.GetHeight())
			self.bottomScale.SetRenderingRect(0, 0, 0, scale - 1 + extra)
			self.bottom.SetPosition(0, height - self.bottom.GetHeight())

	def __init__(self):
		ui.Window.__init__(self)
		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = None
		top = ui.ImageBox()
		top.SetParent(self)
		top.AddFlag('not_pick')
		top.LoadImage(IMG + 'scrollbar/scrollbar_top.tga')
		top.Show()
		bottom = ui.ImageBox()
		bottom.SetParent(self)
		bottom.AddFlag('not_pick')
		bottom.LoadImage(IMG + 'scrollbar/scrollbar_bottom.tga')
		bottom.Show()
		middle = ui.ExpandedImageBox()
		middle.SetParent(self)
		middle.AddFlag('not_pick')
		middle.SetPosition(0, top.GetHeight())
		middle.LoadImage(IMG + 'scrollbar/scrollbar_middle.tga')
		middle.Show()
		self.topImage, self.bottomImage, self.middleImage = top, bottom, middle
		bar = self.MiddleBar()
		bar.SetParent(self)
		bar.SetMoveEvent(ui.__mem_func__(self.OnMove))
		bar.MakeImage()
		bar.SetSize(0)
		bar.Show()
		self.middleBar = bar

	def __del__(self):
		ui.Window.__del__(self)

	def SetScrollEvent(self, event):
		self.eventScroll = event

	def SetScrollBarSize(self, height):
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		scale = float((height - self.SCROLL_BTN_YDIST * 2) - self.middleImage.GetHeight()) / float(max(1, self.middleImage.GetHeight()))
		self.middleImage.SetRenderingRect(0, 0, 0, scale)
		self.bottomImage.SetPosition(0, height - self.bottomImage.GetHeight())
		self.middleBar.SetRestrictMovementArea(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST,
				self.middleBar.GetWidth(), height - self.SCROLL_BTN_YDIST * 2)
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST)
		self.pageSize = height - self.SCROLL_BTN_YDIST * 2 - self.middleBar.GetHeight()

	def SetMiddleBarSize(self, pageScale):
		self.middleBar.SetSize(int(pageScale * float(self.GetHeight() - self.SCROLL_BTN_YDIST * 2)))
		self.pageSize = self.GetHeight() - self.SCROLL_BTN_YDIST * 2 - self.middleBar.GetHeight()

	def GetPos(self):
		return self.curPos

	def SetPos(self, pos):
		pos = max(0.0, min(1.0, pos))
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, int(float(self.pageSize) * pos) + self.SCROLL_BTN_YDIST)
		self.OnMove()

	def OnMove(self):
		if self.pageSize <= 0:
			self.curPos = 0.0
		else:
			(x, y) = self.middleBar.GetLocalPosition()
			self.curPos = max(0.0, min(1.0, float(y - self.SCROLL_BTN_YDIST) / float(self.pageSize)))
		if self.eventScroll:
			self.eventScroll()

	def OnMouseLeftButtonDown(self):
		(x, y) = self.GetMouseLocalPosition()
		self.SetPos(float(y) / float(max(1, self.GetHeight())))


class BattlePassWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.rows = []
		self.first = 0
		self.selected = 0
		self.descLines = []
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/mt2009battlepass.py')
		self.board = self.GetChild('board')
		self.titleName = self.GetChild('TitleName')
		self.missionName = self.GetChild('BpassMissionName')
		self.missionType = self.GetChild('BpassMissionType')
		self.missionStatus = self.GetChild('BpassMissionStatus')
		self.missionProgress = self.GetChild('BpassMissionProgress')
		self.missionDescription = self.GetChild('BPassMissionDescription')
		self.finalButton = self.GetChild('FinalReward')
		self.GetChild('TitleBar').SetCloseEvent(ui.__mem_func__(self.Close))
		self.finalButton.SetEvent(ui.__mem_func__(self.__ClaimFinal))

		self.scrollBar = BattlePassScrollBar()
		self.scrollBar.SetParent(self.board)
		self.scrollBar.SetPosition(303, 33)
		self.scrollBar.SetScrollBarSize(253)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar.Show()

		for i in range(ROWS):
			self.rows.append(self.__MakeRow(i, 13, 33 + 41 * i))

		self.summaryGauge = BattlePassGauge()
		self.summaryGauge.SetParent(self.board)
		self.summaryGauge.MakeGauge(92)
		self.summaryGauge.SetPosition(326, 235)
		self.summaryGauge.Show()
		self.summaryText = ui.TextLine()
		self.summaryText.SetParent(self.board)
		self.summaryText.SetPosition(326, 216)
		self.summaryText.Show()

		self.finalSlot = ui.GridSlotWindow()
		self.finalSlot.SetParent(self.board)
		self.finalSlot.SetPosition(428, 218)
		self.finalSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
		self.finalSlot.ArrangeSlot(0, 3, 1, 32, 32, 0, 3)
		self.finalSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInFinal))
		self.finalSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
		self.finalSlot.RefreshSlot()
		self.finalSlot.Show()
		self.SetCenterPosition()

	def __MakeRow(self, index, x, y):
		tab = ui.Button()
		tab.SetParent(self.board)
		tab.SetPosition(x, y)
		tab.SetUpVisual(IMG + 'tab_normal.tga')
		tab.SetOverVisual(IMG + 'tab_select.tga')
		tab.SetDownVisual(IMG + 'tab_select.tga')
		tab.SetEvent(ui.__mem_func__(self.__Select), index)
		icon = ui.ImageBox()
		icon.SetParent(tab)
		icon.SetPosition(1, 2)
		icon.AddFlag('not_pick')
		name = ui.TextLine()
		name.SetParent(tab)
		name.SetPosition(50, 8)
		name.Show()
		gauge = BattlePassGauge()
		gauge.SetParent(tab)
		gauge.MakeGauge(130)
		gauge.SetPosition(41, 23)
		gauge.AddFlag('not_pick')
		gauge.Show()
		slots = []
		for k, sx in enumerate((187, 219, 252)):
			slot = ui.GridSlotWindow()
			slot.SetParent(tab)
			slot.SetPosition(sx, 6)
			slot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			slot.ArrangeSlot(0, 1, 1, 32, 32, 0, 3)
			slot.SetOverInItemEvent(lambda slotIndex, r=index, kk=k, w=self: w.OverInReward(slotIndex, r, kk))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOut))
			slot.RefreshSlot()
			slot.Show()
			slots.append(slot)
		return {'tab': tab, 'icon': icon, 'name': name, 'gauge': gauge, 'slots': slots}

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()
		Request()
		self.nextRequest = app.GetTime() + REFRESH_SECONDS

	# The progress, fresh while the window is open (the operator: "trzeba
	# wyjsc i wejsc do battlepassa, aby sie odswiezaly postepy").
	def OnUpdate(self):
		if app.GetTime() >= getattr(self, 'nextRequest', 0.0):
			self.nextRequest = app.GetTime() + REFRESH_SECONDS
			Request()

	def Close(self):
		self.tooltipItem.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __OnScroll(self):
		count = len(_data['missions'])
		self.first = int(round(self.scrollBar.GetPos() * max(0, count - ROWS)))
		self.__RefreshRows()

	def __Select(self, index):
		mission = self.first + index
		if mission < len(_data['missions']):
			self.selected = mission
			self.__RefreshRows()
			self.__RefreshInfo()

	def __ClaimFinal(self):
		net.SendChatPacket('/battlepass nagroda')

	def __Mission(self, rowIndex):
		index = self.first + rowIndex
		return _data['missions'][index] if index < len(_data['missions']) else None

	def OverInReward(self, slotIndex, rowIndex, k):
		m = self.__Mission(rowIndex)
		if m and m['rewards'][k][0]:
			self.tooltipItem.SetItemToolTip(m['rewards'][k][0])

	def __OverInFinal(self, slotIndex):
		finals = _data.get('finals') or []
		if slotIndex < len(finals) and finals[slotIndex][0]:
			self.tooltipItem.SetItemToolTip(finals[slotIndex][0])

	def __OverOut(self):
		self.tooltipItem.HideToolTip()

	def Refresh(self):
		begin = _data['begin']
		missions = _data['missions']
		if begin:
			season, days = begin[0], begin[1]
			month = season % 100
			self.titleName.SetText('Battle Pass - %s %d (do ko\xf1ca %d dni)' % (
					MONTHS[month - 1] if 1 <= month <= 12 else str(month), season // 100, days))
			finals = _data.get('finals') or [(begin[2], begin[3])]
			for k in range(3):
				vnum, cnt = finals[k] if k < len(finals) else (0, 0)
				self.finalSlot.SetItemSlot(k, vnum, cnt if cnt > 1 else 0)
		else:
			self.titleName.SetText('Battle Pass')
			for k in range(3):
				self.finalSlot.SetItemSlot(k, 0, 0)
		self.finalSlot.RefreshSlot()
		count = len(missions)
		self.scrollBar.SetMiddleBarSize(float(ROWS) / float(count) if count > ROWS else 1.0)
		if count <= ROWS:
			self.first = 0
		self.first = min(self.first, max(0, count - ROWS))
		self.selected = min(self.selected, max(0, count - 1))
		done = len([m for m in missions if m['progress'] >= m['count']])
		self.summaryGauge.SetPercentage(done, max(1, count))
		self.summaryText.SetText('Uko\xf1czone: %d / %d' % (done, count))
		if begin and begin[4]:
			self.finalButton.Hide()
		elif _data['allDone']:
			self.finalButton.Show()
			self.finalButton.Enable()
		else:
			self.finalButton.Show()
			self.finalButton.Disable()
		self.__RefreshRows()
		self.__RefreshInfo()

	def __RefreshRows(self):
		missions = _data['missions']
		for i, row in enumerate(self.rows):
			index = self.first + i
			if index >= len(missions):
				row['tab'].Hide()
				continue
			m = missions[index]
			row['tab'].SetUpVisual(IMG + ('tab_select.tga' if index == self.selected else 'tab_normal.tga'))
			row['tab'].Show()
			info = TYPES.get(m['type'])
			if m['type'] == 13 and m['target']:
				item.SelectItem(m['target'])
				row['icon'].LoadImage(item.GetIconImageFileName())
			else:
				row['icon'].LoadImage(IMG + ((info and info[1]) or 'monster_icon.tga'))
			row['icon'].Show()
			row['name'].SetText(MissionText(m))
			if m['progress'] >= m['count']:
				row['name'].SetPackedFontColor(0xff82ff7d)
			elif m.get('locked'):
				row['name'].SetPackedFontColor(0xff8c8c8c)
			else:
				row['name'].SetPackedFontColor(0xffffffff)
			row['gauge'].SetPercentage(m['progress'], m['count'])
			for k, slot in enumerate(row['slots']):
				vnum, cnt = m['rewards'][k]
				slot.SetItemSlot(0, vnum, cnt if cnt > 1 else 0)
				slot.RefreshSlot()

	def __RefreshInfo(self):
		for line in self.descLines:
			line.Hide()
		self.descLines = []
		missions = _data['missions']
		if not missions:
			self.missionName.SetText('Nazwa: -')
			self.missionType.SetText('Typ: -')
			self.missionStatus.SetText('Status: -')
			self.missionProgress.SetText('Post\xeap: -')
			self.missionDescription.SetText('Opis: brak misji w tym sezonie.')
			return
		m = missions[self.selected]
		info = TYPES.get(m['type'])
		self.missionName.SetText('Nazwa: ' + MissionText(m))
		self.missionType.SetText('Typ: ' + (info[0] if info else str(m['type'])))
		required = None
		if m.get('locked'):
			for other in missions:
				if other['id'] == m['requires']:
					required = other
		if m['progress'] >= m['count']:
			self.missionStatus.SetText('Status: |cff82ff7dUko\xf1czona')
		elif m.get('locked'):
			self.missionStatus.SetText('Status: |cff9a9a9aZablokowana')
		else:
			self.missionStatus.SetText('Status: |cfff4f770W trakcie')
		self.missionProgress.SetText('Post\xeap: %s / %s' % (Money(m['progress']), Money(m['count'])))
		self.missionDescription.SetText('Opis:')
		text = m['desc'] or 'Brak opisu.'
		if required:
			text = '|cff9a9a9aNajpierw uko\xf1cz://' + MissionText(required) + '//' + text
		for i, part in enumerate(text.split('//')[:5]):
			line = ui.TextLine()
			line.SetParent(self.board)
			line.SetPosition(323, 146 + i * 15)
			line.SetText(part)
			line.Show()
			self.descLines.append(line)


def GetWindow():
	if not _data['window']:
		_data['window'] = BattlePassWindow()
	return _data['window']


def ToggleWindow():
	wnd = GetWindow()
	if wnd.IsShow():
		wnd.Close()
	else:
		wnd.Open()


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Hide()
		wnd.tooltipItem = None
	_data['window'] = None
