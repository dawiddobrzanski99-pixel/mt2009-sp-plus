import ui
import localeInfo
import datetime
import chat

class MaintenanceDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		pass

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/maintenancedialog.py")

			self.startTime = self.GetChild("StartTime")
			self.duration = self.GetChild("Duration")
			self.closeButton = self.GetChild("CloseButton")

			self.closeButton.SAFE_SetEvent(self.Close)

		except:
			import exception
			exception.Abort("MaintenanceDialog.LoadDialog.BindObject")

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Open(self, start_timestamp, duration_seconds):
		self.Show()

		dt = datetime.datetime.fromtimestamp(start_timestamp)
		start_hour = dt.hour
		start_minute = dt.minute
		start_seconds = dt.second

		start_time = "%d:%02d" % (start_hour, start_minute)
		duration_text = localeInfo.SecondToDHM(duration_seconds)

		self.startTime.SetText(localeInfo.MAINTENANCE_DIALOG_START_TIME % start_time)
		self.duration.SetText(localeInfo.MAINTENANCE_DIALOG_DURATION % duration_text)

		chat.AppendChat(chat.CHAT_TYPE_NOTICE, localeInfo.MAINTENANCE_WHISPER % (start_time, duration_text))

	def Close(self):
		self.Hide()
