import ui
import app
import chr
import player
import localeInfo
import flamewindPath
import uiItemShop
import item
import mathUtils
import colorInfo
import itemshop_contentwindow
import eventManager
import constInfo
import player
import net
from _weakref import proxy

class ItemShopItemView(ui.ScriptWindow):
	class ViewState(object):
		def OnEnter(self, owner):
			pass

		def OnExit(self, owner):
			pass

		def Setup(self):
			pass

	class TimeState(ViewState):
		def __init__(self):
			self.start_time = 0
			self.end_time = 0
			self.amount_left = 0

		def CanBuy(self):
			if self.amount_left < 1:
				return False

			current_time = app.GetGlobalTimeStamp()
			if current_time < self.start_time:
				return False

			if current_time >= self.end_time:
				return False

			return True

		def OnEnter(self, owner):
			owner.progressBarBackground.Show()
			owner.progress.SetPercentage(self.amount_left, 100)

		def Setup(self, timedData):
			self.start_time = timedData["startTime"]
			self.end_time = timedData["endTime"]
			self.amount_left = min(timedData["amountLeft"], 100)

		def OnTimeUpdate(self, owner):
			current_time = app.GetGlobalTimeStamp()
			if not self.CanBuy():
				owner.buyButton.Down()
				owner.buyButton.Disable()
			else:
				owner.buyButton.Enable()
				owner.buyButton.SetUp()

			if self.amount_left < 1:
				owner.itemTime.Hide()
				owner.itemSoldOut.Show()
				return

			owner.itemTime.Show()
			if current_time < self.start_time:
				leftSec = max(0, self.start_time - current_time)
				owner.itemTime.SetText(localeInfo.ITEMSHOP_TIME_AUCTION_START % localeInfo.SecondToSmartDHMS2(leftSec))
				owner.clockIcon.Show()
				owner.clockAnimation.Hide()
			else:
				leftSec = max(0, self.end_time - current_time)
				if leftSec > 0:
					owner.itemTime.SetText(localeInfo.ITEMSHOP_TIME_AUCTION_END % localeInfo.SecondToSmartDHMS2(leftSec))
					owner.clockIcon.Hide()
					owner.clockAnimation.Show()
				else:
					owner.itemTime.SetText(localeInfo.ITEMSHOP_TIME_ITEM_EVENT_END)
					owner.clockIcon.Show()
					owner.clockAnimation.Hide()

	ITEM_MIN_HEIGHT = 61
	ITEM_HEIGHT_STEP = 32

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.tooltip = None

		self.viewState = None
		self.timedViewState = self.TimeState()

		self.itemIndex = None
		self.itemName = None
		self.itemVnum = None
		self.itemCount = None
		self.itemCurrency = None
		self.itemPrice = None
		self.minLevel = None
		self.descriptionLabels = []

		self.scrollContent = None

		self.LoadScript()

	def __del__(self):
		# import dbg
		# dbg.LogBox("shop item")
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.tooltipItem = None
		self.tooltip = None

	def SetViewState(self, state):
		if self.viewState:
			self.viewState.OnExit(self)

		self.viewState = state
		self.viewState.OnEnter(self)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = proxy(tooltipItem)

	def SetToolTip(self, tooltip):
		self.tooltip = proxy(tooltip)

	def LoadScript(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/itemshopitem.py")
			self.itemIcon = self.GetChild("ItemIcon")
			self.itemTitleLabel = self.GetChild("ItemTitle")
			self.titleBar = self.GetChild("TitleBar")

			self.itemSoldOut = self.GetChild("ItemSoldOut")
			self.itemTime = self.GetChild("ItemTime")
			self.clockIcon = self.GetChild("ClockIcon")
			self.clockAnimation = self.GetChild("ClockAnimation")
			self.progressBarBackground = self.GetChild("ProgressBarBackground")
			self.progress = self.GetChild("Progress")

			self.itemSoldOut.Hide()
			self.itemTime.Hide()
			self.progressBarBackground.Hide()

			self.buyButton = self.GetChild("BuyButton")
			self.itemSlots = [self.GetChild("ItemSlot" + str(i+1)) for i in range(3)]

			self.itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverInItemSlot)
			self.itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOutItemSlot)

			self.progress.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverInProgress)
			self.progress.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOutProgress)
			self.progressBarBackground.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverInProgress)
			self.progressBarBackground.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOutProgress)
		except:
			import exception
			exception.Abort("ItemShopItem.LoadDialog.BindObject")

	def AddTextLabel(self, parent=None):
		text = ui.TextLine()
		text.SetParent(parent if parent else self)
		text.Show()
		self.descriptionLabels.append(text)
		return text

	def AddTimedLabel(self, start_time, end_time, titleBarTextLength=0):
		text = self.AddTextLabel(self.titleBar)
		text.SetHorizontalAlignRight()
		text.SetWindowHorizontalAlignRight()
		text.SetPosition(titleBarTextLength, 4)
		text.SetPackedFontColor(colorInfo.GetColorFromColorTuple(colorInfo.ITEMSHOP_TIMED_CATEGORY_COLOR))
		text.SetBold()

		current_time = app.GetGlobalTimeStamp()
		if current_time < start_time:
			leftSec = max(0, start_time - current_time)
			text.SetText("Zaczyna się za %s  " % localeInfo.SecondToSmartDHMS2(leftSec))
		else:
			leftSec = max(0, end_time - current_time)
			text.SetText("Koniec za %s  " % localeInfo.SecondToSmartDHMS2(leftSec))

		width, height = text.GetTextSize()
		return titleBarTextLength + width

	def AddCountLabel(self, count, titleBarTextLength=0):
		text = self.AddTextLabel(self.titleBar)
		text.SetHorizontalAlignRight()
		text.SetWindowHorizontalAlignRight()
		text.SetPosition(titleBarTextLength, 4)
		text.SetText("Sztuk: %d | " % count)
		width, height = text.GetTextSize()
		return titleBarTextLength + width

	def GetPriceText(self, price, currency):
		color = ""
		if currency == uiItemShop.CURRENCY_DRAGON_COIN:
			color = "ffc948"
			# elif currency == uiItemShop.CURRENCY_DRAGON_MARK:
		else:
			color = "cfa696"

		return "|cff%s%d %s|r" % (color, price, uiItemShop.GetCurrencyShortName(currency))

	def AddPriceLabel(self, price, currency, promotion=None, titleBarTextLength=0):
		totalWidth = 4
		basePosY = 4

		if promotion:
			promotionPriceText = self.AddTextLabel(self.titleBar)
			promotionPriceText.SetHorizontalAlignRight()
			promotionPriceText.SetWindowHorizontalAlignRight()
			promotionPriceText.SetPosition(totalWidth, basePosY)
			promotionPriceText.SetText(" " + self.GetPriceText(promotion["itemPrice"], currency))
			width, height = promotionPriceText.GetTextSize()
			totalWidth += width

		priceText = self.AddTextLabel(self.titleBar)
		priceText.SetHorizontalAlignRight()
		priceText.SetWindowHorizontalAlignRight()
		priceText.SetPosition(totalWidth, basePosY)
		if promotion:
			priceText.SetStrikeOut()
			priceText.SetPackedFontColor(colorInfo.GetColorFromColorTuple(colorInfo.TITLE_RGB_EVIL_4))
			priceText.SetText(str(price))
		else:
			priceText.SetText(self.GetPriceText(price, currency))
		width, height = priceText.GetTextSize()
		totalWidth += width

		text = self.AddTextLabel(self.titleBar)
		text.SetHorizontalAlignRight()
		text.SetWindowHorizontalAlignRight()
		text.SetPosition(totalWidth, basePosY)
		text.SetText("Cena: ")
		width, height = text.GetTextSize()
		totalWidth += width

		if promotion:
			leftSec = max(0, promotion["endTime"] - app.GetGlobalTimeStamp())

			timeText = self.AddTextLabel(self.titleBar)
			timeText.SetHorizontalAlignRight()
			timeText.SetWindowHorizontalAlignRight()
			timeText.SetPosition(totalWidth, basePosY)
			timeText.SetText("Koniec promocji za %s | " % localeInfo.SecondToSmartDHMS2(leftSec, shortText=True))
			width, height = timeText.GetTextSize()
			totalWidth += width

		return totalWidth

	def SetTitleLabel(self, title):
		self.itemTitleLabel.SetText(title)

	def SetItemSlot(self):
		item.SelectItem(self.itemVnum)
		sizeX, sizeY = item.GetItemSize()
		self.SetSlot(sizeY)
		return sizeY

	def SetSlot(self, sizeY):
		for i in range(3):
			slot = self.itemSlots[i]
			if i <= (sizeY-1):
				slot.Show()
			else:
				slot.Hide()

	def SetDescription(self, description):
		descSplit = description.split("[ENTER]")
		idx = 0
		currentHeight = self.GetHeight()
		lastDescPosY = 0
		offsetY = 0
		if self.minLevel:
			text = self.AddTextLabel()
			text.SetText(localeInfo.ITEMSHOP_MIN_LEVEL % self.minLevel)
			if player.GetStatus(player.LEVEL) >= self.minLevel:
				text.SetPackedFontColor(colorInfo.POSITIVE_COLOR)
			else:
				text.SetPackedFontColor(colorInfo.NEGATIVE_COLOR)

			text.SetPosition(54, offsetY + 24)
			offsetY += 8

		for desc in descSplit:
			text = self.AddTextLabel()
			text.SetText(desc)
			lastDescPosY = offsetY + 32 + 16 * idx
			text.SetPosition(54, lastDescPosY)
			idx += 1

		if lastDescPosY > currentHeight - 16:
			currentHeight += 16 * (idx - 1)
			self.SetSize(self.GetWidth(), currentHeight)

	def ResizeView(self, itemSizeY):
		self.SetSize(self.GetWidth(), self.ITEM_MIN_HEIGHT + self.ITEM_HEIGHT_STEP * (itemSizeY-1))

	def SetItem(self, index, itemData):
		self.itemIndex = index
		self.itemVnum = itemData["itemVnum"]
		item.SelectItem(self.itemVnum)
		self.itemName = itemData["itemName"]
		self.itemCount = itemData["itemCount"]
		self.itemCurrency = itemData["currency"]
		self.itemPrice = itemData["itemPrice"]
		self.minLevel = itemData["minLevel"]

		self.SetTitleLabel(self.itemName)

		promotion = itemData["promotion"] if itemData.has_key("promotion") else None
		totalLen = 0
		totalLen += self.AddPriceLabel(self.itemPrice, self.itemCurrency, promotion, titleBarTextLength=totalLen)
		totalLen += self.AddCountLabel(self.itemCount, totalLen)


		if itemData.has_key("timed"):
			self.timedViewState.Setup(itemData["timed"])
			self.SetViewState(self.timedViewState)

		sizeY = self.SetItemSlot()
		self.ResizeView(sizeY)
		self.itemIcon.LoadImage(item.GetIconImageFileName())

		self.buyButton.SAFE_SetEvent(self.__OnBuyButtonClick)

		description = localeInfo.ITEMSHOP_NO_DESCRIPTION
		if itemData.has_key("description") and itemData["description"] != "":
			description = itemData["description"]

		if itemData.has_key("timed"):
			if itemData["timed"].has_key("accountLimit") and itemData["timed"]["accountLimit"] > 0:
				description += "[ENTER]" + localeInfo.ITEMSHOP_TIME_ACCOUNT_LIMIT % (itemData["timed"]["accountLimit"])

			description += "[ENTER] "

		self.SetDescription(description)

	def SetCustomItem(self, index, itemData):
		self.SetSlot(1)
		self.ResizeView(1)
		self.itemIcon.LoadImage(itemData["icon"])

		if itemData.has_key("endTime"):
			timeString = localeInfo.ConvertTimeStamp(itemData["endTime"])
			if index == 997: # timed event
				self.SetDescription(itemData["description"] % timeString)
			elif index == 998: # happy hour
				self.SetDescription(itemData["description"] % (itemData["value"], timeString))
				self.buyButton.SetBetterToolTip(localeInfo.OPEN_URL_INFO, self.tooltip)
		else:
			self.SetDescription(itemData["description"])
		self.SetTitleLabel(itemData["itemName"])
		# self.SetPriceLabel("")

		self.buyButton.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		self.buyButton.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		self.buyButton.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.buyButton.SetText(localeInfo.ITEMSHOP_CHECK, isBold=True)
		self.buyButton.SetTextColor(colorInfo.GetColorFromColorTuple(itemData["buttonColor"]))
		self.buyButton.SAFE_SetEvent(self.__OnCustomButtonClick, itemData["open_index"])

	def SetBuyButtonState(self, state):
		if not state:
			self.buyButton.Down()
			self.buyButton.Disable()
		else:
			self.buyButton.Enable()
			self.buyButton.SetUp()

	def CanBuyItem(self, cash, cash_mark):
		if self.itemPrice:
			if self.itemCurrency == uiItemShop.CURRENCY_DRAGON_COIN:
				if cash < self.itemPrice:
					return False
			else:
				if cash_mark < self.itemPrice:
					return False

		if self.minLevel:
			if player.GetStatus(player.LEVEL) < self.minLevel:
				return False

		return True

	def RefreshBuyButton(self, cash, cash_mark):
		self.SetBuyButtonState(self.CanBuyItem(cash, cash_mark))

	def OnPerSecondUpdate(self):
		if self.viewState:
			self.viewState.OnTimeUpdate(self)

	def SetMask(self, mask):
		for i in self.ElementDictionary:
			self.ElementDictionary[i].SetClippingMaskWindow(mask)

		for text in self.descriptionLabels:
			text.SetClippingMaskWindow(mask)

	def __OnCustomButtonClick(self, categoryIndex):
		eventManager.EventManager().send_event(uiItemShop.EVENT_OPEN_CATEGORY, categoryIndex)

	def __OnBuyButtonClick(self):
		eventManager.EventManager().send_event(uiItemShop.EVENT_BUY_ITEM, self.itemIndex)

	def __OnMouseOverInItemSlot(self):
		if self.itemVnum:
			self.tooltipItem.SetItemShopItemToolTip(self.itemVnum, self.itemPrice, self.itemCurrency)
			self.tooltipItem.ShowToolTip()

	def __OnMouseOverOutItemSlot(self):
		if self.itemVnum:
			self.tooltipItem.HideToolTip()

	def __OnMouseOverInProgress(self):
		if self.viewState == self.timedViewState:
			self.tooltip.ClearToolTip()
			self.tooltip.AppendTextLine(localeInfo.ITEMSHOP_TIME_PROGRESS_TOOLTIP % self.timedViewState.amount_left)
			self.tooltip.ShowToolTip()

	def __OnMouseOverOutProgress(self):
		self.tooltip.HideToolTip()

class ItemShopShopContent(itemshop_contentwindow.ItemShopContentWindow):
	SCROLL_MASK_VIEW_POSITION_X = 1
	SCROLL_MASK_VIEW_POSITION_Y = 20
	PAGE_SIZE = 30

	def __init__(self, itemshopWnd, itemToolTip, tooltip):
		itemshop_contentwindow.ItemShopContentWindow.__init__(self, itemshopWnd.content)
		self.minWidth = itemshopWnd.content.GetWidth()
		self.minHeight = itemshopWnd.content.GetHeight()
		self.maskWindow = None
		self.itemShopWnd = proxy(itemshopWnd)
		self.SetItemToolTip(itemToolTip)
		self.SetToolTip(tooltip)
		self.__CreateShopContent()

	def __del__(self):
		# import dbg
		# dbg.LogBox("shop window")
		itemshop_contentwindow.ItemShopContentWindow.__del__(self)

	def __CreateShopContent(self):
		try:
			maskWindow = ui.Window()
			maskWindow.SetParent(self)
			maskWindow.SetSize(self.minWidth - self.SCROLL_MASK_VIEW_POSITION_X, self.minHeight - self.SCROLL_MASK_VIEW_POSITION_Y - 28)
			maskWindow.SetPosition(self.SCROLL_MASK_VIEW_POSITION_X, self.SCROLL_MASK_VIEW_POSITION_Y)
			maskWindow.Show()
			self.maskWindow = maskWindow

			scrollContent = ui.Window()
			scrollContent.SetParent(self.maskWindow)
			scrollContent.SetSize(self.maskWindow.GetWidth(), self.maskWindow.GetHeight())
			scrollContent.SetPosition(0, 0)
			scrollContent.Show()
			self.scrollContent = scrollContent

			scroll = ui.ScrollBar()
			scroll.SetParent(self)
			scroll.SetScrollBarSize(maskWindow.GetHeight())
			scroll.SetWindowHorizontalAlignRight()
			scroll.SetPosition(22, 20)
			scroll.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
			scroll.Show()
			scroll.SAFE_SetOnWheelEvent(self)
			self.scrollBar = scroll

			inputBar = ui.SlotBar()
			inputBar.SetParent(self)
			inputBar.SetWindowHorizontalAlignRight()
			inputBar.SetSize(200, 16)
			inputBar.SetPosition(202, 2)
			inputBar.Show()
			self.inputBar = inputBar

			searchInput = ui.EditLine()
			searchInput.SetParent(inputBar)
			searchInput.SetLimitWidth(200)
			searchInput.SetMax(24)
			searchInput.SetSize(200, 20)
			searchInput.SetPosition(2, 2)
			searchInput.SetPlaceholder(localeInfo.ITEMSHOP_SEARCH_PLACEHOLDER)
			searchInput.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
			searchInput.Show()
			self.searchInput = searchInput

			prevButton = ui.Button()
			prevButton.SetParent(self)
			prevButton.SetUpVisual(flamewindPath.GetPublic("big_button_01"))
			prevButton.SetOverVisual(flamewindPath.GetPublic("big_button_02"))
			prevButton.SetDownVisual(flamewindPath.GetPublic("big_button_03"))
			prevButton.SetText("Poprzednia")
			prevButton.SetPosition(25, self.minHeight - 26)
			prevButton.SAFE_SetEvent(self.__OnPreviousPage)
			prevButton.Show()
			self.prevButton = prevButton

			nextButton = ui.Button()
			nextButton.SetParent(self)
			nextButton.SetUpVisual(flamewindPath.GetPublic("big_button_01"))
			nextButton.SetOverVisual(flamewindPath.GetPublic("big_button_02"))
			nextButton.SetDownVisual(flamewindPath.GetPublic("big_button_03"))
			nextButton.SetText("Nastepna")
			nextButton.SetPosition(310, self.minHeight - 26)
			nextButton.SAFE_SetEvent(self.__OnNextPage)
			nextButton.Show()
			self.nextButton = nextButton

			pageText = ui.TextLine()
			pageText.SetParent(self)
			pageText.SetPosition(215, self.minHeight - 20)
			pageText.SetHorizontalAlignCenter()
			pageText.Show()
			self.pageText = pageText

			self.currentItemList = []
			self.currentSortType = uiItemShop.ITEMSHOP_SORT_TYPE_VNUM
			self.currentPage = 0
			self.itemViewDict = {}

		except:
			import exception
			exception.Abort("ItemShopShopContent.__CreateShopContent")

	def Destroy(self):
		self.tooltipItem = None
		self.tooltip = None

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetToolTip(self, tooltip):
		self.tooltip = tooltip

	def __OnValueUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchInput)
		itemSearch = self.searchInput.GetText()
		self.itemShopWnd.ShowItemsByInput(itemSearch)

	def ShowItemList(self, itemList, sortType=0, page=0):
		for itemView in self.itemViewDict.itervalues():
			itemView.Hide()

		def sort_by_vnum(itemShopIndex):
			itemData = constInfo.ITEMSHOP_DATA.get(itemShopIndex, {})
			return itemData.get("itemVnum", 0)

		def sort_by_price(itemShopIndex):
			itemData = constInfo.ITEMSHOP_DATA.get(itemShopIndex, {})
			return itemData.get("itemPrice", 0)

		visibleItems = []
		for itemShopIndex in itemList:
			if not constInfo.ITEMSHOP_DATA.has_key(itemShopIndex):
				continue
			itemData = constInfo.ITEMSHOP_DATA[itemShopIndex]
			if itemData.has_key("itemVnum") and not self.__CanViewItem(itemData["itemVnum"]):
				continue
			visibleItems.append(itemShopIndex)

		sortKey = sort_by_price if sortType == uiItemShop.ITEMSHOP_SORT_TYPE_PRICE else sort_by_vnum
		self.currentItemList = sorted(visibleItems, key=sortKey)
		self.currentSortType = sortType
		pageCount = max(1, (len(self.currentItemList) + self.PAGE_SIZE - 1) / self.PAGE_SIZE)
		self.currentPage = max(0, min(page, pageCount - 1))

		pageStart = self.currentPage * self.PAGE_SIZE
		pageItems = self.currentItemList[pageStart:pageStart + self.PAGE_SIZE]
		totalHeight = 0
		for itemShopIndex in pageItems:
			if not self.itemViewDict.has_key(itemShopIndex):
				self.CreateItem(itemShopIndex, constInfo.ITEMSHOP_DATA[itemShopIndex])
			if not self.itemViewDict.has_key(itemShopIndex):
				continue
			itemView = self.itemViewDict[itemShopIndex]
			itemView.SetPosition(0, totalHeight)
			totalHeight += itemView.GetHeight()
			itemView.Show()

		self.pageText.SetText("Strona %d / %d  (%d)" % (self.currentPage + 1, pageCount, len(self.currentItemList)))
		if self.currentPage > 0:
			self.prevButton.Enable()
		else:
			self.prevButton.Disable()
		if self.currentPage + 1 < pageCount:
			self.nextButton.Enable()
		else:
			self.nextButton.Disable()

		self.ResizeContent(totalHeight)
		self.Show()

	def __OnPreviousPage(self):
		if self.currentPage > 0:
			self.ShowItemList(self.currentItemList, self.currentSortType, self.currentPage - 1)

	def __OnNextPage(self):
		pageCount = max(1, (len(self.currentItemList) + self.PAGE_SIZE - 1) / self.PAGE_SIZE)
		if self.currentPage + 1 < pageCount:
			self.ShowItemList(self.currentItemList, self.currentSortType, self.currentPage + 1)

	def ResizeScrollbar(self, itemListTotalHeight):
		progress = 1
		if itemListTotalHeight > 0:
			progress = min(float(self.maskWindow.GetHeight()) / itemListTotalHeight, 1)
		self.scrollBar.SetMiddleBarSize(progress) # 0 - 1
		self.scrollBar.SetPos(0)

	def ResizeContent(self, itemListTotalHeight):
		self.scrollContent.SetSize(self.maskWindow.GetWidth(), itemListTotalHeight)
		self.ResizeScrollbar(itemListTotalHeight)
		self.scrollContent.SetPosition(0, 0)

	def __OnScroll(self):
		startPos = 0

		maskWindowHeight = self.maskWindow.GetHeight()
		scrollContentHeight = self.scrollContent.GetHeight()
		endPos = 0
		if maskWindowHeight < scrollContentHeight:
			endPos = maskWindowHeight - scrollContentHeight
		v = mathUtils.GetLerp(startPos, endPos, self.scrollBar.GetPos())

		self.scrollContent.SetPosition(0, v)

	def __CanViewItem(self, itemVnum):
		item.SelectItem(itemVnum)
		ANTI_FLAG_DICT = {
			0: item.ITEM_ANTIFLAG_WARRIOR,
			1: item.ITEM_ANTIFLAG_ASSASSIN,
			2: item.ITEM_ANTIFLAG_SURA,
			3: item.ITEM_ANTIFLAG_SHAMAN,
		}

		race = player.GetRace()
		job = chr.RaceToJob(race)
		if not ANTI_FLAG_DICT.has_key(job):
			return False

		if item.IsAntiFlag(ANTI_FLAG_DICT[job]):
			return False

		sex = chr.RaceToSex(race)

		MALE = 1
		FEMALE = 0

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == MALE:
			return False

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == FEMALE:
			return False

		return True

	def CreateItem(self, index, itemData):
		if itemData.has_key("itemVnum") and not self.__CanViewItem(itemData["itemVnum"]):
			return False

		itemView = ItemShopItemView()
		itemView.SetParent(self.scrollContent)
		itemView.SetItemToolTip(self.tooltipItem)
		itemView.SetToolTip(self.tooltip)
		if itemData.has_key("custom"):
			itemView.SetCustomItem(index, itemData)
		else:
			itemView.SetItem(index, itemData)
		itemView.SetMask(self.maskWindow)
		itemView.Hide()
		self.itemViewDict[index] = itemView
		return True

	def UpdateItem(self, index, itemData):
		if not self.itemViewDict.has_key(index):
			return

		itemView = self.itemViewDict[index]
		itemView.SetItem(index, itemData)

	def RefreshBuyButtons(self, cash, cash_mark):
		for i in self.itemViewDict:
			self.itemViewDict[i].RefreshBuyButton(cash, cash_mark)

	def OnPerSecondUpdate(self):
		for item in self.itemViewDict.values():
			if item.IsShow():
				item.OnPerSecondUpdate()
