import uiScriptLocale
import shop
import grp
import flamewindPath

WINDOW_WIDTH = 344
WINDOW_HEIGHT = 354 + 26 * 2

window = {
	"name": "PrivateShopBuilder",

	"x": 0,
	"y": 0,

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
									{"name": "TitleName", "type": "text", "x": -4, "y": 4,
									 "text": uiScriptLocale.PRIVATE_SHOP_TITLE, "horizontal_align": "center",
									 "text_horizontal_align": "center"},
								),
						},

						## Name
						{
							"name": "NameSlot",
							"type": "slotbar",
							"x": 0,
							"y": 35,

							"horizontal_align": "center",

							"width": WINDOW_WIDTH - 27,
							"height": 18,

							"children":
								(
									{
										"name": "ShopSignEditLine",
										"type": "editline",
										"x": 3,
										"y": 3,
										"width": WINDOW_WIDTH - 30,
										"height": 15,
										"input_limit": 32,
										"placeholder" : "Podaj nazwe sklepu...",
									},
								),
						},

						## Item Slot
						# {
						# 	"name": "ItemSlot",
						# 	"type": "grid_table",
						#
						# 	"x": 12,
						# 	"y": 34 + 26,
						#
						# 	"start_index": 0,
						# 	"x_count": shop.SHOP_PLAYER_WIDTH,
						# 	"y_count": shop.SHOP_PLAYER_HEIGHT,
						# 	"x_step": 32,
						# 	"y_step": 32,
						#
						# 	"image": "d:/ymir work/ui/public/Slot_Base.sub",
						# },

						## Name
						{
							"name": "TotalEarningBar",
							"type": "slotbar",
							"x": 0,
							"y": 35 + 25 + 26,

							"horizontal_align": "center",

							"vertical_align": "bottom",

							"width": 108 + 54,
							"height": 19,

							"children":
								(
									{
										"name": "TotalEarningLabel",
										"type": "text",
										"x": 0,
										"y": 3,
										"text_horizontal_align": "center",
										"horizontal_align": "center",
										"text": "20.000.000.000 Yang",
									},

									{
										"name": "Money_Icon",
										"type": "image",

										"x": -18,
										"y": 3,

										"image": "d:/ymir work/ui/game/windows/money_icon.sub",
									},
								),
						},

						{
							"name": "QuestionMark",
							"type": "image",

							"x": 38+46,
							"y": 35 + 25 + 25,

							"vertical_align": "bottom",
							"horizontal_align" : "right",

							"image": flamewindPath.GetPublic("q_mark_01"),
						},

						# Ok
						{
							"name": "OkButton",
							"type": "button",

							"x": -52,
							"y": 33,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"default_image": flamewindPath.GetPublic("accept_button_01"),
							"over_image": flamewindPath.GetPublic("accept_button_02"),
							"down_image": flamewindPath.GetPublic("accept_button_03"),
						},

						# Close
						{
							"name": "CloseButton",
							"type": "button",

							"x": 52,
							"y": 33,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"default_image": flamewindPath.GetPublic("cancel_button_01"),
							"over_image": flamewindPath.GetPublic("cancel_button_02"),
							"down_image": flamewindPath.GetPublic("cancel_button_03"),
						},

						## TimeSelect
						{
							"name": "TimeSelectBar",
							"type": "combobox",
							"x": 0,
							"y": 35 + 26,

							"horizontal_align": "center",

							# "item": {
							# 	0: {
							# 		"value": "Zwykly Sklep | Cena: 0 Yang",
							# 	},
							#
							# 	1: {
							# 		"value": "3 godz. | Cena: 45.000 Yang",
							# 	},
							# 	2: {
							# 		"value": "6 godz. | Cena: 90.000 Yang",
							# 	},
							#
							# 	3: {
							# 		"value": "8 godz. | Cena: 120.000 Yang",
							# 	},
							#
							# 	4: {
							# 		"value": "12 godz. | Cena: 180.000 Yang",
							# 	},
							# 	5: {
							# 		"value": "* 24 godz. | Cena: 240.000 Yang *",
							# 		"color": grp.GenerateColor(float(225) / 255, float(200) / 255, float(100) / 255,
							# 								   1.0)
							# 	},
							# 	6: {
							# 		"value": "* 48 godz. | Cena: 480.000 Yang *",
							# 		"color": grp.GenerateColor(float(225) / 255, float(200) / 255, float(100) / 255,
							# 								   1.0)
							# 	},
							# 	7: {
							# 		"value": "* 72 godz. | Cena: 720.000 Yang *",
							# 		"color": grp.GenerateColor(float(225) / 255, float(200) / 255, float(100) / 255,
							# 								   1.0)
							# 	},
							# },

							"default_text": uiScriptLocale.SHOP_CREATE_SELECT_DEFAULT,

							"vertical_align": "bottom",

							"width": 108 + 54,
							"height": 19,

							"children": (
								{
									"type": "image",

									"x": -18,
									"y": 1,

									"image": flamewindPath.GetPublic("time_0"),
								},
							),
						},

					),
			},
		),
}