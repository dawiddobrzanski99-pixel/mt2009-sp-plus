import ui
import app
import localeInfo
import eventManager
import constInfo
import file_utils
import simplejson as json
import player

PLAYER_STATS_LOCALE = {
	"stat_monster": localeInfo.PLAYER_STATS_MONSTER,
	"stat_boss": localeInfo.PLAYER_STATS_BOSS,
	"stat_miniboss": localeInfo.PLAYER_STATS_MINIBOSS,
	"stat_dungeon": localeInfo.PLAYER_STATS_DUNGEON,
	"stat_empire": localeInfo.PLAYER_STATS_EMPIRE,
	"stat_duel": localeInfo.PLAYER_STATS_DUEL,
	"stat_stone": localeInfo.PLAYER_STATS_STONE,
	"stat_mining": localeInfo.PLAYER_STATS_MINING,
	"stat_fishing": localeInfo.PLAYER_STATS_FISHING,
	"stat_herbalism": localeInfo.PLAYER_STATS_HERBALISM,
	"stat_chest": localeInfo.PLAYER_STATS_CHEST,
	"stat_death": localeInfo.PLAYER_STATS_DEATH,
	"stat_death_player": localeInfo.PLAYER_STATS_DEATH_PLAYER,
	"stat_death_mob": localeInfo.PLAYER_STATS_DEATH_MOB,
	"stat_damage": localeInfo.PLAYER_STATS_DAMAGE,
	"stat_damage_horse": localeInfo.PLAYER_STATS_DAMAGE_HORSE,
	"stat_damage_skill": localeInfo.PLAYER_STATS_DAMAGE_SKILL,
	"stat_gold": localeInfo.PLAYER_STATS_GOLD,
	"stat_sell_shop": localeInfo.PLAYER_STATS_GOLD_SELL_SHOP,
	"stat_questbook": localeInfo.PLAYER_STATS_QUESTBOOK,
	"stat_refine_success": localeInfo.PLAYER_STATS_REFINE_SUCCESS,
	"stat_refine_fail_smith": localeInfo.PLAYER_STATS_REFINE_FAIL_SMITH,
}

STATS_ORDER = [
	"stat_monster",
	"stat_boss",
	"stat_miniboss",
	"stat_stone",
	"stat_dungeon",
	"stat_empire",
	"stat_duel",
	"stat_mining",
	"stat_fishing",
	"stat_herbalism",
	"stat_chest",
	"stat_questbook",
	"stat_death",
	"stat_death_player",
	"stat_death_mob",
	"stat_damage",
	"stat_damage_horse",
	"stat_damage_skill",
	"stat_gold",
	"stat_sell_shop",
	"stat_refine_success",
	"stat_refine_fail_smith",
]

def is_no_save_session(flag):
	return flag in ["stat_damage", "stat_damage_horse", "stat_damage_skill"]

class PlayerStatsWindow(ui.ScriptWindow):
	class StatItem(ui.TextValueBar):
		def __init__(self, name):
			ui.TextValueBar.__init__(self, name, "-", 268, 20)
			self.Show()

		def __del__(self):
			ui.TextValueBar.__del__(self)

		def SetValue(self, value):
			self.SetValueLabel(localeInfo.NumberToString(value))

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()
		eventManager.EventManager().add_observer(eventManager.SPECIAL_FLAG_UPDATE, self.UpdateStat)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.stats_dict = {}
		self.session_dict = {}
		self.current_session_values_dict = {}
		self.is_loaded = False

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.__Initialize()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/playerstatswindow.py")

			self.board = self.GetChild("Board")
			self.content = self.GetChild("ContentWindow")
			self.mask = self.GetChild("ContentMask")
			self.generalBar = self.GetChild("GeneralTitleBar")
			self.sessionBar = self.GetChild("SessionTitleBar")
			self.sessionTime = self.GetChild("SessionTime")
			self.resetSessionBtn = self.GetChild("ResetButton")
			self.titleBar = self.GetChild("TitleBar")
			self.scrollBar = self.GetChild("ScrollBar")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

			self.scrollBar.SetScrollContent(self.mask, self.content)
			self.scrollBar.SAFE_SetOnWheelEvent(self.content)

			self.__AddContentItem(self.generalBar)
			for flag in STATS_ORDER:
				self.__AddStat(flag, self.stats_dict)
			self.__AddContentItem(self.sessionBar)

			self.resetSessionBtn.SAFE_SetEvent(self.StartSession)

		except:
			import exception
			exception.Abort("PlayerStatsWindow.LoadDialog.BindObject")

	def __AddStat(self, flag_name, dict_container):
		if not PLAYER_STATS_LOCALE.has_key(flag_name):
			return

		stat = self.StatItem(PLAYER_STATS_LOCALE[flag_name])
		stat.SetParent(self.content)
		stat.SetPosition(8, 0)
		stat.SetBarBackground(len(dict_container) % 2 == 0)
		self.__AddContentItem(stat)
		dict_container[flag_name] = stat
		return stat

	def __AddContentItem(self, item):
		x, y = item.GetLocalPosition()
		item.SetPosition(x, self.content.GetHeight())
		self.content.SetHeight(self.content.GetHeight() + item.GetHeight())
		item.SetClippingMaskWindow(self.mask)
		self.scrollBar.ResizeScrollBar()

	def __RefreshContentItems(self):
		self.content.SetHeight(0)
		self.__AddContentItem(self.generalBar)
		for flag in STATS_ORDER:
			if self.stats_dict.has_key(flag):
				self.__AddContentItem(self.stats_dict[flag])

		self.__AddContentItem(self.sessionBar)
		for flag in STATS_ORDER:
			if self.session_dict.has_key(flag):
				self.__AddContentItem(self.session_dict[flag])

	def UpdateStat(self, flag_name, value):
		if "stat_" in flag_name and self.stats_dict.has_key(flag_name):
			self.stats_dict[flag_name].SetValue(value)

			if is_no_save_session(flag_name):
				return

			new_session_value = 0
			if self.current_session_values_dict.has_key(flag_name):
				session_value = self.current_session_values_dict[flag_name]
				new_session_value = value - session_value
			if new_session_value > 0:
				if not self.session_dict.has_key(flag_name):
					self.__AddStat(flag_name, self.session_dict)

				self.session_dict[flag_name].SetValue(new_session_value)
				file_utils.WriteFile("cache/stats_session_%s.json" % player.GetName(), json.dumps(self.current_session_values_dict))

	def StartSession(self):
		for i in self.session_dict.itervalues():
			del i
			i = None

		self.session_dict = {}
		self.current_session_values_dict = {}
		for flag_name in PLAYER_STATS_LOCALE.iterkeys():
			if is_no_save_session(flag_name):
				continue

			value = 0
			if constInfo.SPECIAL_FLAG.has_key(flag_name):
				value = constInfo.SPECIAL_FLAG[flag_name]

			self.current_session_values_dict[flag_name] = value

		self.current_session_values_dict["session_time"] = app.GetGlobalTimeStamp()
		file_utils.WriteFile("cache/stats_session_%s.json" % player.GetName(), json.dumps(self.current_session_values_dict))
		self.__RefreshContentItems()

	def LoadSession(self):
		stringData = file_utils.GetFileContent("cache/stats_session_%s.json" % player.GetName())
		if stringData != "":
			self.current_session_values_dict = json.loads(stringData)
			for flag, value in self.current_session_values_dict.iteritems():
				cur_value = (constInfo.SPECIAL_FLAG[flag] if constInfo.SPECIAL_FLAG.has_key(flag) else 0) - value
				if cur_value > 0:
					item = self.__AddStat(flag, self.session_dict)
					item.SetValue(cur_value)
		else:
			self.StartSession()

	def UpdateSessionTime(self):
		if self.IsShow():
			session_duration = app.GetGlobalTimeStamp() - self.current_session_values_dict["session_time"]
			self.sessionTime.SetText(localeInfo.SecondToDHMS(session_duration, True))

	def Close(self):
		self.Hide()

	def Open(self):
		if self.IsShow():
			self.Close()
		else:
			self.Show()

			if not self.is_loaded:
				self.LoadSession()
				self.is_loaded = True

			self.UpdateSessionTime()
