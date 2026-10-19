import ui
OPEN_WHISPER_EVENT = "OPEN_WHISPER" # args | name: string
ADD_AFFECT_EVENT = "ADD_AFFECT" # args | type: number, pointIdx: number, value: number, duration: number
SPECIAL_FLAG_UPDATE = "SPECIAL_FLAG_UPDATE" # args | flag: string, value: number

ADD_ITEM_TO_SHOP_BUILDER = "ADD_ITEM_TO_SHOP_BUILDER" # args | sourceSlotIndex: number, sourceWindowType: number
REMOVE_ITEM_FROM_SHOP_BUILDER = "REMOVE_ITEM_FROM_SHOP_BUILDER" # args | sourceSlotIndex: number, sourceWindowType: number
OPEN_PRIVATE_SHOP_BUILDER = "OPEN_PRIVATE_SHOP_BUILDER" # args |
OPEN_PRIVATE_SHOP = "OPEN_PRIVATE_SHOP" # args |
CLOSE_PRIVATE_SHOP_BUILDER= "CLOSE_PRIVATE_SHOP_BUILDER" # args |

CHANGE_NIGHT_MODE = "CHANGE_NIGHT_MODE" # args | mode: number

ADD_FLOATING_TEXT = "ADD_FLOATING_TEXT" # args | text: string, is_negative: boolean
EVENT_MARK_SHOP_CURRENT = "EVENT_MARK_SHOP_CURRENT" # args: vid: number, is_offline: boolean
EVENT_MARK_SHOP_VIEWED = "EVENT_MARK_SHOP_VIEWED" # args: vid: number, is_offline: boolean

EVENT_HORSE_SUMMON = "EVENT_HORSE_SUMMON" # args: isSummoned: boolean

EVENT_USE_CODE_VOUCHER = "EVENT_USE_CODE_VOUCHER" # args: response: number


FIXED_TIMESTEP_UPDATE = 167
class DelayedEvent:
	def __init__(self, delay, *args):
		self.delay = delay
		self.args = args
		self.timer = 0

	def Destroy(self):
		self.args = None

class EventManager(object):
	_instance = None

	def __new__(cls):
		if not cls._instance:
			cls._instance = super(EventManager, cls).__new__(cls)
			cls._instance.events = {}
			cls._instance.delayed_events = {}
		return cls._instance

	def __register_event(self, eventName):
		self.events[eventName] = set()

	def add_observer(self, event, observer):
		# print "add_observer"
		if not self.events.has_key(event):
			self.__register_event(event)
		self.events[event].add(observer)

	def remove_observer(self, event, observer):
		if self.events.has_key(event):
			self.events[event].discard(observer)

	def clear_event(self, event):
		if self.events.has_key(event):
			self.events[event].clear()
			self.events.pop(event, None)

	def unregister_all_events(self):
		print "unregister_all_events"
		for key in self.events:
			self.events[key].clear()
		self.events.clear()

	def send_event(self, event, *args):
		if self.events.has_key(event):
			for observer in self.events[event]:
				observer(*args)


	def send_delayed_event(self, event, delay, *args):
		if self.delayed_events.has_key(event):
			return

		if delay == 0:
			self.send_event(event, *args)
			return

		self.delayed_events[event] = DelayedEvent(int(delay*10000), *args)

	def Update(self):
		if len(self.delayed_events) < 1:
			return

		list_of_keys = list(self.delayed_events)
		for event_name in list_of_keys:
			event = self.delayed_events[event_name]
			event.timer += FIXED_TIMESTEP_UPDATE
			if event.timer >= event.delay:
				self.send_event(event_name, *event.args)
				event.Destroy()
				self.delayed_events.pop(event_name)
