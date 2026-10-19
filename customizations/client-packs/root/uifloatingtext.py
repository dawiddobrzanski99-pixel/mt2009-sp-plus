import ui
import app
import updateable
import colorInfo
import mathUtils
import gamefont
import systemSetting

class FloatingText(ui.TextLine):
	def __init__(self, text, is_negative, life_time=1.5):
		ui.TextLine.__init__(self, "UI_BOTTOM")

		self.SetFontName(gamefont.GetCurrentFontHuge())
		self.SetText(text)
		print is_negative
		if is_negative:
			self.SetFontColor(0.6, 0.1745, 0.1627)
		else:
			self.SetFontColor(0.3411, 0.7254, 0.3568)

		is_left_align = systemSetting.GetShowFloatingText() == 1
		if is_left_align:
			self.SetHorizontalAlignCenter()
		self.SetCenterPosition()
		x, y = self.GetGlobalPosition()

		self.start_pos = (x + (-30 if is_left_align else 30), y)
		last_y_pos_shift = app.GetRandom(60,70)
		self.end_pos = (self.start_pos[0] + (app.GetRandom(20,30) * (-1 if is_left_align else 1)), y + (last_y_pos_shift if is_negative else -last_y_pos_shift))

		self.SetPosition(self.start_pos[0], self.start_pos[1] + app.GetRandom(-10,10))

		self.Show()

		self.timer = 0
		self.life_time = life_time * updateable.ONE_SECOND

	def __del__(self):
		ui.TextLine.__del__(self)

	def OnUpdate(self):
		self.timer += updateable.FIXED_TIMESTEP_UPDATE
		clamped_progress = mathUtils.GetProgressClamped01(self.timer, self.life_time)
		progress = mathUtils.GetEaseOutCirc(clamped_progress)
		dest_x = mathUtils.GetLerp(self.start_pos[0], self.end_pos[0], progress)
		dest_y = mathUtils.GetLerp(self.start_pos[1], self.end_pos[1], progress)

		self.SetFontAlpha(1-mathUtils.GetEaseInExpo(clamped_progress))
		self.SetPosition(dest_x, dest_y)
		return progress >= 1
