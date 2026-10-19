import eventManager
import ui
import chr
import player
import localeInfo
import special_flags

VALUE_PER_RANK = [
	3000,
	15000,  # 12000
	36000,  # 21000
	38500  # 2500
]

def GET_FRACTION_ID_BY_FLAG(flag):
	if flag == special_flags.REPUTATION_DESERT:
		return 1
	elif flag == special_flags.REPUTATION_ORC_VALLEY:
		return 2

def GET_FRACTION_NAME(fraction):
	if fraction == 1:
		return localeInfo.REPUTATION_DESERT
	elif fraction == 2:
		return localeInfo.REPUTATION_ORC_VALLEY
	else:
		return "NONAME"

def GET_MAX_VALUE_PER_RANK(rank):
	if rank < 0:
		return 0

	return VALUE_PER_RANK[rank]

def GET_REPUTATION_RANK(value):
	if value < VALUE_PER_RANK[0]:
		return 0
	if value < VALUE_PER_RANK[1]:
		return 1
	if value < VALUE_PER_RANK[2]:
		return 2
	else:
		return 3

def GET_RANK_NAME(rank):
	rank_name = [
		localeInfo.REPUTATION_RANK0,
		localeInfo.REPUTATION_RANK1,
		localeInfo.REPUTATION_RANK2,
		localeInfo.REPUTATION_RANK3,
	]
	return rank_name[rank]

def GET_RANK_NAME_BY_TOTAL_VALUE(value):
	return GET_RANK_NAME(GET_REPUTATION_RANK(value))

def GET_RANK_COLOR(rank):
	rank_color = [
		"d6b45c",
		"9fd65c",
		"48bd46",
		"38d6a9"
	]
	return rank_color[rank]

class ReputationBar(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self, "UI_BOTTOM")
		self.__Initialize()
		self.LoadDialog()

		eventManager.EventManager().add_observer(eventManager.SPECIAL_FLAG_UPDATE, self.__OnSpecialFlagUpdate)

	def __del__(self):
		ui.ScriptWindow.__del__(self)


	def __Initialize(self):
		self.vid = 0
		self.fraction = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.__Initialize()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/reputationbar.py")

			self.bar = self.GetChild("bar")
			self.nameLabel = self.GetChild("ReputationNameLabel")
			self.progressBar = self.GetChild("ProgressBar")
			self.progressLabel = self.GetChild("ProgressLabel")

		except:
			import exception
			exception.Abort("ReputationBar.LoadDialog.BindObject")

	def RefreshBar(self):
		total_value = special_flags.GetReputation(self.fraction)

		rank = GET_REPUTATION_RANK(total_value)
		previous_rank_value = GET_MAX_VALUE_PER_RANK(rank-1)
		current_rank_value = total_value - previous_rank_value
		max_rank_value = GET_MAX_VALUE_PER_RANK(rank) - previous_rank_value

		self.progressBar.SetPercentage(current_rank_value, max_rank_value)
		self.progressLabel.SetText("%s/%s - |cff%s%s|r" % (localeInfo.NumberToString(current_rank_value), localeInfo.NumberToString(max_rank_value), GET_RANK_COLOR(rank), GET_RANK_NAME(rank)))
		self.SetName(rank)

	def SetName(self, rank):
		self.nameLabel.SetText("%s" % GET_FRACTION_NAME(self.fraction))

	def __OnSpecialFlagUpdate(self, type, value):
		if special_flags.IsReputationFlag(type):
			self.RefreshBar()

	def OnUpdate(self):
		if not self.vid:
			return

		if chr.GetInstanceType(self.vid) not in [chr.INSTANCE_TYPE_NPC]:
			self.Hide()

		self.bar.Show()

		x, y = chr.GetProjectPosition(self.vid, 300)
		self.SetPosition(x - self.GetWidth() / 2, y - self.GetHeight() / 2)

		LIMIT_RANGE = 3000
		# The NPC may have left the view since the last frame.
		position = chr.GetPixelPosition(self.vid)
		if not position:
			self.Hide()
			return
		(to_x, to_y, to_z) = position
		(my_x, my_y, my_z) = player.GetMainCharacterPosition()
		if abs(my_x - to_x) <= LIMIT_RANGE and abs(my_y - to_y) <= LIMIT_RANGE:
			self.bar.Show()
		else:
			self.bar.Hide()

	def Open(self, vid, fraction):
		self.vid = vid
		self.fraction = fraction
		self.RefreshBar()
		self.Show()
