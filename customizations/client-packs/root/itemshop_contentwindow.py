import ui

class ItemShopContentWindow(ui.Window):
	def __init__(self, parent):
		ui.Window.__init__(self)
		self.SetSize(parent.GetWidth(), parent.GetHeight())
		self.SetParent(parent)
		self.SetPosition(0, 0)

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		pass
