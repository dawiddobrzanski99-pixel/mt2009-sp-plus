# The New Pet System's hatching / renaming window (uinewpet.py): dracaryS'
# nameinputwindow as it was, its sprites in mt2009_ui/newpet/.
# Texts in CP1250 escapes.

IMG = "mt2009_ui/newpet/"

HATCHING_WINDOW_WIDTH = 176
HATCHING_WINDOW_HEIGHT = 184

window = {
	"name" : "PetHatchingWindow",
	"style" : ("movable", "float",),
	"x" : SCREEN_WIDTH / 2 - HATCHING_WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - HATCHING_WINDOW_HEIGHT / 2,
	"width" : HATCHING_WINDOW_WIDTH,
	"height" : HATCHING_WINDOW_HEIGHT,
	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : HATCHING_WINDOW_WIDTH,
			"height" : HATCHING_WINDOW_HEIGHT,
			"children" :
			(
				{
					"name" : "Titlebar",
					"type" : "titlebar",
					"style" : ("attach",),
					"x" : 0,
					"y" : 0,
					"width" : HATCHING_WINDOW_WIDTH - 2,
					"children" :
					(
						{ "name" : "TitleName", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
					),
				},
				{
					"name" : "SlotBG",
					"type" : "expanded_image",
					"style" : ("attach",),
					"x" : 68,
					"y" : 34,
					"image" : IMG + "pet_incu_slot_001.tga",
				},
				{
					"name" : "ItemSlot",
					"type" : "slot",
					"x" : 68 + 4,
					"y" : 34 + 4,
					"width" : 32,
					"height" : 32,
					"slot" : ({ "index" : 0, "x" : 0, "y" : 0, "width" : 32, "height" : 32 },),
				},
				{
					"name" : "HatchingMoneyWindow", "type" : "window", "x" : 13, "y" : 132, "width" : 150, "height" : 14, "style" : ("attach",),
					"children" :
					(
						{ "name" : "HatchingMoney", "type" : "text", "x" : 0, "y" : 0, "text" : "", "r" : 1.0, "g" : 1.0, "b" : 1.0, "all_align" : "center" },
					),
				},
				{
					"name" : "acceptbtn",
					"type" : "button",
					"x" : 39,
					"y" : 151,
					"text" : "Akceptuj",
					"default_image" : IMG + "largeb_button_01.tga",
					"over_image" : IMG + "largeb_button_02.tga",
					"down_image" : IMG + "largeb_button_03.tga",
				},
				{
					"name" : "PetNamingBG",
					"type" : "expanded_image",
					"style" : ("attach",),
					"x" : 12,
					"y" : 78,
					"image" : IMG + "pet_incu_001.tga",
					"children" :
					(
						{
							"name" : "InputString",
							"type" : "editline",
							"x" : 11,
							"y" : 28,
							"width" : 129,
							"height" : 16,
							"input_limit" : 12,
						},
					),
				},
				{
					"name" : "PetNamingTitleWindow", "type" : "window", "x" : 22, "y" : 86, "width" : 130, "height" : 14, "style" : ("attach",),
					"children" :
					(
						{ "name" : "PetNamingTitle", "type" : "text", "x" : 0, "y" : 0, "text" : "", "all_align" : "center" },
					),
				},
			),
		},
	),
}
