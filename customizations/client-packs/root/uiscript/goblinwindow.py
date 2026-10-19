# The Treasure Hunt window (uigoblin.py, MT2009_PLUS_GOBLIN_V1): the
# archive's uiscript/treasurehuntwindow.py - its layout and graphics
# (mt2009_ui/goblin, cut out of treasure_hunt_01.dds), the texts in Polish.
# Texts in CP1250 escapes.

PUBLIC_PATH						= "d:/ymir work/ui/public/"
PATTERN_PATH					= "d:/ymir work/ui/pattern/"
ROOT_PATH						= "mt2009_ui/goblin/event/"

WINDOW_WIDTH					= 314
WINDOW_HEIGHT					= 272
MAIN_WINDOW_WIDTH				= 292
MAIN_WINDOW_HEIGHT				= 202
MAIN_WINDOW_PATTERN_X_COUNT		= (MAIN_WINDOW_WIDTH - 32) / 16
MAIN_WINDOW_PATTERN_Y_COUNT		= (MAIN_WINDOW_HEIGHT - 32) / 16
SLOT_WIDTH						= 32
SLOT_HEIGHT						= 32


window = {
	"name"		: "treasure_hunt_event_window",
	"style"		: ("movable", "float", ),

	"x"			: SCREEN_WIDTH / 2 - WINDOW_WIDTH/2,
	"y"			: SCREEN_HEIGHT / 2 - WINDOW_HEIGHT/2,
	
	"width"		: WINDOW_WIDTH,
	"height"	: WINDOW_HEIGHT,

	"children" :
	(
		{
			"name"		: "board",
			"type"		: "board_with_titlebar",
			
			"x"			: 0,
			"y"			: 0,
			
			"width"		: WINDOW_WIDTH,
			"height"	: WINDOW_HEIGHT,
			
			"title"		: "Poszukiwanie skarb\xf3w",

			"children" :
			(
				{
					"name"		: "thinboard_circle",
					"type"		: "window",
					"style"		: ("ltr", "attach", ),
					
					"x"			: 10,
					"y"			: 32,

					"width"		: MAIN_WINDOW_WIDTH,
					"height"	: MAIN_WINDOW_HEIGHT,

					"children" :
					(
						{
							"name"		: "desc_window_background",
							"type"		: "thinboard_circle",
							"x"			: 0,
							"y"			: 0,
							"width"		: MAIN_WINDOW_WIDTH,
							"height"	: MAIN_WINDOW_HEIGHT,
						},
					),
				},
				{
					"name" : "reward_bg",
					"type" : "image",

					"x" : 13,
					"y" : 34,
							
					"image"	: ROOT_PATH + "main_title.tga",	

					"children":
					(
						{
							"name" : "reward_list_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align" : "center",
							"text_horizontal_align" : "center",

							"vertical_align" : "center",
							"text_vertical_align" : "center",

							"text" : "Nagrody",
						},
					),
				},
				{
					"name" : "reward_slot_bg",
					"type" : "image",

					"x" : 20,
					"y" : 62,
							
					"image"	: ROOT_PATH + "reward_slot.tga",
					
					"children":
					(
						{
							"name" : "reward_slot", "type" : "slot", "x" : 21-20, "y" : 63-62, "width" : 160, "height" : 160,
							"slot" :
							(
								# line 1
								{"index":0, "x":SLOT_WIDTH * 0, "y":SLOT_HEIGHT * 0, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":1, "x":SLOT_WIDTH * 1, "y":SLOT_HEIGHT * 0, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":2, "x":SLOT_WIDTH * 2, "y":SLOT_HEIGHT * 0, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":3, "x":SLOT_WIDTH * 3, "y":SLOT_HEIGHT * 0, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":4, "x":SLOT_WIDTH * 4, "y":SLOT_HEIGHT * 0, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},

								# line 2
								{"index":5, "x":SLOT_WIDTH * 0, "y":SLOT_HEIGHT * 1, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":6, "x":SLOT_WIDTH * 1, "y":SLOT_HEIGHT * 1, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":7, "x":SLOT_WIDTH * 2, "y":SLOT_HEIGHT * 1, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":8, "x":SLOT_WIDTH * 3, "y":SLOT_HEIGHT * 1, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":9, "x":SLOT_WIDTH * 4, "y":SLOT_HEIGHT * 1, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},

								# line 3
								{"index":10, "x":SLOT_WIDTH * 0, "y":SLOT_HEIGHT * 2, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":11, "x":SLOT_WIDTH * 1, "y":SLOT_HEIGHT * 2, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":12, "x":SLOT_WIDTH * 2, "y":SLOT_HEIGHT * 2, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":13, "x":SLOT_WIDTH * 3, "y":SLOT_HEIGHT * 2, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":14, "x":SLOT_WIDTH * 4, "y":SLOT_HEIGHT * 2, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},

								# line 4
								{"index":15, "x":SLOT_WIDTH * 0, "y":SLOT_HEIGHT * 3, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":16, "x":SLOT_WIDTH * 1, "y":SLOT_HEIGHT * 3, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":17, "x":SLOT_WIDTH * 2, "y":SLOT_HEIGHT * 3, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":18, "x":SLOT_WIDTH * 3, "y":SLOT_HEIGHT * 3, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":19, "x":SLOT_WIDTH * 4, "y":SLOT_HEIGHT * 3, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},

								# line 5
								{"index":20, "x":SLOT_WIDTH * 0, "y":SLOT_HEIGHT * 4, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":21, "x":SLOT_WIDTH * 1, "y":SLOT_HEIGHT * 4, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":22, "x":SLOT_WIDTH * 2, "y":SLOT_HEIGHT * 4, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":23, "x":SLOT_WIDTH * 3, "y":SLOT_HEIGHT * 4, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
								{"index":24, "x":SLOT_WIDTH * 4, "y":SLOT_HEIGHT * 4, "width":SLOT_WIDTH, "height":SLOT_HEIGHT},
							),	
						},
					),
				},
				{
					"name" : "gold_bg",
					"type" : "image",

					"x" : 192,
					"y" : 34,
							
					"image"	: ROOT_PATH + "gold_count_bg.tga",	

					"children":
					(
						{
							"name" : "gold_title_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align"		: "center",
							"text_horizontal_align"	: "center",

							"vertical_align"		: "center",
							"text_vertical_align"	: "center",

							"text" : "Zdobyte Doblony",
						},
					),
				},
				{
					"name" : "gold_icon_bg",
					"type" : "image",

					"x" : 211,
					"y" : 66,
							
					"image"	: ROOT_PATH + "gold_icon.tga",	
				},
				{
					"name" : "gold_count_bg",
					"type" : "image",

					"x" : 234,
					"y" : 67,

					"width" : 39,
					"height" : 18,
					
					"image"		: ROOT_PATH + "gold_text_bg.tga",

					"children":
					(
						{
							"name" : "gold_count_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align"		: "center",
							"text_horizontal_align" : "center",

							"vertical_align"		: "center",
							"text_vertical_align"	: "center",
							"text" : "0",
						},
					),
				},
				{
					"name" : "reward_set_button", "type" : "button", "x" : 208, "y" : 97,
					
					"default_image"	: ROOT_PATH + "reward_set_bt_default.tga", 
					"over_image"	: ROOT_PATH + "reward_set_bt_over.tga",
					"down_image"	: ROOT_PATH + "reward_set_bt_down.tga",
				},

				{
					"name" : "reward_set_button_off", "type" : "button", "x" : 208, "y" : 97,
					
					"default_image"	: ROOT_PATH + "reward_set_bt_down.tga", 
					"over_image"	: ROOT_PATH + "reward_set_bt_down.tga",
					"down_image"	: ROOT_PATH + "reward_set_bt_down.tga",
				},

				{
					"name" : "accumulate_count_bg",
					"type" : "image",

					"x" : 192,
					"y" : 132,
							
					"image"	: ROOT_PATH + "accumulate_count_bg.tga",	

					"children":
					(
						{
							"name" : "accumulate_count_title_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align" : "center",
							"text_horizontal_align" : "center",

							"vertical_align" : "center",
							"text_vertical_align" : "center",

							"text" : "Tura",
						},
					),
				},
				{
					"name"			: "accumulate_count_help_button",
					"type"			: "button",
					"x"				: 216,
					"y"				: 167,
					"default_image"	: PATTERN_PATH + "q_mark_01.tga",
					"over_image"	: PATTERN_PATH + "q_mark_02.tga",
					"down_image"	: PATTERN_PATH + "q_mark_01.tga",
				},		
				{
					"name" : "accumulate_count_text_bg",
					"type" : "image",

					"x" : 236,
					"y" : 166,

					"width" : 35,
					"height" : 18,
					
					"image"		: ROOT_PATH + "gold_text_bg.tga",

					"children":
					(
						{
							"name" : "accumulate_count_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align" : "center",
							"text_horizontal_align" : "center",

							"vertical_align" : "center",
							"text_vertical_align" : "center",

							"text" : "0",
						},
					),
				},
				{
					"name" : "accumulate_reward_list_button", "type" : "button", "x" : 208, "y" : 197,
					
					"default_image"	: ROOT_PATH + "reward_list_bt_default.tga", 
					"over_image"	: ROOT_PATH + "reward_list_bt_over.tga",
					"down_image"	: ROOT_PATH + "reward_list_bt_down.tga",
				},
				{
					"name" : "main_bg_line",
					"type" : "image",
					"style" : ("ltr",),
					
					"x" : 189,
					"y" : 32,
					"image" : ROOT_PATH + "main_bg_line.tga",
				},
				{
					"name" : "reward_button", "type" : "button", "x" : 12, "y" : 238,
					
					"default_image"	: ROOT_PATH + "reward_bt_default.tga", 
					"over_image"	: ROOT_PATH + "reward_bt_over.tga",
					"down_image"	: ROOT_PATH + "reward_bt_down.tga",
				},
				{
					"name" : "reward_off_button", "type" : "button", "x" : 12, "y" : 238,
					
					"default_image"	: ROOT_PATH + "reward_bt_down.tga", 
					"over_image"	: ROOT_PATH + "reward_bt_down.tga",
					"down_image"	: ROOT_PATH + "reward_bt_down.tga",
				},
				{
					"name" : "key_img",
					"type" : "image",
					"style" : ("ltr",),
					
					"x" : 93,
					"y" : 240,
					"image" : ROOT_PATH + "key_icon.tga",
				},
				{
					"name" : "key_count_text_bg",
					"type" : "image",

					"x" : 113,
					"y" : 240,

					"width" : 35,
					"height" : 18,
					
					"image"		: ROOT_PATH + "key_count_text_bg.tga",

					"children":
					(
						{
							"name" : "key_count_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align" : "center",
							"text_horizontal_align" : "center",

							"vertical_align" : "center",
							"text_vertical_align" : "center",

							"text" : "0",
						},
					),
				},
				{
					"name" : "reset_button", "type" : "button", "x" : 151, "y" : 239,
					
					"default_image"	: ROOT_PATH + "reset_bt_default.tga", 
					"over_image"	: ROOT_PATH + "reset_bt_over.tga",
					"down_image"	: ROOT_PATH + "reset_bt_down.tga",
				},

				{
					"name" : "reset_off_button", "type" : "button", "x" : 151, "y" : 239,
					
					"default_image"	: ROOT_PATH + "reset_bt_down.tga", 
					"over_image"	: ROOT_PATH + "reset_bt_down.tga",
					"down_image"	: ROOT_PATH + "reset_bt_down.tga",
				},

				{
					"name" : "ranking_button", "type" : "button", "x" : 228, "y" : 239,
					
					"default_image"	: ROOT_PATH + "ranking_bt_default.tga", 
					"over_image"	: ROOT_PATH + "ranking_bt_over.tga",
					"down_image"	: ROOT_PATH + "ranking_bt_down.tga",
				},
			),
		},
	),
}