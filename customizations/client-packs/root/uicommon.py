import ui
import localeInfo
import app
import ime
import uiScriptLocale
import player
import eventManager

POPUP_EVENT = "POPUP_EVENT" # args | text: string

class PopupManager:
	def __init__(self):
		self.popups = []

		eventManager.EventManager().add_observer(POPUP_EVENT, self.Popup)

	def Popup(self, text):
		if len(self.popups) > 0:
			if self.popups[len(self.popups)-1].rawText == text:
				return

		p = PopupDialog()
		p.SetText(text)
		p.Open()
		self.popups.append(p)

	def Destroy(self):
		for i in self.popups:
			i.Close()
			i.Destroy()

		self.popups = []


class PopupDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		if app.ENABLE_IKASHOP_RENEWAL:
			self.autocloseTime = None
		self.__LoadDialog()
		self.acceptEvent = lambda *arg: None
		self.rawText = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/PopupDialog.py")

			self.board = self.GetChild("board")
			self.message = self.GetChild("message")
			self.accceptButton = self.GetChild("accept")
			self.accceptButton.SetEvent(ui.__mem_func__(self.Close))

			self.message.Hide()
			self.messages = []

		except:
			import exception
			exception.Abort("PopupDialog.LoadDialog.BindObject")

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()
		if self.acceptEvent:
			self.acceptEvent()

		self.rawText = None

	@ui.WindowDestroy
	def Destroy(self):
		self.Close()
		for msg in self.messages:
			msg.Hide()
			msg = None

		self.messages = []
		self.ClearDictionary()

	def SetWidth(self, width):
		height = self.GetHeight()
		self.SetSize(width, height)
		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def Resize(self):
		start_pos = 0
		minWidth = self.GetWidth()
		messages_count = len(self.messages)
		for i in range(messages_count):
			msg = self.messages[i]
			(width, height) = msg.GetTextSize()
			minWidth = max(width + 30, minWidth)
			msg.SetPosition(0, 30+start_pos)
			if i < messages_count - 1:
				start_pos += height + 2

		self.SetSize(minWidth, 105 + start_pos)
		self.board.SetSize(minWidth, 105 + start_pos)
		self.SetCenterPosition()
		self.UpdateRect()

	def SetText(self, text):
		self.rawText = text
		textSplit = text.split("[ENTER]")
		for txt in textSplit:
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetText(txt)
			textLine.SetHorizontalAlignCenter()
			textLine.SetWindowHorizontalAlignCenter()
			textLine.Show()
			self.messages.append(textLine)

		self.Resize()

	def SetAcceptEvent(self, event):
		self.acceptEvent = event

	def SetButtonName(self, name):
		self.accceptButton.SetText(name)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnIMEReturn(self):
		self.Close()
		return True
	if app.ENABLE_IKASHOP_RENEWAL:
		def SetAutoClose(self, seconds):
			self.autocloseTime = app.GetTime() + seconds

		def OnUpdate(self):
			if self.autocloseTime is not None:
				remainTime = max(0, self.autocloseTime - app.GetTime())
				if remainTime == 0:
					self.autocloseTime = None
					self.accceptButton.SetText(uiScriptLocale.OK)
					self.Close()
					return
				self.accceptButton.SetText(uiScriptLocale.OK + " ({:0.1f} s)".format(remainTime))



class InputDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.closeEvent = None
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):

		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/inputdialog.py")

		getObject = self.GetChild
		self.board = getObject("Board")
		self.acceptButton = getObject("AcceptButton")
		self.cancelButton = getObject("CancelButton")
		self.inputSlot = getObject("InputSlot")
		self.inputValue = getObject("InputValue")

	def Open(self):
		self.inputValue.SetFocus()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		if self.closeEvent:
			self.closeEvent()
			self.closeEvent = None

		self.ClearDictionary()
		self.board = None
		self.acceptButton = None
		self.cancelButton = None
		self.inputSlot = None
		self.inputValue = None
		self.Hide()
		return True

	def SetTitle(self, name):
		self.board.SetTitleName(name)

	def SetNumberMode(self):
		self.inputValue.SetNumberMode()

	def SetSecretMode(self):
		self.inputValue.SetSecret()

	def SetFocus(self):
		self.inputValue.SetFocus()

	def SetMaxLength(self, length):
		width = length * 6 + 10
		self.SetBoardWidth(max(width + 50, 160))
		self.SetSlotWidth(width)
		self.inputValue.SetMax(length)

	def SetSlotWidth(self, width):
		self.inputSlot.SetSize(width, self.inputSlot.GetHeight())
		self.inputValue.SetSize(width, self.inputValue.GetHeight())
		if self.IsRTL():
			self.inputValue.SetPosition(self.inputValue.GetWidth(), 0)

	def SetBoardWidth(self, width):
		self.SetSize(max(width + 50, 160), self.GetHeight())
		self.board.SetSize(max(width + 50, 160), self.GetHeight())
		if self.IsRTL():
			self.board.SetPosition(self.board.GetWidth(), 0)
		self.UpdateRect()

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)
		self.inputValue.OnIMEReturn = event

	def SetCancelEvent(self, event):
		self.board.SetCloseEvent(event)
		self.cancelButton.SetEvent(event)
		self.inputValue.OnPressEscapeKey = event

	def GetText(self):
		return self.inputValue.GetText()

	def OnPressEscapeKey(self):
		self.Close()
		return True

class InputDialogWithDescription(InputDialog):

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()

	def __del__(self):
		InputDialog.__del__(self)

	def __CreateDialog(self):

		pyScrLoader = ui.PythonScriptLoader()
		if localeInfo.IsARABIC() :
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "inputdialogwithdescription.py")
		else:
			pyScrLoader.LoadScriptFile(self, "uiscript/inputdialogwithdescription.py")

		try:
			getObject = self.GetChild
			self.board = getObject("Board")
			self.acceptButton = getObject("AcceptButton")
			self.cancelButton = getObject("CancelButton")
			self.inputSlot = getObject("InputSlot")
			self.inputValue = getObject("InputValue")
			self.description = getObject("Description")

		except:
			import exception
			exception.Abort("InputDialogWithDescription.LoadBoardDialog.BindObject")

	def SetDescription(self, text):
		self.description.SetText(text)

class InputDialogWithDescription2(InputDialog):

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()

	def __del__(self):
		InputDialog.__del__(self)

	def __CreateDialog(self):

		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/inputdialogwithdescription2.py")

		try:
			getObject = self.GetChild
			self.board = getObject("Board")
			self.acceptButton = getObject("AcceptButton")
			self.cancelButton = getObject("CancelButton")
			self.inputSlot = getObject("InputSlot")
			self.inputValue = getObject("InputValue")
			self.description1 = getObject("Description1")
			self.description2 = getObject("Description2")

		except:
			import exception
			exception.Abort("InputDialogWithDescription.LoadBoardDialog.BindObject")

	def SetDescription1(self, text):
		self.description1.SetText(text)

	def SetDescription2(self, text):
		self.description2.SetText(text)

class QuestionDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.closeEvent = None
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog.py")

		self.board = self.GetChild("board")
		self.textLine = self.GetChild("message")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		if self.closeEvent:
			self.closeEvent()
			self.closeEvent = None

		self.Hide()

	def SetWidth(self, width):
		height = self.GetHeight()
		self.SetSize(width, height)
		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def SAFE_SetAcceptEvent(self, event):
		self.acceptButton.SAFE_SetEvent(event)

	def SAFE_SetCancelEvent(self, event):
		self.cancelButton.SAFE_SetEvent(event)

	def SetDefaultCancelEvent(self):
		self.cancelButton.SAFE_SetEvent(self.Close)

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)

	def SetCancelEvent(self, event):
		self.cancelButton.SetEvent(event)

	def SetText(self, text):
		self.textLine.SetText(text)

	def SetAcceptText(self, text):
		self.acceptButton.SetText(text)

	def SetCancelText(self, text):
		self.cancelButton.SetText(text)

	def OnPressEscapeKey(self):
		self.Close()
		return True

class QuestionDialog2(QuestionDialog):

	def __init__(self):
		QuestionDialog.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		QuestionDialog.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog2.py")

		self.board = self.GetChild("board")
		self.textLine1 = self.GetChild("message1")
		self.textLine2 = self.GetChild("message2")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def SetText1(self, text):
		self.textLine1.SetText(text)

	def SetText2(self, text):
		self.textLine2.SetText(text)

class QuestionDialog3Options(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__CreateDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog3.py")

		self.board = self.GetChild("board")
		self.textLine = self.GetChild("message")
		self.acceptButton = self.GetChild("accept")
		self.middleButton = self.GetChild("middle")
		self.cancelButton = self.GetChild("cancel")

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.acceptButton = None
		self.Hide()

	def SetWidth(self, width):
		height = self.GetHeight()
		self.SetSize(width, height)
		self.board.SetSize(width, height)
		self.SetCenterPosition()
		self.UpdateRect()

	def SAFE_SetAcceptEvent(self, event):
		self.acceptButton.SAFE_SetEvent(event)

	def SAFE_SetMiddleEvent(self, event):
		self.middleButton.SAFE_SetEvent(event)

	def SAFE_SetCancelEvent(self, event):
		self.cancelButton.SAFE_SetEvent(event)

	def SetDefaultCancelEvent(self):
		self.cancelButton.SAFE_SetEvent(self.Close)

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)

	def SetMiddleEvent(self, event):
		self.middleButton.SetEvent(event)

	def SetCancelEvent(self, event):
		self.cancelButton.SetEvent(event)

	def SetText(self, text):
		self.textLine.SetText(text)
		width, height = self.textLine.GetTextSize()
		currentWidth = self.GetWidth()
		minWidth = width + 16
		if currentWidth < minWidth:
			self.SetWidth(minWidth)

	def SetAcceptText(self, text):
		self.acceptButton.SetText(text)

	def SetMiddleText(self, text):
		self.middleButton.SetText(text)

	def SetCancelText(self, text):
		self.cancelButton.SetText(text)

	def OnPressEscapeKey(self):
		self.Close()
		return True

class QuestionDialogWithTimeLimit(QuestionDialog2):

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__CreateDialog()
		self.endTime = 0

	def __del__(self):
		QuestionDialog2.__del__(self)

	def __CreateDialog(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/questiondialog2.py")

		self.board = self.GetChild("board")
		self.textLine1 = self.GetChild("message1")
		self.textLine2 = self.GetChild("message2")
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def Open(self, msg, timeout):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

		self.SetText1(msg)
		self.endTime = app.GetTime() + timeout

	def OnUpdate(self):
		leftTime = max(0, self.endTime - app.GetTime())
		self.SetText2(localeInfo.UI_LEFT_TIME % (leftTime))

class MoneyInputDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.closeEvent = None
		self.moneyHeaderText = localeInfo.MONEY_INPUT_DIALOG_SELLPRICE
		self.__CreateDialog()
		self.SetMaxLength(9)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __CreateDialog(self):

		pyScrLoader = ui.PythonScriptLoader()
		if app.ENABLE_CHEQUE_SYSTEM:
			pyScrLoader.LoadScriptFile(self, "uiscript/moneyinputdialog_cheque.py")
		else:
			pyScrLoader.LoadScriptFile(self, "uiscript/moneyinputdialog.py")

		getObject = self.GetChild
		self.board = self.GetChild("board")
		self.acceptButton = getObject("AcceptButton")
		self.cancelButton = getObject("CancelButton")
		self.inputValue = getObject("InputValue")
		self.inputValue.SetNumberMode()
		self.inputValue.OnIMEUpdate = ui.__mem_func__(self.OnValueUpdate)
		self.moneyText = getObject("MoneyValue")

		if app.ENABLE_CHEQUE_SYSTEM:
			self.chequeText = getObject("ChequeValue")
			self.inputChequeValue = getObject("InputValue_Cheque")
			self.inputChequeValue.OnIMEUpdate = ui.__mem_func__(self.OnValueUpdate)
			self.inputChequeValue.OnMouseLeftButtonDown = ui.__mem_func__(self.__ClickChequeEditLine)
			self.inputValue.OnMouseLeftButtonDown = ui.__mem_func__(self.__ClickValueEditLine)
		if app.ENABLE_IKASHOP_RENEWAL:
			self.inputValue.numberMode = False
	def Open(self):
		self.inputValue.SetText("")
		self.inputValue.SetFocus()
		self.OnValueUpdate()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		
	def Close(self):
		if self.closeEvent:
			self.closeEvent()
			self.closeEvent = None

		self.ClearDictionary()
		if app.ENABLE_CHEQUE_SYSTEM:
			self.inputChequeValue = None
		self.board = None
		self.acceptButton = None
		self.cancelButton = None
		self.inputValue = None
		self.Hide()

	def SetTitle(self, name):
		self.board.SetTitleName(name)

	def SetFocus(self):
		self.inputValue.SetFocus()

	def SetMaxLength(self, length):
		length = min(9, length)
		self.inputValue.SetMax(length)

	def SetMoneyHeaderText(self, text):
		self.moneyHeaderText = text

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)
		self.inputValue.OnIMEReturn = event

	def SetCancelEvent(self, event):
		self.board.SetCloseEvent(event)
		self.cancelButton.SetEvent(event)
		self.inputValue.OnPressEscapeKey = event

	def SetValue(self, value):
		if app.ENABLE_IKASHOP_RENEWAL:
			if value == "":
				self.inputValue.SetText("")
				self.OnValueUpdate()
				ime.SetCursorPosition(0)
				return
		value=str(value)
		self.inputValue.SetText(value)
		self.OnValueUpdate()
		ime.SetCursorPosition(len(value))
	if app.ENABLE_IKASHOP_RENEWAL:
		def SoftClose(self):
			self.Hide()
			for child in vars(self).values():
				if isinstance(child, ui.EditLine):
					if child.IsFocus():
						child.KillFocus()





	def GetText(self):
		return self.inputValue.GetText()

	if app.ENABLE_CHEQUE_SYSTEM:
		def HideCheque(self):
			slotCheque = self.GetChild("InputSlot_Cheque")
			slotYang = self.GetChild("InputSlot")
			if slotCheque and slotCheque.IsShow():
				slotCheque.Hide()
				slotYang.SetPosition(0, slotYang.GetLocalPosition()[1])
				slotYang.SetWindowHorizontalAlignCenter()
				self.chequeText.Hide()
				self.GetChild("SellInfoText").Hide()
				self.moneyText.SetPosition(0, 59)
				self.acceptButton.SetPosition(self.acceptButton.GetLocalPosition()[0], 78)
				self.cancelButton.SetPosition(self.cancelButton.GetLocalPosition()[0], 78)
				if app.ENABLE_IKASHOP_RENEWAL:
					self.SetSize(200, 110)
					self.board.SetSize(200, 110)
				else:
	
					self.SetSize(200, 110)
					self.board.SetSize(200, 110)

		def ShowCheque(self):
			slotCheque = self.GetChild("InputSlot_Cheque")
			slotYang = self.GetChild("InputSlot")
			if not slotCheque.IsShow():
				slotCheque.Show()
				slotYang.SetPosition(90, slotYang.GetLocalPosition()[1])
				slotYang.SetWindowHorizontalAlignLeft()
				self.chequeText.Show()
				self.GetChild("SellInfoText").Show()
				self.moneyText.SetPosition(0, 100)
				self.acceptButton.SetPosition(self.acceptButton.GetLocalPosition()[0], 118)
				self.cancelButton.SetPosition(self.cancelButton.GetLocalPosition()[0], 118)
				if app.ENABLE_IKASHOP_RENEWAL:
					self.SetSize(200, 150)
					self.board.SetSize(200, 150)
				else:
	
					self.SetSize(200, 150)
					self.board.SetSize(200, 150)

		def SetCheque(self, cheque):
			if app.ENABLE_IKASHOP_RENEWAL:
				if cheque == "":
					self.inputChequeValue.SetText(cheque)
					self.OnValueUpdate()
					ime.SetCursorPosition(0)
					return

			cheque=str(cheque)
			self.inputChequeValue.SetText(cheque)
			self.OnValueUpdate()
			ime.SetCursorPosition(len(cheque)+1)

		def GetTextCheque(self):
			return self.inputChequeValue.GetText()

		def __ClickChequeEditLine(self):
			self.inputChequeValue.SetFocus()
			if len(self.inputValue.GetText()) <= 0:
				self.inputValue.SetText(str(0))

		def __ClickValueEditLine(self):
			self.inputValue.SetFocus()
			if len(self.inputChequeValue.GetText()) <= 0:
				self.inputChequeValue.SetText(str(0))

		def GetCheque(self):
			return self.inputChequeValue.GetText()

		def OnValueUpdate(self):
			if self.inputValue.IsFocus():
				ui.EditLine.OnIMEUpdate(self.inputValue)
			elif self.inputChequeValue.IsFocus():
				ui.EditLine.OnIMEUpdate(self.inputChequeValue)
			else:
				pass

			text = self.inputValue.GetText()
			cheque_text = self.inputChequeValue.GetText()
			if app.ENABLE_IKASHOP_RENEWAL:
				text = text.lower().replace("k", "000")


			money = 0
			cheque = 0
			GOLD_MAX = 2000000000
			CHEQUE_MAX = 1000

			if text and text.isdigit():
				try:
					money = int(text)

					if money >= GOLD_MAX:
						money = GOLD_MAX - 1
						self.inputValue.SetText(str(money))
				except ValueError:
					money = 0

			if cheque_text and cheque_text.isdigit():
				try:
					cheque = int(cheque_text)

					if cheque >= CHEQUE_MAX:
						cheque = CHEQUE_MAX - 1
						self.inputValue.SetText(str(cheque))
				except ValueError:
					cheque = 0
			self.chequeText.SetText(str(cheque) + " " + localeInfo.CHEQUE_SYSTEM_UNIT_WON)
			self.moneyText.SetText(localeInfo.NumberToGoldNotText(money) + " " + localeInfo.CHEQUE_SYSTEM_UNIT_YANG)
	else:
		def OnValueUpdate(self):
			ui.EditLine.OnIMEUpdate(self.inputValue)

			text = self.inputValue.GetText()

			money = 0
			if text and text.isdigit():
				try:
					money = int(text)
				except ValueError:
					money = 199999999

			self.moneyText.SetText(self.moneyHeaderText + localeInfo.NumberToMoneyString(money))

class NewMoneyInputDialog(MoneyInputDialog):
	def __init__(self):
		MoneyInputDialog.__init__(self)
		self.SetMaxLength(14)
		self.inputValue.SetNumberMode(False)

	def __del__(self):
		MoneyInputDialog.__del__(self)

	def SetMaxLength(self, length):
		length = min(14, length)
		self.inputValue.SetMax(length)
		self.inputValue.SetUserMax(length)

	def OnValueUpdate(self):
		ui.EditLine.OnIMEUpdate(self.inputValue)
		moneyValue = localeInfo.MoneyStringToNumber(self.inputValue.GetText())

		if moneyValue > player.GOLD_MAX:
			moneyValue = player.GOLD_MAX

		self.moneyText.SetText(self.moneyHeaderText + " " + localeInfo.NumberToMoneyString(moneyValue))
