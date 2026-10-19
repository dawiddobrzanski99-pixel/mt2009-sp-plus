import ui
import constInfo
import net
import utils
import chat

class GameMasterTargetPlayerDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.pid = 0
		self.playerName = ""
		self.banDialog = None

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/gamemaster_targetplayer.py")

			self.closeButton = self.GetChild("CloseButton")
			self.playerLabel = self.GetChild("PlayerName")
			self.accountLabel = self.GetChild("AccountName")

			self.viewPlayerButton = self.GetChild("ViewPlayerButton")
			self.captchaButton = self.GetChild("CaptchaButton")
			self.banButton = self.GetChild("BanButton")
			self.kickButton = self.GetChild("KickButton")

			self.closeButton.SAFE_SetEvent(self.Close)
			self.viewPlayerButton.SAFE_SetEvent(self.__ViewPlayer)
			self.kickButton.SAFE_SetEvent(self.__Kick)
			self.banButton.SAFE_SetEvent(self.__Ban)
			self.captchaButton.SAFE_SetEvent(self.__Captcha)

		except:
			import exception
			exception.Abort("GameMasterTargetPlayerDialog.LoadDialog.BindObject")

	def CloseBanDialog(self):
		if self.banDialog:
			self.banDialog.Close()
			self.banDialog = None

	def SetName(self, name, pid, is_premium):
		text = "Nick: %s (pid: |cff5af22c%d|r)" % (name, pid)

		if is_premium:
			text += "|cffffa600*|r"

		self.playerLabel.SetText(text)

	def SetAccount(self, login, aid):
		self.accountLabel.SetText("Login: %s (aid: |cfffffb24%d|r)" % (login, aid))

	def __ViewPlayer(self):
		utils.open_url(constInfo.ADMIN_API + "players/%d" % self.pid)

	def __Ban(self):
		if self.banDialog:
			self.CloseBanDialog()

		self.banDialog = GameMasterBanDialog()
		self.banDialog.Open(self.playerName, self.pid)
		self.banDialog.SetCenterPosition()
		self.banDialog.SetTop()
		self.banDialog.Show()

	def __Kick(self):
		net.SendChatPacket("/dc %s" % self.playerName)

	def __Captcha(self):
		net.SendChatPacket("/captcha check pid:%d" % self.pid)

	def Open(self, pid, name, aid, login, is_premium):
		if not constInfo.IS_GAMEMASTER:
			return

		if not constInfo.ADMIN_API:
			return

		self.pid = pid
		self.playerName = name

		self.SetName(name, pid, is_premium)
		self.SetAccount(login, aid)
		self.Show()

	def Close(self):
		self.CloseBanDialog()
		self.Hide()

class GameMasterBanDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.pid = 0
		self.playerName = ""
		self.isPerm = False
		self.isInstant = False

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/gamemasterbandialog.py")

			self.titleBar = self.GetChild("TitleBar")
			self.titleLabel = self.GetChild("TitleName")
			self.banButton = self.GetChild("BanButton")

			self.durationSlot = self.GetChild("DurationSlot")
			self.durationInput = self.GetChild("DurationInput")
			self.reasonInput = self.GetChild("ReasonInput")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.banButton.SAFE_SetEvent(self.__Ban)

			self.permToggleButton = self.GetChild("PermToggleButton")
			self.permToggleButton.SetToggleDownEvent(self.__OnPermToggleDown)
			self.permToggleButton.SetToggleUpEvent(self.__OnPermToggleUp)
			self.permToggleButton.OnToggleDown()
			self.permToggleButton.Down()

			self.instantToggleButton = self.GetChild("InstantToggleButton")
			self.instantToggleButton.SetToggleDownEvent(self.__OnInstantToggleDown)
			self.instantToggleButton.SetToggleUpEvent(self.__OnInstantToggleUp)

		except:
			import exception
			exception.Abort("GameMasterTargetPlayerDialog.LoadDialog.BindObject")

	def SetName(self, name, pid):
		text = "Ban (%s pid: |cff5af22c%d|r)" % (name, pid)
		self.titleLabel.SetText(text)

	def __OnPermToggleDown(self):
		self.isPerm = True
		self.durationSlot.Hide()

	def __OnPermToggleUp(self):
		self.isPerm = False
		self.durationSlot.Show()

	def __OnInstantToggleDown(self):
		self.isInstant = True

	def __OnInstantToggleUp(self):
		self.isInstant = False

	def __GetReason(self):
		text = self.reasonInput.GetText()
		return text.replace(" ", "_")

	def __GetDuration(self):
		if self.isPerm:
			return 31536000
		else:
			return max(int(self.durationInput.GetText()), 1) * 86400

	def __Ban(self):
		if len(self.__GetReason()) < 3:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Podaj powod (min. 3 znaki)")
			return

		if not self.isPerm and len(self.durationInput.GetText()) < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Podaj czas trwania blokady w dniach.")
			return

		command = ""
		if self.isInstant:
			command = "/block_player %d %d %s" % (self.pid, self.__GetDuration(), self.__GetReason())
		else:
			command = "/block_pool %d %d %s" % (self.pid, self.__GetDuration(), self.__GetReason())

		net.SendChatPacket(command)
		self.Close()

	def Open(self, name, pid):
		if not constInfo.IS_GAMEMASTER:
			return

		self.pid = pid
		self.playerName = name

		self.SetName(name, pid)
		self.Show()

	def Close(self):
		self.Destroy()
		self.Hide()