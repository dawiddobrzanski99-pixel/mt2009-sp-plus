__basePath = "d:/ymir work/ui/flamewind/"
public = __basePath + "public/"
inventory = __basePath + "inventory/"
fishing = __basePath + "fishing/"
affect = __basePath + "affect/"
hair = __basePath + "hair/"
itemshop = __basePath + "itemshop/"
windows = __basePath + "windows/"

def GetPublic(item):
	return public + item + ".sub"

def GetInventory(item):
	return inventory + item + ".sub"

def GetFishing(item):
	return fishing + item + ".sub"

def GetAffect(item):
	return affect + item + ".sub"

def GetHair(item):
	return hair + item + ".sub"

def GetItemShop(item):
	return itemshop + item + ".sub"

def GetCustom(path, item):
	return __basePath + path + "/" + item + ".sub"

def GetWindows(item):
	return windows + item + ".sub"

