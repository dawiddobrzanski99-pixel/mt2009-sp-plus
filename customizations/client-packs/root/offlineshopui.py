import ui
import dualshop
import mouseModule
import player
import item
import chat
import localeInfo
import app
import colorinfo
import uiScriptLocale
import shop
import flamewindPath
import constInfo
import eventManager
import special_flags
import chr

def GetMinimizedSlotFromFullSlot(fullSlotIndex):
	return fullSlotIndex - fullSlotIndex/shop.SHOP_PLAYER_WIDTH * shop.SHOP_PLAYER_WIDTH/2

def GetSlotXY(slotIndex):
	if slotIndex < 0 or slotIndex >= shop.SHOP_PLAYER_WIDTH * shop.SHOP_PLAYER_HEIGHT:
		return 0

	x = slotIndex % shop.SHOP_PLAYER_WIDTH
	y = slotIndex / shop.SHOP_PLAYER_WIDTH
	return x, y

def IsInLockedArea(slotIndex, unlockProgress=0):
    return dualshop.Locked(slotIndex, unlockProgress)

def IsInPremiumArea(slotIndex):
    return dualshop.Premium(slotIndex)

def CanPlaceItemOnShopSlot(slotIndex, itemHeight, unlockProgress, isPremium):
    if not dualshop.Fits(slotIndex, itemHeight):
        return False
    for i in range(itemHeight):
        slot = slotIndex + i * shop.SHOP_PLAYER_WIDTH
        if IsInLockedArea(slot, unlockProgress) or (not isPremium and IsInPremiumArea(slot)):
            return False
    return True

def HasShopPremium():
	return constInfo.AFFECT_DICT.has_key(chr.NEW_AFFECT_SHOP_PREMIUM)

def IsShopNearClosingTime(leftSec):
	return leftSec < 300

def SetTimeLabel(duration, timeLeftLabel):
	leftSec = max(0, duration*60)
	if not IsShopNearClosingTime(leftSec):
		timeLeftLabel.SetText(localeInfo.SecondToSmartDHMS(leftSec))
		timeLeftLabel.SetPackedFontColor(colorinfo.FONT_COLOR)
		return False
	else:
		timeLeftLabel.SetText(uiScriptLocale.SHOP_NEAR_CLOSED % 5)
		timeLeftLabel.SetPackedFontColor(colorinfo.NEUTRAL_COLOR)
		return True

def SetDuration(duration, label):
	durationText = localeInfo.DURATION5
	color = colorinfo.POSITIVE_COLOR
	if duration == 4:
		durationText = localeInfo.DURATION4
		color = colorinfo.SEMI_POSITIVE_COLOR
	# elif duration == 3:
	# 	durationText = localeInfo.DURATION3
	# 	color = colorinfo.MEDIUM_COLOR
	elif duration == 2:
		durationText = localeInfo.DURATION2
		color = colorinfo.MEDIUM_COLOR
	elif duration == 1:
		durationText = localeInfo.DURATION1
		color = colorinfo.NEGATIVE_COLOR2

	label.SetText(durationText)
	label.SetPackedFontColor(color)

def GetDurationTooltipText(duration):
	if duration == 5:
		return localeInfo.SHOP_DURATION_TOOLTIP_TEXT2 % 24
	elif duration == 4:
		return localeInfo.SHOP_DURATION_TOOLTIP_TEXT % (8, 24)
	# elif duration == 3:
	# 	return localeInfo.SHOP_DURATION_TOOLTIP_TEXT % (8, 10)
	elif duration == 2:
		return localeInfo.SHOP_DURATION_TOOLTIP_TEXT % (1, 8)
	else:
		return localeInfo.SHOP_DURATION_TOOLTIP_TEXT3 % 1

class ShopSlotRenderer:
	def __init__(self, slotWindow=None, bindInternalEvents=True, itemSlotParent=None):

		if slotWindow == None:
			self.itemSlot = self.__CreateSlotWindow(itemSlotParent)
			self.__CreateSlotCurtain()
		else:
			self.itemSlot = slotWindow

		self.tooltipItem = None

		self.selectEmptySlotAction = None
		self.selectItemSlotAction = None

		if bindInternalEvents:
			self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
			self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
			self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
			self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))

	def __CreateSlotWindow(self, parent):
		slotWnd = dualshop.DualGrid() if getattr(self, "_dualShop", False) else ui.GridSlotWindow()
		slotWnd.SetParent(parent)
		if not getattr(self, "_dualShop", False):
			slotWnd.ArrangeSlot(0, shop.SHOP_PLAYER_WIDTH, shop.SHOP_PLAYER_HEIGHT, 32, 32, 0, 0)
		slotWnd.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub")
		slotWnd.Show()
		return slotWnd

	def __CreateSlotCurtain(self):
		self.slotCurtainItems = []
		count = shop.SHOP_PLAYER_HEIGHT + (16 if getattr(self, "_dualShop", False) else 0)
		for i in range(count):
			curtain = ui.ImageBox()
			curtain.SetParent(self.itemSlot)
			premium = i < shop.SHOP_PLAYER_HEIGHT and i >= shop.SHOP_PLAYER_PREMIUM_Y_START
			curtain.LoadImage(flamewindPath.GetPublic("shop_unlock_slot_premium" if premium else "shop_unlock_slot"))
			if i < shop.SHOP_PLAYER_HEIGHT:
				curtain.SetPosition(5*32, 32*i)
			else:
				group = i - shop.SHOP_PLAYER_HEIGHT
				curtain.SetPosition((shop.SHOP_PLAYER_WIDTH + (group % 2)*5)*32, (group//2)*32)
			curtain.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OnSlotCurtainMouseOverIn, i)
			curtain.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OnSlotCurtainMouseOverOut)
			curtain.Show()
			self.slotCurtainItems.append(curtain)

	def UpdateSlotCurtain(self, unlockedNum, isPremium):
		for i, curtain in enumerate(self.slotCurtainItems):
			if i >= shop.SHOP_PLAYER_HEIGHT:
				opened = i - shop.SHOP_PLAYER_HEIGHT < max(0, unlockedNum - dualshop.OLD_KEYS)
			elif i < shop.SHOP_PLAYER_PREMIUM_Y_START:
				opened = i < unlockedNum
			else:
				opened = bool(isPremium)
			if opened:
				curtain.Hide()
			else:
				curtain.Show()

	def OnSlotCurtainMouseOverIn(self, index):
		pass

	def OnSlotCurtainMouseOverOut(self):
		pass

	def SetTooltipItem(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def Destroy(self):
		self.itemSlot = None
		self.tooltipItem = None
		self.selectEmptySlotAction = None
		self.selectItemSlotAction = None
		self.slotCurtainItems = []

	def SAFE_SetSelectItemSlotEvent(self, event):
		self.selectItemSlotAction = ui.__mem_func__(event)

	def SAFE_SetSelectEmptySlotEvent(self, event):
		self.selectEmptySlotAction = ui.__mem_func__(event)

	def OnSelectItemSlot(self, slotIndex):
		pass

	def OnSelectEmptySlot(self, slotIndex):
		pass

	def OnOverInItem(self, slotIndex):
		pass

	def OnOverOutItem(self):
		pass

class MyShopSlots(ShopSlotRenderer):
	def __init__(self, slotWindow=None, bindInternalEvents=True, itemSlotParent=None):
		self._dualShop = True
		ShopSlotRenderer.__init__(self, slotWindow, bindInternalEvents, itemSlotParent)
		self.__CreateTooltipText()

		if slotWindow==None:
			eventManager.EventManager().add_observer(eventManager.ADD_AFFECT_EVENT, self.OnAddAffect)
			eventManager.EventManager().add_observer(eventManager.SPECIAL_FLAG_UPDATE, self.OnSpecialFlagUpdate)
			self.RefreshSlotCurtain()

	def __CreateTooltipText(self):
		toolTip = ui.TextLine()
		toolTip.SetParent(self.itemSlot)
		toolTip.SetSize(0, 0)
		toolTip.SetHorizontalAlignCenter()
		toolTip.SetOutline()
		toolTip.Hide()
		# toolTip.SetPosition(self.GetWidth() / 2, -19)
		self.toolTipText = toolTip

	def OnAddAffect(self, type, pointIdx, value, duration):
		if type == chr.NEW_AFFECT_SHOP_PREMIUM:
			self.RefreshSlotCurtain()

	def OnSpecialFlagUpdate(self, flag, number):
		if flag == special_flags.SHOP_SLOT_UNLOCK_PROGRESS_FLAG:
			self.RefreshSlotCurtain()

	def RefreshSlotCurtain(self):
		# print "refresh slot %d %d" % (special_flags.GetFlag(special_flags.SHOP_SLOT_UNLOCK_PROGRESS_FLAG), 1 if HasShopPremium() else 0)
		self.UpdateSlotCurtain(
			special_flags.GetFlag(special_flags.SHOP_SLOT_UNLOCK_PROGRESS_FLAG), HasShopPremium())

	def OnSlotCurtainMouseOverIn(self, index):
		(x, y) = self.slotCurtainItems[index].GetLocalPosition()
		self.toolTipText.SetPosition(x + (5*32 / 2), y-19)
		self.toolTipText.SetText("5 pol: 2 Drewniane Klucze" if index >= shop.SHOP_PLAYER_HEIGHT else (uiScriptLocale.SHOP_LOCKED_SLOT if index < shop.SHOP_PLAYER_PREMIUM_Y_START else uiScriptLocale.SHOP_PREMIUM_SLOT))
		self.toolTipText.Show()

	def OnSlotCurtainMouseOverOut(self):
		self.toolTipText.Hide()

	def OnSelectEmptySlot(self, slotIndex):
		if constInfo.myshop_data["items"].has_key(slotIndex):
			return

		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if player.SLOT_TYPE_INVENTORY != attachedSlotType and player.SLOT_TYPE_DRAGON_SOUL_INVENTORY != attachedSlotType:
				return
			attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)
			count = player.GetItemCount(attachedInvenType, attachedSlotPos)

			itemVNum = player.GetItemIndex(attachedInvenType, attachedSlotPos)
			item.SelectItem(itemVNum)

			if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PRIVATE_SHOP_CANNOT_SELL_ITEM)
				return

			(width, height) = item.GetItemSize()
			if not CanPlaceItemOnShopSlot(slotIndex, height, special_flags.GetFlag(special_flags.SHOP_SLOT_UNLOCK_PROGRESS_FLAG), HasShopPremium()):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_PLACE_ITEM_ON_LOCKED_SLOT)
				return

			if self.selectEmptySlotAction:
				self.selectEmptySlotAction(attachedSlotPos, slotIndex, attachedSlotType, itemVNum, count)

	def OnSelectItemSlot(self, slotIndex):
		if not constInfo.myshop_data["items"].has_key(slotIndex):
			return

		if self.selectItemSlotAction:
			self.selectItemSlotAction(slotIndex)

	def OnOverInItem(self, slotIndex):
		if self.tooltipItem:
			if constInfo.myshop_data["items"].has_key(slotIndex):
				shopItem = constInfo.myshop_data["items"][slotIndex]
				self.tooltipItem.SetMyShopItem(shopItem["vnum"], shopItem["count"], shopItem["sockets"], shopItem["attrs"], shopItem["price"] if shopItem.has_key("price") else 0)
				__import__("plus9origin").Request(self.tooltipItem, 1, shopItem["id"], 0, shopItem["vnum"]) # MT2009_PLUS9_ORIGIN_V1
				self.tooltipItem.AppendSpace(5)
				self.tooltipItem.AppendTextLine(localeInfo.QUICK_REMOVE_FROM_MYSHOP)
				self.tooltipItem.AppendTextLine(localeInfo.QUICK_EDIT_MYSHOP)
				self.tooltipItem.AppendTextLine(localeInfo.QUICK_EDIT_MYSHOP_SIMILAR)

	def OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

