import uiScriptLocale
import flamewindPath
import colorInfo

WINDOW_WIDTH = 360
WINDOW_HEIGHT = 510

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "CraftingWindow",

	"x": CENTER_X,
	"y": CENTER_Y,

	"style": ("movable", "float",),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
		(
			{
				"name": "board",
				"type": "board",
				"style": ("attach",),

				"x": 0,
				"y": 0,

				"width": WINDOW_WIDTH,
				"height": WINDOW_HEIGHT,

				"children":
					(
						{
							"name": "TitleBar",
							"type": "titlebar",
							"style": ("attach",),

							"x": 8,
							"y": 8,

							"width": WINDOW_WIDTH - 15,
							"color": "gray",

							"children":
								(
									{"name": "TitleName", "type": "text", "x": -4, "y": 4,
									 "text": uiScriptLocale.CRAFTING_WINDOW,
									 "horizontal_align": "center", "text_horizontal_align": "center"},
								),
						},

						{
							"type": "slotbar",

							"x": 12,
							"y": 30,

							"width": 215,
							"height": 20,

							"children": (
								{
									"name": "SearchInput",
									"type": "editline",
									"x": 2,
									"y": 3,

									"width": 208,
									"height": 18,
									"input_limit": 24,
									"placeholder": uiScriptLocale.SEARCH_ITEM,
								},
							),
						},
						{
							"type": "board",

							"skin": "a",

							"x": 0,
							"y": 52,

							"horizontal_align": "center",

							"width": WINDOW_WIDTH - 20,
							"height": 220,

							"children": (
								{
									"name" : "ItemListMask",
									"type" : "window",
									"x": 1, "y" : 1,
									"width" : WINDOW_WIDTH - 20 - 2,
									"height" : 220 - 2,
								},
								{
									"name" : "ItemListContent",
									"type" : "window",
									"x": 1, "y" : 1,
									"width" : WINDOW_WIDTH - 20 - 2,
									"height" : 220 - 2,
								},
								{
									"name" : "ItemListScrollBar",
									"type": "scrollbar",
									"x": 22,
									"y": 0,

									"horizontal_align": "right",
									"vertical_align": "center",

									"size": 204,
								},
							),
						},

						{
							"name" : "FilterBox",
							"type": "combobox",
							"x": 230,
							"y": 30,

							"width": 117,
							"height": 20,
							"default_text": "Filtruj",

							"item": {},
						},

						{
							"type": "board",

							"skin": "a",

							"x": 0,
							"y": 268,

							"horizontal_align": "center",

							"width": WINDOW_WIDTH - 20,
							"height": 212,

							"children": (
								{
									"name" : "RecipeMask",
									"type" : "window",
									"x": 1, "y" : 2,
									"width" : WINDOW_WIDTH - 20 - 2,
									"height" : 212 - 6,
								},
								{
									"name" : "RecipeContent",
									"type" : "window",
									"x": 0, "y" : 0,
									"width" : WINDOW_WIDTH - 20,
									"height" : 212,

									"children" : (
										{
											"name" : "ItemSlot",
											"type": "image",
											"x": 15, "y": 15,
											"image": "d:/ymir work/ui/public/slot_base.sub",
										},
										{
											"name": "ItemSlot2",
											"type": "image",
											"x": 15, "y": 32,
											"image": "d:/ymir work/ui/public/slot_base.sub",
										},
										{
											"name" : "ItemIcon",

											"type" : "image",
											"x" : 15, "y": 15,
											"image" : "icon/item/71095.tga",
										},

										{
											"name" : "ItemSlotCover",
											"style" : ("not_pick",),
											"type": "image",
											"x": 15, "y": 15,
											"image": "d:/ymir work/ui/public/slot_cover_button_02.sub",
										},
										{
											"name": "ItemSlotCover2",
											"style": ("not_pick",),
											"type": "image",
											"x": 15, "y": 15,
											"image": flamewindPath.GetPublic("2slot_cover"),
										},

										{
											"name" : "ItemName",
											"type": "text",
											"x": 57, "y": 15+16,
											"text_vertical_align": "center",
											"text": "ITEM_NAME",
											"fontsize": "LARGE",
											"bold": True,
										},
									),
								},

								{
									"name" : "RecipeScrollBar",
									"type": "scrollbar",
									"x": 22,
									"y": 0,

									"horizontal_align": "right",
									"vertical_align": "center",

									"size": 204,
								},
								# {
								# 	"name": "MaterialBar",
								# 	"type": "thinboard",
								#
								# 	"x": 15,
								# 	"y": 55,
								#
								# 	"width": 200,
								# 	"height": 46,
								#
								# 	"children": (
								# 		{
								# 			"type": "image",
								# 			"x": 10, "y": 0,
								# 			"vertical_align": "center",
								# 			"image": "d:/ymir work/ui/public/slot_base.sub",
								# 		},
								#
								# 		{
								# 			"type": "text",
								# 			"x": 48, "y": 0,
								# 			"vertical_align": "center",
								# 			"text_vertical_align": "center",
								# 			"text": "MATERIAL_NAME",
								# 		},
								# 	),
								# },
								{
									"name" : "Information",
									"type": "text",
									"x": 0, "y": 0,
									"all_align": "center",
									"text": "INFORMATION",
								},
							),
						},

						{
							"type": "slotbar",

							"x": 213,
							"y": 30,

							"width": 110,
							"height": 20,

							"horizontal_align": "right",
							"vertical_align": "bottom",

							"children": (
								{
									"name": "Price",
									"type": "text",
									"x": 0,
									"y": 0,

									"vertical_align": "center",
									"text_vertical_align": "center",
									"horizontal_align": "center",
									"text_horizontal_align": "center",

									"text": "9.999.999.999 Yang",
								},
							),
						},

						{
							"type": "slotbar",

							"x": 256,
							"y": 30,

							"width": 40,
							"height": 20,

							"horizontal_align": "right",
							"vertical_align": "bottom",

							"children": (
								{
									"name": "Chance",
									"type": "text",
									"x": 0,
									"y": 0,

									"vertical_align": "center",
									"text_vertical_align": "center",
									"horizontal_align": "center",
									"text_horizontal_align": "center",

									"text": "100%",
								},
							),
						},

						{
							"type": "slotbar",

							"x": 290,
							"y": 30,

							"width": 30,
							"height": 20,

							"horizontal_align": "right",
							"vertical_align": "bottom",

							"children": (
								{
									"name": "QuantityInput",
									"type": "editline",
									"x": 3,
									"y": 4,

									"width": 38,
									"height": 18,
									"input_limit": 2,
									"only_number" : True,
									"placeholder": uiScriptLocale.CRAFT_QUANTITY,
								},
							),
						},

						{
							"name": "CraftButton",
							"type": "button",

							"x": 98,
							"y": 30,

							"horizontal_align": "right",
							"vertical_align": "bottom",

							"text": uiScriptLocale.CRAFT,

							"default_image": "d:/ymir work/ui/public/large_button_01.sub",
							"over_image": "d:/ymir work/ui/public/large_button_02.sub",
							"down_image": "d:/ymir work/ui/public/large_button_03.sub",
						},
					),
			},
		),
}