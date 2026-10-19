# The Battle Pass window (uibattlepass.py): the layout of the operator's
# chosen Battle Pass window, 537 x 297 - the mission list on the left with
# its scroll bar (made in uibattlepass.py), the mission's details on the
# right, the season's summary and the final reward below them.
# Texts in CP1250 escapes.

IMG = "mt2009_ui/battle_pass/"

window = {
	"name" : "Battlepass",

	"x" : 0,
	"y" : 0,

	"style" : ("movable", "float",),

	"width" : 537,
	"height" : 297,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : 537,
			"height" : 297,

			"children" :
			(
				{
					"name" : "board_misiuni", "type" : "image", "style" : ("attach",), "x" : 10, "y" : 30, "image" : IMG + "mission_board.tga",
				},
				{
					"name" : "DesignTop", "type" : "image", "style" : ("attach",), "x" : 299 + 18, "y" : 30, "image" : IMG + "info_bg.tga",
				},
				{
					"name" : "BpassMissioninfo", "type" : "text", "x" : 370 + 10, "y" : 35, "text" : "Informacje o misji",
				},
				{
					"name" : "BpassMissionName", "type" : "text", "x" : 320 + 3, "y" : 54, "text" : "Nazwa",
				},
				{
					"name" : "BpassMissionType", "type" : "text", "x" : 320 + 3, "y" : 54 + 20, "text" : "Typ",
				},
				{
					"name" : "BpassMissionStatus", "type" : "text", "x" : 320 + 3, "y" : 74 + 20, "text" : "Status",
				},
				{
					"name" : "BpassMissionProgress", "type" : "text", "x" : 320 + 3, "y" : 94 + 20, "text" : "Post\xeap",
				},
				{
					"name" : "BPassMissionDescription", "type" : "text", "x" : 320 + 3, "y" : 114 + 20, "text" : "Opis",
				},
				{
					"name" : "BpassSummary", "type" : "text", "x" : 358, "y" : 174 + 24, "text" : "Podsumowanie Battle Passa",
				},
				{
					"name" : "FinalReward", "type" : "button", "x" : 330, "y" : 254,
					"default_image" : IMG + "reward_normal.tga",
					"over_image" : IMG + "reward_over.tga",
					"down_image" : IMG + "reward_down.tga",
				},
				{
					"name" : "TitleBar", "type" : "titlebar", "style" : ("attach",), "x" : 8, "y" : 8, "width" : 537 - 15, "color" : "gray",
					"children" :
					(
						{
							"name" : "TitleName", "type" : "text", "x" : (537 - 15) / 2, "y" : 4, "text" : "Battle Pass", "text_horizontal_align" : "center",
						},
					),
				},
			),
		},
	),
}
