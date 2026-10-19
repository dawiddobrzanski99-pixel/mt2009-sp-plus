#ifndef __INC_METIN2_PLAYERBOT_BELTS_H__
#define __INC_METIN2_PLAYERBOT_BELTS_H__

// MT2009_PLUS_BOT_BELTS_V1: the bots and the belt system (MT2009_PLUS_BELTS_V1, Autor: Digi
// Rasta, server-patches/pasy). "Naucz boty calego systemu pasow: zbieraja materialy, robia pasy
// u Mistrza, ulepszaja je u Kowala, zakladaja je i korzystaja z ekwipunku pasa, jesli to ma
// sens" (the owner, 7 October). Until now a bot wore a belt it happened to own and did nothing
// else with the system.
//
//   * Makers: PLAYERBOT_BELT_MAKER_PERCENT of the bots from level 50 (by player id). A maker's
//     target is the highest recipe its level can wear whose belt is better than every belt it
//     owns (the families rank by their level: Lniany 50, Skorzany 70, Przepychu 85, Madrosci 97,
//     Dusz 100, the four belts of 103 - one of them by player id). It keeps that recipe's
//     materials (two attempts' worth: the odds are 50% down to 10%), buys what it lacks off the
//     counters (playerbot_offline_market.h; the Energy Shards 51001 come there from the
//     Alchemist's scrap - another pass's work, this one only buys and keeps them) and makes the
//     belt at Mistrz (20082, beside the Blacksmith in M1) - the cube recipe of cube.pasy.txt,
//     done the way the engine's Cube_make does it: materials and yang taken, the recipe's roll,
//     the belt given (the window is a client's; a bot has no hands for it - the Alchemist's
//     pattern, playerbot_town.h).
//   * Upgrading: any bot with a belt raises the one it wears at the Blacksmith (refine_proto,
//     yang only, DoRefine - the engine's fee and roll), to its own aim of +4..+9 (by player id):
//     the steps to +4 never fail, the ones after them may burn the belt.
//   * Wearing: the equipment pass, as before. A better belt in the bag first empties the worn
//     one's pouch (a belt with something in it cannot come off).
//   * The pouch (belt inventory, 287-302): as many cells as the belt's grade opens (value0). A
//     bot moves spare stacks of its red and blue potions there - a second stack of a vnum, never
//     the last one in the bag - and drinks from it once the bag has none (UseHealthPotion,
//     UseManaPotion, playerbot_gear.h): the belt is a reserve that frees bag cells.
//   * Gifts (the owner: "mozesz dac niektorym botom przedmioty, zeby ulatwic robienie/ulepszanie
//     pasow ... zeby szybciej to uruchomic"): PLAYERBOT_BELT_SEED_PERCENT of the makers are owed
//     the materials of PLAYERBOT_BELT_SEED_ATTEMPTS attempts at their target, handed over at
//     Mistrz when the bag lacks them (a quest flag counts them). gifts only with the event flag m2_bot_craft_seed_on.

#if defined(PLAYERBOT_ENGINE_MT2009)

#include "belt_inventory_helper.h"

namespace
{
	const int PLAYERBOT_BELT_MAKER_MIN_LEVEL = 50;
	const int PLAYERBOT_BELT_MAKER_PERCENT = 50;
	const int PLAYERBOT_BELT_SEED_PERCENT = 35;
	const int PLAYERBOT_BELT_SEED_ATTEMPTS = 2;
	const char* const PLAYERBOT_BELT_SEED_FLAG = "playerbot.belt_seed";
	// What a maker keeps of each material: this many attempts' worth.
	const int PLAYERBOT_BELT_KEEP_ATTEMPTS = 2;
	const int PLAYERBOT_BELT_VISIT_ATTEMPTS = 3;
	const int PLAYERBOT_BELT_VISIT_REFINES = 5;
	// The share of the spare purse a material line may take, and its price over the market's.
	const int PLAYERBOT_BELT_BUY_PURSE_PERCENT = 40;
	const int PLAYERBOT_BELT_BUY_OVER_PERCENT = 150;
	// A belt step's fee out of this share of the spare purse.
	const int PLAYERBOT_BELT_REFINE_PURSE_PERCENT = 30;
	const DWORD PLAYERBOT_BELT_PLAN_MS = 20 * 1000;

	struct TPlayerBotBeltRecipe
	{
		DWORD reward;
		int level;
		long long gold;
		int percent;
		struct { DWORD vnum; int count; } mats[4];
	};

	// cube.pasy.txt, as the Dockerfile appends it to cube.txt (npc 20082). A change there is a
	// change here.
	const TPlayerBotBeltRecipe PLAYERBOT_BELT_RECIPES[] = {
		{ 18000, 50,  10000, 50, { { 50624, 10 }, { 27992, 2 }, { 51001, 30 },  { 0, 0 } } },	// Pas Lniany
		{ 18010, 70,  10000, 40, { { 50625, 10 }, { 27992, 2 }, { 51001, 50 },  { 0, 0 } } },	// Pas Skorzany
		{ 18020, 85,  30000, 30, { { 50626, 10 }, { 27993, 2 }, { 51001, 70 },  { 0, 0 } } },	// Pas Przepychu
		{ 18030, 97,  30000, 20, { { 50630, 10 }, { 27993, 2 }, { 51001, 100 }, { 0, 0 } } },	// Pas Madrosci
		{ 18040, 103, 50000, 10, { { 50636, 10 }, { 27994, 2 }, { 30518, 5 },   { 30524, 10 } } },	// Pas Krola
		{ 18050, 103, 50000, 10, { { 50635, 10 }, { 27994, 2 }, { 30519, 5 },   { 30525, 10 } } },	// Pas Mroku
		{ 18060, 103, 50000, 10, { { 50637, 10 }, { 27994, 2 }, { 30522, 5 },   { 30524, 10 } } },	// Pas Runiczny
		{ 18070, 103, 50000, 10, { { 50638, 10 }, { 27994, 2 }, { 30523, 5 },   { 30525, 10 } } },	// Pas Niedzwiedzi
		{ 18080, 100, 50000, 10, { { 50634, 10 }, { 27994, 2 }, { 30550, 20 },  { 51001, 100 } } },	// Pas Dusz
	};
	const int PLAYERBOT_BELT_RECIPE_COUNT = sizeof(PLAYERBOT_BELT_RECIPES) / sizeof(PLAYERBOT_BELT_RECIPES[0]);

	struct TPlayerBotBeltStats
	{
		unsigned crafts;
		unsigned craftFails;
		unsigned refines;
		unsigned burns;
		unsigned pouchMoves;
		unsigned pouchDrinks;
		unsigned seeded;
		unsigned seedGifts;
		unsigned bought;
		unsigned long long boughtYang;
	};
	TPlayerBotBeltStats s_kPlayerBotBeltStats = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };

	// The owner's switch for the gifts of both crafts (this one and playerbot_talismans.h). Off unless
	// the event flag m2_bot_craft_seed_on is set: the gifts were for teaching the bots on the test
	// server, the players' servers do not hand them out (the owner, 8 October).
	bool ArePlayerBotCraftSeedsOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_craft_seed_on") == 0 ||
				quest::CQuestManager::instance().GetEventFlag("m2_bot_craft_seed_off") != 0;
	}

	bool IsPlayerBotBeltItem(LPITEM item)
	{
		return item && item->GetType() == ITEM_BELT && IsPlayerBotBeltVnum(item->GetVnum());
	}

	bool IsPlayerBotBeltMaker(LPCHARACTER ch)
	{
		return ch && (int)ch->GetLevel() >= PLAYERBOT_BELT_MAKER_MIN_LEVEL &&
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x42454c54U) % 100U < (DWORD)PLAYERBOT_BELT_MAKER_PERCENT;
	}

	// A belt family's rank is the level its recipe asks.
	int GetPlayerBotBeltRank(DWORD vnum)
	{
		if (!IsPlayerBotBeltVnum(vnum))
			return 0;
		const DWORD family = vnum - (vnum - PLAYERBOT_BELT_FIRST_VNUM) % 10;
		for (int i = 0; i < PLAYERBOT_BELT_RECIPE_COUNT; ++i)
			if (PLAYERBOT_BELT_RECIPES[i].reward == family)
				return PLAYERBOT_BELT_RECIPES[i].level;
		return 0;
	}

	// The best belt rank the bot owns, worn or in the bag.
	int GetPlayerBotOwnedBeltRank(LPCHARACTER ch)
	{
		int rank = 0;
		if (LPITEM worn = ch->GetWear(WEAR_BELT))
			rank = GetPlayerBotBeltRank(worn->GetVnum());
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotBeltItem(item))
				rank = std::max(rank, GetPlayerBotBeltRank(item->GetVnum()));
		}
		return rank;
	}

	int GetPlayerBotBeltSeedLeft(LPCHARACTER ch)
	{
		if (!ch || ArePlayerBotCraftSeedsOff())
			return 0;
		return std::max(0, ch->GetQuestFlag(PLAYERBOT_BELT_SEED_FLAG) - 1);
	}

	struct TPlayerBotBeltPlan
	{
		DWORD at;
		int recipe;	// -1 for none
	};
	std::map<DWORD, TPlayerBotBeltPlan> s_mapPlayerBotBeltPlan;

	// The maker's target recipe, or -1.
	int GetPlayerBotBeltTarget(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotBeltMaker(ch) || !ch->IsItemLoaded())
			return -1;
		TPlayerBotBeltPlan& p = s_mapPlayerBotBeltPlan[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (p.at != 0 && now - p.at < PLAYERBOT_BELT_PLAN_MS)
			return p.recipe;
		p.at = now;
		p.recipe = -1;
		const int level = (int)ch->GetLevel();
		const int owned = GetPlayerBotOwnedBeltRank(ch);
		// The four belts of 103 by player id; the others by level.
		const int topVariant = 4 + (int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x50415346U) % 4U);
		int bestLevel = 0;
		for (int i = 0; i < PLAYERBOT_BELT_RECIPE_COUNT; ++i)
		{
			const TPlayerBotBeltRecipe& r = PLAYERBOT_BELT_RECIPES[i];
			if (r.level > level || r.level <= owned || r.level < bestLevel)
				continue;
			if (r.level == 103 && i != topVariant)
				continue;
			if (!ITEM_MANAGER::instance().GetTable(r.reward))
				continue;
			bestLevel = r.level;
			p.recipe = i;
		}
		return p.recipe;
	}

	void ForgetPlayerBotBeltPlan(LPCHARACTER ch)
	{
		if (ch)
			s_mapPlayerBotBeltPlan.erase(ch->GetPlayerID());
	}

	bool HasPlayerBotBeltMaterials(LPCHARACTER ch, const TPlayerBotBeltRecipe& r)
	{
		for (int m = 0; m < 4; ++m)
			if (r.mats[m].vnum != 0 && (int)ch->CountSpecifyItem(r.mats[m].vnum) < r.mats[m].count)
				return false;
		return true;
	}

	// What the maker keeps of a vnum for its target.
	int GetPlayerBotBeltMaterialKeep(LPCHARACTER ch, DWORD vnum)
	{
		const int target = GetPlayerBotBeltTarget(ch);
		if (target < 0)
			return 0;
		const TPlayerBotBeltRecipe& r = PLAYERBOT_BELT_RECIPES[target];
		for (int m = 0; m < 4; ++m)
			if (r.mats[m].vnum == vnum)
				return r.mats[m].count * PLAYERBOT_BELT_KEEP_ATTEMPTS;
		return 0;
	}

	// What it lacks for one attempt (not while a seed still owes it one).
	void CollectPlayerBotBeltMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		const int target = GetPlayerBotBeltTarget(ch);
		if (target < 0 || GetPlayerBotBeltSeedLeft(ch) > 0)
			return;
		const TPlayerBotBeltRecipe& r = PLAYERBOT_BELT_RECIPES[target];
		for (int m = 0; m < 4; ++m)
		{
			if (r.mats[m].vnum == 0)
				continue;
			const int lack = r.mats[m].count - (int)ch->CountSpecifyItem(r.mats[m].vnum);
			if (lack > 0)
				missing[r.mats[m].vnum] += lack;
		}
	}

	bool WantsPlayerBotBeltOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer)
			return false;
		std::map<DWORD, int> missing;
		CollectPlayerBotBeltMissing(ch, missing);
		std::map<DWORD, int>::const_iterator it = missing.find(offer->GetVnum());
		// A line of up to twice the lack: a stack of two hundred shards is not one attempt.
		return it != missing.end() && (int)offer->GetCount() <= std::max(it->second * 2, 1);
	}

	long long GetPlayerBotBeltSpare(LPCHARACTER ch)
	{
		return ch ? (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR : 0;
	}

	bool CanPlayerBotPayForBeltOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (!ch || !offer || price <= 0)
			return false;
		const long long fair = (long long)GetPlayerBotShopAskingPrice(offer);
		return (fair <= 0 || price * 100 <= fair * PLAYERBOT_BELT_BUY_OVER_PERCENT) &&
				price <= GetPlayerBotBeltSpare(ch) * PLAYERBOT_BELT_BUY_PURSE_PERCENT / 100;
	}

	void NotePlayerBotBeltBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		if (!ch || GetPlayerBotBeltMaterialKeep(ch, vnum) <= 0)
			return;
		++s_kPlayerBotBeltStats.bought;
		s_kPlayerBotBeltStats.boughtYang += (unsigned long long)std::max<long long>(0, price);
	}

	void DecidePlayerBotBeltSeed(LPCHARACTER ch)
	{
		if (!ch || (int)ch->GetLevel() < PLAYERBOT_BELT_MAKER_MIN_LEVEL || ArePlayerBotCraftSeedsOff() ||
				ch->GetQuestFlag(PLAYERBOT_BELT_SEED_FLAG) != 0)
			return;
		const bool seeded = IsPlayerBotBeltMaker(ch) &&
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x53504153U) % 100U < (DWORD)PLAYERBOT_BELT_SEED_PERCENT;
		ch->SetQuestFlag(PLAYERBOT_BELT_SEED_FLAG, (seeded ? PLAYERBOT_BELT_SEED_ATTEMPTS : 0) + 1);
		if (seeded)
		{
			++s_kPlayerBotBeltStats.seeded;
			sys_log(0, "PLAYERBOT_BELT: seeded pid=%u name=%s lv=%d attempts=%d target=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_BELT_SEED_ATTEMPTS,
					GetPlayerBotBeltTarget(ch));
		}
	}

	// A craft to go to Mistrz for: the target's materials in the bag (or owed by the seed) and
	// its yang.
	bool HasPlayerBotBeltCraftWork(LPCHARACTER ch)
	{
		const int target = GetPlayerBotBeltTarget(ch);
		if (target < 0)
			return false;
		const TPlayerBotBeltRecipe& r = PLAYERBOT_BELT_RECIPES[target];
		if ((long long)ch->GetGold() < r.gold + PLAYERBOT_SHOPPING_GOLD_FLOOR)
			return false;
		return GetPlayerBotBeltSeedLeft(ch) > 0 || HasPlayerBotBeltMaterials(ch, r);
	}

	// One attempt at Mistrz: the gifts the seed owes first, then Cube_make's steps - the
	// materials and the yang go whatever the roll says, the belt comes on success.
	bool CraftPlayerBotBelt(LPCHARACTER ch)
	{
		const int target = GetPlayerBotBeltTarget(ch);
		if (target < 0)
			return false;
		const TPlayerBotBeltRecipe& r = PLAYERBOT_BELT_RECIPES[target];
		if ((long long)ch->GetGold() < r.gold || CountPlayerBotFreeInventoryCells(ch) < 5)
			return false;
		if (!HasPlayerBotBeltMaterials(ch, r))
		{
			const int seedLeft = GetPlayerBotBeltSeedLeft(ch);
			if (seedLeft <= 0)
				return false;
			for (int m = 0; m < 4; ++m)
			{
				if (r.mats[m].vnum == 0)
					continue;
				const int lack = r.mats[m].count - (int)ch->CountSpecifyItem(r.mats[m].vnum);
				if (lack > 0)
					ch->AutoGiveItem(r.mats[m].vnum, (ITEM_COUNT)lack, -1, false);
			}
			ch->SetQuestFlag(PLAYERBOT_BELT_SEED_FLAG, seedLeft);	// left - 1, plus one
			++s_kPlayerBotBeltStats.seedGifts;
			sys_log(0, "PLAYERBOT_BELT: seed attempt given pid=%u name=%s reward=%u left=%d",
					ch->GetPlayerID(), ch->GetName(), r.reward, seedLeft - 1);
			if (!HasPlayerBotBeltMaterials(ch, r))
				return false;
		}
		for (int m = 0; m < 4; ++m)
			if (r.mats[m].vnum != 0)
				ch->RemoveSpecifyItem(r.mats[m].vnum, (ITEM_COUNT)r.mats[m].count);
		if (r.gold > 0)
			PlayerBotChangeGold(ch, -r.gold);
		const bool success = number(1, 100) <= r.percent;
		LPITEM made = success ? ch->AutoGiveItem(r.reward, 1, -1, false) : NULL;
		LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), r.reward,
				made ? made->GetID() : 0, made ? 1 : 0, made ? 1 : 0);
		if (made)
			++s_kPlayerBotBeltStats.crafts;
		else
			++s_kPlayerBotBeltStats.craftFails;
		sys_log(0, "PLAYERBOT_BELT: craft %s pid=%u name=%s lv=%d reward=%u chance=%d gold=%lld",
				made ? "SUCCESS" : "FAILED", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), r.reward, r.percent,
				(long long)ch->GetGold());
		ForgetPlayerBotBeltPlan(ch);
		return true;
	}

	// ---- the pouch ------------------------------------------------------------------------

	int GetPlayerBotBeltGrade(LPCHARACTER ch)
	{
		LPITEM belt = ch ? ch->GetWear(WEAR_BELT) : NULL;
		return belt ? (int)belt->GetValue(0) : 0;
	}

	// Everything out of the pouch into the bag; false when something could not come out.
	bool EmptyPlayerBotBeltPouch(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		bool clear = true;
		for (WORD cell = BELT_INVENTORY_SLOT_START; cell < BELT_INVENTORY_SLOT_END; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item)
				continue;
			const int dest = ch->GetEmptyInventory(item->GetSize());
			if (dest < 0 || !ch->MoveItem(TItemPos(INVENTORY, cell), TItemPos(INVENTORY, (WORD)dest), item->GetCount()))
				clear = false;
		}
		return clear && !CBeltInventoryHelper::IsExistItemInBeltInventory(ch);
	}

	// The belt in the bag the equipment pass would put on over the worn one, or NULL.
	LPITEM FindPlayerBotBetterBagBelt(LPCHARACTER ch)
	{
		LPITEM worn = ch->GetWear(WEAR_BELT);
		if (!worn)
			return NULL;
		LPITEM best = NULL;
		long long bestScore = GetPlayerBotEquipmentScore(worn, ch);
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotBeltItem(item) ||
					item->GetLevelLimit() > (int)ch->GetLevel() || !IsPlayerBotEquipmentCandidate(ch, item))
				continue;
			const long long score = GetPlayerBotEquipmentScore(item, ch);
			if (score > bestScore)
			{
				best = item;
				bestScore = score;
			}
		}
		return best;
	}

	bool PlayerBotHasBetterBagBelt(LPCHARACTER ch)
	{
		return FindPlayerBotBetterBagBelt(ch) != NULL;
	}

	// The better belt on, its predecessor's pouch emptied first (a belt with something in it
	// cannot come off) - the equipment pass's swap, which that pouch refused.
	bool PutOnPlayerBotBetterBelt(LPCHARACTER ch)
	{
		LPITEM better = FindPlayerBotBetterBagBelt(ch);
		LPITEM worn = ch->GetWear(WEAR_BELT);
		if (!better || !worn || IsPlayerBotGearFrozen(ch) || IsPlayerBotSidekickLockedItem(ch, worn) ||
				!EmptyPlayerBotBeltPouch(ch))
			return false;
		const DWORD oldVnum = worn->GetVnum();
		if (ch->GetEmptyInventory(worn->GetSize()) < 0 || !ch->UnequipItem(worn) || worn->IsEquipped())
			return false;
		if (!ch->EquipItem(better))
		{
			if (!worn->IsEquipped())
				ch->EquipItem(worn);
			return false;
		}
		sys_log(0, "PLAYERBOT_BELT: wear pid=%u name=%s lv=%d vnum=%u old=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), better->GetVnum(), oldVnum);
		return true;
	}

	bool IsPlayerBotPouchPotionVnum(DWORD vnum)
	{
		switch (vnum)
		{
			case 27001: case 27002: case 27003: case 27051:	// red
			case 27004: case 27005: case 27006: case 27052:	// blue
				return true;
			default:
				return false;
		}
	}

	// Fills the open, empty cells of the pouch with spare potion stacks, a couple a pass.
	int FillPlayerBotBeltPouch(LPCHARACTER ch)
	{
		const int grade = GetPlayerBotBeltGrade(ch);
		if (grade <= 0 || PlayerBotHasBetterBagBelt(ch))
			return 0;
		int moved = 0;
		for (WORD i = 0; i < BELT_INVENTORY_SLOT_COUNT && moved < 2; ++i)
		{
			const WORD beltCell = BELT_INVENTORY_SLOT_START + i;
			if (!CBeltInventoryHelper::IsAvailableCell(i, grade) || ch->GetInventoryItem(beltCell))
				continue;
			// The potion the pouch holds least of, from a vnum the bag has two stacks of.
			std::map<DWORD, int> stacks, inPouch;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (item && item->GetCell() == cell && IsPlayerBotPouchPotionVnum(item->GetVnum()) &&
						!IsPlayerBotSidekickHeld(ch, item))
					++stacks[item->GetVnum()];
			}
			for (WORD c = BELT_INVENTORY_SLOT_START; c < BELT_INVENTORY_SLOT_END; ++c)
				if (LPITEM item = ch->GetInventoryItem(c))
					inPouch[item->GetVnum()] += item->GetCount();
			DWORD pick = 0;
			for (std::map<DWORD, int>::const_iterator it = stacks.begin(); it != stacks.end(); ++it)
				if (it->second >= 2 && (pick == 0 || inPouch[it->first] < inPouch[pick]))
					pick = it->first;
			if (pick == 0)
				break;
			// The last stack of that vnum in the bag stays; the first one goes.
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetCell() != cell || item->GetVnum() != pick ||
						!CBeltInventoryHelper::CanMoveIntoBeltInventory(item))
					continue;
				if (ch->MoveItem(TItemPos(INVENTORY, cell), TItemPos(INVENTORY, beltCell), item->GetCount()))
				{
					++moved;
					++s_kPlayerBotBeltStats.pouchMoves;
				}
				break;
			}
			if (!ch->GetInventoryItem(beltCell))
				break;	// refused: not again this pass
		}
		if (moved)
			PlayerBotLogThrottled("belt_pouch_fill", get_dword_time(),
					"PLAYERBOT_BELT: pouch filled pid=%u name=%s grade=%d moved=%d",
					ch->GetPlayerID(), ch->GetName(), grade, moved);
		return moved;
	}

	// The drink from the pouch, once the bag has none of these (UseHealthPotion / UseManaPotion).
	bool UsePlayerBotBeltPotion(LPCHARACTER ch, const DWORD* vnums, size_t count, const char* what)
	{
		if (!ch || !ch->GetWear(WEAR_BELT))
			return false;
		for (size_t v = 0; v < count; ++v)
			for (WORD cell = BELT_INVENTORY_SLOT_START; cell < BELT_INVENTORY_SLOT_END; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetVnum() != vnums[v])
					continue;
				if (ch->UseItem(TItemPos(INVENTORY, cell)))
				{
					++s_kPlayerBotBeltStats.pouchDrinks;
					sys_log(0, "PLAYERBOT_BELT: %s potion from the pouch pid=%u name=%s vnum=%u hp=%d/%d sp=%d/%d",
							what, ch->GetPlayerID(), ch->GetName(), vnums[v], ch->GetHP(), ch->GetMaxHP(),
							ch->GetSP(), ch->GetMaxSP());
					return true;
				}
			}
		return false;
	}

	// ---- the anvil ------------------------------------------------------------------------

	// How far a bot takes its belt: +4 (no step to it fails) up to +9, by player id.
	int GetPlayerBotBeltAim(LPCHARACTER ch)
	{
		return 4 + (int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x41494d42U) % 6U);
	}

	LPITEM GetPlayerBotBeltToRefine(LPCHARACTER ch)
	{
		LPITEM belt = ch ? ch->GetWear(WEAR_BELT) : NULL;
		if (!IsPlayerBotBeltItem(belt) || belt->GetRefinedVnum() == 0 ||
				(int)(belt->GetVnum() - PLAYERBOT_BELT_FIRST_VNUM) % 10 >= GetPlayerBotBeltAim(ch) ||
				PlayerBotHasBetterBagBelt(ch) || IsPlayerBotSidekickLockedItem(ch, belt))
			return NULL;
		const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(belt->GetRefineSet());
		if (!recipe || recipe->material_count > 0)
			return NULL;	// the official belt steps are yang only
		const long long fee = (long long)ch->ComputeRefineFee(recipe->cost);
		return fee <= GetPlayerBotBeltSpare(ch) * PLAYERBOT_BELT_REFINE_PURSE_PERCENT / 100 ? belt : NULL;
	}

	bool HasPlayerBotBeltRefineWork(LPCHARACTER ch)
	{
		return GetPlayerBotBeltToRefine(ch) != NULL;
	}

	// One step: the pouch emptied, the belt off, DoRefine, back on.
	bool RefinePlayerBotBeltStep(LPCHARACTER ch)
	{
		LPITEM belt = GetPlayerBotBeltToRefine(ch);
		if (!belt || IsPlayerBotGearFrozen(ch) || !EmptyPlayerBotBeltPouch(ch))
			return false;
		if (ch->GetEmptyInventory(belt->GetSize()) < 0 || !ch->UnequipItem(belt) || belt->IsEquipped())
			return false;
		const DWORD oldVnum = belt->GetVnum();
		const DWORD nextVnum = belt->GetRefinedVnum();
		const WORD cell = belt->GetCell();
		const int before = (int)ch->CountSpecifyItem(nextVnum);
		const long long goldBefore = (long long)ch->GetGold();
		const bool attempted = ch->DoRefine(belt, false);
		LPITEM after = ch->GetInventoryItem(cell);
		if (after && IsPlayerBotBeltItem(after) && !after->IsEquipped())
			ch->EquipItem(after);
		if (!attempted)
			return false;
		const bool success = (int)ch->CountSpecifyItem(nextVnum) > before ||
				(ch->GetWear(WEAR_BELT) && ch->GetWear(WEAR_BELT)->GetVnum() == nextVnum);
		++s_kPlayerBotBeltStats.refines;
		if (!success)
			++s_kPlayerBotBeltStats.burns;
		sys_log(0, "PLAYERBOT_BELT: refine %s pid=%u name=%s lv=%d vnum=%u->%u aim=+%d fee=%lld gold=%lld",
				success ? "SUCCESS" : "FAILED_BURNED", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), oldVnum,
				nextVnum, GetPlayerBotBeltAim(ch), goldBefore - (long long)ch->GetGold(), (long long)ch->GetGold());
		ForgetPlayerBotBeltPlan(ch);
		return true;
	}

	// The light pass: the pouch emptied for a better belt (so the equipment pass can swap) or
	// filled.
	void ManagePlayerBotBeltPouch(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || ch->GetExchange() || ch->GetMyShop() ||
				!ch->GetWear(WEAR_BELT))
			return;
		if (PlayerBotHasBetterBagBelt(ch))
		{
			PutOnPlayerBotBetterBelt(ch);
			return;
		}
		FillPlayerBotBeltPouch(ch);
	}

	void LogPlayerBotBeltCensus()
	{
		const TPlayerBotBeltStats& s = s_kPlayerBotBeltStats;
		sys_log(0, "PLAYERBOT_BELT: census crafts=%u craft_fails=%u refines=%u burns=%u pouch_moves=%u pouch_drinks=%u seeded=%u seed_attempts=%u bought=%u bought_yang=%llu",
				s.crafts, s.craftFails, s.refines, s.burns, s.pouchMoves, s.pouchDrinks, s.seeded, s.seedGifts,
				s.bought, s.boughtYang);
	}
}

#else

namespace
{
	int GetPlayerBotBeltMaterialKeep(LPCHARACTER, DWORD) { return 0; }
	void CollectPlayerBotBeltMissing(LPCHARACTER, std::map<DWORD, int>&) {}
	bool WantsPlayerBotBeltOffer(LPCHARACTER, LPITEM) { return false; }
	bool CanPlayerBotPayForBeltOffer(LPCHARACTER, LPITEM, long long) { return false; }
	void NotePlayerBotBeltBought(LPCHARACTER, DWORD, long long) {}
	void DecidePlayerBotBeltSeed(LPCHARACTER) {}
	bool HasPlayerBotBeltCraftWork(LPCHARACTER) { return false; }
	bool CraftPlayerBotBelt(LPCHARACTER) { return false; }
	bool UsePlayerBotBeltPotion(LPCHARACTER, const DWORD*, size_t, const char*) { return false; }
	bool HasPlayerBotBeltRefineWork(LPCHARACTER) { return false; }
	bool RefinePlayerBotBeltStep(LPCHARACTER) { return false; }
	void ManagePlayerBotBeltPouch(LPCHARACTER) {}
	void LogPlayerBotBeltCensus() {}
}

#endif

#endif
