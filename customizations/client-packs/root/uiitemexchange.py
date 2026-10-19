import localeInfo
import chat
import ui
import item
import player
import math
import eventManager
import uiInventory
import mouseModule
import net
from _weakref import proxy

SOUL_STONE_EXCHANGE = 1
SKILLBOOK_EXCHANGE = 2
REFINEITEM_EXCHANGE = 3

EVENT_ADD_ITEM_TO_ITEM_EXCHANGE = "EVENT_ADD_ITEM_TO_ITEM_EXCHANGE" # args | inven_slot: number
EVENT_REMOVE_ITEM_EXCHANGE = "EVENT_REMOVE_ITEM_EXCHANGE" # args | inven_slot: number
EVENT_ITEM_EXCHANGE_OPEN = "EVENT_ITEM_EXCHANGE_OPEN" # args |
EVENT_ITEM_EXCHANGE_CLOSE = "EVENT_ITEM_EXCHANGE_CLOSE" # args |

class ExchangeItemDialog(ui.ScriptWindow):
	WINDOW_WIDTH = 222
	WINDOW_HEIGHT = 184
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

		eventManager.EventManager().add_observer(uiInventory.EVENT_QUICK_ADD_INVENTORY_ITEM, self.__OnQuickAddInventoryItem)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.invenItemSlots = []
		self.resultVnum = 0
		self.chance = 0
		self.costPerResultItem = 0
		self.exchangeVnum = 0
		self.xWndStart = 0
		self.yWndStart = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()

	def SetItemToolTip(self, itemToolTip):
		self.itemToolTip = proxy(itemToolTip)

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/exchangeitemsdialog.py")

			self.board = self.GetChild("Board")
			self.titleBar = self.GetChild("TitleBar")
			self.itemSlot = self.GetChild("ItemSlot")
			self.resultItemSlot = self.GetChild("ResultItemSlot")
			self.priceLabel = self.GetChild("PriceLabel")
			self.chanceLabel = self.GetChild("ChanceLabel")
			self.acceptButton = self.GetChild("AcceptButton")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

			self.acceptButton.SAFE_SetEvent(self.__OnButtonClick)

			self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnSelectEmptySlot))
			self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__SelectItemSlot))
			self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
			self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))

			self.resultItemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInResultItem))
			self.resultItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))

		except:
			import exception
			exception.Abort("ExchangeItemDialog.LoadDialog.BindObject")

	def __SetPrice(self, cost):
		self.priceLabel.SetText(localeInfo.NumberToMoneyString(cost))

	def __GetItemGrade(self, item_vnum):
		return int(item_vnum/100) - 280

	def __CheckItem(self, inven_pos):
		item_vnum = player.GetItemIndex(inven_pos)
		item.SelectItem(item_vnum)
		if self.exchangeVnum == SOUL_STONE_EXCHANGE:
			if item.GetItemType() != item.ITEM_TYPE_METIN:
				return False

			if self.__GetItemGrade(item_vnum) > 3:
				return False
		elif self.exchangeVnum == SKILLBOOK_EXCHANGE:
			if item.GetItemType() != item.ITEM_TYPE_SKILLBOOK:
				return False
		elif self.exchangeVnum == REFINEITEM_EXCHANGE:
			if not (item_vnum >= 30000 and item_vnum <= 30092 or
			item_vnum >= 30192 and item_vnum <= 30199 or
			item_vnum >= 30343 and item_vnum <= 30359 or
			item_vnum == 30367):
				return False
		else:
			return False

		return True

	def __ResizeItemSlot(self):
		slot_count = len(self.invenItemSlots)
		need_rows = math.ceil(float(slot_count)/6)
		if need_rows < 1:
			need_rows = 1

		if need_rows != self.itemSlot.y_height:
			self.itemSlot.ArrangeSlot(0, 6, need_rows, 32, 32, 0, 0)
			self.itemSlot.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub")
			self.itemSlot.Show()

			self.SetSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT + 32 * (need_rows - 1))
			self.board.SetSize(self.GetWidth(), self.GetHeight())
			self.RefreshPosition()

	def __UpdateItemSlot(self):
		self.__ResizeItemSlot()
		result_item_count = 0
		for i in range(0, len(self.invenItemSlots)):
			inven_pos = self.invenItemSlots[i]
			item_vnum = player.GetItemIndex(inven_pos)
			count = player.GetItemCount(inven_pos)
			if self.exchangeVnum == SOUL_STONE_EXCHANGE:
				result_item_count += (self.__GetItemGrade(item_vnum) + 1) * count
			else:
				result_item_count += count

			socket = tuple(player.GetItemMetinSocket(inven_pos, j) for j in range(player.METIN_SOCKET_MAX_NUM))
			self.itemSlot.SetItemSlot(i, item_vnum, 0 if count < 2 else count, socket=socket)

		self.itemSlot.RefreshSlot()
		self.__SetPrice(result_item_count * self.costPerResultItem)
		self.resultItemSlot.SetItemSlot(0, self.resultVnum, result_item_count)

	def __OnAddToItemExchange(self, inven_pos):
		if inven_pos in self.invenItemSlots:
			return

		if len(self.invenItemSlots) >= 48:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_MAX_ITEM_COUNT)
			return

		if not self.__CheckItem(inven_pos):
			if self.exchangeVnum == SOUL_STONE_EXCHANGE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_WRONG_ITEM_SOULSTONE)
			elif self.exchangeVnum == SKILLBOOK_EXCHANGE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_WRONG_ITEM_SKILLBOOK)
			elif self.exchangeVnum == REFINEITEM_EXCHANGE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_WRONG_ITEM_REFINEITEM)
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_WRONG_ITEM)
			return

		self.invenItemSlots.append(inven_pos)
		self.__UpdateItemSlot()

		eventManager.EventManager().send_event(EVENT_ADD_ITEM_TO_ITEM_EXCHANGE, inven_pos)

	def __OnClearItemExchange(self, exchange_pos):
		eventManager.EventManager().send_event(EVENT_REMOVE_ITEM_EXCHANGE, self.invenItemSlots[exchange_pos])

		for i in range(0, len(self.invenItemSlots)):
			self.itemSlot.ClearSlot(i)

		self.invenItemSlots.pop(exchange_pos)
		self.__UpdateItemSlot()

	def __OnQuickAddInventoryItem(self, type, slotNumber):
		if type != "item_exchange":
			return

		itemVnum = player.GetItemIndex(slotNumber)
		if itemVnum > 0:
			self.__OnAddToItemExchange(slotNumber)

		self.__OverOutItem()

	def __SelectItemSlot(self, slot_num):
		self.__OnClearItemExchange(slot_num)

	def __OnSelectEmptySlot(self, slot_num):
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if player.SLOT_TYPE_INVENTORY != attachedSlotType:
				return

			self.__OnAddToItemExchange(attachedSlotPos)

	def __OverInResultItem(self, slot_num):
		if self.itemToolTip:
			self.itemToolTip.SetItemToolTip(self.resultVnum)

	def __OverInItem(self, slot_num):
		if self.itemToolTip:
			inven_pos = self.invenItemSlots[slot_num]
			self.itemToolTip.SetInventoryItem(inven_pos)

	def __OverOutItem(self):
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()

	def __OnButtonClick(self):
		if len(self.invenItemSlots) < 1:
			if self.exchangeVnum == SOUL_STONE_EXCHANGE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_NO_ITEM_SOUL_STONE)
			elif self.exchangeVnum == SKILLBOOK_EXCHANGE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_NO_ITEM_SKILLBOOK)
			elif self.exchangeVnum == REFINEITEM_EXCHANGE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_NO_ITEM_REFINEITEM)
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ITEM_EXCHANGE_NO_ITEM)

			return
		self.__SendCreatePacket()
		self.__ClearSlots()

	def __SendCreatePacket(self):
		args = ','.join(map(str, self.invenItemSlots))
		net.SendChatPacket("/item_exchange " + args)

	def __ClearSlots(self):
		for i in range(len(self.invenItemSlots)):
			self.itemSlot.ClearSlot(i)
		self.itemSlot.RefreshSlot()
		self.__SetPrice(0)
		self.resultItemSlot.SetItemSlot(0, self.resultVnum, 0)
		self.invenItemSlots = []
		self.__ResizeItemSlot()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Open(self):
		self.Show()
		self.invenItemSlots = []
		self.__SetPrice(0)
		self.chanceLabel.SetText("%d%%" % self.chance)
		eventManager.EventManager().send_event(EVENT_ITEM_EXCHANGE_OPEN)
		self.resultItemSlot.SetItemSlot(0, self.resultVnum, 0)
		self.__ResizeItemSlot()

		(self.xWndStart, self.yWndStart, z) = player.GetMainCharacterPosition()

	def Close(self):
		net.SendChatPacket("/item_exchange close")
		self.Hide()
		self.__ClearSlots()
		eventManager.EventManager().send_event(EVENT_ITEM_EXCHANGE_CLOSE)

	def OnUpdate(self):
		USE_WINDOW_LIMIT_RANGE = 1000

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xWndStart) > USE_WINDOW_LIMIT_RANGE or abs(y - self.yWndStart) > USE_WINDOW_LIMIT_RANGE:
			self.Close()
