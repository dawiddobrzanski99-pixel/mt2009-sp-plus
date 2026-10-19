import uiScriptLocale

WINDOW_WIDTH = 260
WINDOW_HEIGHT = 200

window = {
	"name": "GameMasterBanDialog",

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
								{"name": "TitleName", "type": "text", "x": -4, "y": 4,
								 "text": "Ban (12345678901234 pid: 12345)",
								 "horizontal_align": "center", "text_horizontal_align": "center"},
							),
					},

					{
						"name": "PermToggleButton",
						"type": "toggle_button",

						"x": 15,
						"y": 40,

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",

						"text": "PERM",
					},

					{
						"name": "InstantToggleButton",
						"type": "toggle_button",

						"x": 80,
						"y": 40,

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",

						"text": "INSTANT",
					},

					{
						"name": "DurationSlot",
						"type": "slotbar",
						"x": 84,
						"y": 70,

						"width": 60,
						"height": 18,

						"children":
							(
								{
									"type": "text",
									"x": -70,
									"y": 2,

									"text": "Czas blokady",
								},

								{
									"name": "DurationInput",
									"type": "editline",
									"x": 3,
									"y": 3,
									"width": 80,
									"height": 25,
									"input_limit": 3,
									"only_number": 1,
									"placeholder": "w dniach",
								},
							),
					},

					{
						"name": "ReasonSlot",
						"type": "slotbar",
						"x": 84,
						"y": 95,

						"width": 160,
						"height": 54,

						"children":
							(
								{
									"type": "text",
									"x": -70,
									"y": 2,

									"text": "DLACZEGO?!",
								},

								{
									"name": "ReasonInput",
									"type": "editline",
									"x": 3,
									"y": 3,
									"width": 160,
									"height": 54,
									"input_limit": 68,
									"limit_width": 160,
									"multi_line": True,
									"placeholder": "Podaj powod...",
								},
							),
					},

					{
						"name": "BanButton",
						"type": "button",

						"x": 0,
						"y": 35,

						"horizontal_align": "center",
						"vertical_align": "bottom",

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",

						"text": "Blokuj",
					},
				),
			},
		),
}