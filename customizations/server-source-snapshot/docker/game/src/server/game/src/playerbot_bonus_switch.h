// MT2009 PLUS Bonus Switcher - MT2009_PLUS_BONUS_SWITCH_V1 (Autor: Vekirion)
// (Patryk, 5 October:
// "an UI window where a user puts in an item ... chooses which bonuses they
// want to target and at which values minimum ... uses 39028, 71084, 71284,
// 76014 ... 1 change costs 1 of the items ... 76014 first ... the speed easily
// adjustable by the user"; later the same day: a tab per item, "Wszystkie" or
// "Co najmniej X z", and "Zmien raz" - one change after a confirmation).
//
// The switching runs here, not in the client: the window (client root
// uibonusswitch.py) only sends what the player picked, and this side checks
// it, uses the change items up one per change and stops by itself. A client
// that spams the item's use would cost a packet a change and race the
// inventory; here a change is exactly what using the item by hand does
// (char_item.cpp, USE_CHANGE_ATTRIBUTE: the same checks, the same
// ChangeAttribute and its 76014 table, the same CHANGE_ATTRIBUTE item log),
// only paced by the player's speed.
//  - the change items, in the order they are used: 76014 (the "(B)" ones)
//    first, then 71084, 71284, 39028 - all four are ITEM_USE /
//    USE_CHANGE_ATTRIBUTE in our protos.
//  - the bonuses offered for an item are the ones its attribute set can roll:
//    world.item_attr's rows with a level for the set (g_map_itemAttr, as
//    PutAttributeWithLevel picks them), with the top value of that level, and
//    for a weapon with the damage addon (sAddonType 1) the average and skill
//    damage ApplyAverageTo rolls on every change.
//  - the goal: <need> of the picked bonuses on the item with at least their
//    values (need 0 = all of them). Nothing is used when it is already met.
//  - one run per item (the window's tab), up to MAX_RUNS a player at once,
//    each at the player's speed: 1 to m2_bonus_switch_max changes a second
//    (event flag, 0 = 20, at most 50); m2_bonus_switch_off 1 refuses new starts.
//  - a run stops on its goal, with no change item left, on the player's
//    "stop", and when its item moves, is traded or locked, or the player opens
//    a trade, a shop, the storehouse or dies. A logout or a warp just ends it.
//  - bots never: every command needs a real descriptor.
//
// To the client (game.py "BSW", uibonusswitch.py):
//   BSW attrs <cell> <vnum> <apply>:<max> ...   (the bonuses the item can roll)
//   BSW items <76014 count> <other change items' count> <70063 count> <70064 count>
//   BSW state <cell> <1 running | 0 not>
//   BSW progress <cell> <changes>                 (and an "items" line)
//   BSW done <cell> <reason> <changes> <76014 used> <others used>
//          reason: 1 goal met, 2 no change items, 3 stopped, 4 item gone, 5 busy
//   BSW changed <cell>                           (one change made, "once")
//   BSW msg <id> <data>
// From the client: "/bonus_switch info <cell>", "/bonus_switch items",
// "/bonus_switch start <cell> <speed> <need> <costume bonuses> <apply>:<min> [...]",
// "/bonus_switch once <cell>", "/bonus_switch stop [cell]".
#include "item_manager.h"
#include "char_manager.h"
#include "questmanager.h"
#include "log.h"
#include "constants.h"

namespace mt2009_bonus_switch
{
	const DWORD SWITCH_VNUMS[] = { 76014, 71084, 71284, 39028 };	// the order they are used in
	const int SWITCH_VNUM_COUNT = sizeof(SWITCH_VNUMS) / sizeof(SWITCH_VNUMS[0]);
	const DWORD PRIORITY_VNUM = 76014;
	// Costumes (Patryk, 5 October: "extend the functionality to costumes ...
	// 70063 and 70064"): char_item.cpp's GF26 costume items - 70063
	// USE_RESET_COSTUME_ATTR rolls the costume's bonuses anew, 1-3 of them,
	// 70064 USE_CHANGE_COSTUME_ATTR rolls new ones and keeps their number.
	// A costume run uses 70063 while the costume has fewer bonuses than it
	// needs (the count asked for, or the targets that must match), 70064 after.
	const DWORD COSTUME_RESET_VNUM = 70063;
	const DWORD COSTUME_CHANGE_VNUM = 70064;
	const int COSTUME_MAX_ATTR = 3;
	const int SPEED_DEFAULT_MAX = 20;
	const int SPEED_HARD_MAX = 50;
	const int MAX_RUNS = 5;					// the window's tabs
	const int MAX_CHANGES_PER_TICK = 4;		// a late tick catches up, a little
	const DWORD PROGRESS_EVERY_MS = 250;
	// ApplyAverageTo's top rolls: skill -30..30, average -2 x skill + 1..5
	const long ADDON_NORMAL_HIT_MAX = 65;
	const long ADDON_SKILL_MAX = 30;

	const char* const E_MAX_SPEED = "m2_bonus_switch_max";
	const char* const E_OFF = "m2_bonus_switch_off";

	enum
	{
		MSG_OFF = 1,
		MSG_BUSY = 2,
		MSG_BAD_ITEM = 3,
		MSG_NO_ATTR = 4,
		MSG_ITEM_LOCKED = 5,
		MSG_NO_TARGETS = 6,
		MSG_TOO_MANY = 7,			// data: how many bonuses the item has
		MSG_BAD_TARGET = 8,			// data: the apply
		MSG_TOO_HIGH = 9,			// data: the apply (the client has its max)
		MSG_NO_SWITCHERS = 10,
		MSG_ALREADY = 11,
		MSG_RUNNING = 12,			// "once" on an item being switched
		MSG_BAD_NEED = 13,			// data: how many bonuses were picked
		MSG_TOO_MANY_RUNS = 14,		// data: MAX_RUNS
		MSG_BAD_COUNT = 15,			// data: COSTUME_MAX_ATTR
		MSG_ROLL_FAILED = 16,		// a costume roll undone, the item kept
	};

	enum
	{
		END_FOUND = 1,
		END_NO_SWITCHERS = 2,
		END_STOPPED = 3,
		END_ITEM_GONE = 4,
		END_BUSY = 5,
	};

	struct Target
	{
		BYTE apply;
		long minValue;
	};

	struct Session
	{
		DWORD pid;
		WORD cell;
		DWORD itemId;
		int speed;
		int need;					// how many targets must match (all of them when 0)
		bool costume;
		int count;					// a costume's bonuses at least (0 = any number)
		std::vector<Target> targets;
		DWORD nextAt;
		DWORD lastProgress;
		int changes;
		int usedPriority;
		int usedOther;
	};

	typedef unsigned long long SessionKey;	// player id << 16 | cell
	std::map<SessionKey, Session> s_sessions;
	LPEVENT s_pkTick = NULL;
	std::map<DWORD, DWORD> s_mapLastCommand;

	SessionKey KeyOf(DWORD pid, WORD cell)
	{
		return ((SessionKey)pid << 16) | cell;
	}

	// Live bonus table (Patryk, 5 October: "make the choice rows read data db
	// live"). The cores get world.item_attr from the db core at boot and on
	// "/reload p"; here the table is read again straight from the database
	// when the window asks (an item put in, a tab opened, the list opened),
	// at most every ATTR_RELOAD_MS, so an edit in the table shows - and rolls -
	// without a reload or a restart. Read as the db core reads it
	// (ClientManagerBoot.cpp InitializeItemAttrTable: apply+0 is the index).
	const DWORD ATTR_RELOAD_MS = 2000;
	DWORD s_attrNextReload = 0;

	void RefreshItemAttr()
	{
		const DWORD now = get_dword_time();
		if (s_attrNextReload && (int)(now - s_attrNextReload) < 0)
			return;
		s_attrNextReload = now + ATTR_RELOAD_MS;

		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"SELECT apply, apply+0, prob, lv1, lv2, lv3, lv4, lv5, weapon, body, wrist, foots, neck, head, shield, ear"
#ifdef ENABLE_ITEM_ATTR_COSTUME
				", costume_body, costume_hair"
#if defined(ENABLE_ITEM_ATTR_COSTUME) && defined(ENABLE_WEAPON_COSTUME_SYSTEM)
				", costume_weapon"
#endif
#endif
#ifdef ENABLE_PENDANT_SYSTEM
				", pendant"
#endif
#ifdef ENABLE_GLOVE_SYSTEM
				", glove"
#endif
				" FROM world.item_attr ORDER BY apply"));
		SQLResult* res = msg ? msg->Get() : NULL;
		if (!res || !res->pSQLResult || !res->uiNumRows)
			return;	// no answer: the table the core has stays

		TItemAttrMap fresh;
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(res->pSQLResult)))
		{
			TItemAttrTable t{};
			int col = 0;
			strlcpy(t.szApply, row[col++], sizeof(t.szApply));
			str_to_number(t.dwApplyIndex, row[col++]);
			str_to_number(t.dwProb, row[col++]);
			for (int i = 0; i < ITEM_ATTRIBUTE_MAX_LEVEL; ++i)
				str_to_number(t.lValues[i], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_WEAPON], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_BODY], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_WRIST], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_FOOTS], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_NECK], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_HEAD], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_SHIELD], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_EAR], row[col++]);
#ifdef ENABLE_ITEM_ATTR_COSTUME
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_COSTUME_BODY], row[col++]);
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_COSTUME_HAIR], row[col++]);
#if defined(ENABLE_ITEM_ATTR_COSTUME) && defined(ENABLE_WEAPON_COSTUME_SYSTEM)
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_COSTUME_WEAPON], row[col++]);
#endif
#endif
#ifdef ENABLE_PENDANT_SYSTEM
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_PENDANT], row[col++]);
#endif
#ifdef ENABLE_GLOVE_SYSTEM
			str_to_number(t.bMaxLevelBySet[ATTRIBUTE_SET_GLOVE], row[col++]);
#endif
			if (t.dwApplyIndex < POINT_MAX_NUM)
				fresh[t.dwApplyIndex] = t;
		}
		if (fresh.empty())
			return;
		bool changed = fresh.size() != g_map_itemAttr.size();
		for (TItemAttrMap::const_iterator it = fresh.begin(); !changed && it != fresh.end(); ++it)
		{
			TItemAttrMap::const_iterator old = g_map_itemAttr.find(it->first);
			changed = old == g_map_itemAttr.end() || memcmp(&old->second, &it->second, sizeof(TItemAttrTable)) != 0;
		}
		if (!changed)
			return;
		g_map_itemAttr.swap(fresh);
		sys_log(0, "BONUS_SWITCH: world.item_attr changed, %u rows read again", (unsigned int)g_map_itemAttr.size());
	}

	bool Eligible(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	void Cmd(LPCHARACTER ch, const char* format, ...)
	{
		if (!Eligible(ch))
			return;
		char buf[480];
		va_list args;
		va_start(args, format);
		vsnprintf(buf, sizeof(buf), format, args);
		va_end(args);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "BSW %s", buf);
	}

	void Msg(LPCHARACTER ch, int id, long data = 0)
	{
		Cmd(ch, "msg %d %ld", id, data);
	}

	bool IsOff()
	{
		return quest::CQuestManager::instance().GetEventFlag(E_OFF) == 1;
	}

	int MaxSpeed()
	{
		const int m = quest::CQuestManager::instance().GetEventFlag(E_MAX_SPEED);
		return m > 0 ? std::min(m, SPEED_HARD_MAX) : SPEED_DEFAULT_MAX;
	}

	bool Busy(LPCHARACTER ch)
	{
		return ch->IsDead() || !ch->CanHandleItem() || ch->GetExchange() || ch->GetShop() || ch->GetMyShop() ||
			ch->IsOpenSafebox() || ch->IsCubeOpen();
	}

	bool HasDamageAddon(LPITEM item)
	{
		const TItemTable* proto = item->GetProto();
		return proto && proto->sAddonType == ATTR_DAMAGE_ADDON;
	}

	// The costumes 70063/70064 take (char_item.cpp: body, hair, weapon).
	bool IsCostume(LPITEM item)
	{
		if (item->GetType() != ITEM_COSTUME)
			return false;
		const BYTE sub = item->GetSubType();
		return sub == COSTUME_BODY || sub == COSTUME_HAIR
#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
			|| sub == COSTUME_WEAPON
#endif
			;
	}

	// What char_item.cpp's USE_CHANGE_ATTRIBUTE (for a costume its
	// USE_*_COSTUME_ATTR) refuses, and what a held, traded or locked item must
	// not have done to it.
	int CheckItem(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->GetOwner() != ch || item->GetWindow() != INVENTORY)
			return MSG_BAD_ITEM;
		const bool costume = IsCostume(item);
		if (!costume && item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR)
			return MSG_BAD_ITEM;
		if (item->GetAttributeSetIndex() < 0)
			return MSG_BAD_ITEM;
		const DWORD vnum = item->GetVnum();
		if ((vnum >= 11901 && vnum <= 11904) || vnum == 50201 || vnum == 50202)	// wedding items
			return MSG_BAD_ITEM;
		if (item->IsEquipped() || item->IsExchanging() || item->isLocked() || item->IsChangingAttr())
			return MSG_ITEM_LOCKED;
		if (!costume && item->GetAttributeCount() == 0)
			return MSG_NO_ATTR;	// 70063 gives a bare costume its first bonuses; nothing does a weapon's
		return 0;
	}

	// The top value the item can roll for the bonus, 0 when it cannot roll it.
	long MaxValue(LPITEM item, BYTE apply)
	{
		if (HasDamageAddon(item))
		{
			if (apply == POINT_NORMAL_HIT_DAMAGE_BONUS)
				return ADDON_NORMAL_HIT_MAX;
			if (apply == POINT_SKILL_DAMAGE_BONUS)
				return ADDON_SKILL_MAX;
		}
		const int set = item->GetAttributeSetIndex();
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM)
			return 0;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(apply);
		if (it == g_map_itemAttr.end() || it->second.dwProb == 0)
			return 0;
		int level = it->second.bMaxLevelBySet[set];
		if (level <= 0)
			return 0;
		level = std::min(level, (int)ITEM_ATTRIBUTE_MAX_LEVEL);
		return it->second.lValues[level - 1];
	}

	void SendAttrs(LPCHARACTER ch, int cell, LPITEM item)
	{
		char buf[440];
		int len = snprintf(buf, sizeof(buf), "attrs %d %u", cell, item->GetVnum());
		if (HasDamageAddon(item))
		{
			len += snprintf(buf + len, sizeof(buf) - len, " %d:%ld %d:%ld", POINT_NORMAL_HIT_DAMAGE_BONUS, ADDON_NORMAL_HIT_MAX,
					POINT_SKILL_DAMAGE_BONUS, ADDON_SKILL_MAX);
		}
		for (TItemAttrMap::const_iterator it = g_map_itemAttr.begin(); it != g_map_itemAttr.end(); ++it)
		{
			if (len <= 0 || len >= (int)sizeof(buf) - 12)
				break;
			const long top = MaxValue(item, (BYTE)it->first);
			if (top > 0)
				len += snprintf(buf + len, sizeof(buf) - len, " %u:%ld", (unsigned int)it->first, top);
		}
		Cmd(ch, "%s", buf);
	}

	void CountSwitchers(LPCHARACTER ch, int& priority, int& other)
	{
		priority = (int)ch->CountSpecifyItem(PRIORITY_VNUM);
		other = 0;
		for (int i = 0; i < SWITCH_VNUM_COUNT; ++i)
			if (SWITCH_VNUMS[i] != PRIORITY_VNUM)
				other += (int)ch->CountSpecifyItem(SWITCH_VNUMS[i]);
	}

	void SendItems(LPCHARACTER ch)
	{
		int priority, other;
		CountSwitchers(ch, priority, other);
		Cmd(ch, "items %d %d %d %d", priority, other, (int)ch->CountSpecifyItem(COSTUME_RESET_VNUM),
				(int)ch->CountSpecifyItem(COSTUME_CHANGE_VNUM));
	}

	LPITEM FindVnum(LPCHARACTER ch, DWORD vnum)
	{
		for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem((WORD)cell);
			if (item && item->GetVnum() == vnum && item->GetCount() > 0 && !item->IsExchanging() && !item->isLocked())
				return item;
		}
		return NULL;
	}

	// The costume item for the next roll: 70063 while the costume has fewer
	// bonuses than required (or none), else 70064 - or 70063 when no 70064
	// is left, which may change the number but is still a roll.
	LPITEM FindCostumeItem(LPCHARACTER ch, LPITEM costume, int required)
	{
		const int count = costume->GetAttributeCount();
		if (count == 0 || count < required)
			return FindVnum(ch, COSTUME_RESET_VNUM);
		LPITEM change = FindVnum(ch, COSTUME_CHANGE_VNUM);
		return change ? change : FindVnum(ch, COSTUME_RESET_VNUM);
	}

	// One roll, as char_item.cpp's USE_CHANGE_COSTUME_ATTR / USE_RESET_COSTUME_ATTR
	// does it (same checks after the roll, same item logs), without its chat
	// line. A roll that went wrong puts the old bonuses back and keeps the item.
	bool DoCostumeChange(LPCHARACTER ch, LPITEM reagent, LPITEM costume)
	{
		const bool change = reagent->GetVnum() == COSTUME_CHANGE_VNUM;
		const int countBefore = costume->GetAttributeCount();
		if (change && countBefore == 0)
			return false;
		TPlayerItemAttribute before[ITEM_ATTRIBUTE_MAX_NUM];
		memcpy(before, costume->GetAttributes(), sizeof(before));
		const char* how = change ? "CHANGE_COSTUME_ATTR" : "RESET_COSTUME_ATTR";
		char hint[64];
		snprintf(hint, sizeof(hint), "reagent %u id %u vnum %u", reagent->GetVnum(), costume->GetID(), costume->GetVnum());
		LogManager::instance().ItemLog(ch, costume, (std::string(how) + "_BEFORE").c_str(), hint, true);

		if (change)
			costume->ChangeAttribute();
		else
		{
			costume->ClearAttribute();
			costume->AlterToMagicItem();
		}

		const int countAfter = costume->GetAttributeCount();
		const bool ok = change ? countAfter == countBefore : (countAfter >= 1 && countAfter <= COSTUME_MAX_ATTR);
		if (!ok)
		{
			costume->SetAttributes(before);
			costume->UpdatePacket();
			LogManager::instance().ItemLog(ch, costume, (std::string(how) + "_FAILED").c_str(), hint, true);
			return false;
		}
		costume->UpdatePacket();
		LogManager::instance().ItemLog(ch, costume, (std::string(how) + "_AFTER").c_str(), hint, true);
		reagent->SetCount(reagent->GetCount() - 1);
		return true;
	}

	// The next change item, 76014 first; never one that is traded or locked.
	LPITEM FindSwitcher(LPCHARACTER ch)
	{
		for (int v = 0; v < SWITCH_VNUM_COUNT; ++v)
		{
			for (int cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
			{
				LPITEM item = ch->GetInventoryItem((WORD)cell);
				if (item && item->GetVnum() == SWITCH_VNUMS[v] && item->GetCount() > 0 && !item->IsExchanging() && !item->isLocked())
					return item;
			}
		}
		return NULL;
	}

	bool Matches(LPITEM item, const std::vector<Target>& targets, int need)
	{
		const int wanted = need > 0 ? std::min(need, (int)targets.size()) : (int)targets.size();
		int matched = 0;
		for (size_t t = 0; t < targets.size(); ++t)
		{
			for (int i = 0; i < ITEM_ATTRIBUTE_NORM_NUM; ++i)
			{
				if (item->GetAttributeType(i) == targets[t].apply && item->GetAttributeValue(i) >= targets[t].minValue)
				{
					++matched;
					break;
				}
			}
		}
		return matched >= wanted;
	}

	int Wanted(const std::vector<Target>& targets, int need)
	{
		return need > 0 ? std::min(need, (int)targets.size()) : (int)targets.size();
	}

	// The goal: the targets, and for a costume its number of bonuses.
	bool Done(LPITEM item, const Session& s)
	{
		if (s.costume && s.count > 0 && item->GetAttributeCount() < s.count)
			return false;
		return Matches(item, s.targets, s.need);
	}

	// One change, as using the change item on the item by hand does
	// (char_item.cpp, USE_CHANGE_ATTRIBUTE), without its chat line.
	void DoChange(LPCHARACTER ch, LPITEM switcher, LPITEM item)
	{
		if (switcher->GetVnum() == 76014)
		{
			int aiChangeProb[ITEM_ATTRIBUTE_MAX_LEVEL] = { 0, 10, 50, 39, 1 };
			item->ChangeAttribute(aiChangeProb);
		}
		else
			item->ChangeAttribute();

		char buf[21];
		snprintf(buf, sizeof(buf), "%u", item->GetID());
		LogManager::instance().ItemLog(ch, switcher, "CHANGE_ATTRIBUTE", buf);

		switcher->SetCount(switcher->GetCount() - 1);
	}

	void SendProgress(LPCHARACTER ch, const Session& s)
	{
		Cmd(ch, "progress %u %d", s.cell, s.changes);
		SendItems(ch);
	}

	void Finish(LPCHARACTER ch, const Session& s, int reason)
	{
		if (s.changes > 0)
			sys_log(0, "BONUS_SWITCH: %s item %u, %d changes (76014 %d, others %d), reason %d", ch->GetName(), s.itemId,
					s.changes, s.usedPriority, s.usedOther, reason);
		SendProgress(ch, s);
		Cmd(ch, "done %u %d %d %d %d", s.cell, reason, s.changes, s.usedPriority, s.usedOther);
		Cmd(ch, "state %u 0", s.cell);
	}

	int RunsOf(DWORD pid)
	{
		int n = 0;
		for (std::map<SessionKey, Session>::const_iterator it = s_sessions.lower_bound(KeyOf(pid, 0));
				it != s_sessions.end() && it->second.pid == pid; ++it)
			++n;
		return n;
	}

	EVENTINFO(bonus_switch_tick_info)
	{
		int dummy;
	};

	// Runs one session; false when it ended (the caller erases it).
	bool Run(LPCHARACTER ch, Session& s)
	{
		if (Busy(ch))
		{
			Finish(ch, s, END_BUSY);
			return false;
		}
		LPITEM item = ch->GetInventoryItem(s.cell);
		if (!item || item->GetID() != s.itemId || CheckItem(ch, item))
		{
			Finish(ch, s, END_ITEM_GONE);
			return false;
		}
		const DWORD now = get_dword_time();
		const DWORD step = std::max(1, 1000 / std::max(1, s.speed));
		if ((int)(now - s.nextAt) > 1000)
			s.nextAt = now;	// the core was stalled; no burst to make up for it
		for (int n = 0; n < MAX_CHANGES_PER_TICK && (int)(now - s.nextAt) >= 0; ++n)
		{
			if (Done(item, s))
				break;
			s.nextAt += step;
			if (s.costume)
			{
				LPITEM reagent = FindCostumeItem(ch, item, std::max(s.count, Wanted(s.targets, s.need)));
				if (!reagent)
				{
					Finish(ch, s, END_NO_SWITCHERS);
					return false;
				}
				const bool reset = reagent->GetVnum() == COSTUME_RESET_VNUM;
				if (!DoCostumeChange(ch, reagent, item))
					continue;	// rolled wrong and undone; nothing used
				if (reset)
					++s.usedPriority;	// 70063
				else
					++s.usedOther;		// 70064
				++s.changes;
				continue;
			}
			LPITEM switcher = FindSwitcher(ch);
			if (!switcher)
			{
				Finish(ch, s, END_NO_SWITCHERS);
				return false;
			}
			if (switcher->GetVnum() == PRIORITY_VNUM)
				++s.usedPriority;
			else
				++s.usedOther;
			DoChange(ch, switcher, item);
			++s.changes;
		}
		if (Done(item, s))
		{
			Finish(ch, s, END_FOUND);
			return false;
		}
		if (now - s.lastProgress >= PROGRESS_EVERY_MS)
		{
			s.lastProgress = now;
			SendProgress(ch, s);
		}
		return true;
	}

	EVENTFUNC(bonus_switch_tick)
	{
		for (std::map<SessionKey, Session>::iterator it = s_sessions.begin(); it != s_sessions.end(); )
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->second.pid);
			if (!Eligible(ch) || !ch->GetSectree() || !Run(ch, it->second))
				s_sessions.erase(it++);
			else
				++it;
		}
		if (s_sessions.empty())
		{
			s_pkTick = NULL;
			return 0;
		}
		return 1;	// every pass
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		bonus_switch_tick_info* info = AllocEventInfo<bonus_switch_tick_info>();
		s_pkTick = event_create(bonus_switch_tick, info, 1);
	}

	LPITEM ItemAt(LPCHARACTER ch, const char* arg, int& cell)
	{
		if (!*arg || !isdigit((unsigned char)*arg))
			return NULL;
		cell = atoi(arg);
		if (cell < 0 || cell >= INVENTORY_MAX_NUM)
			return NULL;
		return ch->GetInventoryItem((WORD)cell);
	}

	void Info(LPCHARACTER ch, const char* argument)
	{
		char arg[16];
		one_argument(argument, arg, sizeof(arg));
		int cell = -1;
		LPITEM item = ItemAt(ch, arg, cell);
		if (const int bad = CheckItem(ch, item))
		{
			Msg(ch, bad);
			return;
		}
		RefreshItemAttr();
		SendAttrs(ch, cell, item);
		SendItems(ch);
		Cmd(ch, "state %d %d", cell, s_sessions.count(KeyOf(ch->GetPlayerID(), (WORD)cell)) ? 1 : 0);
	}

	void Start(LPCHARACTER ch, const char* argument)
	{
		char aCell[16], aSpeed[16], aNeed[16], aCount[16];
		const char* rest = one_argument(argument, aCell, sizeof(aCell));
		rest = one_argument(rest, aSpeed, sizeof(aSpeed));
		rest = one_argument(rest, aNeed, sizeof(aNeed));
		rest = one_argument(rest, aCount, sizeof(aCount));

		if (IsOff())
			return Msg(ch, MSG_OFF);
		if (Busy(ch))
			return Msg(ch, MSG_BUSY);
		int cell = -1;
		LPITEM item = ItemAt(ch, aCell, cell);
		if (const int bad = CheckItem(ch, item))
			return Msg(ch, bad);
		RefreshItemAttr();

		std::vector<Target> targets;
		int addonTargets = 0;
		char arg[32];
		while (true)
		{
			rest = one_argument(rest, arg, sizeof(arg));
			if (!*arg)
				break;
			const char* colon = strchr(arg, ':');
			if (!colon)
				return Msg(ch, MSG_BAD_TARGET, 0);
			const int apply = atoi(arg);
			const long minValue = atol(colon + 1);
			if (apply <= 0 || apply > 255)
				return Msg(ch, MSG_BAD_TARGET, apply);
			for (size_t i = 0; i < targets.size(); ++i)
				if (targets[i].apply == apply)
					return Msg(ch, MSG_BAD_TARGET, apply);
			const long top = MaxValue(item, (BYTE)apply);
			if (top <= 0)
				return Msg(ch, MSG_BAD_TARGET, apply);
			if (minValue > top)
				return Msg(ch, MSG_TOO_HIGH, apply);
			if (HasDamageAddon(item) && (apply == POINT_NORMAL_HIT_DAMAGE_BONUS || apply == POINT_SKILL_DAMAGE_BONUS))
				++addonTargets;
			targets.push_back(Target{ (BYTE)apply, std::max(1L, minValue) });
			if ((int)targets.size() > ITEM_ATTRIBUTE_NORM_NUM)
				return Msg(ch, MSG_TOO_MANY, item->GetAttributeCount());
		}
		const bool costume = IsCostume(item);
		const int count = costume ? atoi(aCount) : 0;
		if (count < 0 || count > COSTUME_MAX_ATTR)
			return Msg(ch, MSG_BAD_COUNT, COSTUME_MAX_ATTR);
		if (targets.empty() && count == 0)
			return Msg(ch, MSG_NO_TARGETS);	// a costume may ask for a number of bonuses only

		const int need = atoi(aNeed);
		if (need < 0 || need > (int)targets.size())
			return Msg(ch, MSG_BAD_NEED, (long)targets.size());
		const int wanted = Wanted(targets, need);

		if (costume)
		{
			// a costume rolls 1-3 bonuses, whatever it has now
			if (wanted > COSTUME_MAX_ATTR)
				return Msg(ch, MSG_TOO_MANY, COSTUME_MAX_ATTR);
		}
		else
		{
			// A change keeps the number of bonuses: as many matches as the item
			// has bonuses at most, the addon's two slots only for its own two.
			const int attrCount = item->GetAttributeCount();
			const int addonSlots = HasDamageAddon(item) ? 2 : 0;
			const int plainTargets = (int)targets.size() - addonTargets;
			if (wanted > attrCount || std::min(wanted, plainTargets) > attrCount - addonSlots)
				return Msg(ch, MSG_TOO_MANY, attrCount);
		}

		Session probe;
		probe.costume = costume;
		probe.count = count;
		probe.need = need;
		probe.targets = targets;
		if (Done(item, probe))
			return Msg(ch, MSG_ALREADY);
		if (costume ? !FindCostumeItem(ch, item, std::max(count, wanted)) : !FindSwitcher(ch))
			return Msg(ch, MSG_NO_SWITCHERS);

		const DWORD pid = ch->GetPlayerID();
		const SessionKey key = KeyOf(pid, (WORD)cell);
		std::map<SessionKey, Session>::iterator old = s_sessions.find(key);
		if (old != s_sessions.end())
		{
			Finish(ch, old->second, END_STOPPED);	// started again with new targets
			s_sessions.erase(old);
		}
		if (RunsOf(pid) >= MAX_RUNS)
			return Msg(ch, MSG_TOO_MANY_RUNS, MAX_RUNS);

		Session& s = s_sessions[key];
		s.pid = pid;
		s.cell = (WORD)cell;
		s.itemId = item->GetID();
		s.speed = std::max(1, std::min(atoi(aSpeed), MaxSpeed()));
		s.need = need;
		s.costume = costume;
		s.count = count;
		s.targets = targets;
		s.nextAt = get_dword_time();
		s.lastProgress = 0;
		s.changes = 0;
		s.usedPriority = 0;
		s.usedOther = 0;
		Cmd(ch, "state %d 1", cell);
		EnsureTick();
	}

	// "Zmien raz": one change, after the window's own confirmation.
	void Once(LPCHARACTER ch, const char* argument)
	{
		char arg[16];
		one_argument(argument, arg, sizeof(arg));
		if (IsOff())
			return Msg(ch, MSG_OFF);
		if (Busy(ch))
			return Msg(ch, MSG_BUSY);
		int cell = -1;
		LPITEM item = ItemAt(ch, arg, cell);
		if (const int bad = CheckItem(ch, item))
			return Msg(ch, bad);
		if (s_sessions.count(KeyOf(ch->GetPlayerID(), (WORD)cell)))
			return Msg(ch, MSG_RUNNING);
		if (IsCostume(item))
		{
			// 70064 on a costume with bonuses, 70063 on a bare one (or with no 70064 left)
			LPITEM reagent = FindCostumeItem(ch, item, 0);
			if (!reagent)
				return Msg(ch, MSG_NO_SWITCHERS);
			if (!DoCostumeChange(ch, reagent, item))
				return Msg(ch, MSG_ROLL_FAILED);
			SendItems(ch);
			Cmd(ch, "changed %d", cell);
			return;
		}
		LPITEM switcher = FindSwitcher(ch);
		if (!switcher)
			return Msg(ch, MSG_NO_SWITCHERS);
		DoChange(ch, switcher, item);
		SendItems(ch);
		Cmd(ch, "changed %d", cell);
	}

	void Stop(LPCHARACTER ch, const char* argument)
	{
		char arg[16];
		one_argument(argument, arg, sizeof(arg));
		const DWORD pid = ch->GetPlayerID();
		if (*arg)
		{
			const int cell = atoi(arg);
			std::map<SessionKey, Session>::iterator it = s_sessions.find(KeyOf(pid, (WORD)cell));
			if (it == s_sessions.end())
			{
				Cmd(ch, "state %d 0", cell);
				return;
			}
			Finish(ch, it->second, END_STOPPED);
			s_sessions.erase(it);
			return;
		}
		for (std::map<SessionKey, Session>::iterator it = s_sessions.lower_bound(KeyOf(pid, 0));
				it != s_sessions.end() && it->second.pid == pid; )
		{
			Finish(ch, it->second, END_STOPPED);
			s_sessions.erase(it++);
		}
	}

	bool TooSoon(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapLastCommand[ch->GetPlayerID()];
		if (last && now - last < 150)
			return true;
		last = now;
		return false;
	}
}

void BonusSwitchCommand(LPCHARACTER ch, const char* argument)
{
	using namespace mt2009_bonus_switch;
	if (!Eligible(ch))
		return;
	char sub[32];
	const char* rest = one_argument(argument, sub, sizeof(sub));
	if (!strcmp(sub, "stop"))
		return Stop(ch, rest);	// never throttled
	if (!strcmp(sub, "info"))
		return Info(ch, rest);	// read-only; the window asks once per tab
	if (TooSoon(ch))
		return;
	if (!strcmp(sub, "items"))
		SendItems(ch);
	else if (!strcmp(sub, "start"))
		Start(ch, rest);
	else if (!strcmp(sub, "once"))
		Once(ch, rest);
	else
		ch->ChatPacket(CHAT_TYPE_INFO, "Bonus switcher: /bonus_switch info <cell> | start <cell> <speed> <need> <apply>:<min> ... | once <cell> | stop [cell]");
}
