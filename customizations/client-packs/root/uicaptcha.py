import ui
import captcha
import localeInfo
import app
import colorInfo
import wndMgr
import constInfo
import net

class CaptchaDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self, layer="TOP_MOST")
		self.__Initialize()
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.captchaImage = None
		self.expire_time = 0
		self.attempt_count = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.__Initialize()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/captchadialog.py")

			self.captchaBg = self.GetChild("CaptchaBg")
			self.tipBoard = self.GetChild("TipBoard")
			self.codeEditLine = self.GetChild("CodeInput")
			self.timeLabel = self.GetChild("TimeLabel")
			self.leftLabel = self.GetChild("LeftLabel")
			self.acceptButton = self.GetChild("AcceptButton")
			self.requestChangeButton = self.GetChild("RequestNewCaptchaButton")

			self.acceptButton.SAFE_SetEvent(self.__OnAcceptButton)
			self.requestChangeButton.SAFE_SetEvent(self.__OnRequestChangeButton)

			self.inputBlocker = ui.Window()
			self.inputBlocker.SetPosition(0, 0)
			self.inputBlocker.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
			self.inputBlocker.Hide()

		except:
			import exception
			exception.Abort("CaptchaDialog.LoadDialog.BindObject")

	def __OnAcceptButton(self):
		if len(self.codeEditLine.GetText()) < 1:
			return

		net.SendChatPacket("/captcha_respond verify %s" % self.codeEditLine.GetText())
		self.codeEditLine.Clear()

	def __OnRequestChangeButton(self):
		net.SendChatPacket("/captcha_respond change_request")

	def SetImage(self):
		if not self.captchaImage:
			img = ui.ImageBox()
			img.SetParent(self.captchaBg)
			img.SetWindowHorizontalAlignCenter()
			img.SetPosition(0, 6)
			self.captchaImage = img

		captcha.SetCaptchaImage(0, self.captchaImage.hWnd)
		self.captchaImage.Show()

	def SetAttemptCount(self, count):
		self.attempt_count = count
		self.leftLabel.SetText(localeInfo.CAPTCHA_LEFT_LABEL % count)

		if count == 2:
			self.leftLabel.SetFontColorTuple(colorInfo.TITLE_RGB_EVIL_1)
		elif count < 2:
			self.leftLabel.SetFontColorTuple(colorInfo.TITLE_RGB_EVIL_3)
		else:
			self.leftLabel.SetPackedFontColor(colorInfo.FONT_COLOR)

	def RefreshTime(self):
		left_time = max(self.expire_time - app.GetGlobalTimeStamp(), 0)
		self.timeLabel.SetText(localeInfo.CAPTCHA_TIME_LABEL % left_time)

		if left_time < 10:
			self.timeLabel.SetFontColorTuple(colorInfo.TITLE_RGB_EVIL_3)
		elif left_time < 30:
			self.timeLabel.SetFontColorTuple(colorInfo.TITLE_RGB_EVIL_1)
		else:
			self.timeLabel.SetPackedFontColor(colorInfo.FONT_COLOR)

	def OnUpdatePerSecond(self):
		if self.IsShow():
			self.RefreshTime()

	def Open(self, expire_time, attempt_count):
		self.expire_time = expire_time
		self.SetAttemptCount(attempt_count)
		self.RefreshTime()

		min_x = 20
		max_x = wndMgr.GetScreenWidth() - 20 - 302
		min_y = 20
		max_y = wndMgr.GetScreenHeight() - 20 - 315
		self.SetPosition(app.GetRandom(min_x, max_x), app.GetRandom(min_y, max_y))
		self.Show()
		self.SetTop()
		self.codeEditLine.SetFocus()
		self.inputBlocker.Show()

	def Close(self):
		self.Hide()
		captcha.ClearCaptchaImage(0)
		self.inputBlocker.Hide()


### GAME MASTER CAPTCHA DIALOG
class GameMasterCaptchaDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.captchaImage = None
		self.expire_time = 0
		self.attempt_count = 0
		self.pid = 0
		self.logs = []

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/gamemaster_captchadialog.py")

			self.closeButton = self.GetChild("CloseButton")
			self.codeLabel = self.GetChild("Code")
			self.playerNameLabel = self.GetChild("PlayerName")
			self.timeLabel = self.GetChild("TimeLeft")

			self.closeButton.SAFE_SetEvent(self.Close)

		except:
			import exception
			exception.Abort("GameMasterCaptchaDialog.LoadDialog.BindObject")

	def SetImage(self, pid):
		if not self.captchaImage:
			img = ui.ImageBox()
			img.SetParent(self)
			img.SetWindowHorizontalAlignCenter()
			img.SetPosition(0, 60)
			self.captchaImage = img

		captcha.SetCaptchaImage(pid, self.captchaImage.hWnd)
		self.captchaImage.Show()

	def SetName(self, name, pid):
		self.playerNameLabel.SetText("Nick: %s (pid: |cff5af22c%d|r)" % (name, pid))

	def SetCode(self, code):
		self.codeLabel.SetText("Kod: |cffffa826%s|r" % code)

	def OnUpdatePerSecond(self):
		if self.IsShow():
			self.RefreshTime()

	def RefreshTime(self):
		left_time = max(self.expire_time - app.GetGlobalTimeStamp(), 0)
		self.timeLabel.SetText("Pozostaly czas: %ds" % left_time)

	def SetTime(self, time):
		self.expire_time = time
		self.RefreshTime()

	def AddLog(self, type, code=None, time=None):
		log = ui.TextLine()
		log.SetParent(self)
		log.SetPosition(10, 135 + len(self.logs) * 15)
		log.Show()
		self.logs.append(log)

		if type == captcha.OK:
			log.SetPackedFontColor(colorInfo.POSITIVE_COLOR)
			log.SetText("Poprawnie podany kod. Zajelo to %d sekund." % time)
			self.SetTime(0)
		elif type == captcha.NO_ATTEMPTS:
			log.SetPackedFontColor(colorInfo.NEGATIVE_COLOR)
			log.SetText("Wykorzystano wszystkie proby wpisania kodu. (|cffffa826%s|r)" % code)
			self.SetTime(0)
		elif type == captcha.WRONG_CODE:
			log.SetPackedFontColor(colorInfo.NEGATIVE_COLOR)
			log.SetText("Niepoprawny kod (|cffffa826%s|r)" % code)
		elif type == captcha.EXPIRE:
			log.SetPackedFontColor(colorInfo.NEGATIVE_COLOR)
			log.SetText("Czas minal.")
			self.SetTime(0)
		elif type == captcha.REQUEST_CHANGE:
			log.SetPackedFontColor(colorInfo.MEDIUM_COLOR)
			log.SetText("Zmiana kodu (|cffffa826%s|r)" % code)
		elif type == captcha.DISCONNECT:
			log.SetPackedFontColor(colorInfo.NEGATIVE_COLOR)
			log.SetText("Gracz sie wylogowal.")
			self.SetTime(0)
		else:
			log.SetText(type)

	def Open(self, expire_time, attempt_count, pid, playerName, code):
		if not constInfo.IS_GAMEMASTER:
			return

		self.pid = pid
		self.SetImage(pid)
		self.SetName(playerName, pid)
		self.SetCode(code)
		self.SetTime(expire_time)
		self.Show()

	def Close(self):
		self.Hide()
		captcha.ClearCaptchaImage(self.pid)
