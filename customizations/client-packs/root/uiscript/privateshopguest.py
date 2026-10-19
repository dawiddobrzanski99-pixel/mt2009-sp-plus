import flamewindPath
import uiScriptLocale

WINDOW_WIDTH = 344
WINDOW_HEIGHT = 328

window = {
	"name": "PrivateShopGuest",

	"x": SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y": SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,

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
									 "text": "title", "horizontal_align": "center",
									 "text_horizontal_align": "center"},

									{
										"name": "WhisperButton",
										"type": "button",

										"x": 46,
										"y": -1,

										"horizontal_align": "right",
										"vertical_align": "center",
										"tooltip_text": uiScriptLocale.SHOP_OWNER_ONLINE,

										"default_image": flamewindPath.GetPublic("mail_button_connected_01"),
										"over_image": flamewindPath.GetPublic("mail_button_connected_02"),
										"down_image": flamewindPath.GetPublic("mail_button_connected_03"),
									},

									{
										"name": "OfflineOwner",
										"type": "button",

										"x": 46,
										"y": -1,

										"horizontal_align": "right",
										"vertical_align": "center",

										"tooltip_text" : uiScriptLocale.SHOP_OWNER_OFFLINE,
										"default_image" : flamewindPath.GetPublic("mail_button_disconnected_03"),
										"over_image" : flamewindPath.GetPublic("mail_button_disconnected_03"),
										"down_image" : flamewindPath.GetPublic("mail_button_disconnected_03"),
									},
								),
						},
						## TimeSelect
						{
							"name": "TimeBar",
							"type": "slotbar",
							"x": 33,
							"y": 35,

							"vertical_align": "bottom",

							"width": 108,
							"height": 19,

							"children":
								(
									{
										"name": "TimeLeftLabel",
										"type": "text",
										"x": 0,
										"y": 3,
										"text_horizontal_align": "center",
										"horizontal_align": "center",
										"text": "TIME_LABEL",
									},

									{
										"name": "ClockAnimation",
										"type": "ani_image",

										"x": -18, "y": 2,

										"delay": 8,
										"images":
											(
												flamewindPath.GetPublic("time_0"),
												flamewindPath.GetPublic("time_1"),
												flamewindPath.GetPublic("time_2"),
												flamewindPath.GetPublic("time_3"),
												flamewindPath.GetPublic("time_4"),
												flamewindPath.GetPublic("time_5"),
												flamewindPath.GetPublic("time_6"),
												flamewindPath.GetPublic("time_7"),
											)
									},
								),
						},

						{
							"name": "CloseNormalShopButton",
							"type": "button",

							"x": 0,
							"y": 35,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text" : uiScriptLocale.PRIVATE_SHOP_CLOSE_BUTTON,

							"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
							"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
							"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
						},
					),
			},
		),
}