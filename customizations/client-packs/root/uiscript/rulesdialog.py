import uiScriptLocale
WINDOW_WIDTH = 402
WINDOW_HEIGHT = 500

CONTENT_WIDTH = WINDOW_WIDTH - 42
CONTENT_HEIGHT = WINDOW_HEIGHT - 70

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "RulesDialog",

	"x": 0,
	"y": 0,

	"style": ("float",),

	"width": SCREEN_WIDTH,
	"height": SCREEN_HEIGHT,

	"children":
		(
			{
				"type": "bar",
				"x": 0,
				"y": 0,
				"color": 0xcc000000,
				"width": SCREEN_WIDTH,
				"height": SCREEN_HEIGHT,
			},
			{
				"type": "board",

				"x": 0,
				"y": 0,

				"horizontal_align" : "center",
				"vertical_align" : "center",

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
									"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": uiScriptLocale.RULES_TITLE,
									"horizontal_align": "center", "text_horizontal_align": "center"
								},
							),
					},
					{
						"name": "ScrollBar",
						"type": "scrollbar",
						"x": 26, "y": 32,
						"size": CONTENT_HEIGHT,
						"horizontal_align": "right",
					},

					{
						"type": "slotbar",
						"x": 12, "y": 32,
						"width": CONTENT_WIDTH,
						"height": CONTENT_HEIGHT,
						"children": (
							{
								"name": "ContentMask",
								"type": "window",
								"x": 1, "y": 1,
								"width": CONTENT_WIDTH - 2,
								"height": CONTENT_HEIGHT - 2,

								"children": (
									{
										"name": "Content",
										"type": "window",
										# "x": 4, "y": 3,
										"x": 0, "y": 0,
										"width" : CONTENT_WIDTH-2,
										"height" : CONTENT_HEIGHT - 2,
									},
								),
							},
						),
					},

					{
						"name": "AcceptButton",
						"type": "button",

						"x": 0,
						"y": 34,

						"horizontal_align": "center",
						"vertical_align": "bottom",

						"text": uiScriptLocale.ACCEPT_RULES,

						"default_image": "d:/ymir work/ui/public/xlarge_button_01.sub",
						"over_image": "d:/ymir work/ui/public/xlarge_button_02.sub",
						"down_image": "d:/ymir work/ui/public/xlarge_button_03.sub",
					},
				),
			},
		),
}