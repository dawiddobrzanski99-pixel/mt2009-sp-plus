import player
import exchange
import net
import localeInfo
import chat
import item

import ui
import mouseModule
import uiPickMoney
import uiMoneyShortcuts
import wndMgr
import app
import uiInventory
import eventManager

EVENT_OPEN_EXCHANGE = "EVENT_OPEN_EXCHANGE" # args |
EVENT_ADD_ITEM_TO_EXCHANGE = "EVENT_ADD_ITEM_TO_EXCHANGE" # args | window_type: number, cell: number
EVENT_CLOSE_EXCHANGE = "EVENT_CLOSE_EXCHANGE" # args |

###################################################################################################
## Exchange
class ExchangeDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.TitleName = 0
		self.tooltipItem = 0
		self.xStart = 0
		self.yStart = 0

		eventManager.EventManager().add_observer(uiInventory.EVENT_QUICK_ADD_INVENTORY_ITEM,self.OnQuickAddInventoryItem)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadDialog(self):
		PythonScriptLoader = ui.PythonScriptLoader()
		if app.ENABLE_CHEQUE_SYSTEM:
			PythonScriptLoader.LoadScriptFile(self, "UIScript/exchangedialog_cheque.py")
		else:
			PythonScriptLoader.LoadScriptFile(self, "UIScript/exchangedialog.py")

		## Owner
		self.OwnerSlot = self.GetChild("Owner_Slot")
		self.OwnerSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectOwnerEmptySlot))
		self.OwnerSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectOwnerItemSlot))
		self.OwnerSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInOwnerItem))
		self.OwnerSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.OwnerMoney = self.GetChild("Owner_Money_Value")
		self.OwnerAcceptLight = self.GetChild("Owner_Accept_Light")
		self.OwnerAcceptLight.Disable()
		self.OwnerMoneyButton = self.GetChild("Owner_Money")
		self.OwnerMoneyButton.SetEvent(ui.__mem_func__(self.OpenPickMoneyDialog))

		if app.ENABLE_CHEQUE_SYSTEM:
			self.OwnerCheque = self.GetChild("Owner_Cheque_Value")
			self.OwnerChequeButton = self.GetChild("Owner_Cheque")
			self.OwnerChequeButton.SetEvent(ui.__mem_func__(self.OpenPickChequeDialog))

		## Target
		self.TargetSlot = self.GetChild("Target_Slot")
		self.TargetSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInTargetItem))
		self.TargetSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.TargetMoney = self.GetChild("Target_Money_Value")
		self.TargetAcceptLight = self.GetChild("Target_Accept_Light")
		self.TargetAcceptLight.Disable()

		if app.ENABLE_CHEQUE_SYSTEM:
			self.TargetCheque = self.GetChild("Target_Cheque_Value")

		## PickMoneyDialog
		dlgPickMoney = uiMoneyShortcuts.ExchangeMoneyDialog()
		dlgPickMoney.LoadDialog()
		dlgPickMoney.SetAcceptEvent(ui.__mem_func__(self.OnPickMoney))
		dlgPickMoney.SetTitleName(localeInfo.EXCHANGE_MONEY)
		# MT2009_PLUS_YANG_LIMITS_V1 (Autor: Digi Rasta, nowy-system 0.26.0): up to 10 bn in one trade -
		# the digits of player.EXCHANGE_GOLD_MAX (new exe; an older exe keeps the old 8 digits).
		dlgPickMoney.SetMax(len(str(getattr(player, "EXCHANGE_GOLD_MAX", 99999999))))
		if app.ENABLE_CHEQUE_SYSTEM:
			dlgPickMoney.SetMaxCheque(3)
		dlgPickMoney.Hide()
		self.dlgPickMoney = dlgPickMoney

		## Button
		self.AcceptButton = self.GetChild("Owner_Accept_Button")
		self.AcceptButton.SetToggleDownEvent(ui.__mem_func__(self.AcceptExchange))

		self.TitleName = self.GetChild("TitleName")
		self.GetChild("TitleBar").SetCloseEvent(net.SendExchangeExitPacket)

	@ui.WindowDestroy
	def Destroy(self):
		print "---------------------------------------------------------------------------- DESTROY EXCHANGE"
		self.ClearDictionary()
		if self.dlgPickMoney:
			self.dlgPickMoney.Destroy()
			self.dlgPickMoney = 0
		self.OwnerSlot = 0
		self.OwnerMoney = 0
		self.OwnerAcceptLight = 0
		self.OwnerMoneyButton = 0
		self.TargetSlot = 0
		self.TargetMoney = 0
		self.TargetAcceptLight = 0
		self.TitleName = 0
		self.AcceptButton = 0
		self.tooltipItem = 0

	def OpenDialog(self):
		if app.ENABLE_LEVEL_IN_TRADE:
			self.TitleName.SetText(localeInfo.EXCHANGE_TITLE_LEVEL % (exchange.GetNameFromTarget(), exchange.GetLevelFromTarget()))
		else:
			self.TitleName.SetText(localeInfo.EXCHANGE_TITLE % (exchange.GetNameFromTarget()))
		self.AcceptButton.Enable()
		self.AcceptButton.SetUp()
		self.Show()

		eventManager.EventManager().send_event(EVENT_OPEN_EXCHANGE)

		(self.xStart, self.yStart, z) = player.GetMainCharacterPosition()

	def CloseDialog(self):
		wndMgr.OnceIgnoreMouseLeftButtonUpEvent()

		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()

		eventManager.EventManager().send_event(EVENT_CLOSE_EXCHANGE)

		self.dlgPickMoney.Close()
		self.Hide()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def OpenPickMoneyDialog(self):

		if exchange.GetElkFromSelf() > 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EXCHANGE_CANT_EDIT_MONEY)
			return

		if app.ENABLE_CHEQUE_SYSTEM:
			self.dlgPickMoney.Open(player.GetElk(),player.GetCheque())
			self.dlgPickMoney.SetFocus(0)
		else:
			self.dlgPickMoney.Open(player.GetElk())

	if app.ENABLE_CHEQUE_SYSTEM:
		def OpenPickChequeDialog(self):
			if exchange.GetChequeFromSelf() > 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EXCHANGE_CANT_EDIT_MONEY)
				return
			self.dlgPickMoney.Open(player.GetElk(),player.GetCheque())
			self.dlgPickMoney.SetFocus(1)

		def OnPickMoney(self, money, cheque):
			if exchange.GetChequeFromSelf() <=0:
				net.SendExchangeChequeAddPacket(cheque)
			if exchange.GetElkFromSelf() <= 0:
				net.SendExchangeElkAddPacket(money)
	else:
		def OnPickMoney(self, money):
			# MT2009_PLUS_YANG_LIMITS_V1: never more than one trade carries (the server refuses it anyway).
			money = min(money, getattr(player, "EXCHANGE_GOLD_MAX", 99999999))
			net.SendExchangeElkAddPacket(money)

	def AcceptExchange(self):
		net.SendExchangeAcceptPacket()
		self.AcceptButton.Disable()

	def SelectOwnerEmptySlot(self, SlotIndex):

		if False == mouseModule.mouseController.isAttached():
			return

		if mouseModule.mouseController.IsAttachedMoney():
			net.SendExchangeElkAddPacket(mouseModule.mouseController.GetAttachedMoneyAmount())
			if app.ENABLE_CHEQUE_SYSTEM:
				net.SendExchangeChequeAddPacket(mouseModule.mouseController.GetAttachedMoneyAmount())
		else:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			if (player.SLOT_TYPE_INVENTORY == attachedSlotType
				or player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedSlotType):

				attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)
				SrcSlotNumber = mouseModule.mouseController.GetAttachedSlotNumber()
				DstSlotNumber = SlotIndex

				self.AddToExchange(attachedInvenType, SrcSlotNumber, DstSlotNumber)

		mouseModule.mouseController.DeattachObject()

	def OnQuickAddInventoryItem(self, type, slotNumber):
		if type != "exchange":
			return

		itemVnum = player.GetItemIndex(slotNumber)
		if itemVnum > 0:
			item.SelectItem(itemVnum)
			(itemWidth, itemHeight) = item.GetItemSize()

			freeSlot = self.OwnerSlot.FindEmptySlot(itemHeight)
			if freeSlot >= 0:
				self.AddToExchange(player.INVENTORY, slotNumber, freeSlot)

	def AddToExchange(self, window_type, sourceSlotNumber, destSlotNumber):
		itemID = player.GetItemIndex(window_type, sourceSlotNumber)
		item.SelectItem(itemID)

		if item.IsAntiFlag(item.ANTIFLAG_GIVE):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.EXCHANGE_CANNOT_GIVE)
			mouseModule.mouseController.DeattachObject()
			return

		net.SendExchangeItemAddPacket(window_type, sourceSlotNumber, destSlotNumber)

	def SelectOwnerItemSlot(self, SlotIndex):
		if player.ITEM_MONEY == mouseModule.mouseController.GetAttachedItemIndex():
			net.SendExchangeElkAddPacket(mouseModule.mouseController.GetAttachedItemCount())
			if app.ENABLE_CHEQUE_SYSTEM:
				net.SendExchangeChequeAddPacket(mouseModule.mouseController.GetAttachedChequeAmount())

	def RefreshOwnerSlot(self):
		for i in xrange(exchange.EXCHANGE_ITEM_MAX_NUM):
			itemIndex = exchange.GetItemVnumFromSelf(i)
			itemCount = exchange.GetItemCountFromSelf(i)
			if 1 == itemCount:
				itemCount = 0

			socket = tuple(exchange.GetItemMetinSocketFromSelf(i, j) for j in range(player.METIN_SOCKET_MAX_NUM))
			self.OwnerSlot.SetItemSlot(i, itemIndex, itemCount, socket=socket)
		self.OwnerSlot.RefreshSlot()

	def RefreshTargetSlot(self):
		for i in xrange(exchange.EXCHANGE_ITEM_MAX_NUM):
			itemIndex = exchange.GetItemVnumFromTarget(i)
			itemCount = exchange.GetItemCountFromTarget(i)
			if 1 == itemCount:
				itemCount = 0

			socket = tuple(exchange.GetItemMetinSocketFromTarget(i, j) for j in range(player.METIN_SOCKET_MAX_NUM))
			self.TargetSlot.SetItemSlot(i, itemIndex, itemCount, socket=socket)
		self.TargetSlot.RefreshSlot()

	def Refresh(self):

		self.RefreshOwnerSlot()
		self.RefreshTargetSlot()

		if app.ENABLE_CHEQUE_SYSTEM:
			self.OwnerMoney.SetText(localeInfo.NumberToGoldNotText(exchange.GetElkFromSelf()))
			self.TargetMoney.SetText(localeInfo.NumberToGoldNotText(exchange.GetElkFromTarget()))

			self.OwnerCheque.SetText(str(exchange.GetChequeFromSelf()))
			self.TargetCheque.SetText(str(exchange.GetChequeFromTarget()))
		else:
			self.OwnerMoney.SetText(localeInfo.NumberToString(exchange.GetElkFromSelf()))
			self.TargetMoney.SetText(localeInfo.NumberToString(exchange.GetElkFromTarget()))

		if True == exchange.GetAcceptFromSelf():
			self.OwnerAcceptLight.Down()
		else:
			self.AcceptButton.Enable()
			self.AcceptButton.SetUp()
			self.OwnerAcceptLight.SetUp()

		if True == exchange.GetAcceptFromTarget():
			self.TargetAcceptLight.Down()
		else:
			self.TargetAcceptLight.SetUp()

	def OverInOwnerItem(self, slotIndex):

		if 0 != self.tooltipItem:
			self.tooltipItem.SetExchangeOwnerItem(slotIndex)

	def OverInTargetItem(self, slotIndex):

		if 0 != self.tooltipItem:
			self.tooltipItem.SetExchangeTargetItem(slotIndex)

	def OverOutItem(self):

		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnTop(self):
		self.tooltipItem.SetTop()

	def OnUpdate(self):

		USE_EXCHANGE_LIMIT_RANGE = 1000

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xStart) > USE_EXCHANGE_LIMIT_RANGE or abs(y - self.yStart) > USE_EXCHANGE_LIMIT_RANGE:
			(self.xStart, self.yStart, z) = player.GetMainCharacterPosition()
			net.SendExchangeExitPacket()
