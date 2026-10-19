import uiScriptLocale
import flamewindPath

WINDOW_WIDTH = 290
WINDOW_HEIGHT = 220

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "PotionRechargeDialog",

	"x": CENTER_X,
	"y": CENTER_Y,

	"style": ("movable", "float",),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
		(
			{
				"name" : "Board",
				"type": "board",

				"x": 0,
				"y": 0,

				"style": ("attach",),

				"width": WINDOW_WIDTH,
				"height": WINDOW_HEIGHT,

				"children": (
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
								{
									"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": uiScriptLocale.POTION_RECHARGE_TITLE,
									"horizontal_align": "center", "text_horizontal_align": "center"
								},
							),
					},

					{
						"name": "ItemSlot",
						"type": "grid_table",

						"x": 15+132,
						"y": 35,

						"start_index": 0,
						"x_count": 4,
						"y_count": 4,
						"x_step": 32,
						"y_step": 32,

						"image": "d:/ymir work/ui/public/Slot_Base.sub"
					},

					{
						"type": "image",

						"x": 15,
						"y": 35,

						"image": flamewindPath.GetWindows("brew_bg"),

						"children": (
							{
								"name": "PotionItemSlot",
								"type": "slot",

								"x": 48,
								"y": 48,

								"width" : 32,
								"height" : 32,

								"slot" : (
										{"index":0, "x":0, "y":0, "width":32, "height":32},
									),

								"image": "d:/ymir work/ui/public/Slot_Base.sub",
								"children" : (
									{
										"type": "text",
										"text": "Miejsce na eliksir",
										"x": 0, "y": 0,
										"text_horizontal_align": "center",
										"horizontal_align": "center",
										"vertical_align": "bottom",
									},
								),
							},
						),
					},
					{
						"name": "BrewProgressBg",
						"type": "image",

						"x": 0,
						"y": 35+128+6,

						"horizontal_align": "center",

						"image": flamewindPath.GetWindows("brew_progress"),
						"children" : (
							{
								"name" : "RecoveryGaugeBar",
								"type" : "bar",

								"x" : 6,
								"y" : 0,
								"width" : 248,
								"height" : 11,
								"color" : 0x550000ff,
							},

							{
								"name" : "SPGauge",
								"type" : "ani_image",

								"x" : 6,
								"y" : 0,

								"delay" : 6,

								"images" :
								(
									"D:/Ymir Work/UI/Pattern/SPGauge/01.tga",
									"D:/Ymir Work/UI/Pattern/SPGauge/02.tga",
									"D:/Ymir Work/UI/Pattern/SPGauge/03.tga",
									"D:/Ymir Work/UI/Pattern/SPGauge/04.tga",
									"D:/Ymir Work/UI/Pattern/SPGauge/05.tga",
									"D:/Ymir Work/UI/Pattern/SPGauge/06.tga",
									"D:/Ymir Work/UI/Pattern/SPGauge/07.tga",
								),
							},

							{
								"name" : "HPGauge",
								"type" : "ani_image",

								"x" : 6,
								"y" : 0,

								"delay" : 6,

								"images" :
								(
									"D:/Ymir Work/UI/Pattern/HPGauge/01.tga",
									"D:/Ymir Work/UI/Pattern/HPGauge/02.tga",
									"D:/Ymir Work/UI/Pattern/HPGauge/03.tga",
									"D:/Ymir Work/UI/Pattern/HPGauge/04.tga",
									"D:/Ymir Work/UI/Pattern/HPGauge/05.tga",
									"D:/Ymir Work/UI/Pattern/HPGauge/06.tga",
									"D:/Ymir Work/UI/Pattern/HPGauge/07.tga",
								),
							},

							{
								"name": "RechargeValue",
								"type": "text",
								"text": "6.000.000/10.000.000 (99,99%)",
								"x": 0, "y": 0,
								"all_align": "center",
								"outline": True,
							},
						),
					},

					{
						"name": "AcceptButton",
						"type": "button",

						"x": 0,
						"y": 31,

						"horizontal_align": "center",
						"vertical_align": "bottom",

						# "tooltip_text": uiScriptLocale.POTION_RECHARGE_BUTTON_TOOLTIP,

						"default_image": flamewindPath.GetPublic("accept_button_01"),
						"over_image": flamewindPath.GetPublic("accept_button_02"),
						"down_image": flamewindPath.GetPublic("accept_button_03"),
					},
				),
			},
		),
}