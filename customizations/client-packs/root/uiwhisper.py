import ui
import net
import chat
import player
import app
import localeInfo
import ime
import chr
import constInfo
import messenger

class WhisperButton(ui.Button):
	def __init__(self):
		ui.Button.__init__(self, "TOP_MOST")

	def __del__(self):
		ui.Button.__del__(self)

	def SetToolTipText(self, text, x=0, y = 32):
		ui.Button.SetToolTipText(self, text, x, y)
		self.ToolTipText.Show()

	def SetToolTipTextWithColor(self, text, color, x=0, y = 32):
		ui.Button.SetToolTipText(self, text, x, y)
		self.ToolTipText.SetPackedFontColor(color)
		self.ToolTipText.Show()

	def ShowToolTip(self):
		if 0 != self.ToolTipText:
			self.ToolTipText.Show()

	def HideToolTip(self):
		if 0 != self.ToolTipText:
			self.ToolTipText.Show()

class WhisperDialog(ui.ScriptWindow):

	class TextRenderer(ui.Window):
		def SetTargetName(self, targetName):
			self.targetName = targetName

		def OnRender(self):
			(x, y) = self.GetGlobalPosition()
			chat.RenderWhisper(self.targetName, x, y)

	class ResizeButton(ui.DragButton):

		def __init__(self):
			ui.DragButton.__init__(self)

		def __del__(self):
			ui.DragButton.__del__(self)

		def OnMouseOverIn(self):
			app.SetCursor(app.HVSIZE)

		def OnMouseOverOut(self):
			app.SetCursor(app.NORMAL)

	def __init__(self, eventMinimize, eventClose):
		print "NEW WHISPER DIALOG  ----------------------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)
		self.targetName = ""
		self.eventMinimize = eventMinimize
		self.eventClose = eventClose
		self.eventAcceptTarget = None
		self.lastSentencePos = 0

	def __del__(self):
		print "---------------------------------------------------------------------------- DELETE WHISPER DIALOG"
		ui.ScriptWindow.__del__(self)

	def LoadDialog(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/WhisperDialog.py")
		except:
			import exception
			exception.Abort("WhisperDialog.LoadDialog.LoadScript")

		try:
			GetObject=self.GetChild
			self.titleName = GetObject("titlename")
			self.titleNameEdit = GetObject("titlename_edit")
			self.closeButton = GetObject("closebutton")
			self.scrollBar = GetObject("scrollbar")
			self.chatLine = GetObject("chatline")
			self.minimizeButton = GetObject("minimizebutton")
			self.ignoreButton = GetObject("ignorebutton")
			self.reportViolentWhisperButton = GetObject("reportviolentwhisperbutton")
			self.acceptButton = GetObject("acceptbutton")
			self.sendButton = GetObject("sendbutton")
			self.board = GetObject("board")
			self.editBar = GetObject("editbar")
			self.gamemasterMark = GetObject("gamemastermark")
			self.gameMasterTipBoard = GetObject("GameMasterTipBoard")
		except:
			import exception
			exception.Abort("DialogWindow.LoadDialog.BindObject")

		self.gamemasterMark.Hide()
		self.gameMasterTipBoard.Hide()

		self.titleName.SetText("")
		self.titleNameEdit.SetText("")
		self.minimizeButton.SetEvent(ui.__mem_func__(self.Minimize))
		self.closeButton.SetEvent(ui.__mem_func__(self.Close))
		self.scrollBar.SetPos(1.0)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.chatLine.SAFE_SetKeyDownEvent(self.OnKeyDown)
		self.chatLine.SetReturnEvent(ui.__mem_func__(self.SendWhisper))
		self.chatLine.SetEscapeEvent(ui.__mem_func__(self.Minimize))
		self.chatLine.SetMultiLine()
		self.sendButton.SetEvent(ui.__mem_func__(self.SendWhisper))
		self.titleNameEdit.SetReturnEvent(ui.__mem_func__(self.AcceptTarget))
		self.titleNameEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.ignoreButton.SetEvent(ui.__mem_func__(self.IgnoreTarget))
		self.reportViolentWhisperButton.SetEvent(ui.__mem_func__(self.ReportViolentWhisper))
		self.acceptButton.SetEvent(ui.__mem_func__(self.AcceptTarget))

		self.textRenderer = self.TextRenderer()
		self.textRenderer.SetParent(self)
		self.textRenderer.SetPosition(20, 28)
		self.textRenderer.SetTargetName("")
		self.textRenderer.Show()

		self.resizeButton = self.ResizeButton()
		self.resizeButton.SetParent(self)
		self.resizeButton.SetSize(20, 20)
		self.resizeButton.SetPosition(280, 180)
		self.resizeButton.SetMoveEvent(ui.__mem_func__(self.ResizeWhisperDialog))
		self.resizeButton.Show()

		self.ResizeWhisperDialog()

	@ui.WindowDestroy
	def Destroy(self):
		self.eventMinimize = None
		self.eventClose = None
		self.eventAcceptTarget = None

		self.ClearDictionary()
		self.scrollBar.Destroy()
		self.titleName = None
		self.titleNameEdit = None
		self.closeButton = None
		self.scrollBar = None
		self.chatLine = None
		self.sendButton = None
		self.ignoreButton = None
		self.reportViolentWhisperButton = None
		self.acceptButton = None
		self.minimizeButton = None
		self.textRenderer = None
		self.board = None
		self.editBar = None
		self.resizeButton = None
		self.gameMasterTipBoard = None

	def ResizeWhisperDialog(self):
		(xPos, yPos) = self.resizeButton.GetLocalPosition()
		if xPos < 280:
			self.resizeButton.SetPosition(280, yPos)
			return
		if yPos < 150:
			self.resizeButton.SetPosition(xPos, 150)
			return
		self.SetWhisperDialogSize(xPos + 20, yPos + 20)

	def SetWhisperDialogSize(self, width, height):
		try:

			max = int((width-90)/6) * 3 - 6

			self.board.SetSize(width, height)
			self.scrollBar.SetPosition(width-25, 35)
			self.scrollBar.SetScrollBarSize(height-100)
			self.scrollBar.SetPos(1.0)
			self.editBar.SetSize(width-18, 50)
			self.chatLine.SetSize(width-90, 40)
			self.chatLine.SetLimitWidth(width-90)
			self.SetSize(width, height)

			if 0 != self.targetName:
				chat.SetWhisperBoxSize(self.targetName, width - 50, height - 90)

			self.textRenderer.SetPosition(20, 28)
			self.scrollBar.SetPosition(width-25, 35)
			self.editBar.SetPosition(10, height-60)
			self.sendButton.SetPosition(width-80, 10)
			self.minimizeButton.SetPosition(width-42, 12)
			self.closeButton.SetPosition(width-24, 12)

			self.gameMasterTipBoard.SetPosition(-10, 0)

			self.SetChatLineMax(max)

		except:
			import exception
			exception.Abort("WhisperDialog.SetWhisperDialogSize.BindObject")

	def OnKeyDown(self, key):
		if app.VK_UP == key:
			self.__PrevLastSentenceStack()
			return True

		if app.VK_DOWN == key:
			self.__NextLastSentenceStack()
			return True

		ui.EditLine.BaseOnIMEKeyDown(self.chatLine, key)

	def __GetWhisperData(self):
		player_name = player.GetMainCharacterName()
		if not constInfo.WHISPER_DICT.has_key(player_name):
			return None

		if not constInfo.WHISPER_DICT[player_name].has_key(self.targetName):
			return None

		return constInfo.WHISPER_DICT[player_name][self.targetName]

	# LAST_SENTENCE_STACK
	def __PrevLastSentenceStack(self):
		data = self.__GetWhisperData()
		if not data:
			return

		sentence_stack = data["message_stack"]
		if sentence_stack and self.lastSentencePos < len(sentence_stack):
			self.lastSentencePos += 1
			lastSentence = sentence_stack[-self.lastSentencePos]
			self.chatLine.SetText(lastSentence)
			self.chatLine.SetEndPosition()

	def __NextLastSentenceStack(self):
		data = self.__GetWhisperData()
		if not data:
			return

		sentence_stack = data["message_stack"]
		if sentence_stack and self.lastSentencePos > 1:
			self.lastSentencePos -= 1
			lastSentence = sentence_stack[-self.lastSentencePos]
			self.chatLine.SetText(lastSentence)
			self.chatLine.SetEndPosition()

	def __PushLastSentenceStack(self, text):
		if len(text) <= 0:
			return

		data = self.__GetWhisperData()
		if not data:
			return

		sentence_stack = data["message_stack"]

		LAST_SENTENCE_STACK_SIZE = 8
		if len(sentence_stack) > LAST_SENTENCE_STACK_SIZE:
			sentence_stack.pop(0)

		sentence_stack.append(text)
		constInfo.WHISPER_DICT[player.GetMainCharacterName()][self.targetName] = data

	def __PushHistoryStack(self, text):
		if len(text) <= 0:
			return

		data = self.__GetWhisperData()
		if not data:
			return

		sentence_stack = data["history"]
		LAST_SENTENCE_STACK_SIZE = 12
		if len(sentence_stack) > LAST_SENTENCE_STACK_SIZE:
			sentence_stack.pop(0)

		sentence_stack.append([chat.WHISPER_TYPE_NORMAL, text])
		constInfo.WHISPER_DICT[player.GetName()][self.targetName] = data

	# END_OF_LAST_SENTENCE_STACK

	def SetChatLineMax(self, max):
		self.chatLine.SetMax(max)

		from grpText import GetSplitingTextLine

		text = self.chatLine.GetText()
		if text:
			self.chatLine.SetText(GetSplitingTextLine(text, max, 0))

	def OpenWithTarget(self, targetName, targetEmpire=0):
		chat.CreateWhisper(targetName)
		chat.SetWhisperBoxSize(targetName, self.GetWidth() - 60, self.GetHeight() - 90)
		self.chatLine.SetFocus()
		self.titleName.SetText(targetName)
		self.targetName = targetName
		self.textRenderer.SetTargetName(targetName)
		self.titleNameEdit.Hide()
		self.ignoreButton.Show()

		self.RefreshIgnoreButton(messenger.IsBlock(targetName))

		if app.IsDevStage():
			self.reportViolentWhisperButton.Show()
		else:
			self.reportViolentWhisperButton.Hide()
		self.acceptButton.Hide()
		self.gamemasterMark.Hide()
		self.minimizeButton.Show()

		if targetEmpire > 0 and targetEmpire != player.GetEmpire():
			chat.AppendWhisper(chat.WHISPER_TYPE_SYSTEM, self.targetName, localeInfo.WHISPER_ANOTHER_EMPIRE_WARNING)

	def OpenWithoutTarget(self, event):
		self.eventAcceptTarget = event
		self.titleName.SetText("")
		self.titleNameEdit.SetText("")
		self.titleNameEdit.SetFocus()
		self.targetName = 0
		self.titleNameEdit.Show()
		self.ignoreButton.Hide()
		self.reportViolentWhisperButton.Hide()
		self.acceptButton.Show()
		self.minimizeButton.Hide()
		self.gamemasterMark.Hide()
		self.gameMasterTipBoard.Hide()

	def SetGameMasterLook(self):
		return
		print "SetGameMasterLook"
		self.ignoreButton.Hide()
		self.gamemasterMark.Show()
		self.gameMasterTipBoard.Show()
		self.reportViolentWhisperButton.Hide()

	def Minimize(self):
		self.titleNameEdit.KillFocus()
		self.chatLine.KillFocus()
		self.Hide()

		if None != self.eventMinimize:
			return self.eventMinimize(self.targetName)

		return True

	def Close(self):
		chat.ClearWhisper(self.targetName)
		self.titleNameEdit.KillFocus()
		self.chatLine.KillFocus()
		self.Hide()

		data = self.__GetWhisperData()
		if data is not None:
			constInfo.WHISPER_DICT[player.GetName()].pop(self.targetName)

		if None != self.eventClose:
			return self.eventClose(self.targetName)

		return True

	def ReportViolentWhisper(self):
		net.SendChatPacket("/reportviolentwhisper " + self.targetName)

	def IgnoreTarget(self):
		if messenger.IsBlock(self.targetName):
			net.SendMessengerUnblockPacket(self.targetName)
		else:
			net.SendMessengerBlockPacket(self.targetName)

	def RefreshIgnoreButton(self, state):
		print "state is ", state
		if state:
			self.ignoreButton.SetText(localeInfo.WHISPER_UNBAN)
		else:
			self.ignoreButton.SetText(localeInfo.WHISPER_BAN)

	def AcceptTarget(self):
		name = self.titleNameEdit.GetText()
		if len(name) <= 0:
			self.Close()
			return

		if None != self.eventAcceptTarget:
			self.titleNameEdit.KillFocus()
			self.eventAcceptTarget(name)

	def OnScroll(self):
		chat.SetWhisperPosition(self.targetName, self.scrollBar.GetPos())

	def SendWhisper(self):

		text = self.chatLine.GetText()
		textLength = len(text)

		if textLength > 0:
			if net.IsInsultIn(text):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHAT_INSULT_STRING)
				return

			net.SendWhisperPacket(self.targetName, text)
			self.chatLine.SetText("")

			add_msg = player.GetName() + " : " + text
			chat.AppendWhisper(chat.WHISPER_TYPE_NORMAL, self.targetName, add_msg)
			self.__PushLastSentenceStack(text)
			self.__PushHistoryStack(add_msg)
			self.lastSentencePos = 0

	def OnTop(self):
		self.chatLine.SetFocus()

	def BindInterface(self, interface):
		self.interface = interface

	def OnMouseLeftButtonDown(self):
		hyperlink = ui.GetHyperlink()
		if hyperlink:
			if app.IsPressed(app.DIK_LALT):
				link = chat.GetLinkFromHyperlink(hyperlink)
				ime.PasteString(link)
			else:
				self.interface.MakeHyperlinkTooltip(hyperlink)
