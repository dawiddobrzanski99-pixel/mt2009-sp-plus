import ui
import eventManager
import localeInfo
import chat
import net
import uiCommon

EVENT_REPORT_PLAYER = "EVENT_REPORT_PLAYER" # args: name: string, vid: number

class ReportPlayerDialog(ui.ScriptWindow):
	REPORT_REASONS = [
		"Wybierz",
		localeInfo.REPORT_PLAYER_REASON_BOT,
		localeInfo.REPORT_PLAYER_REASON_FISHBOT,
		localeInfo.REPORT_PLAYER_REASON_HACK,
		localeInfo.REPORT_PLAYER_REASON_INSULT,
	]
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

		eventManager.EventManager().add_observer(EVENT_REPORT_PLAYER, self.Open)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.vid = 0
		self.reasonIndex = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/reportplayerdialog.py")

			self.titleBar = self.GetChild("TitleBar")
			self.playerNameLabel = self.GetChild("PlayerNameLabel")
			self.reasonSelect = self.GetChild("ReasonSelect")
			self.reportButton = self.GetChild("ReportButton")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.reportButton.SAFE_SetEvent(self.Report)

			for i in range(len(self.REPORT_REASONS)):
				self.reasonSelect.InsertItem(i, self.REPORT_REASONS[i])
			self.reasonSelect.SAFE_SetEvent(self.OnReasonSelect)
			self.reasonSelect.SelectItem(0)

		except:
			import exception
			exception.Abort("ReportPlayerDialog.LoadDialog.BindObject")

	def OnReasonSelect(self, index):
		self.reasonSelect.SetCurrentItem(self.REPORT_REASONS[index])
		self.reasonIndex = index

	def Report(self):
		if self.reasonIndex == 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REPORT_PLAYER_SELECT_REASON)
			return

		cmd = "/report_player %d %d" % (self.vid, self.reasonIndex)
		net.SendChatPacket(cmd)
		eventManager.EventManager().send_event(uiCommon.POPUP_EVENT, localeInfo.REPORT_DONE)
		self.Close()

	def Open(self, name, vid):
		self.vid = vid
		self.playerNameLabel.SetText(name)
		self.reasonSelect.SelectItem(0)

		self.SetCenterPosition()
		self.Show()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True
