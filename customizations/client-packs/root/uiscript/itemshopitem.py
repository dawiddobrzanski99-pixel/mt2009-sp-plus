import uiScriptLocale
import flamewindPath
import colorInfo

WINDOW_WIDTH = 439
WINDOW_MIN_HEIGHT = 61

CENTER_X = SCREEN_WIDTH/2 - WINDOW_WIDTH/2
CENTER_Y = SCREEN_HEIGHT/2 - WINDOW_MIN_HEIGHT/2

window = {
	"name" : "ItemShopItem",

	"x" : CENTER_X,
	"y" : CENTER_Y,

	"width" : WINDOW_WIDTH,
	"height" : WINDOW_MIN_HEIGHT,

	"children" :
	(
		{
			"name" : "TitleBar",
			"type" : "image",

			"x" : 0,
			"y" : 0,

			"image" : flamewindPath.GetPublic("bar"),
			
			"children" : (
				{
					"name" : "ItemTitle",
					"type" : "text",
					"x" : 7,
					"y" : 0,
					
					"vertical_align" : "center",
					"text_vertical_align" : "center",
					
					"text" : "Zaczarowanie Przedmiotu (Paczka 4x)",
					"bold" : True,
				},
				
				# {
				# 	"name" : "ItemPrice",
				# 	"type" : "text",
				# 	"x" : 7,
				# 	"y" : 0,
				#
				# 	"horizontal_align" : "right",
				# 	"text_horizontal_align" : "right",
				# 	"vertical_align" : "center",
				# 	"text_vertical_align" : "center",
				#
				# 	"text" : "Cena: |cffffc9481.000 SM|r",
				# 	"outline" : True,
				# },
			),
		},

		{
			"name" : "ItemSlot1",
			"type" : "image",
			"x" : 16,
			"y" : 24,
			
			"image" : "d:/ymir work/ui/public/slot_base.sub"
		},
		
		{
			"name" : "ItemSlot2",
			"type" : "image",
			"x" : 16,
			"y" : 24+32,
			
			"image" : "d:/ymir work/ui/public/slot_base.sub"
		},
		
		{
			"name" : "ItemSlot3",
			"type" : "image",
			"x" : 16,
			"y" : 24+64,
			
			"image" : "d:/ymir work/ui/public/slot_base.sub"
		},

		{
			"name": "ItemIcon",
			"type": "image",
			"x": 16,
			"y": 24,

			"image": "icon/item/itemmallb.tga"
		},
		
		# {
		# 	"name" : "AccountLimit",
		# 	"type" : "text",
		# 	"x" : 54,
		# 	"y" : 20,
		#
		# 	"vertical_align" : "bottom",
		# 	"text_vertical_align" : "bottom",
		#
		# 	"text" : "limit"
		# },

	 	{
			"name" : "ItemTime",
			"type" : "text",
			"x" : 54+18,
			"y" : 8,

			"vertical_align" : "bottom",
			"text_vertical_align" : "bottom",

			"bold" : True,
			"color" : colorInfo.GetColorFromColorTuple(colorInfo.ITEMSHOP_TIMED_CATEGORY_COLOR),

			"text" : "Koniec za xxx",
			"children" : (
				{
					"name" : "ClockIcon",
					"type" : "image",

					"x" : -18, "y" : -14,

					"image" : flamewindPath.GetPublic("time_0"),
				},

				{
					"name" : "ClockAnimation",
					"type" : "ani_image",

					"x" : -18, "y" : -14,

					"delay" : 8,
					"images" :
					(
						flamewindPath.GetPublic("time_0"),
						flamewindPath.GetPublic("time_1"),
						flamewindPath.GetPublic("time_2"),
						flamewindPath.GetPublic("time_3"),
						flamewindPath.GetPublic("time_4"),
						flamewindPath.GetPublic("time_5"),
						flamewindPath.GetPublic("time_6"),
						flamewindPath.GetPublic("time_7"),
					)
				},
			),
		},

		{
			"name" : "ItemSoldOut",
			"type" : "text",
			"x" : 54,
			"y" : 8,

			"text_vertical_align" : "bottom",
			"vertical_align" : "bottom",

			"bold" : True,
			"color" : colorInfo.GetColorFromColorTuple(colorInfo.TITLE_RGB_EVIL_4),

			"text" : "Wyprzedano."
		},
		
		{
			"name" : "BuyButton",
			"type" : "button",

			"x" : 104,
			"y" : 30,

			"horizontal_align" : "right",
			"vertical_align" : "bottom",

			"default_image" : flamewindPath.GetPublic("buy_button_01"),
			"over_image" : flamewindPath.GetPublic("buy_button_02"),
			"down_image" : flamewindPath.GetPublic("buy_button_03"),
		},

		{
			"name" : "ProgressBarBackground",
			"type" : "image",

			"x" : 102,
			"y" : 45,

			"horizontal_align" : "right",
			"vertical_align" : "bottom",

			"image" : flamewindPath.GetPublic("small_progress_bar"),
			"children" : (
				{
					"name": "Progress",
					"type": "expanded_image",

					"x": 1,
					"y": 1,

					"image": flamewindPath.GetPublic("small_progress_blue"),
				},
			),
		},
	),
}