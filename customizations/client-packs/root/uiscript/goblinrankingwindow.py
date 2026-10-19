# The Treasure Hunt's ranking (uigoblin.py, MT2009_PLUS_GOBLIN_V1): the
# archive's uiscript/treasurehuntrankingwindow.py, the texts in Polish.
# Texts in CP1250 escapes.

PUBLIC_PATH						= "d:/ymir work/ui/public/"
PATTERN_PATH					= "d:/ymir work/ui/pattern/"
ROOT_PATH						= "mt2009_ui/goblin/event/ranking/"
WINDOW_WIDTH					= 279
WINDOW_HEIGHT					= 344
OUTLINE_WIDTH					= 258
OUTLINE_HEIGHT					= 300

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
			
			"title"		: "Ranking poszukiwania skarb\xf3w",

			"children" :
			(
				{
					"name"		: "thinboard_circle",
					"type"		: "window",
					"style"		: ("ltr", "attach", ),
					"x"			: 0,
					"y"			: 0,
					"width"		: WINDOW_WIDTH,
					"height"	: WINDOW_HEIGHT,
					"style"		: ("not_pick", ),

					"children"	:
					(
						{
							"name"		: "outline_bg",
							"type"		: "thinboard_circle",
							"x"			: 10,
							"y"			: 32,
							"width"		: OUTLINE_WIDTH,
							"height"	: OUTLINE_HEIGHT,
						},
					),
				},
				{
					"name" : "ranking_menu_bg",
					"type" : "image",

					"x" : 13,
					"y" : 34,
							
					"image"	: ROOT_PATH + "menu_bg.tga",
				},
				{
					"name"		: "rank_text_window",
					"type"		: "window",
					"style"		: ("ltr", "attach", "not_pick", ),
					
					"x"			: 15,
					"y"			: 34,

					"width"		: 54,
					"height"	: 21,

					"children" :
					(
						{
							"name" : "rank",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align"		: "center",
							"text_horizontal_align" : "center",

							"vertical_align"		: "center",
							"text_vertical_align"	: "center",

							"text" : "Miejsce",
						},
					),
				},
				{
					"name"		: "name_text_window",
					"type"		: "window",
					"style"		: ("ltr", "attach", "not_pick", ),
					
					"x"			: 69,
					"y"			: 34,

					"width"		: 125,
					"height"	: 21,

					"children" :
					(
						{
							"name" : "name",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align"		: "center",
							"text_horizontal_align" : "center",

							"vertical_align"		: "center",
							"text_vertical_align"	: "center",

							"text" : "Imi\xea",
						},
					),
				},
				{
					"name"		: "count_text_window",
					"type"		: "window",
					"style"		: ("ltr", "attach", "not_pick", ),
					
					"x"			: 194,
					"y"			: 34,

					"width"		: 55,
					"height"	: 21,

					"children" :
					(
						{
							"name" : "count",
							"type" : "text",

							"x" : 0,
							"y" : 0,

							"horizontal_align"		: "center",
							"text_horizontal_align" : "center",

							"vertical_align"		: "center",
							"text_vertical_align"	: "center",

							"text" : "Tury",
						},
					),
				},

				# 10 rows of 21 px (the rows' background), 23 px apart.
				{
					"name"		: "high_ranking_list",
					"type"		: "listboxex",
					"x"			: 15,
					"y"			: 58,
					"width"		: 246,
					"height"	: 230,
				},

				{
					"name"		: "empty_text",
					"type"		: "text",
					"x"			: 0,
					"y"			: 160,
					"horizontal_align"		: "center",
					"text_horizontal_align" : "center",
					"color"		: 0xFFA0A0A0,
					"text"		: "Nikt jeszcze nie uko\xf1czy\xb3 tury.",
				},

				# Shown only when the own place is below the list (uigoblin.py).
				{
					"name" : "dot",
					"type" : "image",

					"x" : 137,
					"y" : 292,
							
					"image"	: ROOT_PATH + "dot.tga",	
				},

				{
					"name"		: "cur_player_rank",
					"type"		: "listboxex",
					"x"			: 15,
					"y"			: 306,
					"width"		: 246,
					"height"	: 21,
				},

			),
		},
	),
}