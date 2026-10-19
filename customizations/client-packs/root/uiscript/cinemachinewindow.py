import uiScriptLocale

WINDOW_WIDTH = 110
WINDOW_HEIGHT = 160

window = {
	"name": "CinemachineWindow",

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
									{"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": "Cinemachine",
									 "horizontal_align": "center", "text_horizontal_align": "center"},
								),
						},

						{
							"name": "DurationSlot",
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
										"text": "Duration",
									},

									{
										"name": "DurationLine",
										"type": "editline",
										"x": 3,
										"y": 3,
										"width": 57,
										"height": 15,
										"input_limit": 4,
									},
								),
						},

						{
							"type": "text",

							"x": 0,
							"y": 88,

							"horizontal_align": "center",
							"text_horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Camera Mode",
						},

						{
							"name": "LinearModeButton",
							"type": "button",

							"x": -20,
							"y": 73,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Linear",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"name": "BezierModeButton",
							"type": "button",

							"x": 20,
							"y": 73,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Bezier",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"type": "text",

							"x": 0,
							"y": 48,

							"horizontal_align": "center",
							"text_horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Rotation Mode",
						},

						{
							"name": "LinearRotationModeButton",
							"type": "button",

							"x": -20,
							"y": 33,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Linear",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},

						{
							"name": "BezierRotationModeButton",
							"type": "button",

							"x": 20,
							"y": 33,

							"horizontal_align": "center",
							"vertical_align": "bottom",

							"text": "Bezier",

							"default_image": "d:/ymir work/ui/public/small_button_01.sub",
							"over_image": "d:/ymir work/ui/public/small_button_02.sub",
							"down_image": "d:/ymir work/ui/public/small_button_03.sub",
						},
					),
			},
		),
}