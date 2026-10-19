# The Treasure Hunt's round rewards (uigoblin.py, MT2009_PLUS_GOBLIN_V1): the
# archive's uiscript/treasurehuntrewardlistwindow.py, the texts in Polish.
# Texts in CP1250 escapes.

PUBLIC_PATH						= "d:/ymir work/ui/public/"
PATTERN_PATH					= "d:/ymir work/ui/pattern/"
ROOT_PATH						= "mt2009_ui/goblin/event/reward_list/"

WINDOW_WIDTH					= 250
WINDOW_HEIGHT					= 304
OUTLINE_WIDTH					= 228
OUTLINE_HEIGHT					= 260
SLOT_WIDTH						= 45
SLOT_HEIGHT						= 45


window = {
	"name"		: "treasure_hunt_event_reward_list_window",
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
			
			"title"		: "Nagrody za tury",

			"children" :
			(
				{
					"name"		: "thinboard_circle",
					"type"		: "window",
					"x"			: 0,
					"y"			: 0,
					"width"		: WINDOW_WIDTH,
					"height"	: WINDOW_HEIGHT,
					"style"		: ("not_pick", ),

					"children"	:
					(
						{
							"name"		: "desc_background_window",
							"type"		: "thinboard_circle",
							"x"			: 10,
							"y"			: 32,
							"width"		: OUTLINE_WIDTH,
							"height"	: OUTLINE_HEIGHT,
						},
					),
				},

				{
					"name" : "reward_slots_bg",
					"type" : "image",

					"x" : 12,
					"y" : 160,
							
					"image"	: ROOT_PATH + "slots_bg.tga",	
				},
				{
					"name" : "reward_slots", "type" : "slot", "x" : 18, "y" : 167, "width" : 225, "height" : 96,
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
					),	
				},
				{
					"name" : "accumulate_count_bg",
					"type" : "image",

					"x" : 19,
					"y" : 41,
							
					"image"	: ROOT_PATH + "accumulate_count_bg.tga",	

					"children":
					(
						{
							"name" : "accumulate_count_bg_text",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align" : "center",
							"text_horizontal_align" : "center",

							"vertical_align" : "center",
							"text_vertical_align" : "center",

							"text" : "Tury",
						},
					),
				},
				{
					"name" : "accumulate_count_text_bg",
					"type" : "image",

					"x" : 162,
					"y" : 40,
							
					"image"	: ROOT_PATH + "accumulate_count_text_bg.tga",	

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
							"text" : "1",
						},
					),
				},
				{
					"name" : "accumulate_prev_bt", "type" : "button", "x" : 138, "y" : 42,
					
					"default_image"	: ROOT_PATH + "accumulate_count_prev_default.tga", 
					"over_image"	: ROOT_PATH + "accumulate_count_prev_over.tga",
					"down_image"	: ROOT_PATH + "accumulate_count_prev_down.tga",
				},
				{
					"name" : "accumulate_next_bt", "type" : "button", "x" : 210, "y" : 42,
					
					"default_image"	: ROOT_PATH + "accumulate_count_next_default.tga", 
					"over_image"	: ROOT_PATH + "accumulate_count_next_over.tga",
					"down_image"	: ROOT_PATH + "accumulate_count_next_down.tga",
				},
				{
					"name" : "accumulate_reward_bt", "type" : "button", "x" : 19, "y" : 135,
					
					"default_image"	: ROOT_PATH + "reward_on_btn_default.tga", 
					"over_image"	: ROOT_PATH + "reward_on_btn_over.tga",
					"down_image"	: ROOT_PATH + "reward_on_btn_down.tga",
				},
				{
					"name" : "accumulate_reward_off_bt", "type" : "button", "x" : 19, "y" : 135,
					
					"default_image"	: ROOT_PATH + "reward_off_btn_default.tga", 
					"over_image"	: ROOT_PATH + "reward_off_btn_default.tga",
					"down_image"	: ROOT_PATH + "reward_off_btn_default.tga",
				},
				{
					"name" : "desc_prev_bt", "type" : "button", "x" : 158, "y" : 137,

					"default_image"	: ROOT_PATH + "accumulate_reward_list_prev_default.tga",
					"over_image"	: ROOT_PATH + "accumulate_reward_list_prev_default.tga",
					"down_image"	: ROOT_PATH + "accumulated_reward_list_prev_down.tga",
				},
				{
					"name" : "desc_next_bt", "type" : "button", "x" : 200, "y" : 137,

					"default_image"	: ROOT_PATH + "accumulate_reward_list_next_default.tga",
					"over_image"	: ROOT_PATH + "accumulate_reward_list_next_default.tga",
					"down_image"	: ROOT_PATH + "accumulate_reward_list_next_down.tga",
				},
			),
		},
	),
}