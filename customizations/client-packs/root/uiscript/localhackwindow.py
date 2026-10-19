import uiScriptLocale

WINDOW_WIDTH = 110
WINDOW_HEIGHT = 190

window = {
	"name": "LocalHackWindow",

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
									{"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": "hack",
									 "horizontal_align": "center", "text_horizontal_align": "center"},
								),
						},

						{
							# "name": "DurationSlot",
							"type": "slotbar",
							"x": 0,
							"y": 50,

							"horizontal_align": "center",

							"width": 60,
							"height": 18,

							"children":
								(
									{
										"type": "text",
										"x": 0,
										"y": -15,

										"horizontal_align": "center",
										"text_horizontal_align": "center",
										"text": "Target",
									},

									{
										"name": "TargetCount",
										"type": "text",
										"x": 3,
										"y": 3,
										"text": "123456",
									},
								),
						},

						{
							"name": "WHButton",
							"type": "button",

							"x": -23,
							"y": 73,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "WaitHack",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"name": "RWHButton",
							"type": "button",

							"x": 23,
							"y": 73,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "RWaitHack",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"name": "UpButton",
							"type": "button",

							"x": -20,
							"y": 43,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Gora",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"name": "SpeedAttackButton",
							"type": "button",

							"x": -20,
							"y": 23,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "SpeedAttack",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"name": "SpeedMoveButton",
							"type": "button",

							"x": 20,
							"y": 23,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "SpeedMove",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},
					),
			},
		),
}