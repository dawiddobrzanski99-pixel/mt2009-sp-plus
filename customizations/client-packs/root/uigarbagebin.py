import item
import localeInfo
import mouseModule
import net
import player
import snd
import ui
import uiCommon
import app
import chat
import re


SLOT_BASE_IMAGE = "d:/ymir work/ui/public/Slot_Base.sub"
BUTTON_PATH = "d:/ymir work/ui/public/"

try:
	WindowDestroy = ui.WindowDestroy
except AttributeError:
	def WindowDestroy(func):
		return func

def IsInventorySourceSlot(slotType):
	if slotType == player.SLOT_TYPE_INVENTORY:
		return True
	if False:
		return slotType in (
			player.SLOT_TYPE_SKILL_BOOK_INVENTORY,
			player.SLOT_TYPE_UPGRADE_ITEMS_INVENTORY,
			player.SLOT_TYPE_STONE_INVENTORY,
			player.SLOT_TYPE_BOX_INVENTORY,
			player.SLOT_TYPE_ENCHANT_INVENTORY,
			player.SLOT_TYPE_FLOWER_INVENTORY,
		)
	return False

class _GarbageBinBase(ui.ScriptWindow):
	SLOT_X_COUNT = 6
	SLOT_Y_COUNT = 6
	SLOT_COUNT = SLOT_X_COUNT * SLOT_Y_COUNT
	WINDOW_WIDTH = 216
	WINDOW_HEIGHT = 306

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.interface = None
		self.tooltipItem = None
		self.board = None
		self.itemSlot = None
		self.deleteButton = None
		self.clearButton = None
		self.questionDialog = None
		self.items = []

	@WindowDestroy
	def Destroy(self):
		self.CloseQuestionDialog()
		self.__Initialize()

	def __LoadWindow(self):
		self.SetSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
		self.AddFlag("movable")
		self.AddFlag("float")

		board = ui.BoardWithTitleBar()
		board.SetParent(self)
		board.AddFlag("attach")
		board.SetPosition(0, 0)
		board.SetSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
		board.SetTitleName('Kosz (J)')
		board.SetCloseEvent(ui.__mem_func__(self.Close))
		board.Show()
		self.board = board

		itemSlot = ui.GridSlotWindow()
		itemSlot.SetParent(board)
		itemSlot.SetPosition(12, 38)
		itemSlot.ArrangeSlot(0, self.SLOT_X_COUNT, self.SLOT_Y_COUNT, 32, 32, 0, 0)
		itemSlot.SetSlotBaseImage(SLOT_BASE_IMAGE, 1.0, 1.0, 1.0, 1.0)
		itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		itemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		itemSlot.Show()
		self.itemSlot = itemSlot

		if False:
			deleteButton = ui.MakeButton(board, 0, 242, "", "d:/ymir work/ui/eter_interface/buttons/", "settings_button_01.sub", "settings_button_02.sub", "settings_button_03.sub")
		else:
			deleteButton = ui.MakeButton(board, 0, 242, "", BUTTON_PATH, "middle_button_01.sub", "middle_button_02.sub", "middle_button_03.sub")
		deleteButton.SetPosition((self.WINDOW_WIDTH - deleteButton.GetWidth()) // 2, 242)
		deleteButton.SetText('Usun przedmioty')
		deleteButton.SetEvent(ui.__mem_func__(self.OnDelete))
		self.deleteButton = deleteButton

		if False:
			clearButton = ui.MakeButton(board, 0, 268, "", "d:/ymir work/ui/eter_interface/buttons/", "settings_button_01.sub", "settings_button_02.sub", "settings_button_03.sub")
		else:
			clearButton = ui.MakeButton(board, 0, 268, "", BUTTON_PATH, "middle_button_01.sub", "middle_button_02.sub", "middle_button_03.sub")
		clearButton.SetPosition((self.WINDOW_WIDTH - clearButton.GetWidth()) // 2, 268)
		clearButton.SetText('Oproznij kolejke')
		clearButton.SetEvent(ui.__mem_func__(self.ClearItems))
		self.clearButton = clearButton

		self.Refresh()
		self.Hide()

	def BindInterface(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.CloseQuestionDialog()
		self.OverOutItem()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def CanAddItemToGarbageBin(self, invenType, slotIndex = None, gridSlot = None):
		if slotIndex is None:
			slotIndex = invenType
			invenType = player.INVENTORY

		if self.__FindItem(invenType, slotIndex) != -1:
			return False
		if invenType == player.INVENTORY and player.IsEquipmentSlot(slotIndex):
			return False

		itemVnum = player.GetItemIndex(invenType, slotIndex)
		if itemVnum == 0:
			return False

		itemSizeX, itemSizeY = self.__GetItemSize(itemVnum)
		if gridSlot is not None:
			return self.__CanPlaceItem(gridSlot, itemSizeX, itemSizeY, self.__BuildOccupiedSlots())
		return self.__FindEmptySlotForItem(itemSizeX, itemSizeY) != -1

	def IsItemInGarbageBin(self, invenType, slotIndex):
		itemIndex = self.__FindItem(invenType, slotIndex)
		if itemIndex == -1:
			return False

		data = self.items[itemIndex]
		return (player.GetItemIndex(invenType, slotIndex) == data["itemVnum"]
			and player.GetItemCount(invenType, slotIndex) == data["itemCount"])

	def AddItemToGarbageBin(self, invenType, slotIndex = None, gridSlot = None):
		if slotIndex is None:
			slotIndex = invenType
			invenType = player.INVENTORY

		if not self.CanAddItemToGarbageBin(invenType, slotIndex, gridSlot):
			return False

		itemVnum = player.GetItemIndex(invenType, slotIndex)
		itemCount = player.GetItemCount(invenType, slotIndex)
		itemSizeX, itemSizeY = self.__GetItemSize(itemVnum)
		if gridSlot is None:
			gridSlot = self.__FindEmptySlotForItem(itemSizeX, itemSizeY)
		if gridSlot == -1:
			return False

		self.items.append({
			"invenType" : invenType,
			"slotIndex" : slotIndex,
			"itemVnum" : itemVnum,
			"itemCount" : itemCount,
			"gridSlot" : gridSlot,
			"itemSizeX" : itemSizeX,
			"itemSizeY" : itemSizeY,
		})
		self.Refresh()
		snd.PlaySound("sound/ui/drop.wav")
		return True

	def __AddAttachedItemToGarbageBin(self, gridSlot):
		if not mouseModule.mouseController.isAttached():
			return False

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		if IsInventorySourceSlot(attachedSlotType):
			attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)
			self.AddItemToGarbageBin(attachedInvenType, attachedSlotPos, gridSlot)

		mouseModule.mouseController.DeattachObject()
		return True

	def OnSelectEmptySlot(self, slotIndex):
		self.__AddAttachedItemToGarbageBin(slotIndex)

	def OnSelectItemSlot(self, slotIndex):
		if self.__AddAttachedItemToGarbageBin(slotIndex):
			return

		itemIndex = self.__FindItemByGridSlot(slotIndex)
		if itemIndex == -1:
			return
		del self.items[itemIndex]
		self.Refresh()

	def ClearItems(self):
		self.items = []
		self.Refresh()

	def OnDelete(self):
		self.__PruneInvalidItems()
		if not self.items:
			return
		self.__OpenQuestionDialog('Trwale usunac wybrane stosy?', ui.__mem_func__(self.AcceptDelete))

	def AcceptDelete(self):
		for data in self.items:
			raise RuntimeError("Native deletion is disabled")
		self.ClearItems()
		self.CloseQuestionDialog()

	def CloseQuestionDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
		self.questionDialog = None

	def Refresh(self):
		if not self.itemSlot:
			return

		self.__PruneInvalidItems()
		for slotIndex in xrange(self.SLOT_COUNT):
			self.itemSlot.ClearSlot(slotIndex)

		for data in self.items:
			count = data["itemCount"]
			if count <= 1:
				count = 0
			self.itemSlot.SetItemSlot(data["gridSlot"], data["itemVnum"], count)

		self.itemSlot.RefreshSlot()
		self.__RefreshInventoryHighlight()

	def __RefreshInventoryHighlight(self):
		if self.interface:
			self.interface.RefreshInventory()

	def OverInItem(self, slotIndex):
		if not self.tooltipItem:
			return
		itemIndex = self.__FindItemByGridSlot(slotIndex)
		if itemIndex == -1:
			return

		data = self.items[itemIndex]
		self.tooltipItem.SetInventoryItem(data["slotIndex"], data["invenType"])

	def OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __OpenQuestionDialog(self, text, acceptEvent):
		self.CloseQuestionDialog()
		questionDialog = uiCommon.QuestionDialog()
		questionDialog.SetText(text)
		questionDialog.SetAcceptEvent(acceptEvent)
		questionDialog.SetCancelEvent(ui.__mem_func__(self.CloseQuestionDialog))
		questionDialog.Open()
		self.questionDialog = questionDialog

	def __FindItem(self, invenType, slotIndex):
		for index, data in enumerate(self.items):
			if data["invenType"] == invenType and data["slotIndex"] == slotIndex:
				return index
		return -1

	def __FindItemByGridSlot(self, slotIndex):
		for index, data in enumerate(self.items):
			gridSlot = data.get("gridSlot", -1)
			itemSizeX = data.get("itemSizeX", 1)
			itemSizeY = data.get("itemSizeY", 1)
			for y in xrange(itemSizeY):
				for x in xrange(itemSizeX):
					if gridSlot + (y * self.SLOT_X_COUNT) + x == slotIndex:
						return index
		return -1

	def __GetItemSize(self, itemVnum):
		item.SelectItem(itemVnum)
		itemSizeX, itemSizeY = item.GetItemSize()
		itemSizeX = max(1, min(self.SLOT_X_COUNT, itemSizeX))
		itemSizeY = max(1, min(self.SLOT_Y_COUNT, itemSizeY))
		return itemSizeX, itemSizeY

	def __BuildOccupiedSlots(self):
		occupiedSlots = {}
		for data in self.items:
			gridSlot = data.get("gridSlot", -1)
			itemSizeX = data.get("itemSizeX", 1)
			itemSizeY = data.get("itemSizeY", 1)
			for y in xrange(itemSizeY):
				for x in xrange(itemSizeX):
					occupiedSlots[gridSlot + (y * self.SLOT_X_COUNT) + x] = True
		return occupiedSlots

	def __FindEmptySlotForItem(self, itemSizeX, itemSizeY):
		occupiedSlots = self.__BuildOccupiedSlots()
		for slotIndex in xrange(self.SLOT_COUNT):
			if self.__CanPlaceItem(slotIndex, itemSizeX, itemSizeY, occupiedSlots):
				return slotIndex
		return -1

	def __CanPlaceItem(self, slotIndex, itemSizeX, itemSizeY, occupiedSlots):
		slotX = slotIndex % self.SLOT_X_COUNT
		slotY = slotIndex // self.SLOT_X_COUNT
		if slotX + itemSizeX > self.SLOT_X_COUNT:
			return False
		if slotY + itemSizeY > self.SLOT_Y_COUNT:
			return False

		for y in xrange(itemSizeY):
			for x in xrange(itemSizeX):
				if (slotIndex + (y * self.SLOT_X_COUNT) + x) in occupiedSlots:
					return False
		return True

	def __ReflowItems(self, items):
		self.items = []
		pendingItems = []
		occupiedSlots = {}
		for data in items:
			itemSizeX = data.get("itemSizeX", 1)
			itemSizeY = data.get("itemSizeY", 1)
			gridSlot = data.get("gridSlot", -1)
			data["itemSizeX"] = itemSizeX
			data["itemSizeY"] = itemSizeY
			if gridSlot != -1 and self.__CanPlaceItem(gridSlot, itemSizeX, itemSizeY, occupiedSlots):
				data["gridSlot"] = gridSlot
				self.items.append(data)
				for y in xrange(itemSizeY):
					for x in xrange(itemSizeX):
						occupiedSlots[gridSlot + (y * self.SLOT_X_COUNT) + x] = True
			else:
				pendingItems.append(data)

		for data in pendingItems:
			itemSizeX = data.get("itemSizeX", 1)
			itemSizeY = data.get("itemSizeY", 1)
			gridSlot = self.__FindEmptySlotForItem(itemSizeX, itemSizeY)
			if gridSlot == -1:
				continue
			data["gridSlot"] = gridSlot
			data["itemSizeX"] = itemSizeX
			data["itemSizeY"] = itemSizeY
			self.items.append(data)

	def __PruneInvalidItems(self):
		validItems = []
		for data in self.items:
			itemVnum = player.GetItemIndex(data["invenType"], data["slotIndex"])
			itemCount = player.GetItemCount(data["invenType"], data["slotIndex"])
			if itemVnum == 0:
				continue
			if itemVnum != data["itemVnum"]:
				continue
			if itemCount != data["itemCount"]:
				continue
			itemSizeX, itemSizeY = self.__GetItemSize(itemVnum)
			data["itemSizeX"] = itemSizeX
			data["itemSizeY"] = itemSizeY
			validItems.append(data)
		self.__ReflowItems(validItems)


class GarbageBinWindow(_GarbageBinBase):
	def __init__(self):
		self.phase = "idle"
		self.ready = False
		self.serial = 0
		self.waiting = None
		self.nextSend = 0.0
		self.batch = []
		self.cursor = 0
		# A server that answers "GarbageBinBatch 1" (server-patches/playerqol)
		# takes BATCH_SIZE stacks a command: the choice is confirmed first,
		# then every chunk is proved and destroyed in two round trips.
		# Stack by stack it was two round trips and a pause each.
		self.batchReady = False
		self.batchMode = False
		self.batchToken = None
		self.chunkLen = 0
		_GarbageBinBase.__init__(self)
		self.SetCenterPosition()

	def Destroy(self):
		# Logout teardown must not refresh inventory or query cleared player data.
		self.phase = "idle"
		self.waiting = None
		self.batch = []
		self.ready = False
		self.interface = None
		self.tooltipItem = None
		_GarbageBinBase.CloseQuestionDialog(self)
		self.Hide()
		_GarbageBinBase.Destroy(self)

	def Notice(self, text):
		chat.AppendChat(chat.CHAT_TYPE_INFO, "Kosz: " + text)

	def Open(self):
		_GarbageBinBase.Open(self)
		if not self.ready and app.GetTime() >= self.nextSend:
			net.SendChatPacket("/garbage hello")
			self.nextSend = app.GetTime() + 1.0
			self.Notice("Sprawdzanie obslugi na serwerze. Przeciagnij przedmioty do kosza.")

	def OnReady(self, version):
		self.ready = str(version) == "1"
		if self.ready:
			self.Notice("Gotowy. Usuwane sa cale wybrane stosy.")

	def OnBatch(self, version):
		self.batchReady = str(version) == "1"

	def Snapshot(self, window, slot):
		return (player.GetItemIndex(window, slot), player.GetItemCount(window, slot),
			tuple(player.GetItemMetinSocket(window, slot, i) for i in xrange(player.METIN_SOCKET_MAX_NUM)),
			tuple(player.GetItemAttribute(window, slot, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)))

	def CanAddItemToGarbageBin(self, invenType, slotIndex=None, gridSlot=None):
		if self.phase != "idle" or invenType != player.INVENTORY:
			return False
		return _GarbageBinBase.CanAddItemToGarbageBin(self, invenType, slotIndex, gridSlot)

	def AddItemToGarbageBin(self, invenType, slotIndex=None, gridSlot=None):
		result = _GarbageBinBase.AddItemToGarbageBin(self, invenType, slotIndex, gridSlot)
		if result:
			self.items[-1]["snapshot"] = self.Snapshot(invenType, slotIndex)
		return result

	def OnSelectItemSlot(self, slotIndex):
		if self.phase == "idle":
			_GarbageBinBase.OnSelectItemSlot(self, slotIndex)

	def ClearItems(self):
		if self.phase == "idle":
			_GarbageBinBase.ClearItems(self)

	def Valid(self, data):
		return self.Snapshot(data["invenType"], data["slotIndex"]) == data.get("snapshot")

	def OnDelete(self):
		if self.phase != "idle":
			return
		if not self.ready:
			self.Notice("Serwer nie potwierdzil obslugi kosza. Zamknij i otworz kosz po wdrozeniu.")
			return
		self.items = [d for d in self.items if self.Valid(d)]
		self.Refresh()
		if not self.items:
			return
		self.batch = [dict(d) for d in self.items]
		self.cursor = 0
		if self.batchReady:
			self.batchMode = True
			self.AskConfirm()
			return
		self.batchMode = False
		self.phase = "prepare"
		self.deleteButton.SetText("Sprawdzanie...")

	BATCH_SIZE = 18

	def AskConfirm(self):
		self.phase = "confirm"
		self.confirmUntil = app.GetTime() + 30.0
		self.deleteButton.SetText("Potwierdz w oknie")
		question = uiCommon.QuestionDialog()
		question.SetText("Trwale usunac %d stosow?" % len(self.batch))
		question.SetAcceptEvent(ui.__mem_func__(self.AcceptDelete))
		question.SetCancelEvent(ui.__mem_func__(self.CloseQuestionDialog))
		question.Open()
		self.questionDialog = question

	def UpdateBatch(self, now):
		if self.phase == "batch_prepare":
			if self.cursor >= len(self.batch):
				self.phase = "idle"
				self.batch = []
				self.batchMode = False
				self.ClearItems()
				self.deleteButton.SetText("Usun przedmioty")
				self.Notice("Serwer potwierdzil usuniecie wybranych przedmiotow.")
				return
			chunk = self.batch[self.cursor:self.cursor + self.BATCH_SIZE]
			for data in chunk:
				if not self.Valid(data):
					self.Abort("Przedmiot zmienil sie. Operacja przerwana; sprawdz ekwipunek.")
					return
			self.serial += 1
			req = str(self.serial)
			self.waiting = (req, now + 8.0)
			self.nextSend = now + 0.2
			self.chunkLen = len(chunk)
			net.SendChatPacket("/garbage prepare_many %s %s" % (req, " ".join(
				"%d:%d:%d" % (d["slotIndex"], d["itemVnum"], d["itemCount"]) for d in chunk)))
		elif self.phase == "batch_commit":
			self.serial += 1
			req = str(self.serial)
			self.waiting = (req, now + 8.0)
			self.nextSend = now + 0.2
			net.SendChatPacket("/garbage commit_many %s %s" % (req, self.batchToken))

	def OnPreparedMany(self, req, token, count="0"):
		if self.phase != "batch_prepare" or not self.waiting or str(req) != self.waiting[0]:
			return
		if not re.match(r"^[0-9a-f]{32}$", str(token)):
			self.Abort("Nieprawidlowa odpowiedz serwera.")
			return
		self.batchToken = str(token)
		self.phase = "batch_commit"
		self.waiting = None

	def OnRejectedMany(self, req, index="0", reason="?"):
		if self.waiting and str(req) == self.waiting[0]:
			self.Abort("Serwer odrzucil operacje (%s). Sprawdz ekwipunek." % reason)

	def OnResultMany(self, req, status="?", done="0"):
		if self.phase != "batch_commit" or not self.waiting or str(req) != self.waiting[0]:
			return
		if str(status) != "OK":
			self.Abort("Serwer odrzucil operacje (%s). Sprawdz ekwipunek." % status)
			return
		self.cursor += self.chunkLen
		self.batchToken = None
		self.phase = "batch_prepare"
		self.waiting = None

	def OnUpdate(self):
		now = app.GetTime()
		if self.phase == "confirm" and now >= self.confirmUntil:
			self.Abort("Potwierdzenie wygaslo. Sprobuj ponownie.")
			return
		if self.waiting:
			if now >= self.waiting[1]:
				self.Abort("Brak odpowiedzi. Sprawdz ekwipunek przed ponowna proba.")
			return
		if self.phase in ("batch_prepare", "batch_commit"):
			if now >= self.nextSend:
				self.UpdateBatch(now)
			return
		if self.phase not in ("prepare", "commit") or now < self.nextSend:
			return
		if self.cursor >= len(self.batch):
			if self.phase == "prepare":
				self.phase = "confirm"
				self.confirmUntil = now + 30.0
				self.deleteButton.SetText("Potwierdz w oknie")
				question = uiCommon.QuestionDialog()
				question.SetText("Trwale usunac %d stosow?" % len(self.batch))
				question.SetAcceptEvent(ui.__mem_func__(self.AcceptDelete))
				question.SetCancelEvent(ui.__mem_func__(self.CloseQuestionDialog))
				question.Open()
				self.questionDialog = question
			else:
				self.phase = "idle"
				self.batch = []
				self.ClearItems()
				self.deleteButton.SetText("Usun przedmioty")
				self.Notice("Serwer potwierdzil usuniecie wybranych przedmiotow.")
			return
		data = self.batch[self.cursor]
		if not self.Valid(data):
			self.Abort("Przedmiot zmienil sie. Operacja przerwana; sprawdz ekwipunek.")
			return
		self.serial += 1
		req = str(self.serial)
		self.waiting = (req, now + 8.0)
		self.nextSend = now + 0.35
		if self.phase == "prepare":
			net.SendChatPacket("/garbage prepare %s %d %d %d %d" % (req, data["invenType"], data["slotIndex"], data["itemVnum"], data["itemCount"]))
		else:
			net.SendChatPacket("/garbage commit %s %s" % (req, data["token"]))

	def OnPrepared(self, req, token):
		if self.phase != "prepare" or not self.waiting or str(req) != self.waiting[0]:
			return
		if not re.match(r"^[0-9a-f]{32}$", str(token)):
			self.Abort("Nieprawidlowa odpowiedz serwera.")
			return
		self.batch[self.cursor]["token"] = str(token)
		self.cursor += 1
		self.waiting = None

	def OnRejected(self, req, reason):
		if self.waiting and str(req) == self.waiting[0]:
			self.Abort("Serwer odrzucil operacje (%s). Sprawdz ekwipunek." % reason)

	def OnResult(self, req, status):
		if self.phase != "commit" or not self.waiting or str(req) != self.waiting[0]:
			return
		if str(status) != "OK":
			self.OnRejected(req, status)
			return
		self.cursor += 1
		self.waiting = None

	def AcceptDelete(self):
		if self.phase != "confirm":
			return
		if app.GetTime() >= self.confirmUntil or not all(self.Valid(d) for d in self.batch):
			self.Abort("Wybor zmienil sie lub wygasl. Wybierz przedmioty ponownie.")
			return
		if self.batchMode:
			self.phase = "batch_prepare"
			self.cursor = 0
			self.nextSend = 0.0
			_GarbageBinBase.CloseQuestionDialog(self)
			self.deleteButton.SetText("Usuwanie...")
			return
		self.phase = "commit"
		self.cursor = 0
		_GarbageBinBase.CloseQuestionDialog(self)
		self.deleteButton.SetText("Usuwanie...")

	def CloseQuestionDialog(self):
		_GarbageBinBase.CloseQuestionDialog(self)
		if self.phase == "confirm":
			self.phase = "idle"
			self.batch = []
			self.deleteButton.SetText("Usun przedmioty")

	def Abort(self, message):
		self.phase = "idle"
		self.waiting = None
		self.batch = []
		self.batchMode = False
		self.batchToken = None
		_GarbageBinBase.CloseQuestionDialog(self)
		self.deleteButton.SetText("Usun przedmioty")
		self.Notice(message)
		self.Refresh()

	def Close(self):
		if self.phase != "idle":
			self.Abort("Anulowano pozostale operacje. Wyslane usuniecia mogly juz zostac wykonane.")
		self.items = []
		_GarbageBinBase.Close(self)
		self.Refresh()
