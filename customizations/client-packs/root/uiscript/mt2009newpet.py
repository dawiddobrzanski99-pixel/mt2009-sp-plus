# The New Pet System's window (uinewpet.py): dracaryS' PetInformationWindow
# as it was - its layout, its background and its sprites, cut out of the
# mod's dds files into mt2009_ui/newpet/ (our client keeps its own
# public.dds). Two buttons of the mod's size sit in the free bars beside its
# evolution button: summon/choose and release; the pet's picture changes to
# the next pet when there are more. The skill slots are made in uinewpet.py.
# Texts in CP1250 escapes.

IMG = "mt2009_ui/newpet/"

PET_UI_BG_WIDTH = 345
PET_UI_BG_HEIGHT = 493

LONG_LABEL_WIDTH = 266
LONG_LABEL_HEIGHT = 19
SHORT_LABLE_WIDTH = 90
SHORT_LABLE_HEIGHT = 20
MIDDLE_LABLE_WIDTH = 168
MIDDLE_LABLE_HEIGHT = 20

EXP_GAGUE_INTERVAL = 2
EXP_IMG_WIDTH = 16
EXP_IMG_HEIGHT = 16

GOLD_COLOR = 0xFFFEE3AE
WHITE_COLOR = 0xFFFFFFFF

window = {
	"name" : "PetInformationWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH - 176 - 200 - 146 - 145,
	"y" : SCREEN_HEIGHT - 37 - 565,

	"width" : PET_UI_BG_WIDTH,
	"height" : PET_UI_BG_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "window",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : PET_UI_BG_WIDTH,
			"height" : PET_UI_BG_HEIGHT,

			"children" :
			(
				{ "name" : "PetUIBG", "type" : "expanded_image", "style" : ("attach",), "x" : 0, "y" : 0, "image" : IMG + "pet_ui_bg.tga" },

				{
					"name" : "TitleWindow", "type" : "window", "x" : 20, "y" : 5, "width" : PET_UI_BG_WIDTH - 10 - 15, "height" : 15, "style" : ("attach",),
					"children" :
					(
						{ "name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "Pet", "all_align" : "center" },
					),
				},

				{
					"name" : "CloseButton",
					"type" : "button",
					"x" : PET_UI_BG_WIDTH - 10 - 11,
					"y" : 6,
					"default_image" : "d:/ymir work/ui/public/close_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/close_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/close_button_03.sub",
				},

				{
					"name" : "PetNameWindow", "type" : "window", "x" : 60, "y" : 45, "width" : LONG_LABEL_WIDTH, "height" : LONG_LABEL_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "PetName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "PetMobNameWindow", "type" : "window", "x" : 60, "y" : 70, "width" : LONG_LABEL_WIDTH, "height" : LONG_LABEL_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "PetMobName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "LevelWindow", "type" : "window", "x" : 23, "y" : 119, "width" : SHORT_LABLE_WIDTH, "height" : SHORT_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "LevelTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "Poziom", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
						{ "name" : "LevelValue", "type" : "text", "x" : 0, "y" : 22, "text" : "", "color" : WHITE_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "ExpWindow", "type" : "window", "x" : 126, "y" : 119, "width" : SHORT_LABLE_WIDTH, "height" : SHORT_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "ExpTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "Do\x9cwiadczenie", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "UpBringing_Pet_EXP_Gauge_Board",
					"type" : "window",

					"x" : 127,
					"y" : 145,

					"width" : EXP_IMG_WIDTH * 5 + EXP_GAGUE_INTERVAL * 4,
					"height" : EXP_IMG_HEIGHT,

					"children" :
					(
						{ "name" : "UpBringing_Pet_EXPGauge_01", "type" : "expanded_image", "style" : ("not_pick",), "x" : 0, "y" : 0, "image" : IMG + "exp_on.tga" },
						{ "name" : "UpBringing_Pet_EXPGauge_02", "type" : "expanded_image", "style" : ("not_pick",), "x" : EXP_IMG_WIDTH + EXP_GAGUE_INTERVAL, "y" : 0, "image" : IMG + "exp_on.tga" },
						{ "name" : "UpBringing_Pet_EXPGauge_03", "type" : "expanded_image", "style" : ("not_pick",), "x" : EXP_IMG_WIDTH * 2 + EXP_GAGUE_INTERVAL * 2, "y" : 0, "image" : IMG + "exp_on.tga" },
						{ "name" : "UpBringing_Pet_EXPGauge_04", "type" : "expanded_image", "style" : ("not_pick",), "x" : EXP_IMG_WIDTH * 3 + EXP_GAGUE_INTERVAL * 3, "y" : 0, "image" : IMG + "exp_on.tga" },
					),
				},

				{
					"name" : "AgeWindow", "type" : "window", "x" : 227, "y" : 119, "width" : SHORT_LABLE_WIDTH, "height" : SHORT_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "AgeTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "Ewolucja", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
						{ "name" : "AgeValue", "type" : "text", "x" : 0, "y" : 22, "text" : "", "color" : WHITE_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "LifeWindow", "type" : "window", "x" : 23, "y" : 164, "width" : 168, "height" : SHORT_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "LifeTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "Energia \xbfyciowa", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
						{ "name" : "LifeTextValue", "type" : "text", "x" : 0, "y" : 24, "text" : "", "color" : WHITE_COLOR, "all_align" : "center", "outline" : 1 },
						{
							"name" : "LifeGauge",
							"type" : "ani_image",
							"x" : 10,
							"y" : 49,
							"delay" : 6,
							"images" :
							(
								"D:/Ymir Work/UI/Pattern/HPGauge/01.tga",
								"D:/Ymir Work/UI/Pattern/HPGauge/02.tga",
								"D:/Ymir Work/UI/Pattern/HPGauge/03.tga",
								"D:/Ymir Work/UI/Pattern/HPGauge/04.tga",
								"D:/Ymir Work/UI/Pattern/HPGauge/05.tga",
								"D:/Ymir Work/UI/Pattern/HPGauge/06.tga",
								"D:/Ymir Work/UI/Pattern/HPGauge/07.tga",
							),
						},
					),
				},

				# The two free bars beside the mod's evolution button.
				{
					"name" : "SummonButton",
					"type" : "button",
					"x" : 204,
					"y" : 169,
					"default_image" : IMG + "feed_button_default.tga",
					"over_image" : IMG + "feed_button_over.tga",
					"down_image" : IMG + "feed_button_down.tga",
					"text" : "Przywo\xb3aj",
					"text_color" : GOLD_COLOR,
				},
				{
					"name" : "FeedEvolButton",
					"type" : "button",
					"x" : 204,
					"y" : 192,
					"default_image" : IMG + "feed_button_default.tga",
					"over_image" : IMG + "feed_button_over.tga",
					"down_image" : IMG + "feed_button_down.tga",
					"text" : "Ewolucja",
					"text_color" : GOLD_COLOR,
				},
				{
					"name" : "ReleaseButton",
					"type" : "button",
					"x" : 204,
					"y" : 215,
					"default_image" : IMG + "feed_button_default.tga",
					"over_image" : IMG + "feed_button_over.tga",
					"down_image" : IMG + "feed_button_down.tga",
					"text" : "Wypu\x9c\xe6",
					"text_color" : GOLD_COLOR,
				},

				{
					"name" : "AbilitiesWindow", "type" : "window", "x" : 43, "y" : 254, "width" : LONG_LABEL_WIDTH, "height" : LONG_LABEL_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "AbilitiesName", "type" : "text", "x" : 0, "y" : 0, "text" : "Bonusy", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "FirstBonusWindow", "type" : "window", "x" : 20, "y" : 279, "width" : MIDDLE_LABLE_WIDTH, "height" : MIDDLE_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "bonus_title_0", "type" : "text", "x" : 0, "y" : 0, "text" : "", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
						{ "name" : "bonus_value_0", "type" : "text", "x" : 155, "y" : 0, "text" : "", "color" : WHITE_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},
				{
					"name" : "SecondBonusWindow", "type" : "window", "x" : 20, "y" : 301, "width" : MIDDLE_LABLE_WIDTH, "height" : MIDDLE_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "bonus_title_1", "type" : "text", "x" : 0, "y" : 0, "text" : "", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
						{ "name" : "bonus_value_1", "type" : "text", "x" : 155, "y" : 0, "text" : "", "color" : WHITE_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},
				{
					"name" : "ThirdBonusWindow", "type" : "window", "x" : 20, "y" : 323, "width" : MIDDLE_LABLE_WIDTH, "height" : MIDDLE_LABLE_HEIGHT, "style" : ("attach",),
					"children" :
					(
						{ "name" : "bonus_title_2", "type" : "text", "x" : 0, "y" : 0, "text" : "", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
						{ "name" : "bonus_value_2", "type" : "text", "x" : 155, "y" : 0, "text" : "", "color" : WHITE_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},

				{
					"name" : "PetSkillWindow", "type" : "window", "x" : 11, "y" : 366, "width" : 120, "height" : 20, "style" : ("attach",),
					"children" :
					(
						{ "name" : "PetSkillTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "Umiej\xeatno\x9cci", "color" : GOLD_COLOR, "all_align" : "center", "outline" : 1 },
					),
				},
			),
		},
	),
}
