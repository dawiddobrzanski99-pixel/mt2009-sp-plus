# A skill book's icon in a slot: the book with its own skill's emblem
# (2681e77b, 7 October: "Book says 'Dash' but has the three-way cut icon on
# it"). A book is vnum 50300 with its skill in socket 0, and the stock
# SetItemSlot (ui.py) drew it as the book of its skill's group, 50290..50297,
# whose icon carries one skill's emblem for the whole group - the warrior
# body group's is Three-Way Cut's - so every other skill's book showed
# another skill's picture, in every language. The name was always the
# socket's skill (uitooltip.__SetSkillBookToolTip, skill.GetSkillName).
#
# The pictures are playerbot_ui/skillbook/<skill vnum>.tga in the root pack
# (tools/generate_skillbook_icons.py, from the client's own book and skill
# art). A slot takes the resource pointer of a picture, which Python gets for
# an item's icon (item.GetIconImage) or a skill's, and for any file only from
# player.RegisterEmotionIcon/GetEmotionIconImage - the emotion window's
# table, keyed by an index; ours are past every emotion's (EMOTION_INDEX_BASE)
# so they can neither replace nor be replaced by one. A skill with no picture
# of ours keeps the group book.
#
# Python 2.7 as the client has it.

ICON = 'playerbot_ui/skillbook/%d.tga'
EMOTION_INDEX_BASE = 900000


_handles = {}


def IconImage(skillVnum):
	"""The handle of skillVnum's book picture for wndMgr.SetSlot, or 0."""
	try:
		skillVnum = int(skillVnum)
	except (TypeError, ValueError):
		return 0
	if skillVnum in _handles:
		return _handles[skillVnum]
	handle = 0
	if 0 < skillVnum < EMOTION_INDEX_BASE:
		try:
			import app
			import player
			path = ICON % skillVnum
			if app.IsExistFile(path):
				player.RegisterEmotionIcon(EMOTION_INDEX_BASE + skillVnum, path)
				handle = player.GetEmotionIconImage(EMOTION_INDEX_BASE + skillVnum)
		except Exception:
			handle = 0
	_handles[skillVnum] = handle
	return handle
