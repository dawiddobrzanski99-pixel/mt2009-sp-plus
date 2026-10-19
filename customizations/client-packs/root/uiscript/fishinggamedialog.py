import uiScriptLocale
import flamewindPath
import grp

WINDOW_WIDTH = 80
WINDOW_HEIGHT = 330

FISHING_AREA_WIDTH = 26
FISHING_AREA_HEIGHT = 290

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "FishingGameDialog",

	"x": CENTER_X - SCREEN_WIDTH * 0.1,
	"y": CENTER_Y,

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
	(
		{
			"name": "board",
			"type": "board",
			"style": ("attach",),
			"skin" : "a",
			"alpha": 0.5,

			"x": 0,
			"y": 0,

			"width": WINDOW_WIDTH,
			"height": WINDOW_HEIGHT,

			"children":
			(
				{
					"name": "background",
					"type": "image",

					"x": 0,
					"y": 0,

					"image" : flamewindPath.GetFishing("fishing_area"),

					"horizontal_align": "center",
					"vertical_align": "center",

					"children":
					(
						{
							"name": "fishing_area",
							"type": "window",
							"x": 6,
							"y": 0,
							"width": FISHING_AREA_WIDTH,
							"height": FISHING_AREA_HEIGHT,
							"horizontal_align": "center",
							"vertical_align": "center",
							"children":
							(
								{
									"name": "fishing_bar",
									"type": "bar",
									# "type": "board",
									# "skin": "green_bar",
									"color" : grp.GenerateColor(0.2235, 0.8078, 0.1647, 0.36),
									"x": 0,
									"y": FISHING_AREA_HEIGHT * 0.2,
									"width": FISHING_AREA_WIDTH,
									"height": FISHING_AREA_HEIGHT * 0.2,
									"horizontal_align": "center",
									"vertical_align": "bottom",

									"children" : (
										{
											"name" : "help_stick_area", "type" : "expanded_image",
											"x" : -90, "y" : 10,
											"rect" : (-0.4, 0.0, 0.0, 0.0),
											"image" : "d:/ymir work/ui/pattern/help_stick_right.tga",

											"children" :
											(
												{
													"type" : "text",
													"x" : 27, "y" : -4,
													"text_horizontal_align" : "right",
													"outline":True,
													"text" : uiScriptLocale.HELP_FISHING_GAME2,
												},
											),
										},
									),
								},
								{
									"name" : "player_fish",
									"type": "window",
									"x":0,"y":FISHING_AREA_HEIGHT * 0.2,
									"width" : 32,
									"height" : 32,
									"horizontal_align": "center",
									"vertical_align": "bottom",
									"children" :
									(
										{
											"name": "player_fish_icon",
											"type": "expanded_image",
											"x": 0,
											"y": -16,
											"image": "icon/item/27837.tga",
											"horizontal_align": "center", "vertical_align": "center",
											"children" : (
												{
													"name" : "help_stick_player", "type" : "expanded_image",
													"x" : 25, "y" : 16,
													"rect" : (0.0, 0.0, -0.4, 0.0),
													"image" : "d:/ymir work/ui/pattern/help_stick_left.tga",

													"children" :
													(
														{
															 "type" : "text",
															"x" : 70, "y" : -4,
															"outline":True,
															"text" : uiScriptLocale.HELP_FISHING_GAME1,
														},
													),
												},
											),
										},
									),
								},

								{
									"name": "cooldown_label",
									"type": "text",
									"x": 0,
									"y": 0,
									"text": "3...",
									"text_horizontal_align": "center",
									"horizontal_align": "center",
									"vertical_align": "center",
								},
							),
						},

						{
							"name" : "fish_mech_anim",
							"type" : "ani_image",

							"x" : -10,
							"y" : 260,
							"width" : 22,
							"height" : 22,

							"delay" : 7,

							"images" :
							(
								flamewindPath.GetFishing("fish_mech1"),
								flamewindPath.GetFishing("fish_mech2"),
								flamewindPath.GetFishing("fish_mech3"),
								flamewindPath.GetFishing("fish_mech4"),
								flamewindPath.GetFishing("fish_mech5"),
								flamewindPath.GetFishing("fish_mech6"),
								flamewindPath.GetFishing("fish_mech7"),
								flamewindPath.GetFishing("fish_mech8"),
							),
						},

						{
							"name" : "fish_mech",
							"type" : "image",

							"x" : -10,
							"y" : 260,

							"image" : flamewindPath.GetFishing("fish_mech1"),
						},
					),
				},

				{
					"name" : "fish_event",
					"type" : "window",

					"x" : -5,
					"y" : 0,
					"width" : 22,
					"height" : 22,

					"horizontal_align" : "right",
					"children": (
						{
							"name": "fish_event_pause",
							"type": "ani_image",
							"x": 0,"y": 0,"delay": 10,
							"images":
							(
								flamewindPath.GetFishing("pause1"),
								flamewindPath.GetFishing("pause2"),
								flamewindPath.GetFishing("pause3"),
								flamewindPath.GetFishing("pause4"),
							),
						},
						{
							"name": "fish_event_reverse",
							"type": "ani_image",
							"x": 0,"y": 0,"delay": 10,
							"images":
							(
								flamewindPath.GetFishing("reverse1"),
								flamewindPath.GetFishing("reverse2"),
								flamewindPath.GetFishing("reverse3"),
								flamewindPath.GetFishing("reverse4"),
							),
						},
						{
							"name": "fish_event_speed",
							"type": "ani_image",
							"x": 0,"y": 0,"delay": 10,
							"images":
							(
								flamewindPath.GetFishing("speed1"),
								flamewindPath.GetFishing("speed2"),
								flamewindPath.GetFishing("speed3"),
								flamewindPath.GetFishing("speed4"),
							),
						},
					),
				},
			),
		},
	),
}