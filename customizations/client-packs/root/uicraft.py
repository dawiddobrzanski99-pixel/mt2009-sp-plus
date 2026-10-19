import constInfo

import eventManager
import ui
import item
import colorInfo
import localeInfo
import utils
import flamewindPath
import net
import snd
import app
import player
import uiCommon
import gameSettings
from _weakref import proxy

TRADEABLE_CRAFTING_CATEGORIES = {
	0 : {
		"name": "Niehandlowalne",
		"items": [],
		"filters": {
			"antiflag": item.ITEM_ANTIFLAG_MYSHOP,
		}
	},
	1 : {
		"name": "Handlowalne",
		"items": [],
	},
}

DEFAULT_CRAFTING_CATEGORIES = {
	0 : {
		"name": "Bronie",
		"items": [],
		"filters": {
			"item_type": 1,
		}
	},
	1: {
		"name": "Pancerze",
		"items": [],
		"filters": {
			"item_type": 2,
			"item_subtype": 0,
		}
	},
	2 : {
		"name": "Inne",
		"items": [],
	},
}

HERB_CRAFTING_CATEGORIES = {
	0: {
		"name": localeInfo.HERB_CRAFT_CATEGORY_BOOST, "items": [],
		"filters": {"item_value": (1, 1)}
	},
	1: {
		"name": localeInfo.HERB_CRAFT_CATEGORY_OFFENSIVE, "items": [],
		"filters": {"item_value": (1, 2)}
	},
	2: {
		"name": localeInfo.HERB_CRAFT_CATEGORY_DEFENSIVE, "items": [],
		"filters": {"item_value": (1, 3)}
	},
	3: {
		"name": "Inne",
		"items": [],
	},
}

SURA_CRAFTING_CATEGORIES = {
	0 : {
		"name": "Zwoje i Marmury", "items": [],
		"filters": {"craft_vnum": (100, 101, 102,)}
	},
	1 : {
		"name": "Wymiany", "items": [],
		"filters": {"craft_vnum": (104,)}
	},
	3: {
		"name": "Inne",
		"items": [],
	},
}

CRAFTING_CATEGORIES_BY_VNUM = {
	101: TRADEABLE_CRAFTING_CATEGORIES,
	102: HERB_CRAFTING_CATEGORIES,
	104: SURA_CRAFTING_CATEGORIES,
	"default": DEFAULT_CRAFTING_CATEGORIES,
}

TEST_CRAFTING_DATA = {
	1 : {
		"item_vnum" : 71084,
		"count" : 1,
		"price" : 100000,
		"chance" : 100,
		"recipe" : (27001, 10, 27004, 15),
		"is_available" : True,
	},

	2 : {
		"item_vnum" : 71085,
		"count" : 1,
		"price" : 100000,
		"chance" : 100,
		"recipe" : (71095, 1),
		"is_available" : True,
	},

	3 : {
		"item_vnum" : 71001,
		"count" : 2,
		"price" : 2500000,
		"chance" : 70,
		"recipe" : (30006, 5, 71083, 2, 71094, 5, 30008, 1, 30009, 10),
		"is_available" : False,
		"requirements" : {
			"recipe_progress" : (1, 3),
		},
	},

	4 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : True,
	},
5 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : True,
	},
6 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : True,
	},
7 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : True,
	},
8 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : True,
	},
9 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : False,
		"requirements" : {
			"min_level" : 90,
		},
	},
10 : {
		"item_vnum" : 19,
		"count" : 1,
		"price" : 2500,
		"chance" : 90,
		"recipe" : (30030, 1),
		"is_available" : True,
	},
}

def search_similar(input, crafting_data):
	similar_indices = []
	input = input.lower()
	inputWords = input.split()
	for itemIdx,itemData in crafting_data.iteritems():
		if not itemData.has_key("item_vnum"):
			continue

		item.SelectItem(itemData["item_vnum"])
		itemName = item.GetItemName().lower()
		if len(inputWords) == 1:
			words = itemName.split()
			for word in words:
				if utils.check_string_similarity(input, word):
					similar_indices.append(itemIdx)
		else:
			if utils.check_string_similarity(input, itemName):
				similar_indices.append(itemIdx)
	return similar_indices

class CraftingWindow(ui.ScriptWindow):
	class MaterialItem(ui.ThinBoard):
		def __init__(self):
			ui.ThinBoard.__init__(self)
			self.SetSize(250, 46)

			item_slot = ui.ImageBox()
			item_slot.SetParent(self)
			item_slot.SetWindowVerticalAlignCenter()
			item_slot.SetPosition(10, 0)
			item_slot.LoadImage("d:/ymir work/ui/public/slot_base.sub")
			item_slot.Show()
			self.item_slot = item_slot

			icon = ui.ImageBox()
			icon.SetParent(self.item_slot)
			icon.SetWindowVerticalAlignCenter()
			icon.SetPosition(0, 0)
			icon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverIn)
			icon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOut)
			icon.Show()
			self.item_icon = icon

			text = ui.TextLine()
			text.SetParent(self)
			text.SetWindowVerticalAlignCenter()
			text.SetVerticalAlignCenter()
			text.SetPosition(48, 0)
			text.Show()
			self.item_name = text

			self.toolTipItem = None
			self.item_vnum = None
			self.item_count = None

		def __del__(self):
			ui.ThinBoard.__del__(self)

		def SetItemToolTip(self, toolTipItem):
			self.toolTipItem = proxy(toolTipItem)

		def SetItem(self, item_vnum, item_count):
			self.item_vnum = item_vnum
			self.item_count = item_count
			item.SelectItem(item_vnum)
			self.item_icon.LoadImage(item.GetIconImageFileName())
			self.Update()

		def Update(self):
			count_in_inventory = utils.CountItemCountInInventory(self.item_vnum)
			if count_in_inventory >= self.item_count:
				self.item_name.SetPackedFontColor(colorInfo.POSITIVE_COLOR)
			else:
				self.item_name.SetPackedFontColor(colorInfo.NEGATIVE_COLOR)

			item.SelectItem(self.item_vnum)
			self.item_name.SetText("%dx %s (%d)" % (self.item_count, item.GetItemName(), count_in_inventory))

		def __OnMouseOverIn(self):
			if self.toolTipItem:
				self.toolTipItem.ClearToolTip()
				self.toolTipItem.SetItemToolTip(self.item_vnum)
				self.toolTipItem.ShowToolTip()

		def __OnMouseOverOut(self):
			if self.toolTipItem:
				self.toolTipItem.HideToolTip()

		def SetMask(self, mask):
			self.SetClippingMaskWindow(mask)
			self.item_slot.SetClippingMaskWindow(mask)
			self.item_icon.SetClippingMaskWindow(mask)
			self.item_name.SetClippingMaskWindow(mask)

	class TabButton(ui.Window):
		SELECTED_COLOR = 0x48EF6C00
		HOVER_COLOR = 0x48C5C5C5

		def __init__(self):
			ui.Window.__init__(self)
			self.SetSize(307, 20)
			self.hover_bar = self.__CreateBar(self.HOVER_COLOR)
			self.selected_bar = self.__CreateBar(self.SELECTED_COLOR)
			self.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverIn)
			self.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOut)

			self.mask_wnd = None

			self.item_index = 0
			self.max_quantity = 0
			self.text = None

		def __del__(self):
			ui.Window.__del__(self)

		def SetClippingMaskWindow(self, maskWnd):
			self.mask_wnd = proxy(maskWnd)
			ui.Window.SetClippingMaskWindow(self, maskWnd)
			if self.text:
				self.text.SetClippingMaskWindow(maskWnd)

		def __CreateBar(self, color):
			bar = ui.Bar()
			bar.AddFlag("not_pick")
			bar.SetParent(self)
			bar.SetSize(self.GetWidth(), self.GetHeight())
			bar.SetColor(color)
			bar.Hide()
			return bar

		def __OnMouseOverIn(self):
			if not self.selected_bar.IsShow():
				self.hover_bar.Show()

		def __OnMouseOverOut(self):
			self.hover_bar.Hide()

		def Selected(self):
			self.hover_bar.Hide()
			self.selected_bar.Show()

		def Deselect(self):
			self.selected_bar.Hide()

		def SetText(self, title, color=None):
			text = ui.TextLine()
			text.SetParent(self)
			text.SetVerticalAlignCenter()
			text.SetWindowVerticalAlignCenter()
			text.SetText(title)
			if color:
				text.SetPackedFontColor(color)
			text.SetPosition(25, 0)
			text.SetClippingMaskWindow(self.mask_wnd)
			text.Show()
			self.text = text

	class CategoryButton(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.SetSize(300, 20)

			tab_icon = ui.ImageBox()
			tab_icon.AddFlag("not_pick")
			tab_icon.SetParent(self)
			tab_icon.LoadImage(flamewindPath.GetPublic("closed_tab_01"))
			tab_icon.SetWindowVerticalAlignCenter()
			tab_icon.SetPosition(5, 0)
			tab_icon.Show()
			self.tab_icon = tab_icon

			self.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverIn)
			self.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOut)

			self.text = None

			self.is_expanded = False
			self.is_mouse_over_in = False
			self.category_index = 0

		def __del__(self):
			ui.Window.__del__(self)

		def SetClippingMaskWindow(self, maskWnd):
			ui.Window.SetClippingMaskWindow(self, maskWnd)
			self.text.SetClippingMaskWindow(maskWnd)

		def __OnMouseOverIn(self):
			self.is_mouse_over_in = True
			self.text.SetFontColorTuple((255, 255, 255, 1))
			if self.is_expanded:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("open_tab_02"))
			else:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("closed_tab_02"))

		def __OnMouseOverOut(self):
			self.is_mouse_over_in = False
			self.text.SetPackedFontColor(colorInfo.FONT_COLOR)
			if self.is_expanded:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("open_tab_01"))
			else:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("closed_tab_01"))

		def Selected(self):
			if self.is_mouse_over_in:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("open_tab_02"))
			else:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("open_tab_01"))
			self.is_expanded = True

		def Deselect(self):
			if self.is_mouse_over_in:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("closed_tab_02"))
			else:
				self.tab_icon.LoadImage(flamewindPath.GetPublic("closed_tab_01"))
			self.is_expanded = False

		def SetText(self, title):
			text = ui.TextLine()
			text.SetParent(self)
			text.SetVerticalAlignCenter()
			text.SetWindowVerticalAlignCenter()
			text.SetLargeFont()
			text.SetBold()
			text.SetText(title)
			text.SetPosition(25, 0)
			text.Show()
			self.text = text

	FILTER_OPTIONS = [localeInfo.CRAFTING_FILTER_ALL, localeInfo.CRAFTING_FILTER_AVAILABLE, localeInfo.CRAFTING_FILTER_NOT_AVAILABLE]
	FILTER_TYPE_ALL = 0
	FILTER_TYPE_AVAILABLE = 1
	FILTER_TYPE_NOT_AVAILABLE = 2

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.toolTipItem = None
		self.current_data = None
		self.tabButtonsDict = {}
		self.categoryButtonsDict = {}
		self.crafting_category_data = {}
		self.crafting_data = {}
		self.material_items = []
		self.current_crafting_vnum = 0
		self.current_crafting_index = 0
		self.itemSize = 0
		self.filter_type = self.FILTER_TYPE_ALL
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def SoftDestroy(self):
		for i,v in self.categoryButtonsDict.items():
			v.Hide()

		for i,v in self.tabButtonsDict.items():
			v.Hide()

		self.categoryButtonsDict = {}
		self.tabButtonsDict = {}

	def Destroy(self):
		self.toolTipItem = None
		self.tabButtonsDict = None
		self.categoryButtonsDict = None
		self.current_data = None
		self.crafting_category_data = {}
		self.crafting_data = {}

	def SetItemToolTip(self, itemToolTip):
		self.toolTipItem = itemToolTip

	def __LoadWindow(self):

		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "UIScript/CraftingWindow.py")

		try:
			self.board = self.GetChild("board")
			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.Close))
			self.itemListMask = self.GetChild("ItemListMask")
			self.itemListContent = self.GetChild("ItemListContent")
			self.recipeMask = self.GetChild("RecipeMask")
			self.recipeContent = self.GetChild("RecipeContent")
			self.priceLabel = self.GetChild("Price")
			self.chanceLabel = self.GetChild("Chance")
			self.craftButton = self.GetChild("CraftButton")
			self.itemNameLabel = self.GetChild("ItemName")
			self.itemSlot = self.GetChild("ItemSlot")
			self.itemSlot2 = self.GetChild("ItemSlot2")
			self.itemSlotCover = self.GetChild("ItemSlotCover")
			self.itemSlotCover2 = self.GetChild("ItemSlotCover2")
			self.itemIcon = self.GetChild("ItemIcon")
			self.filterBox = self.GetChild("FilterBox")
			self.infoLabel = self.GetChild("Information")
			self.searchInput = self.GetChild("SearchInput")
			self.quantityInput = self.GetChild("QuantityInput")

			self.craftButton.SAFE_SetEvent(self.__OnCraftingButton)

			self.searchInput.OnIMEUpdate = ui.__mem_func__(self.__OnSearchValueUpdate)

			self.itemListScrollBar = self.GetChild("ItemListScrollBar")
			self.recipeScrollBar = self.GetChild("RecipeScrollBar")

			self.itemListScrollBar.SetScrollContent(self.itemListMask, self.itemListContent)
			self.itemListScrollBar.SAFE_SetOnWheelEvent(self.itemListContent)

			self.recipeScrollBar.SetScrollContent(self.recipeMask, self.recipeContent)
			self.recipeScrollBar.SAFE_SetOnWheelEvent(self.recipeContent)

			self.itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.__OnMouseOverInItemIcon)
			self.itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.__OnMouseOverOutItemIcon)

			for item in [self.itemSlot, self.itemSlot2, self.itemIcon, self.itemNameLabel, self.itemSlotCover, self.itemSlotCover2]:
				item.SetClippingMaskWindow(self.recipeMask)

			for i in range(len(self.FILTER_OPTIONS)):
				self.filterBox.InsertItem(i, self.FILTER_OPTIONS[i])

			self.filterBox.SAFE_SetEvent(self.__FilterBoxSelect)
			self.filterBox.SelectItem(0)

		except:
			import exception
			exception.Abort("MessengerWindow.__LoadWindow.__Bind")

	def __OnSearchValueUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchInput)
		itemSearch = self.searchInput.GetText()

		itemList = []
		if len(itemSearch) > 0:
			itemList = search_similar(itemSearch, self.crafting_data)
		else:
			self.__AssignItemsToCategories()
			self.__RefreshItemList()

		item_view_dict = {}
		for i in itemList:
			item_view_dict[i] = self.crafting_data[i]

		self.__AssignItemsToCategories(item_view_dict)
		self.__RefreshItemList()


	def __FilterBoxSelect(self, filter_option_index):
		self.filterBox.SetCurrentItem(self.FILTER_OPTIONS[filter_option_index])
		self.filter_type = filter_option_index
		self.__AssignItemsToCategories()
		self.__RefreshItemList()

	def __RefreshItemList(self):
		start_position = 5
		last_item_position = start_position

		before_pos_height = self.itemListScrollBar.GetPos() * (self.itemListContent.GetHeight() - self.itemListMask.GetHeight())

		item_count = 0
		for cat_key, cat_button in self.categoryButtonsDict.items():
			item_list = self.crafting_category_data[cat_key]["items"]
			if len(item_list) < 1:
				cat_button.Hide()
				continue
			else:
				cat_button.Show()
				item_count += 1

			cat_button.SetPosition(3, last_item_position)
			last_item_position += cat_button.GetHeight()
			for item_key in item_list:
				item_button = self.tabButtonsDict[item_key]
				if cat_button.is_expanded:
					item_button.Show()
					item_button.SetPosition(3, last_item_position)
					last_item_position += item_button.GetHeight()
					item_count += 1
				else:
					item_button.Hide()

		dest_height = max(last_item_position+5, self.itemListMask.GetHeight())
		self.itemListContent.SetHeight(dest_height)
		self.itemListContent.SetPosition(0, 0)
		self.itemListScrollBar.ResizeScrollBar()

		scroll_height = dest_height - self.itemListMask.GetHeight()
		if scroll_height > 0 and item_count > 0:
			average_item_height = (dest_height / item_count)*1.5
			self.itemListScrollBar.SetScrollStep(float(average_item_height) / scroll_height)
			print "scroll_height %d item_count %d scrollstep %f" % (scroll_height, item_count, self.itemListScrollBar.scrollStep)

			self.itemListScrollBar.SetPos(before_pos_height / scroll_height)


	def __CreateCategories(self):

		for key, value in self.crafting_category_data.items():
			self.AddListCategory(value["name"], key)

	def __CreateItems(self):
		for key, value in self.crafting_data.items():
			self.AddListItem(key)

	def __CanAddItemToCategory(self, craft_vnum, item_data, category_data):
		if not category_data.has_key("filters"):
			return True

		filter = category_data["filters"]
		require_craft_vnum = filter.has_key("craft_vnum")
		require_item_vnum = filter.has_key("item_vnum")
		require_item_type = filter.has_key("item_type")
		require_item_sub_type = filter.has_key("item_subtype")
		require_item_anti_flag = filter.has_key("antiflag")
		require_item_value = filter.has_key("item_value")


		item_vnum = item_data["item_vnum"]
		item.SelectItem(item_vnum)

		if require_item_type and filter["item_type"] != item.GetItemType():
			return False

		if require_item_sub_type and filter["item_subtype"] != item.GetItemSubType():
			return False

		if require_item_anti_flag and not item.IsAntiFlag(filter["antiflag"]):
			return False

		if require_item_value and item.GetValue(filter["item_value"][0]) != filter["item_value"][1]:
			return False

		if require_item_vnum and item_vnum not in filter["item_vnum"]:
			return False

		if require_craft_vnum and craft_vnum not in filter["craft_vnum"]:
			return False

		return True

	def __AssignItemsToCategories(self, custom_crafting_data=None):
		if not custom_crafting_data:
			custom_crafting_data = self.crafting_data

		for item_key, item_value in self.crafting_data.items():
			self.tabButtonsDict[item_key].Hide()

		for cat_key, cat_value in self.crafting_category_data.items():
			cat_value["items"] = []

		for item_key, item_value in custom_crafting_data.items():
			if self.filter_type != self.FILTER_TYPE_ALL:
				is_available = item_value["is_available"]
				if is_available and self.filter_type != self.FILTER_TYPE_AVAILABLE:
					continue
				elif not is_available and self.filter_type != self.FILTER_TYPE_NOT_AVAILABLE:
					continue

			for cat_key, cat_value in self.crafting_category_data.items():
				if self.__CanAddItemToCategory(item_key, item_value, cat_value):
					cat_value["items"].append(item_key)
					break

		def sort_by_availability(item_key):
			return not custom_crafting_data[item_key]['is_available']

		for cat_key, cat_value in self.crafting_category_data.items():
			cat_value["items"] = sorted(cat_value["items"], key=sort_by_availability)

	def AddListCategory(self, name, category_index):
		btn = self.CategoryButton()
		btn.category_index = category_index
		btn.SetParent(self.itemListContent)
		btn.SetText(name)
		btn.SAFE_SetStringEvent("MOUSE_LEFT_BUTTON_UP", self.__OnCategoryClick, category_index)
		btn.Show()
		btn.SetClippingMaskWindow(self.itemListMask)
		btn.Selected()
		self.categoryButtonsDict[category_index] = btn

	def __GetTotalCraftingCount(self, item_index):
		crafting_data = self.crafting_data[item_index]
		total_craft_count = -1
		price_per_item = crafting_data["price"]
		for i in range(0, len(crafting_data["recipe"]), 2):
			item_vnum_data = crafting_data["recipe"][i]
			item_count = crafting_data["recipe"][i+1]

			inventory_count = 0
			if isinstance(item_vnum_data, tuple):
				for vnum in item_vnum_data:
					inventory_count += utils.CountItemCountInInventory(vnum)
			else:
				inventory_count = utils.CountItemCountInInventory(item_vnum_data)
			possible_craft_count = inventory_count / item_count
			if total_craft_count < 0:
				total_craft_count = possible_craft_count
			else:
				total_craft_count = min(total_craft_count, possible_craft_count)

		x = 1
		if price_per_item > 0:
			player_money = player.GetMoney()
			x = int(player_money / price_per_item)

		total_craft_count = min(total_craft_count, x)

		return total_craft_count

	def UpdateAllListItem(self):
		for i in self.tabButtonsDict.iterkeys():
			self.UpdateListItem(i)

	def UpdateListItem(self, item_index, update_materials=True):
		crafting_data = self.crafting_data[item_index]
		item.SelectItem(crafting_data["item_vnum"])

		name = item.GetItemName()
		btn = self.tabButtonsDict[item_index]
		if self.crafting_data[item_index]["is_available"]:
			total_craft_count = self.__GetTotalCraftingCount(item_index)
			if total_craft_count > 0:
				btn.SetText("%s [%d]" % (name, total_craft_count), colorInfo.FONT_COLOR)
				btn.max_quantity = total_craft_count
			else:
				btn.SetText(name, colorInfo.DISABLED_FONT_COLOR)
		else:
			btn.SetText(name, colorInfo.NEGATIVE_COLOR)

		if update_materials:
			for i in self.material_items:
				if i.IsShow():
					i.Update()

	def AddListItem(self, item_index):
		btn = self.TabButton()
		btn.item_index = item_index
		btn.SetParent(self.itemListContent)
		btn.SAFE_SetStringEvent("MOUSE_LEFT_BUTTON_UP", self.__OnTabButtonClick, item_index)
		btn.Show()
		btn.SetClippingMaskWindow(self.itemListMask)
		self.tabButtonsDict[item_index] = btn
		self.UpdateListItem(item_index, False)


	def SetInfo(self, text, is_red=False):
		self.infoLabel.SetText(text)
		color = colorInfo.FONT_COLOR
		if is_red:
			color = colorInfo.NEGATIVE_COLOR
		self.infoLabel.SetPackedFontColor(color)

	def GetQuantity(self):
		if self.tabButtonsDict.has_key(self.current_crafting_index):
			tab = self.tabButtonsDict[self.current_crafting_index]

			inputText = self.quantityInput.GetText()
			if len(inputText) > 0:
				return min(int(inputText), tab.max_quantity)
			else:
				return 1

	def __OnCraftingButton(self):
		net.SendChatPacket("/craft create %d %d" % (self.current_crafting_index, self.GetQuantity()))

	def __OnCategoryClick(self, category_index):
		btn = self.categoryButtonsDict[category_index]
		if btn.is_expanded:
			btn.Deselect()
		else:
			btn.Selected()

		self.__RefreshItemList()

	def __OnTabButtonClick(self, item_index):
		for i in self.tabButtonsDict.itervalues():
			i.Deselect()

		btn = self.tabButtonsDict[item_index]
		btn.Selected()
		self.SelectItem(item_index)

	def SelectItem(self, crafting_index):
		self.quantityInput.SetText("")
		if crafting_index > 0:
			data = self.crafting_data[crafting_index]
			if not data["is_available"]:
				self.__HideRecipe()
				if data.has_key("requirements"):
					if data["requirements"].has_key("min_level") and data["requirements"]["min_level"] > player.GetStatus(player.LEVEL):
						self.SetInfo(localeInfo.CRAFTING_REQUIRE_LEVEL % data["requirements"]["min_level"])
					elif data["requirements"].has_key("recipe_progress"):
						req_data = data["requirements"]["recipe_progress"]
						self.SetInfo(localeInfo.CRAFTING_REQUIRE_RECIPE % (req_data[0], req_data[1]))
				else:
					self.SetInfo(localeInfo.CRAFTING_ITEM_NOT_AVAILABLE)
				return

			self.__SetItem(data["item_vnum"], data["count"])
			self.__SetPrice(data["price"])
			self.__SetChance(data["chance"])
			self.__SetMaterials(data["recipe"])
			self.current_data = data
			self.current_crafting_index = crafting_index
			self.infoLabel.Hide()

			if not gameSettings.GetBoolKey("attr_change_craft") and crafting_index == 100: # zmianka
				eventManager.EventManager().send_event(uiCommon.POPUP_EVENT, localeInfo.CRAFTING_ATTR_CHANGER_INFO)
				gameSettings.SetKey("attr_change_craft", True)

		else:
			self.__HideRecipe()
			self.SetInfo(localeInfo.CRAFTING_SELECT_ITEM)

	def __HideRecipe(self):
		self.__SetPrice(0)
		self.__SetChance(0)
		self.__SetItem(0)
		self.__SetMaterials(())
		self.infoLabel.Show()
		self.current_crafting_index = 0

	def __SetItem(self, item_vnum, item_count=1):
		if item_vnum > 0:
			item.SelectItem(item_vnum)
			self.__SetItemName(item.GetItemName(), item_count)
			self.itemSize = item.GetItemSize()[1]
			self.itemIcon.LoadImage(item.GetIconImageFileName())
			self.__ShowItemSlot(self.itemSize)
		else:
			self.__HideItemSlot()
			self.__SetItemName("")

	def __ShowItemSlot(self, size):
		self.__HideItemSlot()
		self.itemIcon.Show()
		if size == 2:
			self.itemSlot2.Show()
			self.itemSlotCover2.Show()
		else:
			self.itemSlot.Show()
			self.itemSlotCover.Show()

	def __HideItemSlot(self):
		self.itemSlot.Hide()
		self.itemSlot2.Hide()
		self.itemSlotCover.Hide()
		self.itemSlotCover2.Hide()
		self.itemIcon.Hide()

	def __SetItemName(self, name, count=1):
		if count < 2:
			self.itemNameLabel.SetText(name)
		else:
			self.itemNameLabel.SetText("%dx %s" % (count, name))

	def __SetPrice(self, price):
		self.priceLabel.SetText(localeInfo.NumberToMoneyString(price))

	def __SetChance(self, chance):
		self.chanceLabel.SetText("%d%%" % chance)

	def __SetMaterials(self, material_tuple):
		for i in self.material_items:
			i.Hide()

		base_add_height = 23 + 32 * self.itemSize

		for i in range(0, len(material_tuple), 2):
			item_vnum_data = material_tuple[i]
			item_count = material_tuple[i+1]
			material_item = self.__GetMaterialItem()

			item_vnum = 0
			if isinstance(item_vnum_data, tuple):
				item_vnum = item_vnum_data[len(item_vnum_data) - 1]
			else:
				item_vnum = item_vnum_data

			material_item.SetItem(item_vnum, item_count)
			add_y_pos = 50 * (i / 2)
			material_item.SetPosition(15, base_add_height + add_y_pos)
			material_item.Show()

		total_height = base_add_height + 50 * (len(material_tuple) / 2)
		dest_height = max(total_height, self.recipeMask.GetHeight())
		self.recipeContent.SetHeight(dest_height)
		self.recipeContent.SetPosition(0, 0)
		self.recipeScrollBar.ResizeScrollBar()

	def __GetMaterialItem(self):
		for i in self.material_items:
			if not i.IsShow():
				return i

		item = self.MaterialItem()
		item.SetParent(self.recipeContent)
		item.SetItemToolTip(self.toolTipItem)
		item.SetMask(self.recipeMask)
		self.material_items.append(item)
		return item

	def __OnMouseOverInItemIcon(self):
		if self.toolTipItem:
			self.toolTipItem.ClearToolTip()
			item_vnum = self.current_data["item_vnum"]
			metinSlot = [0 for i in xrange(player.METIN_SOCKET_MAX_NUM)]
			if constInfo.IS_AUTO_POTION(item_vnum):
				metinSlot[1] = 1
			self.toolTipItem.SetRawItem(item_vnum, metinSlot, isClearToolTip=False)
			self.toolTipItem.ShowToolTip()

	def __OnMouseOverOutItemIcon(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

	def Close(self):
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()

		self.Hide()
		net.SendChatPacket("/craft close")
		constInfo.CRAFTING_LOAD_DATA.pop(self.current_crafting_vnum, None)

	# def RequestOpen(self, craft_vnum):
	# 	self.current_crafting_vnum = craft_vnum
	# 	net.SendChatPacket("/craft request")
		# if not constInfo.CRAFTING_LOAD_DATA.has_key(craft_vnum):
		# 	net.SendChatPacket("/craft request item")
		# else:
		# 	net.SendChatPacket("/craft request")

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnCraftUpdate(self):
		self.UpdateAllListItem()
		if self.current_crafting_vnum == 102:
			sounds = ["brewing", "brewing2"]
			number = app.GetRandom(0, 1)
			snd.PlaySound("sound/ui/%s.wav" % (sounds[number]))
		else:
			snd.PlaySound("sound/ui/craft.wav")

	def Open(self):
		self.SoftDestroy()

		if CRAFTING_CATEGORIES_BY_VNUM.has_key(self.current_crafting_vnum):
			self.crafting_category_data = CRAFTING_CATEGORIES_BY_VNUM[self.current_crafting_vnum]
		else:
			self.crafting_category_data = CRAFTING_CATEGORIES_BY_VNUM["default"]
		self.crafting_data = constInfo.CRAFTING_DATA[self.current_crafting_vnum]
		self.__CreateCategories()
		self.__CreateItems()
		self.__AssignItemsToCategories()
		self.__RefreshItemList()
		self.SelectItem(0)

		self.Show()
