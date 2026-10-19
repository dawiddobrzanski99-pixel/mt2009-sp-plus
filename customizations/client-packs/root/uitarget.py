import app

import eventManager
import ui
import player
import net
import wndMgr
import messenger
import guild
import chr
import nonplayer
import localeInfo
import constInfo
import uiAffectBar
import uiReport
import mobraceflag # MT2009_PLUS_TARGET_BONUS_V1 (Autor: Vekirion)
from _weakref import proxy

# MT2009_TARGET_BONUS_V2: the same additive bonuses as battle.cpp CalcAttBonus.
# Values are read from player.GetStatus on every target refresh, including
# current equipment, guild and quest affects. ATT_* elements use a separate
# damage calculation and are not race bonuses.
def _GetTargetBonusPoint(name, serverIndex):
	if hasattr(player, name):
		return getattr(player, name)
	if getattr(player, "POINT_ATTBONUS_HUMAN", -1) == 43:
		return serverIndex
	return -1

TARGET_BONUS_RACE_LIST = (
	(mobraceflag.ANIMAL, "Zwierz\xeatom", _GetTargetBonusPoint("POINT_ATTBONUS_ANIMAL", 44)),
	(mobraceflag.UNDEAD, "Nieumar\xb3ym", _GetTargetBonusPoint("POINT_ATTBONUS_UNDEAD", 47)),
	(mobraceflag.DEVIL, "Diab\xb3om", _GetTargetBonusPoint("POINT_ATTBONUS_DEVIL", 48)),
	(mobraceflag.HUMAN, "Ludziom", _GetTargetBonusPoint("POINT_ATTBONUS_HUMAN", 43)),
	(mobraceflag.ORC, "Orkom", _GetTargetBonusPoint("POINT_ATTBONUS_ORC", 45)),
	(mobraceflag.MILGYO, "Mistykom", _GetTargetBonusPoint("POINT_ATTBONUS_MILGYO", 46)),
	(mobraceflag.INSECT, "Owadom", _GetTargetBonusPoint("POINT_ATTBONUS_INSECT", 49)),
	(mobraceflag.FIRE, "Ognistym potworom", _GetTargetBonusPoint("POINT_ATTBONUS_FIRE", 50)),
	(mobraceflag.ICE, "Lodowym potworom", _GetTargetBonusPoint("POINT_ATTBONUS_ICE", 51)),
	(mobraceflag.DESERT, "Potworom pustyni", _GetTargetBonusPoint("POINT_ATTBONUS_DESERT", 52)),
	(mobraceflag.TREE, "Le\x9cnym potworom", _GetTargetBonusPoint("POINT_ATTBONUS_TREE", 58)),
)
TARGET_BONUS_MONSTER_POINT = _GetTargetBonusPoint("POINT_ATTBONUS_MONSTER", 53)
TARGET_BONUS_BOSS_POINT = _GetTargetBonusPoint("POINT_ATTBONUS_BOSS", 150)
TARGET_BONUS_STONE_POINT = _GetTargetBonusPoint("POINT_ATTBONUS_STONE", 149)
TARGET_BONUS_VALLEY_POINT = _GetTargetBonusPoint("POINT_ATTBONUS_ORC_VALLEY", 148)

def _GetTargetBonusEntry(name, point):
	if point < 0:
		return name
	return "%s %d%%" % (name, player.GetStatus(point))

def _IsTargetBonusValleyMap():
	# CalcAttBonus tests the attacker's exact map index, not race or region.
	getter = getattr(player, "GetMapIndex", None)
	if getter is not None:
		try:
			return int(getter()) == 64
		except Exception:
			return False
	try:
		import background
		return str(background.GetCurrentMapName()) == "map_n_threeway"
	except Exception:
		return False

def GetTargetBonusText(vid):
	vnum = nonplayer.GetVnumByVID(vid)
	if vnum <= 0:
		return ""
	instanceType = chr.GetInstanceType(vid)
	isStone = instanceType == getattr(chr, "INSTANCE_TYPE_STONE", 2)
	if instanceType != chr.INSTANCE_TYPE_ENEMY and not isStone:
		return ""

	info = mobraceflag.GetInfo(vnum)
	if info is not None:
		mobType, grade, raceFlag = info
		# Database types: MONSTER=0, STONE=2. Never label friendly NPCs or PCs.
		if mobType not in (0, 2):
			return ""
		isStone = mobType == 2
	else:
		grade = nonplayer.GetGradeByVID(vid)
		raceFlag = mobraceflag.Get(vnum)

	parts = [(name, point) for flag, name, point in TARGET_BONUS_RACE_LIST if raceFlag & flag]
	if grade >= nonplayer.BOSS:
		if isStone:
			parts.append(("Metinom", TARGET_BONUS_STONE_POINT))
		else:
			parts.append(("Bossom", TARGET_BONUS_BOSS_POINT))
	# This applies to every monster/stone, even when its race flags are empty.
	parts.append(("Potworom", TARGET_BONUS_MONSTER_POINT))
	if TARGET_BONUS_VALLEY_POINT >= 0 and player.GetStatus(TARGET_BONUS_VALLEY_POINT) and _IsTargetBonusValleyMap():
		parts.append(("W Dolinie Ork\xf3w", TARGET_BONUS_VALLEY_POINT))
	entries = [_GetTargetBonusEntry(name, point) for name, point in parts]
	if all(point >= 0 for name, point in parts):
		# These points are summed by CalcAttBonus before its single percentage.
		total = sum(player.GetStatus(point) for name, point in parts)
		entries.append("Razem %d%%" % total)
	return "Silny przeciwko: " + ", ".join(entries)

if app.ENABLE_ELEMENTAL_TARGET:
	ELEMENTAL_PATH = "d:/ymir work/ui/game/12zi/element/{}.sub"

	SUB_RACE_FLAG_TO_FILENAME = {
		nonplayer.RACE_FLAG_ATT_ELEC:	ELEMENTAL_PATH.format("elect"),
		nonplayer.RACE_FLAG_ATT_FIRE:	ELEMENTAL_PATH.format("fire"),
		nonplayer.RACE_FLAG_ATT_ICE:	ELEMENTAL_PATH.format("ice"),
		nonplayer.RACE_FLAG_ATT_WIND:	ELEMENTAL_PATH.format("wind"),
		nonplayer.RACE_FLAG_ATT_EARTH:	ELEMENTAL_PATH.format("earth"),
		nonplayer.RACE_FLAG_ATT_DARK:	ELEMENTAL_PATH.format("dark"),
	}

	def GetElementalFilename(mobVnum):
		if not mobVnum:
			return ""

		dwRaceFlag = nonplayer.GetMonsterRaceFlag(mobVnum)
		for k,v in SUB_RACE_FLAG_TO_FILENAME.iteritems():
			curFlag = k
			if HAS_FLAG(dwRaceFlag, curFlag):
				return v
		return ""

	def HAS_FLAG(value, flag):
		return (value & flag) == flag

# MT2009_PLUS_TARGET_POISON_GAUGE_V1: whether a character in view is poisoned,
# for its gauge (Kiciamol, 9 October). chrmgr.HasAffectByVID and chr.AFF_POISON
# are in our exe (PythonCharacterManagerModule.cpp, PythonCharacterModule.cpp);
# the target's affect list (chr.AFFECT_POISON) is the fallback. Any error is
# "not poisoned": the gauge stays red.
def IsPoisonedTarget(vid, affects):
	if not vid:
		return False
	try:
		import chrmgr
		if chrmgr.HasAffectByVID(vid, chr.AFF_POISON):
			return True
	except Exception:
		pass
	try:
		return chr.AFFECT_POISON in affects
	except Exception:
		return False

# The green picture comes with the client's root pack
# (client-patches/client-2.0.30/atlas/d_/ymir work/ui/pattern/gauge_green.tga);
# a client without it keeps the red gauge instead of an empty one.
POISON_GAUGE_IMAGE = "d:/ymir work/ui/pattern/gauge_green.tga"
_poisonGaugeImage = {}

def HasPoisonGaugeImage():
	if "exists" not in _poisonGaugeImage:
		try:
			_poisonGaugeImage["exists"] = bool(app.IsExistFile(POISON_GAUGE_IMAGE))
		except Exception:
			_poisonGaugeImage["exists"] = False
	return _poisonGaugeImage["exists"]

class CompactDropButton(ui.Button):
	def __init__(self):
		ui.Button.__init__(self)
		self.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		self.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		self.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		self.cover = ui.Bar()
		self.cover.SetParent(self)
		self.cover.SetPosition(3, 3)
		self.cover.SetSize(9, 9)
		self.cover.SetColor(0xFF171717)
		self.cover.AddFlag("not_pick")
		self.cover.Show()
		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.SetPosition(8, -2)
		self.label.SetHorizontalAlignCenter()
		self.label.SetOutline(True)
		self.label.SetText("?")
		self.label.AddFlag("not_pick")
		self.label.Show()

def IsDropPreviewTarget(vid):
	if nonplayer.GetVnumByVID(vid) <= 0:
		return False
	return chr.GetInstanceType(vid) in (chr.INSTANCE_TYPE_ENEMY, getattr(chr, "INSTANCE_TYPE_STONE", 2))

# MT2009_PLUS_SIDEKICK_ZODIAC_V1: "Wskrzeszenie" on a character's target board
# in the Swiatynia Zodiaku - the temple's revive window for somebody else (a
# fallen Towarzysz, a party member): "/revivedialog <vid>", and the window's
# "Tak" spends the Prisms of Revival ("/revive <vid>").
TARGET_BUTTON_REVIVE = getattr(localeInfo, "TARGET_BUTTON_REVIVE", "Wskrzeszenie")

class TargetBoard(ui.ThinBoard):

	BUTTON_NAME_LIST = (
		localeInfo.TARGET_BUTTON_WHISPER,
		localeInfo.TARGET_BUTTON_EXCHANGE,
		localeInfo.TARGET_BUTTON_FIGHT,
		localeInfo.TARGET_BUTTON_ACCEPT_FIGHT,
		localeInfo.TARGET_BUTTON_AVENGE,
		localeInfo.TARGET_BUTTON_FRIEND,
		localeInfo.TARGET_BUTTON_INVITE_PARTY,
		localeInfo.TARGET_BUTTON_LEAVE_PARTY,
		localeInfo.TARGET_BUTTON_EXCLUDE,
		localeInfo.TARGET_BUTTON_INVITE_GUILD,
		localeInfo.TARGET_BUTTON_DISMOUNT,
		localeInfo.TARGET_BUTTON_EXIT_OBSERVER,
		localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT,
		localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY,
		localeInfo.TARGET_BUTTON_BUILDING_DESTROY,
		localeInfo.TARGET_BUTTON_EMOTION_ALLOW,
		"VOTE_BLOCK_CHAT",
		localeInfo.TARGET_BUTTON_REPORT,
		"Sprawdz",
		"EQ",
		TARGET_BUTTON_REVIVE,
	)

	GRADE_NAME =	{
						nonplayer.PAWN : localeInfo.TARGET_LEVEL_PAWN,
						nonplayer.S_PAWN : localeInfo.TARGET_LEVEL_S_PAWN,
						nonplayer.KNIGHT : localeInfo.TARGET_LEVEL_KNIGHT,
						nonplayer.S_KNIGHT : localeInfo.TARGET_LEVEL_S_KNIGHT,
						nonplayer.BOSS : localeInfo.TARGET_LEVEL_BOSS,
						nonplayer.KING : localeInfo.TARGET_LEVEL_KING,
					}
	EXCHANGE_LIMIT_RANGE = 3000
	HP_BOARD_MIN_WIDTH = 250
	HP_BOARD_MAX_WIDTH = 560
	wideNameReported = False

	def __init__(self):
		ui.ThinBoard.__init__(self)

		affectBar = ui.Window()
		affectBar.SetSize(0, 0)
		affectBar.Hide()
		self.affectBar = affectBar

		name = ui.TextLine()
		name.SetParent(self)
		name.SetDefaultFontName()
		name.SetOutline()
		name.Show()

		hpGauge = ui.Gauge()
		hpGauge.SetParent(self)
		hpGauge.MakeGauge(130, "red")
		hpGauge.Hide()

		# HP_NUMBER_ON_GAUGE / HP_REAL_VALUES: liczbowy zapis HP na pasku.
		# SetHP() ustawia tymczasowo "..." (bo dostaje tylko procent),
		# a realne "aktualny/max" doklada SetRealHP() po komendzie TargetHP.
		hpText = ui.TextLine()
		hpText.SetParent(hpGauge)
		hpText.SetOutline()
		hpText.SetHorizontalAlignCenter()
		hpText.SetVerticalAlignCenter()
		hpText.SetPosition(65, 1)
		hpText.Hide()

		# MT2009_PLUS_TARGET_BONUS_V1 (Autor: Vekirion): the bonuses against the monster (GetTargetBonusText), a line under
		# the name and the gauge; SetEnemyVID shows it and makes room.
		bonusText = ui.TextLine()
		bonusText.SetParent(self)
		bonusText.SetOutline()
		bonusText.SetPackedFontColor(0xFFFFD27F)
		bonusText.SetHorizontalAlignCenter()
		bonusText.SetWindowHorizontalAlignCenter()
		bonusText.SetPosition(0, 33)
		bonusText.Hide()

		if app.ENABLE_ELEMENTAL_TARGET:
			elementImage = ui.ImageBox()
			elementImage.SetParent(self)
			elementImage.Hide()
			self.elementImage = elementImage

		closeButton = ui.Button()
		closeButton.SetParent(self)
		closeButton.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		closeButton.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		closeButton.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		closeButton.SetPosition(30, 13)

		if localeInfo.IsARABIC():
			hpGauge.SetPosition(55, 17)
			hpGauge.SetWindowHorizontalAlignLeft()
			closeButton.SetWindowHorizontalAlignLeft()
		else:
			hpGauge.SetPosition(175, 17)
			hpGauge.SetWindowHorizontalAlignRight()
			closeButton.SetWindowHorizontalAlignRight()

		closeButton.SetEvent(ui.__mem_func__(self.OnPressedCloseButton))
		closeButton.Show()

		self.mobDropButton = CompactDropButton()
		self.mobDropButton.SetParent(self)
		self.mobDropButton.SetPosition(30, 13)
		self.mobDropButton.SetWindowHorizontalAlignRight()
		self.mobDropButton.SetEvent(ui.__mem_func__(self.OnPressedMobDrop))
		self.mobDropButton.Hide()
		self.eventMobDrop = None

		self.buttonDict = {}
		self.showingButtonList = []
		for buttonName in self.BUTTON_NAME_LIST:
			button = ui.Button()
			button.SetParent(self)

			button.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
			button.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
			button.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")

			button.SetWindowHorizontalAlignCenter()
			button.SetText(buttonName)
			button.Hide()
			self.buttonDict[buttonName] = button
			self.showingButtonList.append(button)

		self.buttonDict[localeInfo.TARGET_BUTTON_WHISPER].SetEvent(ui.__mem_func__(self.OnWhisper))
		self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE].SetEvent(ui.__mem_func__(self.OnExchange))
		self.buttonDict[localeInfo.TARGET_BUTTON_FIGHT].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_ACCEPT_FIGHT].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_AVENGE].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_FRIEND].SetEvent(ui.__mem_func__(self.OnAppendToMessenger))
		self.buttonDict[localeInfo.TARGET_BUTTON_FRIEND].SetEvent(ui.__mem_func__(self.OnAppendToMessenger))
		self.buttonDict[localeInfo.TARGET_BUTTON_INVITE_PARTY].SetEvent(ui.__mem_func__(self.OnPartyInvite))
		self.buttonDict[localeInfo.TARGET_BUTTON_LEAVE_PARTY].SetEvent(ui.__mem_func__(self.OnPartyExit))
		self.buttonDict[localeInfo.TARGET_BUTTON_EXCLUDE].SetEvent(ui.__mem_func__(self.OnPartyRemove))

		self.buttonDict[localeInfo.TARGET_BUTTON_INVITE_GUILD].SAFE_SetEvent(self.__OnGuildAddMember)
		self.buttonDict[localeInfo.TARGET_BUTTON_DISMOUNT].SAFE_SetEvent(self.__OnDismount)
		self.buttonDict[localeInfo.TARGET_BUTTON_EXIT_OBSERVER].SAFE_SetEvent(self.__OnExitObserver)
		self.buttonDict[localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT].SAFE_SetEvent(self.__OnViewEquipment)
		self.buttonDict[localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY].SAFE_SetEvent(self.__OnRequestParty)
		self.buttonDict[localeInfo.TARGET_BUTTON_BUILDING_DESTROY].SAFE_SetEvent(self.__OnDestroyBuilding)
		self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW].SAFE_SetEvent(self.__OnEmotionAllow)

		self.buttonDict["VOTE_BLOCK_CHAT"].SetEvent(ui.__mem_func__(self.__OnVoteBlockChat))

		self.buttonDict[localeInfo.TARGET_BUTTON_REPORT].SetEvent(ui.__mem_func__(self.__OnReportPlayer))

		# Panel GM (F9): "Sprawdz" otwiera zakladke "Sprawdz Gracza" z tym
		# celem, "EQ" pokazuje ekwipunek przez tekstowa odpowiedz serwera
		# (/gmpanel_view_equip) - oba tylko gdy constInfo.IsGM (RefreshButton).
		self.buttonDict["Sprawdz"].SAFE_SetEvent(self.__OnGMCheck)
		self.buttonDict["EQ"].SAFE_SetEvent(self.__OnEQClick)
		self.buttonDict[TARGET_BUTTON_REVIVE].SAFE_SetEvent(self.__OnZodiacRevive)

		self.affectDict = {}

		self.name = name
		self.hpGauge = hpGauge
		self.hpGaugeColor = "red" # MT2009_PLUS_TARGET_POISON_GAUGE_V1
		self.hpGaugeValue = (0, 100)
		self.poisonCheckTime = 0.0
		self.hpText = hpText
		self.bonusText = bonusText # MT2009_PLUS_TARGET_BONUS_V1
		self.closeButton = closeButton
		self.nameString = 0
		self.nameLength = 0
		self.vid = 0
		self.eventWhisper = None
		self.eventGMCheck = None
		self.eventEQ = None
		self.isShowButton = False

		self.__Initialize()
		self.ResetTargetBoard()

	def __del__(self):
		ui.ThinBoard.__del__(self)
		print "===================================================== DESTROYED TARGET BOARD"

	def __Initialize(self):
		self.nameString = ""
		self.nameLength = 0
		self.vid = 0
		self.isShowButton = False
		self.refreshTargetAffectList = []
		self.bonusRefreshTime = 0 # MT2009_PLUS_TARGET_BONUS_V1

	def Destroy(self):
		self.eventWhisper = None
		self.closeButton = None
		self.mobDropButton = None
		self.eventMobDrop = None
		self.showingButtonList = None
		self.buttonDict = None
		self.name = None
		self.hpGauge = None
		self.hpText = None
		self.bonusText = None # MT2009_PLUS_TARGET_BONUS_V1
		self.affectDict = None
		self.affectBar = None
		self.tooltip = None
		if app.ENABLE_ELEMENTAL_TARGET:
			self.elementImage = None
		self.__Initialize()

	def SetToolTip(self, tooltip):
		self.tooltip = proxy(tooltip)

	def OnPressedCloseButton(self):
		player.ClearTarget()
		self.Close()

	def SetMobDropEvent(self, callback):
		self.eventMobDrop = callback

	def OnPressedMobDrop(self):
		if self.eventMobDrop and self.vid:
			vnum = nonplayer.GetVnumByVID(self.vid)
			if vnum > 0:
				self.eventMobDrop(self.vid, vnum, chr.GetNameByVID(self.vid))

	def Close(self):
		self.__Initialize()
		self.Hide()
		self.affectBar.Hide()

	def Open(self, vid, name):
		if vid:
			if not constInfo.GET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD():
				if not player.IsSameEmpire(vid):
					self.Hide()
					return

			if vid != self.GetTargetVID():
				self.ResetTargetBoard()
				self.SetTargetVID(vid)
				self.SetTargetName(name)

			if player.IsMainCharacterIndex(vid):
				self.__ShowMainCharacterMenu()
			elif chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(self.vid):
				self.Hide()
			else:
				self.RefreshButton()
				self.Show()
		else:
			self.HideAllButton()
			self.__ShowButton(localeInfo.TARGET_BUTTON_WHISPER)
			self.__ShowButton("VOTE_BLOCK_CHAT")
			self.__ArrangeButtonPosition()
			self.SetTargetName(name)
			self.Show()

	def Refresh(self):
		if self.IsShow():
			if self.IsShowButton():
				self.RefreshButton()

	def RefreshByVID(self, vid):
		if vid == self.GetTargetVID():
			self.Refresh()

	def RefreshByName(self, name):
		if name == self.GetTargetName():
			self.Refresh()

	def __ShowMainCharacterMenu(self):
		canShow=0

		self.HideAllButton()

		if player.IsMountingHorse():
			self.__ShowButton(localeInfo.TARGET_BUTTON_DISMOUNT)
			canShow=1

		if player.IsObserverMode():
			self.__ShowButton(localeInfo.TARGET_BUTTON_EXIT_OBSERVER)
			canShow=1

		if canShow:
			self.__ArrangeButtonPosition()
			self.Show()
		else:
			self.Hide()

	def __ShowNameOnlyMenu(self):
		self.HideAllButton()

	def SetWhisperEvent(self, event):
		self.eventWhisper = event

	def SetGMCheckEvent(self, event):
		self.eventGMCheck = event

	def SetEQEvent(self, event):
		self.eventEQ = event

	def __OnGMCheck(self):
		if None != self.eventGMCheck:
			self.eventGMCheck(self.nameString)

	def __OnEQClick(self):
		if None != self.eventEQ:
			self.eventEQ(self.vid, self.nameString)

	def UpdatePosition(self):
		self.SetPosition(wndMgr.GetScreenWidth()/2 - self.GetWidth()/2, 10)

		x, y = self.GetGlobalPosition()
		self.affectBar.SetPosition(x, y + self.GetHeight() + 4)

	def ResetTargetBoard(self):

		for btn in self.buttonDict.values():
			btn.Hide()
		self.showingButtonList = []

		self.__Initialize()

		self.name.SetPosition(0, 13)
		self.name.SetHorizontalAlignCenter()
		self.name.SetWindowHorizontalAlignCenter()
		self.hpGauge.Hide()
		self.__SetHPGaugeColor("red") # MT2009_PLUS_TARGET_POISON_GAUGE_V1
		self.poisonCheckTime = 0.0
		if self.mobDropButton:
			self.mobDropButton.Hide()
			self.closeButton.Show()
		self.hpText.Hide()
		self.bonusText.Hide() # MT2009_PLUS_TARGET_BONUS_V1
		if app.ENABLE_ELEMENTAL_TARGET:
			self.elementImage.Hide()

		self.ClearTargetAffect()
		self.SetSize(250, 40)

	def SetTargetVID(self, vid):
		self.vid = vid

	# MT2009_PLUS_ELEMENTS_V1: the element mark left of the board, centred on the board's
	# height, which changes with the HP bar and the bonus line (the owner, 7 October).
	def SetSize(self, width, height):
		ui.ThinBoard.SetSize(self, width, height)
		if app.ENABLE_ELEMENTAL_TARGET and getattr(self, "elementImage", None):
			self.__CenterElementImage()

	def __CenterElementImage(self):
		image = self.elementImage
		image.SetPosition(-image.GetWidth(), max(0, (self.GetHeight() - image.GetHeight()) / 2))

	if app.ENABLE_ELEMENTAL_TARGET:
		def SetRaceElement(self, vid):
			mobVnum = nonplayer.GetVnumByVID(vid)
			imagePath = GetElementalFilename(mobVnum)
			# MT2009_PLUS_ELEMENTS_V1: a missing image must never break the target board
			# (the name and the bar were lost when LoadImage raised).
			self.elementImage.Hide()
			if imagePath:
				try:
					self.elementImage.LoadImage(imagePath)
					self.__CenterElementImage()
					self.elementImage.Show()
				except Exception:
					self.elementImage.Hide()

	def SetEnemyVID(self, vid):
		self.SetTargetVID(vid)
		if self.mobDropButton:
			if IsDropPreviewTarget(vid):
				self.closeButton.Hide()
				self.mobDropButton.Show()
			else:
				self.mobDropButton.Hide()
				self.closeButton.Show()
		if app.ENABLE_ELEMENTAL_TARGET:
			self.SetRaceElement(vid)

		self.__RefreshBonusText() # MT2009_PLUS_TARGET_BONUS_V1 (Autor: Vekirion)

		name = chr.GetNameByVID(vid)
		level = nonplayer.GetLevelByVID(vid)
		grade = nonplayer.GetGradeByVID(vid)

		nameFront = ""
		if -1 != level:
			nameFront += "Lv." + str(level) + " "
		if self.GRADE_NAME.has_key(grade):
			nameFront += "(" + self.GRADE_NAME[grade] + ") "

		self.SetTargetName(nameFront + name, nonplayer.GetVnumByVID(vid))

	# MT2009_PLUS_TARGET_BONUS_V1 (Autor: Vekirion): the line of bonuses against the target, with the player's values; again
	# from OnUpdate, so a changed item shows while the target stays.
	def __RefreshBonusText(self):
		self.bonusRefreshTime = app.GetTime() + 0.5
		text = GetTargetBonusText(self.vid)
		if not text:
			if self.bonusText.IsShow():
				self.bonusText.Hide()
				self.SetSize(self.__GetBoardWidth(), 40)
				self.UpdatePosition()
			return

		if self.bonusText.IsShow() and text == self.bonusText.GetText():
			return

		self.bonusText.SetText(text)
		self.bonusText.Show()
		self.SetSize(max(self.HP_BOARD_MIN_WIDTH, self.__GetBoardWidth()), 52)
		self.UpdatePosition()

	def GetTargetVID(self):
		return self.vid

	def GetTargetName(self):
		return self.nameString

	def SetTargetName(self, name, vnum=0):
		self.nameString = name
		self.nameLength = len(name)

		text = ""
		if constInfo.IS_GAMEMASTER and vnum > 10:
			text = " (vnum: %d)" % vnum
		self.nameString += text
		self.nameLength += len(text)

		self.name.SetText(self.nameString)

	def __ShowHPBoard(self):
		if not self.hpGauge.IsShow():
			self.name.SetPosition(23, 13)

			self.name.SetWindowHorizontalAlignLeft()
			self.name.SetHorizontalAlignLeft()
			self.hpGauge.Show()
			self.hpText.Show()
			# Sized with the gauge up, which __GetBoardWidth counts.
			self.SetSize(self.__GetBoardWidth(), self.GetHeight())
			self.UpdatePosition()

	# The board is as wide as the name draws, not seven pixels a character:
	# a name longer than what it shows stretched it past the screen and put
	# the HP bar under the minimap (St_August, 28 September).
	def __GetHPBoardWidth(self):
		stock = 200 + 7*self.nameLength
		try:
			drawn = 200 + self.name.GetTextSize()[0]
		except Exception:
			drawn = stock
		if stock > self.HP_BOARD_MAX_WIDTH and not TargetBoard.wideNameReported:
			TargetBoard.wideNameReported = True
			import dbg
			dbg.TraceError("TARGET_BOARD: wide name len=%d drawn=%d vid=%s name=%r" % (
				self.nameLength, drawn, self.vid, self.nameString))
		return max(self.HP_BOARD_MIN_WIDTH, min(drawn, self.HP_BOARD_MAX_WIDTH))

	# ... and never narrower than the rest of what it shows: the row of
	# buttons under the name, and the name and the gauge while the gauge is
	# up. A right-click lays a character's buttons out and the server's
	# TargetHP puts the gauge up a moment later; each sized the board alone,
	# and the gauge left nine buttons hanging past a board 272 pixels wide
	# (DUDU, 28 September).
	def __GetBoardWidth(self):
		width = max(150, len(self.showingButtonList) * 75)
		if self.hpGauge.IsShow():
			width = max(width, self.__GetHPBoardWidth())
		if self.bonusText.IsShow(): # MT2009_PLUS_TARGET_BONUS_V1
			width = max(width, self.__GetBonusTextWidth())
		return width

	def __GetBonusTextWidth(self):
		try:
			return min(40 + self.bonusText.GetTextSize()[0], self.HP_BOARD_MAX_WIDTH)
		except Exception:
			return self.HP_BOARD_MIN_WIDTH

	def SetHP(self, hpPercentage):
		self.__ShowHPBoard()
		self.hpText.SetText("%d%%" % max(0, min(100, int(hpPercentage)))) if IsDropPreviewTarget(self.vid) else self.hpText.SetText("...")

		self.__SetHPGauge(hpPercentage, 100)
		# HP_REAL_VALUES: tekst na pasku nie jest juz liczony z procentu -
		# ustawia go SetRealHP() po otrzymaniu prawdziwych liczb z serwera
		# (komenda "TargetHP" - patrz game.py).

	def SetRealHP(self, vid, hp, maxHp):
		# Ignoruj dane, ktore dojda po zmianie celu (spoznione w drodze)
		if vid != self.vid:
			return

		# HP_REAL_VALUES: niezalezne od SetHP(), bo u niektorych klientow
		# binarka C++ w ogole nie wywoluje SetHP() dla celu-gracza (twarda
		# blokada pokazywania paska HP wroga w PvP, zaszyta w kodzie klienta,
		# do ktorego nie mamy zrodel). Ten kanal idzie osobno przez komende
		# czatu, wiec sam musi pokazac pasek/tekst, a nie polegac na SetHP().
		self.__ShowHPBoard()

		if maxHp > 0:
			self.__SetHPGauge(hp, maxHp)
		if IsDropPreviewTarget(vid):
			percent = max(0, min(100, int(hp * 100 // maxHp))) if maxHp > 0 else 0
			self.hpText.SetText("%d%%" % percent)
		else:
			self.hpText.SetText("%d/%d" % (hp, maxHp))

	# MT2009_PLUS_TARGET_POISON_GAUGE_V1: the gauge green while the target is
	# poisoned (Kiciamol, 9 October). The value is kept, because a new picture
	# draws the gauge full.
	def __SetHPGauge(self, curValue, maxValue):
		self.hpGaugeValue = (curValue, maxValue)
		self.hpGauge.SetPercentage(curValue, maxValue)

	def __SetHPGaugeColor(self, color):
		if not self.hpGauge or color == self.hpGaugeColor:
			return
		if color != "red" and not HasPoisonGaugeImage():
			return
		self.hpGaugeColor = color
		try:
			self.hpGauge.imgGauge.LoadImage("d:/ymir work/ui/pattern/gauge_%s.tga" % color)
		except Exception:
			return
		(curValue, maxValue) = self.hpGaugeValue
		self.hpGauge.SetPercentage(curValue, maxValue)

	def __RefreshPoisonGauge(self):
		import clientclock
		now = clientclock.Now()
		if now < self.poisonCheckTime:
			return
		self.poisonCheckTime = now + 0.2
		poisoned = IsPoisonedTarget(self.vid, self.affectDict or {})
		self.__SetHPGaugeColor("green" if poisoned else "red")

	def StartTargetAffect(self):
		self.refreshTargetAffectList = []

	def AddTargetAffect(self, affect_type, duration):
		self.refreshTargetAffectList.append(affect_type)
		view_data = uiAffectBar.AFFECT_SHOW_DATA

		if self.affectDict.has_key(affect_type):
			self.affectDict[affect_type][2] = int(app.GetGlobalTimeStamp()) + duration
			self.UpdateTargetAffectDuration()

		if not self.affectDict.has_key(affect_type) and view_data.has_key(affect_type):
			aff = ui.ExpandedImageBox()
			aff.SetParent(self.affectBar)
			aff.LoadImage(view_data[affect_type]["icon"])
			aff.SetScale(0.8, 0.8)
			aff.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverInAffect, affect_type, int(app.GetGlobalTimeStamp()) + duration)
			aff.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOutAffect)
			aff.SetPosition(27 * (len(self.refreshTargetAffectList) - 1), 0)
			aff.Show()

			durationText = ui.TextLine()
			durationText.SetParent(aff)
			durationText.SetOutline(True)
			durationText.SetText(localeInfo.SecondToAffectTime(duration))
			durationText.SetWindowHorizontalAlignCenter()
			durationText.SetHorizontalAlignCenter()
			durationText.SetWindowVerticalAlignBottom()
			durationText.SetVerticalAlignBottom()
			durationText.SetPosition(0, -9)
			durationText.Show()
			self.affectDict[affect_type] = [aff, durationText, int(app.GetGlobalTimeStamp()) + duration]

	def UpdateTargetAffectDuration(self):
		isClear = False
		for key, data in self.affectDict.iteritems():
			duration_label = data[1]
			affect_endtime = data[2]
			duration = affect_endtime - int(app.GetGlobalTimeStamp())
			duration_label.SetText(localeInfo.SecondToAffectTime(duration))

			if duration < 0 and key in self.refreshTargetAffectList:
				self.refreshTargetAffectList.remove(key)
				isClear = True

		if isClear:
			self.ClearTargetAffect()

	def ClearTargetAffect(self):
		temp = []
		for affect_type in self.affectDict.iterkeys():
			if affect_type not in self.refreshTargetAffectList:
				self.affectDict[affect_type][0].Hide()
				if self.tooltip and self.tooltip.IsShow():
					self.tooltip.HideToolTip()
				temp.append(affect_type)

		for i in temp:
			self.affectDict.pop(i)

		self.__RefreshTargetAffectPosition()

	def __OnMouseOverInAffect(self, affect_type, duration):
		if self.tooltip:
			self.tooltip.ClearToolTip()
			self.tooltip.AppendTextLine(uiAffectBar.AFFECT_SHOW_DATA[affect_type]["description"])
			self.tooltip.AppendTextLine(localeInfo.SecondToSmartDHMS(duration -  int(app.GetGlobalTimeStamp())))
			self.tooltip.ShowToolTip()

	def __OnMouseOverOutAffect(self):
		if self.tooltip:
			self.tooltip.HideToolTip()

	def __RefreshTargetAffectPosition(self):
		idx = 0
		for affect_type in self.refreshTargetAffectList:
			self.affectDict[affect_type][0].SetPosition(27 * idx, -4)
			idx += 1

		self.affectBar.SetSize(idx * (27 + 2), 27)
		self.affectBar.Show()

	def ShowDefaultButton(self):

		self.isShowButton = True
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_WHISPER])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_FIGHT])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_REPORT])
		for button in self.showingButtonList:
			button.Show()

	def HideAllButton(self):
		self.isShowButton = False
		for button in self.showingButtonList:
			button.Hide()
		self.showingButtonList = []

	def __ShowButton(self, name):

		if not self.buttonDict.has_key(name):
			return

		self.buttonDict[name].Show()
		self.showingButtonList.append(self.buttonDict[name])

	def __HideButton(self, name):

		if not self.buttonDict.has_key(name):
			return

		button = self.buttonDict[name]
		button.Hide()

		for btnInList in self.showingButtonList:
			if btnInList == button:
				self.showingButtonList.remove(button)
				break

	def OnWhisper(self):
		if None != self.eventWhisper:
			self.eventWhisper(self.nameString)

	def OnExchange(self):
		net.SendExchangeStartPacket(self.vid)

	def OnPVP(self):
		net.SendChatPacket("/pvp %d" % (self.vid))

	def OnAppendToMessenger(self):
		net.SendMessengerAddByVIDPacket(self.vid)

	def OnPartyInvite(self):
		net.SendPartyInvitePacket(self.vid)

	def OnPartyExit(self):
		net.SendPartyExitPacket()

	def OnPartyRemove(self):
		net.SendPartyRemovePacketVID(self.vid)

	def __OnGuildAddMember(self):
		net.SendGuildAddMemberPacket(self.vid)

	def __OnDismount(self):
		net.SendChatPacket("/unmount")

	def __OnExitObserver(self):
		net.SendChatPacket("/observer_exit")

	def __OnViewEquipment(self):
		net.SendChatPacket("/view_equip " + str(self.vid))

	def __OnRequestParty(self):
		net.SendChatPacket("/party_request " + str(self.vid))

	def __OnDestroyBuilding(self):
		net.SendChatPacket("/build d %d" % (self.vid))

	def __OnEmotionAllow(self):
		net.SendChatPacket("/emotion_allow %d" % (self.vid))

	def __OnZodiacRevive(self):
		net.SendChatPacket("/revivedialog %d" % (self.vid))

	def __IsInZodiacTemple(self):
		if not getattr(app, "ENABLE_12ZI", 0):
			return False
		try:
			import background
			return str(background.GetCurrentMapName()) == "metin2_12zi_stage"
		except Exception:
			return False

	def __OnVoteBlockChat(self):
		cmd = "/vote_block_chat %s" % (self.nameString)
		net.SendChatPacket(cmd)

	def __OnReportPlayer(self):
		eventManager.EventManager().send_event(uiReport.EVENT_REPORT_PLAYER, self.nameString, self.vid)

	def OnPressEscapeKey(self):
		self.OnPressedCloseButton()
		return True

	def IsShowButton(self):
		return self.isShowButton

	def RefreshButton(self):

		self.HideAllButton()

		if chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(self.vid):
			#self.__ShowButton(localeInfo.TARGET_BUTTON_BUILDING_DESTROY)
			#self.__ArrangeButtonPosition()
			return

		if player.IsPVPInstance(self.vid) or player.IsObserverMode():
			# PVP_INFO_SIZE_BUG_FIX
			self.SetSize(self.__GetHPBoardWidth(), 40)
			self.UpdatePosition()
			# END_OF_PVP_INFO_SIZE_BUG_FIX
			return

		self.ShowDefaultButton()

		if self.nameString[0] == '[':
			self.__HideButton(localeInfo.TARGET_BUTTON_REPORT)

		if guild.MainPlayerHasAuthority(guild.AUTH_ADD_MEMBER):
			if not guild.IsMemberByName(self.nameString):
				if 0 == chr.GetGuildID(self.vid):
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_GUILD)

		if not messenger.IsFriendByName(self.nameString):
			self.__ShowButton(localeInfo.TARGET_BUTTON_FRIEND)

		if player.IsPartyMember(self.vid):

			self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

			if player.IsPartyLeader(self.vid):
				self.__ShowButton(localeInfo.TARGET_BUTTON_LEAVE_PARTY)
			elif player.IsPartyLeader(player.GetMainCharacterIndex()):
				self.__ShowButton(localeInfo.TARGET_BUTTON_EXCLUDE)

		else:
			if player.IsPartyMember(player.GetMainCharacterIndex()):
				if player.IsPartyLeader(player.GetMainCharacterIndex()):
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)
			else:
				if chr.IsPartyMember(self.vid):
					self.__ShowButton(localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY)
				else:
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)

			if player.IsRevengeInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)
				self.__ShowButton(localeInfo.TARGET_BUTTON_AVENGE)
			elif player.IsChallengeInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)
				self.__ShowButton(localeInfo.TARGET_BUTTON_ACCEPT_FIGHT)
			elif player.IsCantFightInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

			if not player.IsSameEmpire(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)
				self.__HideButton(localeInfo.TARGET_BUTTON_FRIEND)
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

		distance = player.GetCharacterDistance(self.vid)
		if distance > self.EXCHANGE_LIMIT_RANGE:
			self.__HideButton(localeInfo.TARGET_BUTTON_EXCHANGE)
			self.__ArrangeButtonPosition()

		# Panel GM: "Sprawdz" i "EQ" tylko dla GM-a (flaga SetGMFlag z serwera,
		# game.py __SetGMFlag). Serwer i tak sprawdza gm_level przy kazdej
		# komendzie /gmpanel_*, wiec to tylko ukrywa przyciski przed graczem.
		if constInfo.IsGM:
			self.__ShowButton("Sprawdz")
			self.__ShowButton("EQ")

		# MT2009_PLUS_SIDEKICK_ZODIAC_V1: the temple's revive window for this
		# character (the server answers only for one lying on a temple floor).
		if self.__IsInZodiacTemple():
			self.__ShowButton(TARGET_BUTTON_REVIVE)

		self.__ArrangeButtonPosition()

	def __ArrangeButtonPosition(self):
		showingButtonCount = len(self.showingButtonList)

		pos = -(showingButtonCount / 2) * 68
		if 0 == showingButtonCount % 2:
			pos += 34

		for button in self.showingButtonList:
			button.SetPosition(pos, 33)
			pos += 68

		# As wide as the row, and as the gauge's half while the gauge is up.
		self.SetSize(self.__GetBoardWidth(), 65)
		self.UpdatePosition()

	# MT2009_PLUS_ZODIAC_V1 (Autor: Digi Rasta, nowy-system 0.35.0): okno wskrzeszenia
	if getattr(app, "ENABLE_12ZI", 0):
		def OpenReviveDialog(self, vid, itemcount):
			import uiCommon
			self.questionDialog = uiCommon.QuestionDialog2()
			if player.IsMainCharacterIndex(vid):
				self.questionDialog.SetText1(localeInfo.REVIVE_SELF_QUESTION1)
				self.questionDialog.SetText2(localeInfo.REVIVE_SELF_QUESTION2 % (itemcount))
			else:
				self.questionDialog.SetText1(localeInfo.REVIVE_QUESTION1 % chr.GetNameByVID(vid))
				self.questionDialog.SetText2(localeInfo.REVIVE_QUESTION2 % itemcount)

			self.questionDialog.SetAcceptEvent(lambda arg=vid: self.OnRivive(arg))
			self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnQuestionDialogClose))
			self.questionDialog.Open()

		def OnRivive(self, virId):
			net.SendChatPacket("/revive %d" % (virId))
			self.OnQuestionDialogClose()

		def OnQuestionDialogClose(self):
			if getattr(self, "questionDialog", None):
				self.questionDialog.Close()
				self.questionDialog = None
			return True
	def OnUpdate(self):
		# MT2009_PLUS_TARGET_BONUS_V1 (Autor: Vekirion): refreshed every 0.5 s.
		if self.bonusText and self.bonusText.IsShow() and app.GetTime() >= self.bonusRefreshTime:
			self.__RefreshBonusText()

		# MT2009_PLUS_TARGET_POISON_GAUGE_V1: five times a second.
		if self.hpGauge and self.hpGauge.IsShow():
			self.__RefreshPoisonGauge()

		if self.isShowButton:

			exchangeButton = self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE]
			distance = player.GetCharacterDistance(self.vid)

			if distance < 0:
				return

			if exchangeButton.IsShow():
				if distance > self.EXCHANGE_LIMIT_RANGE:
					self.RefreshButton()

			else:
				if distance < self.EXCHANGE_LIMIT_RANGE:
					self.RefreshButton()
