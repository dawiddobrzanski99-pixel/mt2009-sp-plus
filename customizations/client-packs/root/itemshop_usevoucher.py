import ui
import gamefont
import localeInfo
import itemshop_contentwindow
import net
import eventManager
import colorInfo

class ItemShopUseVoucher(itemshop_contentwindow.ItemShopContentWindow):
	def __init__(self, itemshopWnd):
		itemshop_contentwindow.ItemShopContentWindow.__init__(self, itemshopWnd.content)
		self.elements = []
		self.codeInput = None
		self.responseLabel = None

		self.__CreateContent()

		eventManager.EventManager().add_observer(eventManager.EVENT_USE_CODE_VOUCHER, self.OnResponse)

	def __del__(self):
		itemshop_contentwindow.ItemShopContentWindow.__del__(self)

	def Destroy(self):
		self.elements = None
		self.codeInput = None
		self.responseLabel = None

	def __CreateContent(self):
		slot = ui.SlotBar()
		slot.SetParent(self)
		slot.SetSize(200, 30)
		slot.SetWindowVerticalAlignCenter()
		slot.SetWindowHorizontalAlignCenter()
		slot.SetPosition(0, 0)
		slot.Show()
		self.elements.append(slot)

		codeInput = ui.EditLine()
		codeInput.SetParent(slot)
		codeInput.SetPosition(5, 5)
		codeInput.SetSize(200, 30)
		codeInput.SetFontName(gamefont.GetCurrentFontHuge())
		codeInput.SetPlaceholder(localeInfo.ITEMSHOP_USE_VOUCHER_PLACEHOLDER, fontName=gamefont.GetCurrentFontHuge())
		codeInput.SetMax(20)
		codeInput.Show()
		self.codeInput = codeInput

		btn = ui.Button()
		btn.SetParent(self)
		btn.SetWindowVerticalAlignCenter()
		btn.SetWindowHorizontalAlignCenter()
		btn.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		btn.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		btn.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		btn.SetText(localeInfo.ITEMSHOP_USE_VOUCHER)
		btn.SAFE_SetEvent(self.__OnButtonClick)
		btn.SetPosition(0, 45)
		btn.Show()
		self.elements.append(btn)

		response = ui.TextLine()
		response.SetParent(self)
		response.SetHorizontalAlignCenter()
		response.SetWindowVerticalAlignCenter()
		response.SetWindowHorizontalAlignCenter()
		response.SetPosition(0, -30)
		response.SetText("")
		response.Show()
		self.responseLabel = response

	def __OnButtonClick(self):
		code = self.codeInput.GetText()
		if len(code) < 3:
			return

		net.SendChatPacket("/itemshop use_voucher %s" % code)

	def OnResponse(self, response):
		if response == 0:
			self.SetResponseText(localeInfo.USE_VOUCHER_SUCCESS, colorInfo.POSITIVE_COLOR)
		elif response == 1:
			self.SetResponseText(localeInfo.USE_VOUCHER_NO_CODE, colorInfo.NEGATIVE_COLOR)
		elif response == 2:
			self.SetResponseText(localeInfo.USE_VOUCHER_ALREADY_USED, colorInfo.NEGATIVE_COLOR)
		elif response == 3:
			self.SetResponseText(localeInfo.USE_VOUCHER_TRY_AGAIN_LATER, colorInfo.FONT_COLOR)
		else:
			self.SetResponseText(localeInfo.USE_VOUCHER_TRY_AGAIN_LATER, colorInfo.FONT_COLOR)

	def SetResponseText(self, text, color):
		self.responseLabel.SetPackedFontColor(color)
		self.responseLabel.SetText(text)

	def Show(self):
		ui.Window.Show(self)
		self.codeInput.Clear()
		self.responseLabel.SetText("")
