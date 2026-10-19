import ui
import mathUtils
import updateable
import colorinfo

class BusyActionDialog(ui.ScriptWindow, updateable.UpdatableAbstract):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.duration = 0
		self.timer = 0
		self.action_type = 0
		self.text_anim_timer = 0
		self.text_anim_delay = 0.6 * updateable.ONE_SECOND
		self.text_anim_progress = 0
		self.close_timer = 0
		self.interrupted = False
		self.success = False
		self.LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/dialog_busy_action.py")

			self.progressBar = self.GetChild("progress")
			self.actionLabel = self.GetChild("action")
			self.tip = self.GetChild("tip")

		except:
			import exception
			exception.Abort("BusyActionDialog.LoadDialog.LoadScript")

	def OnUpdate(self):
		if self.interrupted or self.success:
			self.close_timer += updateable.FIXED_TIMESTEP_UPDATE

			if self.close_timer > updateable.ONE_SECOND:
				self.Close()
		else:
			self.SetProgress()
			self.timer += updateable.FIXED_TIMESTEP_UPDATE
			self.UpdateLabel()

	def GetActionName(self):
		if self.action_type == 1:
			return "Zbieranie"
		else:
			return "Trwa akcja"

	def UpdateLabel(self):
		self.text_anim_timer += updateable.FIXED_TIMESTEP_UPDATE
		if self.text_anim_timer >= self.text_anim_delay:
			self.text_anim_timer = 0

			if self.text_anim_progress >= 3:
				self.text_anim_progress = 0
			else:
				self.text_anim_progress += 1

		dots = '.' * self.text_anim_progress
		action_name = self.GetActionName() + dots
		self.actionLabel.SetText(action_name)

	def SetTipPosition(self, progress):
		min_pos = -1
		max_pos = 133
		self.tip.SetPosition(mathUtils.GetLerp(min_pos, max_pos, progress), 0)

	def CanUpdate(self):
		return self.IsShow() and (self.duration > 0 or self.interrupted)

	def GetProgress(self):
		return min(float(self.timer) / float(self.duration), 1.0)

	def SetProgress(self):
		progress = self.GetProgress()
		self.progressBar.SetPercentage(progress, 1.0)
		self.SetTipPosition(progress)

	def Fail(self, is_interrupt):
		self.actionLabel.SetPackedFontColor(colorinfo.NEGATIVE_COLOR)
		self.actionLabel.SetText("Przerwano" if is_interrupt else "Niepowodzenie")
		self.interrupted = True
		self.progressBar.SetColor(1.0, 0.4, 0.4, 1.0)
		self.tip.SetColor(1.0, 0.3, 0.3, 1.0)

	def Success(self):
		self.actionLabel.SetPackedFontColor(colorinfo.POSITIVE_COLOR)
		self.actionLabel.SetText("Sukces")
		self.success = True
		self.progressBar.SetColor(0.3, 1.0, 0.3, 1.0)
		self.tip.SetColor(0.3, 1.0, 0.3, 1.0)

	def Open(self, actionType, duration, success):
		if self.IsShow() and duration == 0:
			if not success:
				self.Fail(self.GetProgress() < 0.99)
				return
			else:
				self.Success()
				return

		self.action_type = actionType
		self.close_timer = 0
		self.text_anim_timer = 0
		self.text_anim_progress = 0
		self.progressBar.SetColor(1.0, 1.0, 1.0, 1.0)
		self.tip.SetColor(1.0, 1.0, 1.0, 1.0)
		self.timer = 0
		self.interrupted = False
		self.success = False

		self.duration = duration * updateable.ONE_SECOND
		self.actionLabel.SetPackedFontColor(colorinfo.FONT_COLOR)
		self.SetProgress()
		self.Show()

	def Close(self):
		self.Hide()
