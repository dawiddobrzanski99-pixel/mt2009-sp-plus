# -*- coding: utf-8 -*-
import ui
import app
import player
import item
import grp
import playerSettingModule
import localeInfo
import uiCommon
import uiToolTip
from _weakref import proxy

from ui_event import Event


class GlobalRankingsManager(ui.SimplyWindow):
	ROOT_PATH = "d:/ymir work/ui/game/global-rankings/{}"
	RENDER_TARGET_INDEX = 9

	FACE_IMAGE_DICT = {
		playerSettingModule.RACE_WARRIOR_M	: "icon/face/warrior_m.tga",
		playerSettingModule.RACE_WARRIOR_W	: "icon/face/warrior_w.tga",
		playerSettingModule.RACE_ASSASSIN_M	: "icon/face/assassin_m.tga",
		playerSettingModule.RACE_ASSASSIN_W	: "icon/face/assassin_w.tga",
		playerSettingModule.RACE_SURA_M		: "icon/face/sura_m.tga",
		playerSettingModule.RACE_SURA_W		: "icon/face/sura_w.tga",
		playerSettingModule.RACE_SHAMAN_M	: "icon/face/shaman_m.tga",
		playerSettingModule.RACE_SHAMAN_W	: "icon/face/shaman_w.tga",
	}

	@staticmethod
	def CreatePlace(parent, yPos, ):
		window = [ui.Window() for _ in range(2)]
		# map(lambda wnd : wnd.AddFlag("not_pick"), window[1:])

		window[0].SetParent(parent)
		window[0].SetPosition(58, yPos)
		window[0].SetSize(133, 27)
		window[0].Show()

		window[1].SetParent(parent)
		window[1].SetPosition(58 + 133, yPos)
		window[1].SetSize(189, 27)
		window[1].Show()

		textLine = [ui.TextLine() for _ in range(2)]

		textLine[0].SetParent(window[0])
		textLine[0].SetPosition(0, -1)
		textLine[0].SetHorizontalAlignCenter()
		textLine[0].SetVerticalAlignCenter()
		textLine[0].SetText('-')
		textLine[0].SetOutline(True)
		textLine[0].Show()
		
		textLine[1].SetParent(window[1])
		textLine[1].SetPosition(0, -1)
		textLine[1].SetHorizontalAlignCenter()
		textLine[1].SetVerticalAlignCenter()
		textLine[1].SetText('-')
		textLine[1].SetOutline(True)
		textLine[1].Show()

		return (window, textLine, )

	@staticmethod
	def CreatePlayerPlace(parent, i, yPos, ):
		button = ui.Window()
		button.SetParent(parent)
		button.SetPosition(125, yPos)
		button.SetSize(255, 21)
		button.Show()

		window = ui.Window()
		window.AddFlag("not_pick")
		window.SetParent(button)
		window.SetPosition(0, 0)
		window.SetSize(245, 21)
		window.Show()

		textLine = ui.TextLine()
		textLine.SetParent(window)
		textLine.SetPosition(0, 0)
		textLine.SetHorizontalAlignCenter()
		textLine.SetVerticalAlignCenter()
		textLine.SetText('-')
		textLine.SetOutline(True)
		textLine.Show()

		imageBox = ui.ImageBox()
		imageBox.SetParent(button)
		imageBox.AddFlag("not_pick")
		imageBox.LoadImage( GlobalRankingsManager.ROOT_PATH.format("inactive.png"))
		imageBox.SetPosition(5, 0)
		imageBox.SetWindowHorizontalAlignRight()
		imageBox.SetWindowVerticalAlignCenter()
		imageBox.Show()

		return window, textLine, button, imageBox,

	@staticmethod
	def CalculateDate(time):
		import datetime
		return datetime.datetime.fromtimestamp(time).strftime("%d-%m-%Y ~ %H:%M:%S")

	@staticmethod
	def CalculateTime(time):
		return localeInfo.sec2time(time, "DHM")

	class RankingCategoryButton(ui.RadioButton):

		IMAGE_PATTERN = "d:/ymir work/ui/game/global-rankings/btn_{}.png"
		ICON_PATTERN = "d:/ymir work/ui/game/global-rankings/icons/icon_{}.png"
		WINDOW_SIZE = (165, 37)

		FIELD_SIZE = {"Icon" : (40, 42), "Type" : (105, 42)}
		FIELD_POS = {"Icon" : (0, 0), "Type" : (50, 0)}

		def __init__(self, iNum):
			ui.RadioButton.__init__(self)
			self.iNum = iNum
			self.Objects = {}
			self.__BuildWindow()

		def __eq__(self, rOther):
			if isinstance(rOther, GlobalRankingsManager.RankingCategoryButton):
				return self.iNum == rOther.iNum

			raise NotImplemented

		def __ne__(self, rOther):
			return not self.__eq__(rOther)

		def __BuildWindow(self):
			## Size
			self.SetSize(*self.WINDOW_SIZE)

			## Generate fields
			for sKey in ("Icon", "Type"):
				sKeyName = "{}_Field".format(sKey)
				self.Objects[sKeyName] = ui.Window()
				self.Objects[sKeyName].SetParent(self)
				self.Objects[sKeyName].AddFlag("not_pick")
				self.Objects[sKeyName].SetSize(*self.FIELD_SIZE[sKey])
				self.Objects[sKeyName].SetPosition(*self.FIELD_POS[sKey])
				self.Objects[sKeyName].Show()

			## Design
			self.SetUpVisual(self.IMAGE_PATTERN.format(0))
			self.SetOverVisual(self.IMAGE_PATTERN.format(1))
			self.SetDownVisual(self.IMAGE_PATTERN.format(2))

			## Generate corresponding icon image
			self.Objects["Icon"] = ui.MakeImageBox(self.Objects["Icon_Field"], self.ICON_PATTERN.format(self.iNum), 0, 0)
			self.Objects["Icon"].SetWindowHorizontalAlignCenter()
			self.Objects["Icon"].SetWindowVerticalAlignCenter()

			## Generate corresponding text lines
			self.Objects["Type"] = ui.MakeTextLine(self.Objects["Type_Field"])
			self.Objects["Type"].SetPosition(10, -1)
			self.Objects["Type"].SetFontName("Nunito Sans:10")
			self.Objects["Type"].SetLimitWidth(self.FIELD_SIZE["Type"][0])
			self.Objects["Type"].SetMultiLine()
			self.Objects["Type"].SetText(getattr(localeInfo, "GLOBAL_RANKINGS_CATEGORY_{}".format(self.iNum), "NOT_FOUND")) 
			self.Objects["Type"].SetPackedFontColor(0xFF9e9e9e)

			self.Show()

	class RankingWindow(ui.Window):
		WINDOW_SIZE = (445, 22)
		FIELD_SIZE = {"Pos" : (59, 22), "Name" : (145, 22), "Empire" : (145, 22), "Score" : (78, 22)}
		FIELD_POS = {"Pos" : (10, 0), "Name" : (75, 0), "Empire" : (226, 0), "Score" : (377, 0)}
		EMPIRE_NAMES = {1 : localeInfo.EMPIRE_A, 2 : localeInfo.EMPIRE_B, 3 : localeInfo.EMPIRE_C}
		FIELD_COLOR = {"Pos" : 0xFF7b7874, "Name" : 0xFFbca882, "Empire" : 0xFF7b7874, "Score" : 0xFF7b7874}

		def __init__(self):
			ui.Window.__init__(self)
			self.Objects = {}
			self.__BuildWindow()

		def __del__(self):
			ui.Window.__del__(self)
			self.Objects = {}

		def __BuildWindow(self):
			## Size
			self.SetSize(*self.WINDOW_SIZE)

			## Generate fields
			for sKey in self.FIELD_SIZE.keys():
				sKeyName = "{}_Field".format(sKey)
				self.Objects[sKeyName] = ui.Window()
				self.Objects[sKeyName].SetParent(self)
				self.Objects[sKeyName].SetSize(*self.FIELD_SIZE[sKey])
				self.Objects[sKeyName].SetPosition(*self.FIELD_POS[sKey])
				self.Objects[sKeyName].Show()

				## Generate corresponding text lines
				self.Objects["{}_Text".format(sKey)] = ui.MakeTextLine(self.Objects[sKeyName])
				self.Objects["{}_Text".format(sKey)].SetPackedFontColor(self.FIELD_COLOR[sKey])

		def SetData(self, sName, iEmpire, iScore, iPos = -1, bSelf = False):
			if iEmpire == -1:
				## Set it blank
				self.Objects["Name_Text"].SetText("-")
				self.Objects["Empire_Text"].SetText("-")
				self.Objects["Score_Text"].SetText("-")
			else:
				self.Objects["Name_Text"].SetText(sName)
				self.Objects["Empire_Text"].SetText(self.EMPIRE_NAMES.get(iEmpire, "Unknown"))
				if type(iScore) is not float:
					self.Objects["Score_Text"].SetText('.'.join([ i-3<0 and str(iScore)[:i] or str(iScore)[i-3:i] for i in range(len(str(iScore))%3, len(str(iScore))+1, 3) if i ]))
				else:
					self.Objects["Score_Text"].SetText(iScore)

			if iPos > -1:
				self.Objects["Pos_Text"].SetText(str(iPos))
			elif iPos == -1 and bSelf:
				self.Objects["Pos_Text"].SetText("-")
			else:
				self.Objects["Pos_Text"].SetText("")

		def GetText(self, name):
			return self.Objects.get("{}_Text".format(name)).GetText()

	def __init__(self, *Args, **Kwargs):
		ui.SimplyWindow.__init__(self, "UI", ("movable", "float", ), 660, 425, self.__Initialize, self.__Destroy)

	def __Initialize(self):
		self.windowConfig["category-count"] = 10
		self.windowConfig["category-per-page"] = 8
		self.windowConfig["category-index"] = -1
		self.windowConfig["player-count"] = 10 + 1
		#
		self.windowConfig["high-score"] = {}
		self.windowConfig["player-high-score"]   = {}
		self.windowConfig["season-time"]         = ()
		self.windowConfig["left-time"]           = 0

		board = ui.BoardWithTitleBar()
		board.SetParent(self)
		board.SetPosition(0, 0)
		board.SetSize(*self.GetSize())
		board.SetTitleName("GLOBAL_RANKINGS_WINDOW_TITLE")
		board.SetCloseEvent(self.Hide)
		board.Show()

		self.AppendObject("board-with-titlebar", board)

		window = ui.ImageBox()
		window.SetParent(board)
		window.SetPosition(10, 30)
		window.LoadImage(self.ROOT_PATH.format("categories-container.png"))
		window.Show()

		self.AppendObject("window", window, True)

		window = ui.ImageBox()
		window.SetParent(board)
		window.LoadImage(self.ROOT_PATH.format("elements-container-highscore.png"))
		window.SetWindowHorizontalAlignRight()
		window.SetPosition(10 + window.GetWidth(), 30)
		window.Show()

		self.AppendObject("window", window)

		window = ui.ImageBox()
		window.SetParent(board)
		window.SetPosition(10, 30)
		window.SetWindowHorizontalAlignRight()
		window.LoadImage(self.ROOT_PATH.format("elements-container-player.png"))
		window.Hide()

		self.AppendObject("window", window)

		button = ui.Button()
		button.SetParent(self.GetObject("window", 0))
		button.SetPosition(0, 50)
		button.SetUpVisual  (self.ROOT_PATH.format("btn-mode-ranking-0.png"))
		button.SetOverVisual(self.ROOT_PATH.format("btn-mode-ranking-1.png"))
		button.SetDownVisual(self.ROOT_PATH.format("btn-mode-ranking-2.png"))
		button.SetWindowHorizontalAlignCenter()
		button.SetWindowVerticalAlignBottom()
		button.SetEvent(self.__OnClickTypeCategoryButton)
		button.Show()

		self.AppendObject("type-category-button", button)


		self.__LoadCategoryItems()
		self.__LoadHighscoreItems()
		self.__LoadHighscoreInformation()

		# renderTarget =  ui.RenderTarget()
		# renderTarget.SetParent(self.GetObject("window", 1))
		# renderTarget.SetPosition(0, 30)
		# renderTarget.SetSize(\
		# 	self.GetObject("window", 1).GetWidth(),
		# 	self.GetObject("window", 1).GetHeight() - 21
		# )
		# player.SetBackground(self.RENDER_TARGET_INDEX, "d:/ymir work/ui/game/monster_card/model_view_bg.sub")
		# renderTarget.SetRenderTarget(self.RENDER_TARGET_INDEX)
		# renderTarget.Show()

		# self.AppendObject("render-target", renderTarget)


		self.windowIndex = 0
		self._realTime   = 0

	def __LoadCategoryItems(self):
		parent = self.GetObject("window", 0)

		controller = [ui.Window(), ui.ListBoxEx(), ui.ScrollBar()]
		controller[ 0 ].SetSize(parent.GetWidth() - 12, parent.GetHeight() - 45)
		controller[ 0 ].Show()
		
		controller[ 1 ].SetParent(parent)
		controller[ 1 ].AddFlag("not_pick")
		controller[ 1 ].SetSize(parent.GetWidth(), parent.GetHeight() - (45 + 4))
		controller[ 1 ].SetPosition(6, 2)
		controller[ 1 ].SetViewItemCount( self.windowConfig["category-per-page"] )
		controller[ 1 ].Show()

		controller[ 2 ].SetParent( parent )
		controller[ 2 ].SetPosition(controller [ 0 ].GetWidth() - 4, 5)
		controller[ 2 ].SetScrollBarSize( 226 )
		controller[ 2 ].Show()
		
		controller[ 1 ].SetScrollBar( controller[ 2 ] )

		for _ in range( self.windowConfig["category-count"] ):
			button = self.RankingCategoryButton( _ )
			button.SetParent(controller [ 0 ])
			button.SetEvent(Event(self.__OnClickCategoryButton, _))
			
			controller[ 1 ].SetItemSize(button.GetWidth(), button.GetHeight())
			controller[ 1 ].SetItemStep(button.GetHeight())
			controller[ 1 ].AppendItem( button )

			self.windowConfig["high-score"][_] =  { _ : ("", -1, -1, -1) for _ in range(self.windowConfig["player-count"])}

		self.AppendObject("category-with-scroll", controller)

	def __LoadHighscoreItems(self):
		parent = self.GetObject("window", 1)

		yPos = 36
		for _ in range( self.windowConfig["player-count"] ):
			highScorePlace = self.RankingWindow()
			highScorePlace.SetParent(parent)
			ySAdder = 8 if _ == self.windowConfig["player-count"] - 1 else 0
			highScorePlace.SetPosition(0, yPos + (_ * 31) + ySAdder)
			highScorePlace.Show()

			self.AppendObject("highscore-place", highScorePlace, True)

	def __LoadHighscoreInformation(self):
		parent = self.GetObject("window", 2)

		yPos = 131

		highScorePlace = ()
		for i in range( 3 ):
			highScorePlace += GlobalRankingsManager.CreatePlayerPlace(parent, i, yPos),

			yPos += highScorePlace[-1][0].GetHeight()
			yPos += 7

		yPos += 50
		highScorePlace += GlobalRankingsManager.CreatePlace(parent, yPos),

		image = ui.FillImage()
		image.SetParent( parent )
		image.SetPosition(0, 10)
		image.LoadBaseImage(self.ROOT_PATH.format("gauge-empty.png"))
		image.LoadFillImage(self.ROOT_PATH.format("gauge-full.png"))
		image.SetWindowHorizontalAlignCenter()
		image.SetWindowVerticalAlignBottom()
		# image.SetOverInEvent(Event(self.__ShowToolTip, "season-time"))
		# image.SetOverOutEvent(self.__HideToolTip)
		image.Show()

		self.AppendObject("highscore-information", (highScorePlace, image, ))

	def __OnClickTypeCategoryButton(self):
		map(ui.Window.Hide, self.GetObject("window")[1:])
		self.windowIndex = not self.windowIndex

		window = self.GetObject("window", self.windowIndex + 1)
		window.Show()

		# self._UpdatePlayerPage()


	def __ShowToolTip(self, what):
		index = self.windowConfig["category-index"]

		toolTip = uiToolTip.GetItemToolTipInstance()
		toolTip.ClearToolTip()
		toolTip.ResizeToolTip()

		if what == "season-time":
			start, end = self.windowConfig["season-time"]
			toolTip.AppendTextLine("GLOBAL_RANKINGS_TOOLTIP_WIPE_0".format( self.CalculateDate(start) ))
			toolTip.AppendTextLine("GLOBAL_RANKINGS_TOOLTIP_WIPE_1".format( self.CalculateDate(end) ))
			toolTip.AppendSpace(5)
			toolTip.AppendTextLine("GLOBAL_RANKINGS_TOOLTIP_WIPE_2".format(self.CalculateTime( self._realTime )))
			toolTip.AppendSpace(5)

		toolTip.ResizeToolTip()
		toolTip.AlignHorizonalCenter()
		toolTip.ShowToolTip()

	def __HideToolTip(self):
		uiToolTip.GetItemToolTipInstance().HideToolTip()

	def __Destroy(self):
		pass

	def __OnClickCategoryButton(self, index):
		ButtonList = self.GetObject("category-with-scroll")[1].itemList
		map(ui.RadioButton.SetUp, ButtonList)
		ButtonList[index].Down()

		## RadioButtons were already update so simply process raw logic
		self.windowConfig["category-index"] = index

		self._Refresh()


	def _Refresh(self):
		index = self.windowConfig["category-index"]
		if index == -1: return

		for _ in range( self.windowConfig["player-count"] - 1 ):
			self.GetObject("highscore-place", _).SetData(*self.windowConfig["high-score"][index][_])

		self._RefreshPlayerScore()

	def _RefreshPlayerScore(self):
		row         = self.GetObject("highscore-place", 10)
		index       = self.windowConfig["category-index"]

		try:
			row.SetData(*self.windowConfig["player-high-score"][ index ])
		except:
			sys_err("There's no registred category for this highscore")

	def RefreshHighscore(self, iStart, iEnd):
		iEnd -= 1

		self.windowConfig["season-time"]         = iStart, iEnd, 
		self.windowConfig["left-time"]           = max(0, iEnd - iStart)

	def UpdateRankingData(self, iCategory, iNum, sName, iEmpire, lScore):
		self.windowConfig["high-score"][ iCategory ][iNum] = (sName, iEmpire, lScore)

	def UpdateRankingData_Self(self, iCategory, iPos, sName, iEmpire, lScore):
		self.windowConfig["player-high-score"][ iCategory ] = [sName, iEmpire, lScore, iPos, True]

	def UpdateWindow(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def OnUpdate(self):
		if self.windowConfig["left-time"] == 0:
			return

		self._realTime = max(0, self.windowConfig["season-time"][1] - app.GetGlobalTimeStamp())

	def Open(self):
		super(GlobalRankingsManager, self).Open()
		# player.SelectModel(self.RENDER_TARGET_INDEX, 591)
		# player.SetVisibility(self.RENDER_TARGET_INDEX, True)

	def Close(self):
		super(GlobalRankingsManager, self).Close()

	def OnKeyDown(self, key):
		if key == app.VK_ESCAPE:
			self.Close()
			return True

		return False
