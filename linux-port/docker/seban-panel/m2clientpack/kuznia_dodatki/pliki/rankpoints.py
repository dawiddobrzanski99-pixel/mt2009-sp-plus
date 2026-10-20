# MT2009_RANK_BADGES_V4
# MT2009_PLUS_RANK_POINTS_V1 - Punkty Rangi: the extra ranks raised by eating the rank
# fruits (Jablko, Gruszka, Winogrono, Arbuz, Ananas - Arezzo's "dodatkowe rangi"; the
# server: playerbot_rank_points.h, server-patches/rankpoints).
#
# MT2009_PLUS_RANK_POINTS_V2 - ONE scale: the game's own alignment ("Punkty Rangi",
# up to 20 000) is its bottom, Arezzo's points continue it above 20 000:
#   total = alignment            while the alignment is under 20 000
#   total = 20 000 + Arezzo's    once the alignment stands at 20 000
# Jablko raises the alignment itself (0 - 20 000), the other fruits the points above it.
# The character window's alignment tooltip shows that ONE total (uicharacter.py,
# BuildAlignmentToolTip); under 20 000 it is the client's live alignment, above it the
# server's "RANGA self". A server that never sent "RANGA self": the old tooltip.
#
# From 21 000 points a character's rank stands, in the rank's own colour, where its
# alignment title stood (Arezzo's names and colours, colorinfo.py TITLE_RGB_GOOD_*):
#
#   "RANGA tail <vid> <tier>"     a character with a rank came into view (or its rank
#                                 changed); tier 0 = the alignment title again
#   "RANGA self <total> <tier>"   the player's own total (V2; V1: its separate points),
#                                 for the character window's alignment tooltip
#
# An exe with ENABLE_RANK_TITLE (client-patches/exe) keeps the rank on the character
# (chrmgr.SetRankTitle) and draws it whenever it draws the title; with an older exe the
# keeper below puts it back over the alignment title every half second
# (textTail.AttachTitle), the exe drawing the alignment title in between.
#
# CP1250 as escapes, like every name the client draws.

POINTS_MAX = 200000
ALIGN_CAP = 20000	# the alignment's cap as shown; the Arezzo points start here

# tier: (from, Polish name, English name, colour)
TIERS = {
	1: (0, 'Turysta z M1', 'Turysta z M1', (215, 225, 235)),
	2: (1000, 'Klepacz Dzik\xf3w', 'Klepacz Dzik\xf3w', (100, 255, 160)),
	3: (3000, 'S\xb9siad Kowala', 'S\xb9siad Kowala', (80, 235, 235)),
	4: (6000, 'Sponsor Kowala', 'Sponsor Kowala', (100, 165, 255)),
	5: (10000, 'Czytelnik Nieudanych KU', 'Czytelnik Nieudanych KU', (200, 165, 255)),
	6: (16000, 'M\xb3ot na Metiny', 'M\xb3ot na Metiny', (180, 115, 255)),
	7: (30000, 'Sta\xb3y Klient Dozorcy', 'Sta\xb3y Klient Dozorcy', (255, 135, 185)),
	8: (50000, 'Lokator Loch\xf3w', 'Lokator Loch\xf3w', (255, 175, 80)),
	9: (80000, 'Windykator Boss\xf3w', 'Windykator Boss\xf3w', (255, 105, 105)),
	10: (110000, 'Postrach Serwera', 'Postrach Serwera', (255, 195, 90)),
	11: (150000, 'Ostatni Przed Emerytur\xb9', 'Ostatni Przed Emerytur\xb9', (255, 220, 100)),
	12: (200000, 'Emeryt Olimpu', 'Emeryt Olimpu', (255, 240, 165)),
}

# MT2009_PLUS_FEMALE_TITLES_V1 (Autor: Digi Rasta, Extended-Alignment, nowy-system 0.28): the
# female forms, over a woman's head (an exe with chrmgr.RegisterRankTitleFemale) and in a woman's
# character window. A tier without one keeps its name (Legenda is both).
TIERS_FEMALE = {}
# The alignment titles (localeInfo.TITLE_NAME_LIST, grades 0-8) in the female form - his list.
ALIGNMENT_FEMALE = ("Rycerska", "Szlachetna", "Dobra", "Przyjazna", "Neutralna", "Agresywna",
	"Nieuczciwa", "Z\xb3o\x9cliwa", "Okrutna")

# tier: (monsters %, people %, Metins %, bosses %, average damage %, HP) - = the server's TIERS
BONUS = {}  # superseded by RewardValues
BONUS_LABELS = (
	"Silny przeciwko potworom +%d%%",
	"Silny przeciwko ludziom +%d%%",
	"Silny przeciwko Metinom +%d%%",
	"Silny przeciwko bossom +%d%%",
	"\x8crednie obra\xbfenia +%d%%",
	"Maks. P\xaf +%d",
)

# (from, to, name, points a piece) - V2: four times V1's 50 / 50 / 100 / 100 / 100
FRUITS = (
	(0, 20000, "Jab\xb3ko", 200),
	(20000, 40000, "Gruszka", 200),
	(40000, 80000, "Winogrono", 400),
	(80000, 120000, "Arbuz", 400),
	(120000, 200000, "Ananas", 400),
)

TEXT_NEXT = "Nast\xeapna: %s od %d"
TEXT_FRUIT = "Teraz jedz: %s (+%d)"
TEXT_MAX = "Najwy\xbfsza ranga"
TEXT_TOTAL = "Punkty Rangi: %d"
TEXT_NEGATIVE = "Owoce rangi dzia\xb3aj\xb9 od 0 punkt\xf3w"

REFRESH_SECONDS = 0.5

_english = False
try:
	import systemSetting
	_english = systemSetting.GetLanguage() == "en"
except Exception:
	pass


def TierName(tier, female=False):
	t = TIERS.get(tier)
	if not t:
		return ""
	if _english:
		return t[2]
	if female and tier in TIERS_FEMALE:
		return TIERS_FEMALE[tier]
	return t[1]


def IsPlayerFemale():
	"""The player's own character is a woman (chr.RaceToSex: 0)."""
	try:
		import chr
		import player
		return chr.RaceToSex(player.GetRace()) == 0
	except Exception:
		return False


def AlignmentTitle(grade, female=None):
	"""The alignment title of a grade, in the female form for a woman (Polish only)."""
	import localeInfo
	if female is None:
		female = IsPlayerFemale()
	if female and not _english and 0 <= grade < len(ALIGNMENT_FEMALE):
		return ALIGNMENT_FEMALE[grade]
	return localeInfo.TITLE_NAME_LIST[grade]


def RegisterFemaleTitles():
	"""The female alignment titles for the exe (introloading.py, next to RegisterTitleName);
	nothing in English or with an exe without chrmgr.RegisterTitleNameFemale."""
	import chrmgr
	if _english or not hasattr(chrmgr, "RegisterTitleNameFemale"):
		return
	for grade, name in enumerate(ALIGNMENT_FEMALE):
		chrmgr.RegisterTitleNameFemale(grade, name)


def TierOf(points):
	tier = 0
	for t, row in TIERS.items():
		if points >= row[0] and t > tier:
			tier = t
	return tier


def FruitFor(points):
	for row in FRUITS:
		if row[0] <= points < row[1]:
			return row
	return None


_registered = False


def _Register():
	global _registered
	if _registered:
		return
	_registered = True
	import chrmgr
	if not hasattr(chrmgr, "RegisterRankTitle"):
		return
	for tier, row in TIERS.items():
		(r, g, b) = row[3]
		chrmgr.RegisterRankTitle(tier, __import__("rankbadges").PlaceholderName(tier), r, g, b) # RANK_SIDE_GOTHIC_V1
	# MT2009_PLUS_FEMALE_TITLES_V1: the ranks' female forms over a woman's head
	if hasattr(chrmgr, "RegisterRankTitleFemale"):
		for tier in TIERS:
			chrmgr.RegisterRankTitleFemale(tier, __import__("rankbadges").PlaceholderName(tier))


def HasNativeTitle():
	import chrmgr
	return hasattr(chrmgr, "SetRankTitle")


def _ToInt(value, default=None):
	try:
		return int(value)
	except (ValueError, TypeError):
		return default


def _Vid(value):
	vid = _ToInt(value)
	if vid is None or vid <= 0 or vid > 0xffffffff:
		return None
	# the text tail and chrmgr read the VID as a signed int
	if vid >= 0x80000000:
		vid -= 0x100000000
	return vid


class Keeper(object):
	"""With an exe without chrmgr.SetRankTitle: every rank heard of, put back over
	the alignment title every REFRESH_SECONDS while its character is in view."""

	def __init__(self):
		self.titles = {}
		self.nextRefresh = 0.0

	def Set(self, vid, tier):
		if tier in TIERS:
			self.titles[vid] = tier
			self.Attach(vid, tier)
		elif vid in self.titles:
			del self.titles[vid]

	def Attach(self, vid, tier):
		import textTail
		(r, g, b) = TIERS[tier][3]
		textTail.AttachTitle(vid, __import__("rankbadges").PlaceholderName(tier), r / 255.0, g / 255.0, b / 255.0)

	def CanUpdate(self):
		return bool(self.titles)

	def OnUpdate(self):
		import app
		now = app.GetTime()
		if now < self.nextRefresh:
			return
		self.nextRefresh = now + REFRESH_SECONDS
		import chr
		for vid, tier in list(self.titles.items()):
			if not chr.HasInstance(vid):
				del self.titles[vid]
				continue
			self.Attach(vid, tier)

	def Destroy(self):
		self.titles = {}


_keeper = None


def GetKeeper():
	global _keeper
	if _keeper is None:
		_keeper = Keeper()
	return _keeper


# The player's own points ("RANGA self"), None until the server says.
selfPoints = None
selfTier = 0


def OnCommand(*args):
	global selfPoints, selfTier
	if not args:
		return False
	if args[0] == "self" and len(args) >= 3:
		selfPoints = max(-ALIGN_CAP, min(_ToInt(args[1], 0), POINTS_MAX))
		selfTier = _ToInt(args[2], 0)
		import player
		vid = player.GetMainCharacterIndex()
		if vid:
			__import__("rankbadges").Set(vid, selfTier)
	elif args[0] == "tail" and len(args) >= 3:
		vid = _Vid(args[1])
		if vid is not None:
			__import__("rankbadges").Set(vid, _ToInt(args[2], 0))
	return False


def Total(alignment):
	"""The one total of the scale from the client's live alignment (as shown) and the
	server's last "RANGA self"; None when the server never sent it."""
	if selfPoints is None:
		return None
	if alignment < ALIGN_CAP:
		return alignment
	return max(ALIGN_CAP, selfPoints)


# RANK_CUMULATIVE_REWARDS_V3: totals for all positive alignment ranks.
REWARD_THRESHOLDS = (0, 1000, 3000, 6000, 10000, 16000, 30000, 50000, 80000, 110000, 150000, 200000)
REWARD_NAMES = ('Turysta z M1', 'Klepacz Dzik\xf3w', 'S\xb9siad Kowala', 'Sponsor Kowala', 'Czytelnik Nieudanych KU', 'M\xb3ot na Metiny', 'Sta\xb3y Klient Dozorcy', 'Lokator Loch\xf3w', 'Windykator Boss\xf3w', 'Postrach Serwera', 'Ostatni Przed Emerytur\xb9', 'Emeryt Olimpu')
REWARD_LABELS = ("Obrona +%d", "Sila kazdego zywiolu +%d%%", "Odpornosc na kazdy zywiol +%d%%", "Szybkosc ataku +%d%%", "Szybkosc ruchu +%d%%", "Silny przeciwko metinom +%d%%")

def RewardStage(points):
	return sum(1 for threshold in REWARD_THRESHOLDS if points >= threshold)

def RewardValues(stage):
	stage = max(0, min(12, int(stage)))
	return (stage * 30 // 12, stage * 20 // 12, stage * 20 // 12,
		(stage // 2) * 10 // 6, (stage // 2) * 10 // 6, stage // 2)


def AppendRankRewards(toolTip, total):
	stage = RewardStage(total)
	current = RewardValues(stage)
	green = getattr(toolTip, "POSITIVE_COLOR", 0xff6cff6c)
	red = getattr(toolTip, "NEGATIVE_COLOR", 0xffff6666)
	toolTip.AutoAppendTextLine("Obecne bonusy rangi:", green)
	for label, value in zip(REWARD_LABELS, current):
		if value > 0:
			toolTip.AutoAppendTextLine(label % value, green)
	if not any(current):
		toolTip.AutoAppendTextLine("Brak bonusow przy ujemnej randze", green)
	if stage < len(REWARD_THRESHOLDS):
		toolTip.AutoAppendTextLine("Nastepna: %s (%d pkt)" % (REWARD_NAMES[stage], REWARD_THRESHOLDS[stage]), red)
		future = RewardValues(stage + 1)
		for label, now, later in zip(REWARD_LABELS, current, future):
			if later > now:
				toolTip.AutoAppendTextLine(label % (later - now), red)
	else:
		toolTip.AutoAppendTextLine("Osiagnieto najwyzsza range")

def BuildAlignmentToolTip(toolTip, alignment, gradeTitle, gradeColor, pointsLabel=None):
	"""The whole alignment tooltip on the one scale: the rank (or the alignment's title
	under the first rank), ONE "Punkty Rangi: <total>", the rank's bonus, the next rank
	and the fruit wanted now. False (nothing written) when the server never sent
	"RANGA self" - the caller writes the old tooltip."""
	total = Total(alignment)
	if total is None:
		return False
	import ui
	tier = TierOf(total)
	female = IsPlayerFemale()
	if tier:
		(r, g, b) = TIERS[tier][3]
		toolTip.AutoAppendTextLine(TierName(tier, female), ui.GenerateColor(r, g, b))
	else:
		toolTip.AutoAppendTextLine(gradeTitle, gradeColor)
	if pointsLabel:
		toolTip.AutoAppendTextLine(pointsLabel + str(total))
	else:
		toolTip.AutoAppendTextLine(TEXT_TOTAL % total)
	AppendRankRewards(toolTip, total)
	fruit = FruitFor(total)
	if fruit:
		toolTip.AutoAppendTextLine(TEXT_FRUIT % (fruit[2], fruit[3]))
	elif total < 0:
		toolTip.AutoAppendTextLine(TEXT_NEGATIVE)
	else:
		toolTip.AutoAppendTextLine(TEXT_MAX)
	return True
