import uiScriptLocale

WINDOW_WIDTH = 448 + 164
WINDOW_HEIGHT = 400

window = {
	"name": "ShopSearchWindow",

	"x": SCREEN_WIDTH - 213 - WINDOW_WIDTH,
	"y": 90,

	"style": ("float", "movable",),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
		(
			{
				"type": "board",

				"x": 0,
				"y": 0,

				"style": ("attach",),

				"width": WINDOW_WIDTH,
				"height": WINDOW_HEIGHT,

				"children": (
					## Title
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
								{"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": uiScriptLocale.SHOP_SEARCH_TITLE,
								 "horizontal_align": "center", "text_horizontal_align": "center"},
							),
					},

					{
						"name": "CategoryList",
						"type": "board",

						"x": 12,
						"y": 33,

						"style": ("attach",),

						"skin": "a",

						"width": 166,
						"height": WINDOW_HEIGHT - 43,

						"children": (
							{
								"name": "CategoryMask",
								"type": "window",
								"x": 3,
								"y": 3,
								"width": 166 - 6,
								"height": WINDOW_HEIGHT - 43 - 6,
								"children": (
									{
										"name": "CategoryContent",
										"type": "window",
										"x": 0,
										"y": 0,
										"width": 160,
										"height": 1,
									},
								),
							},
						),
					},

					{
						"name": "SubCategoryList",
						"type": "board",

						"x": 12+188,
						"y": 33,

						"style": ("attach",),

						"skin": "a",

						"width": 166,
						"height": WINDOW_HEIGHT - 43,

						"children": (
							{
								"name": "SubCategoryMask",
								"type": "window",
								"x": 3,
								"y": 3,
								"width": 166 - 6,
								"height": WINDOW_HEIGHT - 43 - 6,
								"children": (
									{
										"name": "SubCategoryContent",
										"type": "window",
										"x": 0,
										"y": 0,
										"width": 160,
										"height": 1,
									},
								),
							},
						),
					},

					{
						"name": "Scrollbar",
						"type": "scrollbar",
						"x": 179,
						"y": 34,

						"size": 356,
					},

					{
						"name": "SubScrollbar",
						"type": "scrollbar",
						"x": 368,
						"y": 34,

						"size": 356,
					},

					{
						"name": "ItemList",
						"type": "board",

						"x": 330+60,
						"y": 33,

						"style": ("attach",),

						"skin": "a",

						"width": 204,
						"height": WINDOW_HEIGHT - 43 - 25,
						"children": (
							{
								"name": "ItemSlot",
								"type": "grid_table",
								"x": 6,
								"y": 5,
								"start_index": 0,
								"x_count": 6,
								"y_count": 10,
								"x_step": 32,
								"y_step": 32,

								"image": "d:/ymir work/ui/public/Slot_Base.sub"
							},

							{
								"name": "SearchAttrToggle",
								"type": "toggle_button",

								"x": 15,
								"y": 15,

								"text": uiScriptLocale.SHOP_SEARCH_ATTR,

								"default_image": "d:/ymir work/ui/public/large_button_01.sub",
								"over_image": "d:/ymir work/ui/public/large_button_02.sub",
								"down_image": "d:/ymir work/ui/public/large_button_03.sub",
							},

							{
								"name": "InfoLabel",
								"type" : "text",
								"x": 0, "y": 0,

								"all_align": "center",

								"text": "",
								"bold": True,
								"color": 0xffe3d7b1,
							},
						),
					},

					{
						"name": "SearchButton",
						"type": "button",

						"x": 255+ 164,
						"y": 31,

						"text": uiScriptLocale.SHOP_SEARCH,
						"vertical_align": "bottom",

						"default_image": "d:/ymir work/ui/public/large_button_01.sub",
						"over_image": "d:/ymir work/ui/public/large_button_02.sub",
						"down_image": "d:/ymir work/ui/public/large_button_03.sub",
					},

					{
						"name": "ClearButton",
						"type": "button",

						"x": 347 + 164,
						"y": 31,

						"text": uiScriptLocale.SHOP_SEARCH_CLEAR,
						"vertical_align": "bottom",

						"default_image": "d:/ymir work/ui/public/large_button_01.sub",
						"over_image": "d:/ymir work/ui/public/large_button_02.sub",
						"down_image": "d:/ymir work/ui/public/large_button_03.sub",
					},
				),
			},
		),
}