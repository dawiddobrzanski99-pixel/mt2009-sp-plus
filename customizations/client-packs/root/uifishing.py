import ui
import app
import constInfo
import eventManager
import grp
import gameSettings
import uiCommon
import localeInfo

EVENT_FISHING_GAME_START = "EVENT_FISHING_GAME_START" # args | bar_height: number, player_pos: number, start_delay: number
EVENT_FISHING_GAME_STOP = "EVENT_FISHING_GAME_STOP" # args | isWin: boolean
EVENT_FISHING_GAME_UPDATE = "EVENT_FISHING_GAME_UPDATE" # args | top_bar_pos: number, player_pos: number
EVENT_FISHING_PLAYER_UPDATE = "EVENT_FISHING_PLAYER_UPDATE" # args | player_pos: number
EVENT_FISHING_GAME_EVENT = "EVENT_FISHING_GAME_EVENT" # args | event_type: number, event_duration

FISHING_GAME_EVENT_NONE = 0
FISHING_GAME_EVENT_STOP = 1
FISHING_GAME_EVENT_REVERSE = 2
FISHING_GAME_EVENT_SPEEDUP = 3

class FishingGameDialog(ui.ScriptWindow):
	WINDOW_WIDTH = 110
	WINDOW_HEIGHT = 330

	FISHING_AREA_WIDTH = 32
	FISHING_AREA_HEIGHT = 290

	CLOSE_DELAY = 20000 # 2s

	BAR_NORMAL_COLOR = grp.GenerateColor(0.2235, 0.8078, 0.1647, 0.36)
	BAR_EVENT_STOP_COLOR = grp.GenerateColor(0.8078, 0.6784, 0.1647, 0.36)
	BAR_EVENT_SPEED_COLOR = grp.GenerateColor(0.1647, 0.5882, 0.8078, 0.36)
	BAR_EVENT_REVERSE_COLOR = grp.GenerateColor(0.7137, 0.251, 0.8823, 0.36)

	PLAYER_FISH_NORMAL_COLOR = (1.0, 1.0, 1.0, 1.0)
	# PLAYER_FISH_NORMAL_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)
	PLAYER_FISH_LOSE_COLOR = (1.0, 0.0, 0.0, 0.75)
	# PLAYER_FISH_LOSE_COLOR = grp.GenerateColor(1.0, 0.0, 0.0, 0.5)

	class FishGameEvent:
		def __init__(self, item, duration):
			self.item = None
			self.duration = 0
			self.SetEvent(item, duration)

		def Update(self):
			self.duration -= 1
			if self.duration < 1:
				if self.item.IsShow():
					self.item.Hide()
					return True
			return False

		def Destroy(self):
			self.item = None

		def SetEvent(self, item, duration):
			self.item = item
			self.duration = duration + 1 # + 1 bo sync z serwerem
			self.item.Show()

	class UpdatableItem:
		def __init__(self, item):
			self.item = item

			(x,y) = self.item.GetLocalPosition()
			self.startPos = y
			self.destPosition = y
			self.timer = 0
			self.speed = 0
			self.delay = 3500
			self.lastUpdate = 0

		def SetPosition(self, position, force=False):
			if force:
				self.startPos = position
				self.destPosition = position
				self.item.SetPosition(0, position)
				return

			deltaUpdate = constInfo.FIXED_TIME_SINCE_START - self.lastUpdate
			self.lastUpdate = constInfo.FIXED_TIME_SINCE_START
			print deltaUpdate, (deltaUpdate*1.2)
			if deltaUpdate < 1000:
				deltaUpdate = self.delay

			(x, y) = self.item.GetLocalPosition()
			self.startPos = float(y)
			self.destPosition = float(position)

			delta = self.destPosition - self.startPos
			self.speed = delta * 167 / deltaUpdate
			self.timer = 0

		def Destroy(self):
			self.item = None

		def OnFixedUpdate(self, deltaTime):
			distance = abs(self.destPosition - self.startPos)
			if distance > 0.2:
				self.startPos = self.startPos + self.speed
				self.item.SetPosition(0, self.startPos)
			else:
				self.item.SetPosition(0, self.destPosition)

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.bar_height = 0
		self.cooldown = 0
		self.closeTimer = 0
		self.startClose = False
		self.updatableItems = []
		self.fishEvents = {}
		self.currentEvent = None
		self.questionDialog = None

		self.LoadDialog()
		eventManager.EventManager().add_observer(EVENT_FISHING_GAME_START, self.__OnFishingGameStart)
		eventManager.EventManager().add_observer(EVENT_FISHING_GAME_STOP, self.__OnFishingGameStop)
		eventManager.EventManager().add_observer(EVENT_FISHING_GAME_UPDATE, self.__OnFishingGameUpdate)
		eventManager.EventManager().add_observer(EVENT_FISHING_PLAYER_UPDATE, self.__OnFishingPlayerUpdate)
		eventManager.EventManager().add_observer(EVENT_FISHING_GAME_EVENT, self.__OnFishingGameEvent)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		for item in self.updatableItems:
			item.Destroy()
		self.updatableItems = []

		if self.currentEvent:
			self.currentEvent.Destroy()
			self.currentEvent = None

		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/fishinggamedialog.py")

			self.fishingArea = self.GetChild("fishing_area")
			self.cooldownLabel = self.GetChild("cooldown_label")
			self.fishMechAnim = self.GetChild("fish_mech_anim")
			self.fishMech = self.GetChild("fish_mech")
			self.playerFishIcon = self.GetChild("player_fish_icon")
			self.helpPlayer = self.GetChild("help_stick_player")
			self.tutorialItems = (self.GetChild("help_stick_player"), self.GetChild("help_stick_area"))

			self.fishingBar = self.UpdatableItem(self.GetChild("fishing_bar"))
			self.playerFish = self.UpdatableItem(self.GetChild("player_fish"))
			self.updatableItems.append(self.playerFish)
			self.updatableItems.append(self.fishingBar)

			self.fishEvents = {
				FISHING_GAME_EVENT_STOP: {
					"item":self.GetChild("fish_event_pause"),
					"color":self.BAR_EVENT_STOP_COLOR,
				},

				FISHING_GAME_EVENT_REVERSE: {
					"item": self.GetChild("fish_event_reverse"),
					"color": self.BAR_EVENT_REVERSE_COLOR,
				},

				FISHING_GAME_EVENT_SPEEDUP: {
					"item": self.GetChild("fish_event_speed"),
					"color": self.BAR_EVENT_SPEED_COLOR,
				}
			}

			self.__HideAllEventIcons()

		except:
			import exception
			exception.Abort("FishingGameDialog.LoadDialog.BindObject")

	def __ShowQuestionDialog(self):
		self.__CloseQuestionDialog()

		dlg = uiCommon.QuestionDialog2()
		dlg.SetText1(localeInfo.FISHING_GAME_TUTORIAL_QUESTION1)
		dlg.SetText2(localeInfo.FISHING_GAME_TUTORIAL_QUESTION2)
		dlg.SAFE_SetAcceptEvent(self.__AcceptQuestionDialog)
		dlg.SAFE_SetCancelEvent(self.__CancelQuestionDialog)
		dlg.Open()
		self.questionDialog = dlg

	def __AcceptQuestionDialog(self):
		self.__CloseQuestionDialog()

	def __CancelQuestionDialog(self):
		self.__CloseQuestionDialog()
		gameSettings.SetKey("fish_tutorial_done", True)

	def __CloseQuestionDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

	def __CanShowTutorial(self):
		return not gameSettings.GetBoolKey("fish_tutorial_done")

	def __HideTutorial(self):
		for i in self.tutorialItems:
			i.Hide()

	def __ShowTutorial(self):
		if not self.__CanShowTutorial():
			self.__HideTutorial()
			return

		for i in self.tutorialItems:
			i.Show()

	def __HideAllEventIcons(self):
		for i in self.fishEvents.values():
			i["item"].Hide()

	def __StartAnimation(self):
		self.fishMech.Hide()
		self.fishMechAnim.Show()

	def __StopAnimation(self):
		self.fishMech.Show()
		self.fishMechAnim.Hide()

	def __OnFishingGameEvent(self, event_type, event_duration):
		eventItem = self.fishEvents[event_type]
		if not self.currentEvent:
			self.currentEvent = self.FishGameEvent(eventItem["item"], event_duration)
		else:
			self.currentEvent.SetEvent(eventItem["item"], event_duration)

		self.fishingBar.item.SetColor(eventItem["color"])

	def __OnFishingGameUpdate(self, top_bar_pos, player_pos):
		self.SetBarPosition(top_bar_pos)
		self.__OnFishingPlayerUpdate(player_pos)
		if self.currentEvent:
			if self.currentEvent.Update():
				self.fishingBar.item.SetColor(self.BAR_NORMAL_COLOR)

	def __OnFishingPlayerUpdate(self, player_pos):
		self.SetPlayerPosition(player_pos)

	def __OnFishingGameStart(self, bar_height, player_pos, start_delay):
		self.fishingBar.item.SetColor(self.BAR_NORMAL_COLOR)
		self.playerFishIcon.SetColor(*self.PLAYER_FISH_NORMAL_COLOR)
		self.__StopAnimation()
		self.__HideAllEventIcons()
		self.bar_height = bar_height
		self.fishingBar.item.SetHeight(self.__GetLocalBarHeight())
		self.SetBarPosition(bar_height, True)
		self.SetPlayerPosition(player_pos, True)
		self.cooldown = start_delay
		self.SetCooldown(start_delay)
		self.__ShowTutorial()
		self.Open()

	def __OnFishingGameStop(self, isWin):
		if isWin and self.__CanShowTutorial():
			self.__ShowQuestionDialog()

		if not isWin:
			self.playerFishIcon.SetColor(*self.PLAYER_FISH_LOSE_COLOR)

		if self.currentEvent:
			self.currentEvent.item.Hide()
			self.fishingBar.item.SetColor(self.BAR_NORMAL_COLOR)

		self.__StopAnimation()
		self.closeTimer = 0
		self.startClose = True

	def __GetLocalBarHeight(self):
		return self.bar_height * self.FISHING_AREA_HEIGHT / 100

	def __GetLocalBarPosition(self, top_bar_pos):
		return top_bar_pos * self.FISHING_AREA_HEIGHT / 100

	def SetPlayerPosition(self, player_pos, force=False):
		player_pos = min(player_pos, 100)
		self.playerFish.SetPosition(player_pos * self.FISHING_AREA_HEIGHT / 100, force)

	def SetBarPosition(self, top_bar_pos, force=False):
		top_bar_pos = min(top_bar_pos, 100)
		self.fishingBar.SetPosition(self.__GetLocalBarPosition(top_bar_pos), force)

	def OnFixedUpdate(self, deltaTime):
		for item in self.updatableItems:
			item.OnFixedUpdate(deltaTime)

		if self.startClose:
			self.closeTimer += deltaTime
			if self.closeTimer >= self.CLOSE_DELAY:
				self.closeTimer = 0
				self.startClose = False
				self.Close()

	def SetCooldown(self, leftSeconds):
		if leftSeconds > 0:
			self.cooldownLabel.SetText("%d..." % leftSeconds)
			self.cooldownLabel.Show()
		else:
			self.__StartAnimation()
			self.cooldownLabel.Hide()
			self.__HideTutorial()

	def Open(self):
		self.Show()

	def Close(self):
		self.Hide()
