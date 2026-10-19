# MT2009_PLUS_GUILD_DUTY_V1 - the guild leader's panel (the operator, 28
# September: "jesli jestes liderem gildii, mozesz zlecac gildyjne obowiazki
# ... niech to bedzie osobny panel lidera w gildii").
#
# Three pages: the yang collection for the guild's treasury (the bots pay it in
# over the hours the leader gives), the item mission (bots gather a building
# material into the guild's item bank, the leader takes it out; a cancelled
# mission gives the bank's pieces back to the bots) and the Demon Tower
# expedition. Opened from the guild window (the leader's button) or with
# "/gildia_obowiazki" in the chat. Fed by the server (playerbot_guildduty.h):
#   GDBegin <guild yang> <server time> <default hours> <default tower bots> <tower level>
#   GDCollect <id> <state> <target> <collected> <start> <end> <donors>
#   GDDonor <amount> <name hex>
#   GDMission <id> <state> <vnum> <target> <collected> <workers> <workers max> <min level>
#   GDWorker <level> <delivered> <name hex>
#   GDBank <vnum> <count>
#   GDTower <id> <state> <wanted> <members> <recruits> <floor> <created> <note hex>
#   GDEnd
#   GDUpdate                    - something changed; an open panel asks again
# States: 1 running, 2 done, 3 cancelled, 4 expired; the tower 1 waiting,
# 2 gathering, 3 the stone, 4 inside, 5 done, 6 called off, 7 failed.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import item
import net
import ui

WIDTH = 430
HEIGHT = 440
REFRESH_SECONDS = 5.0
MATERIALS = ((90011, 'Pie\xf1'), (90010, 'Kamie\xf1 W\xeaglowy'), (90012, 'Dykta'))
BUTTON = 'd:/ymir work/ui/public/large_button_0%d.sub'
SMALL = 'd:/ymir work/ui/public/middle_button_0%d.sub'

TOWER_STATES = {
	0: 'Brak wyprawy',
	1: 'Oczekuje na boty',
	2: 'Zbi\xf3rka na parterze wie\xbfy',
	3: 'Rozbijanie Metina Twardo\x9cci',
	4: 'W wie\xbfy',
	5: 'Zako\xf1czona',
	6: 'Odwo\xb3ana',
	7: 'Nieudana',
}

_data = {'window': None, 'pending': None, 'data': None}


def Money(n):
	text = str(abs(int(n)))
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return ('-' if n < 0 else '') + '.'.join(parts)


def ItemName(vnum):
	try:
		item.SelectItem(int(vnum))
		return item.GetItemName()
	except Exception:
		return str(vnum)


def Unhex(text):
	if not text or text == '-':
		return ''
	try:
		return ''.join([chr(int(text[i:i + 2], 16)) for i in xrange(0, len(text) - 1, 2)])
	except Exception:
		return ''


def Ints(args, n):
	values = []
	for a in args[:n]:
		try:
			values.append(int(a))
		except (ValueError, TypeError):
			values.append(0)
	while len(values) < n:
		values.append(0)
	return values


def Request(line=''):
	if line:
		net.SendChatPacket('/gildia_obowiazki ' + line)
	else:
		net.SendChatPacket('/gildia_obowiazki')


def OnBegin(*args):
	money, now, hours, tower, towerLevel = Ints(args, 5)
	_data['pending'] = {'money': money, 'now': now, 'hours': hours or 12, 'tower': tower or 8,
			'towerLevel': towerLevel or 55, 'at': app.GetTime(), 'collect': None, 'donors': [],
			'mission': None, 'workers': [], 'bank': [], 'towerRow': None}


def OnCollect(*args):
	p = _data['pending']
	if p is None:
		return
	v = Ints(args, 7)
	p['collect'] = {'id': v[0], 'state': v[1], 'target': v[2], 'collected': v[3], 'start': v[4], 'end': v[5],
			'donors': v[6], 'unpaid': Ints(args[7:], 1)[0] if len(args) > 7 else -1}


def OnDonor(amount='0', name='-', *rest):
	p = _data['pending']
	if p is not None:
		p['donors'].append((Ints([amount], 1)[0], Unhex(name)))


def OnMission(*args):
	p = _data['pending']
	if p is None:
		return
	v = Ints(args, 8)
	p['mission'] = {'id': v[0], 'state': v[1], 'vnum': v[2], 'target': v[3], 'collected': v[4], 'workers': v[5],
			'workersMax': v[6], 'minLevel': v[7]}


def OnWorker(level='0', delivered='0', name='-', *rest):
	p = _data['pending']
	if p is not None:
		v = Ints([level, delivered], 2)
		p['workers'].append((v[0], v[1], Unhex(name)))


def OnBank(vnum='0', count='0', *rest):
	p = _data['pending']
	if p is not None:
		v = Ints([vnum, count], 2)
		if v[0] and v[1] > 0:
			p['bank'].append((v[0], v[1]))


def OnTower(*args):
	p = _data['pending']
	if p is None:
		return
	v = Ints(args, 7)
	p['towerRow'] = {'id': v[0], 'state': v[1], 'wanted': v[2], 'members': v[3], 'recruits': v[4], 'floor': v[5],
			'created': v[6], 'note': Unhex(args[7] if len(args) > 7 else '-')}


def OnEnd(*rest):
	if _data['pending'] is None:
		return
	_data['data'] = _data['pending']
	_data['pending'] = None
	wnd = GetWindow()
	wnd.Refresh()
	# An answer to a closed panel is "/gildia_obowiazki" typed in the chat.
	if not wnd.IsShow():
		wnd.Show()
		wnd.SetTop()


def OnUpdate(*rest):
	wnd = _data['window']
	if wnd and wnd.IsShow():
		Request()


def TimeLeft(seconds):
	seconds = max(0, int(seconds))
	hours = seconds // 3600
	minutes = (seconds % 3600) // 60
	if hours:
		return '%d godz. %d min' % (hours, minutes)
	return '%d min' % minutes


class GuildDutyWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.page = 0
		self.material = MATERIALS[0][0]
		self.nextRequest = 0.0
		self.pages = []
		self.textLines = [] # retain labels; unreferenced UI objects disappear
		self.SetSize(WIDTH, HEIGHT)
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetTitleName('Obowi\xb9zki gildii - panel lidera')
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		self.tabs = []
		for i, name in enumerate(('Zrzutka yang', 'Przedmioty', 'Wie\xbfa Demon\xf3w')):
			self.tabs.append(self.__Button(self, 20 + i * 132, 36, name, lambda i=i: self.SelectPage(i), True))
		self.moneyLine = self.__Text(self, 20, 64)

		for i in range(3):
			page = ui.Window()
			page.SetParent(self)
			page.SetPosition(0, 84)
			page.SetSize(WIDTH, HEIGHT - 90)
			self.pages.append(page)
		self.__MakeCollectPage(self.pages[0])
		self.__MakeMissionPage(self.pages[1])
		self.__MakeTowerPage(self.pages[2])
		self.SelectPage(0)
		self.SetCenterPosition()
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	# ------------------------------------------------------------ widgets

	def __Text(self, parent, x, y, text=''):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		self.textLines.append(line)
		return line

	def __Button(self, parent, x, y, text, event, large=True):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		pattern = BUTTON if large else SMALL
		button.SetUpVisual(pattern % 1)
		button.SetOverVisual(pattern % 2)
		button.SetDownVisual(pattern % 3)
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		return button

	def __Edit(self, parent, x, y, width, maxLen, text=''):
		bar = ui.SlotBar()
		bar.SetParent(parent)
		bar.SetPosition(x, y)
		bar.SetSize(width, 18)
		bar.Show()
		edit = ui.EditLine()
		edit.SetParent(bar)
		edit.SetPosition(4, 2)
		edit.SetSize(width - 8, 16)
		edit.SetMax(maxLen)
		edit.SetNumberMode()
		edit.SetText(text)
		edit.Show()
		return bar, edit

	def __Gauge(self, parent, x, y, width):
		gauge = ui.Gauge()
		gauge.SetParent(parent)
		gauge.SetPosition(x, y)
		gauge.MakeGauge(width, 'red')
		gauge.SetPercentage(0, 1)
		gauge.Show()
		return gauge

	# ------------------------------------------------------------ the pages

	def __MakeCollectPage(self, page):
		self.cStatus = self.__Text(page, 20, 2)
		self.cAmount = self.__Text(page, 20, 20)
		self.cGauge = self.__Gauge(page, 20, 40, WIDTH - 40)
		self.cTime = self.__Text(page, 20, 54)
		self.cUnpaid = self.__Text(page, 20, 72)
		self.__Text(page, 20, 90, 'Najwi\xeaksze wp\xb3aty bot\xf3w:')
		self.cDonors = [self.__Text(page, 30, 108 + i * 16) for i in range(5)]
		self.cForm = ui.ThinBoard()
		self.cForm.SetParent(page)
		self.cForm.SetPosition(20, 190)
		self.cForm.SetSize(WIDTH - 40, 118)
		self.cForm.Show()
		title = self.__Text(self.cForm, 16, 12, 'Nowa zrzutka do skarbca gildii')
		title.SetPackedFontColor(0xffffcf75)
		self.__Text(self.cForm, 16, 36, 'Kwota Yang do zebrania:')
		self.__Text(self.cForm, 250, 36, 'Czas w godzinach:')
		self.cAmountBar, self.cAmountEdit = self.__Edit(self.cForm, 16, 54, 210, 10, '1000000')
		self.cHoursBar, self.cHoursEdit = self.__Edit(self.cForm, 250, 54, 100, 2, '12')
		self.cStart = self.__Button(self.cForm, 16, 84, 'Rozpocznij', ui.__mem_func__(self.__StartCollect))
		self.cCancel = self.__Button(self.cForm, 116, 84, 'Zako\xf1cz', ui.__mem_func__(self.__CancelCollect))
		self.__Text(page, 20, 318, 'Boty wp\xb3acaj\xb9 stopniowo przez wskazany czas.')
		self.__Text(page, 20, 334, 'Skarbiec op\xb3aca teren gildii i budynki.')

	def __MakeMissionPage(self, page):
		self.mStatus = self.__Text(page, 20, 2)
		self.mProgress = self.__Text(page, 20, 20)
		self.mGauge = self.__Gauge(page, 20, 40, WIDTH - 40)
		self.mWorkers = self.__Text(page, 20, 54)
		self.mWorkerLines = []
		for i in range(8):
			self.mWorkerLines.append(self.__Text(page, 30 + (i % 2) * 195, 72 + (i // 2) * 16))
		self.__Text(page, 20, 142, 'Zle\xe6 zbieranie:')
		self.mMaterialButtons = []
		for i, (vnum, name) in enumerate(MATERIALS):
			self.mMaterialButtons.append(self.__Button(page, 20 + i * 132, 160, name,
					lambda vnum=vnum: self.__SelectMaterial(vnum)))
		self.mHint = self.__Text(page, 20, 186)
		self.__Text(page, 20, 208, 'Ilo\x9c\xe6:')
		self.mCountBar, self.mCountEdit = self.__Edit(page, 70, 206, 50, 3, '50')
		self.mStart = self.__Button(page, 135, 204, 'Wy\x9clij boty', ui.__mem_func__(self.__StartMission))
		self.mCancel = self.__Button(page, 230, 204, 'Anuluj misj\xea', ui.__mem_func__(self.__CancelMission))
		self.__Text(page, 20, 236, 'Bank przedmiot\xf3w gildii:')
		self.__Text(page, 250, 236, 'Wyp\xb3a\xe6 sztuk:')
		self.mTakeBar, self.mTakeEdit = self.__Edit(page, 335, 234, 50, 3, '200')
		self.mBankLines = []
		for i in range(4):
			text = self.__Text(page, 30, 260 + i * 22)
			button = self.__Button(page, 300, 256 + i * 22, 'Wyp\xb3a\xe6', lambda i=i: self.__Withdraw(i), False)
			self.mBankLines.append((text, button))
		self.mBankEmpty = self.__Text(page, 30, 260, 'Bank jest pusty.')

	def __MakeTowerPage(self, page):
		self.tStatus = self.__Text(page, 20, 2)
		self.tMembers = self.__Text(page, 20, 20)
		self.tNote = self.__Text(page, 20, 38)
		lines = (
			'Wyprawa rusza na kanale 1. Boty z gildii od poziomu %(level)d zbieraj\xb9 si\xea',
			'przy Metinie Twardo\x9cci na parterze Wie\xbfy Demon\xf3w; brakuj\xb9ce miejsca',
			'zajmuj\xb9 wynaj\xeate boty z Twojego kr\xf3lestwa. Po kilku minutach zbi\xf3rki',
			'rozbijaj\xb9 kamie\xf1 i wchodz\xb9 do wie\xbfy.',
			'Sta\xf1 na parterze, zanim kamie\xf1 p\xeaknie - wejdziesz razem z nimi.',
			'Gdy inna gildia jest w wie\xbfy, wyprawa czeka na swoj\xb9 kolej.',
		)
		self.tInfo = [self.__Text(page, 20, 66 + i * 16) for i in range(len(lines))]
		self.tInfoText = lines
		self.__Text(page, 20, 188, 'Liczba bot\xf3w (3-16):')
		self.tCountBar, self.tCountEdit = self.__Edit(page, 150, 186, 40, 2, '8')
		self.tStart = self.__Button(page, 20, 216, 'Zorganizuj', ui.__mem_func__(self.__StartTower))
		self.tCancel = self.__Button(page, 115, 216, 'Odwo\xb3aj', ui.__mem_func__(self.__CancelTower))

	# ------------------------------------------------------------ actions

	def SelectPage(self, index):
		self.page = index
		for i, page in enumerate(self.pages):
			if i == index:
				page.Show()
			else:
				page.Hide()
		for i, tab in enumerate(self.tabs):
			if i == index:
				tab.Down()
			else:
				tab.SetUp()

	def __Number(self, edit, default=0):
		try:
			return int(edit.GetText())
		except (ValueError, TypeError):
			return default

	def __StartCollect(self):
		amount = self.__Number(self.cAmountEdit)
		hours = self.__Number(self.cHoursEdit, 12)
		Request('zrzutka %d %d' % (amount, hours))

	def __CancelCollect(self):
		Request('zrzutka_anuluj')

	def __SelectMaterial(self, vnum):
		self.material = vnum
		self.__RefreshMaterials()

	def __StartMission(self):
		Request('misja %d %d' % (self.material, self.__Number(self.mCountEdit)))

	def __CancelMission(self):
		Request('misja_anuluj')

	def __Withdraw(self, index):
		data = _data['data']
		if not data or index >= len(data['bank']):
			return
		vnum, count = data['bank'][index]
		take = self.__Number(self.mTakeEdit, count)
		if take <= 0:
			take = count
		Request('wyplac %d %d' % (vnum, min(take, count)))

	def __StartTower(self):
		Request('dt %d' % self.__Number(self.tCountEdit, 8))

	def __CancelTower(self):
		Request('dt_anuluj')

	# ------------------------------------------------------------ refresh

	def __RefreshMaterials(self):
		for i, (vnum, name) in enumerate(MATERIALS):
			if vnum == self.material:
				self.mMaterialButtons[i].Down()
			else:
				self.mMaterialButtons[i].SetUp()
		level = {90011: 60, 90010: 50, 90012: 57}.get(self.material, 0)
		where = {90011: 'G\xf3ra Sohan', 90010: 'Dolina Ork\xf3w / Ognista Ziemia', 90012: '\x8cwi\xb9tynia Hwang'}
		self.mHint.SetText('%s: boty od poziomu %d (%s).' % (ItemName(self.material), level,
				where.get(self.material, '-')))

	def Refresh(self):
		data = _data['data']
		if not data:
			return
		self.moneyLine.SetText('Skarbiec gildii: %s yang' % Money(data['money']))
		now = data['now'] + int(app.GetTime() - data['at'])
		self.__RefreshCollect(data, now)
		self.__RefreshMission(data)
		self.__RefreshTower(data)

	def __RefreshCollect(self, data, now):
		c = data['collect']
		running = c and c['state'] == 1
		if c and c['id']:
			unpaid = c.get('unpaid', -1)
			self.cUnpaid.SetText('Cz\xb3onkowie bez wp\xb3aty: %d' % unpaid if unpaid >= 0 else 'Licznik bez wp\xb3aty wymaga nowego serwera.')
		else:
			self.cUnpaid.SetText('')
		if not c or not c['id']:
			self.cStatus.SetText('Brak zrzutki. Rozpocznij now\xb9 poni\xbfej.')
			self.cAmount.SetText('')
			self.cGauge.SetPercentage(0, 1)
			self.cTime.SetText('')
		else:
			label = {1: '|cfff4f770Trwa zrzutka', 2: '|cff82ff7dZrzutka zako\xf1czona - zebrano ca\xb3\xb9 kwot\xea',
					3: '|cff9a9a9aZrzutka zako\xf1czona przez lidera', 4: '|cff9a9a9aCzas zrzutki min\xb9\xb3'}
			self.cStatus.SetText(label.get(c['state'], 'Zrzutka'))
			percent = 100.0 * c['collected'] / c['target'] if c['target'] > 0 else 0.0
			self.cAmount.SetText('Zebrano %s z %s yang (%.1f%%)' % (Money(c['collected']), Money(c['target']), percent))
			self.cGauge.SetPercentage(c['collected'], max(1, c['target']))
			if running:
				if now < c['end']:
					self.cTime.SetText('Do ko\xf1ca: %s   Wp\xb3acaj\xb9cych bot\xf3w: %d' % (TimeLeft(c['end'] - now), c['donors']))
				else:
					self.cTime.SetText('Czas min\xb9\xb3 - boty wyr\xf3wnuj\xb9 zaleg\xb3o\x9c\xe6.   Wp\xb3acaj\xb9cych bot\xf3w: %d' % c['donors'])
			else:
				self.cTime.SetText('Wp\xb3aca\xb3o bot\xf3w: %d' % c['donors'])
		donors = data['donors']
		for i, line in enumerate(self.cDonors):
			if i < len(donors):
				line.SetText('%d. %s - %s yang' % (i + 1, donors[i][1] or '?', Money(donors[i][0])))
			else:
				line.SetText('-' if i == 0 and not donors else '')
		if running:
			self.cStart.Hide()
			self.cCancel.Show()
		else:
			self.cStart.Show()
			self.cCancel.Hide()

	def __RefreshMission(self, data):
		m = data['mission']
		running = m and m['state'] == 1
		if not m or not m['id']:
			self.mStatus.SetText('Brak misji. Zle\xe6 zbieranie poni\xbfej.')
			self.mProgress.SetText('')
			self.mGauge.SetPercentage(0, 1)
			self.mWorkers.SetText('')
		else:
			label = {1: '|cfff4f770Trwa misja', 2: '|cff82ff7dMisja wykonana', 3: '|cff9a9a9aMisja anulowana'}
			self.mStatus.SetText('%s: %d x %s' % (label.get(m['state'], 'Misja'), m['target'], ItemName(m['vnum'])))
			self.mProgress.SetText('Zebrano: %d / %d' % (m['collected'], m['target']))
			self.mGauge.SetPercentage(m['collected'], max(1, m['target']))
			if running:
				self.mWorkers.SetText('Boty w misji: %d / %d (od poziomu %d)' % (m['workers'], m['workersMax'], m['minLevel']))
			else:
				self.mWorkers.SetText('')
		workers = data['workers'] if running else []
		for i, line in enumerate(self.mWorkerLines):
			if i < len(workers):
				level, delivered, name = workers[i]
				line.SetText('%s (%d) - %d szt.' % (name or '?', level, delivered))
			else:
				line.SetText('')
		if running:
			self.mStart.Hide()
			self.mCancel.Show()
			for button in self.mMaterialButtons:
				button.Disable()
		else:
			self.mStart.Show()
			self.mCancel.Hide()
			for button in self.mMaterialButtons:
				button.Enable()
		self.__RefreshMaterials()
		bank = data['bank']
		for i, (text, button) in enumerate(self.mBankLines):
			if i < len(bank):
				text.SetText('%s x %d' % (ItemName(bank[i][0]), bank[i][1]))
				text.Show()
				button.Show()
			else:
				text.Hide()
				button.Hide()
		if bank:
			self.mBankEmpty.Hide()
		else:
			self.mBankEmpty.Show()

	def __RefreshTower(self, data):
		t = data['towerRow']
		level = data.get('towerLevel', 55)
		for i, line in enumerate(self.tInfo):
			text = self.tInfoText[i]
			line.SetText(text % {'level': level} if '%(level)d' in text else text)
		if not t or not t['id']:
			self.tStatus.SetText('Status: ' + TOWER_STATES[0])
			self.tMembers.SetText('')
			self.tNote.SetText('')
			running = False
		else:
			state = t['state']
			text = TOWER_STATES.get(state, '?')
			if state in (4, 5) and t['floor'] > 0:
				text += ' - pi\xeatro %d' % t['floor']
			color = '|cfff4f770' if state in (1, 2, 3, 4) else ('|cff82ff7d' if state == 5 else '|cff9a9a9a')
			self.tStatus.SetText('Status: ' + color + text)
			if t['members']:
				self.tMembers.SetText('Bot\xf3w: %d (z gildii %d, wynaj\xeatych %d), chciano %d' % (
						t['members'], t['members'] - t['recruits'], t['recruits'], t['wanted']))
			else:
				self.tMembers.SetText('Chciano bot\xf3w: %d' % t['wanted'])
			self.tNote.SetText(t['note'] and ('|cff9a9a9a' + t['note']) or '')
			running = state in (1, 2, 3, 4)
		if running:
			self.tStart.Hide()
			if t['state'] == 4:
				self.tCancel.Hide()
			else:
				self.tCancel.Show()
		else:
			self.tStart.Show()
			self.tCancel.Hide()

	# ------------------------------------------------------------ window

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()
		Request()
		self.nextRequest = app.GetTime() + REFRESH_SECONDS

	def OnUpdate(self):
		if app.GetTime() >= self.nextRequest:
			self.nextRequest = app.GetTime() + REFRESH_SECONDS
			Request()

	def Close(self):
		for edit in (self.cAmountEdit, self.cHoursEdit, self.mCountEdit, self.mTakeEdit, self.tCountEdit):
			edit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


def GetWindow():
	if not _data['window']:
		_data['window'] = GuildDutyWindow()
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
	_data['window'] = None
	_data['data'] = None
	_data['pending'] = None
