import flamewindPath

WINDOW_WIDTH = 139
WINDOW_HEIGHT = 12

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "BusyActionDialog",
	"style": ("float",),

	"x": CENTER_X,
	"y": SCREEN_HEIGHT*0.3,

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
	(
		{
			"type": "image",

			"x": 0,
			"y": 0,

			"image": flamewindPath.GetPublic("progress_bar"),

			"children":
			(
				{
					"name": "progress",
					"type": "expanded_image",

					"x": 2,
					"y": 2,

					"image": flamewindPath.GetPublic("progress_bar_full"),
				},

				{
					"name": "tip",
					"type": "image",

					"x": 0,
					"y": 0,

					"image": flamewindPath.GetPublic("progress_bar_tip"),
				},

				{
					"name": "action",
					"type": "text",

					"x": 0,
					"y": -14,
					"all_align": "center",
					"outline": True,

					"text": "Zbieranie...",
				},
			),
		},
	),
}