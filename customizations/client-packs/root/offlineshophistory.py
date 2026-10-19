import file_utils
import ui
import localeInfo
import item
import ikashop
import eventManager
import datetime
import player

EVENT_OPEN_SHOP_HISTORY = "EVENT_OPEN_SHOP_HISTORY" # args: None
EVENT_SET_SHOP_HISTORY = "EVENT_SET_SHOP_HISTORY" # args | data: dict

class OfflineShopHistory(ui.ScriptWindow):
	class Log(ui.Bar):
		def __init__(self):
			ui.Bar.__init__(self)

			self.SetSize(398, 20)

			actionLabel = ui.TextLine()
			actionLabel.SetParent(self)
			actionLabel.SetPosition(5, 2)
			actionLabel.Show()
			self.actionLabel = actionLabel

			dateLabel = ui.TextLine()
			dateLabel.SetParent(self)
			dateLabel.SetPosition(300, 2)
			dateLabel.Show()
			self.dateLabel = dateLabel

		def __del__(self):
			ui.Bar.__del__(self)

		def SetActionText(self, text):
			self.actionLabel.SetText(text)

		def SetDate(self, text):
			self.dateLabel.SetText(text)

		def SetMask(self, maskWindow):
			self.SetClippingMaskWindow(maskWindow)
			self.actionLabel.SetClippingMaskWindow(maskWindow)
			self.dateLabel.SetClippingMaskWindow(maskWindow)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.LoadScript()

		self.logList = []

		eventManager.EventManager().add_observer(EVENT_OPEN_SHOP_HISTORY, self.Toggle)
		eventManager.EventManager().add_observer(EVENT_SET_SHOP_HISTORY, self.OnGetNotificationList)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.logList = []

	def LoadScript(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/PrivateShopHistory.py")

			self.mask = self.GetChild("Mask")
			self.content = self.GetChild("Content")
			self.clearButton = self.GetChild("ClearButton")
			self.titleBar = self.GetChild("TitleBar")
			self.scrollBar = self.GetChild("Scroll")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.clearButton.SAFE_SetEvent(self.ClearHistory)

			self.scrollBar.SetScrollContent(self.mask, self.content)
			self.scrollBar.SAFE_SetOnWheelEvent(self.content)

		except:
			import exception
			exception.Abort("OfflineShopHistory.LoadDialog.BindObject")

	def ClearHistory(self, is_soft=False):
		if not self.logList or len(self.logList) < 1:
			return

		for log in self.logList:
			log.Hide()

		self.logList = []

		if not is_soft:
			file_utils.DeleteFile("cache/shop_notifications_{}.json".format(player.GetName()))

	def OnGetNotificationList(self, data):
		self.ClearHistory(is_soft=True)
		for v in data:
			self.AddLog(v)

		self.__SetContentWindowHeight()
		self.scrollBar.ResizeScrollBar()
		self.scrollBar.SetStepScrollBasedOnAverageHeight(self.logList)

	def __SetContentWindowHeight(self):
		min_height = 250
		height = max(min_height, len(self.logList) * 20)
		self.content.SetHeight(height)

	def __GetItemName(self, what):
		if what == 0:
			return ""
		item.SelectItem(what)
		return item.GetItemName()

	def __ToDate(self, timestamp):
		dt = datetime.datetime.fromtimestamp(timestamp)
		formatted_time = dt.strftime("%H:%M %d-%m-%Y")
		return formatted_time

	def AddLog(self, data):
		type = data['type']
		who = data['who']
		what = data['what']
		datetime = data['datetime']
		format = data['format']

		itemname = self.__GetItemName(what)
		message = ""
		if type == ikashop.NOTIFICATION_SELLER_SELLER_SOLD_ITEM:
			price = localeInfo.NumberToMoneyString(format)
			message = localeInfo.IKASHOP_PRO_NOTIFICATION_SELLER_SOLD_ITEM.format(itemname, price)
		elif type == ikashop.NOTIFICATION_SELLER_SHOP_EXPIRED:
			message = localeInfo.IKASHOP_PRO_NOTIFICATION_SELLER_SHOP_EXPIRED
		else:
			return

		log = self.Log()
		log.SetParent(self.content)
		log.SetPosition(0, len(self.logList) * 20)
		log.SetColor(0x40000000 if len(self.logList) % 2 == 0 else 0x10ffffff)
		log.SetActionText(message)
		log.SetDate(self.__ToDate(datetime))
		log.SetMask(self.mask)
		log.Show()
		self.logList.append(log)

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def Open(self):
		ikashop.SendNotificationListRequest()
		self.Show()
		self.SetTop()

	def Close(self):
		ikashop.SendNotificationListClose()
		self.Hide()
