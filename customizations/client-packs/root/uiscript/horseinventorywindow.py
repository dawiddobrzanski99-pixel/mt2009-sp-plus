import uiScriptLocale
import flamewindPath
import player

WINDOW_WIDTH = 184
WINDOW_HEIGHT = 340

window = {
	"name": "HorseInventoryWindow",

	"x" : SCREEN_WIDTH - 176 - WINDOW_WIDTH,
	"y" : SCREEN_HEIGHT - 37 - WINDOW_HEIGHT,

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
								{"name": "TitleName", "type": "text", "x": -4, "y": 4, "text": "Juki Konne",
								 "horizontal_align": "center", "text_horizontal_align": "center"},
							),
					},

					{
						"name": "ItemList",
						"type": "board",

						"x": 0,
						"y": 33,

						"style": ("attach",),

						"skin": "a",

						"horizontal_align": "center",

						"width": 170,
						"height": WINDOW_HEIGHT - 41,
						"children": (
							{
								"name": "ItemSlot",
								"type": "grid_table",
								"x": 5,
								"y": 5,
								"start_index": player.INVENTORY_DEFAULT_MAX_NUM,
								"x_count": 5,
								"y_count": 9,
								"x_step": 32,
								"y_step": 32,

								"image": "d:/ymir work/ui/public/Slot_Base.sub",
							},
							{
								"name": "NoHorseBackground",
								"type": "bar",
								"x": 5, "y": 5,
								"style": ("not_pick",),
								"width": 32*5,
								"height": 32*9,
								"color": 0x30e02222,
							},
						),
					},
				),
			},
		),
}