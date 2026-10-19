import net

import ui
import networkModule

###################################################################################################
## PointReset
class PointResetDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.ConfirmDialog = ui.ScriptWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "uiscript/questiondialog2.py")
			PythonScriptLoader.LoadScriptFile(self.ConfirmDialog, "uiscript/questiondialog2.py")
		except:
			import exception
			exception.Abort("PointResetDialog.LoadDialog.LoadObject")

		try:
			GetObject = self.ConfirmDialog.GetChild
			self.ConfirmText = GetObject("message1")
			self.ConfirmText2 = GetObject("message2")
			self.ConfirmAcceptButton = GetObject("accept")
			self.ConfirmCancelButton = GetObject("cancel")
		except:
			import exception
			exception.Abort("PointResetDialog.LoadWindow.BindObject")

		self.GetChild("accept").SetEvent(ui.__mem_func__(self.OpenConfirmDialog))
		self.GetChild("cancel").SetEvent(ui.__mem_func__(self.Close))

		## Confirm Dialog
		self.ConfirmText.SetFontColor(1.0, 0.3, 0.3)
		self.ConfirmAcceptButton.SetEvent(ui.__mem_func__(self.ResetPoint))
		self.ConfirmCancelButton.SetEvent(ui.__mem_func__(self.Close))

	def Destroy(self):
		self.ClearDictionary()
		self.ConfirmDialog.ClearDictionary()
		self.ConfirmAcceptButton.SetEvent(0)
		self.ConfirmCancelButton.SetEvent(0)

		self.ConfirmDialog = 0
		self.ConfirmText = 0
		self.ConfirmAcceptButton = 0
		self.ConfirmCancelButton = 0

	def OpenDialog(self):
		self.Show()

	def OpenConfirmDialog(self):
		self.ConfirmDialog.Show()
		self.ConfirmDialog.SetTop()

	def ResetPoint(self):
		net.SendChatPacket("/pointreset")
		self.Close()

	def Close(self):
		self.ConfirmDialog.Hide()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True
