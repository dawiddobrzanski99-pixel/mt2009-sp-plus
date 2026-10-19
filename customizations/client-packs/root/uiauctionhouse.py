# DOM AUKCYJNY (AH_V1) - okno klienta.
# Autor: Vekirion
#
# Wyszukiwarka ofert ze sklepow offline. Cale filtrowanie, sortowanie i strony
# liczy serwer (auction_house.cpp); okno wysyla komendy /ah_* i pokazuje jedna
# strone ofert naraz.
#
#   klient -> serwer : net.SendChatPacket("/ah_...")
#   serwer -> klient : komendy AH... (game.py -> OnServerCommand) oraz pakiet
#                      wynikow Ikarusa (SetSearchResultItems)
#
# Ograniczenia silnika: jedna komenda to najwyzej 256 znakow, a gracz ma 10
# komend na pol sekundy - stad COMMAND_MAX i kolejka wysylania.
#
# Indeksy kategorii (CATEGORY_DEFS) musza zgadzac sie z s_categories w
# auction_house.cpp.
import re
import ui
import ikashop
import item
import skill
import net
import app
import chat
import localeInfo
import localeinfo_point
import uiCommon
import wndMgr
import gamefont
import nonplayer		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: potwor marmuru polimorfii
from _weakref import proxy

# ---- uklad okna (do dopasowania) ---------------------------------------------
WINDOW_WIDTH_MAX = 880
WINDOW_WIDTH_MIN = 700		# ponizej tego kolumny ofert nachodza na siebie
WINDOW_WIDTH = WINDOW_WIDTH_MAX
SCREEN_MARGIN = 8			# tyle wolnego miejsca zostaje z kazdej strony ekranu
TASKBAR_RESERVE = 48		# dolny pasek gry (skroty, HP); okno go nie zaslania
FOOTER_HEIGHT = 44			# stopka pod lista ofert
SIDEBAR_X = 12
SIDEBAR_WIDTH = 176
CATEGORY_GAP = 1			# odstep miedzy przyciskami kategorii
SIDEBAR_GAP = 6				# odstep miedzy panelem kategorii a lista ofert
TOOLBAR_TOP = 30			# dolna krawedz belki tytulu
TOOLBAR_HEIGHT = 34			# wysokosc pola nazwy i przyciskow gornego paska
TOOLBAR_GAP = 10
MAIN_X = 200
MAIN_RIGHT = WINDOW_WIDTH - 12
ROW_WIDTH = MAIN_RIGHT - MAIN_X
ROW_HEIGHT_TARGET = 54		# docelowa wysokosc oferty; ApplyLayout dopasowuje ja o kilka px
ROW_HEIGHT = ROW_HEIGHT_TARGET
ROWS_PER_PAGE = 8
HEADER_HEIGHT = 24			# pasek naglowkow kolumn
ROWS_Y = 112
HEADER_Y = ROWS_Y - HEADER_HEIGHT - 4
SIDEBAR_PAD = 4				# ramka panelu kategorii wokol przyciskow
SIDEBAR_Y = ROWS_Y				# ramka panelu kategorii zaczyna sie rowno z ramka pierwszej oferty
FOOTER_Y = ROWS_Y + ROWS_PER_PAGE * ROW_HEIGHT + 14		# strony i liczba ofert
WINDOW_HEIGHT = FOOTER_Y + 34
SIDEBAR_HEIGHT = WINDOW_HEIGHT - SIDEBAR_Y - 10
CHECK_SIZE = 16
# zaznaczenie oferty: obrazek (32x32 w pliku) pomniejszony do SELECT_SIZE, a na
# nim drugi, gdy oferta jest zaznaczona
SELECT_IMAGE = "mt2009_ui/auctionhouse/choice.tga"
SELECT_MARK_IMAGE = "mt2009_ui/auctionhouse/selected.tga"
SELECT_SIZE = 20			# o 25% wiecej niz dawna kratka 16 px
# okno bonusow: tlo nazwy przedmiotu, tlo pozycji listy, usuwanie wybranego bonusu
BONUS_CONTEXT_IMAGE = "mt2009_ui/goblin/event/gold_count_bg.tga"
BONUS_ROW_IMAGE = "mt2009_ui/ranking/header_small.png"
REMOVE_IMAGE = "mt2009_ui/auctionhouse/red_x.tga"
REMOVE_HOVER_IMAGE = "mt2009_ui/auctionhouse/gray_x.tga"	# po najechaniu
REMOVE_SIZE = SELECT_SIZE	# jak zaznaczenie w ofertach
MODE_SIZE = 25				# zaznaczenia Rowno / Przynajmniej / Maksymalnie
ALL_NAMES_OPTION = "ah_allnames"	# klucze opcji w uiopcjedodatkowe.py
WHITE_TEXT_OPTION = "ah_white"		# bialy zamiast kremowego koloru napisow
SORT_TOTAL_OPTION = "ah_sorttotal"	# sortuj po cenie calej oferty zamiast za sztuke
OPTIONS_POLL = 0.5			# co tyle sekund okno sprawdza, czy opcje sie zmienily
BONUS_REFRESH_GAP = 3.0		# najczestsze ponowne pytanie o tabele bonusow
TOOLBAR_FONT_EXTRA = 3		# o tyle punktow wieksze napisy przyciskow gornego paska
NAMES_DELAY = 0.2			# po tylu sekundach od ostatniej litery idzie pytanie o podpowiedzi
SEARCH_FONT_EXTRA = 4		# o ile punktow tekst w polu nazwy jest wiekszy od duzej czcionki gry
BUY_X = 8					# przycisk "Kup" przy lewej krawedzi oferty
BUY_BUTTON_WIDTH = 61
SELECT_RIGHT = 12			# zaznaczenie: odleglosc od prawej krawedzi oferty
ICON_BOX = 40
ICON_X = BUY_X + BUY_BUTTON_WIDTH + 6
ICON_SCALE_MAX = 1.0		# ikony nie sa powiekszane; wysokie sa zmniejszane do ramki
# Wyjatki: przedmioty z mala grafika na ikonie sa powiekszane tyle razy
# (nazwa typu i podtypu z modulu item -> powiekszenie). Dopisz kolejne w razie potrzeby.
ICON_ZOOM = (
	("ITEM_TYPE_ARMOR", "ARMOR_EAR", 1.2),
	("ITEM_TYPE_ARMOR", "ARMOR_NECK", 1.2),
	("ITEM_TYPE_ARMOR", "ARMOR_WRIST", 1.2),
)
TEXT_X = ICON_X + ICON_BOX + 8
TEXT_LINE = 14				# wysokosc linii zwyklej czcionki (bonusy, cena za sztuke)
TEXT_LINE_LARGE = 16		# ...i duzej (nazwa, ilosc, sprzedawca, cena)
# kolumny wiersza, liczone od jego prawej krawedzi: ilosc i cena koncza sie w
# podanej odleglosci, sprzedawca sie w niej zaczyna
COUNT_RIGHT = 300
SELLER_LEFT = 284
PRICE_RIGHT = 46
ROW_BONUS_LINES = 2			# ile bonusow widac w wierszu

COLOR_PLUS_LOW = 0xFF9A9A9A		# +0
COLOR_PLUS_MID = 0xFF6EDC82		# +1 .. +6
COLOR_PLUS_HIGH = 0xFFFFD56A	# +7 i wyzej
REFINE_MAX = 9
COLOR_OPTION_FILL = 0x80000000		# wybor na liscie: tlo jak w ofercie
COLOR_OPTION_BORDER = 0xFF6A665C	# ...i cienka ramka
COLOR_OPTION_HOVER = 0x306EDC82		# podswietlenie wyboru
COLOR_OPTION_SELECTED = 0x706EDC82	# aktualnie ustawiona wartosc
# Tlo pod ikona: zlota ramka wycieta z windows.dds (227,0 - 278,53) i zapisana
# jako gotowy obrazek 40 x 40. Ramka ma przezroczysty srodek, wiec pod nia lezy wypelnienie,
# cofniete od krawedzi, zeby nie wystawalo za zaokraglone rogi.
COLOR_ICON_BACK = 0xFF3F3A33		# wypelnienie srodka ramki
ICON_BACK_INSET = 3				# o tyle wypelnienie jest cofniete od krawedzi ramki
ICON_SLOT_IMAGE = "mt2009_ui/auctionhouse/icon_frame.tga"	# 40 x 40, jak ICON_BOX
COLOR_TITLE_BUTTON = 0xFFE8D9B0		# napis przycisku na belce tytulu
COLOR_BUY_BORDER = 0xFFB8974A		# zlota ramka przyciskow zakupu
COLOR_BUY_TEXT = 0xFFFFD56A
BUY_SELECTED_WIDTH = 146
BUY_BULK_WIDTH = 112
PAGER_BUTTON = 28				# przyciski stron
PAGER_BOX = 76					# ramka z numerem strony
PAGER_HEIGHT = 20
# (nazwa, numer klasy dla serwera); 0 = dowolna
CLASS_DEFS = (("Wszystkie", 0), ("Wojownik", 1), ("Ninja", 2), ("Sura", 3), ("Szaman", 4))
# duzy przycisk (kategorie, Poziom, Bonus, Kup wybrane)
BIG_BUTTON = "d:/ymir work/ui/flamewind/public/big_button_%02d.sub"
# ksiega umiejetnosci (vnum 50300) ma wlasny obrazek dla kazdej umiejetnosci z
# gniazda 0 - te same pliki, ktorych uzywa skillbookicon.py
SKILLBOOK_VNUM = 50300
SKILLBOOK_ICON = "playerbot_ui/skillbook/%d.tga"
COLOR_OPTION_LINE = 0xFFB8A57C		# ciemnokremowa belka miedzy wyborami
OPTION_SEPARATORS = True

COLOR_TEXT = 0xFFEDEDED
COLOR_DIM = 0xFF9A9A9A
COLOR_GOLD = 0xFFFFD56A
COLOR_GREEN = 0xFF6EDC82
COLOR_HEAD = 0xFFE8E8E8
COLOR_BONUS = 0xFF8FD6FF
COLOR_CARD_BORDER = 0xFF4A4A4A
COLOR_CARD_FILL = 0xE0101010

# ---- protokol ----------------------------------------------------------------
COMMAND_MAX = 250
SEARCH_DELAY = 0.35			# po wpisaniu litery
SEARCH_GAP = 0.2			# miedzy zapytaniami
SEARCH_TIMEOUT = 4.0
SEND_GAP = 0.3				# kolejka komend: paczka co tyle sekund
SEND_BATCH = 3
JOB_TIMEOUT = 20.0
WHEEL_GAP = 0.09
BONUS_MAX = 7
BULK_MAX = 100000

SORT_PRICE = 0
SORT_UNIT_PRICE = 1
SORT_COUNT = 2

BONUS_EQUAL = 0
BONUS_AT_LEAST = 1
BONUS_AT_MOST = 2

JOB_SINGLE = 0
JOB_CART = 1
JOB_BULK = 2

BUY_REASONS = {
	1: "oferta zosta\xb3a ju\xbf sprzedana",
	2: "zmieni\xb3a si\xea cena albo ilo\x9c\xe6",
	3: "sklep odm\xf3wi\xb3 sprzeda\xbfy",
	4: "kto\x9c by\xb3 szybszy",
	5: "serwer nie potwierdzi\xb3 zakupu",
}

STOP_REASONS = {
	1: "Zakupy przerwane.",
	2: "Zabrak\xb3o Yang.",
	3: "Brak miejsca w ekwipunku.",
	4: "Serwer nie potwierdzi\xb3 zakupu - sprawd\x9f ekwipunek.",
	5: "Dom Aukcyjny dzia\xb3a tylko w M1.",
	6: "Poprzednie zakupy jeszcze trwaj\xb9.",
	7: "Nie ma nic do kupienia.",
	8: "Wycena wygas\xb3a - wyce\xf1 ponownie.",
	9: "Dom Aukcyjny jest wy\xb3\xb9czony.",
	10: "Limit zakup\xf3w na minut\xea - doko\xf1cz za chwil\xea.",
}

# zestawy bonusow z item_attr: kolejnosc kolumn, ktore wysyla serwer
SET_WEAPON = 0
SET_BODY = 1
SET_WRIST = 2
SET_FOOTS = 3
SET_NECK = 4
SET_HEAD = 5
SET_SHIELD = 6
SET_EAR = 7

# (nazwa, indeks rodzica albo -1, zestaw bonusow albo None) - indeks = pozycja
CATEGORY_DEFS = (
	("Wszystko", -1, None),
	("Bro\xf1", -1, SET_WEAPON),
	("Miecze jednor\xeaczne", 1, SET_WEAPON),
	("Miecze dwur\xeaczne", 1, SET_WEAPON),
	("\xa3uki", 1, SET_WEAPON),
	("Sztylety", 1, SET_WEAPON),
	("Dzwony", 1, SET_WEAPON),
	("Wachlarze", 1, SET_WEAPON),
	("Zbroje", -1, SET_BODY),
	("Zbroje - Wojownik", 8, SET_BODY),
	("Zbroje - Ninja", 8, SET_BODY),
	("Zbroje - Sura", 8, SET_BODY),
	("Zbroje - Szaman", 8, SET_BODY),
	("He\xb3my", -1, SET_HEAD),
	("He\xb3my - Wojownik", 13, SET_HEAD),
	("He\xb3my - Ninja", 13, SET_HEAD),
	("He\xb3my - Sura", 13, SET_HEAD),
	("He\xb3my - Szaman", 13, SET_HEAD),
	("Tarcze", -1, SET_SHIELD),
	("Buty", -1, SET_FOOTS),
	("Bransolety", -1, SET_WRIST),
	("Naszyjniki", -1, SET_NECK),
	("Kolczyki", -1, SET_EAR),
	("Ksi\xeagi", -1, None),
	("Ksi\xeagi zapomnienia", -1, None),
	("Kamienie duszy", -1, None),
	("Rudy i przetopy", -1, None),
	("Dopalacze", -1, None),
	("U\xbfywalne", -1, None),
	("Ulepszacze", -1, None),
	("Inne", -1, None),
	# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: kategorie z Domu Towarowego - na koncu, bo indeksy
	# sa wspolne z serwerem (stary klient dalej trafia w swoje kategorie)
	("Smocza Alchemia", -1, None),		# 31: kamienie smoka i Cory Draconis
	("Polimorfia", -1, None),			# 32: marmury polimorfii
)

# Kategorie pokazywane w panelu, w tej kolejnosci (indeksy z CATEGORY_DEFS).
# Rodzaje broni stoja wprost zamiast "Bro\xf1", a Zbroje i Helmy nie maja juz
# podzialu na klasy - od tego jest przycisk "Klasa".
# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: Smocza Alchemia i Polimorfia stoja tam, gdzie w Domu Towarowym.
CATEGORY_VISIBLE = (0, 2, 3, 4, 5, 6, 7, 8, 13, 18, 19, 20, 21, 22, 23, 24, 31, 25, 26, 27, 28, 29, 32, 30)

BOOK_VNUMS = (50300, 70037, 70055)
# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: marmury polimorfii nosza vnum potwora w gniezdzie 0 -
# oferta nazywa sie "<marmur> - <potwor>"
POLYMORPH_VNUMS = (70104, 70105, 70106, 70107, 71093)
MARBLE_VNUM = 70104
# plec w filtrze: (napis, numer dla serwera)
SEX_DEFS = (("Dowolna", 0), ("Kobieta", 1), ("M\xea\xbfczyzna", 2))
# Umiejetnosci, ktore maja ksiegi. skill.GetSkillName dla nieznanego numeru psuje
# interpreter, wiec pytamy tylko o te.
SKILL_IDS = tuple(range(1, 6) + range(16, 21) + range(31, 36) + range(46, 51) + range(61, 67) + range(76, 82) + range(91, 97) + range(106, 112))

_PL_LOWER_MAP = {
	'\xa5': '\xb9', '\xc6': '\xe6', '\xca': '\xea', '\xa3': '\xb3',
	'\xd1': '\xf1', '\xd3': '\xf3', '\x8c': '\x9c', '\x8f': '\x9f', '\xaf': '\xbf',
}

def PolishLower(text):
	# nazwy sa w CP1250, a str.lower() zna tylko A-Z
	lowered = text.lower()
	return "".join([_PL_LOWER_MAP.get(ch, ch) for ch in lowered])

def ApplyLayout(buttonWidth, buttonHeight):
	# Uklad zalezy od grafiki przycisku kategorii i od rozdzielczosci gry. Panel
	# kategorii ma szerokosc przycisku, lista ofert stoi tuz za nim. Pasek
	# naglowkow ma wysokosc i polozenie przycisku "Klasa", a ramki ofert zaczynaja
	# sie i koncza rowno z ramka panelu.
	# Na duzym ekranie panel miesci wszystkie kategorie. Gdy okno nie zmiesciloby
	# sie w grze, jest nizsze (mniej ofert na stronie, kategorie przewijane
	# kolkiem) i wezsze (krotsza kolumna nazwy).
	global WINDOW_WIDTH, MAIN_RIGHT
	global SIDEBAR_WIDTH, SIDEBAR_HEIGHT, MAIN_X, ROW_WIDTH, ROW_HEIGHT, ROWS_PER_PAGE
	global HEADER_HEIGHT, HEADER_Y, FOOTER_Y, WINDOW_HEIGHT
	screenWidth, screenHeight = WINDOW_WIDTH_MAX, 100000
	try:
		screenWidth = wndMgr.GetScreenWidth()
		screenHeight = wndMgr.GetScreenHeight()
	except:
		pass
	WINDOW_WIDTH = max(WINDOW_WIDTH_MIN, min(WINDOW_WIDTH_MAX, screenWidth - 2 * SCREEN_MARGIN))
	MAIN_RIGHT = WINDOW_WIDTH - 12
	SIDEBAR_WIDTH = buttonWidth + 2 * SIDEBAR_PAD
	MAIN_X = SIDEBAR_X + SIDEBAR_WIDTH + SIDEBAR_GAP
	ROW_WIDTH = MAIN_RIGHT - MAIN_X
	HEADER_HEIGHT = buttonHeight
	HEADER_Y = SIDEBAR_Y - buttonHeight - 3
	needed = len(CATEGORY_VISIBLE) * (buttonHeight + CATEGORY_GAP) - CATEGORY_GAP + 2 * SIDEBAR_PAD
	# tyle wysokosci moze miec panel, zeby okno ze stopka zmiescilo sie na ekranie
	room = screenHeight - TASKBAR_RESERVE - 2 * SCREEN_MARGIN - SIDEBAR_Y - FOOTER_HEIGHT
	if needed <= room:
		# Oferty wypelniaja wysokosc panelu: tyle wierszy, ile wychodzi przy
		# docelowej wysokosci (serwer daje najwyzej 20 na strone), po czym wysokosc
		# wiersza jest zaokraglana w gore, a panel wydluzany o brakujace piksele.
		space = needed + 2
		ROWS_PER_PAGE = max(4, min(20, int(float(space) / ROW_HEIGHT_TARGET + 0.5)))
		ROW_HEIGHT = (space + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
	else:
		# maly ekran: tyle calych ofert, ile sie miesci
		ROW_HEIGHT = ROW_HEIGHT_TARGET
		ROWS_PER_PAGE = max(3, min(20, (room + 2) // ROW_HEIGHT))
	SIDEBAR_HEIGHT = ROWS_PER_PAGE * ROW_HEIGHT - 2
	FOOTER_Y = SIDEBAR_Y + SIDEBAR_HEIGHT + 10
	WINDOW_HEIGHT = FOOTER_Y + FOOTER_HEIGHT - 10

_PLUS_RE = re.compile(r'^(.*?)(\+\d+)$')

def SplitPlus(name):
	# "Miecz+9" -> ("Miecz", "+9")
	match = _PLUS_RE.match(name)
	if match:
		return match.group(1), match.group(2)
	return name, ""

def RefineLabel(value):
	return "-" if value < 0 else "+%d" % value

_iconZoom = None

def GetIconZoom(itemType, subType):
	# powiekszenie ikony dla typu przedmiotu z ICON_ZOOM, albo None
	global _iconZoom
	if _iconZoom is None:
		_iconZoom = {}
		for typeName, subName, zoom in ICON_ZOOM:
			typeValue = getattr(item, typeName, None)
			subValue = getattr(item, subName, None)
			if typeValue is not None and subValue is not None:
				_iconZoom[(typeValue, subValue)] = zoom
	return _iconZoom.get((itemType, subType))

def Option(key):
	# opcja z "Opcje Gry" -> "Dodatkowe" (uiopcjedodatkowe.py)
	try:
		import uiopcjedodatkowe
		return bool(uiopcjedodatkowe.Settings().get(key, False))
	except:
		return False

def AllNamesMode():
	# podpowiadaj wszystkie nazwy przedmiotow
	return Option(ALL_NAMES_OPTION)

def PriceSortColumn():
	# kolumna "Cena" sortuje po cenie za sztuke (oferta 2 szt. za 150 jest przed
	# 1 szt. za 100), a z wlaczona opcja po cenie calej oferty
	return SORT_PRICE if Option(SORT_TOTAL_OPTION) else SORT_UNIT_PRICE

def ToInt(text, default=0):
	try:
		return int(text)
	except:
		return default

def Money(value):
	return localeInfo.NumberToMoneyString(value)

def PartPrice(price, count, quantity):
	# czesc stosu kosztuje swoj udzial w cenie, zaokraglony w gore - tak liczy serwer
	count = max(1, count)
	quantity = max(1, min(quantity, count))
	return (price * quantity + count - 1) // count

_FORMAT_RE = re.compile(r'[+-]?%[-+ #0-9.]*[a-zA-Z]|%%')

def GetBonusLabel(applyType):
	# nazwa bonusu z tekstu dymka ("Maks. PZ +%d" -> "Maks. PZ")
	text = localeinfo_point.AFFECT_DICT.get(applyType)
	if callable(text):
		try:
			text = text.func_closure[0].cell_contents
		except:
			text = None
	if not isinstance(text, str):
		return "Bonus nr %d" % applyType
	text = _FORMAT_RE.sub("", text)
	text = " ".join(text.split()).strip(" :+-.")
	return text or "Bonus nr %d" % applyType

def GetItemAttrSet(vnum):
	# zestaw bonusow przedmiotu, tak jak wybiera go serwer (typ i podtyp)
	try:
		item.SelectItem(vnum)
		itemType = item.GetItemType()
		subType = item.GetItemSubType()
	except:
		return None
	if itemType == getattr(item, "ITEM_TYPE_WEAPON", 1):
		return SET_WEAPON
	if itemType == getattr(item, "ITEM_TYPE_ARMOR", 2):
		return {
			getattr(item, "ARMOR_BODY", 0): SET_BODY,
			getattr(item, "ARMOR_HEAD", 1): SET_HEAD,
			getattr(item, "ARMOR_SHIELD", 2): SET_SHIELD,
			getattr(item, "ARMOR_WRIST", 3): SET_WRIST,
			getattr(item, "ARMOR_FOOTS", 4): SET_FOOTS,
			getattr(item, "ARMOR_NECK", 5): SET_NECK,
			getattr(item, "ARMOR_EAR", 6): SET_EAR,
		}.get(subType)
	return None


# ---- male kontrolki ----------------------------------------------------------
def MakeBar(parent, x, y, width, height, color):
	bar = ui.Bar()
	bar.SetParent(parent)
	bar.SetPosition(x, y)
	bar.SetSize(width, height)
	bar.SetColor(color)
	bar.AddFlag("not_pick")
	bar.Show()
	return bar

# Wszystkie napisy okna sa pisane jak naglowek "Atrybuty" w oknie postaci: duza
# czcionka gry, pogrubiona. Opcja gry (Dodatkowe) przelacza kolor
# zwyklych napisow miedzy kremowym a bialym; wybor zapisuje sie w pliku.
# Napisy w innych kolorach (zloto cen, bonusy, szare podpisy) zostaja swoje.
COLOR_CREAM = 0xFFEFE3BD
CREAM_STYLE = True

def SyncTextStyle():
	# kolor zwyklych napisow wg opcji gry; True, gdy sie zmienil
	global CREAM_STYLE
	cream = not Option(WHITE_TEXT_OPTION)
	if cream == CREAM_STYLE:
		return False
	CREAM_STYLE = cream
	return True

def MainColor():
	# kolor zwyklych napisow
	return COLOR_CREAM if CREAM_STYLE else COLOR_TEXT

# napisy w kolorze zwyklym, do przemalowania po przelaczeniu
_mainLines = []

def RegisterMain(line):
	try:
		_mainLines.append(proxy(line))
	except TypeError:
		_mainLines.append(line)

def RecolorMain():
	color = MainColor()
	alive = []
	for line in _mainLines:
		try:
			line.SetPackedFontColor(color)
			alive.append(line)
		except:
			pass		# napis juz nie istnieje
	_mainLines[:] = alive

def FontName(extra=0, large=True):
	# Pogrubiona czcionka gry: duza albo zwykla, powiekszona o podana liczbe
	# punktow. Nazwa czcionki to "Nazwa:rozmiar", a "b" na koncu to pogrubienie.
	# Czcionke trzeba ustawic PRZED pierwszym napisem - zmieniona na gotowym
	# napisie rozsypuje znaki.
	font = gamefont.GetCurrentFontLarge() if large else gamefont.GetCurrentFont()
	if extra:
		name, size = font.rsplit(":", 1)
		font = "%s:%d" % (name, int(size) + extra)
	return font + "b"

def BigFontName():
	return FontName()

def BigFontColor():
	return MainColor()

def MakeScaledImage(parent, x, y, fileName, width, height):
	# obrazek rozciagniety do podanych wymiarow, przezroczysty dla myszy
	image = ui.ExpandedImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.AddFlag("not_pick")
	# Brakujacego pliku nie wolno nawet probowac wczytac: klient zglasza wtedy
	# blad dopiero przy nastepnej operacji i psuje budowe calego okna.
	try:
		exists = app.IsExistFile(fileName)
	except:
		exists = True
	if not exists:
		image.Hide()
		return image
	try:
		image.LoadImage(fileName)
		if image.GetWidth() > 0 and image.GetHeight() > 0:
			image.SetScale(float(width) / image.GetWidth(), float(height) / image.GetHeight())
	except:
		pass
	image.Show()
	return image

def SetButtonText(button, text, bigButton=False):
	# pierwszy napis przycisku: czcionka razem z napisem, kolor zwykly
	try:
		button.SetText(text, font=FontName())
		button.ButtonText.SetPackedFontColor(MainColor())
		RegisterMain(button.ButtonText)
	except:
		button.SetText(text)

def MakeText(parent, x, y, text="", color=None, large=True, extra=0):
	# color None (albo dawne COLOR_TEXT / COLOR_HEAD) to kolor zwykly, przelaczany
	# opcja gry; large=False to zwykly rozmiar czcionki (drobne napisy ofert)
	line = ui.TextLine()
	line.SetParent(parent)
	try:
		line.SetFontName(FontName(extra, large))
	except:
		pass
	line.SetPosition(x, y)
	if color is None or color in (COLOR_TEXT, COLOR_HEAD):
		line.SetPackedFontColor(MainColor())
		RegisterMain(line)
	else:
		line.SetPackedFontColor(color)
	line.SetText(text)
	line.AddFlag("not_pick")
	line.Show()
	return line

def FitText(line, text, maxWidth):
	# napis, ktory nie miesci sie w podanej szerokosci, jest skracany i konczy
	# sie wielokropkiem
	line.SetText(text)
	try:
		if maxWidth <= 0 or line.GetTextSize()[0] <= maxWidth:
			return
		low, high = 0, len(text)
		while low < high:
			middle = (low + high + 1) // 2
			line.SetText(text[:middle].rstrip() + "...")
			if line.GetTextSize()[0] <= maxWidth:
				low = middle
			else:
				high = middle - 1
		line.SetText(text[:low].rstrip() + "...")
	except:
		line.SetText(text)

def MakeButton(parent, x, y, width, text, event, *args):
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	# tekstury przyciskow maja staly rozmiar (43, 61 i 88 x 21), wiec bierzemy pasujaca
	if width < 55:
		name = "small"
	elif width < 80:
		name = "middle"
	else:
		name = "large"
	button.SetUpVisual("d:/ymir work/ui/public/%s_button_01.sub" % name)
	button.SetOverVisual("d:/ymir work/ui/public/%s_button_02.sub" % name)
	button.SetDownVisual("d:/ymir work/ui/public/%s_button_03.sub" % name)
	SetButtonText(button, text)
	button.SetEvent(event, *args)
	button.Show()
	return button

# ---- podpisy przyciskow -------------------------------------------------------
# Jak w ekwipunku: po najechaniu na przycisk nad nim pojawia sie krotki podpis.
# Jedno wspolne okienko na najwyzszej warstwie, zeby nie chowalo sie pod
# sasiednimi elementami. Przycisk dostaje podpis przez SetHint(przycisk, tekst).
_hintWindow = None

class HintWindow(ui.Window):
	def __init__(self):
		ui.Window.__init__(self, "TOP_MOST")
		self.owner = None
		self.AddFlag("not_pick")
		self.AddFlag("float")
		self.back = MakeBar(self, 0, 0, 10, 10, 0xD0000000)
		self.text = ui.TextLine()
		self.text.SetParent(self)
		try:
			self.text.SetFontName(FontName(0, False))
		except:
			pass
		self.text.SetPosition(6, 3)
		self.text.SetPackedFontColor(0xFFFFFFFF)
		self.text.SetOutline()
		self.text.AddFlag("not_pick")
		self.text.Show()
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def ShowFor(self, owner, text):
		try:
			self.owner = proxy(owner)
		except TypeError:
			self.owner = owner
		self.text.SetText(text)
		try:
			textWidth, textHeight = self.text.GetTextSize()
		except:
			textWidth, textHeight = 8 * len(text), TEXT_LINE
		width, height = textWidth + 12, textHeight + 7
		self.SetSize(width, height)
		self.back.SetSize(width, height)
		x, y = owner.GetGlobalPosition()
		x += (owner.GetWidth() - width) // 2
		top = y - height - 3
		if top < 0:
			top = y + owner.GetHeight() + 3		# brak miejsca u gory: pod przyciskiem
		try:
			x = max(2, min(wndMgr.GetScreenWidth() - width - 2, x))
		except:
			pass
		self.SetPosition(x, top)
		self.Show()
		self.SetTop()

	def Close(self):
		self.owner = None
		self.Hide()

	def IsOwner(self, owner):
		try:
			return self.owner is not None and self.owner.hWnd == owner.hWnd
		except:
			return False

	def OnUpdate(self):
		# przycisk schowany pod kursorem nie dostaje OnMouseOverOut
		try:
			if self.owner is None or not self.owner.IsShow() or not self.owner.IsIn():
				self.Close()
		except:
			self.Close()

def SetHint(widget, text):
	widget.hintText = text
	return widget

def ShowHint(widget):
	global _hintWindow
	text = getattr(widget, "hintText", None)
	if not text:
		return
	try:
		if _hintWindow is None:
			_hintWindow = HintWindow()
		_hintWindow.ShowFor(widget, text)
	except:
		pass

def HideHint(widget=None):
	# bez argumentu chowa zawsze; z przyciskiem tylko jego wlasny podpis
	try:
		if _hintWindow and (widget is None or _hintWindow.IsOwner(widget)):
			_hintWindow.Close()
	except:
		pass

def DestroyHint():
	global _hintWindow
	if _hintWindow:
		_hintWindow.Close()
		_hintWindow = None

class BigButton(ui.Button):
	# duzy przycisk; prawy klik ma wlasne zdarzenie (czyszczenie filtra)
	def __init__(self):
		ui.Button.__init__(self)
		self.rightEvent = None

	def __del__(self):
		ui.Button.__del__(self)

	def SetRightEvent(self, event):
		self.rightEvent = event

	def OnMouseRightButtonUp(self):
		if self.rightEvent:
			self.rightEvent()
		return True

def MakeBigButton(parent, x, y, text, event, rightEvent=None):
	button = BigButton()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(BIG_BUTTON % 1)
	button.SetOverVisual(BIG_BUTTON % 2)
	button.SetDownVisual(BIG_BUTTON % 3)
	SetButtonText(button, text, True)
	button.SetEvent(event)
	button.SetRightEvent(rightEvent)
	button.Show()
	return button

def MakeTextButton(parent, x, y, width, height, text, event, *args):
	# sam tekst, bez tekstury - tekstury przyciskow maja wlasny minimalny rozmiar
	button = ui.Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetSize(width, height)
	SetButtonText(button, text)
	button.SetEvent(event, *args)
	button.Show()
	return button

class SuggestionBox(ui.Window):
	# Podpowiedzi nazw pod polem wyszukiwania: ciemny panel w ramce, wiersze z
	# podswietleniem i pasek przewijania po prawej (takze kolko myszy).
	ROWS = 8
	LINE = 20
	SCROLL_WIDTH = 17

	def __init__(self, width, event):
		ui.Window.__init__(self)
		self.event = event
		self.width = width
		self.names = []
		self.offset = 0
		self.scrolling = False
		self.fill = MakeBar(self, 1, 1, width - 2, 1, 0xF20C0C0C)
		self.borders = [MakeBar(self, 0, 0, 1, 1, COLOR_OPTION_BORDER) for index in xrange(4)]
		self.rows = []
		for index in xrange(self.ROWS):
			row = ListButton(width - 4, self.LINE - 1, ui.__mem_func__(self.__OnClick), index)
			row.SetParent(self)
			row.SetPosition(2, 2 + index * self.LINE)
			row.Hide()
			self.rows.append(row)
		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(width - self.SCROLL_WIDTH - 2, 2)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar.Hide()
		self.AddFlag("float")
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def SetNames(self, names):
		self.names = list(names)
		self.offset = 0
		shown = min(len(self.names), self.ROWS)
		height = shown * self.LINE + 3
		self.SetSize(self.width, height)
		self.fill.SetSize(self.width - 2, height - 2)
		for bar, (x, y, w, h) in zip(self.borders, ((0, 0, self.width, 1), (0, height - 1, self.width, 1), (0, 0, 1, height), (self.width - 1, 0, 1, height))):
			bar.SetPosition(x, y)
			bar.SetSize(w, h)
		if len(self.names) > self.ROWS:
			self.scrolling = True
			self.scrollBar.SetScrollBarSize(height - 4)
			self.scrollBar.SetMiddleBarSize(float(self.ROWS) / len(self.names))
			self.scrollBar.SetPos(0.0)
			self.scrolling = False
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		self.__Refresh()

	def __Refresh(self):
		for index, row in enumerate(self.rows):
			nameIndex = self.offset + index
			if nameIndex < len(self.names):
				row.SetLabel(self.names[nameIndex])
				row.Show()
			else:
				row.Hide()

	def __MaxOffset(self):
		return max(0, len(self.names) - self.ROWS)

	def __OnScroll(self):
		if self.scrolling:
			return
		self.offset = int(self.scrollBar.GetPos() * self.__MaxOffset() + 0.5)
		self.__Refresh()

	def OnMouseWheel(self, length):
		limit = self.__MaxOffset()
		if limit > 0:
			self.offset = max(0, min(limit, self.offset + (-2 if length > 0 else 2)))
			self.scrolling = True
			self.scrollBar.SetPos(float(self.offset) / limit)
			self.scrolling = False
			self.__Refresh()
		return True

	def __OnClick(self, index):
		nameIndex = self.offset + index
		if nameIndex < len(self.names) and self.event:
			self.event(self.names[nameIndex])


class SearchEditLine(ui.EditLine):
	# Pole nazwy: Ctrl+A zaznacza caly tekst (nastepny klawisz go zastepuje,
	# Backspace i Delete kasuja), a prawy klik czysci pole.
	def __init__(self):
		ui.EditLine.__init__(self)
		self.allSelected = False
		self.rightEvent = None
		self.basePos = None
		self.viewWidth = 0
		self.measure = None
		self.selectionBar = ui.Bar()
		self.selectionBar.SetParent(self)
		self.selectionBar.SetPosition(0, 0)
		self.selectionBar.SetColor(0x604A91D1)
		self.selectionBar.AddFlag("not_pick")
		self.selectionBar.Hide()

	def __del__(self):
		ui.EditLine.__del__(self)

	def SetRightEvent(self, event):
		self.rightEvent = event

	# Dluga nazwa nie wychodzi poza pole: napis jest przycinany do pola (mask),
	# a gdy sie nie miesci, przesuwa sie w lewo tak, zeby przy pisaniu bylo widac
	# koniec; bez kursora w polu widac poczatek nazwy.
	def SetView(self, x, y, width, mask, measure=None):
		self.basePos = (x, y)
		self.viewWidth = width
		self.measure = measure
		try:
			self.SetClippingMaskWindow(mask)
			self.selectionBar.SetClippingMaskWindow(mask)
		except:
			pass
		self.AdjustView()

	def AdjustView(self):
		# MT2009_PLUS_AUCTION_HOUSE_PLACEHOLDER_V1: napis "Nazwa przedmiotu" tylko
		# przy pustym polu (nazwa wpisana z podpowiedzi albo z oferty go nie ukrywala)
		placeholder = getattr(self, "placeholderTextLine", None)
		if placeholder:
			if self.GetText() or self.IsFocus():
				placeholder.Hide()
			else:
				placeholder.Show()
		if not self.basePos:
			return
		try:
			textWidth = self.GetTextSize()[0]
		except:
			return
		shift = 0
		if self.IsFocus():
			shift = self.__ScrollShift(max(0, textWidth + 6 - self.viewWidth))
		ui.EditLine.SetPosition(self, self.basePos[0] - shift, self.basePos[1])
		self.SetSize(max(self.viewWidth, textWidth + 6), self.GetHeight())

	def __ScrollShift(self, need):
		# Przesuniecie zawsze o cale litery: pierwsza widoczna litera zaczyna sie
		# dokladnie na poczatku pola. Litera przecieta przycieciem w polowie
		# wygladala na cienka; to, co zostaje na marginesie z lewej, zakrywa
		# zaslona w kolorze pola (MakeEdit).
		if need <= 0 or not self.measure:
			return need
		text = self.GetText()
		try:
			for length in xrange(1, len(text) + 1):
				self.measure.SetText(text[:length])
				width = self.measure.GetTextSize()[0]
				if width >= need:
					return width
		except:
			pass
		return need

	def SetText(self, text):
		ui.EditLine.SetText(self, text)
		self.AdjustView()

	def OnSetFocus(self):
		ui.EditLine.OnSetFocus(self)
		self.AdjustView()

	def ClearSelection(self):
		self.allSelected = False
		self.selectionBar.Hide()

	def __SelectAll(self):
		if not self.GetText():
			return
		self.allSelected = True
		self.selectionBar.SetSize(self.GetWidth(), self.GetHeight())
		self.selectionBar.Show()
		self.AdjustView()

	def OnIMEKeyDown(self, key):
		if self.IsFocus():
			control = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
			if control and key == 0x41:		# A
				self.__SelectAll()
				return True
			if self.allSelected and key not in (0x10, 0x11, 0x12):		# Shift, Ctrl, Alt
				if key in (0x25, 0x27, 0x24, 0x23, 0x1B, 0x0D):		# strzalki, Home, End, Esc, Enter
					self.ClearSelection()
				else:
					self.SetText("")
					self.ClearSelection()
					if key in (0x08, 0x2E):		# Backspace, Delete
						self.OnIMEUpdate()
						return True
		return ui.EditLine.OnIMEKeyDown(self, key)

	def OnKeyDown(self, key):
		control = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
		if control and key == app.DIK_A:
			self.__SelectAll()
			return True
		modifiers = (app.DIK_LCONTROL, app.DIK_RCONTROL, app.DIK_LSHIFT, app.DIK_RSHIFT, app.DIK_LALT)
		if self.allSelected and key not in modifiers:
			if key in (app.DIK_LEFT, app.DIK_RIGHT, app.DIK_HOME, app.DIK_END, app.DIK_ESCAPE, app.DIK_RETURN):
				self.ClearSelection()
			else:
				self.SetText("")
				self.ClearSelection()
				self.OnIMEUpdate()
				if key in (app.DIK_BACK, app.DIK_DELETE):
					return True
		return ui.EditLine.OnKeyDown(self, key)

	def OnKillFocus(self):
		self.ClearSelection()
		ui.EditLine.OnKillFocus(self)
		self.AdjustView()

	def OnMouseLeftButtonDown(self):
		self.ClearSelection()
		return ui.EditLine.OnMouseLeftButtonDown(self)

	def OnMouseRightButtonUp(self):
		self.ClearSelection()
		if self.rightEvent:
			self.rightEvent()
		return True

def MakeEdit(parent, x, y, width, maxLength, numeric=False, editClass=ui.EditLine, height=20, fontExtra=0):
	slot = ui.SlotBar()
	slot.SetParent(parent)
	slot.SetPosition(x, y)
	slot.SetSize(width, height)
	slot.AddFlag("not_pick")
	slot.Show()
	edit = editClass()
	edit.SetParent(slot)
	# czcionka przed pierwszym tekstem; wyzsza czcionka to wyzsza linia w polu
	lineHeight = 18 + fontExtra
	edit.SetPosition(4, (height - lineHeight) // 2 + 1)
	edit.SetSize(width - 8, lineHeight)
	edit.SetMax(maxLength)
	try:
		edit.SetFontName(FontName(fontExtra))
	except:
		pass
	if numeric:
		edit.SetNumberMode()
	if hasattr(edit, "SetView"):
		# okno, do ktorego przycinany jest napis: wnetrze pola
		mask = ui.Window()
		mask.SetParent(slot)
		mask.SetPosition(1, 0)
		mask.SetSize(width - 2, height)
		mask.AddFlag("not_pick")
		mask.Show()
		slot.clipMask = mask
		# napis zaczyna sie 6 px za krawedzia przyciecia: przyciecie tuz przy
		# literze zjadalo jej lewy brzeg (pierwsza litera wygladala na cienka)
		# niewidoczny napis ta sama czcionka: mierzy szerokosc poczatku tekstu
		measure = ui.TextLine()
		measure.SetParent(slot)
		try:
			measure.SetFontName(FontName(fontExtra))
		except:
			pass
		measure.AddFlag("not_pick")
		measure.Hide()
		slot.measure = measure
		edit.SetView(7, (height - lineHeight) // 2 + 1, width - 13, mask, measure)
	edit.Show()
	if hasattr(edit, "SetView"):
		# zaslona lewego marginesu, nad napisem: chowa koncowke litery, ktora
		# przewinela sie poza poczatek pola
		slot.cover = MakeBar(slot, 1, 1, 6, height - 2, 0xFF000000)
	return slot, edit


class ScaledButton(ui.Window):
	# Przycisk w stylu kategorii, ale w dowolnym rozmiarze: trzy grafiki duzego
	# przycisku (zwykla, najechana, wcisnieta) rozciagniete do podanych wymiarow.
	# Zwykly ui.Button nie skaluje swoich grafik.
	def __init__(self, width, height, text, event, rightEvent=None, fontExtra=0):
		ui.Window.__init__(self)
		self.event = event
		self.rightEvent = rightEvent
		self.pressed = False
		self.SetSize(width, height)
		self.images = []
		for state in (1, 2, 3):
			image = ui.ExpandedImageBox()
			image.SetParent(self)
			image.SetPosition(0, 0)
			image.AddFlag("not_pick")
			try:
				image.LoadImage(BIG_BUTTON % state)
				if image.GetWidth() > 0 and image.GetHeight() > 0:
					image.SetScale(float(width) / image.GetWidth(), float(height) / image.GetHeight())
			except:
				pass
			image.Hide()
			self.images.append(image)
		self.text = ui.TextLine()
		self.text.SetParent(self)
		try:
			self.text.SetFontName(FontName(fontExtra))
		except:
			pass
		self.text.SetPackedFontColor(MainColor())
		RegisterMain(self.text)
		self.text.AddFlag("not_pick")
		self.text.Show()
		self.SetText(text)
		self.__ShowState(0)

	def __del__(self):
		ui.Window.__del__(self)

	def __ShowState(self, state):
		for index, image in enumerate(self.images):
			if index == state:
				image.Show()
			else:
				image.Hide()

	def SetText(self, text):
		# Napis stoi na calych pikselach: wysrodkowanie przez silnik przy
		# nieparzystym rozmiarze dawalo pol piksela i rozmyty, "chudy" napis.
		self.text.SetText(text)
		try:
			textWidth, textHeight = self.text.GetTextSize()
		except:
			textWidth, textHeight = 0, TEXT_LINE_LARGE
		self.text.SetPosition(int(self.GetWidth() - textWidth) // 2, int(self.GetHeight() - textHeight) // 2)

	def OnMouseOverIn(self):
		self.__ShowState(2 if self.pressed else 1)
		ShowHint(self)

	def OnMouseOverOut(self):
		self.pressed = False
		self.__ShowState(0)
		HideHint(self)

	def OnMouseLeftButtonDown(self):
		self.pressed = True
		self.__ShowState(2)
		return True

	def OnMouseLeftButtonUp(self):
		wasPressed = self.pressed
		self.pressed = False
		self.__ShowState(1)
		if wasPressed and self.event:
			self.event()
		return True

	def OnMouseRightButtonUp(self):
		if self.rightEvent:
			self.rightEvent()
		return True


class IconButton(ui.Window):
	# Klikalny obrazek w podanym rozmiarze (usuwanie wybranego bonusu). Po
	# najechaniu pokazuje drugi obrazek i podpis nad soba.
	def __init__(self, fileName, hoverFileName, toolTip, size, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.SetSize(size, size)
		self.image = MakeScaledImage(self, 0, 0, fileName, size, size)
		self.hoverImage = MakeScaledImage(self, 0, 0, hoverFileName, size, size)
		self.hoverImage.Hide()
		self.toolTip = MakeText(self, size // 2, -TEXT_LINE_LARGE - 2, toolTip)
		self.toolTip.SetHorizontalAlignCenter()
		self.toolTip.SetOutline()
		self.toolTip.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def __SetHover(self, hover):
		if hover:
			self.image.Hide()
			self.hoverImage.Show()
			self.toolTip.Show()
		else:
			self.hoverImage.Hide()
			self.toolTip.Hide()
			self.image.Show()

	def Hide(self):
		# schowany pod kursorem przycisk nie dostaje OnMouseOverOut
		self.__SetHover(False)
		ui.Window.Hide(self)

	def OnMouseOverIn(self):
		self.__SetHover(True)

	def OnMouseOverOut(self):
		self.__SetHover(False)

	def OnMouseLeftButtonUp(self):
		if self.event:
			self.event(*self.args)
		return True


class LabeledSelect(ui.Window):
	# zaznaczenie z podpisem: obrazki jak w ofertach, klika sie i obrazek, i napis
	def __init__(self, label, size, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.base = MakeScaledImage(self, 0, 0, SELECT_IMAGE, size, size)
		self.mark = MakeScaledImage(self, 0, 0, SELECT_MARK_IMAGE, size, size)
		self.mark.Hide()
		self.text = ui.TextLine()
		self.text.SetParent(self)
		try:
			self.text.SetFontName(BigFontName())
		except:
			pass
		# srodek napisu na wysokosci srodka obrazka
		self.text.SetPosition(size + 7, size // 2 - 1)
		self.text.SetVerticalAlignCenter()
		self.text.SetPackedFontColor(MainColor())
		RegisterMain(self.text)
		self.text.SetText(label)
		self.text.AddFlag("not_pick")
		self.text.Show()
		textWidth, textHeight = self.text.GetTextSize()
		self.SetSize(size + 7 + textWidth + 4, size)

	def __del__(self):
		ui.Window.__del__(self)

	def SetChecked(self, checked):
		if checked:
			self.mark.Show()
		else:
			self.mark.Hide()

	def OnMouseOverIn(self):
		ShowHint(self)

	def OnMouseOverOut(self):
		HideHint(self)

	def OnMouseLeftButtonUp(self):
		if self.event:
			self.event(*self.args)
		return True


class ImageListButton(ui.Window):
	# Pozycja listy na tle z obrazka. Obrazka nie da sie przemalowac, wiec stan
	# pokazuje polprzezroczysta nakladka nad nim: jasna po najechaniu, zielona
	# (z paskiem z lewej) dla wybranej pozycji.
	def __init__(self, width, height, fileName, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.selected = False
		self.hover = False
		self.SetSize(width, height)
		self.image = MakeScaledImage(self, 0, 0, fileName, width, height)
		self.overlay = MakeBar(self, 0, 0, width, height, 0x00000000)
		self.accent = MakeBar(self, 0, 0, 3, height, COLOR_GREEN)
		# wyrazny separator pozycji: jasna kreska u gory, ciemna u dolu
		self.sepTop = MakeBar(self, 0, 0, width, 1, 0x38FFFFFF)
		self.sepBottom = MakeBar(self, 0, height - 1, width, 1, 0xE0000000)
		self.text = MakeText(self, 10, (height - TEXT_LINE_LARGE) // 2, "", COLOR_DIM)
		self.__Refresh()

	def __del__(self):
		ui.Window.__del__(self)

	def SetLabel(self, label):
		self.text.SetText(label)

	def SetSelected(self, selected):
		self.selected = bool(selected)
		self.__Refresh()

	def __Refresh(self):
		if self.selected:
			self.overlay.SetColor(0x706EDC82 if self.hover else 0x506EDC82)
			self.accent.Show()
			self.text.SetPackedFontColor(COLOR_GREEN)
		else:
			self.overlay.SetColor(0x28FFFFFF if self.hover else 0x00000000)
			self.accent.Hide()
			self.text.SetPackedFontColor(MainColor())

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


class FrameButton(ui.Window):
	# Przycisk w wygladzie oferty: polprzezroczyste tlo i cienka ramka w podanym
	# kolorze. Rysowany z paskow, wiec moze miec dowolny rozmiar. Bez zdarzenia
	# jest sama ramka z napisem (numer strony).
	FONT_EXTRA = 0		# o tyle punktow wiekszy napis (BigFrameButton)

	def __init__(self, width, height, text, event, borderColor=COLOR_OPTION_BORDER, textColor=COLOR_TEXT, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.SetSize(width, height)
		self.parts = (
			MakeBar(self, 1, 1, width - 2, height - 2, COLOR_OPTION_FILL),
			MakeBar(self, 1, 0, width - 2, 1, borderColor),
			MakeBar(self, 1, height - 1, width - 2, 1, borderColor),
			MakeBar(self, 0, 1, 1, height - 2, borderColor),
			MakeBar(self, width - 1, 1, 1, height - 2, borderColor),
		)
		self.hoverBar = MakeBar(self, 1, 1, width - 2, height - 2, COLOR_OPTION_HOVER)
		self.hoverBar.Hide()
		self.textY = (height - TEXT_LINE_LARGE - self.FONT_EXTRA) // 2
		self.text = MakeText(self, width // 2, self.textY, text, textColor, True, self.FONT_EXTRA)
		self.text.SetHorizontalAlignCenter()
		self.textColor = textColor
		self.tail = None

	def __del__(self):
		ui.Window.__del__(self)

	def SetText(self, text):
		self.text.SetText(text)

	# Napis z osobna koncowka, dosunieta o podana liczbe pikseli - czcionka gry
	# zostawia przed nawiasem zamykajacym o piksel wiecej niz za otwierajacym.
	def SetTextWithTail(self, text, tail, pull=1):
		if self.tail is None:
			self.tail = MakeText(self, 0, 0, "", self.textColor, True, self.FONT_EXTRA)
			self.text.SetHorizontalAlignLeft()
		self.text.SetText(text)
		self.tail.SetText(tail)
		textWidth, textHeight = self.text.GetTextSize()
		tailWidth, tailHeight = self.tail.GetTextSize()
		y = self.textY
		x = (self.GetWidth() - (textWidth + tailWidth - pull)) // 2
		self.text.SetPosition(x, y)
		self.tail.SetPosition(x + textWidth - pull, y)

	def OnMouseOverIn(self):
		if self.event:
			self.hoverBar.Show()
		ShowHint(self)

	def OnMouseOverOut(self):
		self.hoverBar.Hide()
		HideHint(self)

	def OnMouseLeftButtonUp(self):
		if self.event:
			self.event(*self.args)
		return True


class OptionButton(ui.Window):
	# Jeden wybor na rozwijanej liscie, w wygladzie oferty: polprzezroczyste tlo i
	# cienka ramka. Rysowany z paskow, bo ramka ThinBoard ma rogi 16 px i przy tak
	# malym przycisku nachodzi sama na siebie.
	def __init__(self, width, height, text, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.SetSize(width, height)
		self.parts = (
			MakeBar(self, 1, 1, width - 2, height - 2, COLOR_OPTION_FILL),
			MakeBar(self, 1, 0, width - 2, 1, COLOR_OPTION_BORDER),
			MakeBar(self, 1, height - 1, width - 2, 1, COLOR_OPTION_BORDER),
			MakeBar(self, 0, 1, 1, height - 2, COLOR_OPTION_BORDER),
			MakeBar(self, width - 1, 1, 1, height - 2, COLOR_OPTION_BORDER),
		)
		self.selectedBar = MakeBar(self, 1, 1, width - 2, height - 2, COLOR_OPTION_SELECTED)
		self.selectedBar.Hide()
		self.hoverBar = MakeBar(self, 1, 1, width - 2, height - 2, COLOR_OPTION_HOVER)
		self.hoverBar.Hide()
		self.text = MakeText(self, width // 2, (height - TEXT_LINE_LARGE) // 2, text)
		self.text.SetHorizontalAlignCenter()

	def __del__(self):
		ui.Window.__del__(self)

	def SetText(self, text):
		self.text.SetText(text)

	def SetSelected(self, selected):
		if selected:
			self.selectedBar.Show()
		else:
			self.selectedBar.Hide()

	def OnMouseOverIn(self):
		self.hoverBar.Show()
		ShowHint(self)

	def OnMouseOverOut(self):
		self.hoverBar.Hide()
		HideHint(self)

	def OnMouseLeftButtonUp(self):
		self.hoverBar.Hide()
		if self.event:
			self.event(*self.args)
		return True


class ClickCatcher(ui.Window):
	# niewidoczne okno na caly ekran pod rozwinietym okienkiem: klik gdziekolwiek
	# poza okienkiem trafia tutaj i je zamyka
	def __init__(self, event):
		ui.Window.__init__(self)
		self.event = event
		self.AddFlag("float")
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def Open(self):
		self.SetPosition(0, 0)
		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		self.SetTop()
		self.Show()

	def OnMouseLeftButtonDown(self):
		self.event()
		return True

	def OnMouseRightButtonDown(self):
		self.event()
		return True


class SelectBox(ui.Window):
	# zaznaczenie oferty: obrazek, a po zaznaczeniu drugi obrazek na nim
	def __init__(self, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.checked = False
		self.SetSize(SELECT_SIZE, SELECT_SIZE)
		self.base = self.__MakeImage(SELECT_IMAGE)
		self.mark = self.__MakeImage(SELECT_MARK_IMAGE)
		self.mark.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def __MakeImage(self, fileName):
		image = ui.ExpandedImageBox()
		image.SetParent(self)
		image.SetPosition(0, 0)
		image.AddFlag("not_pick")
		try:
			image.LoadImage(fileName)
			width = image.GetWidth()
			if width > 0:
				scale = float(SELECT_SIZE) / width
				image.SetScale(scale, scale)
		except:
			pass
		image.Show()
		return image

	def SetChecked(self, checked):
		self.checked = bool(checked)
		if self.checked:
			self.mark.Show()
		else:
			self.mark.Hide()

	def OnMouseOverIn(self):
		ShowHint(self)

	def OnMouseOverOut(self):
		HideHint(self)

	def OnMouseLeftButtonUp(self):
		if self.event:
			self.event(*self.args)
		return True


class CheckBox(ui.Window):
	def __init__(self, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.checked = False
		self.hover = False
		self.SetSize(CHECK_SIZE, CHECK_SIZE)
		self.border = MakeBar(self, 0, 0, CHECK_SIZE, CHECK_SIZE, 0xFF8A8A8A)
		self.fill = MakeBar(self, 1, 1, CHECK_SIZE - 2, CHECK_SIZE - 2, 0xFF0A0A0A)
		self.mark = MakeBar(self, 4, 4, CHECK_SIZE - 8, CHECK_SIZE - 8, COLOR_GREEN)
		self.__Refresh()

	def __del__(self):
		ui.Window.__del__(self)

	def SetChecked(self, checked):
		checked = bool(checked)
		if checked != self.checked:
			self.checked = checked
			self.__Refresh()

	def __Refresh(self):
		self.border.SetColor(COLOR_GREEN if (self.checked or self.hover) else 0xFF8A8A8A)
		self.fill.SetColor(0xFF1E3A26 if self.checked else 0xFF0A0A0A)
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


class ListButton(ui.Window):
	# wiersz listy (kategoria, bonus): tlo, znacznik wyboru, tekst
	def __init__(self, width, height, event, *args):
		ui.Window.__init__(self)
		self.event = event
		self.args = args
		self.selected = False
		self.hover = False
		self.indent = 0
		self.SetSize(width, height)
		self.bg = MakeBar(self, 0, 0, width, height, 0x14FFFFFF)
		self.accent = MakeBar(self, 0, 0, 3, height, COLOR_GREEN)
		self.text = MakeText(self, 10, 4, "", COLOR_DIM)
		self.__Refresh()

	def __del__(self):
		ui.Window.__del__(self)

	def SetLabel(self, label, indent=0):
		self.indent = indent
		self.text.SetPosition(10 + indent * 14, 4)
		self.text.SetText(label)
		self.__Refresh()

	def SetArgs(self, *args):
		self.args = args

	def SetSelected(self, selected):
		self.selected = bool(selected)
		self.__Refresh()

	def __Refresh(self):
		if self.selected:
			self.bg.SetColor(0x406EDC82)
			self.accent.Show()
			self.text.SetPackedFontColor(COLOR_GREEN)
		else:
			self.bg.SetColor(0x30FFFFFF if self.hover else (0x00000000 if self.indent else 0x14FFFFFF))
			self.accent.Hide()
			self.text.SetPackedFontColor(COLOR_DIM if self.indent else MainColor())

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


class OfferRow(ui.Window):
	# Wyglad jak pozycja materialu w oknie ulepszania: ramka ThinBoard, przez ktora
	# widac tlo okna.
	def __init__(self, market):
		ui.Window.__init__(self)
		self.market = proxy(market)
		self.data = None
		self.index = 0
		height = ROW_HEIGHT - 2
		self.height = height
		self.SetSize(ROW_WIDTH, height)

		self.board = ui.ThinBoard()
		self.board.SetParent(self)
		self.board.SetPosition(0, 0)
		self.board.SetSize(ROW_WIDTH, height)
		self.board.AddFlag("not_pick")
		self.board.Show()
		self.hoverBar = MakeBar(self, 3, 3, ROW_WIDTH - 6, height - 6, 0x206EDC82)
		self.hoverBar.Hide()

		self.check = SelectBox(ui.__mem_func__(self.__OnCheck))
		SetHint(self.check, "Zaznacz do \"Kup wybrane\"")
		self.check.SetParent(self)
		self.check.SetPosition(ROW_WIDTH - SELECT_RIGHT - SELECT_SIZE, (height - SELECT_SIZE) // 2)
		self.check.Show()

		self.iconBack = MakeBar(self, ICON_X + ICON_BACK_INSET, (height - ICON_BOX) // 2 + ICON_BACK_INSET, ICON_BOX - 2 * ICON_BACK_INSET, ICON_BOX - 2 * ICON_BACK_INSET, COLOR_ICON_BACK)
		self.iconSlot = MakeScaledImage(self, ICON_X, (height - ICON_BOX) // 2, ICON_SLOT_IMAGE, ICON_BOX, ICON_BOX)

		self.icon = ui.ExpandedImageBox()
		self.icon.SetParent(self)
		self.icon.SetPosition(ICON_X, 2)
		self.icon.AddFlag("not_pick")
		self.icon.Show()

		# nazwa, a za nia poziom ulepszenia w kolorze; pod nia bonusy
		self.nameText = MakeText(self, TEXT_X, 0, "", COLOR_TEXT, True)
		self.bonusTexts = []
		for line in xrange(ROW_BONUS_LINES):
			self.bonusTexts.append(MakeText(self, TEXT_X, 0, "", COLOR_BONUS, False))

		middle = (height - TEXT_LINE_LARGE) // 2
		self.countText = self.__MakeRightText(COUNT_RIGHT, middle, COLOR_TEXT, True)
		self.sellerText = MakeText(self, ROW_WIDTH - SELLER_LEFT, middle, "", COLOR_DIM, True)
		# cena oferty, pod nia cena za sztuke
		self.priceText = self.__MakeRightText(PRICE_RIGHT, middle, COLOR_GOLD, True)
		self.unitText = self.__MakeRightText(PRICE_RIGHT, middle + 10, COLOR_DIM)

		# "Kup" w tym samym stylu co "Kup wybrane": zlota ramka
		self.buyButton = FrameButton(BUY_BUTTON_WIDTH, 22, "Kup", ui.__mem_func__(self.__OnBuy), COLOR_BUY_BORDER, COLOR_BUY_TEXT)
		SetHint(self.buyButton, "Kup t\xea ofert\xea")
		self.buyButton.SetParent(self)
		self.buyButton.SetPosition(BUY_X, (height - 22) // 2)
		self.buyButton.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def __MakeRightText(self, right, y, color, large=False):
		line = MakeText(self, 0, 0, "", color, large)
		line.SetWindowHorizontalAlignRight()
		line.SetHorizontalAlignRight()
		line.SetPosition(right, y)
		return line

	def SetData(self, data, index):
		self.data = data
		self.index = index
		item.SelectItem(data["vnum"])

		# ikona: wysokie przedmioty zmniejszone do ramki, male lekko powiekszone
		iconFile = item.GetIconImageFileName()
		zoom = GetIconZoom(item.GetItemType(), item.GetItemSubType())
		if data["vnum"] == SKILLBOOK_VNUM:
			try:
				bookIcon = SKILLBOOK_ICON % int(data.get("sockets", [0])[0])
				if app.IsExistFile(bookIcon):
					iconFile = bookIcon
			except:
				pass
		self.icon.SetScale(1.0, 1.0)
		self.icon.LoadImage(iconFile)
		width = self.icon.GetWidth()
		height = self.icon.GetHeight()
		biggest = max(1, width, height)
		if zoom:
			# mala grafika: lekko powiekszona, ale nigdy poza swoje tlo
			scale = min(zoom, float(ICON_BOX - 2 * ICON_BACK_INSET) / biggest)
		else:
			scale = min(ICON_SCALE_MAX, float(ICON_BOX - 2 * ICON_BACK_INSET) / biggest)
		self.icon.SetScale(scale, scale)
		self.icon.SetPosition(ICON_X + int((ICON_BOX - width * scale) / 2), int((self.height - height * scale) / 2))

		# nazwa z bonusami jako jeden blok, wysrodkowany w pionie
		bonuses = self.market.GetBonusLines(data)
		shown = min(len(bonuses), ROW_BONUS_LINES)
		top = (self.height - TEXT_LINE_LARGE - shown * TEXT_LINE) // 2

		# kolumna nazwy konczy sie przed iloscia (ta jest dosunieta do prawej)
		count = max(1, data["count"])
		self.countText.SetText("%d szt." % count)
		try:
			countWidth = self.countText.GetTextSize()[0]
		except:
			countWidth = 60
		nameWidth = ROW_WIDTH - COUNT_RIGHT - countWidth - 10 - TEXT_X

		self.nameText.SetPosition(TEXT_X, top)
		FitText(self.nameText, self.market.GetItemName(data), nameWidth)

		# pierwsze bonusy wprost w wierszu; reszte widac w dymku
		for line, text in enumerate(self.bonusTexts):
			if line < shown:
				label = bonuses[line]
				if line == ROW_BONUS_LINES - 1 and len(bonuses) > ROW_BONUS_LINES:
					label += "  (+%d)" % (len(bonuses) - ROW_BONUS_LINES)
				text.SetPosition(TEXT_X, top + TEXT_LINE_LARGE + line * TEXT_LINE)
				FitText(text, label, nameWidth)
			else:
				text.SetText("")

		middle = (self.height - TEXT_LINE_LARGE) // 2
		self.sellerText.SetText(data["seller_name"])
		self.priceText.SetText(Money(data["price"]))
		if count > 1:
			self.priceText.SetPosition(PRICE_RIGHT, middle - 8)
			self.unitText.SetText("%s / szt." % Money(PartPrice(data["price"], count, 1)))
		else:
			self.priceText.SetPosition(PRICE_RIGHT, middle)
			self.unitText.SetText("")
		self.check.SetChecked(self.market.IsSelected(data))
		self.hoverBar.Hide()
		self.Show()

	def RefreshCheck(self):
		if self.data:
			self.check.SetChecked(self.market.IsSelected(self.data))

	def Clear(self):
		self.data = None
		self.hoverBar.Hide()
		self.Hide()

	def __OnCheck(self):
		if self.data:
			self.market.ToggleSelected(self.data)

	def __OnBuy(self):
		if self.data:
			self.market.AskBuy(self.data)

	def OnMouseOverIn(self):
		self.hoverBar.Show()
		if self.data:
			self.market.ShowItemToolTip(self.data)

	def OnMouseOverOut(self):
		self.hoverBar.Hide()
		self.market.HideItemToolTip()

	# lewy klik w oferte: zaznacz ja (dla "Kup wybrane"); prawy: szukaj tylko tego
	# przedmiotu (dla "Kup wiele")
	def OnMouseLeftButtonUp(self):
		if self.data:
			self.market.ToggleSelected(self.data)
		return True

	def OnMouseRightButtonUp(self):
		if self.data:
			self.market.LockItem(self.data)
		return True


# ---- poziom ulepszenia: od +N do +N -------------------------------------------
class RefinePopup(ui.Board):
	# Male okienko nad przyciskiem "Poziom": przyciski "Od" i "Do", a nad nimi dwie
	# listy wyborow naraz. Wybor na jednej liscie nie zamyka drugiej; klik
	# gdziekolwiek poza okienkiem zamyka calosc.
	WIDTH = 210
	HEIGHT = 64				# panel (ui.Board) nie rysuje sie nizszy
	GAP = 10				# odstep od przycisku "Poziom"
	OPTION_WIDTH = 46
	OPTION_HEIGHT = 16
	OPTION_STEP = 21		# wybor + belka rozdzielajaca
	LIST_TOP = 12			# margines panelu nad lista
	BUTTON_WIDTH = 61
	# "Od: [przycisk]   Do: [przycisk]" na srodku panelu
	LABEL_WIDTH = 24
	GROUP_GAP = 16
	MIN_LABEL_X = (WIDTH - (2 * (LABEL_WIDTH + BUTTON_WIDTH) + GROUP_GAP)) // 2
	MIN_X = MIN_LABEL_X + LABEL_WIDTH
	MAX_LABEL_X = MIN_X + BUTTON_WIDTH + GROUP_GAP
	MAX_X = MAX_LABEL_X + LABEL_WIDTH

	def __init__(self, market):
		ui.Board.__init__(self)
		self.market = proxy(market)
		self.values = [-1, -1]		# [od, do]; -1: bez granicy
		self.expanded = True		# listy rozwiniete
		self.anchor = (0, 0)
		self.AddFlag("float")
		self.catcher = ClickCatcher(ui.__mem_func__(self.Close))

		# dwie listy: "-" (bez granicy) i +0 .. +9; miedzy wyborami belka
		optionCount = REFINE_MAX + 2
		self.listHeight = self.LIST_TOP + optionCount * self.OPTION_STEP - 6
		self.options = ([], [])
		self.separators = ([], [])
		for side in (0, 1):
			for index in xrange(optionCount):
				value = index - 1
				option = OptionButton(self.OPTION_WIDTH, self.OPTION_HEIGHT, RefineLabel(value), ui.__mem_func__(self.__Pick), side, value)
				option.SetParent(self)
				option.Hide()
				self.options[side].append(option)
				if index > 0:
					separator = MakeBar(self, 0, 0, self.OPTION_WIDTH - 10, 1, COLOR_OPTION_LINE)
					separator.Hide()
					self.separators[side].append(separator)

		self.labels = (MakeText(self, 0, 0, "Od:", COLOR_HEAD), MakeText(self, 0, 0, "Do:", COLOR_HEAD))
		self.buttons = (
			MakeButton(self, 0, 0, 61, "-", ui.__mem_func__(self.__NoAction)),
			MakeButton(self, 0, 0, 61, "-", ui.__mem_func__(self.__NoAction)),
		)
		self.__Layout()
		self.Hide()

	def __del__(self):
		ui.Board.__del__(self)

	def Destroy(self):
		self.catcher.Hide()
		self.catcher = None
		self.options = ([], [])
		self.separators = ([], [])
		self.Hide()

	# x, y: lewy gorny rog przycisku "Poziom" na ekranie
	def Open(self, x, y, minValue, maxValue):
		self.values = [minValue, maxValue]
		self.expanded = True
		self.anchor = (x, y)
		self.__Refresh()
		self.__Layout()
		self.catcher.Open()
		self.SetTop()
		self.Show()

	def Close(self):
		if self.catcher:
			self.catcher.Hide()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __Refresh(self):
		for side in (0, 1):
			self.buttons[side].SetText(RefineLabel(self.values[side]))
			for index, option in enumerate(self.options[side]):
				option.SetSelected(index - 1 == self.values[side])

	# Dol okienka stoi zawsze tuz nad przyciskiem "Poziom"; listy rosna w gore.
	def __Layout(self):
		listHeight = self.listHeight if self.expanded else 0
		height = listHeight + self.HEIGHT
		self.SetSize(self.WIDTH, height)
		self.SetPosition(self.anchor[0], max(0, self.anchor[1] - self.GAP - height))

		rowY = listHeight + (self.HEIGHT - 21) // 2
		self.labels[0].SetPosition(self.MIN_LABEL_X, rowY + 3)
		self.labels[1].SetPosition(self.MAX_LABEL_X, rowY + 3)
		self.buttons[0].SetPosition(self.MIN_X, rowY)
		self.buttons[1].SetPosition(self.MAX_X, rowY)

		# kazda lista na srodku nad swoim przyciskiem
		for side in (0, 1):
			x = (self.MAX_X if side else self.MIN_X) + (self.BUTTON_WIDTH - self.OPTION_WIDTH) // 2
			for position, option in enumerate(self.options[side]):
				if not self.expanded:
					option.Hide()
					continue
				option.SetPosition(x, self.LIST_TOP + position * self.OPTION_STEP)
				option.Show()
			for position, separator in enumerate(self.separators[side]):
				if not self.expanded or not OPTION_SEPARATORS:
					separator.Hide()
					continue
				separator.SetPosition(x + 5, self.LIST_TOP + (position + 1) * self.OPTION_STEP - 3)
				separator.Show()

	# przyciski "Od" i "Do" tylko pokazuja ustawiona wartosc; wybiera sie z list
	def __NoAction(self):
		pass

	def __Pick(self, side, value):
		self.values[side] = value
		# "od" nie moze byc wyzej niz "do": druga granica idzie za wybrana
		if self.values[0] >= 0 and self.values[1] >= 0 and self.values[0] > self.values[1]:
			self.values[1 - side] = value
		self.__Refresh()
		self.market.SetRefineRange(self.values[0], self.values[1])


# ---- wybor jednej pozycji z krotkiej listy (klasa postaci) ----------------------
class ChoicePopup(ui.Board):
	# Lista pod przyciskiem, ktory ja otwiera; klik poza nia ja zamyka.
	OPTION_HEIGHT = 18
	OPTION_STEP = 23
	PAD = 14

	def __init__(self, choices, width, event):
		ui.Board.__init__(self)
		self.event = event
		self.AddFlag("float")
		self.catcher = ClickCatcher(ui.__mem_func__(self.Close))
		optionWidth = width - 2 * self.PAD
		self.SetSize(width, max(64, 2 * self.PAD + len(choices) * self.OPTION_STEP - (self.OPTION_STEP - self.OPTION_HEIGHT)))
		self.options = []
		self.keepers = []
		for index, (label, value) in enumerate(choices):
			option = OptionButton(optionWidth, self.OPTION_HEIGHT, label, ui.__mem_func__(self.__Pick), value)
			option.SetParent(self)
			option.SetPosition(self.PAD, self.PAD + index * self.OPTION_STEP)
			option.Show()
			self.options.append((option, value))
			if index > 0 and OPTION_SEPARATORS:
				self.keepers.append(MakeBar(self, self.PAD + 5, self.PAD + index * self.OPTION_STEP - 3, optionWidth - 10, 1, COLOR_OPTION_LINE))
		self.Hide()

	def __del__(self):
		ui.Board.__del__(self)

	def Destroy(self):
		self.catcher.Hide()
		self.catcher = None
		self.options = []
		self.keepers = []
		self.event = None
		self.Hide()

	# x, y: lewy dolny rog przycisku na ekranie
	def Open(self, x, y, current):
		for option, value in self.options:
			option.SetSelected(value == current)
		self.SetPosition(x, y + 2)
		self.catcher.Open()
		self.SetTop()
		self.Show()

	def Close(self):
		if self.catcher:
			self.catcher.Hide()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __Pick(self, value):
		self.Close()
		if self.event:
			self.event(value)


# ---- ile sztuk ze stosu ------------------------------------------------------
class QuantityDialog(ui.BoardWithTitleBar):
	def __init__(self, market):
		ui.BoardWithTitleBar.__init__(self)
		self.market = proxy(market)
		self.data = None
		self.SetSize(340, 176)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName("Kup cz\xea\x9c\xe6 stosu")
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		self.itemLine = MakeText(self, 18, 40)
		self.availableLine = MakeText(self, 18, 60, "", COLOR_DIM)
		self.label = MakeText(self, 18, 88, "Ile sztuk kupi\xe6:")
		self.slot, self.edit = MakeEdit(self, 130, 85, 80, 6, True)
		self.edit.OnIMEUpdate = ui.__mem_func__(self.__OnChanged)
		self.edit.SetReturnEvent(ui.__mem_func__(self.Accept))
		self.edit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.totalLine = MakeText(self, 18, 114, "", COLOR_GOLD)
		self.buyButton = MakeButton(self, 86, 140, 76, "Kup", ui.__mem_func__(self.Accept))
		self.cancelButton = MakeButton(self, 178, 140, 76, "Anuluj", ui.__mem_func__(self.Close))
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __GetQuantity(self):
		if not self.data:
			return 0
		return max(1, min(ToInt(self.edit.GetText(), 1), self.data["count"]))

	def __OnChanged(self):
		ui.EditLine.OnIMEUpdate(self.edit)
		self.__UpdatePrice()

	def __UpdatePrice(self):
		if not self.data:
			return
		quantity = self.__GetQuantity()
		price = PartPrice(self.data["price"], self.data["count"], quantity)
		self.totalLine.SetText("Do zap\xb3aty za %d szt.: %s" % (quantity, Money(price)))

	def Open(self, data):
		self.data = data
		self.itemLine.SetText(self.market.GetItemName(data))
		self.availableLine.SetText("W stosie: %d szt. za %s" % (data["count"], Money(data["price"])))
		self.edit.SetText(str(data["count"]))
		self.__UpdatePrice()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.edit.SetFocus()

	def Accept(self):
		if not self.data:
			return
		data = self.data
		quantity = self.__GetQuantity()
		self.Close()
		self.market.SendBuy(data, quantity)

	def Close(self):
		self.data = None
		self.edit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


# ---- okno filtrow (MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1) ---------------------
# Cena, poziom postaci, liczba sztuk (od / do) i plec - jak "Filtry" Domu Towarowego.
class FilterDialog(ui.BoardWithTitleBar):
	WIDTH = 360
	LABEL_X = 18
	MIN_X = 150
	MAX_X = 250
	EDIT_WIDTH = 80
	TOP = 58
	LINE = 28
	SELECT = 18

	# (klucz, podpis, najwiecej cyfr)
	RANGES = (
		("price", "Cena (Yang):", 12),
		("level", "Poziom postaci:", 3),
		("count", "Liczba sztuk:", 6),
	)

	def __init__(self, market):
		ui.BoardWithTitleBar.__init__(self)
		self.market = proxy(market)
		self.sex = 0
		self.edits = {}
		self.keepers = []
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName("Filtry")
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		y = self.TOP
		for key, label, digits in self.RANGES:
			self.keepers.append(MakeText(self, self.LABEL_X, y + 2, label))
			pair = []
			for x in (self.MIN_X, self.MAX_X):
				slot, edit = MakeEdit(self, x, y, self.EDIT_WIDTH, digits, True)
				edit.SetReturnEvent(ui.__mem_func__(self.Accept))
				edit.SetEscapeEvent(ui.__mem_func__(self.Close))
				self.keepers.append(slot)
				pair.append(edit)
			self.keepers.append(MakeText(self, self.MAX_X - 8, y + 2, "-", COLOR_DIM))
			self.edits[key] = pair
			y += self.LINE
		self.keepers.append(MakeText(self, self.MIN_X, self.TOP - 18, "od", COLOR_DIM))
		self.keepers.append(MakeText(self, self.MAX_X, self.TOP - 18, "do", COLOR_DIM))

		self.keepers.append(MakeText(self, self.LABEL_X, y + 1, "P\xb3e\xe6:"))
		self.sexSelects = []
		x = 72
		for name, value in SEX_DEFS:
			select = LabeledSelect(name, self.SELECT, ui.__mem_func__(self.SetSex), value)
			select.SetParent(self)
			select.SetPosition(x, y)
			select.Show()
			self.sexSelects.append((value, select))
			x += select.GetWidth() + 8
		SetHint(self.sexSelects[1][1], "Tylko bro\xf1, zbroje i kostiumy dla tej p\xb3ci")
		SetHint(self.sexSelects[2][1], "Tylko bro\xf1, zbroje i kostiumy dla tej p\xb3ci")
		y += self.LINE + 8

		self.applyButton = MakeButton(self, self.WIDTH // 2 - 92, y, 88, "Zastosuj", ui.__mem_func__(self.Accept))
		self.clearButton = MakeButton(self, self.WIDTH // 2 + 4, y, 88, "Wyczy\x9c\xe6", ui.__mem_func__(self.Clear))
		self.SetSize(self.WIDTH, y + 34)
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def SetSex(self, value):
		self.sex = value
		for selectValue, select in self.sexSelects:
			select.SetChecked(selectValue == value)

	def Open(self, values):
		# values: slownik jak AuctionHouseWindow.extraFilter
		for key, label, digits in self.RANGES:
			for index, edit in enumerate(self.edits[key]):
				value = values[key][index]
				edit.SetText(str(value) if value >= 0 and not (key == "price" and value == 0) else "")
		self.SetSex(values["sex"])
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.edits["price"][0].SetFocus()

	def __Read(self, edit, empty):
		text = edit.GetText().strip()
		if not text:
			return empty
		return max(0, ToInt(text, empty))

	def Accept(self):
		values = {"sex": self.sex}
		for key, label, digits in self.RANGES:
			empty = 0 if key == "price" else -1
			low = self.__Read(self.edits[key][0], empty)
			high = self.__Read(self.edits[key][1], empty)
			if high != empty and low != empty and high < low:
				low, high = high, low		# odwrocony zakres
			values[key] = (low, high)
		self.Close()
		self.market.SetExtraFilter(values)

	def Clear(self):
		for key, label, digits in self.RANGES:
			for edit in self.edits[key]:
				edit.SetText("")
		self.SetSex(0)

	def Close(self):
		for key, label, digits in self.RANGES:
			for edit in self.edits[key]:
				edit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


# ---- okno bonusow ------------------------------------------------------------
def SampleValues(values, limit):
	# najwyzej limit wartosci, rowno rozlozonych, zawsze z najnizsza i najwyzsza
	if len(values) <= limit:
		return list(values)
	last = len(values) - 1
	picked = []
	for index in xrange(limit):
		value = values[int(float(index) * last / (limit - 1) + 0.5)]
		if value not in picked:
			picked.append(value)
	return picked


class BonusDialog(ui.BoardWithTitleBar):
	# Po lewej przewijana lista bonusow, po prawej wybrane bonusy: kazdy w ramce
	# jak oferta, z wartosciami z bazy do klikniecia. Na dole tryb porownania i
	# przyciski. Rozmiary sa policzone pod najdluzsza nazwe bonusu.
	TOP = 62
	LIST_X = 16
	LIST_WIDTH = 244
	LIST_ROWS = 14
	LINE = 22
	SCROLL_WIDTH = 17
	PANEL_X = LIST_X + LIST_WIDTH + SCROLL_WIDTH + 24
	VALUE_MAX = 7			# bonus ma w bazie najwyzej tyle wartosci
	VALUE_STEP = 46
	PANEL_WIDTH = 10 + VALUE_MAX * VALUE_STEP + REMOVE_SIZE + 14
	ENTRY_HEIGHT = 42
	ENTRY_STEP = 44
	VALUE_WIDTH = 42
	VALUE_HEIGHT = 16
	COUNT_HEIGHT = 20			# przyciski liczby bonusow
	LIST_HEIGHT = LIST_ROWS * LINE
	MODE_Y = TOP + LIST_HEIGHT + 16
	BUTTON_Y = MODE_Y + MODE_SIZE + 14
	BUTTON_WIDTH = 110
	BUTTON_HEIGHT = 24
	WIDTH = PANEL_X + PANEL_WIDTH + 16
	HEIGHT = BUTTON_Y + BUTTON_HEIGHT + 18

	def __init__(self, market):
		ui.BoardWithTitleBar.__init__(self)
		self.market = proxy(market)
		self.options = []			# [(typ, nazwa, [wartosci z bazy])]
		self.optionByType = {}
		self.chosen = []			# [[typ, wartosc]]
		self.mode = BONUS_AT_LEAST
		self.count = 0				# ile bonusow ma miec przedmiot; 0: dowolnie
		self.offset = 0
		self.scrolling = False
		self.keepers = []

		self.SetSize(self.WIDTH, self.HEIGHT)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName("Bonusy")
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		# lewa strona: lista w ciemnym panelu, jak kategorie
		self.keepers.append(MakeText(self, self.LIST_X, 40, "Dost\xeapne bonusy", COLOR_HEAD))
		# nazwa przedmiotu albo kategorii: jasny napis na wlasnym tle, rozciaganym
		# do dlugosci napisu
		self.contextBack = MakeScaledImage(self, self.LIST_X + 118, 37, BONUS_CONTEXT_IMAGE, 107, 21)
		self.contextLine = MakeText(self, self.LIST_X + 126, 40, "", COLOR_TEXT)
		cardWidth = self.LIST_WIDTH + self.SCROLL_WIDTH + 6
		self.keepers.append(MakeBar(self, self.LIST_X - 3, self.TOP - 3, cardWidth, self.LIST_HEIGHT + 6, COLOR_CARD_BORDER))
		self.keepers.append(MakeBar(self, self.LIST_X - 2, self.TOP - 2, cardWidth - 2, self.LIST_HEIGHT + 4, COLOR_CARD_FILL))
		self.listButtons = []
		for index in xrange(self.LIST_ROWS):
			button = ImageListButton(self.LIST_WIDTH, self.LINE - 1, BONUS_ROW_IMAGE, ui.__mem_func__(self.__OnClickOption), index)
			button.SetParent(self)
			button.SetPosition(self.LIST_X, self.TOP + index * self.LINE)
			button.Hide()
			self.listButtons.append(button)
		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(self.LIST_X + self.LIST_WIDTH + 1, self.TOP)
		self.scrollBar.SetScrollBarSize(self.LIST_HEIGHT)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar.Hide()
		self.emptyLine = MakeText(self, self.LIST_X + 8, self.TOP + 8, "", COLOR_DIM)

		# prawa strona: wybrane bonusy, kazdy w ramce jak oferta
		self.keepers.append(MakeBar(self, self.PANEL_X - 12, 38, 1, self.TOP + self.LIST_HEIGHT - 34, COLOR_CARD_BORDER))
		self.keepers.append(MakeText(self, self.PANEL_X, 40, "Wybrane bonusy i warto\x9cci", COLOR_HEAD))
		self.entries = []
		for index in xrange(BONUS_MAX):
			y = self.TOP + index * self.ENTRY_STEP
			entry = {}
			board = ui.ThinBoard()
			board.SetParent(self)
			board.SetPosition(self.PANEL_X, y)
			board.SetSize(self.PANEL_WIDTH, self.ENTRY_HEIGHT)
			board.AddFlag("not_pick")
			entry["board"] = board
			entry["name"] = MakeText(self, self.PANEL_X + 10, y + 4, "", COLOR_BONUS)
			entry["remove"] = IconButton(REMOVE_IMAGE, REMOVE_HOVER_IMAGE, "Usu\xf1", REMOVE_SIZE, ui.__mem_func__(self.__RemoveChosen), index)
			entry["remove"].SetParent(self)
			# na srodku wysokosci ramki bonusu
			entry["remove"].SetPosition(self.PANEL_X + self.PANEL_WIDTH - REMOVE_SIZE - 10, y + (self.ENTRY_HEIGHT - REMOVE_SIZE) // 2)
			entry["values"] = []
			for slot in xrange(self.VALUE_MAX):
				value = OptionButton(self.VALUE_WIDTH, self.VALUE_HEIGHT, "", ui.__mem_func__(self.__PickValue), index, slot)
				value.SetParent(self)
				value.SetPosition(self.PANEL_X + 10 + slot * self.VALUE_STEP, y + 22)
				value.Hide()
				entry["values"].append(value)
			entry["shown"] = []
			self.entries.append(entry)
		self.hintLine = MakeText(self, self.PANEL_X + 4, self.TOP + 6, "Kliknij bonus na li\x9ccie po lewej.", COLOR_DIM)

		# tryb porownania: zaznaczenie tymi samymi obrazkami co oferty
		self.keepers.append(MakeBar(self, self.LIST_X - 3, self.MODE_Y - 8, self.WIDTH - 2 * (self.LIST_X - 3), 1, COLOR_CARD_BORDER))
		self.modeChecks = []
		for mode, label in ((BONUS_EQUAL, "R\xf3wno"), (BONUS_AT_LEAST, "Przynajmniej"), (BONUS_AT_MOST, "Maksymalnie")):
			check = LabeledSelect(label, MODE_SIZE, ui.__mem_func__(self.SetMode), mode)
			SetHint(check, ("Warto\x9c\xe6 bonusu dok\xb3adnie taka", "Warto\x9c\xe6 bonusu taka albo wy\xbfsza", "Warto\x9c\xe6 bonusu taka albo ni\xbfsza")[mode])
			check.SetParent(self)
			check.Show()
			self.modeChecks.append(check)
		# trzy tryby rozlozone rowno na szerokosci prawej strony
		modeSpare = self.PANEL_WIDTH - sum([check.GetWidth() for check in self.modeChecks])
		modeX = self.PANEL_X
		for check in self.modeChecks:
			check.SetPosition(modeX, self.MODE_Y)
			modeX += check.GetWidth() + max(8, modeSpare // 2)

		# "Ilo\x9c\xe6" pod lista, na wysokosci trybow: ile bonusow ma miec przedmiot
		# (rowno tyle). Klik w zaznaczona liczbe zdejmuje ten warunek.
		countLabel = MakeText(self, self.LIST_X - 3, self.MODE_Y + (MODE_SIZE - TEXT_LINE_LARGE) // 2, "Ilo\x9c\xe6", COLOR_HEAD)
		self.keepers.append(countLabel)
		try:
			countX = self.LIST_X - 3 + countLabel.GetTextSize()[0] + 10
		except:
			countX = self.LIST_X + 45
		countRight = self.LIST_X + self.LIST_WIDTH + self.SCROLL_WIDTH + 3
		countStep = max(20, (countRight - countX + 4) // BONUS_MAX)
		self.countButtons = []
		for number in xrange(1, BONUS_MAX + 1):
			button = OptionButton(countStep - 4, self.COUNT_HEIGHT, str(number), ui.__mem_func__(self.SetCount), number)
			SetHint(button, "Przedmioty z liczb\xb9 bonus\xf3w: %d" % number)
			button.SetParent(self)
			button.SetPosition(countX + (number - 1) * countStep, self.MODE_Y + (MODE_SIZE - self.COUNT_HEIGHT) // 2)
			button.Show()
			self.countButtons.append(button)

		# "Zastosuj" na srodku dolu okna, "Wyczy\x9c\xe6" przy lewej krawedzi
		self.applyButton = FrameButton(self.BUTTON_WIDTH, self.BUTTON_HEIGHT, "Zastosuj", ui.__mem_func__(self.Accept), COLOR_BUY_BORDER, COLOR_BUY_TEXT)
		SetHint(self.applyButton, "Zastosuj filtr i szukaj")
		self.applyButton.SetParent(self)
		self.applyButton.SetPosition((self.WIDTH - self.BUTTON_WIDTH) // 2, self.BUTTON_Y)
		self.applyButton.Show()
		self.clearButton = FrameButton(self.BUTTON_WIDTH, self.BUTTON_HEIGHT, "Wyczy\x9c\xe6", ui.__mem_func__(self.ClearChosen))
		SetHint(self.clearButton, "Usu\xf1 wybrane bonusy i ilo\x9c\xe6")
		self.clearButton.SetParent(self)
		self.clearButton.SetPosition(self.LIST_X - 3, self.BUTTON_Y)
		self.clearButton.Show()
		self.SetMode(self.mode)
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	# options: [(typ, [wartosci])], kontekst: napis, np. "Buty"
	def Open(self, options, contextName, chosen, mode, count=0):
		self.__ShowCount(count)
		self.options = [(applyType, GetBonusLabel(applyType), values) for applyType, values in options]
		self.options.sort(key=lambda option: PolishLower(option[1]))
		self.optionByType = dict([(option[0], option) for option in self.options])
		# zostaja tylko te wybrane bonusy, ktore ten przedmiot moze miec
		self.chosen = [[applyType, value] for applyType, value in chosen if applyType in self.optionByType]
		self.offset = 0
		self.contextLine.SetText(contextName or "")
		if contextName:
			textWidth, textHeight = self.contextLine.GetTextSize()
			try:
				self.contextBack.SetScale(float(textWidth + 16) / 107.0, 1.0)		# obrazek ma 107 px szerokosci
			except:
				pass
			self.contextBack.Show()
		else:
			self.contextBack.Hide()
		self.emptyLine.SetText("" if self.options else "Brak danych o bonusach.")
		if len(self.options) > self.LIST_ROWS:
			self.scrolling = True
			self.scrollBar.SetMiddleBarSize(float(self.LIST_ROWS) / len(self.options))
			self.scrollBar.SetPos(0.0)
			self.scrolling = False
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
		self.SetMode(mode)
		self.__RefreshList()
		self.__RefreshChosen()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def UpdateOptions(self, options):
		# nowe tabele z serwera przy otwartym oknie: wybor, tryb, miejsce okna i
		# przewiniecie listy zostaja
		chosen = [tuple(entry) for entry in self.chosen]
		offset = self.offset
		x, y = self.GetGlobalPosition()
		self.Open(options, self.contextLine.GetText(), chosen, self.mode, self.count)
		self.SetPosition(x, y)
		limit = self.__MaxOffset()
		self.offset = max(0, min(limit, offset))
		if limit > 0:
			self.scrolling = True
			self.scrollBar.SetPos(float(self.offset) / limit)
			self.scrolling = False
		self.__RefreshList()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SetMode(self, mode):
		self.mode = mode
		for index, check in enumerate(self.modeChecks):
			check.SetChecked(index == mode)

	def __ShowCount(self, count):
		self.count = count
		for index, button in enumerate(self.countButtons):
			button.SetSelected(index + 1 == count)

	def SetCount(self, count):
		# drugi klik w te sama liczbe wylacza warunek
		self.__ShowCount(0 if count == self.count else count)

	def __IsChosen(self, applyType):
		for entry in self.chosen:
			if entry[0] == applyType:
				return True
		return False

	# ---- lista
	def __MaxOffset(self):
		return max(0, len(self.options) - self.LIST_ROWS)

	def __OnScroll(self):
		if self.scrolling:
			return
		self.offset = int(self.scrollBar.GetPos() * self.__MaxOffset() + 0.5)
		self.__RefreshList()

	def OnMouseWheel(self, length):
		limit = self.__MaxOffset()
		if limit > 0:
			self.offset = max(0, min(limit, self.offset + (-2 if length > 0 else 2)))
			self.scrolling = True
			self.scrollBar.SetPos(float(self.offset) / limit)
			self.scrolling = False
			self.__RefreshList()
		return True

	def __RefreshList(self):
		for index, button in enumerate(self.listButtons):
			optionIndex = self.offset + index
			if optionIndex < len(self.options):
				applyType, label, values = self.options[optionIndex]
				button.SetLabel(label)
				button.SetSelected(self.__IsChosen(applyType))
				button.Show()
			else:
				button.Hide()

	def __OnClickOption(self, index):
		optionIndex = self.offset + index
		if optionIndex >= len(self.options):
			return
		applyType, label, values = self.options[optionIndex]
		if self.__IsChosen(applyType):
			self.chosen = [entry for entry in self.chosen if entry[0] != applyType]
		elif len(self.chosen) < BONUS_MAX:
			self.chosen.append([applyType, values[0] if values else 1])
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Dom Aukcyjny: najwy\xbfej %d bonus\xf3w naraz." % BONUS_MAX)
		self.__RefreshList()
		self.__RefreshChosen()

	# ---- wybrane bonusy
	def __RefreshChosen(self):
		for index, entry in enumerate(self.entries):
			if index < len(self.chosen):
				applyType, current = self.chosen[index]
				label, values = self.optionByType[applyType][1], self.optionByType[applyType][2]
				shown = SampleValues(values, self.VALUE_MAX)
				entry["shown"] = shown
				entry["name"].SetText(label)
				entry["board"].Show()
				entry["name"].Show()
				entry["remove"].Show()
				for slot, button in enumerate(entry["values"]):
					if slot < len(shown):
						button.SetText(str(shown[slot]))
						button.SetSelected(shown[slot] == current)
						button.Show()
					else:
						button.Hide()
			else:
				entry["shown"] = []
				entry["board"].Hide()
				entry["name"].Hide()
				entry["remove"].Hide()
				for button in entry["values"]:
					button.Hide()
		if self.chosen:
			self.hintLine.Hide()
		else:
			self.hintLine.Show()

	def __PickValue(self, index, slot):
		if index >= len(self.chosen):
			return
		shown = self.entries[index]["shown"]
		if slot >= len(shown):
			return
		self.chosen[index][1] = shown[slot]
		self.__RefreshChosen()

	def __RemoveChosen(self, index):
		if index >= len(self.chosen):
			return
		del self.chosen[index]
		self.__RefreshList()
		self.__RefreshChosen()

	def ClearChosen(self):
		self.chosen = []
		self.__ShowCount(0)
		self.__RefreshList()
		self.__RefreshChosen()

	def Accept(self):
		self.market.SetBonusFilters([(entry[0], entry[1]) for entry in self.chosen], self.mode, self.count)
		self.Close()


# ---- okno glowne -------------------------------------------------------------
class BigFrameButton(FrameButton):
	# przyciski zakupu gornego paska: wiekszy napis
	FONT_EXTRA = TOOLBAR_FONT_EXTRA


class AuctionHouseWindow(ui.BoardWithTitleBar):
	SUGGESTION_LIMIT = 80		# tyle podpowiedzi najwyzej trafia na przewijana liste
	SUGGESTION_WIDTH = 230

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.tooltip = None
		self.guestBoard = None
		self.keepers = []
		self.rows = []
		self.categoryButtons = []

		# filtr
		self.category = 0
		self.expandedParent = -1
		self.categoryScroll = 0
		self.categoryScrollMax = 0
		self.sortColumn = SORT_PRICE
		self.sortDescending = False
		self.bonusFilters = []			# [(typ, wartosc)]
		self.bonusMode = BONUS_AT_LEAST
		self.bonusCount = 0				# liczba bonusow przedmiotu; 0: dowolna
		self.lockedItem = None			# (vnum, socket0, nazwa): szukaj tylko tego przedmiotu
		self.refineMin = -1				# poziom ulepszenia od / do; -1: bez granicy
		self.refineMax = -1
		self.classFilter = 0			# klasa postaci z CLASS_DEFS; 0: dowolna
		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: cena (0 = bez granicy), poziom postaci i sztuki
		# (-1 = bez granicy) od / do, plec z SEX_DEFS
		self.extraFilter = self.__EmptyExtraFilter()
		self.mobNames = None			# "<marmur> - <potwor>" z dt_mob_catalog.py
		self.marbleBaseName = ""
		self.sidebarHeight = SIDEBAR_HEIGHT
		self.baseHeight = WINDOW_HEIGHT

		# wynik
		self.requestId = 0
		self.pendingHeader = None
		self.loading = False
		self.requestAt = 0.0
		self.lastSearchAt = 0.0
		self.searchAt = None
		self.searchPage = 0
		self.page = 0
		self.pageCount = 1
		self.total = 0
		self.uniqueVnum = 0
		self.uniqueSocket0 = -1
		self.items = []

		# zakupy
		self.selected = {}				# (wlasciciel, id) -> oferta
		self.selectionKey = None		# filtr, przy ktorym zaznaczano oferty
		self.jobRunning = False
		self.jobDeadline = 0.0
		self.quoteRequest = 0
		self.quoteWanted = 0
		self.quoteToken = 0
		self.bulkInput = None
		self.bulkTarget = None
		self.sendQueue = []
		self.nextSendAt = 0.0
		self.questionDialog = None
		self.popupDialog = None
		self.buyData = None

		# bonusy z bazy: typ -> [(wartosci lv1..lv5, maks. poziom dla 8 zestawow)]
		self.bonusTable = {}
		self.bonusIncoming = None
		self.bonusRequestAt = -100.0
		self.optionsAt = 0.0
		self.priceSort = PriceSortColumn()
		self.priceSortOption = self.priceSort

		self.namesAt = None
		self.namesRequestId = 0
		self.itemNames = None			# nazwy z klienta, posortowane (tryb "wszystkie nazwy")
		self.suggestionNames = []
		self.suggestionBox = None
		self.suggestionCatcher = None
		self.lastWheelAt = -1.0

		SyncTextStyle()
		self.quantityDialog = QuantityDialog(self)
		self.bonusDialog = BonusDialog(self)
		self.refinePopup = RefinePopup(self)
		self.filterDialog = FilterDialog(self)		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1
		self.classPopup = None			# powstaje w __Build, gdy znana jest szerokosc przycisku
		self.__Build()
		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	# ---- budowa okna ---------------------------------------------------------
	def __Keep(self, window):
		self.keepers.append(window)
		return window

	def __Card(self, x, y, width, height):
		self.__Keep(MakeBar(self, x, y, width, height, COLOR_CARD_BORDER))
		self.__Keep(MakeBar(self, x + 1, y + 1, width - 2, height - 2, COLOR_CARD_FILL))

	def __Build(self):
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName("Dom Aukcyjny")
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		# duzy przycisk wyznacza szerokosc panelu kategorii i wysokosc okna
		measure = ui.Button()
		measure.SetUpVisual(BIG_BUTTON % 1)
		bigWidth = measure.GetWidth()
		bigHeight = measure.GetHeight()
		measure = None
		if bigWidth <= 0:
			bigWidth, bigHeight = 143, 27
		ApplyLayout(bigWidth, bigHeight)
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)

		self.baseHeight = WINDOW_HEIGHT

		# "Reset" na lewym koncu belki tytulu, wysrodkowany w niej w pionie, na
		# przyciemnionym tle (takim jak tlo ofert)
		resetHeight = 18
		resetX, resetY = 20, 9
		try:
			barX, barY = self.titleBar.GetGlobalPosition()
			myX, myY = self.GetGlobalPosition()
			resetX = barX - myX + 14
			resetY = barY - myY + (self.titleBar.GetHeight() - resetHeight) // 2
		except:
			pass
		self.resetButton = FrameButton(50, resetHeight, "Reset", ui.__mem_func__(self.ResetFilters), COLOR_OPTION_FILL, COLOR_TITLE_BUTTON)
		SetHint(self.resetButton, "Wyczy\x9c\xe6 wszystkie filtry")
		self.resetButton.SetParent(self)
		self.resetButton.SetPosition(resetX, resetY)
		self.resetButton.Show()

		# Gorny pasek: pole nazwy i piec przyciskow tej samej wysokosci, na srodku
		# miedzy belka tytulu a przyciskiem "Klasa".
		#   [pole nazwy] [Szukaj] [Poziom] [Bonus] [Kup wiele] [Kup wybrane]
		klasaY = SIDEBAR_Y - bigHeight - 3
		y = TOOLBAR_TOP + max(0, (klasaY - TOOLBAR_TOP - TOOLBAR_HEIGHT) // 2)
		leftX = SIDEBAR_X + SIDEBAR_PAD
		gap = TOOLBAR_GAP

		# Przyciski zajmuja cala szerokosc listy ofert z rownymi odstepami; trzy
		# pierwsze dziela miejsce, ktore zostaje po przyciskach zakupu, a reszta z
		# dzielenia idzie w szerokosc ostatniego.
		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: czwarty przycisk "Filtry"
		wide = max(60, (ROW_WIDTH - 5 * gap - BUY_BULK_WIDTH - BUY_SELECTED_WIDTH) // 4)
		widths = [wide, wide, wide, wide, BUY_BULK_WIDTH, BUY_SELECTED_WIDTH]
		# na waskim ekranie "Kup wybrane" oddaje reszte szerokosci, zeby pasek nie
		# wyszedl poza liste ofert
		widths[-1] = max(100, ROW_WIDTH - sum(widths[:-1]) - 5 * gap)
		xs = []
		x = MAIN_X
		for width in widths:
			xs.append(x)
			x += width + gap

		# pole nazwy konczy sie o ten sam odstep przed "Szukaj" (ramka pola rysuje
		# sie o piksel szerzej niz jego rozmiar)
		self.searchX = leftX
		self.searchWidth = max(60, MAIN_X - gap - 1 - leftX)
		self.searchSlot, self.searchEdit = MakeEdit(self, self.searchX, y, self.searchWidth, 32, False, SearchEditLine, TOOLBAR_HEIGHT, SEARCH_FONT_EXTRA)
		self.searchEdit.SetRightEvent(ui.__mem_func__(self.ClearSearchText))
		try:
			self.searchEdit.SetPlaceholder("Nazwa przedmiotu", FontName(SEARCH_FONT_EXTRA))
		except:
			pass
		self.searchEdit.OnIMEUpdate = ui.__mem_func__(self.__OnSearchTextChanged)
		self.searchEdit.SetReturnEvent(ui.__mem_func__(self.Search))
		self.searchEdit.SetEscapeEvent(ui.__mem_func__(self.Close))

		# Szukaj, Poziom, Bonus: grafika kategorii rozciagnieta do wysokosci paska
		self.searchButton = ScaledButton(widths[0], TOOLBAR_HEIGHT, "Szukaj", ui.__mem_func__(self.Search), None, TOOLBAR_FONT_EXTRA)
		self.refineButton = ScaledButton(widths[1], TOOLBAR_HEIGHT, "Poziom", ui.__mem_func__(self.ToggleRefinePopup), ui.__mem_func__(self.ClearRefineRange), TOOLBAR_FONT_EXTRA)
		self.bonusButton = ScaledButton(widths[2], TOOLBAR_HEIGHT, "Bonus", ui.__mem_func__(self.OpenBonusDialog), ui.__mem_func__(self.ClearBonusFilters), TOOLBAR_FONT_EXTRA)
		self.filterButton = ScaledButton(widths[3], TOOLBAR_HEIGHT, "Filtry", ui.__mem_func__(self.OpenFilterDialog), ui.__mem_func__(self.ClearExtraFilter), TOOLBAR_FONT_EXTRA)
		# przyciski zakupu: ramka jak oferta, w zlocie
		self.bulkButton = BigFrameButton(widths[4], TOOLBAR_HEIGHT, "Kup wiele", ui.__mem_func__(self.AskBuyBulk), COLOR_BUY_BORDER, COLOR_BUY_TEXT)
		self.buySelectedButton = BigFrameButton(widths[5], TOOLBAR_HEIGHT, "", ui.__mem_func__(self.AskBuySelected), COLOR_BUY_BORDER, COLOR_BUY_TEXT)
		SetHint(self.searchButton, "Szukaj ofert (Enter)")
		SetHint(self.refineButton, "Poziom ulepszenia od / do (prawy klik czy\x9cci)")
		SetHint(self.bonusButton, "Filtr bonus\xf3w (prawy klik czy\x9cci)")
		SetHint(self.filterButton, "Cena, poziom postaci, liczba sztuk, p\xb3e\xe6 (prawy klik czy\x9cci)")
		SetHint(self.bulkButton, "Kup podan\xb9 liczb\xea sztuk jednego przedmiotu, od najta\xf1szej")
		SetHint(self.buySelectedButton, "Kup wszystkie zaznaczone oferty")
		for position, button in enumerate((self.searchButton, self.refineButton, self.bonusButton, self.filterButton, self.bulkButton, self.buySelectedButton)):
			button.SetParent(self)
			button.SetPosition(xs[position], y)
			button.Show()
		self.buySelectedButton.SetTextWithTail("Kup wybrane (0", ")")

		# pod polem nazwy, nad kategoriami: "Klasa"
		self.classButton = self.__Keep(MakeBigButton(self, leftX, SIDEBAR_Y - bigHeight - 3, "Klasa", ui.__mem_func__(self.ToggleClassPopup), ui.__mem_func__(self.ClearClassFilter)))
		self.classButton.SetToolTipText("Przedmioty dla wybranej klasy (prawy klik czy\x9cci)", 0, -23)
		self.classPopup = ChoicePopup(CLASS_DEFS, bigWidth, ui.__mem_func__(self.SetClassFilter))

		# kategorie: przyciski jak w wyszukiwarce sklepow (F5); glowne zawsze, dzieci
		# tylko rozwinietego rodzica. Gdy nie mieszcza sie w panelu - kolko myszy.
		self.sidebarBorder = self.__Keep(MakeBar(self, SIDEBAR_X, SIDEBAR_Y, SIDEBAR_WIDTH, SIDEBAR_HEIGHT, COLOR_CARD_BORDER))
		self.sidebarFill = self.__Keep(MakeBar(self, SIDEBAR_X + 1, SIDEBAR_Y + 1, SIDEBAR_WIDTH - 2, SIDEBAR_HEIGHT - 2, COLOR_CARD_FILL))
		for index, (label, parent, attrSet) in enumerate(CATEGORY_DEFS):
			button = ui.Button()
			button.SetParent(self)
			button.SetUpVisual(BIG_BUTTON % 1)
			button.SetOverVisual(BIG_BUTTON % 2)
			button.SetDownVisual(BIG_BUTTON % 3)
			SetButtonText(button, label, True)
			button.ButtonText.SetHorizontalAlignLeft()
			button.ButtonText.SetWindowVerticalAlignCenter()
			button.ButtonText.SetPosition(7, 0)
			button.SetEvent(ui.__mem_func__(self.SetCategory), index)
			button.Hide()
			self.categoryButtons.append(button)
		self.__RelayoutCategories()

		# naglowek listy: klik w kolumne sortuje
		headerY = HEADER_Y
		textY = headerY + (HEADER_HEIGHT - TEXT_LINE_LARGE) // 2
		self.__Keep(MakeBar(self, MAIN_X, headerY, ROW_WIDTH, HEADER_HEIGHT, 0x33FFFFFF))
		self.pageCheck = SelectBox(ui.__mem_func__(self.SelectPage))
		SetHint(self.pageCheck, "Zaznacz albo odznacz ca\xb3\xb9 stron\xea")
		self.pageCheck.SetParent(self)
		self.pageCheck.SetPosition(MAIN_RIGHT - SELECT_RIGHT - SELECT_SIZE, headerY + (HEADER_HEIGHT - SELECT_SIZE) // 2)
		self.pageCheck.Show()
		self.__Keep(MakeText(self, MAIN_X + TEXT_X, textY, "Przedmiot", COLOR_HEAD))
		self.__Keep(MakeText(self, MAIN_RIGHT - SELLER_LEFT, textY, "Sprzedawca", COLOR_HEAD))
		self.sortLabels = {}
		for column, right, width in ((SORT_COUNT, COUNT_RIGHT, 60), (SORT_PRICE, PRICE_RIGHT, 70)):
			# etykieta konczy sie tam, gdzie liczby w wierszach; nad nia niewidoczny przycisk
			label = self.__Keep(MakeText(self, 0, 0, "", COLOR_HEAD))
			label.SetWindowHorizontalAlignRight()
			label.SetHorizontalAlignRight()
			label.SetPosition(WINDOW_WIDTH - MAIN_RIGHT + right, textY)
			self.sortLabels[column] = label
			sortButton = self.__Keep(MakeTextButton(self, MAIN_RIGHT - right - width, headerY, width, HEADER_HEIGHT, "", ui.__mem_func__(self.SetSort), column))
			try:
				sortButton.SetToolTipText("Sortuj po ilo\x9cci" if column == SORT_COUNT else "Sortuj po cenie oferty albo za sztuk\xea", 0, -19)
			except:
				pass
		self.__UpdateSortHeaders()

		# wiersze ofert
		for index in xrange(ROWS_PER_PAGE):
			row = OfferRow(self)
			row.SetParent(self)
			row.SetPosition(MAIN_X, ROWS_Y + index * ROW_HEIGHT)
			row.Hide()
			self.rows.append(row)
		self.emptyText = self.__Keep(MakeText(self, MAIN_X + 220, ROWS_Y + 80, "", COLOR_DIM))

		# stopka: strony pod lista ofert, liczba ofert pod kategoriami
		footerY = FOOTER_Y
		center = WINDOW_WIDTH // 2		# srodek calego okna
		self.pager = []
		pagerWidth = 4 * PAGER_BUTTON + PAGER_BOX + 4 * 4
		x = center - pagerWidth // 2
		for text, event in (("<<", self.FirstPage), ("<", self.PreviousPage), (None, None), (">", self.NextPage), (">>", self.LastPage)):
			if text is None:
				button = FrameButton(PAGER_BOX, PAGER_HEIGHT, "1 / 1", None)
				self.pageBox = button
				width = PAGER_BOX
			else:
				button = FrameButton(PAGER_BUTTON, PAGER_HEIGHT, text, ui.__mem_func__(event))
				SetHint(button, {"<<": "Pierwsza strona", "<": "Poprzednia strona", ">": "Nast\xeapna strona", ">>": "Ostatnia strona"}[text])
				width = PAGER_BUTTON
			button.SetParent(self)
			button.SetPosition(x, footerY)
			button.Show()
			self.pager.append(button)
			x += width + 4
		self.statusText = self.__Keep(MakeText(self, SIDEBAR_X + SIDEBAR_PAD, SIDEBAR_Y + SIDEBAR_HEIGHT + 6, "", COLOR_DIM))
		self.lockText = self.__Keep(MakeText(self, center + pagerWidth // 2 + 16, footerY + 2, "", COLOR_GREEN))
		self.unlockButton = self.__Keep(MakeTextButton(self, MAIN_RIGHT - 18, footerY, 16, 20, "x", ui.__mem_func__(self.UnlockItem)))
		self.unlockButton.SetToolTipText("Poka\xbf znowu wszystkie przedmioty", 0, -23)
		self.unlockButton.Hide()

		# podpowiedzi nazw - na koncu, zeby byly nad lista
		self.suggestionBox = SuggestionBox(max(self.SUGGESTION_WIDTH, self.searchWidth), ui.__mem_func__(self.__OnSelectSuggestion))
		self.suggestionCatcher = ClickCatcher(ui.__mem_func__(self.__HideSuggestions))

	def SetToolTip(self, tooltip):
		self.tooltip = proxy(tooltip) if tooltip else None

	def SetGuestBoard(self, board):
		# modul ikashop ma jeden cel pakietow (wyniki i otwarcie sklepu); okno
		# przejmuje go, wiec sklep przekazuje dalej do okna goscia
		self.guestBoard = proxy(board) if board else None

	def Destroy(self):
		DestroyHint()
		self.__CloseDialogs()
		if self.quantityDialog:
			self.quantityDialog.Hide()
			self.quantityDialog = None
		if self.bonusDialog:
			self.bonusDialog.Hide()
			self.bonusDialog = None
		if self.refinePopup:
			self.refinePopup.Destroy()
			self.refinePopup = None
		if self.filterDialog:
			self.filterDialog.Hide()
			self.filterDialog = None
		if self.classPopup:
			self.classPopup.Destroy()
			self.classPopup = None
		self.__HideSuggestions()
		self.suggestionBox = None
		self.suggestionCatcher = None
		self.selected = {}
		self.items = []
		self.rows = []
		self.categoryButtons = []
		self.keepers = []
		self.sendQueue = []
		self.tooltip = None
		self.guestBoard = None
		self.Hide()

	# ---- otwieranie ----------------------------------------------------------
	def Open(self):
		ikashop.SetSearchShopBoard(self)
		if self.jobRunning and app.GetTime() > self.jobDeadline:
			self.jobRunning = False
		self.Show()
		self.SetTop()
		self.__PlaceWindow()
		self.__SyncOptions(False)
		self.__RequestBonusTable()
		self.Search()

	def __PlaceWindow(self):
		# srodek tej czesci ekranu, ktora zostaje nad dolnym paskiem gry
		try:
			screenWidth = wndMgr.GetScreenWidth()
			screenHeight = wndMgr.GetScreenHeight()
		except:
			self.SetCenterPosition()
			return
		x = max(0, (screenWidth - self.GetWidth()) // 2)
		y = max(0, (screenHeight - TASKBAR_RESERVE - self.GetHeight()) // 2)
		self.SetPosition(x, y)

	def __RequestBonusTable(self):
		# Tabele bonusow sa pobierane przy kazdym otwarciu okna i okna bonusow,
		# wiec zmiany z bazy widac po przeladowaniu tabel na serwerze, bez
		# restartu klienta.
		now = app.GetTime()
		if now < self.bonusRequestAt:
			self.bonusRequestAt = -100.0		# zegar gry cofnal sie (zmiana kanalu)
		if now - self.bonusRequestAt < BONUS_REFRESH_GAP:
			return
		self.bonusRequestAt = now
		self.__Send("/ah_bonus")

	def __SyncOptions(self, search=True):
		# opcje gry zmienione przy otwartym oknie: kolor napisow i sortowanie
		if SyncTextStyle():
			RecolorMain()
		priceSort = PriceSortColumn()
		if priceSort != self.priceSortOption:
			self.priceSortOption = priceSort
			self.priceSort = priceSort
			self.__UpdateSortHeaders()
			if search and self.sortColumn == SORT_PRICE:
				self.Search()

	def Close(self):
		if self.jobRunning:
			self.__Send("/ah_cancel")
		self.__CloseDialogs()
		if self.quantityDialog:
			self.quantityDialog.Close()
		if self.bonusDialog:
			self.bonusDialog.Close()
		if self.filterDialog:
			self.filterDialog.Close()
		self.__HideSuggestions()
		self.HideItemToolTip()
		HideHint()
		if self.refinePopup:
			self.refinePopup.Close()
		if self.classPopup:
			self.classPopup.Close()
		self.searchEdit.KillFocus()
		if self.sendQueue:
			# lista "Kup wybrane" nie poszla cala, wiec zakup sie nie zacznie
			self.sendQueue = []
			self.jobRunning = False
		self.searchAt = None
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __CloseDialogs(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		if self.popupDialog:
			self.popupDialog.Hide()
			self.popupDialog = None
		self.buyData = None
		self.__CloseBulkInput()

	def __Popup(self, lines):
		for line in lines:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Dom Aukcyjny: %s" % line)
		if not self.IsShow():
			return
		if self.popupDialog:
			self.popupDialog.Hide()
		popup = uiCommon.PopupDialog()
		popup.SetText("[ENTER]".join(lines))
		popup.Open()
		self.popupDialog = popup

	def __Ask(self, lines, acceptEvent):
		if self.questionDialog:
			self.questionDialog.Close()
		if len(lines) > 1:
			dialog = uiCommon.QuestionDialog2()
			dialog.SetText1(lines[0])
			dialog.SetText2(lines[1])
		else:
			dialog = uiCommon.QuestionDialog()
			dialog.SetText(lines[0])
		dialog.SAFE_SetAcceptEvent(acceptEvent)
		dialog.SAFE_SetCancelEvent(self.__CancelQuestion)
		dialog.Open()
		self.questionDialog = dialog

	def __CancelQuestion(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		self.buyData = None

	# ---- wysylanie -----------------------------------------------------------
	def __Send(self, command):
		net.SendChatPacket(command)

	def __Queue(self, command):
		self.sendQueue.append(command)

	# ---- nazwy ---------------------------------------------------------------
	def GetItemName(self, data):
		name = data.get("_ah_name")
		if name is None:
			item.SelectItem(data["vnum"])
			name = item.GetItemName()
			# ksiega to jeden vnum, a umiejetnosc siedzi w gniezdzie 0
			if data["vnum"] in BOOK_VNUMS:
				try:
					skillVnum = int(data.get("sockets", [0])[0])
					skillName = skill.GetSkillName(skillVnum) if skillVnum in SKILL_IDS else ""
					if skillName:
						name = "%s - %s" % (skillName, name)
				except:
					pass
			# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: marmur pokazuje swojego potwora
			if data["vnum"] in POLYMORPH_VNUMS:
				try:
					mobVnum = int(data.get("sockets", [0])[0])
					mobName = nonplayer.GetMonsterName(mobVnum) if mobVnum else ""
					if mobName:
						name = "%s - %s" % (name, mobName)
				except:
					pass
			data["_ah_name"] = name
		return name

	def GetBonusLines(self, data):
		# bonusy oferty jako napisy, tak jak w dymku przedmiotu
		lines = data.get("_ah_bonus")
		if lines is None:
			lines = []
			try:
				for attr in data.get("attrs", []):
					if not attr[0]:
						continue
					text = localeinfo_point.GetApplyString(attr[0], attr[1])
					if text:
						lines.append(text)
			except:
				pass
			data["_ah_bonus"] = lines
		return lines

	def __HideSuggestions(self):
		self.suggestionNames = []
		self.namesAt = None
		self.namesRequestId += 1		# odpowiedz, ktora jest w drodze, juz sie nie liczy
		if self.suggestionCatcher:
			self.suggestionCatcher.Hide()
		if self.suggestionBox:
			self.suggestionBox.Hide()

	# Podpowiedzi daje serwer: przedmioty, ktore sa teraz wystawione i pasuja do
	# wpisanego tekstu oraz do wybranej kategorii, klasy i poziomu (bonusy sie nie
	# licza). Pytanie idzie chwile po ostatniej literze.
	def __UpdateSuggestions(self):
		query = self.searchEdit.GetText().strip()
		if len(query) < 2 or self.lockedItem:
			self.namesAt = None
			self.__HideSuggestions()
			return
		if AllNamesMode():
			self.namesAt = None
			self.__ShowLocalNames(query)
			return
		self.namesAt = app.GetTime() + NAMES_DELAY

	# Tryb z opcji gry: wszystkie nazwy przedmiotow, ktore zna klient - takze tych,
	# ktorych nikt teraz nie wystawia. Klient zna same nazwy, wiec kategoria, klasa
	# i poziom nie zawezaja tej listy.
	def __ShowLocalNames(self, query):
		if self.itemNames is None:
			names = []
			seen = set()
			try:
				for name in ikashop.GetItemNames():
					key = PolishLower(name)
					if key not in seen:
						seen.add(key)
						names.append((key, name))
			except:
				pass
			for name in self.__GetMarbleNames():		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1
				key = PolishLower(name)
				if key not in seen:
					seen.add(key)
					names.append((key, name))
			names.sort()
			self.itemNames = names
		key = PolishLower(query)
		startsWith = []
		contains = []
		for lowerName, name in self.itemNames:
			if lowerName == key:
				continue
			if lowerName.startswith(key):
				startsWith.append(name)
			elif key in lowerName:
				contains.append(name)
		self.__ShowSuggestions((startsWith + contains)[:self.SUGGESTION_LIMIT])

	def __SendNames(self):
		if len(self.searchEdit.GetText().strip()) < 2 or self.lockedItem:
			return
		self.namesRequestId += 1
		prefix = "/ah_names %d " % self.namesRequestId
		self.__Send(prefix + self.__BuildFilter(len(prefix)))

	# args: (numer pytania, "vnum,vnum,..." albo "-")
	def __OnNames(self, args):
		if len(args) < 2 or ToInt(args[0], -1) != self.namesRequestId or not self.IsShow():
			return
		query = PolishLower(self.searchEdit.GetText().strip())
		names = []
		seen = set()
		if args[1] != "-":
			for token in args[1].split(","):
				vnum = ToInt(token)
				if vnum <= 0:
					continue
				try:
					item.SelectItem(vnum)
					name = item.GetItemName()
				except:
					continue
				key = PolishLower(name)
				if not name or key == query or key in seen:
					continue
				seen.add(key)
				names.append(name)
				# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: wystawiony marmur - podpowiedzi
				# "<marmur> - <potwor>" pasujace do tekstu (serwer szuka tez po potworze)
				if vnum in POLYMORPH_VNUMS:
					for marbleName in self.__GetMarbleNames():
						marbleKey = PolishLower(marbleName)
						if query in marbleKey and marbleKey != query and marbleKey not in seen:
							seen.add(marbleKey)
							names.append(marbleName)
		self.__ShowSuggestions(names[:self.SUGGESTION_LIMIT])

	# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: "<marmur> - <potwor>" dla kazdego potwora
	# z dt_mob_catalog.py (jak w Domu Towarowym); liczone raz.
	def __GetMarbleNames(self):
		if self.mobNames is not None:
			return self.mobNames
		names = []
		try:
			item.SelectItem(MARBLE_VNUM)
			self.marbleBaseName = item.GetItemName()
		except:
			self.marbleBaseName = ""
		if self.marbleBaseName:
			try:
				from dt_mob_catalog import MOB_VNUMS
			except ImportError:
				MOB_VNUMS = ()
			for mobVnum in MOB_VNUMS:
				try:
					mobName = nonplayer.GetMonsterName(mobVnum)
				except:
					continue
				if mobName:
					names.append("%s - %s" % (self.marbleBaseName, mobName))
		self.mobNames = names
		return names

	def __ShowSuggestions(self, names):
		if not names:
			self.__HideSuggestions()
			return
		self.suggestionNames = names
		# lista jest osobnym oknem tuz pod polem nazwy; klik gdziekolwiek poza nia
		# trafia w niewidoczne okno pod spodem i ja zamyka (jak okienko "Poziom")
		slotX, slotY = self.searchSlot.GetGlobalPosition()
		self.suggestionBox.SetNames(self.suggestionNames)
		self.suggestionBox.SetPosition(slotX, slotY + TOOLBAR_HEIGHT + 2)
		self.suggestionCatcher.Open()
		self.suggestionBox.Show()
		self.suggestionBox.SetTop()

	def __OnSelectSuggestion(self, name):
		self.__SetSearchText(name)
		self.lockedItem = None
		self.__HideSuggestions()
		self.Search()

	def ClearSearchText(self):
		# prawy klik w pole nazwy
		self.lockedItem = None
		self.__SetSearchText("")
		self.__HideSuggestions()
		self.__RefreshLock()
		self.Search()

	def __SetSearchText(self, text):
		self.searchEdit.SetText(text)
		self.searchEdit.SetEndPosition()

	def __OnSearchTextChanged(self):
		ui.EditLine.OnIMEUpdate(self.searchEdit)
		self.searchEdit.AdjustView()
		# reczna zmiana nazwy zdejmuje blokade na jeden przedmiot
		if self.lockedItem and self.searchEdit.GetText() != self.lockedItem[2]:
			self.lockedItem = None
			self.__RefreshLock()
		self.__UpdateSuggestions()
		self.searchPage = 0
		self.searchAt = app.GetTime() + SEARCH_DELAY

	# ---- filtr ---------------------------------------------------------------
	def __FindSkillIds(self, query):
		# serwer nie zna nazw umiejetnosci, wiec klient podaje mu pasujace do tekstu
		key = PolishLower(query)
		if len(key) < 2:
			return []
		bookNames = []
		for vnum in BOOK_VNUMS:
			try:
				item.SelectItem(vnum)
				bookNames.append(item.GetItemName())
			except:
				pass
		ids = []
		for skillVnum in SKILL_IDS:
			try:
				name = skill.GetSkillName(skillVnum)
			except:
				continue
			if not name:
				continue
			for bookName in bookNames:
				if key in PolishLower("%s - %s" % (name, bookName)):
					ids.append(skillVnum)
					break
		return ids

	# FILTR komend /ah_search i /ah_bulk_quote; reserve: ile znakow zajmie poczatek komendy
	def __BuildFilter(self, reserve, vnum=0, socket0=-1):
		if not vnum and self.lockedItem:
			vnum, socket0 = self.lockedItem[0], self.lockedItem[1]
		bonuses = ",".join(["%d:%d" % (applyType, value) for applyType, value in self.bonusFilters]) or "-"
		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: cena od / do oraz dalsze filtry w polu klasy
		# ("klasa:poziomOd:poziomDo:sztukiOd:sztukiDo:plec"); bez nich - sama klasa
		extra = self.extraFilter
		classText = "%d" % self.classFilter
		if self.__HasExtraRanges():
			classText += ":%d:%d:%d:%d:%d" % (extra["level"][0], extra["level"][1], extra["count"][0], extra["count"][1], extra["sex"])
		text = "%d %d %d %d %d %d %d %d %d %d %d %s %s" % (
			self.category, self.priceSort if self.sortColumn == SORT_PRICE else self.sortColumn, 1 if self.sortDescending else 0,
			self.refineMin, self.refineMax, extra["price"][0], extra["price"][1],
			vnum, socket0, self.bonusMode, self.bonusCount, classText, bonuses)
		if vnum:
			return text			# konkretny przedmiot: nazwa juz nic nie zmienia
		query = self.searchEdit.GetText().strip()
		for char in ('"', "'", "|", "$"):
			query = query.replace(char, "")
		query = query[:60]
		if not query:
			return text
		text += " " + query
		# umiejetnosci ksiag - tyle, ile zmiesci sie w komendzie
		ids = []
		for skillVnum in self.__FindSkillIds(query):
			if reserve + len(text) + 1 + len(",".join([str(i) for i in ids + [skillVnum]])) > COMMAND_MAX:
				break
			ids.append(skillVnum)
		if ids:
			text += "|" + ",".join([str(i) for i in ids])
		return text

	def Search(self):
		# nowe zapytanie od pierwszej strony
		self.__HideSuggestions()
		self.searchPage = 0
		self.searchAt = max(app.GetTime(), self.lastSearchAt + SEARCH_GAP)

	def __RequestPage(self, page):
		self.searchPage = max(0, page)
		self.searchAt = max(app.GetTime(), self.lastSearchAt + SEARCH_GAP)

	def __SelectionKey(self):
		# wszystko, co decyduje o tym, JAKIE oferty widac (bez sortowania i strony)
		return (self.category, self.classFilter, self.refineMin, self.refineMax,
			tuple(sorted(self.extraFilter.items())),
			tuple(self.bonusFilters), self.bonusMode, self.bonusCount,
			self.lockedItem and (self.lockedItem[0], self.lockedItem[1]),
			PolishLower(self.searchEdit.GetText().strip()))

	def __SendSearch(self):
		# Inna kategoria, inna nazwa albo inny filtr to inna lista ofert: zaznaczenia
		# z poprzedniej znikaja. Zmiana strony i sortowania ich nie rusza.
		key = self.__SelectionKey()
		if key != self.selectionKey:
			self.selectionKey = key
			if self.selected:
				self.selected = {}
				self.__RefreshSelection()
		self.requestId += 1
		prefix = "/ah_search %d %d %d " % (self.requestId, self.searchPage, ROWS_PER_PAGE)
		self.loading = True
		self.requestAt = app.GetTime()
		self.lastSearchAt = self.requestAt
		self.__Send(prefix + self.__BuildFilter(len(prefix)))
		self.__UpdateStatus()

	def ResetFilters(self):
		self.__SetSearchText("")
		self.refineMin = -1
		self.refineMax = -1
		self.classFilter = 0
		self.extraFilter = self.__EmptyExtraFilter()		# MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1
		if self.filterDialog:
			self.filterDialog.Close()
		self.__RefreshFilterButton()
		self.__RefreshClassButton()
		self.__RefreshRefineButton()
		self.bonusFilters = []
		self.bonusMode = BONUS_AT_LEAST
		self.bonusCount = 0
		self.lockedItem = None
		self.sortColumn = SORT_PRICE
		self.sortDescending = False
		self.category = 0
		self.expandedParent = -1
		self.categoryScroll = 0
		self.__RelayoutCategories()
		self.__UpdateSortHeaders()
		self.__RefreshLock()
		self.__RefreshBonusButton()
		self.ClearSelection()
		self.Search()

	def SetCategory(self, index):
		self.category = index
		self.__RelayoutCategories()
		self.Search()

	def __RelayoutCategories(self):
		count = len(CATEGORY_VISIBLE)
		buttonHeight = self.categoryButtons[0].GetHeight()
		inner = SIDEBAR_HEIGHT - 2 * SIDEBAR_PAD
		fit = max(1, min(count, (inner + CATEGORY_GAP) // (buttonHeight + CATEGORY_GAP)))
		if fit >= count:
			# Wszystkie sie mieszcza: miejsce, ktore zostaje po dopasowaniu panelu
			# do listy ofert, jest rozlozone rowno na odstepy miedzy przyciskami.
			spare = max(0, inner - count * buttonHeight)
			gaps = max(1, count - 1)
			gap = spare // gaps
			extra = spare % gaps		# pierwszym odstepom po jednym pikselu wiecej
		else:
			# maly ekran: widac tyle, ile sie miesci, reszta pod kolkiem myszy
			gap = CATEGORY_GAP
			extra = 0
		self.categoryScrollMax = count - fit
		self.categoryScroll = max(0, min(self.categoryScroll, self.categoryScrollMax))
		self.sidebarHeight = SIDEBAR_HEIGHT
		for index, button in enumerate(self.categoryButtons):
			if index not in CATEGORY_VISIBLE:
				button.Hide()
				continue
			row = CATEGORY_VISIBLE.index(index) - self.categoryScroll
			if row < 0 or row >= fit:
				button.Hide()
				continue
			button.SetPosition(SIDEBAR_X + SIDEBAR_PAD, SIDEBAR_Y + SIDEBAR_PAD + row * (buttonHeight + gap) + min(row, extra))
			# wybrana kategoria wyglada jak wcisniety przycisk (tak robi to wyszukiwarka F5)
			if index == self.category:
				button.Down()
				button.Disable()
			else:
				button.Enable()
				button.SetUp()
			button.Show()

	def __IsMouseOverSidebar(self):
		mouseX, mouseY = wndMgr.GetMousePosition()
		x, y = self.GetGlobalPosition()
		return (x + SIDEBAR_X <= mouseX < x + SIDEBAR_X + SIDEBAR_WIDTH) and (y + SIDEBAR_Y <= mouseY < y + SIDEBAR_Y + self.sidebarHeight)

	def SetSort(self, column):
		# MT2009_PLUS_AUCTION_HOUSE_UNIT_SORT_V1: "Cena" przechodzi kolejno przez
		# cene oferty rosnaco/malejaco i cene za sztuke rosnaco/malejaco
		if self.sortColumn == column and column == SORT_PRICE:
			if not self.sortDescending:
				self.sortDescending = True
			else:
				self.sortDescending = False
				self.priceSort = SORT_PRICE if self.priceSort == SORT_UNIT_PRICE else SORT_UNIT_PRICE
		elif self.sortColumn == column:
			self.sortDescending = not self.sortDescending
		else:
			self.sortColumn = column
			self.sortDescending = False
		self.__UpdateSortHeaders()
		self.Search()

	def __UpdateSortHeaders(self):
		priceLabel = "Cena/szt." if self.priceSort == SORT_UNIT_PRICE else "Cena"
		for column, label in ((SORT_COUNT, "Ilo\x9c\xe6"), (SORT_PRICE, priceLabel)):
			if column == self.sortColumn:
				label += " v" if self.sortDescending else " ^"
			self.sortLabels[column].SetText(label)

	# ---- blokada na jeden przedmiot ------------------------------------------
	def LockItem(self, data):
		vnum = data["vnum"]
		socket0 = -1
		if vnum in BOOK_VNUMS:
			try:
				socket0 = int(data.get("sockets", [0])[0])
			except:
				socket0 = -1
		name = self.GetItemName(data)
		if self.lockedItem and self.lockedItem[0] == vnum and self.lockedItem[1] == socket0:
			return
		self.lockedItem = None
		self.__SetSearchText(name[:32])
		self.lockedItem = (vnum, socket0, self.searchEdit.GetText())
		self.__HideSuggestions()
		self.__RefreshLock()
		self.Search()

	def UnlockItem(self):
		if not self.lockedItem:
			return
		self.lockedItem = None
		self.__SetSearchText("")
		self.__RefreshLock()
		self.Search()

	def __RefreshLock(self):
		if self.lockedItem:
			self.lockText.SetText("Tylko ten przedmiot")
			self.unlockButton.Show()
		else:
			self.lockText.SetText("")
			self.unlockButton.Hide()

	# ---- klasa postaci -------------------------------------------------------
	def ToggleClassPopup(self):
		if self.classPopup.IsShow():
			self.classPopup.Close()
			return
		x, y = self.classButton.GetGlobalPosition()
		self.classPopup.Open(x, y + self.classButton.GetHeight(), self.classFilter)

	def SetClassFilter(self, value):
		if value == self.classFilter:
			return
		self.classFilter = value
		self.__RefreshClassButton()
		self.Search()

	def ClearClassFilter(self):
		self.classPopup.Close()
		self.SetClassFilter(0)

	def __RefreshClassButton(self):
		label = "Klasa"
		for name, value in CLASS_DEFS:
			if value and value == self.classFilter:
				label = "Klasa: %s" % name
		self.classButton.SetText(label)

	# ---- poziom ulepszenia ---------------------------------------------------
	def ToggleRefinePopup(self):
		if self.refinePopup.IsShow():
			self.refinePopup.Close()
			return
		x, y = self.refineButton.GetGlobalPosition()
		self.refinePopup.Open(x, y, self.refineMin, self.refineMax)

	def ClearRefineRange(self):
		self.refinePopup.Close()
		if self.refineMin >= 0 or self.refineMax >= 0:
			self.SetRefineRange(-1, -1)

	def ClearBonusFilters(self):
		self.bonusDialog.Close()
		if self.bonusFilters or self.bonusCount:
			self.SetBonusFilters([], BONUS_AT_LEAST, 0)

	def SetRefineRange(self, minValue, maxValue):
		self.refineMin = minValue
		self.refineMax = maxValue
		self.__RefreshRefineButton()
		self.Search()

	def __RefreshRefineButton(self):
		if self.refineMin < 0 and self.refineMax < 0:
			label = "Poziom"
		elif self.refineMax < 0:
			label = "od +%d" % self.refineMin
		elif self.refineMin < 0:
			label = "do +%d" % self.refineMax
		elif self.refineMin == self.refineMax:
			label = "tylko +%d" % self.refineMin
		else:
			label = "+%d do +%d" % (self.refineMin, self.refineMax)
		self.refineButton.SetText(label)

	# ---- filtry: cena, poziom postaci, sztuki, plec (MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1)
	def __EmptyExtraFilter(self):
		return {"price": (0, 0), "level": (-1, -1), "count": (-1, -1), "sex": 0}

	def __HasExtraRanges(self):
		extra = self.extraFilter
		return extra["level"] != (-1, -1) or extra["count"] != (-1, -1) or extra["sex"] != 0

	def OpenFilterDialog(self):
		if self.filterDialog.IsShow():
			self.filterDialog.Close()
			return
		self.filterDialog.Open(self.extraFilter)

	def ClearExtraFilter(self):
		self.filterDialog.Close()
		if self.extraFilter != self.__EmptyExtraFilter():
			self.SetExtraFilter(self.__EmptyExtraFilter())

	def SetExtraFilter(self, values):
		self.extraFilter = values
		self.__RefreshFilterButton()
		self.Search()

	def __RefreshFilterButton(self):
		extra = self.extraFilter
		active = (1 if extra["price"] != (0, 0) else 0) + (1 if extra["level"] != (-1, -1) else 0)
		active += (1 if extra["count"] != (-1, -1) else 0) + (1 if extra["sex"] else 0)
		if active:
			self.filterButton.SetText("Filtry (%d)" % active)
		else:
			self.filterButton.SetText("Filtry")

	# ---- bonusy --------------------------------------------------------------
	def __GetBonusContext(self):
		# zestaw bonusow: z konkretnego przedmiotu, a jak go nie ma - z kategorii
		vnum = 0
		if self.lockedItem:
			vnum = self.lockedItem[0]
		elif self.uniqueVnum:
			vnum = self.uniqueVnum
		if vnum:
			attrSet = GetItemAttrSet(vnum)
			if attrSet is not None:
				item.SelectItem(vnum)
				return attrSet, item.GetItemName()
		label, parent, attrSet = CATEGORY_DEFS[self.category]
		if attrSet is not None:
			return attrSet, label
		return None, "wszystkie przedmioty"

	def __GetBonusOptions(self, attrSet):
		options = []
		for applyType, entries in self.bonusTable.items():
			values = set()
			for levels, maxLevels in entries:
				if attrSet is None:
					maxLevel = max(maxLevels)
				else:
					maxLevel = maxLevels[attrSet]
				for value in levels[:maxLevel]:
					if value:
						values.add(value)
			if values:
				options.append((applyType, sorted(values)))
		return options

	def OpenBonusDialog(self):
		self.__RequestBonusTable()
		attrSet, contextName = self.__GetBonusContext()
		self.bonusDialog.Open(self.__GetBonusOptions(attrSet), contextName, self.bonusFilters, self.bonusMode, self.bonusCount)

	def SetBonusFilters(self, filters, mode, count=0):
		self.bonusFilters = list(filters)[:BONUS_MAX]
		self.bonusMode = mode
		self.bonusCount = max(0, min(BONUS_MAX, count))
		self.__RefreshBonusButton()
		self.Search()

	def __RefreshBonusButton(self):
		active = len(self.bonusFilters) + (1 if self.bonusCount else 0)
		if active:
			self.bonusButton.SetText("Bonus (%d)" % active)
		else:
			self.bonusButton.SetText("Bonus")

	# ---- wynik ---------------------------------------------------------------
	def __UpdateStatus(self):
		if self.loading:
			self.statusText.SetText("Szukam...")
		else:
			self.statusText.SetText("Ofert: %d" % self.total)

	def __RefreshRows(self):
		for index in xrange(ROWS_PER_PAGE):
			if index < len(self.items):
				self.rows[index].SetData(self.items[index], index)
			else:
				self.rows[index].Clear()
		self.pageBox.SetText("%d / %d" % (self.page + 1, self.pageCount))
		if self.items or self.loading:
			self.emptyText.SetText("")
		else:
			self.emptyText.SetText("Brak ofert spe\xb3niaj\xb9cych kryteria")
		self.__RefreshSelection()
		self.__UpdateStatus()

	def FirstPage(self):
		if self.page > 0:
			self.__RequestPage(0)

	def LastPage(self):
		if self.page + 1 < self.pageCount:
			self.__RequestPage(self.pageCount - 1)

	def PreviousPage(self):
		if self.page > 0:
			self.__RequestPage(self.page - 1)

	def NextPage(self):
		if self.page + 1 < self.pageCount:
			self.__RequestPage(self.page + 1)

	def OnMouseWheel(self, length):
		# nad lista kategorii kolko przewija kategorie, poza nia - strony ofert
		if self.__IsMouseOverSidebar():
			if self.categoryScrollMax > 0:
				self.categoryScroll += -2 if length > 0 else 2
				self.__RelayoutCategories()
			return True
		now = app.GetTime()
		if now - self.lastWheelAt < WHEEL_GAP:
			return True
		self.lastWheelAt = now
		if length > 0:
			self.PreviousPage()
		elif length < 0:
			self.NextPage()
		return True

	def ShowItemToolTip(self, data):
		if self.tooltip:
			self.tooltip.ClearToolTip()
			self.tooltip.AddItemData(data["vnum"], data["sockets"], data["attrs"])
			self.tooltip.ShowToolTip()

	def HideItemToolTip(self):
		if self.tooltip:
			self.tooltip.HideToolTip()

	# ---- zaznaczanie ---------------------------------------------------------
	def IsSelected(self, data):
		return (data["owner"], data["id"]) in self.selected

	def ToggleSelected(self, data):
		key = (data["owner"], data["id"])
		if key in self.selected:
			del self.selected[key]
		else:
			self.selected[key] = data
		self.__RefreshSelection()

	def SelectPage(self):
		# naglowek: zaznacza cala strone, a gdy cala jest zaznaczona - odznacza ja
		if not self.items:
			return
		allSelected = len([data for data in self.items if not self.IsSelected(data)]) == 0
		for data in self.items:
			key = (data["owner"], data["id"])
			if allSelected:
				self.selected.pop(key, None)
			else:
				self.selected[key] = data
		self.__RefreshSelection()

	def ClearSelection(self):
		self.selected = {}
		self.__RefreshSelection()

	def __RefreshSelection(self):
		for row in self.rows:
			row.RefreshCheck()
		self.pageCheck.SetChecked(len(self.items) > 0 and len([data for data in self.items if not self.IsSelected(data)]) == 0)
		self.buySelectedButton.SetTextWithTail("Kup wybrane (%d" % len(self.selected), ")")

	# ---- zakupy --------------------------------------------------------------
	def __CanStartJob(self):
		if self.jobRunning:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Dom Aukcyjny: poprzednie zakupy jeszcze trwaj\xb9.")
			return False
		return True

	def __BeginJob(self):
		self.jobRunning = True
		self.jobDeadline = app.GetTime() + JOB_TIMEOUT

	def AskBuy(self, data):
		if not self.__CanStartJob():
			return
		if data["count"] > 1:
			self.quantityDialog.Open(data)
			return
		self.buyData = data
		self.__Ask(["Kupi\xe6 %s za %s?" % (self.GetItemName(data), Money(data["price"]))], self.__AcceptBuy)

	def __AcceptBuy(self):
		data = self.buyData
		self.__CancelQuestion()
		if data:
			self.SendBuy(data, data["count"])

	def SendBuy(self, data, quantity):
		if not self.__CanStartJob():
			return
		quantity = max(1, min(int(quantity), data["count"]))
		if quantity == data["count"]:
			quantity = 0		# cala oferta
		self.__BeginJob()
		self.__Send("/ah_buy %d %d %d %d" % (data["owner"], data["id"], quantity, data["price"]))

	def AskBuySelected(self):
		if not self.__CanStartJob():
			return
		if not self.selected:
			self.__Popup(["Zaznacz oferty, kt\xf3re chcesz kupi\xe6."])
			return
		total = sum([data["price"] for data in self.selected.values()])
		self.__Ask(["Kupi\xe6 zaznaczone oferty: %d?" % len(self.selected), "Razem: %s" % Money(total)], self.__AcceptBuySelected)

	def __AcceptBuySelected(self):
		self.__CancelQuestion()
		if not self.selected or not self.__CanStartJob():
			return
		# lista idzie w kilku komendach (kazda do COMMAND_MAX znakow), od najtanszej oferty
		offers = sorted(self.selected.values(), key=lambda data: data["price"])
		reset = 1
		entries = []
		for data in offers:
			entry = "%d:%d:%d" % (data["owner"], data["id"], data["price"])
			if entries and len("/ah_cart_add 1 " + ",".join(entries + [entry])) > COMMAND_MAX:
				self.__Queue("/ah_cart_add %d %s" % (reset, ",".join(entries)))
				reset = 0
				entries = []
			entries.append(entry)
		if entries:
			self.__Queue("/ah_cart_add %d %s" % (reset, ",".join(entries)))
		self.__Queue("/ah_cart_buy")
		self.__BeginJob()
		self.jobDeadline += len(self.sendQueue) * SEND_GAP

	# "Kup wiele": najpierw pytanie o liczbe sztuk, potem wycena z serwera
	def AskBuyBulk(self):
		if not self.__CanStartJob():
			return
		if self.lockedItem:
			target = (self.lockedItem[0], self.lockedItem[1])
		elif self.uniqueVnum and not self.loading:
			target = (self.uniqueVnum, self.uniqueSocket0)
		else:
			self.__Popup(["Kup wiele dzia\xb3a dla jednego przedmiotu.", "Wpisz jego pe\xb3n\xb9 nazw\xea albo kliknij ofert\xea prawym przyciskiem."])
			return
		self.__CloseBulkInput()
		self.bulkTarget = target
		dialog = uiCommon.InputDialog()
		dialog.SetTitle("Ile sztuk kupi\xe6?")
		dialog.SetNumberMode()
		dialog.SetMaxLength(5)
		dialog.SetAcceptEvent(ui.__mem_func__(self.__AcceptBulkCount))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseBulkInput))
		dialog.Open()
		self.bulkInput = dialog

	def __CloseBulkInput(self):
		if self.bulkInput:
			self.bulkInput.Close()
			self.bulkInput = None
		return True

	def __AcceptBulkCount(self):
		if not self.bulkInput:
			return True
		wanted = min(ToInt(self.bulkInput.GetText()), BULK_MAX)
		self.__CloseBulkInput()
		if wanted <= 0 or not self.bulkTarget or not self.__CanStartJob():
			return True
		vnum, socket0 = self.bulkTarget
		self.requestId += 1
		self.quoteRequest = self.requestId
		self.quoteWanted = wanted
		prefix = "/ah_bulk_quote %d %d " % (self.quoteRequest, wanted)
		self.__Send(prefix + self.__BuildFilter(len(prefix), vnum, socket0))
		return True

	def __OnBulkQuote(self, request, token, pieces, offers, cost, available):
		if request != self.quoteRequest:
			return
		self.quoteRequest = 0
		if pieces <= 0:
			self.__Popup(["Nie ma ofert tego przedmiotu do kupienia."])
			return
		self.quoteToken = token
		lines = ["Kupi\xe6 %d szt. (ofert: %d) za %s?" % (pieces, offers, Money(cost))]
		if pieces < self.quoteWanted:
			lines.append("Chcia\xb3e\x9c %d szt., a tyle da si\xea kupi\xe6." % self.quoteWanted)
		else:
			lines.append("Na rynku jest razem %d szt." % available)
		self.__Ask(lines, self.__AcceptBulk)

	def __AcceptBulk(self):
		self.__CancelQuestion()
		if not self.__CanStartJob():
			return
		self.__BeginJob()
		self.__Send("/ah_bulk_buy %d" % self.quoteToken)

	# ---- odpowiedzi serwera --------------------------------------------------
	def OnServerCommand(self, name, args):
		if name == "AHNames":
			self.__OnNames(args)		# lista vnumow, nie same liczby
			return
		try:
			values = [int(arg) for arg in args]
		except:
			return
		if name == "AHSearch" and len(values) >= 6:
			self.pendingHeader = values[:6]
		elif name == "AHBusy" and len(values) >= 1:
			if values[0] == self.requestId and self.loading:
				self.searchAt = app.GetTime() + SEARCH_GAP
			elif values[0] == self.quoteRequest:
				self.quoteRequest = 0
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Dom Aukcyjny: spr\xf3buj jeszcze raz za chwil\xea.")
		elif name == "AHBonusBegin":
			self.bonusIncoming = {}
		elif name == "AHBonus" and len(values) >= 15:
			if self.bonusIncoming is not None:
				self.bonusIncoming.setdefault(values[1], []).append((values[2:7], values[7:15]))
		elif name == "AHBonusEnd":
			if self.bonusIncoming is not None:
				changed = self.bonusIncoming != self.bonusTable
				self.bonusTable = self.bonusIncoming
				self.bonusIncoming = None
				if changed and self.bonusDialog and self.bonusDialog.IsShow():
					# okno bonusow jest otwarte: nowe wartosci od razu
					attrSet, contextName = self.__GetBonusContext()
					self.bonusDialog.UpdateOptions(self.__GetBonusOptions(attrSet))
		elif name == "AHBuyResult" and len(values) >= 6:
			self.__OnBuyResult(values[0], values[1], values[2], values[3])
		elif name == "AHJobDone" and len(values) >= 6:
			self.__OnJobDone(values[0], values[1], values[2], values[3], values[4], values[5])
		elif name == "AHJobRefused" and len(values) >= 2:
			self.jobRunning = False
			self.__Popup([STOP_REASONS.get(values[1], "Nie mo\xbfna teraz kupi\xe6.")])
		elif name == "AHBulkQuote" and len(values) >= 6:
			self.__OnBulkQuote(values[0], values[1], values[2], values[3], values[4], values[5])

	def __OnBuyResult(self, owner, itemId, ok, reason):
		self.jobDeadline = app.GetTime() + JOB_TIMEOUT
		if ok:
			return
		data = self.selected.get((owner, itemId))
		if data is None:
			for other in self.items:
				if other["owner"] == owner and other["id"] == itemId:
					data = other
					break
		name = self.GetItemName(data) if data else "oferta"
		chat.AppendChat(chat.CHAT_TYPE_INFO, "Dom Aukcyjny: %s - %s." % (name, BUY_REASONS.get(reason, "nie kupiono")))

	def __OnJobDone(self, kind, okCount, total, pieces, spent, reason):
		self.jobRunning = False
		if kind == JOB_SINGLE:
			lines = []
			if okCount:
				lines.append("Kupiono %d szt. za %s." % (pieces, Money(spent)))
			elif reason == 0:
				lines.append("Nie uda\xb3o si\xea kupi\xe6 tej oferty.")
		else:
			lines = ["Kupiono %d z %d ofert: %d szt. za %s." % (okCount, total, pieces, Money(spent))]
		if reason:
			lines.append(STOP_REASONS.get(reason, "Zakupy przerwane."))
		if kind == JOB_CART:
			self.ClearSelection()
		if kind == JOB_SINGLE and okCount and not reason:
			for line in lines:
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Dom Aukcyjny: %s" % line)
		elif lines:
			self.__Popup(lines)
		if self.IsShow():
			self.__RequestPage(self.page)

	# stan linii po zakupie czesci stosu albo gdy oferta sie zmienila
	def UpdateStackOffer(self, ownerID, itemID, remainingCount, remainingYang, remainingCheque=0):
		for data in self.items + self.selected.values():
			if data["owner"] == ownerID and data["id"] == itemID:
				data["count"] = remainingCount
				data["price"] = remainingYang
		if self.IsShow():
			self.__RefreshRows()

	# ---- wywolania z modulu ikashop ------------------------------------------
	def SetSearchResultItems(self, items):
		header = self.pendingHeader
		self.pendingHeader = None
		if header is None or header[0] != self.requestId:
			return		# odpowiedz na stare zapytanie
		self.loading = False
		self.page = header[1]
		self.pageCount = max(1, header[2])
		self.total = header[3]
		self.uniqueVnum = header[4]
		self.uniqueSocket0 = header[5]
		self.searchPage = self.page
		self.items = [data for data in items if not data.get("is_auction")]
		# zaznaczone oferty pokazuja dane z ostatnio widzianej strony
		for data in self.items:
			key = (data["owner"], data["id"])
			if key in self.selected:
				self.selected[key] = data
		self.__RefreshRows()

	def DeleteSearchResultItem(self, itemID):
		for key in self.selected.keys():
			if key[1] == itemID:
				del self.selected[key]
		self.items = [data for data in self.items if data["id"] != itemID]
		if self.IsShow():
			self.__RefreshRows()

	# Serwer wprowadzil juz gracza do sklepu, gdy to przychodzi - sklepu nie wolno
	# porzucic (niewidoczny sklep goscia blokuje NPC, zmiane kanalu i wylogowanie).
	def OpenShopGuest(self, data):
		self.Close()
		try:
			if self.guestBoard:
				self.guestBoard.OpenShopGuest(data)
				return
		except:
			pass
		ikashop.SendCloseShopGuestBoard()

	def ShopExpiredGuesting(self, id):
		if self.guestBoard:
			self.guestBoard.ShopExpiredGuesting(id)

	def ShopGuestRemoveItem(self, itemID):
		if self.guestBoard:
			self.guestBoard.ShopGuestRemoveItem(itemID)

	def ShopGuestEditItem(self, itemID, price):
		if self.guestBoard:
			self.guestBoard.ShopGuestEditItem(itemID, price)

	# ---- zegar ---------------------------------------------------------------
	def OnUpdate(self):
		# zadnych zapytan w drodze na inny core (warpsafe.py)
		try:
			import warpsafe
			if not warpsafe.InGame():
				return
		except ImportError:
			pass
		now = app.GetTime()

		if now >= self.optionsAt or now < self.optionsAt - OPTIONS_POLL - 1.0:
			self.optionsAt = now + OPTIONS_POLL
			self.__SyncOptions()

		if self.sendQueue and now >= self.nextSendAt:
			self.nextSendAt = now + SEND_GAP
			for command in self.sendQueue[:SEND_BATCH]:
				self.__Send(command)
			del self.sendQueue[:SEND_BATCH]

		if self.namesAt is not None and now >= self.namesAt:
			self.namesAt = None
			self.__SendNames()

		if self.searchAt is not None and now >= self.searchAt:
			self.searchAt = None
			self.__SendSearch()

		if self.loading and now - self.requestAt > SEARCH_TIMEOUT:
			self.loading = False
			self.statusText.SetText("Serwer nie odpowiedzia\xb3 - spr\xf3buj ponownie.")

		if self.jobRunning and now > self.jobDeadline:
			self.jobRunning = False
