import simplejson as json
import file_utils

GAME_SETTINGS = {}

def LoadSettings():
	stringData = file_utils.GetFileContent("cache/game_settings.json")
	if stringData != "":
		global GAME_SETTINGS
		GAME_SETTINGS = json.loads(stringData)
		if not GAME_SETTINGS.has_key("loaded"):
			GAME_SETTINGS["loaded"] = True

def SetKey(key, value):
	GAME_SETTINGS[key] = value
	Save()

def GetKey(key, defaultValue=None):
	if not GAME_SETTINGS.has_key(key):
		return defaultValue

	return GAME_SETTINGS[key]

def GetNumberKey(key):
	return GetKey(key, 0)

def GetStringKey(key):
	return GetKey(key, "")

def GetBoolKey(key):
	return GetKey(key, False)

def Save():
	if len(GAME_SETTINGS) > 0:
		file_utils.WriteFile("cache/game_settings.json", json.dumps(GAME_SETTINGS))
