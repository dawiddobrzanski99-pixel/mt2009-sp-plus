import uiScriptLocale
import flamewindPath

WINDOW_WIDTH = 184
WINDOW_HEIGHT = 145

window = {
	"name": "ReportPlayerDialog",

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
								{"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": uiScriptLocale.REPORT_PLAYER_TITLE,
								 "horizontal_align": "center", "text_horizontal_align": "center"},
							),
					},

					{
						"type": "board",

						"x": 0,
						"y": 33,

						"style": ("attach",),

						"skin": "a",

						"horizontal_align": "center",

						"width": 170,
						"height": WINDOW_HEIGHT - 41,
						"children": (
							{
								"type": "slotbar",
								"x": 0,
								"y": 5,

								"horizontal_align": "center",

								"width": 106,
								"height": 22,

								"children": (
									{
										"name": "PlayerNameLabel",
										"type": "text",
										"x": 3,
										"y": 5,
										"text": "12345678901234",
									},
								),
							},

							{
								"type": "text",
								"x": 0,
								"y": -10,
								"all_align": "center",
								"text": uiScriptLocale.REPORT_PLAYER_REASON,
								"bold": True,
							},

							{
								"name": "ReportButton",
								"type": "button",

								"x": 0,
								"y": 25,
								"horizontal_align": "center",
								"vertical_align": "bottom",

								"text": uiScriptLocale.REPORT_PLAYER_SUBMIT,

								"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
								"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
								"down_image": "d:/ymir work/ui/public/middle_button_03.sub",
							},

							{
								"name": "ReasonSelect",
								"type": "combobox",
								"x": 0,
								"y": 51,

								"horizontal_align": "center",

								"width": 128,
								"height": 19,
							},
						),
					},
				),
			},
		),
}