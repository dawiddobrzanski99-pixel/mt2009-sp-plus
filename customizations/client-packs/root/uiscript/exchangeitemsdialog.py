WINDOW_WIDTH = 222
WINDOW_HEIGHT = 184

CENTER_X = SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2
CENTER_Y = SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2

window = {
	"name": "ExchangeItemsDialog",

	"x": CENTER_X,
	"y": CENTER_Y,

	"style": ("movable", "float",),

	"width": WINDOW_WIDTH,
	"height": WINDOW_HEIGHT,

	"children":
		(
			{
				"name" : "Board",
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
									"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": "Wymiana",
									"horizontal_align": "center", "text_horizontal_align": "center"
								},
							),
					},

					{
						"name": "ItemSlot",
						"type": "grid_table",

						"x": 15,
						"y": 35,

						"start_index": 0,
						"x_count": 6,
						"y_count": 1,
						"x_step": 32,
						"y_step": 32,

						"image": "d:/ymir work/ui/public/Slot_Base.sub"
					},

					{
						"type": "board",

						"x": 8,
						"y": 105 + 9,

						"skin": "a",

						"vertical_align": "bottom",

						"width": WINDOW_WIDTH - 16,
						"height": 105,

						"children": (
							{
								"name": "ResultItemSlot",
								"type": "slot",

								"x": 0,
								"y": 98,

								"width" : 32,
								"height" : 32,

								"horizontal_align": "center",
								"vertical_align": "bottom",

								"slot" : (
										{"index":0, "x":0, "y":0, "width":32, "height":32},
									),

								"image": "d:/ymir work/ui/public/Slot_Base.sub",
								"children" : (
									{
										"type": "text",
										"text": "Rezultat",
										"x": 0, "y": 0,
										"text_horizontal_align": "center",
										"horizontal_align": "center",
										"vertical_align": "bottom",
									},
								),
							},
							# {
							# 	"type": "image",
							#
							# 	"x": 0,
							# 	"y": 78,
							#
							# 	"horizontal_align": "center",
							# 	"vertical_align": "bottom",
							#
							# 	"image": "d:/ymir work/ui/public/Slot_Base.sub",
							#
							# 	"children": (
							# 		{
							# 			"name": "ResultIcon",
							# 			"type": "image",
							# 			"x": 0, "y": 0,
							# 			"horizontal_align": "center",
							# 			"vertical_align": "center",
							# 			"image": "d:/ymir work/ui/public/Slot_Base.sub",
							# 		},
							# 		{
							# 			"type": "text",
							# 			"text": "Rezultat",
							# 			"x": 0, "y": 0,
							# 			"text_horizontal_align": "center",
							# 			"horizontal_align": "center",
							# 			"vertical_align": "bottom",
							# 		},
							# 	),
							# },

						{
								"type": "slotbar",
								"x": 6, "y": 46,
								"width": 96,
								"height": 20,
								"vertical_align": "bottom",

								"children": (
									{
										"name" : "ChanceLabel",
										"type": "text",
										"text": "100%",
										"x": 0, "y": 0,
										"all_align": "center",
									},
								),
							},

							{
								"type": "slotbar",
								"x": 6, "y": 26,
								"width": 96,
								"height": 20,
								"vertical_align": "bottom",

								"children": (
									{
										"name" : "PriceLabel",
										"type": "text",
										"text": "9.999.999.999 Yang",
										"x": 0, "y": 0,
										"all_align": "center",
									},
								),
							},

							{
								"name": "AcceptButton",
								"type": "button",

								"x": 96,
								"y": 26,

								"horizontal_align": "right",
								"vertical_align": "bottom",

								"text": "Wymiana",

								"default_image": "d:/ymir work/ui/public/large_button_01.sub",
								"over_image": "d:/ymir work/ui/public/large_button_02.sub",
								"down_image": "d:/ymir work/ui/public/large_button_03.sub",
							},
						),
					},
				),
			},
		),
}