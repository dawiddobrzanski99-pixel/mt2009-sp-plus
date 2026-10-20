import constInfo
import localeInfo
import systemSetting

def GetFontName(fontName, fontSize):
	return fontName + ":" + str(fontSize)

def GetCurrentFont():
	return GetFontName(constInfo.CURRENT_GAME_FONT_NAME, constInfo.CURRENT_GAME_FONT_SIZE["DEFAULT"])

def GetCurrentFontLarge():
	return GetFontName(constInfo.CURRENT_GAME_FONT_NAME, constInfo.CURRENT_GAME_FONT_SIZE["LARGE"])

def GetCurrentFontSmall():
	return GetFontName(constInfo.CURRENT_GAME_FONT_NAME, constInfo.CURRENT_GAME_FONT_SIZE["SMALL"])

def GetCurrentFontHuge():
	return GetFontName(constInfo.CURRENT_GAME_FONT_NAME, constInfo.CURRENT_GAME_FONT_SIZE["HUGE"]) + "b"

def SetCurrentFont(fontName, fontSize):
	constInfo.CURRENT_GAME_FONT_NAME = fontName
	constInfo.CURRENT_GAME_FONT_SIZE["DEFAULT"] = fontSize
	constInfo.CURRENT_GAME_FONT_SIZE["LARGE"] = fontSize + 2
	constInfo.CURRENT_GAME_FONT_SIZE["HUGE"] = fontSize + 4
	constInfo.CURRENT_GAME_FONT_SIZE["SMALL"] = fontSize - 2

def SetFontOnGameStart():
	SetCurrentFont(systemSetting.GetFontName(), systemSetting.GetFontSize())

