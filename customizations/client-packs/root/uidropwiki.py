# Drop wiki - which monsters drop an item, and what a monster drops (the
# owner, 3 October: "Player should be able to type in an item name and see
# which monsters drop that item, at what rarity and amount ... as well as be
# able to type in a monster name to see what they drop"; chests stay with the
# chest preview, uichestpreview.py).
#
# MT2009_PLUS_DROP_WIKI_V2 (the owner, 10 October: the wiki shows the new
# things - weapons, refine materials, monsters, dungeons - by itself): an item
# also says where else it comes from and what it is for, a monster where it
# lives and its element. Tabs under the name:
#     item:    Potwory (who drops it), Zdobycie (recipes, the refine step that
#              makes it, chests, shops), Uzycie (recipes it is a material of,
#              the next refine step, the refine ladders it is a material of)
#              and, for a chest, Zawartosc;
#     monster: Drop and Miejsca (maps, dungeons, a dungeon's boss).
# A tab with nothing in it is not shown.
#
# Everything comes from the server (do_drop_wiki in cmd_general.cpp,
# ITEM_MANAGER::GetDropWikiRows in item_manager.cpp, MT2009_PLUS_DROP_WIKI_V1
# and V2 - server-patches/dropwiki), so what the window shows is what the
# running server's tables give:
#
#     /drop_wiki find <i|m> <text>    ->  DropWiki find_begin <i|m>
#                                         DropWiki match <vnum> <level>
#                                         DropWiki find_end <i|m> <total>
#     /drop_wiki show <i|m> <vnum>    ->  DropWiki show_begin <i|m> <vnum>
#                                         (V2 lines, below)
#                                         DropWiki row <vnum> <countMin> <countMax> <chance> <level>
#                                         DropWiki show_end <i|m> <vnum>
#     /drop_wiki                      ->  DropWiki open
#                                         DropWiki error <short|busy|bad>
#
# The V2 lines (a client without V2 skips them - OnCommand ignores what it
# does not know):
#     cube <o|i> <0 recipe|1 exchange> <npc[,npc]> <yang> <percent> <result> <count> <material:count,...>
#     refine <f|t> <item> <yang> <percent> <material:count,...>
#     chain <first> <last> <countMin> <countMax> <steps>
#     chest <i|c> <vnum> <countMin> <countMax> <chance>
#     shop <npc> <price> <count>
#     mob <level> <rank> <elements>
#     place <map> <0 map|1 dungeon|2 dungeon boss> <name or ->
# A material "a-b:n" is n of any one of the items a..b.
#
# chance is per kill in hundred-millionths (100000000 = 100%), for a player at
# the monster's own level with no premium, gloves or event; level is the
# monster's (0 on an item's row). The search is the server's: case and Polish
# letters do not matter, a number is also a vnum.
#
# Opened with its key (keybind.py "drop_wiki", "/" by default) or /drop_wiki.
# A click on a row goes the other way: an item's row shows who drops it, a
# monster's row what it drops, a recipe's or a ladder's row its item.
#
# The texts are CP1250 escapes so the file stays ASCII. Python 2.7 as the
# client has it; the rows hold the window through a weak proxy and every event
# goes through ui.__mem_func__, so nothing keeps a cycle alive.

import item
import net
import nonplayer
import ui
import uiToolTip

import uichestpreview

try:
	import dropwikiportraits
except Exception:
	dropwikiportraits = None

# ---------------------------------------------------------------------------
# The columns. False hides one: the window narrows itself and nothing else
# needs changing (the server still sends the numbers).
SHOW_COUNT = True	# "Ilosc" - how many drop at once
SHOW_CHANCE = True	# "Szansa" - the chance per kill
# ---------------------------------------------------------------------------

MARGIN = 12
ICON_W = 34
NAME_W = 230
COUNT_W = 60
CHANCE_W = 80
SCROLL_W = 17

MATCH_ROWS = 5
MATCH_ROW_H = 17
ROWS = 8
ROW_H = 34
TAB_W = 64

TEXT_HINT = 'Wpisz nazw\xea przedmiotu lub potwora i naci\x9cnij Enter.'
TEXT_SEARCHING = 'Szukam...'
TEXT_NONE = 'Nic nie znaleziono.'
TEXT_SHORT = 'Wpisz co najmniej 2 litery.'
TEXT_BUSY = 'Chwil\xea... spr\xf3buj jeszcze raz.'
TEXT_BAD = 'B\xb3\xb9d zapytania.'
TEXT_MANY = 'Znaleziono %d - pokazano %d, zaw\xea\x9f wyszukiwanie.'
TEXT_FOUND = 'Znaleziono: %d - wybierz z listy.'
TEXT_LOADING = 'Pobieram...'
TEXT_NO_DROP = 'Nic nie wypada z tabel dropu.'
TEXT_NO_MOB = '\xa3aden potw\xf3r tego nie dropi.'
TEXT_FOOTER = 'Szansa od jednego zab\xf3jstwa, dla gracza na poziomie potwora (bez premium i event\xf3w).'

# MT2009_PLUS_DROP_WIKI_V2: the tabs and their rows.
TAB_MOBS = 'Potwory'
TAB_GET = 'Zdobycie'
TAB_USE = 'U\xbfycie'
TAB_BOX = 'Zawarto\x9c\xe6'
TAB_DROP = 'Drop'
TAB_PLACES = 'Miejsca'
HEAD_MOB = 'Potw\xf3r'
HEAD_ITEM = 'Przedmiot'
HEAD_SOURCE = 'Sk\xb9d'
HEAD_USE = 'Do czego'
HEAD_PLACE = 'Gdzie'
TEXT_RECIPE = 'Receptura: %s'
TEXT_EXCHANGE = 'Wymiana: %s'
TEXT_RECIPE_AT = 'Receptura u: %s'
TEXT_EXCHANGE_AT = 'Wymiana u: %s'
TEXT_REFINE_FROM = 'Ulepszenie z: %s'
TEXT_REFINE_TO = 'Ulepszysz do: %s'
TEXT_SHOP = 'Sklep: %s'
TEXT_SHOP_PRICE = 'Cena: %s Yang'
TEXT_SPECIAL_SHOP = 'Sklep specjalny'
TEXT_IN_CHEST = 'Szansa przy jednym otwarciu skrzyni'
TEXT_CHAIN = 'Materia\xb3 ulepszania (%s)'
TEXT_CHAIN_RANGE = '%s (+%s do +%s)'
TEXT_YANG = '%s Yang'
TEXT_ANY_OF = '%dx %s (dowolne z %d)'
TEXT_NO_GET = 'Brak innych \x9fr\xf3de\xb3 ni\xbf potwory.'
TEXT_NO_USE = 'Nie jest sk\xb3adnikiem receptur ani ulepsze\xf1.'
TEXT_NO_PLACE = 'Brak danych o miejscu.'
TEXT_FOOTER_LINKS = 'Kliknij wiersz, by przej\x9c\xe6 do przedmiotu. Szansa: receptury, ulepszenia, skrzyni.'
TEXT_FOOTER_PLACES = 'Mapy z plik\xf3w odrodze\xf1 i lochy (wyprawy) z ich boss\xf3w.'
TEXT_LEVEL = 'Poziom %d'
TEXT_BOSS = 'Boss'
TEXT_ELEMENT = '\xafywio\xb3: %s'
TEXT_SEP = '  \xb7  '
ELEMENT_NAMES = ('Ogie\xf1', 'B\xb3yskawica', 'L\xf3d', 'Wiatr', 'Ziemia', 'Mrok')
PLACE_KINDS = ('Mapa', 'Loch / wyprawa', 'Boss lochu')

# The maps by index (map/index); a dungeon's name the server knows comes with
# its line (dungeon_info.txt).
MAP_NAMES = {
	1: 'Yongan', 3: 'Jayang', 4: 'Jungrang', 5: 'Ma\xb3pi Loch', 6: 'Wioska Gildii',
	21: 'Joan', 23: 'Bokjung', 24: 'Waryong', 25: 'Ma\xb3pi Loch', 26: 'Wioska Gildii',
	41: 'Pyungmoo', 43: 'Bakra', 44: 'Imha', 45: 'Ma\xb3pi Loch', 46: 'Wioska Gildii',
	61: 'G\xf3ra Sohan', 62: 'Doyyumhwaji', 63: 'Pustynia Yongbi', 64: 'Dolina Seungryong',
	65: '\x8cwi\xb9tynia Hwang', 66: 'Wie\xbfa Demon\xf3w', 67: 'Las Duch\xf3w Lungsam', 68: 'Czerwony Las',
	69: 'W\xea\xbfowe Pole', 70: 'Kraina Gigant\xf3w', 71: 'Loch Paj\xb9k\xf3w (2)', 72: 'Grota Wygna\xf1c\xf3w (1)',
	73: 'Grota Wygna\xf1c\xf3w (2)', 79: 'Labirynt', 81: 'Mapa \x8clubna', 90: 'Lodowy Loch',
	100: 'Loch Polowy', 101: 'Strefa Surowc\xf3w', 103: 'Arena (1)', 104: 'Loch Paj\xb9k\xf3w (1)',
	105: 'Arena (2)', 107: 'Ma\xb3pi Loch (\xb3atwy)', 108: 'Ma\xb3pi Loch (\x9credni)', 109: 'Ma\xb3pi Loch (trudny)',
	110: 'Arena (3)', 111: 'Arena (4)', 112: 'Arena Pojedynk\xf3w', 113: 'Mapa OX',
	181: 'Wojna Kr\xf3lestw', 182: 'Wojna Kr\xf3lestw', 183: 'Wojna Kr\xf3lestw',
	208: 'Le\xbfe Smoka', 209: '\x8cwi\xb9tynia Ochao', 216: 'Katakumby Diab\xb3a', 217: 'Loch Paj\xb9k\xf3w (3)',
	301: 'Przyl\xb9dek Smoczego Ognia', 302: 'Las Porannej Mg\xb3y', 303: 'Zatoka Czarnego Piasku', 304: 'G\xf3ra Grzmot\xf3w',
	351: 'Czy\x9cciec Ognia', 352: 'Lodowa Kraina', 358: '\x8cwi\xb9tynia Zodiaku',
	360: 'Dolina Cyklop\xf3w', 361: 'Pustkowie Faraona', 362: 'Zaczarowany Las', 363: 'Biblioteka Wiedzy',
	364: 'Wzg\xf3rze Wukonga', 365: 'Ruiny Skorpiona', 366: 'Staro\xbfytna D\xbfungla', 158: 'Ruiny Atlantydy',
	419: 'Poszukiwanie Skarb\xf3w',
}

COLOR_HEADER = 0xffc8aa80
# The Przedmiot / Potwor tabs: the chosen one in the pressed (darker) look.
TAB_UP = 'd:/ymir work/ui/public/middle_button_01.sub'
TAB_OVER = 'd:/ymir work/ui/public/middle_button_02.sub'
TAB_CHOSEN = 'd:/ymir work/ui/public/middle_button_03.sub'
COLOR_TAB = 0xffffffff
COLOR_TAB_CHOSEN = 0xfff0c860
# The rows: a darker shade of the board under each, a line above each, and the
# highlight under the mouse (ARGB - the first two digits are the opacity).
ROW_SHADE = 0x90000000
ROW_SEPARATOR = 0xff6b5a46
ROW_HOVER = 0x20ffffff
COLOR_DIM = 0xffa0a0a0
COLOR_SUB = 0xffb4a68c
COLOR_INFO = 0xffd2c8b4
# Chance colours: common, uncommon, rare, very rare.
COLOR_CHANCES = ((10.0, 0xffffffff), (1.0, 0xff9be36b), (0.1, 0xff6bb6ff), (0.0, 0xffffb050))

_data = {'window': None}


# CP1250 Polish letters to plain ones (the server folds as well, CP1250 or UTF-8).
_FOLD = {}
for _src, _dst in zip('\xb9\xe6\xea\xb3\xf1\xf3\x9c\x9f\xbf\xa5\xc6\xca\xa3\xd1\xd3\x8c\x8f\xaf',
		'acelnoszzacelnoszz'):
	_FOLD[_src] = _dst


def Fold(text):
	"""Lower case, Polish letters to plain ones."""
	return ''.join([_FOLD.get(ch, ch) for ch in text]).lower()


def ItemName(vnum):
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


def ItemDescription(vnum):
	"""The item's description (itemdesc), one line of plain text."""
	try:
		item.SelectItem(vnum)
		text = item.GetItemDescription() or ''
	except Exception:
		return ''
	for code in ('[ENTER]', '\r', '\n', '\t'):
		text = text.replace(code, ' ')
	# colour codes |cAARRGGBB ... |r / |h
	out = []
	i = 0
	while i < len(text):
		if text[i] == '|' and i + 1 < len(text):
			if text[i + 1] in 'cC':
				i += 10
				continue
			if text[i + 1] in 'rRhH':
				i += 2
				continue
		out.append(text[i])
		i += 1
	return ' '.join(''.join(out).split())


def MobName(vnum):
	try:
		name = nonplayer.GetMonsterName(vnum)
		if name:
			return name
	except Exception:
		pass
	return str(vnum)


def MobIcon(vnum):
	"""The monster's portrait (dropwikiportraits.py, icon/monster/), or the
	boss / Metin / monster icon when it has none."""
	if not dropwikiportraits:
		return ''
	try:
		return dropwikiportraits.Icon(vnum)
	except Exception:
		return ''


def NpcName(npcs):
	"""The NPCs of a recipe or a shop ("20091" or "20091,20092")."""
	names = []
	for text in npcs.split(','):
		vnum = _Int(text)
		if vnum > 0:
			names.append(MobName(vnum))
	return ', '.join(names) or TEXT_SPECIAL_SHOP


def MapName(mapIndex, name):
	if name and name != '-':
		return name.replace('_', ' ')
	return MAP_NAMES.get(mapIndex, 'Mapa %d' % mapIndex)


def FormatChance(value):
	pct = value / 1000000.0
	if pct >= 100.0:
		return '100%'
	if pct >= 1.0:
		text = '%.2f' % pct
	else:
		# three significant digits under one percent
		digits = 2
		limit = 0.1
		while pct < limit and digits < 7:
			digits += 1
			limit /= 10.0
		text = '%.*f' % (digits, pct)
	if '.' in text:
		text = text.rstrip('0').rstrip('.')
	return text + '%'


def ChanceColor(value):
	pct = value / 1000000.0
	for limit, color in COLOR_CHANCES:
		if pct >= limit:
			return color
	return COLOR_CHANCES[-1][1]


def FormatCount(countMin, countMax):
	if countMin == countMax:
		return str(countMin)
	return '%d-%d' % (countMin, countMax)


def FormatYang(value):
	"""1234567 -> '1 234 567'."""
	text = str(abs(value))
	parts = []
	while len(text) > 3:
		parts.insert(0, text[-3:])
		text = text[:-3]
	parts.insert(0, text)
	return ('-' if value < 0 else '') + ' '.join(parts)


def StepWord(steps):
	if steps == 1:
		return '1 krok'
	if steps % 10 in (2, 3, 4) and steps % 100 not in (12, 13, 14):
		return '%d kroki' % steps
	return '%d krok\xf3w' % steps


def ParseMats(text):
	"""'v:c,a-b:c' -> [(first, last, count)]."""
	mats = []
	if not text or text == '-':
		return mats
	for part in text.split(','):
		if ':' not in part:
			continue
		what, count = part.split(':', 1)
		if '-' in what:
			first, last = what.split('-', 1)
		else:
			first, last = what, '0'
		mats.append((_Int(first), _Int(last), _Int(count)))
	return mats


def MatText(mat):
	first, last, count = mat
	if last > first:
		return TEXT_ANY_OF % (count, ItemName(first), last - first + 1)
	return '%dx %s' % (count, ItemName(first))


def MatsText(mats, gold):
	parts = [MatText(mat) for mat in mats]
	text = ', '.join(parts)
	if gold > 0:
		text = (text + ' + ' if text else '') + TEXT_YANG % FormatYang(gold)
	return text


def MatsTip(title, mats, gold, pct):
	lines = [title]
	for mat in mats:
		lines.append(MatText(mat))
	if gold > 0:
		lines.append(TEXT_YANG % FormatYang(gold))
	if pct > 0:
		lines.append('Szansa: %d%%' % pct)
	return lines


def SplitPlus(name):
	"""'Miecz Zodiaku+6' -> ('Miecz Zodiaku', '6'); no '+N' -> (name, '')."""
	pos = name.rfind('+')
	if pos > 0 and name[pos + 1:].isdigit():
		return name[:pos].rstrip(), name[pos + 1:]
	return name, ''


def _Columns():
	"""x of each column inside a row, and the row's width."""
	x = ICON_W + NAME_W
	countX = chanceX = None
	if SHOW_COUNT:
		countX = x
		x += COUNT_W
	if SHOW_CHANCE:
		chanceX = x
		x += CHANCE_W
	return countX, chanceX, x


def FitText(textLine, text, width):
	"""The text, shortened with '...' to fit the width."""
	textLine.SetText(text)
	try:
		if textLine.GetTextSize()[0] <= width:
			return
		low, high = 0, len(text)
		while low < high:
			middle = (low + high + 1) // 2
			textLine.SetText(text[:middle].rstrip() + '...')
			if textLine.GetTextSize()[0] <= width:
				low = middle
			else:
				high = middle - 1
		textLine.SetText(text[:low].rstrip() + '...')
	except Exception:
		if len(text) > 64:
			textLine.SetText(text[:61] + '...')


def MakeRow(icon=None, title='', sub='', count='', chance=None, click=None, tip=None):
	"""One line of a list: icon ('i'|'m', vnum) or None, the title, a second
	line (or ''), the Ilosc and Szansa texts (chance in hundred-millionths or
	None), where a click goes (('i'|'m', vnum) or None) and the tooltip (('i',
	vnum) for an item's, a list of lines for a text one, or None)."""
	return {'icon': icon, 'title': title, 'sub': sub, 'count': count, 'chance': chance, 'click': click, 'tip': tip}


class DropRow(ui.Window):
	"""One line of the list: an icon, a name (and a second line), Ilosc, Szansa."""

	def __init__(self, owner, index):
		ui.Window.__init__(self)
		self.owner = uichestpreview.WindowProxy(owner)
		self.index = index
		countX, chanceX, width = _Columns()
		self.width = width
		self.countX = countX
		self.chanceX = chanceX
		self.SetSize(width, ROW_H)

		# a darker strip under every row, a line above it, and a lighter one
		# over it while the mouse is on the row
		self.shade = ui.Bar()
		self.shade.SetParent(self)
		self.shade.SetPosition(0, 1)
		self.shade.SetSize(width, ROW_H - 2)
		self.shade.SetColor(ROW_SHADE)
		self.shade.AddFlag('not_pick')
		self.shade.Show()

		self.separator = ui.Line()
		self.separator.SetParent(self)
		self.separator.SetPosition(0, 0)
		self.separator.SetSize(width, 0)
		self.separator.SetColor(ROW_SEPARATOR)
		self.separator.AddFlag('not_pick')
		self.separator.Show()

		self.back = ui.Bar()
		self.back.SetParent(self)
		self.back.SetPosition(0, 1)
		self.back.SetSize(width, ROW_H - 2)
		self.back.SetColor(ROW_HOVER)
		self.back.AddFlag('not_pick')
		self.back.Hide()

		self.icon = ui.ExpandedImageBox()
		self.icon.SetParent(self)
		self.icon.AddFlag('not_pick')
		self.icon.Hide()

		self.nameText = self.__Text(ICON_W, False)
		self.subText = self.__Text(ICON_W, False)
		self.subText.SetPackedFontColor(COLOR_SUB)
		self.subText.Hide()
		self.countText = self.__Text(countX + COUNT_W // 2, True) if countX is not None else None
		self.chanceText = self.__Text(chanceX + CHANCE_W // 2, True) if chanceX is not None else None

	def __Text(self, x, center):
		text = ui.TextLine()
		text.SetParent(self)
		text.SetPosition(x, ROW_H // 2 - 7)
		if center:
			text.SetHorizontalAlignCenter()
		text.AddFlag('not_pick')
		text.Show()
		return text

	def SetData(self, data):
		icon = data['icon']
		if icon and icon[0] == 'i':
			self.__SetIcon(ItemIcon(icon[1]))
		elif icon and icon[0] == 'm':
			self.__SetIcon(MobIcon(icon[1]))
		else:
			self.__SetIcon('')
		# with a second line the title, Ilosc and Szansa go up and the second
		# line takes the row's whole width
		textY = ROW_H // 2 - 7
		if data['sub']:
			textY = 3
			self.subText.SetPosition(ICON_W, 18)
			FitText(self.subText, data['sub'], self.width - ICON_W - 4)
			self.subText.Show()
		else:
			self.subText.Hide()
		self.nameText.SetPosition(ICON_W, textY)
		FitText(self.nameText, data['title'], NAME_W - 4)
		if self.countText:
			self.countText.SetPosition(self.countX + COUNT_W // 2, textY)
			self.countText.SetText(data['count'])
		if self.chanceText:
			self.chanceText.SetPosition(self.chanceX + CHANCE_W // 2, textY)
			if data['chance'] is None:
				self.chanceText.SetText('')
			else:
				self.chanceText.SetText(FormatChance(data['chance']))
				self.chanceText.SetPackedFontColor(ChanceColor(data['chance']))
		self.Show()

	def __SetIcon(self, path):
		if not path:
			self.icon.Hide()
			return
		try:
			self.icon.LoadImage(path)
			width = max(1, self.icon.GetWidth())
			height = max(1, self.icon.GetHeight())
			# 32x64 and 32x96 icons shrink to the row's height.
			scale = min(1.0, 32.0 / height, 32.0 / width)
			self.icon.SetScale(scale, scale)
			self.icon.SetPosition(int((32 - width * scale) // 2), int((ROW_H - 2 - height * scale) // 2))
			self.icon.Show()
		except Exception:
			self.icon.Hide()

	def OnMouseOverIn(self):
		self.back.Show()
		self.owner.OnRowOver(self.index)

	def OnMouseOverOut(self):
		self.back.Hide()
		self.owner.OnRowOut(self.index)

	def OnMouseLeftButtonUp(self):
		self.owner.OnRowClick(self.index)

	def OnMouseWheel(self, delta):
		self.owner.OnRowsWheel(1 if delta > 0 else -1)
		return True


class InfoArea(ui.Window):
	"""The line under the name: the mouse over it shows the whole text."""

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = uichestpreview.WindowProxy(owner)

	def OnMouseOverIn(self):
		self.owner.OnInfoOver()

	def OnMouseOverOut(self):
		self.owner.OnInfoOut()


class MatchListBox(ui.ListBox):
	"""The search results. The stock list draws its highlight from x+2 but its
	text from x 0, so the text is moved under the highlight; and a click on
	the line already chosen opens it again (the stock list ignores it), which
	is the way back after clicking through the rows to another item or
	monster."""
	TEXT_X = 5

	def _LocateItem(self):
		ui.ListBox._LocateItem(self)
		for textLine in self.itemList:
			x, y = textLine.GetLocalPosition()
			textLine.SetPosition(x + self.TEXT_X, y)

	def SelectItem(self, line):
		if not self.keyDict.has_key(line):
			return
		self.selectedLine = line
		self.event(self.keyDict.get(line, 0), self.textDict.get(line, 'None'))


class DropWikiWindow(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag('movable')
		self.AddFlag('float')
		countX, chanceX, rowWidth = _Columns()
		self.rowWidth = rowWidth
		self.width = MARGIN * 2 + rowWidth + SCROLL_W + 4
		self.mode = 'i'
		self.pendingFind = None
		self.matches = []
		self.matchTotal = 0
		self.showKind = None
		self.showVnum = 0
		self.rows = []
		self.rowBase = 0
		self.matchBase = 0
		self.scrollLock = False
		self.levels = {}
		self.widgets = []
		# MT2009_PLUS_DROP_WIKI_V2: what the server sent for the shown item or
		# monster, by tab, and the tab on screen
		self.lists = {}
		self.tab = None
		self.tabOrder = []
		self.mobInfo = None
		self.infoFull = ''

		self.SetTitleName('Drop wiki')
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		y = 34
		self.itemButton = self.__ModeButton('Przedmiot', MARGIN, y, 'i')
		self.mobButton = self.__ModeButton('Potw\xf3r', MARGIN + 64, y, 'm')

		searchX = MARGIN + 132
		searchW = self.width - MARGIN - 61 - 6 - searchX
		slot = ui.SlotBar()
		slot.SetParent(self)
		slot.SetPosition(searchX, y + 1)
		slot.SetSize(searchW, 19)
		slot.Show()
		self.widgets.append(slot)

		self.searchEdit = ui.EditLine()
		self.searchEdit.SetParent(slot)
		self.searchEdit.SetPosition(3, 3)
		self.searchEdit.SetSize(searchW - 6, 16)
		self.searchEdit.SetMax(30)
		try:
			self.searchEdit.SetPlaceholder('Szukaj...')
		except Exception:
			pass
		self.searchEdit.SetReturnEvent(ui.__mem_func__(self.Search))
		self.searchEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.searchEdit.Show()
		self.widgets.append(self.searchEdit)

		self.searchButton = self.__Button('Szukaj', self.width - MARGIN - 61, y, ui.__mem_func__(self.Search))

		# the matches
		y += 28
		listH = MATCH_ROWS * MATCH_ROW_H
		self.matchList = MatchListBox()
		self.matchList.SetParent(self)
		self.matchList.SetPosition(MARGIN, y)
		self.matchList.SetSize(self.width - MARGIN * 2 - SCROLL_W - 4, listH)
		self.matchList.SetTextCenterAlign(False)
		self.matchList.SetEvent(ui.__mem_func__(self.OnMatchSelect))
		self.matchList.SetMouseWheelEvent(self.OnMatchWheel)
		self.matchList.Show()
		self.widgets.append(self.matchList)

		self.matchScroll = ui.ScrollBar()
		self.matchScroll.SetParent(self)
		self.matchScroll.SetPosition(self.width - MARGIN - SCROLL_W, y - 3)
		self.matchScroll.SetScrollBarSize(listH + 4)
		self.matchScroll.SetScrollEvent(ui.__mem_func__(self.OnMatchScroll))
		self.matchScroll.Hide()
		self.widgets.append(self.matchScroll)

		self.statusText = self.__Label(MARGIN + 2, y + listH // 2 - 7, COLOR_DIM)
		self.statusText.SetText(TEXT_HINT)

		# the chosen one
		y += listH + 8
		line = ui.Line()
		line.SetParent(self)
		line.SetPosition(MARGIN, y)
		line.SetSize(self.width - MARGIN * 2, 0)
		line.SetColor(0xff5a4a3a)
		line.Show()
		self.widgets.append(line)

		y += 6
		self.headerText = self.__Label(MARGIN, y, 0xffffffff)
		y += 16
		# the description, or the monster's level and element
		self.infoArea = InfoArea(self)
		self.infoArea.SetParent(self)
		self.infoArea.SetPosition(MARGIN, y)
		self.infoArea.SetSize(self.width - MARGIN * 2, 15)
		self.infoArea.Show()
		self.widgets.append(self.infoArea)
		self.infoText = ui.TextLine()
		self.infoText.SetParent(self.infoArea)
		self.infoText.SetPosition(0, 0)
		self.infoText.SetPackedFontColor(COLOR_INFO)
		self.infoText.AddFlag('not_pick')
		self.infoText.Show()
		self.widgets.append(self.infoText)

		# the tabs
		y += 18
		self.tabButtons = []
		for index in xrange(4):
			button = self.__Button('', MARGIN + index * TAB_W, y, ui.__mem_func__(self.OnTabButton), index)
			button.Hide()
			self.tabButtons.append(button)

		y += 26
		self.nameHeader = self.__Label(MARGIN + ICON_W, y, COLOR_HEADER)
		self.countHeader = None
		self.chanceHeader = None
		if countX is not None:
			self.countHeader = self.__Label(MARGIN + countX + COUNT_W // 2, y, COLOR_HEADER, True)
			self.countHeader.SetText('Ilo\x9c\xe6')
		if chanceX is not None:
			self.chanceHeader = self.__Label(MARGIN + chanceX + CHANCE_W // 2, y, COLOR_HEADER, True)
			self.chanceHeader.SetText('Szansa')

		y += 18
		self.rowsTop = y
		self.rowWindows = []
		for index in xrange(ROWS):
			row = DropRow(self, index)
			row.SetParent(self)
			row.SetPosition(MARGIN, y + index * ROW_H)
			row.Hide()
			self.rowWindows.append(row)

		rowsH = ROWS * ROW_H
		self.rowScroll = ui.ScrollBar()
		self.rowScroll.SetParent(self)
		self.rowScroll.SetPosition(self.width - MARGIN - SCROLL_W, y - 2)
		self.rowScroll.SetScrollBarSize(rowsH)
		self.rowScroll.SetScrollEvent(ui.__mem_func__(self.OnRowScroll))
		self.rowScroll.Hide()
		self.widgets.append(self.rowScroll)

		self.emptyText = self.__Label(MARGIN + ICON_W, y + 8, COLOR_DIM)

		y += rowsH + 4
		self.footerText = self.__Label(MARGIN, y, COLOR_DIM)
		self.footerText.SetText(TEXT_FOOTER if SHOW_CHANCE else '')
		y += 16

		self.SetSize(self.width, y + 10)
		self.tooltipItem = uiToolTip.ItemToolTip()
		self.tooltipItem.HideToolTip()
		self.tooltipText = uiToolTip.ToolTip()
		self.tooltipText.HideToolTip()
		self.__SetMode('i')
		self.__ClearShow()
		self.SetCenterPosition()
		self.Hide()

	# -- building ------------------------------------------------------------
	def __Label(self, x, y, color, center=False):
		text = ui.TextLine()
		text.SetParent(self)
		text.SetPosition(x, y)
		if center:
			text.SetHorizontalAlignCenter()
		text.SetPackedFontColor(color)
		text.Show()
		self.widgets.append(text)
		return text

	def __Button(self, text, x, y, event, arg=None):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual('d:/ymir work/ui/public/middle_button_01.sub')
		button.SetOverVisual('d:/ymir work/ui/public/middle_button_02.sub')
		button.SetDownVisual('d:/ymir work/ui/public/middle_button_03.sub')
		button.SetText(text)
		if arg is None:
			button.SetEvent(event)
		else:
			button.SetEvent(event, arg)
		button.Show()
		self.widgets.append(button)
		return button

	def __ModeButton(self, text, x, y, mode):
		return self.__Button(text, x, y, ui.__mem_func__(self.OnModeItem if mode == 'i' else self.OnModeMob))

	# -- the search ----------------------------------------------------------
	def __SetMode(self, mode):
		self.mode = mode
		self.__MarkTab(self.itemButton, mode == 'i')
		self.__MarkTab(self.mobButton, mode == 'm')

	def __MarkTab(self, button, chosen):
		# The chosen tab keeps the pressed (darker) look even under the mouse,
		# with gold text; a button's own Down() lasts only until the mouse
		# passes over it.
		if chosen:
			button.SetUpVisual(TAB_CHOSEN)
			button.SetOverVisual(TAB_CHOSEN)
			button.SetDownVisual(TAB_CHOSEN)
			button.SetTextColor(COLOR_TAB_CHOSEN)
		else:
			button.SetUpVisual(TAB_UP)
			button.SetOverVisual(TAB_OVER)
			button.SetDownVisual(TAB_CHOSEN)
			button.SetTextColor(COLOR_TAB)

	def OnModeItem(self):
		self.__ChangeMode('i')

	def OnModeMob(self):
		self.__ChangeMode('m')

	def __ChangeMode(self, mode):
		changed = mode != self.mode
		self.__SetMode(mode)
		if changed and self.searchEdit.GetText().strip():
			self.Search()

	def Search(self):
		query = Fold(self.searchEdit.GetText().strip()).replace('"', '')
		if len(query) < 2 and not query.isdigit():
			self.__SetMatches([])
			self.__Status(TEXT_SHORT)
			return
		self.pendingFind = self.mode
		self.__SetMatches([])
		self.__Status(TEXT_SEARCHING)
		net.SendChatPacket('/drop_wiki find %s %s' % (self.mode, query))

	def __Status(self, text):
		self.statusText.SetText(text)
		if text:
			self.statusText.Show()
		else:
			self.statusText.Hide()

	def __MatchLabel(self, kind, vnum, level):
		if kind == 'i':
			return ItemName(vnum)
		if level > 0:
			return '%s (Lv %d)' % (MobName(vnum), level)
		return MobName(vnum)

	def __SetMatches(self, matches):
		self.matches = matches
		for line in self.matchList.itemList:
			line.Hide()
		self.matchList.ClearItem()
		for index, (kind, vnum, level) in enumerate(matches):
			self.matchList.InsertItem(index, self.__MatchLabel(kind, vnum, level))
		self.matchBase = 0
		self.matchList.SetBasePos(0)
		if len(matches) > MATCH_ROWS:
			self.matchScroll.SetMiddleBarSize(float(MATCH_ROWS) / len(matches))
			self.matchScroll.SetPos(0.0)
			self.matchScroll.Show()
		else:
			self.matchScroll.Hide()

	# The wheel moves the list a line at a time and puts the bar where the list
	# is - not the other way round: a short bar moves in whole pixels, so a
	# step of less than one pixel down was lost and the list never went down.
	def __SetScrollPos(self, scroll, base, extra):
		self.scrollLock = True
		try:
			scroll.SetPos(float(base) / extra)
		finally:
			self.scrollLock = False

	def OnMatchScroll(self):
		extra = len(self.matches) - MATCH_ROWS
		if extra > 0 and not self.scrollLock:
			self.matchBase = int(round(self.matchScroll.GetPos() * extra))
			self.matchList.SetBasePos(self.matchBase)

	def OnMatchWheel(self, direction):
		extra = len(self.matches) - MATCH_ROWS
		if extra > 0:
			self.matchBase = max(0, min(extra, self.matchBase - direction))
			self.matchList.SetBasePos(self.matchBase)
			self.__SetScrollPos(self.matchScroll, self.matchBase, extra)

	def OnMatchSelect(self, index, name):
		if 0 <= index < len(self.matches):
			kind, vnum, level = self.matches[index]
			self.RequestShow(kind, vnum)

	def RequestShow(self, kind, vnum):
		self.__ClearShow()
		self.headerText.SetText(TEXT_LOADING)
		net.SendChatPacket('/drop_wiki show %s %d' % (kind, vnum))

	# -- the list ------------------------------------------------------------
	def __ClearShow(self):
		self.showKind = None
		self.showVnum = 0
		self.rows = []
		self.rowBase = 0
		self.lists = {}
		self.tab = None
		self.tabOrder = []
		self.mobInfo = None
		self.infoFull = ''
		self.headerText.SetText('')
		self.infoText.SetText('')
		self.nameHeader.SetText('')
		for header in (self.countHeader, self.chanceHeader):
			if header:
				header.Hide()
		for button in self.tabButtons:
			button.Hide()
		self.emptyText.Hide()
		self.rowScroll.Hide()
		self.__HideTip()
		for row in self.rowWindows:
			row.Hide()

	def __List(self, tab):
		return self.lists.setdefault(tab, [])

	def __DrawRows(self):
		self.__HideTip()
		for index, row in enumerate(self.rowWindows):
			line = self.rowBase + index
			if line < len(self.rows):
				row.SetData(self.rows[line])
			else:
				row.Hide()

	def OnRowScroll(self):
		extra = len(self.rows) - ROWS
		if extra > 0 and not self.scrollLock:
			base = int(round(self.rowScroll.GetPos() * extra))
			if base != self.rowBase:
				self.rowBase = base
				self.__DrawRows()

	def OnRowsWheel(self, direction):
		extra = len(self.rows) - ROWS
		if extra > 0:
			base = max(0, min(extra, self.rowBase - direction * 2))
			if base != self.rowBase:
				self.rowBase = base
				self.__DrawRows()
			self.__SetScrollPos(self.rowScroll, base, extra)

	def __RowAt(self, index):
		line = self.rowBase + index
		if 0 <= line < len(self.rows):
			return self.rows[line]
		return None

	def OnRowOver(self, index):
		row = self.__RowAt(index)
		if not row or not row['tip']:
			return
		tip = row['tip']
		try:
			if isinstance(tip, tuple):
				self.tooltipItem.SetItemToolTip(tip[1])
				self.tooltipItem.ShowToolTip()
			else:
				self.__ShowTextTip(tip)
		except Exception:
			pass

	def OnRowOut(self, index):
		self.__HideTip()

	def OnRowClick(self, index):
		row = self.__RowAt(index)
		if not row or not row['click']:
			return
		kind, vnum = row['click']
		self.__SetMode(kind)
		self.RequestShow(kind, vnum)

	def __ShowTextTip(self, lines):
		self.tooltipText.ClearToolTip()
		for index, text in enumerate(lines):
			self.tooltipText.AppendTextLine(text, self.tooltipText.TITLE_COLOR if index == 0 else self.tooltipText.FONT_COLOR)
		self.tooltipText.ShowToolTip()

	def OnInfoOver(self):
		if self.infoFull and self.infoText.GetText() != self.infoFull:
			try:
				lines = uiToolTip.SplitDescription(self.infoFull, 40)
			except Exception:
				lines = [self.infoFull]
			self.__ShowTextTip([ItemName(self.showVnum)] + list(lines))

	def OnInfoOut(self):
		self.__HideTip()

	def __HideTip(self):
		for tip in (self.tooltipItem, self.tooltipText):
			try:
				tip.HideToolTip()
			except Exception:
				pass

	# -- the tabs (MT2009_PLUS_DROP_WIKI_V2) ---------------------------------
	def __TabNames(self, kind):
		if kind == 'i':
			return (('drop', TAB_MOBS), ('get', TAB_GET), ('use', TAB_USE), ('box', TAB_BOX))
		return (('drop', TAB_DROP), ('place', TAB_PLACES))

	def __SetupTabs(self):
		names = self.__TabNames(self.showKind)
		# the first tab is always there; the others only with something in them
		self.tabOrder = [key for index, (key, text) in enumerate(names) if index == 0 or self.lists.get(key)]
		texts = dict(names)
		for index, button in enumerate(self.tabButtons):
			if index < len(self.tabOrder) and len(self.tabOrder) > 1:
				button.SetText(texts[self.tabOrder[index]])
				button.Show()
			else:
				button.Hide()
		# the first tab with something in it
		chosen = self.tabOrder[0]
		for key in self.tabOrder:
			if self.lists.get(key):
				chosen = key
				break
		self.__ChooseTab(chosen)

	def OnTabButton(self, index):
		if 0 <= index < len(self.tabOrder):
			self.__ChooseTab(self.tabOrder[index])

	def __ChooseTab(self, key):
		self.tab = key
		for index, button in enumerate(self.tabButtons):
			if index < len(self.tabOrder):
				self.__MarkTab(button, self.tabOrder[index] == key)
		self.rows = self.lists.get(key, [])
		isItem = self.showKind == 'i'
		heads = {
			'drop': HEAD_MOB if isItem else HEAD_ITEM, 'get': HEAD_SOURCE, 'use': HEAD_USE,
			'box': HEAD_ITEM, 'place': HEAD_PLACE,
		}
		self.nameHeader.SetText(heads.get(key, ''))
		for header in (self.countHeader, self.chanceHeader):
			if header:
				if key == 'place':
					header.Hide()
				else:
					header.Show()
		if key in ('get', 'use', 'box'):
			self.footerText.SetText(TEXT_FOOTER_LINKS)
		elif key == 'place':
			self.footerText.SetText(TEXT_FOOTER_PLACES)
		else:
			self.footerText.SetText(TEXT_FOOTER if SHOW_CHANCE else '')
		self.rowBase = 0
		if len(self.rows) > ROWS:
			self.rowScroll.SetMiddleBarSize(float(ROWS) / len(self.rows))
			self.rowScroll.SetPos(0.0)
			self.rowScroll.Show()
		else:
			self.rowScroll.Hide()
		if not self.rows:
			empty = {
				'drop': TEXT_NO_MOB if isItem else TEXT_NO_DROP, 'get': TEXT_NO_GET, 'use': TEXT_NO_USE,
				'place': TEXT_NO_PLACE,
			}
			self.emptyText.SetText(empty.get(key, ''))
			self.emptyText.Show()
		else:
			self.emptyText.Hide()
		self.__DrawRows()

	# -- the server ----------------------------------------------------------
	def OnFindBegin(self, kind):
		if kind == self.pendingFind:
			self.matches = []

	def OnMatch(self, vnum, level):
		if self.pendingFind:
			self.matches.append((self.pendingFind, vnum, level))
			if level > 0:
				self.levels[vnum] = level

	def OnFindEnd(self, kind, total):
		if kind != self.pendingFind:
			return
		self.pendingFind = None
		matches = self.matches
		self.__SetMatches(matches)
		if not matches:
			self.__Status(TEXT_NONE)
		elif total > len(matches):
			self.__Status('')
			self.headerText.SetText(TEXT_MANY % (total, len(matches)))
		elif len(matches) > 1:
			self.__Status('')
			self.headerText.SetText(TEXT_FOUND % len(matches))
		else:
			self.__Status('')
			# one match: the server shows it straight away

	def OnShowBegin(self, kind, vnum):
		self.__ClearShow()
		self.showKind = kind
		self.showVnum = vnum
		self.headerText.SetText(TEXT_LOADING)

	def OnRow(self, vnum, countMin, countMax, chance, level):
		if not self.showKind:
			return
		if level > 0:
			self.levels[vnum] = level
		if self.showKind == 'i':
			# an item's row: a monster that drops it
			title = MobName(vnum)
			if level > 0:
				title = '%s (Lv %d)' % (title, level)
			row = MakeRow(('m', vnum), title, '', FormatCount(countMin, countMax), chance, ('m', vnum))
		else:
			row = MakeRow(('i', vnum), ItemName(vnum), '', FormatCount(countMin, countMax), chance, ('i', vnum), ('i', vnum))
		self.__List('drop').append(row)

	# MT2009_PLUS_DROP_WIKI_V2: the lines before the rows
	def OnCube(self, side, how, npcs, gold, pct, reward, rewardCount, mats):
		if self.showKind != 'i':
			return
		mats = ParseMats(mats)
		npcName = NpcName(npcs)
		chance = pct * 1000000 if pct > 0 else None
		if side == 'o':
			title = (TEXT_EXCHANGE if how == 1 else TEXT_RECIPE) % npcName
			icon = ('i', mats[0][0]) if mats else None
			tip = MatsTip(title, mats, gold, pct)
			self.__List('get').append(MakeRow(icon, title, MatsText(mats, gold), str(rewardCount), chance, None, tip))
		else:
			need = 0
			for first, last, count in mats:
				if first == self.showVnum or (last and first <= self.showVnum <= last):
					need = count
			sub = ((TEXT_EXCHANGE_AT if how == 1 else TEXT_RECIPE_AT) % npcName) + ': ' + MatsText(mats, gold)
			title = ItemName(reward)
			if rewardCount > 1:
				title = '%s (x%d)' % (title, rewardCount)
			tip = MatsTip(title, mats, gold, pct)
			self.__List('use').append(MakeRow(('i', reward), title, sub, str(need) if need else '', chance, ('i', reward), tip))

	def OnRefine(self, side, other, gold, pct, mats):
		if self.showKind != 'i':
			return
		mats = ParseMats(mats)
		chance = pct * 1000000 if pct > 0 else None
		if side == 'f':
			title = TEXT_REFINE_FROM % ItemName(other)
			self.__List('get').append(MakeRow(('i', other), title, MatsText(mats, gold), '1', chance, ('i', other),
					MatsTip(title, mats, gold, pct)))
		else:
			title = TEXT_REFINE_TO % ItemName(other)
			self.__List('use').append(MakeRow(('i', other), title, MatsText(mats, gold), '1', chance, ('i', other),
					MatsTip(title, mats, gold, pct)))

	def OnChain(self, first, last, countMin, countMax, steps):
		if self.showKind != 'i':
			return
		firstName = ItemName(first)
		if first == last:
			title = firstName
		else:
			base, firstLevel = SplitPlus(firstName)
			lastBase, lastLevel = SplitPlus(ItemName(last))
			if firstLevel and lastLevel and base == lastBase:
				title = TEXT_CHAIN_RANGE % (base, firstLevel, lastLevel)
			else:
				title = '%s - %s' % (firstName, ItemName(last))
		self.__List('use').append(MakeRow(('i', last), title, TEXT_CHAIN % StepWord(steps),
				FormatCount(countMin, countMax), None, ('i', first), ('i', last)))

	def OnChest(self, side, vnum, countMin, countMax, chance):
		if self.showKind != 'i':
			return
		if side == 'i':
			self.__List('get').append(MakeRow(('i', vnum), ItemName(vnum), TEXT_IN_CHEST,
					FormatCount(countMin, countMax), chance, ('i', vnum), ('i', vnum)))
		else:
			self.__List('box').append(MakeRow(('i', vnum), ItemName(vnum), '',
					FormatCount(countMin, countMax), chance, ('i', vnum), ('i', vnum)))

	def OnShop(self, npc, price, count):
		if self.showKind != 'i':
			return
		name = MobName(npc) if npc > 0 else TEXT_SPECIAL_SHOP
		title = TEXT_SHOP % name if npc > 0 else name
		self.__List('get').append(MakeRow(('i', self.showVnum), title, TEXT_SHOP_PRICE % FormatYang(price),
				str(count), None, None, None))

	def OnMobInfo(self, level, rank, elements):
		if self.showKind != 'm':
			return
		self.mobInfo = (level, rank, elements)
		if level > 0:
			self.levels[self.showVnum] = level

	def OnPlace(self, mapIndex, kind, name):
		if self.showKind != 'm':
			return
		kindText = PLACE_KINDS[kind] if 0 <= kind < len(PLACE_KINDS) else ''
		self.__List('place').append(MakeRow(None, MapName(mapIndex, name), kindText, '', None, None, None))

	def OnShowEnd(self, kind, vnum):
		if kind != self.showKind or vnum != self.showVnum:
			return
		if kind == 'i':
			self.headerText.SetText(ItemName(vnum))
			self.infoFull = ItemDescription(vnum)
			FitText(self.infoText, self.infoFull, self.width - MARGIN * 2)
		else:
			level = self.levels.get(vnum, 0)
			name = MobName(vnum)
			if level > 0:
				name = '%s (Lv %d)' % (name, level)
			self.headerText.SetText(name)
			parts = []
			if self.mobInfo:
				mobLevel, rank, elements = self.mobInfo
				if mobLevel > 0 and level <= 0:
					parts.append(TEXT_LEVEL % mobLevel)
				if rank >= 4:
					parts.append(TEXT_BOSS)
				names = [ELEMENT_NAMES[i] for i in xrange(len(ELEMENT_NAMES)) if elements & (1 << i)]
				if names:
					parts.append(TEXT_ELEMENT % ', '.join(names))
			self.infoFull = ''
			self.infoText.SetText(TEXT_SEP.join(parts))
		self.__SetupTabs()

	def OnError(self, why):
		if why == 'short':
			self.__Status(TEXT_SHORT)
		elif why == 'busy':
			self.__Status(TEXT_BUSY)
		else:
			self.__Status(TEXT_BAD)
		self.pendingFind = None

	# -- the window ----------------------------------------------------------
	def Open(self):
		self.Show()
		self.SetTop()
		self.searchEdit.SetFocus()

	def Close(self):
		self.__HideTip()
		self.searchEdit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.Close()
		for row in self.rowWindows:
			row.Hide()
		self.rowWindows = []
		self.tabButtons = []
		self.widgets = []
		self.tooltipItem = None
		self.tooltipText = None


def GetWindow():
	if not _data['window']:
		_data['window'] = DropWikiWindow()
	return _data['window']


def ToggleWindow():
	wnd = GetWindow()
	if wnd.IsShow():
		wnd.Close()
	else:
		wnd.Open()


def OpenWindow():
	GetWindow().Open()


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


# game.py "DropWiki": the server's answers.
def OnCommand(sub='', *args):
	if sub == 'open':
		OpenWindow()
		return
	wnd = _data['window']
	if not wnd:
		return
	if sub == 'find_begin' and args:
		wnd.OnFindBegin(args[0])
	elif sub == 'match' and len(args) >= 2:
		wnd.OnMatch(_Int(args[0]), _Int(args[1]))
	elif sub == 'find_end' and len(args) >= 2:
		wnd.OnFindEnd(args[0], _Int(args[1]))
	elif sub == 'show_begin' and len(args) >= 2:
		wnd.OnShowBegin(args[0], _Int(args[1]))
	elif sub == 'row' and len(args) >= 5:
		wnd.OnRow(_Int(args[0]), _Int(args[1]), _Int(args[2]), _Int(args[3]), _Int(args[4]))
	elif sub == 'show_end' and len(args) >= 2:
		wnd.OnShowEnd(args[0], _Int(args[1]))
	elif sub == 'error' and args:
		wnd.OnError(args[0])
	# MT2009_PLUS_DROP_WIKI_V2
	elif sub == 'cube' and len(args) >= 8:
		wnd.OnCube(args[0], _Int(args[1]), args[2], _Int(args[3]), _Int(args[4]), _Int(args[5]), _Int(args[6]), args[7])
	elif sub == 'refine' and len(args) >= 5:
		wnd.OnRefine(args[0], _Int(args[1]), _Int(args[2]), _Int(args[3]), args[4])
	elif sub == 'chain' and len(args) >= 5:
		wnd.OnChain(_Int(args[0]), _Int(args[1]), _Int(args[2]), _Int(args[3]), _Int(args[4]))
	elif sub == 'chest' and len(args) >= 5:
		wnd.OnChest(args[0], _Int(args[1]), _Int(args[2]), _Int(args[3]), _Int(args[4]))
	elif sub == 'shop' and len(args) >= 3:
		wnd.OnShop(_Int(args[0]), _Int(args[1]), _Int(args[2]))
	elif sub == 'mob' and len(args) >= 3:
		wnd.OnMobInfo(_Int(args[0]), _Int(args[1]), _Int(args[2]))
	elif sub == 'place' and len(args) >= 3:
		wnd.OnPlace(_Int(args[0]), _Int(args[1]), args[2])
