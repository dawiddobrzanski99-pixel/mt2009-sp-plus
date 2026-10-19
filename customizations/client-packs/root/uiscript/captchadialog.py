import uiScriptLocale
import flamewindPath

WINDOW_WIDTH = 302
WINDOW_HEIGHT = 315

window = {
	"name": "CaptchaDialog",

	"x": 0,
	"y": 0,

	"style": (),

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
					{
						"type": "horizontalbar",

						"x": 0,
						"y": 1,

						"horizontal_align": "center",

						"width": WINDOW_WIDTH - 4,

						"children":
							(
								{
									"name": "TitleName", "type": "text", "x": -4, "y": 3, "text": "Podaj kod CAPTCHA",
									"horizontal_align": "center", "text_horizontal_align": "center", "bold": True,
								},
							),
					},

					{
						"name": "CaptchaBg",
						"type": "thinboard",
						"x": 0,
						"y": 25,

						"width": 196,
						"height": 80,

						"horizontal_align": "center",

						"children": (
							{
								"type": "horizontalbar",
								"x": 0,
								"y": 18,

								"width": 196,

								"horizontal_align": "center",
								"vertical_align": "bottom",

								"children": (
									{
										"name": "TimeLabel",
										"type": "text",
										"x": 0,
										"y": 0,

										"all_align": "center",
										"text": "Pozostalo: 45s",
									},

									{
										"name": "RequestNewCaptchaButton",
										"type": "button",

										"x": 17,
										"y": 0,

										"horizontal_align": "right",
										"vertical_align": "center",

										"tooltip_x" : 95,
										"tooltip_y" : -15,
										"tooltip_text": uiScriptLocale.CAPTCHA_REQUEST_NEW_IMAGE,

										"default_image": flamewindPath.GetPublic("refresh_button_01"),
										"over_image": flamewindPath.GetPublic("refresh_button_02"),
										"down_image": flamewindPath.GetPublic("refresh_button_03"),
									},
								),
							},
						),
					},

					{
						"name": "TipBoard",
						"type": "slotbar",
						"x": 0,
						"y": 200,

						"horizontal_align": "center",
						"vertical_align": "bottom",

						"width": 280,
						"height": 96,
						"children" :(
							{"type": "text","x": 0,"y": 1,"horizontal_align": "center","text_horizontal_align": "center", "bold": True, "text": uiScriptLocale.CAPTCHA_TIP1,},
							{"type": "text","x": 6,"y": 18, "text": uiScriptLocale.CAPTCHA_TIP2,},
							{"type": "text","x": 6,"y": 33, "text": uiScriptLocale.CAPTCHA_TIP3,},
							{"type": "text","x": 6,"y": 48, "text": uiScriptLocale.CAPTCHA_TIP4,},
							{"type": "text","x": 6,"y": 63, "text": uiScriptLocale.CAPTCHA_TIP5,},
							{"type": "text","x": 6,"y": 78, "text": uiScriptLocale.CAPTCHA_TIP6,},
						),
					},

					{
						"type": "slotbar",
						"x": 0,
						"y": 80,

						"horizontal_align": "center",
						"vertical_align": "bottom",

						"width": 70,
						"height": 21,

						"children":
							(
								{
									"type": "text",
									"x": 0,
									"y": -15,

									"horizontal_align": "center",
									"text_horizontal_align": "center",
									"text": "Podaj Kod:",
								},

								{
									"name": "CodeInput",
									"type": "editline",
									"x": 3,
									"y": 4,
									"width": 67,
									"height": 18,
									"input_limit": 8,
								},

								{
									"name": "LeftLabel",
									"type": "text",
									"x": 0,
									"y": -14,

									"text_vertical_align": "bottom",
									"vertical_align": "bottom",
									"horizontal_align": "center",
									"text_horizontal_align": "center",
									"text": "Pozostalo prob: 3",
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

						"default_image": flamewindPath.GetPublic("accept_button_01"),
						"over_image": flamewindPath.GetPublic("accept_button_02"),
						"down_image": flamewindPath.GetPublic("accept_button_03"),
					},
				),
			},
		),
}