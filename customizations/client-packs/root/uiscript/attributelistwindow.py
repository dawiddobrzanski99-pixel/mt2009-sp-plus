import uiScriptLocale

WINDOW_WIDTH = 352
WINDOW_HEIGHT = 480

CONTENT_WIDTH = WINDOW_WIDTH - 42
CONTENT_HEIGHT = WINDOW_HEIGHT - 70

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "AttributeListWindow",

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
							"text": uiScriptLocale.ATTRIBUTE_LIST_TITLE,
							"horizontal_align": "center", "text_horizontal_align": "center"
						},
					),
				},

				{
					"name": "ScrollBar",
					"type": "scrollbar",
					"x": 26, "y": 36,
					"size": WINDOW_HEIGHT - 20 - 34,
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
						},
					),
				},
			),
		},
	),
}