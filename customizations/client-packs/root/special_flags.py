import constInfo

SHOP_SLOT_UNLOCK_PROGRESS_FLAG = "shop_unlock_slot"
HORSE_INVENTORY_SLOT = "horse_inventory_slot"
REPUTATION_DESERT = "reputation_desert"
REPUTATION_ORC_VALLEY = "reputation_orc_valley"

def GetFlag(flag):
	if not constInfo.SPECIAL_FLAG.has_key(flag):
		return 0
	else:
		return constInfo.SPECIAL_FLAG[flag]

def GetReputation(fraction):
	if fraction == 1:
		return GetFlag(REPUTATION_DESERT)
	elif fraction == 2:
		return GetFlag(REPUTATION_ORC_VALLEY)
	else:
		return 0

def IsReputationFlag(flag):
	if flag in (REPUTATION_DESERT, REPUTATION_ORC_VALLEY,):
		return True
	else:
		return False
