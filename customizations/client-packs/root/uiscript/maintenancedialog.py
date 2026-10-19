import uiScriptLocale

WINDOW_WIDTH = 302
WINDOW_HEIGHT = 110

window = {
	"name": "MaintenanceDialog",

	"x": 50,
	"y": SCREEN_HEIGHT * 0.6,

	"style": (),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
		(
			{
				"type": "thinboard",

				"x": 0,
				"y": 0,

				"style": ("attach",),

				"width": WINDOW_WIDTH,
				"height": WINDOW_HEIGHT,

				"children": (
					{
						"type": "horizontalbar",

						"x": 0,
						"y": 0,

						"horizontal_align": "center",

						"width": WINDOW_WIDTH,

						"children":
							(
								{
									"name": "TitleName", "type": "text", "x": -4, "y": 3, "text": uiScriptLocale.MAINTENANCE_DIALOG_TITLE,
									"horizontal_align": "center", "text_horizontal_align": "center", "bold": True,
								},
							),
					},
					{
						"type": "bar",
						"x": 2, "y": 17,
						"width": WINDOW_WIDTH - 4,
						"height": 44,
						"color": 0x60000000,
					},

					{
						"type": "text",
						"x": 10, "y": 24,
						"text": uiScriptLocale.MAINTENANCE_DIALOG_INFO1,
					},
					{
						"type": "text",
						"x": 10, "y": 39,
						"text": uiScriptLocale.MAINTENANCE_DIALOG_INFO2,
					},

					{
						"type": "line",
						"x": 0, "y": 60,
						"width": WINDOW_WIDTH,
						"height": 0,
						"color": 0xff555555,
					},

					{
						"type": "line",
						"x": 0, "y": 61,
						"width": WINDOW_WIDTH,
						"height": 0,
						"color": 0xff000000,
					},

					{
						"name": "StartTime",
						"type": "text",
						"x": 10, "y": 65,
						"fontsize": "LARGE",
						"bold": True,
						"text": "START_TIME",
					},

					{
						"name": "Duration",
						"type": "text",
						"x": 10, "y": 85,
						"fontsize": "LARGE",
						"bold": True,
						"text": "DURATION",
					},

					{
						"name": "CloseButton",
						"type": "button",

						"x": WINDOW_WIDTH - 16,
						"y": 2,

						"default_image": "d:/ymir work/ui/public/close_button_01.sub",
						"over_image": "d:/ymir work/ui/public/close_button_02.sub",
						"down_image": "d:/ymir work/ui/public/close_button_03.sub",
					},
				),
			},
		),
}