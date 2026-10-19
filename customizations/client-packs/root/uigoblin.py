# Poszukiwanie skarbow - the Treasure Hunt event with the Treasure Goblin
# (MT2009_PLUS_GOBLIN_V1; the operator, 28 September: "event goblina ...
# Wszystkie GUI maja byc takie jak w plikach"). The "Official Treasure Hunt
# System" archive's windows - root/uitreasurehunt.py and
# uitreasurehuntdungeon.py with uiscript/treasurehunt*.py - on our
# chat-command protocol: no packet, no net.SendTreasureHunt*, nothing the exe
# lacks. Layout and graphics as the archive has them (uiscript/goblin*.py,
# mt2009_ui/goblin cut out of treasure_hunt_01.dds), the texts in Polish.
#
# The server (playerbot_goblin.h) sends one command, "GOB", with a
# sub-command (game.py passes it here):
#   GOB event <on> <end epoch>
#   GOB info <on> <doubloons> <rounds> <keys> <claims> <tier> <revealed> <can claim> <can take round> <claimed mask>
#   GOB slots <vnum>,<count>;...        GOB open
#   GOB got <slot> <vnum> <count> <keys>
#   GOB acc <round index> <can take>    GOB accr <round> <vnum>,<count>,<affect>,<limited>,<left>;...
#   GOB rank <place> <name> <rounds>    GOB rankme <place> <name> <rounds>    GOB rankend
#   GOB dun <in> <phase> <hp> <max hp> <blessings> <seconds left>
#   GOB msg <id> <data>
# and the windows answer with "/goblin <info|odkryj|szukaj|reset|tury|tura|ranking|wyjdz>".
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import app
import chat
import item
import net
import ui
import uiCommon
import uiToolTip
import wndMgr

IMG = 'mt2009_ui/goblin/'
EV = IMG + 'event/'

REWARD_LIST_COUNT = 25
GET_MAX_REWARD_COUNT = 9
NEED_GOLD_FOR_SET_REWARD = 90
GOLD_MAX = 999
ROUND_REWARD_SLOT_COUNT = 15
DISPLAY_MAX_ROUND = 10
MAX_ROUND_INDEX = DISPLAY_MAX_ROUND - 1
KEY_VNUM = 70618
KEY_BOX_VNUM = 70619
AFFECT_REFINE_PCT = 668
AFFECT_REFINE_FREE = 669
LOCKED_SLOT_DIFFUSE = (0.4, 0.4, 0.4, 1.0)
FLASH_PERIOD = 30

# The archive's SLOT_REWARD_TYPE_DATA and OPEN_SLOT_DATA_BY_REWARD_TYPE.
SLOT_REWARD_TYPE_DATA = {
	0: (0, 1, 2, 5, 6, 7, 10, 11, 12),
	1: (3, 8, 13, 15, 16, 17, 18),
	2: (20, 21, 22, 23, 24),
	3: (4, 9, 14, 19),
}
OPEN_SLOT_DATA_BY_REWARD_TYPE = {
	0: (0, 1, 2, 5, 6, 7, 10, 11, 12),
	1: (0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, 18),
	2: (0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, 18, 20, 21, 22, 23, 24),
	3: tuple(range(REWARD_LIST_COUNT)),
}

# Names for the event's own items while the client's item table lacks them.
OWN_ITEM_NAME = {
	70617: 'Bilet Skarb\xf3w',
	KEY_VNUM: 'Klucz Goblina',
	KEY_BOX_VNUM: 'Szkatu\xb3ka z Kluczami Goblina',
}
# Their icons are in the icon pack (icon/item) - the ticket's used to be a
# black box.
OWN_ITEM_ICON = {
	70617: 'icon/item/70617.tga',
	KEY_VNUM: 'icon/item/70618.tga',
	KEY_BOX_VNUM: 'icon/item/70619.tga',
}

TITLE = 'Poszukiwanie skarb\xf3w'
GOLD_ICON_TOOLTIP_TITLE = 'Doblony'
GOLD_ICON_TOOLTIP_1 = 'Zdobywasz je, chroni\xb9c Goblina Skarb\xf3w'
GOLD_ICON_TOOLTIP_1B = 'na Wyspie Skarb\xf3w (Bilety Skarb\xf3w ze skrzy\xf1).'
GOLD_ICON_TOOLTIP_2 = 'Najwi\xeacej Doblon\xf3w: %d'
SET_REWARD_BUTTON_TOOLTIP_1 = 'Zobacz nagrody'
SET_REWARD_BUTTON_TOOLTIP_2 = 'Zobacz nagrody za %d Doblon\xf3w.'
SET_REWARD_BUTTON_TOOLTIP_DONE = 'Nagrody s\xb9 ju\xbf odkryte.'
SET_REWARD_BUTTON_TOOLTIP_GOLD = 'Masz za ma\xb3o Doblon\xf3w (potrzeba %d).'
ACCUMULATE_COUNT_TOOLTIP = 'Aby uko\xf1czy\xe6 1 tur\xea, musisz zebra\xe6 9 nagr\xf3d.'
SHOW_ACCUMULATE_REWARD_BUTTON_TOOLTIP = 'Przejd\x9f do nagr\xf3d za tury'
REWARD_BUTTON_TOOLTIP_1 = 'Szukaj skarbu'
REWARD_BUTTON_TOOLTIP_2 = 'Nie mo\xbfesz szuka\xe6 skarbu, zanim nie zobaczysz nagr\xf3d.'
RESET_BUTTON_TOOLTIP = 'Resetuj'
RESET_BUTTON_TOOLTIP_COST = 'Nowa plansza nagr\xf3d za %d Doblon\xf3w.'
REWARD_BUTTON_TOOLTIP_FREE = 'Pierwsza nagroda tury jest darmowa.'
REWARD_BUTTON_TOOLTIP_KEY = 'Koszt: 1 Klucz Goblina.'
REWARD_BUTTON_TOOLTIP_FULL = 'Ta tura jest ju\xbf pe\xb3na - odbierz nagrod\xea za tur\xea.'
RANKING_BUTTON_TOOLTIP = 'Ranking tur'
REWARD_RESET_POPUP_1 = 'Czy chcesz zresetowa\xe6 nagrody?'
REWARD_RESET_POPUP_2 = 'Wszystkie nagrody zostan\xb9 zresetowane.'
GET_ACCUMULATED_REWARD_BUTTON_TOOLTIP = 'Aby zobaczy\xe6 nowe nagrody, odbierz nagrod\xea za tur\xea.'
ROUND_REWARD_TOOLTIP_TITLE = 'Odbierz nagrod\xea za tur\xea'
ROUND_REWARD_TOOLTIP_NOT_YET = 'Najpierw zbierz %d nagr\xf3d z planszy.'
ROUND_REWARD_TOOLTIP_OTHER = 'Odebra\xe6 mo\xbfesz tylko nagrod\xea za bie\xbf\xb9c\xb9 tur\xea (%d).'
UNKNOWN_ITEM = 'Przedmiot %d'
BUFF_TITLE = 'B\xb3ogos\xb3awie\xf1stwo ulepszania'
INCREASE_REFINE_PCT = 'Nast\xeapne ulepszenie ma o %d%% wi\xeaksz\xb9 szans\xea. (Raz na event)'
REFINE_FREE_MATERIAL = 'Nast\xeapne ulepszenie nie zu\xbfyje materia\xb3\xf3w. (Raz na event)'
REMAINING_LABEL = 'Pozosta\xb3o'
TIER_LOCKED = {
	1: 'Rzadkie: te nagrody odblokujesz po 3 turach.',
	2: 'Antyczne: te nagrody odblokujesz po 5 turach.',
	3: 'Legendarne: te nagrody odblokujesz po 10 turach.',
}
DESCRIPTION = (
	'Otrzymujesz jedn\xb9 z wymienionych nagr\xf3d.',
	'Aby uko\xf1czy\xe6 1 tur\xea, musisz zebra\xe6 9 nagr\xf3d.',
	'Za uko\xf1czone tury tak\xbfe otrzymujesz nagrody.',
	'Nowe nagrody wylosujesz dopiero po odebraniu co najmniej 1 nagrody.',
	'Na 6. i 9. turze mo\xbfesz otrzyma\xe6 ograniczone b\xb3ogos\xb3awie\xf1stwa.',
	'Ich liczba na event jest ograniczona.',
	'Ka\xbfda posta\xe6 mo\xbfe otrzyma\xe6 ka\xbfde b\xb3ogos\xb3awie\xf1stwo tylko raz na event.',
)
GIVE_UP_BUTTON = 'Wyjd\x9f'
GIVE_UP_POPUP = 'Czy chcesz przerwa\xe6 poszukiwanie skarb\xf3w?'
GOBLIN_NAME = 'Goblin Skarb\xf3w'
GOBLIN_BUFF_TITLE = 'B\xb3ogos\xb3awie\xf1stwa goblina'
GOBLIN_BUFFS = ('\xafycie goblina', 'Obrona goblina', 'Odporno\x9c\xe6 goblina na trucizn\xea', 'Szybko\x9c\xe6 goblina')
EVENT_BUTTON_TOOLTIP = 'Poszukiwanie skarb\xf3w'
EVENT_ENDS = 'Koniec: %s'
TIME_LEFT = 'Pozosta\xb3y czas: %s'

# The server's messages (playerbot_goblin.h, EMsg): (text, big notice).
MESSAGES = {
	0: ('Poszukiwanie skarb\xf3w rozpocz\xea\xb3o si\xea.', False),
	1: ('Poszukiwanie skarb\xf3w zako\xf1czy\xb3o si\xea.', False),
	2: ('Odbierz nagrod\xea za tur\xea w oknie Poszukiwania skarb\xf3w.', False),
	4: ('Na %d. turze nie ma ju\xbf b\xb3ogos\xb3awie\xf1stw.', False),
	6: ('Masz %d Doblon\xf3w. Wykorzystaj je, zanim wejdziesz ponownie.', False),
	7: ('Pozosta\xb3y czas: %s', False),
	8: ('Czas min\xb9\xb3 - za chwil\xea zostaniesz przeniesiony z wyspy.', False),
	9: ('Uda\xb3o ci si\xea ochroni\xe6 Goblina Skarb\xf3w!', True),
	10: ('Otrzymujesz 100 Doblon\xf3w.', False),
	11: ('Bezpiecznie odprowad\x9f Goblina Skarb\xf3w do celu.', False),
	12: ('Je\x9cli ty albo Goblin Skarb\xf3w zginiecie, wyprawa si\xea nie uda.', False),
	13: ('Otrzymujesz 1 Doblona.', False),
	14: ('Nie mo\xbfesz mie\xe6 wi\xeacej Doblon\xf3w. Wydaj cz\xea\x9c\xe6, aby zobaczy\xe6 nagrody.', False),
	15: ('To z\xb3a skrzynia skarb\xf3w. Odprowad\x9f Goblina Skarb\xf3w jeszcze raz!', True),
	16: ('Eskorta nie powiod\xb3a si\xea.', False),
	17: ('Za chwil\xea zostaniesz przeniesiony z wyspy.', False),
	18: ('Aby wej\x9c\xe6, potrzebujesz co najmniej %d poziomu.', False),
	19: ('Nie mo\xbfesz wej\x9c\xe6, b\xead\xb9c w grupie.', False),
	20: ('Nagrody mo\xbfesz zresetowa\xe6 dopiero po odebraniu co najmniej jednej.', False),
	21: ('Aby zresetowa\xe6 nagrody, najpierw odbierz nagrod\xea za tur\xea.', False),
	22: (GET_ACCUMULATED_REWARD_BUTTON_TOOLTIP, False),
	23: ('[Poszukiwanie skarb\xf3w] Osi\xb9gni\xeato now\xb9 tur\xea!', False),
	24: ('Aby zobaczy\xe6 nagrody, potrzebujesz %d Doblon\xf3w.', False),
	25: ('Brak miejsca w ekwipunku.', False),
	26: ('Nie masz wystarczaj\xb9co Kluczy Goblina.', False),
	27: (REWARD_BUTTON_TOOLTIP_2, False),
	28: ('Ta tura jest ju\xbf pe\xb3na - odbierz nagrod\xea za tur\xea.', False),
	29: ('Nie mo\xbfesz tego tutaj u\xbfy\xe6.', False),
	40: ('Wyspa Skarb\xf3w jest jeszcze zamkni\xeata.', False),
	41: ('W skrzyni by\xb3 Bilet Skarb\xf3w!', False),
	42: ('Otrzymujesz %d Kluczy Goblina.', False),
	43: ('Porozmawiaj z Goblinem Skarb\xf3w.', False),
	44: ('Za %d. odprowadzenie do w\xb3a\x9cciwej skrzyni otrzymujesz Klucz Goblina!', False),
}
REMAIN_BUFF = 'Na %d. turze zosta\xb3o jeszcze %d b\xb3ogos\xb3awie\xf1stw.'

_data = {
	'game': None,
	'on': False, 'end': 0,
	'info': None,
	'slots': [],
	'acc': (0, 0), 'rounds': {},
	'rank': [], 'rankme': None, 'rankPending': [],
	'window': None, 'button': None, 'island': None,
}


def Send(command):
	net.SendChatPacket(('/goblin ' + command).strip())


def ToInt(value, default=0):
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


_known = {}


# Whether the client's item table has the item: an unknown vnum makes the
# exe select 60001 instead (and say so in syserr - hence the cache).
def ItemKnown(vnum):
	if vnum in _known:
		return _known[vnum]
	known = False
	try:
		result = item.SelectItem(vnum)
		if result is not None:
			known = bool(result)
		else:
			name = item.GetItemName()
			item.SelectItem(60001)
			known = vnum == 60001 or name != item.GetItemName()
	except Exception:
		known = False
	_known[vnum] = known
	return known


def ItemName(vnum):
	if not ItemKnown(vnum):
		# Not the fallback item's name (the exe selects 60001).
		return OWN_ITEM_NAME.get(vnum, UNKNOWN_ITEM % vnum)
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except Exception:
		return UNKNOWN_ITEM % vnum


_iconKnown = {}


# The icon of an item the client's item table does not know: the event's own
# ones, else icon/item/<vnum>.tga when the packs have it (an empty slot
# otherwise - a hole in the board).
def FallbackIcon(vnum):
	if vnum in OWN_ITEM_ICON:
		return OWN_ITEM_ICON[vnum]
	if vnum in _iconKnown:
		return _iconKnown[vnum]
	path = 'icon/item/%05d.tga' % vnum
	try:
		if not app.IsExistFile(path):
			path = None
	except Exception:
		path = None
	_iconKnown[vnum] = path
	return path


def ClockText(epoch):
	try:
		import time
		return time.strftime('%d.%m %H:%M', time.localtime(int(epoch)))
	except Exception:
		return ''


def MinSec(seconds):
	seconds = max(0, int(seconds))
	return '%02d:%02d' % (seconds // 60, seconds % 60)


def GetSlotRewardType(slotIndex):
	for rewardType, slotList in SLOT_REWARD_TYPE_DATA.items():
		if slotIndex in slotList:
			return rewardType
	return 0


def AppendChat(message, big=False):
	game = _data.get('game')
	if big and game is not None:
		interface = getattr(game, 'interface', None)
		board = getattr(interface, 'bigBoard', None) if interface else None
		if board:
			try:
				board.SetTip(message)
				return
			except Exception:
				pass
	chat.AppendChat(chat.CHAT_TYPE_INFO, message)


def OnMessage(msgId, data=0):
	if msgId == 3:
		AppendChat(REMAIN_BUFF % (data >> 16, data & 0xFFFF))
		return
	entry = MESSAGES.get(msgId)
	if not entry:
		return
	text, big = entry
	if '%s' in text:
		text = text % MinSec(data)
	elif '%d' in text:
		text = text % data
	AppendChat(text, big)
	if msgId in (16, 17):
		island = _data.get('island')
		if island:
			island.Hide()


# The refine blessings on the affect bar (uiaffectbar.py keeps a dict of what
# it shows; the event's two affects are added to it, not to the file).
def RegisterAffects():
	try:
		import uiaffectbar
		for affect, text in ((AFFECT_REFINE_PCT, INCREASE_REFINE_PCT % 10), (AFFECT_REFINE_FREE, REFINE_FREE_MATERIAL)):
			if not uiaffectbar.AFFECT_SHOW_DATA.has_key(affect):
				uiaffectbar.AFFECT_SHOW_DATA[affect] = {
					'description': BUFF_TITLE + ': ' + text,
					'icon': IMG + 'affect/treasure_hunt_refine_buff.tga',
				}
	except Exception:
		pass


RegisterAffects()


class ThinToolTip(object):
	"""The archive's thin tooltip: a few centred lines, the first a title."""

	def __init__(self):
		self.tooltip = None

	def Show(self, lines, titleFirst=False):
		self.Hide()
		if not lines:
			return
		tooltip = uiToolTip.ToolTip()
		for index, line in enumerate(lines):
			if not line:
				continue
			if titleFirst and index == 0 and len(lines) > 1:
				tooltip.AutoAppendTextLine(line, uiToolTip.ToolTip.TITLE_COLOR)
			else:
				tooltip.AutoAppendTextLine(line)
		# AutoAppendTextLine neither sizes the background nor re-centres the
		# lines placed before the tooltip grew wider: without this the text
		# floated with no background (what uicharacter.py does too).
		tooltip.AlignHorizonalCenter()
		tooltip.ShowToolTip()
		self.tooltip = tooltip

	def Hide(self):
		if self.tooltip:
			self.tooltip.HideToolTip()
			self.tooltip = None

	def Update(self):
		if self.tooltip:
			try:
				self.tooltip.OnUpdate()
			except Exception:
				pass


# The hover of a button or a plain window. A Button's C++ side calls
# ShowToolTip/HideToolTip, which run Window.OnMouseOverIn/Out - the class's,
# reading eventDict - so an OnMouseOverIn set on the instance never ran and
# the buttons had no tooltips. The string events work for both.
def BindHover(widget, overIn, overOut):
	if not widget:
		return
	if isinstance(widget, ui.ImageBox) or not hasattr(widget, 'eventDict'):
		widget.OnMouseOverIn = overIn
		widget.OnMouseOverOut = overOut
		return
	ui.Window.SetStringEvent(widget, 'MOUSE_OVER_IN', overIn)
	ui.Window.SetStringEvent(widget, 'MOUSE_OVER_OUT', overOut)


class SlotMarks(object):
	"""Images over a slot window: the claimed tick, and the icon of an item the
	client's item table does not know yet (the event's own)."""

	ICON_SIZE = 32

	def __init__(self, slotWindow, slotSize, count):
		self.slot = slotWindow
		self.size = slotSize
		self.count = count
		self.images = {}

	# Where the slot window draws an item: its icon at the slot's top left
	# (the 45 px cells of the round window are laid out for that), a smaller
	# image centred in that 32 x 32 icon box. The marks used to be centred
	# in the whole cell - 6 px off the items beside them.
	def __Position(self, index, image, width, height):
		column = index % 5
		row = index // 5
		image.SetPosition(column * self.size + max(0, (self.ICON_SIZE - width) // 2),
				row * self.size + max(0, (self.ICON_SIZE - height) // 2))

	def Set(self, index, kind, fileName, locked=False):
		key = (index, kind)
		image = self.images.get(key)
		if image is None:
			image = ui.ImageBox()
			image.SetParent(self.slot)
			image.AddFlag('not_pick')
			self.images[key] = image
		image.LoadImage(fileName)
		if locked:
			image.SetColor(*LOCKED_SLOT_DIFFUSE)
		else:
			image.SetColor(1.0, 1.0, 1.0, 1.0)
		self.__Position(index, image, image.GetWidth(), image.GetHeight())
		image.Show()

	def Raise(self, index, kind):
		image = self.images.get((index, kind))
		if image:
			image.SetTop()

	def Clear(self, index=None, kind=None):
		for key, image in self.images.items():
			if (index is None or key[0] == index) and (kind is None or key[1] == kind):
				image.Hide()

	def Destroy(self):
		for image in self.images.values():
			image.Hide()
		self.images = {}
		self.slot = None


class TreasureHuntWindow(ui.ScriptWindow):
	"""The archive's TreasureHuntWindow: the board of 25 rewards, the
	Doubloons, the round counter, the keys, the buttons."""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.isLoaded = 0
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.thin = ThinToolTip()
		self.resetPopup = None
		self.roundWindow = None
		self.rankingWindow = None
		self.flashCounter = 0
		self.flashOn = False
		self.marks = None
		self.glows = {}
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		if self.isLoaded:
			return
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/goblinwindow.py')
		self.board = self.GetChild('board')
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.rewardSlot = self.GetChild('reward_slot')
		self.rewardSlot.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInItem))
		self.rewardSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutItem))
		self.marks = SlotMarks(self.rewardSlot, 32, REWARD_LIST_COUNT)
		self.goldCountText = self.GetChild('gold_count_text')
		self.accumulateCountText = self.GetChild('accumulate_count_text')
		self.keyCountText = self.GetChild('key_count_text')
		self.rewardButton = self.GetChild('reward_button')
		self.rewardOffButton = self.GetChild('reward_off_button')
		self.rewardSetButton = self.GetChild('reward_set_button')
		self.rewardSetOffButton = self.GetChild('reward_set_button_off')
		self.resetButton = self.GetChild('reset_button')
		self.resetOffButton = self.GetChild('reset_off_button')
		self.accumulateRewardListButton = self.GetChild('accumulate_reward_list_button')
		self.rankingButton = self.GetChild('ranking_button')
		self.accumulateHelpButton = self.GetChild('accumulate_count_help_button')

		self.rewardButton.SetEvent(ui.__mem_func__(self.__ClickRewardButton))
		self.rewardSetButton.SetEvent(ui.__mem_func__(self.__ClickRewardSettingButton))
		self.resetButton.SetEvent(ui.__mem_func__(self.__ClickRewardResetButton))
		# The sunken (*_off) frames ask the server too: it decides and says
		# why not (too few Doubloons, the round's reward first...), where a
		# click on them used to do nothing at all.
		self.rewardOffButton.SetEvent(ui.__mem_func__(self.__ClickRewardOffButton))
		self.rewardSetOffButton.SetEvent(ui.__mem_func__(self.__ClickRewardSettingButton))
		self.resetOffButton.SetEvent(ui.__mem_func__(self.__ClickRewardResetButton))
		self.accumulateRewardListButton.SetEvent(ui.__mem_func__(self.__ClickAccumulatedRewardButton))
		self.rankingButton.SetEvent(ui.__mem_func__(self.__ClickRankingButton))
		self.accumulateHelpButton.SetEvent(ui.__mem_func__(self.__ClickAccumulatedRewardButton))

		# The glow of what can be done now: the lit frame of the button, an
		# image over it that takes no click (the archive's overlay).
		for name, image, x, y in (('reveal', 'reward_set_bt_over.tga', 208, 97), ('claim', 'reward_bt_over.tga', 12, 238),
				('reset', 'reset_bt_over.tga', 151, 239), ('tur', 'reward_list_bt_over.tga', 208, 197)):
			glow = ui.ImageBox()
			glow.SetParent(self.board)
			glow.AddFlag('not_pick')
			glow.LoadImage(EV + image)
			glow.SetPosition(x, y)
			glow.Hide()
			self.glows[name] = glow

		# gold_icon_bg lies under gold_count_bg; a window that always takes
		# the mouse gives the icon its tooltip.
		pick = ui.Window()
		pick.SetParent(self.board)
		pick.SetPosition(205, 62)
		pick.SetSize(72, 28)
		pick.SetPickAlways()
		pick.AddFlag('float')
		pick.Show()
		self.goldIconPick = pick

		BindHover(pick, ui.__mem_func__(self.__OverInGoldIcon), ui.__mem_func__(self.thin.Hide))
		BindHover(self.rewardSetButton, ui.__mem_func__(self.__OverInRewardSetButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.rewardSetOffButton, ui.__mem_func__(self.__OverInRewardSetButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.rewardButton, ui.__mem_func__(self.__OverInRewardButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.rewardOffButton, ui.__mem_func__(self.__OverInRewardButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.resetButton, ui.__mem_func__(self.__OverInResetButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.resetOffButton, ui.__mem_func__(self.__OverInResetButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.accumulateRewardListButton, ui.__mem_func__(self.__OverInAccumulateRewardListButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.rankingButton, ui.__mem_func__(self.__OverInRankingButton), ui.__mem_func__(self.thin.Hide))
		BindHover(self.accumulateHelpButton, ui.__mem_func__(self.__OverInAccumulateHelpButton), ui.__mem_func__(self.thin.Hide))
		self.isLoaded = 1

	def Destroy(self):
		self.thin.Hide()
		self.__ClosePopup()
		if self.roundWindow:
			self.roundWindow.Destroy()
			self.roundWindow = None
		if self.rankingWindow:
			self.rankingWindow.Destroy()
			self.rankingWindow = None
		if self.marks:
			self.marks.Destroy()
			self.marks = None
		self.tooltipItem = None
		self.Hide()
		self.ClearDictionary()

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.thin.Hide()
		self.tooltipItem.HideToolTip()
		self.__ClosePopup()
		if self.roundWindow:
			self.roundWindow.Close()
		if self.rankingWindow:
			self.rankingWindow.Close()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# --- the state from the server

	def Info(self):
		return _data.get('info') or {}

	def CanReveal(self):
		info = self.Info()
		return (not info.get('revealed')) and info.get('gold', 0) >= NEED_GOLD_FOR_SET_REWARD

	def CanReset(self):
		info = self.Info()
		if not info.get('revealed'):
			return False
		if info.get('claims', 0) <= 0 and info.get('mask', 0) == 0:
			return False
		if info.get('canAcc'):
			return False
		return info.get('gold', 0) >= NEED_GOLD_FOR_SET_REWARD

	def Refresh(self):
		if not self.isLoaded:
			return
		info = self.Info()
		self.goldCountText.SetText(str(info.get('gold', 0)))
		self.accumulateCountText.SetText(str(info.get('rounds', 0)))
		self.keyCountText.SetText(str(info.get('keys', 0)))
		self.__RefreshRewardGrid()
		self.__RefreshButtons()
		if self.roundWindow and self.roundWindow.IsShow():
			self.roundWindow.Refresh()

	def __SlotInfo(self, index):
		info = self.Info()
		if not info.get('revealed'):
			return (0, 0, False, False)
		slots = _data.get('slots') or []
		if index >= len(slots):
			return (0, 0, False, False)
		vnum, count = slots[index]
		tier = info.get('tier', 0)
		enabled = index in OPEN_SLOT_DATA_BY_REWARD_TYPE.get(tier, ())
		claimed = (info.get('mask', 0) & (1 << index)) != 0
		return (vnum, count, claimed, enabled)

	def __RefreshRewardGrid(self):
		self.marks.Clear()
		for index in xrange(REWARD_LIST_COUNT):
			self.rewardSlot.ClearSlot(index)
			vnum, count, claimed, enabled = self.__SlotInfo(index)
			if not vnum:
				continue
			if ItemKnown(vnum):
				if enabled:
					self.rewardSlot.SetItemSlot(index, vnum, count)
				else:
					self.rewardSlot.SetItemSlot(index, vnum, count, LOCKED_SLOT_DIFFUSE)
			else:
				icon = FallbackIcon(vnum)
				if icon:
					self.marks.Set(index, 'icon', icon, not enabled)
			if claimed:
				self.marks.Set(index, 'check', EV + 'get_reward_check.tga')
				self.marks.Raise(index, 'check')
		self.rewardSlot.RefreshSlot()

	def __SetButtonPair(self, onButton, offButton, active):
		if active:
			onButton.Show()
			offButton.Hide()
		else:
			onButton.Hide()
			offButton.Show()

	def __RefreshButtons(self):
		info = self.Info()
		self.__SetButtonPair(self.rewardSetButton, self.rewardSetOffButton, self.CanReveal())
		self.__SetButtonPair(self.rewardButton, self.rewardOffButton, bool(info.get('revealed') and info.get('canGet')))
		self.__SetButtonPair(self.resetButton, self.resetOffButton, self.CanReset())
		self.accumulateRewardListButton.Show()
		for glow in self.glows.values():
			glow.Hide()
		self.flashOn = False
		self.flashCounter = 0

	def OnUpdate(self):
		self.thin.Update()
		self.flashCounter += 1
		if self.flashCounter < FLASH_PERIOD:
			return
		self.flashCounter = 0
		self.flashOn = not self.flashOn
		on = self.flashOn
		info = self.Info()
		# Reveal while it can be used; the first (free) claim of a round; the
		# round reward and the reset once the round is complete.
		self.__Glow('reveal', on and self.CanReveal())
		self.__Glow('claim', on and info.get('revealed') and info.get('canGet') and info.get('claims', 0) == 0)
		self.__Glow('tur', on and info.get('canAcc'))
		self.__Glow('reset', on and self.CanReset())

	def __Glow(self, name, visible):
		glow = self.glows.get(name)
		if not glow:
			return
		if visible:
			glow.Show()
		else:
			glow.Hide()

	# --- the buttons

	def __ClosePopup(self):
		if self.resetPopup:
			self.resetPopup.Close()
			self.resetPopup = None

	def __ClickRewardSettingButton(self):
		Send('odkryj')

	def __ClickRewardButton(self):
		Send('szukaj')

	def __ClickRewardOffButton(self):
		Send('szukaj')

	def __ClickRewardResetButton(self):
		if self.resetPopup:
			return
		popup = uiCommon.QuestionDialog2()
		popup.SetText1(REWARD_RESET_POPUP_1)
		popup.SetText2(REWARD_RESET_POPUP_2)
		popup.SetAcceptEvent(ui.__mem_func__(self.__ConfirmRewardReset))
		popup.SetCancelEvent(ui.__mem_func__(self.__ClosePopup))
		popup.Open()
		self.resetPopup = popup

	def __ConfirmRewardReset(self):
		self.__ClosePopup()
		Send('reset')

	def __ClickAccumulatedRewardButton(self):
		if not self.roundWindow:
			self.roundWindow = RoundRewardWindow()
		if self.roundWindow.IsShow():
			self.roundWindow.Close()
			return
		self.roundWindow.Open()
		self.PlaceSideWindows()
		Send('tury')

	def __ClickRankingButton(self):
		if not self.rankingWindow:
			self.rankingWindow = RankingWindow()
		if self.rankingWindow.IsShow():
			self.rankingWindow.Close()
			return
		self.rankingWindow.Open()
		self.PlaceSideWindows()
		Send('ranking')

	# Main window -> round rewards -> ranking, side by side (the archive's
	# chain). Each side window goes right of the group when it fits there,
	# else left of it, else under the main window - never on the main window
	# (the chain used to flip the ranking back onto it on a 1024 or 1280 px
	# wide screen). They follow the main window when it is dragged.
	SIDE_GAP = -5

	def PlaceSideWindows(self):
		screenW = wndMgr.GetScreenWidth()
		screenH = wndMgr.GetScreenHeight()
		mainX, mainY = self.GetGlobalPosition()
		mainW, mainH = self.GetWidth(), self.GetHeight()
		left, right = mainX, mainX + mainW
		below = mainY + mainH + self.SIDE_GAP
		for side in (self.roundWindow, self.rankingWindow):
			if not side or not side.IsShow():
				continue
			sideW, sideH = side.GetWidth(), side.GetHeight()
			y = mainY
			if right + self.SIDE_GAP + sideW <= screenW:
				x = right + self.SIDE_GAP
				right = x + sideW
			elif left - self.SIDE_GAP - sideW >= 0:
				x = left - self.SIDE_GAP - sideW
				left = x
			elif below + sideH <= screenH:
				x = min(max(0, mainX), max(0, screenW - sideW))
				y = below
				below += sideH + self.SIDE_GAP
			else:
				x = max(0, screenW - sideW)
			y = max(0, min(y, screenH - sideH))
			side.SetPosition(x, y)

	def OnMoveWindow(self, x, y):
		self.PlaceSideWindows()

	# --- the tooltips

	def __OnOverInItem(self, slotIndex):
		vnum, count, claimed, enabled = self.__SlotInfo(slotIndex)
		if not vnum:
			return
		if ItemKnown(vnum):
			self.tooltipItem.SetItemToolTip(vnum)
			if not enabled:
				tier = GetSlotRewardType(slotIndex)
				if tier in TIER_LOCKED:
					self.tooltipItem.AppendSpace(5)
					self.tooltipItem.AppendTextLine(TIER_LOCKED[tier], 0xffff7777)
			self.tooltipItem.ShowToolTip()
		else:
			lines = [ItemName(vnum)]
			if not enabled and GetSlotRewardType(slotIndex) in TIER_LOCKED:
				lines.append(TIER_LOCKED[GetSlotRewardType(slotIndex)])
			self.thin.Show(lines, True)

	def __OnOverOutItem(self):
		self.tooltipItem.HideToolTip()
		self.thin.Hide()

	def __OverInGoldIcon(self):
		self.thin.Show((GOLD_ICON_TOOLTIP_TITLE, GOLD_ICON_TOOLTIP_1, GOLD_ICON_TOOLTIP_1B, GOLD_ICON_TOOLTIP_2 % GOLD_MAX), True)

	# The buttons say what they would do now (the sunken ones why not).
	def __OverInRewardSetButton(self):
		info = self.Info()
		lines = [SET_REWARD_BUTTON_TOOLTIP_1, SET_REWARD_BUTTON_TOOLTIP_2 % NEED_GOLD_FOR_SET_REWARD]
		if info.get('revealed'):
			lines.append(SET_REWARD_BUTTON_TOOLTIP_DONE)
		elif info.get('gold', 0) < NEED_GOLD_FOR_SET_REWARD:
			lines.append(SET_REWARD_BUTTON_TOOLTIP_GOLD % NEED_GOLD_FOR_SET_REWARD)
		self.thin.Show(lines, True)

	def __OverInAccumulateHelpButton(self):
		self.thin.Show((ACCUMULATE_COUNT_TOOLTIP,))

	def __OverInAccumulateRewardListButton(self):
		self.thin.Show((SHOW_ACCUMULATE_REWARD_BUTTON_TOOLTIP,))

	def __OverInRewardButton(self):
		info = self.Info()
		if not info.get('revealed'):
			second = REWARD_BUTTON_TOOLTIP_2
		elif info.get('claims', 0) >= GET_MAX_REWARD_COUNT or not info.get('canGet'):
			second = REWARD_BUTTON_TOOLTIP_FULL
		elif info.get('claims', 0) == 0:
			second = REWARD_BUTTON_TOOLTIP_FREE
		else:
			second = REWARD_BUTTON_TOOLTIP_KEY
		self.thin.Show((REWARD_BUTTON_TOOLTIP_1, second), True)

	def __OverInResetButton(self):
		info = self.Info()
		lines = [RESET_BUTTON_TOOLTIP, RESET_BUTTON_TOOLTIP_COST % NEED_GOLD_FOR_SET_REWARD]
		if info.get('revealed') and not self.CanReset():
			if info.get('claims', 0) <= 0 and info.get('mask', 0) == 0:
				lines.append(MESSAGES[20][0])
			elif info.get('canAcc'):
				lines.append(MESSAGES[21][0])
			else:
				lines.append(SET_REWARD_BUTTON_TOOLTIP_GOLD % NEED_GOLD_FOR_SET_REWARD)
		self.thin.Show(lines, True)

	def __OverInRankingButton(self):
		self.thin.Show((RANKING_BUTTON_TOOLTIP,))


class RoundRewardWindow(ui.ScriptWindow):
	"""The archive's AccumulatedRewardListWindow: the ten rounds' rewards, the
	description, the round reward's button."""

	DESC_VISIBLE_LINES = 4
	DESC_WRAP = 30

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.thin = ThinToolTip()
		self.viewRound = 0
		self.rewardData = []
		self.canClaimNow = False
		self.flashCounter = 0
		self.flashOn = False
		self.descStart = 0
		self.descLines = []
		self.descTexts = []
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/goblinrewardlistwindow.py')
		self.board = self.GetChild('board')
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.rewardSlot = self.GetChild('reward_slots')
		self.rewardSlot.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInItem))
		self.rewardSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutItem))
		self.marks = SlotMarks(self.rewardSlot, 45, ROUND_REWARD_SLOT_COUNT)
		self.countText = self.GetChild('accumulate_count_text')
		self.GetChild('accumulate_prev_bt').SetEvent(ui.__mem_func__(self.__ClickPrev))
		self.GetChild('accumulate_next_bt').SetEvent(ui.__mem_func__(self.__ClickNext))
		self.rewardButton = self.GetChild('accumulate_reward_bt')
		self.rewardOffButton = self.GetChild('accumulate_reward_off_bt')
		self.rewardButton.SetEvent(ui.__mem_func__(self.__ClickClaim))
		BindHover(self.rewardButton, ui.__mem_func__(self.__OverInClaim), ui.__mem_func__(self.thin.Hide))
		BindHover(self.rewardOffButton, ui.__mem_func__(self.__OverInClaim), ui.__mem_func__(self.thin.Hide))
		self.descPrev = self.GetChild('desc_prev_bt')
		self.descNext = self.GetChild('desc_next_bt')
		self.descPrev.SetEvent(ui.__mem_func__(self.__ClickDescPrev))
		self.descNext.SetEvent(ui.__mem_func__(self.__ClickDescNext))

		self.glow = ui.ImageBox()
		self.glow.SetParent(self.board)
		self.glow.AddFlag('not_pick')
		self.glow.LoadImage(EV + 'reward_list/reward_on_btn_over.tga')
		self.glow.SetPosition(19, 135)
		self.glow.Hide()

		# The description, four lines at a time (the archive's event set).
		for line in DESCRIPTION:
			self.descLines.extend(self.__Wrap(line))
		for i in xrange(self.DESC_VISIBLE_LINES):
			text = ui.TextLine()
			text.SetParent(self.board)
			text.SetPosition(17, 67 + i * 16)
			text.SetFontColor(0.7843, 0.7843, 0.7843)
			text.Show()
			self.descTexts.append(text)
		self.__RefreshDescription()

	def __Wrap(self, text):
		words = text.split(' ')
		lines = []
		current = ''
		for word in words:
			candidate = (current + ' ' + word).strip()
			if len(candidate) > self.DESC_WRAP and current:
				lines.append(current)
				current = word
			else:
				current = candidate
		if current:
			lines.append(current)
		return lines

	def __RefreshDescription(self):
		for i, text in enumerate(self.descTexts):
			index = self.descStart + i
			text.SetText(self.descLines[index] if index < len(self.descLines) else '')
		if len(self.descLines) <= self.DESC_VISIBLE_LINES:
			self.descPrev.Hide()
			self.descNext.Hide()
		else:
			self.descPrev.Show()
			self.descNext.Show()

	def __ClickDescPrev(self):
		if self.descStart <= 0:
			return
		self.descStart = max(0, self.descStart - self.DESC_VISIBLE_LINES)
		self.__RefreshDescription()

	def __ClickDescNext(self):
		if self.descStart + self.DESC_VISIBLE_LINES >= len(self.descLines):
			return
		self.descStart += self.DESC_VISIBLE_LINES
		self.__RefreshDescription()

	def Destroy(self):
		self.thin.Hide()
		if self.marks:
			self.marks.Destroy()
			self.marks = None
		self.tooltipItem = None
		self.descTexts = []
		self.Hide()
		self.ClearDictionary()

	def Open(self):
		tier, canTake = _data.get('acc', (0, 0))
		self.viewRound = min(MAX_ROUND_INDEX, max(0, tier))
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.thin.Hide()
		self.tooltipItem.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SetData(self, tierChanged):
		tier, canTake = _data.get('acc', (0, 0))
		if tierChanged:
			self.viewRound = min(MAX_ROUND_INDEX, max(0, tier))
		self.Refresh()

	def __ClickPrev(self):
		if self.viewRound > 0:
			self.viewRound -= 1
			self.Refresh()

	def __ClickNext(self):
		if self.viewRound < MAX_ROUND_INDEX:
			self.viewRound += 1
			self.Refresh()

	def Refresh(self):
		self.thin.Hide()
		self.tooltipItem.HideToolTip()
		self.countText.SetText(str(self.viewRound + 1))
		self.rewardData = _data['rounds'].get(self.viewRound, [])
		self.marks.Clear()
		for i in xrange(ROUND_REWARD_SLOT_COUNT):
			self.rewardSlot.ClearSlot(i)
			if i >= len(self.rewardData):
				continue
			vnum, count, affect = self.rewardData[i][0], self.rewardData[i][1], self.rewardData[i][2]
			if affect:
				self.marks.Set(i, 'icon', IMG + 'affect/treasure_hunt_refine_buff.tga')
			elif ItemKnown(vnum):
				self.rewardSlot.SetItemSlot(i, vnum, count)
			else:
				icon = FallbackIcon(vnum)
				if icon:
					self.marks.Set(i, 'icon', icon)
		self.rewardSlot.RefreshSlot()
		tier, canTake = _data.get('acc', (0, 0))
		info = _data.get('info') or {}
		canTake = canTake or (info.get('canAcc') and info.get('revealed') and info.get('claims', 0) >= GET_MAX_REWARD_COUNT)
		self.canClaimNow = bool(canTake) and self.viewRound == min(MAX_ROUND_INDEX, tier)
		if self.canClaimNow:
			self.rewardButton.Show()
			self.rewardOffButton.Hide()
		else:
			self.rewardButton.Hide()
			self.rewardOffButton.Show()
			self.glow.Hide()
		self.flashOn = False
		self.flashCounter = 0

	def OnUpdate(self):
		self.thin.Update()
		if not self.canClaimNow:
			return
		self.flashCounter += 1
		if self.flashCounter < FLASH_PERIOD:
			return
		self.flashCounter = 0
		self.flashOn = not self.flashOn
		if self.flashOn:
			self.glow.Show()
		else:
			self.glow.Hide()

	def __ClickClaim(self):
		if not self.canClaimNow:
			return
		self.glow.Hide()
		Send('tura')

	def __OverInClaim(self):
		tier, canTake = _data.get('acc', (0, 0))
		current = min(MAX_ROUND_INDEX, max(0, tier))
		if self.canClaimNow:
			second = GET_ACCUMULATED_REWARD_BUTTON_TOOLTIP
		elif self.viewRound != current:
			second = ROUND_REWARD_TOOLTIP_OTHER % (current + 1)
		else:
			second = ROUND_REWARD_TOOLTIP_NOT_YET % GET_MAX_REWARD_COUNT
		self.thin.Show((ROUND_REWARD_TOOLTIP_TITLE, second), True)

	def __OnOverInItem(self, slotIndex):
		self.thin.Hide()
		self.tooltipItem.HideToolTip()
		if slotIndex < 0 or slotIndex >= len(self.rewardData):
			return
		vnum, count, affect, limited, left = self.rewardData[slotIndex]
		if affect:
			lines = [BUFF_TITLE]
			if vnum == AFFECT_REFINE_PCT:
				lines.append(INCREASE_REFINE_PCT % (count or 10))
			else:
				lines.append(REFINE_FREE_MATERIAL)
			if limited:
				lines.append('%s: %d' % (REMAINING_LABEL, left))
			self.thin.Show(lines, True)
			return
		if not ItemKnown(vnum):
			self.thin.Show((ItemName(vnum),))
			return
		self.tooltipItem.SetItemToolTip(vnum)
		if limited:
			self.tooltipItem.AppendSpace(6)
			self.tooltipItem.AppendTextLine('%s: %d' % (REMAINING_LABEL, left), 0xffffd200)
		self.tooltipItem.ShowToolTip()

	def __OnOverOutItem(self):
		self.thin.Hide()
		self.tooltipItem.HideToolTip()


class RankInfo(ui.ListBoxEx.Item):
	"""A row of the archive's ranking: the place, the name, the rounds."""
	HIGH_RANK_IMG = EV + 'ranking/high_ranking_bg.tga'
	CUR_PLAYER_RANK_IMG = EV + 'ranking/my_ranking_bg.tga'
	# The row's background (246 x 21) has three boxes: the place 0-54, the
	# name 54-179 and the rounds 179-234. Every text is centred in its box
	# (the headers of uiscript/goblinrankingwindow.py sit over the same ones).
	WIDTH = 246
	HEIGHT = 21
	COLUMNS = ((0, 54), (54, 125), (179, 55))

	def __init__(self, rank, name, rounds, isHighRanker):
		ui.ListBoxEx.Item.__init__(self)
		self.children = []
		background = ui.ImageBox()
		background.SetParent(self)
		background.LoadImage(self.HIGH_RANK_IMG if isHighRanker else self.CUR_PLAYER_RANK_IMG)
		background.SetPosition(0, 0)
		background.AddFlag('not_pick')
		background.Show()
		self.children.append(background)
		for (x, width), text in zip(self.COLUMNS, (str(rank), name, str(rounds))):
			holder = ui.Window()
			holder.SetParent(self)
			holder.SetPosition(x, 0)
			holder.SetSize(width, self.HEIGHT)
			holder.AddFlag('not_pick')
			holder.Show()
			line = ui.TextLine()
			line.SetParent(holder)
			line.SetPosition(0, 0)
			line.SetHorizontalAlignCenter()
			line.SetVerticalAlignCenter()
			line.SetWindowHorizontalAlignCenter()
			line.SetWindowVerticalAlignCenter()
			line.SetText(text)
			line.Show()
			self.children.append(holder)
			self.children.append(line)
		self.SetSize(self.WIDTH, self.HEIGHT)

	def __del__(self):
		ui.ListBoxEx.Item.__del__(self)

	# A ranking row is not selectable (no blue bar on a click).
	def OnMouseLeftButtonDown(self):
		pass

	def OnSelectedRender(self):
		pass


class RankingWindow(ui.ScriptWindow):
	"""The archive's AccumultedCountRankingWindow."""

	HIGH_RANKER_MAX_COUNT = 10
	ROW_STEP = 23

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		ui.PythonScriptLoader().LoadScriptFile(self, 'UIScript/goblinrankingwindow.py')
		self.board = self.GetChild('board')
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.highRankerList = self.GetChild('high_ranking_list')
		self.curPlayerRank = self.GetChild('cur_player_rank')
		self.emptyText = self.GetChild('empty_text')
		self.dot = self.GetChild('dot')
		# The view count first: SetItemSize/SetItemStep size the list box from
		# it (the own-place box was ten rows tall, out of the window).
		for listBox, count in ((self.highRankerList, self.HIGH_RANKER_MAX_COUNT), (self.curPlayerRank, 1)):
			listBox.SetViewItemCount(count)
			listBox.SetItemSize(RankInfo.WIDTH, RankInfo.HEIGHT)
			listBox.SetItemStep(self.ROW_STEP)
		self.dot.Hide()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.Hide()
		self.ClearDictionary()

	def Open(self):
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Refresh(self):
		self.highRankerList.RemoveAllItems()
		self.curPlayerRank.RemoveAllItems()
		ranks = _data.get('rank', [])[:self.HIGH_RANKER_MAX_COUNT]
		for place, name, rounds in ranks:
			self.highRankerList.AppendItem(RankInfo(place, name, rounds, True))
		if ranks:
			self.emptyText.Hide()
		else:
			self.emptyText.Show()
		me = _data.get('rankme')
		self.dot.Hide()
		if me and me[2] > 0:
			self.curPlayerRank.AppendItem(RankInfo(me[0] if me[0] > 0 else '-', me[1], me[2], False))
			# The dots only between the list and a place below it.
			if me[0] <= 0 or me[0] > len(ranks) + 1:
				self.dot.Show()


class GoblinBoard(ui.ThinBoard):
	"""The archive's AllianceTargetBoard: the goblin's name and life, and on
	the mouse his life in numbers and his blessings."""
	BOARD_WIDTH = 116
	BOARD_HEIGHT = 43
	GAUGE_WIDTH = 87

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.AddFlag('float')
		self.curHP = 0
		self.maxHP = 0
		self.buffMask = 0
		self.left = 0
		self.thin = ThinToolTip()
		self.nameText = ui.TextLine()
		self.nameText.SetParent(self)
		self.nameText.SetPosition(13, 11)
		self.nameText.SetOutline()
		self.nameText.SetText(GOBLIN_NAME)
		self.nameText.Show()
		self.hpGauge = ui.Gauge()
		self.hpGauge.SetParent(self)
		self.hpGauge.MakeGauge(self.GAUGE_WIDTH, 'red')
		self.hpGauge.SetPosition(13, 11 + 12 + 1 + 3)
		self.hpGauge.Show()
		self.hover = ui.Window()
		self.hover.SetParent(self)
		self.hover.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)
		self.hover.SetPosition(0, 0)
		self.hover.SetPickAlways()
		BindHover(self.hover, ui.__mem_func__(self.__ShowDetail), ui.__mem_func__(self.thin.Hide))
		self.hover.Show()
		self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def Destroy(self):
		self.thin.Hide()
		self.hover = None
		self.hpGauge = None
		self.nameText = None

	def SetState(self, hp, maxHP, buffMask, left):
		self.curHP = max(0, int(hp))
		self.maxHP = max(1, int(maxHP))
		self.buffMask = int(buffMask)
		self.left = int(left)
		self.hpGauge.SetPercentage(self.curHP, self.maxHP)
		if self.thin.tooltip:
			self.__ShowDetail()

	def __ShowDetail(self):
		lines = ['HP : %d / %d' % (self.curHP, self.maxHP)]
		if self.left > 0:
			lines.append(TIME_LEFT % MinSec(self.left))
		buffs = [GOBLIN_BUFFS[i] for i in xrange(4) if self.buffMask & (1 << i)]
		if buffs:
			lines.append(GOBLIN_BUFF_TITLE)
			lines.extend(buffs)
		self.thin.Show(lines)

	def OnUpdate(self):
		self.thin.Update()


class TreasureIsland(object):
	"""The archive's TreasureIsland: the goblin's board and the give-up button,
	on the screen while the escort runs."""
	PANEL_WIDTH = GoblinBoard.BOARD_WIDTH
	SHOW_PHASES = (3, 4, 5)

	def __init__(self):
		self.giveUpDialog = None
		self.window = ui.Window()
		self.window.AddFlag('float')
		self.board = GoblinBoard()
		self.board.SetParent(self.window)
		self.board.SetPosition(0, 0)
		self.board.Show()
		self.giveUp = ui.Button()
		self.giveUp.SetParent(self.window)
		self.giveUp.SetUpVisual('d:/ymir work/ui/public/large_button_01.sub')
		self.giveUp.SetOverVisual('d:/ymir work/ui/public/large_button_02.sub')
		self.giveUp.SetDownVisual('d:/ymir work/ui/public/large_button_03.sub')
		self.giveUp.SetText(GIVE_UP_BUTTON)
		self.giveUp.SetEvent(ui.__mem_func__(self.__OnClickGiveUp))
		# large_button_*.sub is 88 px wide.
		self.giveUp.SetPosition((self.PANEL_WIDTH - 88) // 2, GoblinBoard.BOARD_HEIGHT + 4)
		self.giveUp.Show()
		self.window.SetSize(self.PANEL_WIDTH, GoblinBoard.BOARD_HEIGHT + 26 + 8)
		self.window.SetPosition(wndMgr.GetScreenWidth() // 2 - self.PANEL_WIDTH // 2, 60)
		self.window.Hide()

	def Destroy(self):
		self.__CloseDialog()
		if self.board:
			self.board.Destroy()
			self.board = None
		self.giveUp = None
		if self.window:
			self.window.Hide()
		self.window = None

	def Hide(self):
		self.__CloseDialog()
		if self.window:
			self.window.Hide()

	def Process(self, inDungeon, phase, hp, maxHP, buffMask, left):
		if not self.window:
			return
		if not inDungeon or maxHP <= 0 or phase not in self.SHOW_PHASES:
			self.Hide()
			return
		self.board.SetState(hp, maxHP, buffMask, left)
		if not self.window.IsShow():
			self.window.Show()
			self.window.SetTop()

	def __CloseDialog(self):
		if self.giveUpDialog:
			self.giveUpDialog.Close()
			self.giveUpDialog = None

	def __OnClickGiveUp(self):
		self.__CloseDialog()
		dialog = uiCommon.QuestionDialog()
		dialog.SetText(GIVE_UP_POPUP)
		dialog.SetAcceptEvent(ui.__mem_func__(self.__ConfirmGiveUp))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDialog))
		dialog.Open()
		self.giveUpDialog = dialog

	def __ConfirmGiveUp(self):
		self.__CloseDialog()
		self.Hide()
		Send('wyjdz')


class EventButton(ui.Window):
	"""The event's entry on the screen while it runs (the archive's mini-game
	banner): the Doubloon, left of the event calendar's icon."""

	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag('float')
		self.thin = ThinToolTip()
		self.button = ui.Button()
		self.button.SetParent(self)
		self.button.SetUpVisual(IMG + 'button_01.tga')
		self.button.SetOverVisual(IMG + 'button_02.tga')
		self.button.SetDownVisual(IMG + 'button_03.tga')
		self.button.SetEvent(ui.__mem_func__(self.__OnClick))
		BindHover(self.button, ui.__mem_func__(self.__OverIn), ui.__mem_func__(self.thin.Hide))
		self.button.SetPosition(0, 0)
		self.button.Show()
		self.SetSize(32, 32)
		self.SetPosition(wndMgr.GetScreenWidth() - 150 - 40, 204)

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.thin.Hide()
		self.button = None
		self.Hide()

	def __OnClick(self):
		ToggleWindow()

	def __OverIn(self):
		lines = [EVENT_BUTTON_TOOLTIP]
		if _data.get('end'):
			lines.append(EVENT_ENDS % ClockText(_data['end']))
		self.thin.Show(lines, True)

	def OnUpdate(self):
		self.thin.Update()


def GetWindow():
	wnd = _data['window']
	if wnd is None:
		wnd = TreasureHuntWindow()
		_data['window'] = wnd
	return wnd


def ToggleWindow():
	wnd = _data['window']
	if wnd and wnd.IsShow():
		wnd.Close()
		return
	# The server answers with the state and "GOB open".
	Send('')


def RefreshWindows():
	wnd = _data['window']
	if wnd and wnd.IsShow():
		wnd.Refresh()


def __OnEvent(on='0', end='0', *rest):
	_data['on'] = ToInt(on) == 1
	_data['end'] = ToInt(end)
	button = _data['button']
	if _data['on']:
		if button is None:
			button = EventButton()
			_data['button'] = button
		button.Show()
	else:
		if button:
			button.Hide()
		wnd = _data['window']
		if wnd:
			wnd.Close()
		island = _data['island']
		if island:
			island.Hide()


def __OnInfo(*args):
	values = [ToInt(a) for a in args]
	if len(values) < 10:
		return
	_data['info'] = {
		'on': values[0] == 1, 'gold': values[1], 'rounds': values[2], 'keys': values[3],
		'claims': values[4], 'tier': values[5], 'revealed': values[6] == 1, 'canGet': values[7] == 1,
		'canAcc': values[8] == 1, 'mask': values[9],
	}
	if not _data['info']['on']:
		wnd = _data['window']
		if wnd:
			wnd.Close()
		return
	RefreshWindows()


def __OnSlots(text='', *rest):
	slots = []
	for part in text.split(';'):
		if not part:
			continue
		fields = part.split(',')
		if len(fields) >= 2:
			slots.append((ToInt(fields[0]), ToInt(fields[1])))
	_data['slots'] = slots


def __OnAcc(tier='0', canTake='0', *rest):
	old = _data.get('acc', (0, 0))[0]
	_data['acc'] = (ToInt(tier), ToInt(canTake))
	wnd = _data['window']
	if wnd and wnd.roundWindow and wnd.roundWindow.IsShow():
		wnd.roundWindow.SetData(ToInt(tier) != old)


def __OnAccRound(roundIndex='0', text='', *rest):
	entries = []
	for part in text.split(';'):
		if not part:
			continue
		fields = [ToInt(f) for f in part.split(',')]
		while len(fields) < 5:
			fields.append(0)
		entries.append(tuple(fields[:5]))
	_data['rounds'][ToInt(roundIndex)] = entries
	wnd = _data['window']
	if wnd and wnd.roundWindow and wnd.roundWindow.IsShow():
		wnd.roundWindow.SetData(False)


def __OnRank(place='0', name='', rounds='0', *rest):
	_data['rankPending'].append((ToInt(place), name, ToInt(rounds)))


def __OnRankMe(place='0', name='', rounds='0', *rest):
	_data['rankme'] = (ToInt(place), name, ToInt(rounds))


def __OnRankEnd(*rest):
	_data['rank'] = _data['rankPending']
	_data['rankPending'] = []
	wnd = _data['window']
	if wnd and wnd.rankingWindow:
		wnd.rankingWindow.Refresh()


def __OnDungeon(*args):
	values = [ToInt(a) for a in args]
	while len(values) < 6:
		values.append(0)
	island = _data['island']
	if island is None:
		if not values[0]:
			return
		island = TreasureIsland()
		_data['island'] = island
	island.Process(values[0], values[1], values[2], values[3], values[4], values[5])


def OnCommand(game, *args):
	_data['game'] = game
	if not args:
		return
	sub, rest = args[0], args[1:]
	try:
		if sub == 'event':
			__OnEvent(*rest)
		elif sub == 'info':
			__OnInfo(*rest)
		elif sub == 'slots':
			__OnSlots(*rest)
		elif sub == 'open':
			wnd = GetWindow()
			wnd.Open()
		elif sub == 'got':
			RefreshWindows()
		elif sub == 'acc':
			__OnAcc(*rest)
		elif sub == 'accr':
			__OnAccRound(*rest)
		elif sub == 'rank':
			__OnRank(*rest)
		elif sub == 'rankme':
			__OnRankMe(*rest)
		elif sub == 'rankend':
			__OnRankEnd(*rest)
		elif sub == 'dun':
			__OnDungeon(*rest)
		elif sub == 'msg':
			OnMessage(ToInt(rest[0]) if rest else -1, ToInt(rest[1]) if len(rest) > 1 else 0)
	except Exception:
		import dbg
		import sys
		dbg.TraceError('uigoblin.OnCommand %s: %s' % (str(args), str(sys.exc_info()[1])))


def DestroyWindow():
	wnd = _data['window']
	if wnd:
		wnd.Destroy()
	_data['window'] = None
	button = _data['button']
	if button:
		button.Destroy()
	_data['button'] = None
	island = _data['island']
	if island:
		island.Destroy()
	_data['island'] = None
	_data['game'] = None
