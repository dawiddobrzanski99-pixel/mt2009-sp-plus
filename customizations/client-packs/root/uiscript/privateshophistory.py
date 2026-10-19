import flamewindPath
import uiScriptLocale

WINDOW_WIDTH = 440
WINDOW_HEIGHT = 300

window = {
	"name": "PrivateShopHistory",

	"x": SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y": SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,

	"style": ("movable", "float",),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children": (
		{
			"name": "board",
			"type": "board",
			"style": ("attach",),

			"x": 0,
			"y": 0,

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

					"children": (
						{"name": "TitleName", "type": "text", "x": -4, "y": 4,
						 "text": uiScriptLocale.SHOP_HISTORY_TITLE, "horizontal_align": "center",
						 "text_horizontal_align": "center"},
					),
				},

				{
					"type": "horizontalbar",

					"x": 13,
					"y": 35,
					"width": WINDOW_WIDTH-43,
					"children": (
						{
							"type": "text",
							"x": 6,
							"y": 2,
							"text": uiScriptLocale.SHOP_COLUMN_FIRST,
							"bold": True,
							"color": 0xffe3d4a3,
						},

						{
							"type": "text",
							"x": 300,
							"y": 2,
							"text": uiScriptLocale.SHOP_COLUMN_SECOND,
							"bold": True,
							"color": 0xffe3d4a3,
						},
					),
				},

				{
					"name": "ClearButton",
					"type": "button",

					"x": 30,
					"y": 34,

					"horizontal_align": "right",
					"tooltip_text": uiScriptLocale.SHOP_HISTORY_CLEAR,

					"default_image": flamewindPath.GetPublic("delete_button_01"),
					"over_image": flamewindPath.GetPublic("delete_button_02"),
					"down_image": flamewindPath.GetPublic("delete_button_03"),
				},

				{
					"name": "Mask",
					"type": "window",
					"x": 0,
					"y": 53,
					"horizontal_align": "center",

					"width": WINDOW_WIDTH-30,
					"height": WINDOW_HEIGHT - 35 - 20 - 8,

					"children": (
						{
							"name": "Content",
							"type": "window",

							"x": 0,
							"y": 0,

							"width": WINDOW_WIDTH-30,
							"height": WINDOW_HEIGHT - 35 - 15,
						},
					),
				},

				{
					"name" : "Scroll",
					"type" : "scrollbar",

					"x" : 25,
					"y" : 55,
					"size" : WINDOW_HEIGHT - 35 - 20 - 10,
					"horizontal_align" : "right",
				},
			),
		},
	),
}