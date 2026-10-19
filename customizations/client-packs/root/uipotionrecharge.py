import ui
import mouseModule
import player
import chat
import localeInfo
import mathUtils
import item
import net
import eventManager
import uiInventory

AUTOPOTION_TYPE_HP = 0
AUTOPOTION_TYPE_SP = 1

def GET_AUTOPOTION_TYPE(item_vnum):
	if item_vnum in (72723, 72724, 72725, 72726,):
		return AUTOPOTION_TYPE_HP
	elif item_vnum in (72727, 72728, 72729, 72730,):
		return AUTOPOTION_TYPE_SP
	else:
		return -1

def IS_AUTOPOTION(item_vnum):
	return GET_AUTOPOTION_TYPE(item_vnum) >= 0

EVENT_RECHARGE_ADD_AUTOPOTION_SLOT = "EVENT_RECHARGE_ADD_AUTOPOTION_SLOT" # args | inven_slot: Number
EVENT_RECHARGE_ADD_ITEM_SLOT = "EVENT_RECHARGE_ADD_ITEM_SLOT" # args | inven_slot: Number
EVENT_RECHARGE_REMOVE_ITEM = "EVENT_RECHARGE_REMOVE_ITEM" # args | inven_slot: Number

EVENT_RECHARGE_POTION_OPEN = "EVENT_RECHARGE_POTION_OPEN"
EVENT_RECHARGE_POTION_CLOSE = "EVENT_RECHARGE_POTION_CLOSE"

class PotionRechargeDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

		eventManager.EventManager().add_observer(uiInventory.EVENT_QUICK_ADD_INVENTORY_ITEM, self.__OnQuickAddInventory)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.itemToolTip = None
		self.autoPotionInventorySlot = -1
		self.potionType = -1
		self.potionMaxValue = 0
		self.potionCurValue = 0
		self.potionRechargeValue = 0
		self.itemSlotToInvenSlotDict = {}
		self.xWndStart = 0
		self.yWndStart = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.__Initialize()

	def SetItemToolTip(self, itemToolTip):
		self.itemToolTip = itemToolTip

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/potionrechargedialog.py")

			self.titleBar = self.GetChild("TitleBar")
			self.itemSlot = self.GetChild("ItemSlot")
			self.potionItemSlot = self.GetChild("PotionItemSlot")
			self.brewProgressBg = self.GetChild("BrewProgressBg")
			self.acceptButton = self.GetChild("AcceptButton")
			self.hpGauge = self.GetChild("HPGauge")
			self.spGauge = self.GetChild("SPGauge")
			self.recoveryBar = self.GetChild("RecoveryGaugeBar")
			self.rechargeLabel = self.GetChild("RechargeValue")

			self.potionItemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnSelectEmptyPotionItemSlot))
			self.potionItemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSelectPotionItemSlot))
			self.potionItemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInPotionItemSlot))
			self.potionItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))

			self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnSelectEmptyItemSlot))
			self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSelectItemSlot))
			self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItemSlot))
			self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
			self.acceptButton.SAFE_SetEvent(self.__OnAcceptButton)

			self.__RefreshWindowView(-1)
			self.SetRechargeProgress(0)

		except:
			import exception
			exception.Abort("PotionRechargeDialog.LoadDialog.BindObject")

	def __GetCurrentGauge(self):
		if self.potionType == AUTOPOTION_TYPE_SP:
			return self.spGauge
		else:
			return self.hpGauge

	def __OnSelectItemSlot(self, slot_num):
		self.__OnClearItemSlot(slot_num)

	def __OnSelectPotionItemSlot(self, slot_num):
		self.__OnClearPotionItemSlot(slot_num)

	def __OverInItemSlot(self, slot_num):
		self.__OverInItem(self.itemSlotToInvenSlotDict[slot_num])

	def __OverInPotionItemSlot(self, slot):
		self.__OverInItem(self.autoPotionInventorySlot)

	def __OverInItem(self, inven_slot):
		if self.itemToolTip:
			self.itemToolTip.ClearToolTip()
			self.itemToolTip.SetInventoryItem(inven_slot)
			self.itemToolTip.ShowToolTip()

	def __OverOutItem(self):
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()

	def __OnSelectEmptyItemSlot(self, slot_num):
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if player.SLOT_TYPE_INVENTORY != attachedSlotType:
				return

			self.__OnAddItemSlot(attachedSlotPos, slot_num)

	def __OnSelectEmptyPotionItemSlot(self, slot_num):
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if player.SLOT_TYPE_INVENTORY != attachedSlotType:
				return

			self.__OnAddPotionItemSlot(attachedSlotPos)

	def __OnClearItemSlot(self, slot_pos):
		self.itemSlot.ClearSlot(slot_pos)
		self.itemSlot.RefreshSlot()

		inven_pos = self.itemSlotToInvenSlotDict.pop(slot_pos, -1)
		if inven_pos >= 0:
			self.RefreshChargeProgress()
			eventManager.EventManager().send_event(EVENT_RECHARGE_REMOVE_ITEM, inven_pos)

	def __OnClearPotionItemSlot(self, slot_pos):
		self.potionItemSlot.ClearSlot(slot_pos)
		eventManager.EventManager().send_event(EVENT_RECHARGE_REMOVE_ITEM, self.autoPotionInventorySlot)

		self.autoPotionInventorySlot = -1
		self.__RefreshWindowView(-1)
		self.SetMainProgress(0, 0)
		self.SetRechargeProgress(0)
		self.RefreshRechargeLabel()

	def __OnQuickAddInventory(self, window, inven_pos):
		if window == "recharge_potion":
			item_vnum = player.GetItemIndex(inven_pos)
			if IS_AUTOPOTION(item_vnum):
				self.__OnAddPotionItemSlot(inven_pos)
			else:
				self.__OnAddItemSlot(inven_pos)

	def __OnAddPotionItemSlot(self, inven_slot):
		item_vnum = player.GetItemIndex(inven_slot)
		if not IS_AUTOPOTION(item_vnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.POTION_RECHARGE_WRONG_ITEM)
			return

		metinSlot = [player.GetItemMetinSocket(inven_slot, i) for i in xrange(player.METIN_SOCKET_MAX_NUM)]
		if metinSlot[0] > 0: # its activated
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.POTION_RECHARGE_WRONG_ITEM)
			return

		self.Clear()

		self.autoPotionInventorySlot = inven_slot

		self.potionItemSlot.SetItemSlot(0, item_vnum, 0)
		self.__RefreshWindowView(GET_AUTOPOTION_TYPE(item_vnum))

		self.SetMainProgress(metinSlot[2] - metinSlot[1], metinSlot[2])
		self.SetRechargeProgress(0)
		eventManager.EventManager().send_event(EVENT_RECHARGE_ADD_AUTOPOTION_SLOT, inven_slot)

	def __OnAddItemSlot(self, inven_slot, slot_pos=-1):
		for pos in self.itemSlotToInvenSlotDict.values():
			if pos == inven_slot:
				return

		if self.potionType == -1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.POTION_RECHARGE_FIRST_AUTOPOTION)
			return

		item_vnum = player.GetItemIndex(inven_slot)
		item.SelectItem(item_vnum)
		if item.GetItemType() != item.ITEM_TYPE_USE or item.GetItemSubType() != item.USE_POTION:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.POTION_RECHARGE_WRONG_ITEM)
			return

		itemWidth, itemHeight = item.GetItemSize()

		empty_slot = slot_pos
		if slot_pos < 0 or self.itemSlotToInvenSlotDict.has_key(slot_pos):
			empty_slot = self.itemSlot.FindEmptySlot(itemHeight)
		if empty_slot < 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.POTION_RECHARGE_NO_SLOTS)
			return

		rechargeValue = self.GetRechargeValueFromItemVnum(item_vnum)
		if rechargeValue < 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.POTION_RECHARGE_WRONG_ITEM)
			return

		self.itemSlotToInvenSlotDict[empty_slot] = inven_slot

		inven_item_count = player.GetItemCount(inven_slot)
		self.itemSlot.SetItemSlot(empty_slot, item_vnum, 0 if inven_item_count < 2 else inven_item_count)
		self.RefreshChargeProgress()
		eventManager.EventManager().send_event(EVENT_RECHARGE_ADD_ITEM_SLOT, inven_slot)

	def __RefreshWindowView(self, potion_type):
		self.potionType = potion_type
		if potion_type == AUTOPOTION_TYPE_HP:
			self.hpGauge.Show()
			self.spGauge.Hide()
			self.recoveryBar.SetColor(0x55ff0000)
		elif potion_type == AUTOPOTION_TYPE_SP:
			self.hpGauge.Hide()
			self.spGauge.Show()
			self.recoveryBar.SetColor(0x550000ff)
		else:
			self.hpGauge.Hide()
			self.spGauge.Hide()

	def SetMainProgress(self, current_value, max_value):
		self.potionCurValue = current_value
		self.potionMaxValue = max_value

		progress = mathUtils.GetProgressClamped01(current_value, max_value)
		real_gauge_width = 95
		potion_gauge_width = 248
		progress *= float(potion_gauge_width) / float(real_gauge_width)

		self.__GetCurrentGauge().SetPercentage(progress, 1.0)
		self.RefreshRechargeLabel()

	def GetRechargeValueFromItemVnum(self, item_vnum):
		item.SelectItem(item_vnum)
		if item.GetItemType() == item.ITEM_TYPE_USE and item.GetItemSubType() == item.USE_POTION:
			if self.potionType == AUTOPOTION_TYPE_SP:
				return item.GetValue(1)
			else:
				return item.GetValue(0)
		return 0

	def RefreshChargeProgress(self):
		recharge_value = 0
		for inven_pos in self.itemSlotToInvenSlotDict.values():
			item_vnum = player.GetItemIndex(inven_pos)
			item_count = player.GetItemCount(inven_pos)
			recharge_value += self.GetRechargeValueFromItemVnum(item_vnum) * item_count

		self.SetRechargeProgress(recharge_value)

	def SetRechargeProgress(self, value):
		max_recharge = self.potionMaxValue - self.potionCurValue
		if value > max_recharge:
			value = max_recharge

		self.potionRechargeValue = value

		max_width = 248
		recharge_progress = mathUtils.GetProgressClamped01(self.potionCurValue + value, self.potionMaxValue)
		self.recoveryBar.SetWidth(max_width * recharge_progress)
		self.RefreshRechargeLabel()

	def RefreshRechargeLabel(self):
		# current_value = localeInfo.NumberToString(self.potionCurValue)
		# max_value = localeInfo.NumberToString(self.potionMaxValue)
		percent = "%.2f%%" % (mathUtils.GetProgressClamped01(self.potionCurValue, self.potionMaxValue) * 100)

		if self.potionRechargeValue > 0:
			recharge_progress = mathUtils.GetProgressClamped01(self.potionRechargeValue, self.potionMaxValue)
			percent += " |cffd5eb4b+%.2f%%|r" % (recharge_progress * 100)
			percent += " |cffd5eb4b(+%s)|r" % localeInfo.NumberToString(self.potionRechargeValue)


		self.rechargeLabel.SetText("%s" % percent)

	def __OnAcceptButton(self):
		if self.autoPotionInventorySlot < 0:
			return

		if self.potionRechargeValue < 1:
			return

		slots = ""
		for inven_pos in self.itemSlotToInvenSlotDict.values():
			slots += str(inven_pos) + ","

		slots = slots[:-1]
		if len(slots) == 0:
			return

		net.SendChatPacket("/potion_recharge charge %d %s" % (self.autoPotionInventorySlot, slots))
		self.Clear()

	def Clear(self):
		self.__OnClearPotionItemSlot(0)
		for slot, inv_pos in self.itemSlotToInvenSlotDict.items():

			eventManager.EventManager().send_event(EVENT_RECHARGE_REMOVE_ITEM, inv_pos)
			self.itemSlot.ClearSlot(slot)
		self.itemSlot.RefreshSlot()

		self.itemSlotToInvenSlotDict = {}

	def Open(self):
		self.Clear()
		self.Show()
		eventManager.EventManager().send_event(EVENT_RECHARGE_POTION_OPEN)

		(self.xWndStart, self.yWndStart, z) = player.GetMainCharacterPosition()

	def Close(self):
		net.SendChatPacket("/potion_recharge close")
		self.Hide()
		eventManager.EventManager().send_event(EVENT_RECHARGE_POTION_CLOSE)

	def OnUpdate(self):
		USE_WINDOW_LIMIT_RANGE = 1000

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xWndStart) > USE_WINDOW_LIMIT_RANGE or abs(y - self.yWndStart) > USE_WINDOW_LIMIT_RANGE:
			self.Close()
