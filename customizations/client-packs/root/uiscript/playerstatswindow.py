import uiScriptLocale

WINDOW_WIDTH = 302
WINDOW_HEIGHT = 300

CONTENT_WIDTH = WINDOW_WIDTH - 42
CONTENT_HEIGHT = WINDOW_HEIGHT - 70

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "PlayerStatsWindow",

	"x": CENTER_X,
	"y": CENTER_Y,

	"style" : ("movable", "float",),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
	(
		{
			"name": "Board",
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
							"name": "TitleName", "type": "text", "x": -4, "y": 4,
							"text": uiScriptLocale.PLAYER_STATS_TITLE,
							"horizontal_align": "center", "text_horizontal_align": "center"
						},
					),
				},

				{
					"name": "ScrollBar",
					"type": "scrollbar",
					"x": 26, "y": 36,
					"size": WINDOW_WIDTH - 20 - 32,
					"horizontal_align": "right",
				},

				{
					"name": "ContentMask",
					"type": "window",
					"x": 0,
					"y": 32,
					"width": WINDOW_WIDTH-20,
					"height": WINDOW_HEIGHT-32 - 11,
				},

				{
					"type" : "window",
					"x":0,
					"y":32,
					"width" : WINDOW_WIDTH-20,
					"height": WINDOW_HEIGHT - 32,
					"children" : (
						{
							"name": "ContentWindow",
							"type": "window",
							"x": 0,
							"y": 0,
							"width": WINDOW_WIDTH-20,
							"height": 0,
							"children" : (
								{
									"name": "GeneralTitleBar",
									"type": "horizontalbar",
									"x": 8,
									"y": 0,
									"width": WINDOW_WIDTH - 34,
									"children": (
										{
											"type": "text", "x": 4, "y": 0,
											"text": uiScriptLocale.PLAYER_STATS_GENERAL,
											"bold": True,
											"color": 0xffe3cca1,
											"text_vertical_align": "center",
											"vertical_align": "center",
										},
									),
								},
								{
									"name": "SessionTitleBar",
									"type": "horizontalbar",
									"x": 8,
									"y": 20,
									"width": WINDOW_WIDTH - 34,
									"children": (
										{
											"type": "text", "x": 4, "y": 0,
											"text": uiScriptLocale.PLAYER_STATS_CURRENT_SESSION,
											"bold": True,
											"color": 0xffe3cca1,
											"text_vertical_align": "center",
											"vertical_align": "center",
										},

										{
											"name": "SessionTime",
											"type": "text", "x": 26, "y": 0,
											"text": "999d 24h 50m 60s",
											"color": 0xffe3cca1,
											"text_vertical_align": "center",
											"vertical_align": "center",
											"horizontal_align": "right",
											"text_horizontal_align": "right",
										},

										{
											"name": "ResetButton",
											"type": "button",

											"x": 22,
											"y": 0,

											"horizontal_align": "right",
											"vertical_align": "center",

											"tooltip_text": uiScriptLocale.PLAYER_STATS_RESET_SESSION,

											"default_image": "d:/ymir work/ui/game/guild/refresh_button_01.sub",
											"over_image": "d:/ymir work/ui/game/guild/refresh_button_02.sub",
											"down_image": "d:/ymir work/ui/game/guild/refresh_button_03.sub",
										},
									),
								},
							),
						},
					),
				},
			),
		},
	),
}