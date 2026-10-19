WINDOW_WIDTH = 250
WINDOW_HEIGHT = 135

window = {
	"name": "GameMasterTargetPlayerDialog",

	"x": SCREEN_WIDTH - 213 - WINDOW_WIDTH,
	"y": 90,

	"style": ("float", "movable",),

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
									"name": "TitleName", "type": "text", "x": -4, "y": 3, "text": "GM: Podglad Gracza",
									"horizontal_align": "center", "text_horizontal_align": "center", "bold": True,
								},
							),
					},
					{
						"type": "bar",
						"x": 2, "y": 17,
						"style": ("attach",),
						"width": WINDOW_WIDTH - 4,
						"height": 47,
						"color": 0x60000000,
					},

					{
						"name": "PlayerName",
						"type": "text",
						"x": 10, "y": 24,
						"text": "Nick: PLAYER_NAME",
						"bold": True,
					},

					{
						"name": "AccountName",
						"type": "text",
						"x": 10, "y": 39,
						"text": "Konto: ACCOUNT_NAME)",
					},

					{
						"type": "line",
						"x": 0, "y": 65,
						"width": WINDOW_WIDTH,
						"height": 0,
						"color": 0xff555555,
					},

					{
						"type": "line",
						"x": 0, "y": 66,
						"width": WINDOW_WIDTH,
						"height": 0,
						"color": 0xff000000,
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

					### MENU
					{
						"name": "ViewPlayerButton",
						"type": "button",

						"x": 10,
						"y": 75,

						"text": "Podglad",

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",
					},

					{
						"name": "CaptchaButton",
						"type": "button",

						"x": 80,
						"y": 75,

						"text": "Captcha",

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",
					},

					{
						"name": "BanButton",
						"type": "button",

						"x": 180,
						"y": 75,

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",

						"children": (
							{
								"type": "text",
								"text": "Ban",
								"x": 0, "y": 0,
								"all_align": "center",
								"color": 0xffed3434,
								"bold": True,
							},
						),
					},

					{
						"name": "KickButton",
						"type": "button",

						"x": 180,
						"y": 100,

						"default_image": "d:/ymir work/ui/public/middle_button_01.sub",
						"over_image": "d:/ymir work/ui/public/middle_button_02.sub",
						"down_image": "d:/ymir work/ui/public/middle_button_03.sub",

						"children": (
							{
								"type": "text",
								"text": "Kick",
								"x": 0, "y": 0,
								"all_align": "center",
								"color": 0xfff02e82,
							},
						),
					},
				),
			},
		),
}