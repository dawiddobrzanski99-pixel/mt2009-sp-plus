import uiScriptLocale

ROOT_PATH = "d:/ymir work/ui/public/"

window = {
	"name": "ConfigWindow",

	"x": 0,
	"y": 0,

	"width": SCREEN_WIDTH,
	"height": SCREEN_HEIGHT,

	"children": (
		{
			"type": "bar",

			"x": 0,
			"y": 0,

			"color": 0xcc000000,

			"width": SCREEN_WIDTH,
			"height": SCREEN_HEIGHT,
		},

		{
			"name": "Board",
			"type": "board_with_titlebar",

			"x": SCREEN_WIDTH / 2 - 435 / 2,
			"y": SCREEN_HEIGHT / 2 - 415 / 2,

			"width": 435,
			"height": 415,

			"title": uiScriptLocale.CONFIG_TITLE,

			"children":
				(
					{
						"name": "SaveButton",
						"type": "button",

						"x": -90,
						"y": 38,

						"horizontal_align": "center",
						"vertical_align": "bottom",

						"default_image": ROOT_PATH + "xlarge_Button_01.sub",
						"over_image": ROOT_PATH + "xlarge_Button_02.sub",
						"down_image": ROOT_PATH + "xlarge_Button_03.sub",

						"text": uiScriptLocale.CONFIG_SAVE,
					},
					{
						"name": "SoundBoard",
						"type": "board",
						"skin" : "a",

						"x": 20,
						"y": 250,

						"width": 220,
						"height": 120,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1, "width": 216,
									"horizontal_align": "center",
									"children": (
										{
											"type": "text",
											"x": 0, "y": 0,
											"all_align": "center",
											"bold": True,
											"fontsize": "LARGE",
											"color": 0xfff2e4bd,
											"text": uiScriptLocale.CONFIG_SOUND,
										},
									),
								},
								{
									"name": "BGMText",
									"type": "text",

									"x": 20,
									"y": 28,
									"bold" : True,
									"text": "Muzyka",
								},
								{
									"name": "BGMSlider",
									"type": "sliderbar",
									"x": 20, "y": 25 + 22,
								},
								{
									"name": "SFXMText",
									"type": "text",

									"x": 20,
									"y": 73,
									"bold" : True,
									"text": "Inne",
								},
								{
									"name": "SFXSlider",
									"type": "sliderbar",
									"x": 20, "y": 70 + 22,
								},
							),
					},

					{
						"name": "LanguageBoard",
						"type": "board",
						"skin" : "a",

						"x": 250,
						"y": 340,

						"width": 165,
						"height": 60,

						"children":
						(
							{
								"type": "horizontalbar",
								"x": 0, "y": 1,"width" : 162,
								"horizontal_align" : "center",
								"children" : (
									{
										"type" : "text",
										"x" : 0, "y" : 0,
										"all_align" : "center",
										"bold" : True,
										"fontsize" : "LARGE",
										"color" : 0xfff2e4bd,
										"text" : uiScriptLocale.CONFIG_LANGUAGE,
									},
								),
							},
							{
								"name": "LanguageSelectBar",
								"type": "combobox",
								"x": 0,
								"y": 26,

								"horizontal_align": "center",

								"width": 128,
								"height": 19,
							},
						),
					},

					{
						"name": "ShadowBoard",
						"type": "board",
						"skin" : "a",

						"x": 250,
						"y": 282,

						"width": 165,
						"height": 60,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1,"width" : 162,
									"horizontal_align" : "center",
									"children" : (
										{
											"type" : "text",
											"x" : 0, "y" : 0,
											"all_align" : "center",
											"bold" : True,
											"fontsize" : "LARGE",
											"color" : 0xfff2e4bd,
											"text" : uiScriptLocale.CONFIG_SHADOWS,
										},
									),
								},
								{
									"name": "ShadowSelectBar",
									"type": "combobox",
									"x": 0,
									"y": 26,

									"horizontal_align": "center",

									"width": 128,
									"height": 19,
								},
							),
					},

					{
						"name": "MultiSamplingBoard",
						"type": "board",
						"skin" : "a",

						"x": 250,
						"y": 224,

						"width": 165,
						"height": 60,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1,"width" : 162,
									"horizontal_align" : "center",
									"children" : (
										{
											"type" : "text",
											"x" : 0, "y" : 0,
											"all_align" : "center",
											"bold" : True,
											"fontsize" : "LARGE",
											"color" : 0xfff2e4bd,
											"text" : uiScriptLocale.CONFIG_MULTISAMPLING,
										},
									),
								},
								{
									"name": "SamplingSelectBar",
									"type": "combobox",
									"x": 0,
									"y": 26,

									"horizontal_align": "center",

									"width": 108,
									"height": 19,
								},
							),
					},
					{
						"name": "FontSizeModeBoard",
						"type": "board",
						"skin": "a",

						"x": 250,
						"y": 166,

						"width": 165,
						"height": 60,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1, "width": 162,
									"horizontal_align": "center",
									"children": (
										{
											"type": "text",
											"x": 0, "y": 0,
											"all_align": "center",
											"bold": True,
											"fontsize": "LARGE",
											"color": 0xfff2e4bd,
											"text": uiScriptLocale.CONFIG_FONT,
										},
									),
								},
								{
									"name": "FontSelect",
									"type": "combobox",
									"x": 0,
									"y": 26,

									"horizontal_align": "center",

									"width": 108,
									"height": 19,
								},
							),
					},

					{
						"name": "TextureModeBoard",
						"type": "board",

						"x": 250,
						"y": 108,

						"width": 165,
						"height": 60,

						"skin": "a",

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1, "width": 162,
									"horizontal_align": "center",
									"children": (
										{
											"type": "text",
											"x": 0, "y": 0,
											"all_align": "center",
											"bold": True,
											"fontsize": "LARGE",
											"color": 0xfff2e4bd,
											"text": uiScriptLocale.CONFIG_TEXTURE,
										},
									),
								},

								{
									"name": "TextureSelectBar",
									"type": "combobox",
									"x": 0,
									"y": 26,

									"horizontal_align": "center",

									"width": 128,
									"height": 19,
								},
							),
					},
					{
						"name": "ScaleModeBoard",
						"type": "board",
						"skin" : "a",

						"x": 20,
						"y": 147,

						"width": 220,
						"height": 105,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1,"width" : 216,
									"horizontal_align" : "center",
									"children" : (
										{
											"type" : "text",
											"x" : 0, "y" : 0,
											"all_align" : "center",
											"bold" : True,
											"fontsize" : "LARGE",
											"color" : 0xfff2e4bd,
											"text" : uiScriptLocale.CONFIG_SCALE_MODE,
										},
									),
								},
								{
									"name": "ScaleLabel",
									"type": "text",

									"x": 20,
									"y": 53,
									"bold" : True,
									"text": "Skala (1.0)",
								},
								{
									"name": "ScaleSlider",
									"type": "sliderbar",
									"x": 20, "y": 47+25,
								},
								{
									"name": "ScaleModeSelectBar",
									"type": "combobox",
									"x": 0,
									"y": 30,

									"horizontal_align": "center",

									"width": 108,
									"height": 19,
								},
							),
					},
					{
						"name": "CustomResolutionModeBoard",
						"type": "board",
						"skin" : "a",

						"x": 250,
						"y": 30,

						"width": 165,
						"height": 80,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1, "width": 162,
									"horizontal_align": "center",
									"children": (
										{
											"type": "text",
											"x": 0, "y": 0,
											"all_align": "center",
											"bold": True,
											"fontsize": "LARGE",
											"color": 0xfff2e4bd,
											"text": uiScriptLocale.CONFIG_CUSTOM_RESOLUTION,
										},
									),
								},
								{
									"type": "image",
									"image": "d:/ymir work/ui/public/Parameter_Slot_04.sub",
									"x": 0,
									"y": 25,
									"horizontal_align": "center",
									"children":
										(
											{
												"name": "WidthEditLine",
												"type": "editline",

												"x": 5,
												"y": 2,

												"width": 120,
												"height": 15,

												"only_number": 1,
												"input_limit": 4,
											},
										),
								},
								{
									"type": "image",
									"image": "d:/ymir work/ui/public/Parameter_Slot_04.sub",
									"x": 0,
									"y": 50,
									"horizontal_align": "center",
									"children":
										(
											{
												"name": "HeightEditLine",
												"type": "editline",

												"x": 5,
												"y": 2,

												"width": 120,
												"height": 15,

												"only_number": 1,
												"input_limit": 4,
											},
										),
								},
							),
					},

					{
						"name": "ResolutionBoard",
						"type": "board",
						"skin": "a",

						"x": 20,
						"y": 30,

						"width": 220,
						"height": 118,

						"children":
							(
								{
									"type": "horizontalbar",
									"x": 0, "y": 1, "width": 216,
									"horizontal_align": "center",
									"children": (
										{
											"type": "text",
											"x": 0, "y": 0,
											"all_align": "center",
											"bold": True,
											"fontsize": "LARGE",
											"color": 0xfff2e4bd,
											"text": uiScriptLocale.CONFIG_RESOLUTION,
										},
									),
								},

								{
									"name": "WindowMode",
									"type": "button",

									"x": -45,
									"y": 65,

									"horizontal_align": "center",

									"default_image": ROOT_PATH + "large_Button_01.sub",
									"over_image": ROOT_PATH + "large_Button_02.sub",
									"down_image": ROOT_PATH + "large_Button_03.sub",

									"text": uiScriptLocale.CONFIG_WINDOW_WINDOWED,
								},
								{
									"name": "FullscreenMode",
									"type": "button",

									"x": -45,
									"y": 85,
									"horizontal_align": "center",

									"default_image": ROOT_PATH + "large_Button_01.sub",
									"over_image": ROOT_PATH + "large_Button_02.sub",
									"down_image": ROOT_PATH + "large_Button_03.sub",

									"text": uiScriptLocale.CONFIG_WINDOW_FULL,
								},
								{
									"name": "FullscreenWindowMode",
									"type": "button",

									"x": 45,
									"y": 65,

									"horizontal_align": "center",

									"default_image": ROOT_PATH + "large_Button_01.sub",
									"over_image": ROOT_PATH + "large_Button_02.sub",
									"down_image": ROOT_PATH + "large_Button_03.sub",

									"text": uiScriptLocale.CONFIG_WINDOW_FULL_WINDOWED,
								},

								{
									"name": "Resolution",
									"type": "combobox",
									"x": 0,
									"y": 34,

									"horizontal_align": "center",

									"default_text": uiScriptLocale.CONFIG_MUTLISAMPLING_LEVEL3,

									"width": 148,
									"height": 19,
								},


							),
					},
				),
		},
	),
}