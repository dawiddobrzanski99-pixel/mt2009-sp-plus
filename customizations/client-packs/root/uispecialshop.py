import special_flags
import ui
import localeInfo
import shop
import colorInfo
import player
import net
import wndMgr
import mouseModule
import chat
import item
import uiToolTip
import utils
import uiReputation

class SpecialShopWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.xShopStart = 0
		self.yShopStart = 0
		self.currentViewedSlot = -1
		self.itemToolTip = None
		self.shopItemDict = {}
		self.cellToShopItemDict = {}
		self.fraction = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.__Initialize()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/specialshopwindow.py")

			self.titleBar = self.GetChild("TitleBar")
			self.itemSlot = self.GetChild("ItemSlot")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

			self.itemSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.itemSlot.SAFE_SetButtonEvent("LEFT", "EXIST", self.__SelectItemSlot)
			self.itemSlot.SAFE_SetButtonEvent("RIGHT", "EXIST", self.__SelectItemSlot)
			self.itemSlot.SAFE_SetButtonEvent("LEFT", "EMPTY", self.__SelectEmptySlot)

			self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
			self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))

			self.itemToolTip = uiToolTip.ItemToolTip()

		except:
			import exception
			exception.Abort("SpecialShopWindow.LoadDialog.BindObject")

	def __IsLimit(self, vnum):
		limits = self.shopItemDict[vnum]["limits"]
		for limit in limits:
			limitType = limit[0]
			limitValue = limit[1]

			if limitType == shop.SPECIAL_SHOP_LIMIT_LEVEL:
				if player.GetStatus(player.LEVEL) < limitValue:
					return True

			if limitType == shop.SPECIAL_SHOP_LIMIT_REPUTATION:
				if special_flags.GetReputation(self.fraction) < limitValue:
					return True

		return False

	def __AppendLimitToolTip(self, vnum):
		if not self.itemToolTip:
			return

		limits = self.shopItemDict[vnum]["limits"]

		if len(limits) > 0:
			self.itemToolTip.AppendSpace(5)
			self.itemToolTip.AppendHorizontalLine()

		for limit in limits:
			limitType = limit[0]
			limitValue = limit[1]

			if limitType == shop.SPECIAL_SHOP_LIMIT_LEVEL:
				isLimit = player.GetStatus(player.LEVEL) < limitValue
				self.itemToolTip.AppendTextLine(localeInfo.SPECIAL_SHOP_LIMIT_LEVEL % limitValue, colorInfo.NEGATIVE_COLOR if isLimit else colorInfo.POSITIVE_COLOR)

			if limitType == shop.SPECIAL_SHOP_LIMIT_REPUTATION:
				isLimit = special_flags.GetReputation(self.fraction) < limitValue
				self.itemToolTip.AppendTextLine(localeInfo.SPECIAL_SHOP_LIMIT_REPUTATION % uiReputation.GET_RANK_NAME_BY_TOTAL_VALUE(limitValue), colorInfo.NEGATIVE_COLOR if isLimit else colorInfo.POSITIVE_COLOR)

			if limitType == shop.SPECIAL_SHOP_LIMIT_BUY_PER_TIME:
				self.itemToolTip.AppendTextLine(localeInfo.SPECIAL_SHOP_LIMIT_TIME % localeInfo.SecondToSmartDHMS(limitValue))

			if limitType == shop.SPECIAL_SHOP_LIMIT_ACCOUNT:
				self.itemToolTip.AppendTextLine(localeInfo.SPECIAL_SHOP_ACCOUNT_LIMIT % limitValue)

	def __AppendItemsToolTip(self, vnum):
		if not self.itemToolTip:
			return

		reqItems = self.shopItemDict[vnum]["reqItems"]

		if len(reqItems) < 1:
			return

		self.itemToolTip.AppendSpace(5)
		self.itemToolTip.AppendTextLine(localeInfo.SPECIAL_SHOP_REQ_ITEMS, isBold=True)

		column_block = ui.ColumnBlock(2 if len(reqItems) > 1 else 1)
		i = 0
		for reqItem in reqItems:
			itemVnum = reqItem[0]
			count = reqItem[1]

			item.SelectItem(itemVnum)
			countInInventory = utils.CountItemCountInInventory(itemVnum)
			hasEnoughItems = countInInventory >= count

			itemInfo = uiToolTip.ToolTip(isNoBackground=True)
			itemInfo.followFlag = False
			itemInfo.AppendImage(item.GetIconImageFileName())
			itemInfo.AppendSpace(1)

			itemName = ("%dx " + item.GetItemName() + " (%d na %d)") % (count, countInInventory, count)
			itemInfo.AppendTextLine(itemName, colorInfo.POSITIVE_COLOR if hasEnoughItems else colorInfo.NEGATIVE_COLOR)
			itemInfo.ShowToolTip()

			column_block.AddItem(i % 2, itemInfo)
			i += 1
		column_block.Show()
		self.itemToolTip.AppendColumnBlock(column_block)

	def __OverInItem(self, slotIndex):
		if self.itemToolTip:
			vnum = self.cellToShopItemDict[slotIndex]
			self.currentViewedSlot = slotIndex

			itemData = self.shopItemDict[vnum]

			self.itemToolTip.ClearToolTip()

			attrSlot = [(0, 0,) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
			if itemData["rarePct"] > 0:
				attrSlot[0] = (991, itemData["rarePct"],)
			self.itemToolTip.SetRawItem(itemData["itemVnum"], None, attrSlot, False)

			self.__AppendLimitToolTip(vnum)

			price = itemData["price"]
			priceType = itemData["priceType"]
			if price > 0:
				self.itemToolTip.AppendSpace(5)
				self.itemToolTip.AppendHorizontalLine()
				if priceType == shop.SPECIAL_SHOP_PRICE_GOLD:
					self.itemToolTip.AppendTextLine(localeInfo.TOOLTIP_BUYPRICE % localeInfo.NumberToMoneyString(price))
				elif priceType == shop.SPECIAL_SHOP_PRICE_REPUTATION:
					self.itemToolTip.AppendTextLine(localeInfo.TOOLTIP_BUYPRICE_REPUTATION % localeInfo.NumberToString(price))

			self.__AppendItemsToolTip(vnum)

			self.itemToolTip.ShowToolTip()

	def __OverOutItem(self):
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()
		self.currentViewedSlot = -1

	def __SelectItemSlot(self, slotIndex):
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			mouseModule.mouseController.DeattachObject()
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL_ITEM_HERE)
			return

		self.__BuyItem(slotIndex)

	def __SelectEmptySlot(self, slotIndex):
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			mouseModule.mouseController.DeattachObject()
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_SELL_ITEM_HERE)

	def __BuyItem(self, slotIndex):
		net.SendChatPacket("/special_shop buy %d" % self.cellToShopItemDict[slotIndex])

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __GetSortedItems(self):
		vnums = self.shopItemDict.keys()

		def sort_key(x):
			item_vnum = self.shopItemDict[x]["itemVnum"]
			type_2_value = next((limit[1] for limit in self.shopItemDict[x]["limits"] if limit[0] == 2), float('inf'))
			has_type_2 = any(limit[0] == 2 for limit in self.shopItemDict[x]["limits"])

			return (has_type_2, type_2_value, item_vnum)

		sorted_vnums = sorted(vnums, key=sort_key)
		return sorted_vnums

	def __PrepareShop(self):
		sorted_vnums = self.__GetSortedItems()
		for vnum in sorted_vnums:
			itemData = self.shopItemDict[vnum]
			item.SelectItem(itemData["itemVnum"])
			emptySlot = self.itemSlot.FindEmptySlot(item.GetItemSize()[1])
			if emptySlot >= 0:
				self.itemSlot.SetItemSlot(emptySlot, itemData["itemVnum"], 0 if itemData["count"] < 2 else itemData["count"])

				if self.__IsLimit(vnum):
					color = (1.0, 0.0, 0.0, 0.3)
					self.itemSlot.SetSlotMaskColor(emptySlot, color)

				self.cellToShopItemDict[emptySlot] = vnum

	def Close(self):
		net.SendChatPacket("/special_shop close")
		self.SoftClose()

	def SoftClose(self):
		self.Hide()
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()

	def Open(self):
		self.Show()
		self.SetTop()
		self.__PrepareShop()
		(self.xShopStart, self.yShopStart, z) = player.GetMainCharacterPosition()

	def AddItem(self, vnum, itemDict):
		self.shopItemDict[vnum] = itemDict

	def OnBuy(self, vnum): # binary call
		if self.cellToShopItemDict[self.currentViewedSlot] == vnum:
			self.__OverInItem(self.currentViewedSlot)

	def SetFraction(self, fraction):
		self.fraction = fraction

	def Clear(self):
		self.shopItemDict = {}
		self.cellToShopItemDict = {}
		for i in range(shop.SHOP_NPC_SLOT_COUNT):
			self.itemSlot.ClearSlot(i)

	def OnUpdate(self):
		USE_SHOP_LIMIT_RANGE = 1000
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xShopStart) > USE_SHOP_LIMIT_RANGE or abs(y - self.yShopStart) > USE_SHOP_LIMIT_RANGE:
			self.Close()
