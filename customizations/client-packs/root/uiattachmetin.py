import app
import dbg
import player
import item
import net
import snd
import ui
import uiToolTip
import localeInfo
import eventManager
import uiRefine

EVENT_ATTACH_METIN_OPEN = "EVENT_ATTACH_METIN_OPEN" # args | itemSlotPos: number, metinSlotPos: number
EVENT_ATTACH_METIN_CLOSE = "EVENT_ATTACH_METIN_CLOSE" # args |

class AttachMetinDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadScript()

		self.metinItemPos = 0
		self.targetItemPos = 0

	def __LoadScript(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/attachstonedialog.py")

		except:
			import exception
			exception.Abort("AttachStoneDialog.__LoadScript.LoadObject")

		try:
			self.board = self.GetChild("Board")
			self.titleBar = self.GetChild("TitleBar")
			self.metinImage = self.GetChild("MetinImage")
			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.Accept))
			self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Close))
		except:
			import exception
			exception.Abort("AttachStoneDialog.__LoadScript.BindObject")

		oldToolTip = uiToolTip.ItemToolTip()
		oldToolTip.SetParent(self)
		oldToolTip.SetPosition(15, 38)
		oldToolTip.SetFollow(False)
		oldToolTip.Show()
		self.oldToolTip = oldToolTip

		newToolTip = uiToolTip.ItemToolTip()
		newToolTip.SetParent(self)
		newToolTip.SetPosition(230 + 20, 38)
		newToolTip.SetFollow(False)
		newToolTip.Show()
		self.newToolTip = newToolTip

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.board = 0
		self.titleBar = 0
		self.metinImage = 0
		self.toolTip = 0

	def CanAttachMetin(self, slot, metin):
		if item.METIN_NORMAL == metin:
			if player.METIN_SOCKET_TYPE_SILVER == slot or player.METIN_SOCKET_TYPE_GOLD == slot:
				return True

		elif item.METIN_GOLD == metin:
			if player.METIN_SOCKET_TYPE_GOLD == slot:
				return True

	def Open(self, metinItemPos, targetItemPos):
		self.metinItemPos = metinItemPos
		self.targetItemPos = targetItemPos
		self.enterReleased = not uiRefine.IsEnterHeld()	# MT2009_PLUS_REFINE_ENTER_V1

		metinIndex = player.GetItemIndex(metinItemPos)
		itemIndex = player.GetItemIndex(targetItemPos)
		self.oldToolTip.ClearToolTip()
		self.newToolTip.ClearToolTip()

		item.SelectItem(metinIndex)

		## Metin Image
		try:
			self.metinImage.LoadImage(item.GetIconImageFileName())
		except:
			dbg.TraceError("AttachMetinDialog.Open.LoadImage - Failed to find item data")

		## Old Item ToolTip
		metinSlot = []
		for i in xrange(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(player.GetItemMetinSocket(targetItemPos, i))
		self.oldToolTip.AddItemData(itemIndex, metinSlot)

		## New Item ToolTip
		item.SelectItem(metinIndex)
		metinSubType = item.GetItemSubType()

		metinSlot = []
		for i in xrange(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(player.GetItemMetinSocket(targetItemPos, i))
		for i in xrange(player.METIN_SOCKET_MAX_NUM):
			slotData = metinSlot[i]
			if self.CanAttachMetin(slotData, metinSubType):
				metinSlot[i] = metinIndex
				break
		self.newToolTip.AddItemData(itemIndex, metinSlot)

		self.UpdateDialog()
		self.SetTop()
		self.Show()

		eventManager.EventManager().send_event(EVENT_ATTACH_METIN_OPEN, targetItemPos, metinItemPos)

	def UpdateDialog(self):
		newWidth = self.newToolTip.GetWidth() + 230 + 15 + 20
		newHeight = self.newToolTip.GetHeight() + 98

		if localeInfo.IsARABIC():
			self.board.SetPosition( newWidth, 0 )

			(x,y) = self.titleBar.GetLocalPosition()
			self.titleBar.SetPosition( newWidth - 15, y )

		self.board.SetSize(newWidth, newHeight)
		self.titleBar.SetWidth(newWidth-15)
		self.SetSize(newWidth, newHeight)

		(x, y) = self.GetLocalPosition()
		self.SetPosition(x, y)

	def Accept(self):
		net.SendItemUseToItemPacket(self.metinItemPos, self.targetItemPos)
		snd.PlaySound("sound/ui/metinstone_insert.wav")
		self.Close()

	def Close(self):
		self.Hide()
		eventManager.EventManager().send_event(EVENT_ATTACH_METIN_CLOSE)

	# MT2009_PLUS_REFINE_ENTER_V1 (Autor: Vekirion): Enter (routed from game.OnIMEReturn) presses
	# "Accept"; a held Enter counts once, until it is let go.
	def PressByEnter(self):
		if not self.IsShow():
			return False
		if not getattr(self, "enterReleased", True):
			return True
		self.enterReleased = False
		self.Accept()
		return True

	def OnUpdate(self):
		if not getattr(self, "enterReleased", True) and not uiRefine.IsEnterHeld():
			self.enterReleased = True
