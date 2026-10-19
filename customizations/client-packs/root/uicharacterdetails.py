import ui
import localeInfo
import player
import item
import uiToolTip
import wndMgr
import app

class CharacterDetailsUI(ui.ScriptWindow):
	def __init__(self, parent):
		#print "CharacterDetailsUI __init__"
		self.uiCharacterStatus = parent
		ui.ScriptWindow.__init__(self)
		self.toolTip = uiToolTip.ToolTip()

		self.__LoadScript()
		#fix first time position
		self.AutoAdjustPosition()

	def __del__(self):
		#print "CharacterDetailsUI __del__"
		self.uiCharacterStatus = None
		self.toolTip = None
		ui.ScriptWindow.__del__(self)

	def __LoadScript(self):
		#print "CharacterDetailsUI __LoadScript"

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/CharacterDetailsWindow.py")
		except:
			import exception
			exception.Abort("CharacterDetailsUI.__LoadScript")

		## CharacterWindow.py width = 253
		self.Width = 253 - 3

		self.GetChild("TitleBar").CloseButtonHide()
		self.ScrollBar = self.GetChild("ScrollBar")
		self.ScrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))

		self.UI_MAX_COUNT = 13

		## UI KEY & VALUE
		self.INFO_TEXT	= 0
		self.INFO_TOOLTIP = 1
		self.INFO_VALUE	= 2
		self.CATEGORY_STARTLINE	= -1
		self.CATEGORY_ENDLINE	= -2

		## Child
		self.labelList		= []
		self.labelValueList	= []
		self.labelTextList	= []
		self.horizonBarList	= []
		self.horizonBarNameList = []

		for i in xrange(self.UI_MAX_COUNT):
			self.labelList.append( self.GetChild("label%s"%i) )
			self.labelValueList.append( self.GetChild("labelvalue%s"%i) )
			self.labelTextList.append( self.GetChild("labelname%s"%i) )
			self.horizonBarList.append( self.GetChild("horizontalbar%s"%i) )
			self.horizonBarNameList.append( self.GetChild("horizontalbarName%s"%i) )

		for i in xrange(self.UI_MAX_COUNT):
			self.labelTextList[i].SetOverEvent( ui.__mem_func__(self.__ButtonOverIn), i )
			self.labelTextList[i].SetOverOutEvent( ui.__mem_func__(self.__ButtonOverOut), i )
			if localeInfo.IsARABIC():
				(x,y) = self.labelTextList[i].GetLocalPosition()
				self.labelTextList[i].SetPosition(65, y+7)
				self.labelTextList[i].SetWindowHorizontalAlignLeft()
				self.labelTextList[i].ButtonText.SetHorizontalAlignRight()
				(x,y) = self.labelList[i].GetLocalPosition()
				self.labelList[i].SetPosition(10 , y)
				self.labelList[i].SetWindowHorizontalAlignLeft()
			else:
				(x,y) = self.labelTextList[i].GetLocalPosition()
				self.labelTextList[i].SetPosition(80, y)
				self.labelTextList[i].SetWindowHorizontalAlignLeft()
				self.labelTextList[i].ButtonText.SetHorizontalAlignRight()
				(x,y) = self.labelList[i].GetLocalPosition()
				self.labelList[i].SetPosition(120 , y)
				self.labelList[i].SetWindowHorizontalAlignLeft()

		self.__Initialize()

	def OnMouseWheel(self, delta):
		if not self.ScrollBar or not self.ScrollBar.IsShow():
			return False
		return self.ScrollBar.OnMouseWheel(delta)

	def __Initialize(self):
		self.InfoList = []

		self.InfoList.append( [ localeInfo.DETAILS_CATE_1, "", self.CATEGORY_STARTLINE ] )
		self.InfoList.append( [ localeInfo.DETAILS_1, localeInfo.DETAILS_TOOLTIP_1, player.POINT_ATTBONUS_HUMAN ] )
		self.InfoList.append( [ localeInfo.DETAILS_14, localeInfo.DETAILS_TOOLTIP_14, player.POINT_NORMAL_HIT_DAMAGE_BONUS ] )

		#self.InfoList.append( [ "", "", self.CATEGORY_ENDLINE ] )

		self.Diff = len(self.InfoList) - self.UI_MAX_COUNT
		stepSize = 1.0 / self.Diff
		# self.ScrollBar.SetScrollStep( stepSize )
		self.ScollPos = 0
		self.RefreshLabel()

	def Show(self):
		#print "CharacterDetailsUI Show"
		ui.ScriptWindow.Show(self)
		self.SetTop()

	def Close(self):
		#print "CharacterDetailsUI Close"
		self.Hide()

	def AdjustPosition(self, x, y):
		self.SetPosition(x + self.Width, y)

	def AutoAdjustPosition(self):
		if self.uiCharacterStatus:
			(x, y) = self.uiCharacterStatus.GetGlobalPosition()
			width = self.uiCharacterStatus.GetWidth()
			self.SetPosition(x + width, y)

	def OnScroll(self):
		self.RefreshLabel()
		pass

	def RefreshLabel(self):
		self.ScollPos = int(self.ScrollBar.GetPos() * self.Diff)
		# self.ScollPos = int(self.ScrollBar.GetPos())

		count = max(len(self.InfoList), self.UI_MAX_COUNT)

		if count < self.UI_MAX_COUNT:
			self.ScollPos = 0

		for i in xrange(count):
			idx = i + self.ScollPos

			text = self.InfoList[idx][self.INFO_TEXT]
			type = self.InfoList[idx][self.INFO_VALUE]

			if type == self.CATEGORY_STARTLINE:
				self.__LabelTitleLine(i, text)
			elif type == self.CATEGORY_ENDLINE:
				self.__EmptyLine(i)
			else:
				value = player.GetStatus(type)

				self.__LabelLine(i, text, value)

	def __LabelTitleLine(self, idx, text):
		self.labelList[idx].Hide()
		self.labelTextList[idx].Hide()
		self.horizonBarList[idx].Show()
		self.horizonBarNameList[idx].SetText( text )

	def __EmptyLine(self, idx):
		self.labelList[idx].Hide()
		self.labelTextList[idx].Hide()
		self.horizonBarList[idx].Hide()

	def __LabelLine(self, idx, text, value):
		self.labelList[idx].Show()
		self.labelTextList[idx].Show()
		self.horizonBarList[idx].Hide()

		self.labelTextList[idx].SetText( text )
		# self.labelTextList[idx].ButtonText.SetHorizontalAlignRight()
		# self.labelTextList[idx].ButtonText.SetHorizontalAlignLeft()
		self.labelValueList[idx].SetText( str(value) )

	def __ButtonOverIn(self, i):
		#print "__ButtonOverIn %s" % i
		idx = i + self.ScollPos
		tooltip = self.InfoList[idx][self.INFO_TOOLTIP]

		arglen = len(str(tooltip))
		pos_x, pos_y = wndMgr.GetMousePosition()

		self.toolTip.ClearToolTip()
		self.toolTip.SetThinBoardSize(6 * arglen)
		self.toolTip.SetToolTipPosition(pos_x + 50, pos_y + 50)
		self.toolTip.AppendTextLine(tooltip, 0xffffff00)
		self.toolTip.Show()

	def __ButtonOverOut(self, idx):
		self.toolTip.Hide()

	def OnTop(self):
		if self.uiCharacterStatus:
			self.uiCharacterStatus.SetTop()
