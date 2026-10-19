import uiScriptLocale

WINDOW_WIDTH = 302
WINDOW_HEIGHT = 310

window = {
	"name": "GameMasterCaptchaDialog",

	"x": 50,
	"y": 50,

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
									"name": "TitleName", "type": "text", "x": -4, "y": 3, "text": "GM: Captcha",
									"horizontal_align": "center", "text_horizontal_align": "center", "bold": True,
								},
							),
					},
					{
						"type": "bar",
						"style":("attach",),
						"x": 2, "y": 17,
						"width": WINDOW_WIDTH - 4,
						"height": 110,
						"color": 0x60000000,
					},

					{
						"name": "TimeLeft",
						"type": "text",
						"x": 10, "y": 24,
						"text": "Pozostalo czasu: 30s",
						"text_horizontal_align": "right",
						"horizontal_align": "right",
					},

					{
						"name": "PlayerName",
						"type": "text",
						"x": 10, "y": 24,
						"text": "Nick: NAZWA_GRACZA (pid: |cff5af22c99999|r)",
					},
					{
						"name": "Code",
						"type": "text",
						"x": 10, "y": 39,
						"text": "Kod: |cffffa826KOD_CAPTCHA|r",
					},

					{
						"type": "line",
						"x": 0, "y": 126,
						"width": WINDOW_WIDTH,
						"height": 0,
						"color": 0xff555555,
					},

					{
						"type": "line",
						"x": 0, "y": 127,
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
				),
			},
		),
}