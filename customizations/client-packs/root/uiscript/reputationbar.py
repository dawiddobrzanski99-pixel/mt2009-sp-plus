import flamewindPath

BAR_WIDTH = 160
BAR_HEIGHT = 53

window = {
	"name": "ReputationBar",

	"x": 0,
	"y": 0,

	"style": ("no_pick",),

	"width": BAR_WIDTH,
	"height": BAR_HEIGHT,

	"children":
	(
		{
			"name": "bar",
			"type" : "thinboard",

			"x": 0, "y": 0,
			"width": BAR_WIDTH,
			"height": BAR_HEIGHT,

			"children":
			(
				{
					"type" : "horizontalbar",
					"x": 0, "y": 0,
					"width": BAR_WIDTH,
					"horizontal_align" : "center",
					"skin": "light",
					"children" : (
						{
							"type" : "image",
							"x": -2, "y": -2,
							"image": flamewindPath.GetPublic("reputation_icon"),
						},
					),
				},

				{
					"name" : "ReputationNameLabel",
					"type" : "text",
					"x": 15, "y": 2,
					"text": "REPUTATION_NAME",
					"outline" : True,
					"bold" : True,
				},

				{
					"name" : "ProgressLabel",
					"type" : "text",
					"x": 0, "y": 20,
					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text": "99999/99999",
					"outline" : True,
				},

				{
					"type" : "image",

					"horizontal_align": "center",
					"x": 0, "y": 35,
					"image": flamewindPath.GetPublic("reputation_empty"),
					"children" : (
						{
							"name" : "ProgressBar",
							"type" : "expanded_image",
							"x": 0, "y": 0,
							"horizontal_align": "center",
							"vertical_align": "center",
							"image": flamewindPath.GetPublic("reputation_full"),
						},
						{
							"type" : "image",
							"x": 0, "y": 0,
							"horizontal_align": "center",
							"vertical_align": "center",
							"image": flamewindPath.GetPublic("reputation_split"),
						},
					),
				},

			),
		},
	),
}