import chr
import grp
import app
import net
import snd
import wndMgr
import event
import systemSetting
import localeInfo

import ui
import networkModule
import math
import snd
import musicInfo
import playerSettingModule
import uiScriptLocale
import uiToolTip

LOCALE_PATH = "uiscript/"+uiScriptLocale.CODEPAGE+"_"

MAN			= 0
WOMAN		= 1
GENDER_LIST = (MAN, WOMAN)
SHAPE0		= 0
SHAPE1		= 1
PAGE_COUNT	= 2

USE_WOLFMAN_CHARACTER = app.ENABLE_WOLFMAN_CHARACTER and not app.DISABLE_WOLFMAN_ON_CREATE

if USE_WOLFMAN_CHARACTER:
	SLOT_COUNT	= (5, 4)
else:
	SLOT_COUNT	= (4, 4)
BASE_CHR_ID	= 3

def GetRealID(page):
	realIdx = 0
	for i in xrange(len(SLOT_COUNT)):
		if i>=page:
			break
		realIdx+=SLOT_COUNT[i]
	return realIdx

def GetRealIDnSlot(page, slot):
	realIdx = 0
	for i in xrange(len(SLOT_COUNT)):
		if i>=page:
			break
		realIdx+=SLOT_COUNT[i]
	# import dbg
	# dbg.TraceError("page(%d) slot(%d)=real(%d)+=%d"%(page, slot, realIdx, realIdx+slot))
	return realIdx + slot

class CreateCharacterWindow(ui.Window):

	if USE_WOLFMAN_CHARACTER:
		SLOT_ROTATION = [[135.0, 207.0, 279.0, 351.0, 63.0], [135.0, 225.0, 315.0, 45.0]]
	else:
		SLOT_ROTATION = [[135.0, 225.0, 315.0, 45.0], [135.0, 225.0, 315.0, 45.0]]


	CREATE_STAT_POINT = 0

	STAT_CON = 0
	STAT_INT = 1
	STAT_STR = 2
	STAT_DEX = 3

	STAT_DESCRIPTION =	{
							STAT_CON : localeInfo.STAT_TOOLTIP_CON,
							STAT_INT : localeInfo.STAT_TOOLTIP_INT,
							STAT_STR : localeInfo.STAT_TOOLTIP_STR,
							STAT_DEX : localeInfo.STAT_TOOLTIP_DEX,
						}

	START_STAT =	(  ## CON INT STR DEX
						[ 4, 3, 6, 3, ], ## Warrior
						[ 3, 3, 4, 6, ], ## Assassin
						[ 3, 5, 5, 3, ], ## Sura
						[ 4, 6, 3, 3, ], ## Shaman
						[ 4, 3, 6, 3, ], ## Warrior
						[ 3, 3, 4, 6, ], ## Assassin
						[ 3, 5, 5, 3, ], ## Sura
						[ 4, 6, 3, 3, ], ## Shaman
					)
	if USE_WOLFMAN_CHARACTER:
		tmpStartStat = list(START_STAT)
		tmpStartStat.insert(GetRealIDnSlot(MAN, 5-1), [ 6, 2, 2, 6, ])
		START_STAT = tuple(tmpStartStat)

	DESCRIPTION_FILE_NAME =	(
		uiScriptLocale.JOBDESC_WARRIOR_PATH,
		uiScriptLocale.JOBDESC_ASSASSIN_PATH,
		uiScriptLocale.JOBDESC_SURA_PATH,
		uiScriptLocale.JOBDESC_SHAMAN_PATH,
	)
	if USE_WOLFMAN_CHARACTER:
		DESCRIPTION_FILE_NAME += (uiScriptLocale.JOBDESC_WOLFMAN_PATH,)

	CLASS_SPEC_INFO = {
		0: {  # JOB_WARRIOR
			"dir": "warrior",
			0: {  # body
				"icon": "geomgyeong_03.sub",
				"name": localeInfo.JOB_WARRIOR1,
				"skill": {
					0: ["geomgyeong_03.sub", localeInfo.SKILL_SWORD_AURA, localeInfo.SKILL_SWORD_AURA_DESC],
					1: ["jeongwi_03.sub", localeInfo.SKILL_BERSERK, localeInfo.SKILL_BERSERK_DESC],
					2: ["palbang_03.sub", localeInfo.SKILL_WHIRLWIND, localeInfo.SKILL_WHIRLWIND_DESC],
					3: ["samyeon_03.sub", localeInfo.SKILL_THREEWAY_CUT, localeInfo.SKILL_THREEWAY_CUT_DESC],
					4: ["tanhwan_03.sub", localeInfo.SKILL_CHARGE, localeInfo.SKILL_CHARGE_DESC],
				},
			},
			1: {  # mental
				"icon": "cheongeun_03.sub",
				"name": localeInfo.JOB_WARRIOR2,
				"skill": {
					0: ["cheongeun_03.sub", localeInfo.SKILL_STRONG_BODY, localeInfo.SKILL_STRONG_BODY_DESC],
					1: ["gigongcham_03.sub", localeInfo.SKILL_SPIRIT_STRIKE, localeInfo.SKILL_SPIRIT_STRIKE_DESC],
					2: ["gyeoksan_03.sub", localeInfo.SKILL_BASH, localeInfo.SKILL_BASH_DESC],
					3: ["daejin_03.sub", localeInfo.SKILL_STUMP, localeInfo.SKILL_STUMP_DESC],
					4: ["geompung_03.sub", localeInfo.SKILL_SWORD_STRIKE, localeInfo.SKILL_SWORD_STRIKE_DESC],
				},
			},
		},

		1: {  # JOB_ASSASSIN
			"dir": "assassin",
			0: {  # dagger
				"icon": "amseup_03.sub",
				"name": localeInfo.JOB_ASSASSIN1,
				"skill": {
					0: ["amseup_03.sub", localeInfo.SKILL_AMBUSH, localeInfo.SKILL_AMBUSH_DESC],
					1: ["eunhyeong_03.sub", localeInfo.SKILL_STEALTH, localeInfo.SKILL_STEALTH_DESC],
					2: ["charyun_03.sub", localeInfo.SKILL_ROLLING_DAGGER, localeInfo.SKILL_ROLLING_DAGGER_DESC],
					3: ["gungsin_03.sub", localeInfo.SKILL_FAST_ATTACK, localeInfo.SKILL_FAST_ATTACK_DESC],
					4: ["sangong_03.sub", localeInfo.SKILL_POISON_CLOUD, localeInfo.SKILL_POISON_CLOUD_DESC],
				},
				"other": {
					0: ["d:/ymir work/ui/flamewind/affect/bloodthirst.sub", localeInfo.SKILL_ASSASSIN_BLOODTHIRST,
						localeInfo.SKILL_ASSASSIN_BLOODTHIRST_DESC],
				},
			},
			1: {  # archer
				"icon": "gwangyeok_03.sub",
				"name": localeInfo.JOB_ASSASSIN2,
				"description": localeInfo.ASSASSIN_ARCHER_DESCRIPTION,
				"skill": {
					0: ["yeonsa_03.sub", localeInfo.SKILL_REPETITIVE_SHOT, localeInfo.SKILL_REPETITIVE_SHOT_DESC],
					1: ["gwangyeok_03.sub", localeInfo.SKILL_ARROW_SHOWER, localeInfo.SKILL_ARROW_SHOWER_DESC],
					2: ["hwajo_03.sub", localeInfo.SKILL_FIRE_ARROW, localeInfo.SKILL_FIRE_ARROW_DESC],
					3: ["gigung_03.sub", localeInfo.SKILL_POISON_ARROW, localeInfo.SKILL_POISON_ARROW_DESC],
					4: ["gyeonggong_03.sub", localeInfo.SKILL_FEATHER_WALK, localeInfo.SKILL_FEATHER_WALK_DESC],
				},
			},
		},

		2: {  # JOB_SURA
			"dir": "sura",
			0: {  # wp
				"icon": "gwigeom_03.sub",
				"name": localeInfo.JOB_SURA1,
				"skill": {
					0: ["gwigeom_03.sub", localeInfo.SKILL_ENCHANTED_BLADE, localeInfo.SKILL_ENCHANTED_BLADE_DESC],
					1: ["gongpo_03.sub", localeInfo.SKILL_TERROR, localeInfo.SKILL_TERROR_DESC],
					2: ["jumagap_03.sub", localeInfo.SKILL_ENCHANTED_ARMOR, localeInfo.SKILL_ENCHANTED_ARMOR_DESC],
					3: ["yonggwon_03.sub", localeInfo.SKILL_DRAGON_SWIRL, localeInfo.SKILL_DRAGON_SWIRL_DESC],
					4: ["pabeop_03.sub", localeInfo.SKILL_DISPEL, localeInfo.SKILL_DISPEL_DESC],
					5: ["swaeryeong_03.sub", localeInfo.SKILL_FINGER_STRIKE, localeInfo.SKILL_FINGER_STRIKE_DESC],
				},
			},
			1: {  # bm
				"icon": "hwayeom_03.sub",
				"name": localeInfo.JOB_SURA2,
				"skill": {
					0: ["maryeong_03.sub", localeInfo.SKILL_DARK_STRIKE, localeInfo.SKILL_DARK_STRIKE_DESC],
					1: ["hwayeom_03.sub", localeInfo.SKILL_FLAME_STRIKE, localeInfo.SKILL_FLAME_STRIKE_DESC],
					2: ["muyeong_03.sub", localeInfo.SKILL_FLAME_SPIRIT, localeInfo.SKILL_FLAME_SPIRIT_DESC],
					3: ["heuksin_03.sub", localeInfo.SKILL_MANASHIELD, localeInfo.SKILL_MANASHIELD_DESC],
					4: ["tusok_03.sub", localeInfo.SKILL_SPIRIT_ORB, localeInfo.SKILL_SPIRIT_ORB_DESC],
					5: ["geomhwan_03.sub", localeInfo.SKILL_DARK_ORB, localeInfo.SKILL_DARK_ORB_DESC],
				},
			},
		},

		3: {  # JOB_SHAMAN
			"dir": "shaman",
			0: {  # dragon
				"icon": "yongpa_03.sub",
				"name": localeInfo.JOB_SHAMAN1,
				"description": localeInfo.SHAMAN_DESCRIPTION,
				"skill": {
					0: ["bipabu_03.sub", localeInfo.SKILL_FLYING_TALISMAN, localeInfo.SKILL_FLYING_TALISMAN_DESC],
					1: ["yongpa_03.sub", localeInfo.SKILL_SHOOTING_DRAGON, localeInfo.SKILL_SHOOTING_DRAGON_DESC],
					2: ["paeryong_03.sub", localeInfo.SKILL_DRAGON_ROAR, localeInfo.SKILL_DRAGON_ROAR_DESC],
					3: ["hosin_03.sub", localeInfo.SKILL_BLESSING, localeInfo.SKILL_BLESSING_DESC],
					4: ["boho_03.sub", localeInfo.SKILL_REFLECT, localeInfo.SKILL_REFLECT_DESC],
					5: ["gicheon_03.sub", localeInfo.SKILL_DRAGON_HELP, localeInfo.SKILL_DRAGON_HELP_DESC],
				},
				"other": {
					0: ["d:/ymir work/ui/flamewind/affect/fire_rage.sub", localeInfo.SKILL_SHAMAN_FIRE_RAGE,
						localeInfo.SKILL_SHAMAN_FIRE_RAGE_DESC],
				},
			},
			1: {  # lightning
				"icon": "byeorak_03.sub",
				"name": localeInfo.JOB_SHAMAN2,
				"description": localeInfo.SHAMAN_DESCRIPTION,
				"skill": {
					0: ["noejeon_03.sub", localeInfo.SKILL_LIGHTNING_THROW, localeInfo.SKILL_LIGHTNING_THROW_DESC],
					1: ["byeorak_03.sub", localeInfo.SKILL_SUMMON_LIGHTNING, localeInfo.SKILL_SUMMON_LIGHTNING_DESC],
					2: ["pokroe_03.sub", localeInfo.SKILL_LIGHTNING_CLAW, localeInfo.SKILL_LIGHTNING_CLAW_DESC],
					3: ["jeongeop_03.sub", localeInfo.SKILL_CURE, localeInfo.SKILL_CURE_DESC],
					4: ["kwaesok_03.sub", localeInfo.SKILL_SWIFTNESS, localeInfo.SKILL_SWIFTNESS_DESC],
					5: ["jeungryeok_03.sub", localeInfo.SKILL_ATTACK_UP, localeInfo.SKILL_ATTACK_UP_DESC],
				},
				"other": {
					0: ["d:/ymir work/ui/flamewind/affect/heaven_protection.sub",
						localeInfo.SKILL_SHAMAN_HEAVEN_PROTECTION,
						localeInfo.SKILL_SHAMAN_HEAVEN_PROTECTION_DESC],
				},
			},
		},
	}


	class DescriptionBox(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.descIndex = 0
		def __del__(self):
			ui.Window.__del__(self)
		def SetIndex(self, index):
			self.descIndex = index
		def OnRender(self):
			event.RenderEventSet(self.descIndex)

	class CharacterRenderer(ui.Window):
		def OnRender(self):
			grp.ClearDepthBuffer()
			grp.SetGameRenderState()
			grp.PushState()
			grp.SetOmniLight()

			screenWidth = wndMgr.GetScreenWidth()
			screenHeight = wndMgr.GetScreenHeight()
			newScreenWidth = float(screenWidth - 270)
			newScreenHeight = float(screenHeight)

			grp.SetViewport(270.0/screenWidth, 0.0, newScreenWidth/screenWidth, newScreenHeight/screenHeight)

			app.SetCenterPosition(0.0, 0.0, 0.0)
			app.SetCamera(1550.0, 15.0, 180.0, 95.0)
			grp.SetPerspective(10.0, newScreenWidth/newScreenHeight, 1000.0, 3000.0)

			(x, y) = app.GetCursorPosition()
			grp.SetCursorPosition(x, y)

			chr.Deform()
			chr.Render()

			grp.RestoreViewport()
			grp.PopState()
			grp.SetInterfaceRenderState()

	def __init__(self, stream):
		print "NEW CREATE WINDOW ----------------------------------------------------------------------------"
		ui.Window.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_CREATE, self)

		self.stream=stream

	def __del__(self):
		print "---------------------------------------------------------------------------- DELETE CREATE WINDOW"

		net.SetPhaseWindow(net.PHASE_WINDOW_CREATE, 0)
		ui.Window.__del__(self)

	def Open(self):
		print "OPEN CREATE WINDOW ----------------------------------------------------------------------------"

		playerSettingModule.LoadGameData("INIT")

		self.reservingRaceIndex = -1
		self.reservingShapeIndex = -1
		self.reservingStartTime = 0
		self.stat = [0, 0, 0, 0]

		self.gender = 0
		self.slot = -1
		#
		self.instanceIDs = []
		if USE_WOLFMAN_CHARACTER:
			self.shapeList = [
				[0, 0, 0, 0, 0],
				[0, 0, 0, 0]]
		else:
			self.shapeList = [
				[0, 0, 0, 0],
				[0, 0, 0, 0]]

		self.descIndex = 0

		try:
			dlgBoard = ui.ScriptWindow()
			pythonScriptLoader = ui.PythonScriptLoader()
			pythonScriptLoader.LoadScriptFile(dlgBoard, "UIScript/createcharacterwindow.py")

		except:
			import exception
			exception.Abort("CreateCharacterWindow.Open.LoadObject")

		try:
			getChild = dlgBoard.GetChild

			self.NameList = {}
			self.NameList[MAN] = []
			self.NameList[MAN].append(getChild("name_warrior"))
			self.NameList[MAN].append(getChild("name_assassin"))
			self.NameList[MAN].append(getChild("name_sura"))
			self.NameList[MAN].append(getChild("name_shaman"))
			if USE_WOLFMAN_CHARACTER:
				self.NameList[MAN].append(getChild("name_wolfman"))
			self.NameList[WOMAN] = []
			self.NameList[WOMAN].append(getChild("name_warrior"))
			self.NameList[WOMAN].append(getChild("name_assassin"))
			self.NameList[WOMAN].append(getChild("name_sura"))
			self.NameList[WOMAN].append(getChild("name_shaman"))

			self.GaugeList = []
			self.GaugeList.append(getChild("hth_gauge"))
			self.GaugeList.append(getChild("int_gauge"))
			self.GaugeList.append(getChild("str_gauge"))
			self.GaugeList.append(getChild("dex_gauge"))

			self.btnCreate = getChild("create_button")
			self.btnCancel = getChild("cancel_button")
			self.btnPrev = getChild("prev_button")
			self.btnNext = getChild("next_button")
			self.btnLeft = getChild("left_button")
			self.btnRight = getChild("right_button")
			self.textBoard = getChild("text_board")

			self.genderButtonList = []
			self.genderButtonList.append(getChild("gender_button_01"))
			self.genderButtonList.append(getChild("gender_button_02"))

			self.shapeButtonList = []
			self.shapeButtonList.append(getChild("shape_button_01"))
			self.shapeButtonList.append(getChild("shape_button_02"))

			self.editCharacterName = getChild("character_name_value")

			self.statValue = []
			self.statValue.append(getChild("hth_value"))
			self.statValue.append(getChild("int_value"))
			self.statValue.append(getChild("str_value"))
			self.statValue.append(getChild("dex_value"))

			self.specIcons = []
			for i in range(2):
				self.specIcons.append(getChild("SpecIcon%d" % (i + 1)))
				self.specIcons[i].SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnSpecIconMouseOverIn, i)
				self.specIcons[i].SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnSpecIconMouseOverOut)

			getChild("hth_button").ShowToolTip = lambda arg=self.STAT_CON: self.OverInStatButton(arg)
			getChild("hth_button").HideToolTip = lambda arg=self.STAT_CON: self.OverOutStatButton()
			getChild("int_button").ShowToolTip = lambda arg=self.STAT_INT: self.OverInStatButton(arg)
			getChild("int_button").HideToolTip = lambda arg=self.STAT_INT: self.OverOutStatButton()
			getChild("str_button").ShowToolTip = lambda arg=self.STAT_STR: self.OverInStatButton(arg)
			getChild("str_button").HideToolTip = lambda arg=self.STAT_STR: self.OverOutStatButton()
			getChild("dex_button").ShowToolTip = lambda arg=self.STAT_DEX: self.OverInStatButton(arg)
			getChild("dex_button").HideToolTip = lambda arg=self.STAT_DEX: self.OverOutStatButton()

			getChild("hth_button").Hide()
			getChild("int_button").Hide()
			getChild("str_button").Hide()
			getChild("dex_button").Hide()

			self.backGround = getChild("BackGround")

		except:
			import exception
			exception.Abort("CreateCharacterWindow.Open.BindObject")

		self.btnCreate.SetEvent(ui.__mem_func__(self.CreateCharacter))
		self.btnCancel.SetEvent(ui.__mem_func__(self.CancelCreate))
		self.btnPrev.SetEvent(ui.__mem_func__(self.PrevDescriptionPage))
		self.btnNext.SetEvent(ui.__mem_func__(self.NextDescriptionPage))
		self.btnLeft.SetEvent(ui.__mem_func__(self.__DecreaseSlotIndex))
		self.btnRight.SetEvent(ui.__mem_func__(self.__IncreaseSlotIndex))

		self.genderButtonList[0].SetEvent(ui.__mem_func__(self.__SelectGender), MAN)
		self.genderButtonList[1].SetEvent(ui.__mem_func__(self.__SelectGender), WOMAN)

		self.shapeButtonList[0].SetEvent(ui.__mem_func__(self.__SelectShape), SHAPE0)
		self.shapeButtonList[1].SetEvent(ui.__mem_func__(self.__SelectShape), SHAPE1)
		self.editCharacterName.SetReturnEvent(ui.__mem_func__(self.CreateCharacter))
		self.editCharacterName.SetEscapeEvent(ui.__mem_func__(self.CancelCreate))
		self.dlgBoard = dlgBoard

		self.curRotation	= [] + self.SLOT_ROTATION[self.gender]
		self.destRotation	= [] + self.SLOT_ROTATION[self.gender]
		self.curNameAlpha	= [0.0, 0.0, 0.0, 0.0, 0.0]
		self.destNameAlpha	= [0.0, 0.0, 0.0, 0.0, 0.0]
		self.curGauge		= [0.0, 0.0, 0.0, 0.0]
		self.destGauge		= [0.0, 0.0, 0.0, 0.0]

		self.descriptionBox = self.DescriptionBox()
		self.descriptionBox.Show()

		self.chrRenderer = self.CharacterRenderer()
		self.chrRenderer.SetParent(self.backGround)
		self.chrRenderer.Show()

		self.toolTip = uiToolTip.ToolTip()
		self.toolTip.ClearToolTip()

		self.editCharacterName.SetText("")

		self.EnableWindow()
		self.__SelectSlot(0)

		app.SetCamera(500.0, 10.0, 180.0, 95.0)

		self.__MakeCharacter(MAN, 0, playerSettingModule.RACE_WARRIOR_M)
		self.__MakeCharacter(MAN, 1, playerSettingModule.RACE_ASSASSIN_M)
		self.__MakeCharacter(MAN, 2, playerSettingModule.RACE_SURA_M)
		self.__MakeCharacter(MAN, 3, playerSettingModule.RACE_SHAMAN_M)
		if USE_WOLFMAN_CHARACTER:
			self.__MakeCharacter(MAN, 4, playerSettingModule.RACE_WOLFMAN_M)

		self.__MakeCharacter(WOMAN, 0, playerSettingModule.RACE_WARRIOR_W)
		self.__MakeCharacter(WOMAN, 1, playerSettingModule.RACE_ASSASSIN_W)
		self.__MakeCharacter(WOMAN, 2, playerSettingModule.RACE_SURA_W)
		self.__MakeCharacter(WOMAN, 3, playerSettingModule.RACE_SHAMAN_W)

		self.__SelectGender(app.GetRandom(MAN, WOMAN))
		self.__SelectShape(0)
		self.__SelectSlot(app.GetRandom(0, SLOT_COUNT[self.gender]-1))

		self.dlgBoard.Show()
		self.Show()

		if musicInfo.createMusic != "":
			snd.SetMusicVolume(systemSetting.GetMusicVolume())
			snd.FadeInMusic("BGM/"+musicInfo.createMusic)

		app.ShowCursor()

	def Close(self):
		print "---------------------------------------------------------------------------- CLOSE CREATE WINDOW"

		self.editCharacterName.Enable()
		self.dlgBoard.ClearDictionary()
		self.stream=0
		self.shapeButtonList = []
		self.genderButtonList = []
		self.btnCreate = 0
		self.btnCancel = 0
		self.btnPrev = 0
		self.btnNext = 0
		self.btnLeft = 0
		self.btnRight = 0
		self.textBoard = 0
		self.editCharacterName = 0
		self.backGround = None

		if musicInfo.createMusic != "":
			snd.FadeOutMusic("BGM/"+musicInfo.createMusic)

		for id in self.instanceIDs:
			chr.DeleteInstance(id)

		self.dlgBoard.Hide()
		self.Hide()

		app.HideCursor()
		event.Destroy()

	def EnableWindow(self):
		self.reservingRaceIndex = -1
		self.reservingShapeIndex = -1
		self.btnCreate.Enable()
		self.btnCancel.Enable()
		self.btnPrev.Enable()
		self.btnNext.Enable()
		self.btnLeft.Enable()
		self.btnRight.Enable()

		self.editCharacterName.SetFocus()
		self.editCharacterName.Enable()

		for page in xrange(PAGE_COUNT):
			for slot in xrange(SLOT_COUNT[page]):
				chr_id = self.__GetSlotChrID(page, slot)
				chr.SelectInstance(chr_id)
				chr.BlendLoopMotion(chr.MOTION_INTRO_WAIT, 0.1)

	def DisableWindow(self):
		self.btnCreate.Disable()
		self.btnCancel.Disable()
		self.btnPrev.Disable()
		self.btnNext.Disable()
		self.btnLeft.Disable()
		self.btnRight.Disable()
		self.editCharacterName.Disable()

		self.btnCreate.SetUp()

	def __OnSpecIconMouseOverIn(self, specIndex):
		self.toolTip.ClearToolTip()

		class_data = self.CLASS_SPEC_INFO[self.slot]
		spec_data = class_data[specIndex]

		self.toolTip.AppendTextLine(spec_data["name"], isBold=True, isLarge=True)
		if spec_data.has_key("description"):
			self.toolTip.AppendDescription(spec_data["description"], space=0)
		self.toolTip.AppendHorizontalLine()
		skill_len = len(spec_data["skill"])

		self.toolTip.AppendTextLine(localeInfo.INTRO_CREATE_ACTIVE_SKILLS_TITLE, isBold=True, isLarge=True)

		base_skill_icon_dir = "d:/ymir work/ui/skill/%s/" % class_data["dir"]
		column_block = ui.ColumnBlock(3)
		for i in range(skill_len):
			tooltip = uiToolTip.ToolTip(isNoBackground=True)
			tooltip.followFlag = False
			skill_data = spec_data["skill"][i]
			tooltip.AppendImage(base_skill_icon_dir + skill_data[0])
			tooltip.AppendSpace(1)
			tooltip.AppendTextLine(skill_data[1], isBold=True)
			tooltip.AppendDescription(skill_data[2], space=0)
			tooltip.AppendSpace(3)
			tooltip.ShowToolTip()
			column_block.AddItem(i / 2, tooltip)

		column_block.Show()
		self.toolTip.AppendColumnBlock(column_block)

		if spec_data.has_key("other"):
			self.toolTip.AppendHorizontalLine()
			self.toolTip.AppendTextLine(localeInfo.INTRO_CREATE_OTHER, isBold=True, isLarge=True)
			self.toolTip.AppendSpace(5)
			other_len = len(spec_data["other"])
			for i in range(other_len):
				other_data = spec_data["other"][i]
				self.toolTip.AppendImage(other_data[0])
				self.toolTip.AppendSpace(1)
				self.toolTip.AppendTextLine(other_data[1], isBold=True)
				self.toolTip.AppendDescription(other_data[2], space=0)
				tooltip.AppendSpace(3)

		self.toolTip.ShowToolTip()

	def __OnSpecIconMouseOverOut(self):
		self.toolTip.HideToolTip()

	def __RefreshSpecIcons(self):
		for i in range(2):
			icon = self.specIcons[i]
			class_data = self.CLASS_SPEC_INFO[self.slot]
			spec_data = class_data[i]
			icon.LoadImage("d:/ymir work/ui/skill/%s/%s" % (class_data["dir"], spec_data["icon"]))

	## Manage Character
	def __GetSlotChrID(self, page, slot):
		return BASE_CHR_ID + GetRealIDnSlot(page, slot)

	def __MakeCharacter(self, page, slot, race):

		chr_id = self.__GetSlotChrID(page, slot)

		chr.CreateInstance(chr_id)
		chr.SelectInstance(chr_id)
		chr.SetVirtualID(chr_id)
		#
		self.instanceIDs.append(chr_id)

		chr.SetRace(race)
		chr.SetArmor(0)
		chr.SetHair(0)

		chr.Refresh()
		chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)

		chr.SetRotation(0.0)
		chr.Hide()

	def __SelectGender(self, gender):
		for button in self.genderButtonList:
			button.SetUp()

		self.genderButtonList[gender].Down()

		old_gender = self.gender
		self.gender = gender

		for v1 in GENDER_LIST:
			for i in xrange(SLOT_COUNT[v1]):
				chr.SelectInstance(self.__GetSlotChrID(v1, i))
				if v1==self.gender:
					chr.Show()
				else:
					chr.Hide()
		self.__ResetNameList(old_gender)
		if self.slot >= SLOT_COUNT[self.gender]:
			# self.NameList[self.slot].SetAlpha(0.0)
			self.__SelectSlot(app.GetRandom(0, SLOT_COUNT[self.gender]-1))
			return # the scene will be already updated, so return or double updated scene
		self.__UpdateScene()

	def __SelectShape(self, shape):
		self.shapeList[self.gender][self.slot] = shape

		for button in self.shapeButtonList:
			button.SetUp()

		self.shapeButtonList[shape].Down()

		chr_id = self.__GetSlotChrID(self.gender, self.slot)
		chr.SelectInstance(chr_id)
		chr.ChangeShape(shape)
		chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)

	def GetSlotIndex(self):
		return self.slot

	def RefreshStat(self):
		statSummary = self.stat[0] + self.stat[1] + self.stat[2] + self.stat[3]
		self.destGauge =	(
								float(self.stat[0])/float(statSummary),
								float(self.stat[1])/float(statSummary),
								float(self.stat[2])/float(statSummary),
								float(self.stat[3])/float(statSummary),
							)

		for i in xrange(4):
			self.statValue[i].SetText(str(self.stat[i]))

	def __ResetNameList(self, old_gender):
		for i in xrange(SLOT_COUNT[old_gender]):
			self.destNameAlpha[i] = 0.0
			# self.curNameAlpha[i] += (self.destNameAlpha[i] - self.curNameAlpha[i]) / 10.0
			self.NameList[old_gender][i].SetAlpha(0.0)

	def __UpdateScene(self):
		for i in xrange(SLOT_COUNT[self.gender]):
			self.destNameAlpha[i] = 0.0

		self.destNameAlpha[self.slot] = 1.0

		for i in xrange(SLOT_COUNT[self.gender]):
			self.destRotation[(i+self.slot)%SLOT_COUNT[self.gender]] = self.SLOT_ROTATION[self.gender][i]

		if self.IsShow():
			snd.PlaySound("sound/ui/click.wav")

		event.ClearEventSet(self.descIndex)
		self.descIndex = event.RegisterEventSet(self.DESCRIPTION_FILE_NAME[self.slot])

		chr_id = self.__GetSlotChrID(self.gender, self.slot)
		if chr.HasInstance(chr_id):
			chr.SelectInstance(chr_id)
			self.__SelectShape(self.shapeList[self.gender][self.slot])

			self.__RefreshSpecIcons()

	def __SelectSlot(self, slot):

		if slot < 0:
			return

		if slot >= SLOT_COUNT[self.gender]:
			return

		if self.slot == slot:
			return

		self.slot = slot
		self.ResetStat()
		#
		self.__UpdateScene()

	def CreateCharacter(self):

		if -1 != self.reservingRaceIndex:
			return

		textName = self.editCharacterName.GetText()
		if False == self.__CheckCreateCharacter(textName):
			return

		if musicInfo.selectMusic != "":
			snd.FadeLimitOutMusic("BGM/"+musicInfo.selectMusic, systemSetting.GetMusicVolume()*0.05)

		self.DisableWindow()


		chr_id = self.__GetSlotChrID(self.gender, self.slot)

		chr.SelectInstance(chr_id)

		self.reservingRaceIndex = chr.GetRace()

		self.reservingShapeIndex = self.shapeList[self.gender][self.slot]
		self.reservingStartTime = app.GetTime()

		for eachSlot in xrange(SLOT_COUNT[self.gender]):

			sel_id = self.__GetSlotChrID(self.gender, eachSlot)

			chr.SelectInstance(sel_id)

			if eachSlot == self.slot:
				chr.PushOnceMotion(chr.MOTION_INTRO_SELECTED)
			else:
				chr.PushOnceMotion(chr.MOTION_INTRO_NOT_SELECTED)

	def CancelCreate(self):
		self.stream.SetSelectCharacterPhase()

	def __DecreaseSlotIndex(self):
		slotIndex = (self.GetSlotIndex() - 1 + SLOT_COUNT[self.gender]) % SLOT_COUNT[self.gender]
		self.__SelectSlot(slotIndex)

	def __IncreaseSlotIndex(self):
		slotIndex = (self.GetSlotIndex() + 1) % SLOT_COUNT[self.gender]
		self.__SelectSlot(slotIndex)

	def PrevDescriptionPage(self):
		if True == event.IsWait(self.descIndex):
			if event.GetVisibleStartLine(self.descIndex)-event.BOX_VISIBLE_LINE_COUNT >= 0:
				event.SetVisibleStartLine(self.descIndex, event.GetVisibleStartLine(self.descIndex)-event.BOX_VISIBLE_LINE_COUNT)
				event.Skip(self.descIndex)
		else:
			event.Skip(self.descIndex)

	def NextDescriptionPage(self):
		if True == event.IsWait(self.descIndex):
			event.SetVisibleStartLine(self.descIndex, event.GetVisibleStartLine(self.descIndex)+event.BOX_VISIBLE_LINE_COUNT)
			event.Skip(self.descIndex)
		else:
			event.Skip(self.descIndex)

	def __CheckCreateCharacter(self, name):
		if len(name) == 0:
			self.PopupMessage(localeInfo.CREATE_INPUT_NAME, self.EnableWindow)
			return False

		if name.find(localeInfo.CREATE_GM_NAME)!=-1:
			self.PopupMessage(localeInfo.CREATE_ERROR_GM_NAME, self.EnableWindow)
			return False

		if net.IsInsultIn(name):
			self.PopupMessage(localeInfo.CREATE_ERROR_INSULT_NAME, self.EnableWindow)
			return False

		return True

	def ResetStat(self):
		realIdx = GetRealIDnSlot(self.gender, self.slot)
		for i in xrange(4):
			self.stat[i] = self.START_STAT[realIdx][i]
		self.lastStatPoint = self.CREATE_STAT_POINT
		self.RefreshStat()

	## Event
	def OnCreateSuccess(self):
		self.stream.SetSelectCharacterPhase()

	def OnCreateFailure(self, type):
		if 0 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_STRANGE_NAME, self.EnableWindow)
		elif 1 == type:
			self.PopupMessage(localeInfo.CREATE_EXIST_SAME_NAME, self.EnableWindow)
		elif 2 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_SAME_AS_LOGIN, self.EnableWindow)
		else:
			self.PopupMessage(localeInfo.CREATE_FAILURE, self.EnableWindow)

	def OnKeyDown(self, key):
		for i in xrange(SLOT_COUNT[self.gender]):
			if key == 2+i:
				self.__SelectSlot(i)

		if 203 == key:
			self.__DecreaseSlotIndex()
		if 205 == key:
			self.__IncreaseSlotIndex()

		if 59 == key:
			self.__SelectGender(MAN)
		if 60 == key:
			self.__SelectGender(WOMAN)

		return True

	def OnUpdate(self):
		chr.Update()

		(xposEventSet, yposEventSet) = self.textBoard.GetGlobalPosition()
		event.UpdateEventSet(self.descIndex, xposEventSet+7, -(yposEventSet+7))
		self.descriptionBox.SetIndex(self.descIndex)

		for i in xrange(SLOT_COUNT[self.gender]):
			self.curNameAlpha[i] += (self.destNameAlpha[i] - self.curNameAlpha[i]) / 10.0
			self.NameList[self.gender][i].SetAlpha(self.curNameAlpha[i])

		for i in xrange(4):
			self.curGauge[i] += (self.destGauge[i] - self.curGauge[i]) / 10.0
			if abs(self.curGauge[i] - self.destGauge[i]) < 0.005:
				self.curGauge[i] = self.destGauge[i]
			self.GaugeList[i].SetPercentage(self.curGauge[i], 1.0)

		for page in xrange(PAGE_COUNT):
			for i in xrange(SLOT_COUNT[page]):
				chr.SelectInstance(self.__GetSlotChrID(page, i))

				distance = 50.0
				rotRadian = self.curRotation[i] * (math.pi*2) / 360.0
				x = distance*math.sin(rotRadian) + distance*math.cos(rotRadian)
				y = distance*math.cos(rotRadian) - distance*math.sin(rotRadian)
				chr.SetPixelPosition(int(x), int(y), 30)

				if abs(self.destRotation[i] - self.curRotation[i]) < 1.0:
					self.curRotation[i] = self.destRotation[i]

				dir = app.GetRotatingDirection(self.destRotation[i], self.curRotation[i])
				rot = app.GetDegreeDifference(self.destRotation[i], self.curRotation[i])

				if app.DEGREE_DIRECTION_RIGHT == dir:
					self.curRotation[i] += rot / 10.0
				elif app.DEGREE_DIRECTION_LEFT == dir:
					self.curRotation[i] -= rot / 10.0

				self.curRotation[i] = (self.curRotation[i] + 360.0) % 360.0

		###########################################################
		if -1 != self.reservingRaceIndex:
			if app.GetTime() - self.reservingStartTime >= 1.5:

				chrSlot=self.stream.GetCharacterSlot()
				textName = self.editCharacterName.GetText()
				raceIndex = self.reservingRaceIndex
				shapeIndex = self.reservingShapeIndex

				startStat = self.START_STAT[self.reservingRaceIndex]
				statCon = self.stat[0] - startStat[0]
				statInt = self.stat[1] - startStat[1]
				statStr = self.stat[2] - startStat[2]
				statDex = self.stat[3] - startStat[3]

				net.SendCreateCharacterPacket(chrSlot, textName, raceIndex, shapeIndex, statCon, statInt, statStr, statDex)

				self.reservingRaceIndex = -1

		###########################################################

	def EmptyFunc(self):
		pass

	def PopupMessage(self, msg, func=0):
		if not func:
			func=self.EmptyFunc

		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)

	def OnPressExitKey(self):
		self.CancelCreate()
		return True

	def OverInStatButton(self, stat):
		if not self.STAT_DESCRIPTION.has_key(stat):
			return

		self.toolTip.ClearToolTip()
		self.toolTip.AppendTextLine(self.STAT_DESCRIPTION[stat])
		self.toolTip.Show()

	def OverOutStatButton(self):
		self.toolTip.Hide()
