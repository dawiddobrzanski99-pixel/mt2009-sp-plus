from interfaceModule import *

import app
import wndMgr
import systemSetting
import mouseModule
import grp
import ui

app.SetMouseHandler(mouseModule.mouseController)
app.SetHairColorEnable(True)
wndMgr.SetMouseHandler(mouseModule.mouseController)
wndMgr.SetScreenSize(systemSetting.GetWidth(), systemSetting.GetHeight())
app.Create("METIN2", systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
mouseModule.mouseController.Create()

import chr

class TestGame(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)

		self.interface = Interface()
		self.interface.MakeInterface()
		self.interface.ShowDefaultWindows()


	def __del__(self):
		ui.Window.__del__(self)

	def OnKeyUp(self, key):
		print key
		return True

	def OnUpdate(self):
		app.UpdateGame()

	def OnRender(self):
		app.RenderGame()
		grp.PopState()
		grp.SetInterfaceRenderState()

game = TestGame()
game.SetSize(systemSetting.GetWidth(), systemSetting.GetHeight())
game.Show()

app.Loop()
