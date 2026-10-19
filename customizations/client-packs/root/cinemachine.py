import ui

class CinemachineWindow(ui.ScriptWindow):
	TWEEN_DURATION_DEFAULT = 3

	MODE_BEZIER = 0
	MODE_LINEAR = 1

	ROTATION_MODE_BEZIER = 0
	ROTATION_MODE_LINEAR = 1

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.TWEEN_DURATION = self.TWEEN_DURATION_DEFAULT
		self.cameraInterpolationMode = self.MODE_BEZIER
		self.rotationInterpolationMode = self.ROTATION_MODE_BEZIER
		self.LoadScript()

	def __del(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()

	def LoadScript(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/CinemachineWindow.py")

			self.titleBar = self.GetChild("TitleBar")
			self.durationEditLine = self.GetChild("DurationLine")
			self.linearModeButton = self.GetChild("LinearModeButton")
			self.bezierModeButton = self.GetChild("BezierModeButton")

			self.bezierRotationModeButton = self.GetChild("BezierRotationModeButton")
			self.linearRotationModeButton = self.GetChild("LinearRotationModeButton")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.durationEditLine.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
			self.durationEditLine.SAFE_SetReturnEvent(self.Close)

			self.camModeButtons = [self.bezierModeButton, self.linearModeButton]
			self.bezierModeButton.SAFE_SetEvent(self.__ChangeCamMode, self.MODE_BEZIER)
			self.linearModeButton.SAFE_SetEvent(self.__ChangeCamMode, self.MODE_LINEAR)

			self.rotModeButtons = [self.bezierRotationModeButton, self.linearRotationModeButton]
			self.bezierRotationModeButton.SAFE_SetEvent(self.__ChangeRotMode, self.ROTATION_MODE_BEZIER)
			self.linearRotationModeButton.SAFE_SetEvent(self.__ChangeRotMode, self.ROTATION_MODE_LINEAR)

			self.__ChangeCamMode(self.MODE_BEZIER)
			self.__ChangeRotMode(self.ROTATION_MODE_BEZIER)


		except:
			import exception
			exception.Abort("CinemachineWindow.LoadDialog.BindObject")

	def __ChangeCamMode(self, mode):
		for btn in self.camModeButtons:
			btn.SetUp()
			btn.Enable()

		self.camModeButtons[mode].Down()
		self.camModeButtons[mode].Disable()
		self.cameraInterpolationMode = mode

	def __ChangeRotMode(self, mode):
		for btn in self.rotModeButtons:
			btn.SetUp()
			btn.Enable()

		self.rotModeButtons[mode].Down()
		self.rotModeButtons[mode].Disable()
		self.rotationInterpolationMode = mode

		# print "rot mode: " + str(mode)

	def __OnValueUpdate(self):
		ui.EditLine.OnIMEUpdate(self.durationEditLine)

		text = self.durationEditLine.GetText()

		if len(text) < 1:
			self.TWEEN_DURATION = self.TWEEN_DURATION_DEFAULT
			return

		value = float(text)
		self.TWEEN_DURATION = value


	def Open(self):
		self.durationEditLine.SetText("")
		self.Show()

	def Close(self):
		self.Hide()

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def OnPressEscapeKey(self):
		self.Close()
		return True
