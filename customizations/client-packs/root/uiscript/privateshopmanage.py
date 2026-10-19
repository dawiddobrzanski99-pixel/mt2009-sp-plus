import uiScriptLocale
import shop
import grp
import flamewindPath

WINDOW_WIDTH = 344
WINDOW_HEIGHT = 380

window = {
	"name" : "PrivateShopManage",

	"x" : SCREEN_WIDTH/2 - WINDOW_WIDTH/2,
	"y" : SCREEN_HEIGHT/2 - WINDOW_HEIGHT/2,

	"style" : ("movable", "float",),

	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,

			"children" :
			(
				## Title
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 8,

					"width" : WINDOW_WIDTH-15,
					"color" : "gray",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":-4, "y":4, "text":uiScriptLocale.SHOP_MANAGE_TITLE, "horizontal_align":"center", "text_horizontal_align":"center" },
						{
							"name": "ShopSearchButton",
							"type": "button",

							"x": 46,
							"y": -1,

							"horizontal_align": "right",
							"vertical_align": "center",
							"tooltip_text": uiScriptLocale.SHOP_SEARCH_TOOLTIP,

							"default_image": flamewindPath.GetPublic("search_button_01"),
							"over_image": flamewindPath.GetPublic("search_button_02"),
							"down_image": flamewindPath.GetPublic("search_button_03"),
						},

						## Find Shop
						{
							"name": "FindShopButton",
							"type": "button",

							"x": 46+24,
							"y": -1,

							"horizontal_align": "right",
							"vertical_align": "center",
							"tooltip_text": uiScriptLocale.SHOP_MANAGE_TOOLTIP_FIND_SHOP,

							"default_image": flamewindPath.GetPublic("find_button_01"),
							"over_image": flamewindPath.GetPublic("find_button_02"),
							"down_image": flamewindPath.GetPublic("find_button_03"),
						},
					),
				},
				
				## Name
				{
					"name" : "NameSlot",
					"type" : "slotbar",
					"x" : 14,
					"y" : 35,

					"horizontal_align" : "left",

					"width" : WINDOW_WIDTH - 27,
					"height" : 18,

					"children" :
					(
						{
							"name" : "NameLine",
							"type" : "text",
							"x" : 3,
							"y" : 3,
							"width" : 157,
							"height" : 15,
							"input_limit" : 25,
							"text" : "1234567890123456789012345",
						},
						
						{
							"name" : "ChangeShopSignButton",
							"type" : "button",

							"x" : 20,
							"y" : 0,

							"horizontal_align" : "right",
							"vertical_align" : "center",

							"default_image" : "d:/ymir work/ui/game/taskbar/open_chat_log_button_01.sub",
							"over_image" : "d:/ymir work/ui/game/taskbar/open_chat_log_button_02.sub",
							"down_image" : "d:/ymir work/ui/game/taskbar/open_chat_log_button_03.sub",
						},
					),
				},

				## Item Slot
				# {
				# 	"name" : "ItemSlot",
				# 	"type" : "grid_table",
				#
				# 	"x" : 12,
				# 	"y" : 34 + 26,
				#
				# 	"start_index" : 0,
				# 	"x_count" : shop.SHOP_PLAYER_WIDTH,
				# 	"y_count" : shop.SHOP_PLAYER_HEIGHT,
				# 	"x_step" : 32,
				# 	"y_step" : 32,
				#
				# 	"image" : "d:/ymir work/ui/public/Slot_Base.sub",
				# },
				
				## Earnings
				{
					"name" : "TotalEarningBar",
					"type" : "slotbar",
					"x" : 33,
					"y" : 35+25,

					"vertical_align" : "bottom",

					"width" : 108,
					"height" : 19,

					"children" :
					(
						{
							"name" : "TotalEarningLabel",
							"type" : "text",
							"x" : 0,
							"y" : 3,
							"text_horizontal_align" : "center",
							"horizontal_align" : "center",
							"text" : "20.000.000.000 Yang",
						},
						
						{
							"name":"Money_Icon",
							"type":"image",

							"x":-18,
							"y":3,

							"image":"d:/ymir work/ui/game/windows/money_icon.sub",
						},
					),
				},
				
				## TimeSelect
				{
					"name" : "TimeBar",
					"type" : "slotbar",
					"x" : 33,
					"y" : 35,
					
					"vertical_align" : "bottom",

					"width" : 108,
					"height" : 19,

					"children" :
					(
						{
							"name" : "TimeLeftLabel",
							"type" : "text",
							"x" : 0,
							"y" : 3,
							"text_horizontal_align" : "center",
							"horizontal_align" : "center",
							"text" : "Pozostalo 23:59:59",
						},

						{
							"name" : "ClockIcon",
							"type" : "image",

							"x" : -18, "y" : 2,

							"image" : flamewindPath.GetPublic("time_0"),
						},

						{
							"name" : "ClockAnimation",
							"type" : "ani_image",

							"x" : -18, "y" : 2,

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

				## Edit Shop
				{
					"name" : "EditShopButton",
					"type" : "button",

					"x" : 190,
					"y" : 33+25,

					"horizontal_align" : "right",
					"vertical_align" : "bottom",

					"default_image" : flamewindPath.GetPublic("edit_button_01"),
					"over_image" : flamewindPath.GetPublic("edit_button_02"),
					"down_image" : flamewindPath.GetPublic("edit_button_02"),
				},

				## Reopen
				{
					"name": "ReopenButton",
					"type": "button",

					"x": 190,
					"y": 33 + 25,

					"horizontal_align": "right",
					"vertical_align": "bottom",

					"default_image": flamewindPath.GetPublic("reopen_button_01"),
					"over_image": flamewindPath.GetPublic("reopen_button_02"),
					"down_image": flamewindPath.GetPublic("reopen_button_03"),
				},
				
				## Withdraw Gold
				{
					"name" : "WithdrawGoldButton",
					"type" : "button",

					"x" : 100,
					"y" : 33+25,

					"horizontal_align" : "right",
					"vertical_align" : "bottom",

					"default_image" : flamewindPath.GetPublic("withdraw_button_01"),
					"over_image" : flamewindPath.GetPublic("withdraw_button_02"),
					"down_image" : flamewindPath.GetPublic("withdraw_button_03"),
				},

				## Close
				{
					"name" : "CloseButton",
					"type" : "button",

					"x" : 100,
					"y" : 35,

					"horizontal_align" : "right",
					"vertical_align" : "bottom",

					"default_image" : flamewindPath.GetPublic("close_shop_01"),
					"over_image" : flamewindPath.GetPublic("close_shop_02"),
					"down_image" : flamewindPath.GetPublic("close_shop_03"),
				},

				## Withdraw Items
				{
					"name" : "WithdrawItemsButton",
					"type" : "button",

					"x" : 100,
					"y" : 35,

					"horizontal_align" : "right",
					"vertical_align" : "bottom",

					"default_image" : flamewindPath.GetPublic("withgdraw_item_button_01"),
					"over_image" : flamewindPath.GetPublic("withgdraw_item_button_02"),
					"down_image" : flamewindPath.GetPublic("withgdraw_item_button_03"),
				},

				## Logs
				{
					"name": "LogsButton",
					"type": "button",

					"x": 190,
					"y": 35,

					"horizontal_align": "right",
					"vertical_align": "bottom",

					"default_image": flamewindPath.GetPublic("logs_button_01"),
					"down_image": flamewindPath.GetPublic("logs_button_03"),
					"over_image": flamewindPath.GetPublic("logs_button_02"),
				},
			),
		},
		
		
		{
			"name" : "TooltipInfo",
			"type" : "thinboard",

			"x" : 0,
			"y" : -5,

			"horizontal_align" : "center",
			"vertical_align" : "bottom",

			"width" : 110,
			"height" : 30,
			
			"children" : (
				{
					"name" : "TooltipLabel",
					"type" : "text",

					"x" : 0,
					"y" : -1,

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"vertical_align" : "center",
					"text_vertical_align" : "center",

					"text" : "Tooltip info",
					
					"r" : float(255)/255,
					"g" : float(252)/255,
					"b" : float(22)/255,
				},
			),
		},
	),
}