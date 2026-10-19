import uiScriptLocale
import flamewindPath

ROOT = "d:/ymir work/ui/minimap/"

window = {
	"name" : "AtlasWindow",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH - 136 - 256 - 10,
	"y" : 0,

	"width" : 256 + 15,
	"height" : 256 + 38,

	"children" :
	(
		## BOARD
		{
			"name" : "board",
			"type" : "board_with_titlebar",

			"x" : 0,
			"y" : 0,

			"width" : 256 + 15,
			"height" : 256 + 38,

			"title" : uiScriptLocale.ZONE_MAP,
			"children" :
			(
				{
					"name" : "ToggleScaleButton",
					"type" : "button",

					"x" : 45,
					"y" : 9,

					"horizontal_align" : "right",

					"default_image" : flamewindPath.GetPublic("shrink_button_01"),
					"over_image" : flamewindPath.GetPublic("shrink_button_02"),
					"down_image" : flamewindPath.GetPublic("shrink_button_03"),
				},
			)
		},
	),
}
