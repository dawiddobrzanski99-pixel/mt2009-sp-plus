#ifndef __INC_METIN2_PLAYERBOT_ENERGY_SHARDS_H__
#define __INC_METIN2_PLAYERBOT_ENERGY_SHARDS_H__

// MT2009_PLUS_BOT_ENERGY_SHARDS_V1 - the bots' Odlamki Energii (51001), and the
// owner's two fixed prices of 7 October 2026 (a shard, a talisman).
//
// The shards ("Odlamki Energii ze zlomu", the owner, 7 October): the players'
// Alchemist (20001) dismantles an item of level 35 or more - a weapon but an
// arrow, an armour or a jewel - dragged onto him by a player of 35 or more into
// 0-15 shards by the item's level (quest/energia_alchemik.quest, the official
// energy_system tables; server-patches/pasy/README.md). A bot has no hands for
// the drag and the select, so the quest's own steps are done here: the item
// removed, number(1, 100) drawn against the quest's cumulative table of its
// level band, the shards given. Same odds, same table, no fee - the quest
// takes none.
//
//   * what goes: ONLY what the bot would otherwise sell to the merchant ("tylko
//     zlom, ktory i tak sprzedalby u handlarza"). The merchant's sale
//     (SellPlayerBotJunkAtMerchant, playerbot_economy.h) asks
//     ShouldPlayerBotKeepScrapForAlchemist of every piece IsPlayerBotJunkItem
//     already sent to it, and a piece the Alchemist takes stays in the bag
//     instead of being sold. Nothing the bot wears, lists, keeps for a counter,
//     refines or holds for any other rule ever reaches that question - those
//     are not junk. The operator's "merchant" policy is the merchant's: such a
//     piece is sold, not dismantled. A talisman is never dismantled (700 000
//     yang below), nor anything of a player's companion (its bag is its
//     owner's);
//   * where: only in a village where the Alchemist stands (the three first
//     villages, playerbot_empire_rules::GetAlchemist), since the walk to him is
//     part of the same visit. Anywhere else the merchant buys it as before;
//   * the walk: the Alchemist's errand of the soul stones (ManagePlayerBotAlchemist,
//     playerbot_town.h) goes for the held scrap as well, right after the
//     merchant's round (the hold marks the bot due), and dismantles every held
//     piece at his counter (DismantlePlayerBotEnergyScrap);
//   * never stuck: a bag under pressure sells as before, and a piece held for
//     PLAYERBOT_ENERGY_SCRAP_HOLD_MS without the walk (a route that failed, the
//     bot called away) goes to the merchant on the next visit.
//
// The counters: "paczki po 10 odlamkow, 30 000 yang za sztuke" - a line is ten
// shards at 300 000, never another size, at the owner's price with no markdown
// and no markup. Against spam the bots' counters of the whole world carry at
// most PLAYERBOT_ENERGY_SHARD_MARKET_UNITS shards between them, on any number of
// counters (the owner, 8 October: "3 rynki = rynki trzech krolestw. Odlamki moga
// stac w dowolnej liczbie sklepow, a limit dotyczy tylko sztuk na caly serwer").
// What does not fit waits in the bag. Lines go up through the offline stand's own add, one a service visit
// (BotOfflinePrepareLine / BotOfflineCounterRefuses, playerbot_offline_shop.h);
// the classic stall that opens a stand takes none, so every line is counted at
// the one place that knows the counters. A line of any other size - the whole
// stacks of before - and the lines over the caps come home a line a visit
// (BotOfflineUnwantedLine).
//
// The belts (another agent teaches the bots the belt recipes): a bot that wants
// its shards for a belt says how many it keeps with SetPlayerBotEnergyShardKeep
// (by pid; 0 lets all go); GetPlayerBotEnergyShardsForSale is what is over that,
// and only whole packs of it are listed.
//
// The talismans (94000-95450, six elements x +0..+200, tools/zywioly): 700 000
// yang a talisman whatever its element and grade ("700 000 yang, obojetnie jaki
// talizman") - the bots' asking price, their listing price and so every
// buyer's idea of a fair price (GetPlayerBotShopAskingPrice is all three).
//
// Both prices are the owner's numbers as written, not through the sheet's
// yang-rate curve and inflation (ScalePlayerBotIwakuraPrice): he named the
// yang a shard and a talisman cost.
//
// An implementation fragment in the sense playerbot_types.h describes: included
// once, from playerbot_manager.cpp, before playerbot_economy.h.

namespace
{
	// Defined further down the unit (playerbot_economy.h).
	bool IsPlayerBotJunkItem(LPCHARACTER ch, LPITEM item);
	bool IsPlayerBotBagUnderPressure(LPCHARACTER ch);
	bool IsPlayerBotSidekickPID(DWORD pid);

	const DWORD PLAYERBOT_ENERGY_SHARD_VNUM = 51001;
	// The quest's two levels: the player's and the item's.
	const int PLAYERBOT_ENERGY_MIN_LEVEL = 35;
	// The owner's price of a shard, and the one size of a line.
	const DWORD PLAYERBOT_ENERGY_SHARD_UNIT_PRICE = 30000;
	const int PLAYERBOT_ENERGY_SHARD_LINE_UNITS = 10;
	// The whole world's bot counters: at most this many shards, on at most this
	// many counters at once.
	// 1000 since 8 October (the owner: "Odblokuj również limit odłamków energii do 1000 na sklepach").
	const int PLAYERBOT_ENERGY_SHARD_MARKET_UNITS = 1000;
	// How long a piece held for the Alchemist may wait for the walk.
	const DWORD PLAYERBOT_ENERGY_SCRAP_HOLD_MS = 45 * 60 * 1000;
	// The counters are counted afresh at most this often; a line added in
	// between is on the count at once and for PLAYERBOT_ENERGY_SHARD_PENDING_MS
	// (the add is the db core's, a moment later).
	const DWORD PLAYERBOT_ENERGY_SHARD_CENSUS_MS = 5000;
	const DWORD PLAYERBOT_ENERGY_SHARD_PENDING_MS = 90000;
	// The talismans of MT2009_PLUS_ELEMENTS_V1: six elements 250 vnums apart,
	// +0..+200 each; Kwiat Zywiolu (95500) is not one.
	const DWORD PLAYERBOT_TALISMAN_FIRST_VNUM = 94000;
	const DWORD PLAYERBOT_TALISMAN_LAST_VNUM = 95450;
	// A Talisman +0 is 700 000 and every next grade 650 000 more (the owner, 8 October: "Talizman
	// +0 kosztuje 700k, kazdy kolejny kosztuje 650k wiecej"): +1 1 350 000, +200 130 700 000.
	const DWORD PLAYERBOT_TALISMAN_PRICE = 700000;
	const DWORD PLAYERBOT_TALISMAN_PRICE_PER_GRADE = 650000;

	bool IsPlayerBotEnergyShardVnum(DWORD vnum)
	{
		return vnum == PLAYERBOT_ENERGY_SHARD_VNUM;
	}

	bool IsPlayerBotFixedPriceTalismanVnum(DWORD vnum)
	{
		return vnum >= PLAYERBOT_TALISMAN_FIRST_VNUM && vnum <= PLAYERBOT_TALISMAN_LAST_VNUM &&
				(vnum - PLAYERBOT_TALISMAN_FIRST_VNUM) % 250 <= 200;
	}

	DWORD GetPlayerBotTalismanPrice(DWORD vnum)
	{
		if (!IsPlayerBotFixedPriceTalismanVnum(vnum))
			return 0;
		return PLAYERBOT_TALISMAN_PRICE + PLAYERBOT_TALISMAN_PRICE_PER_GRADE * ((vnum - PLAYERBOT_TALISMAN_FIRST_VNUM) % 250);
	}

	// MT2009_PLUS_TRADEABLE_BONUS_V1 (the owner, 8 October: "71284 i 71285 to
	// bardzo wartosciowe przedmioty ... zaczarowanie i wzmocnienie, ale
	// handlowalne"): the tradeable change (Zaczarowanie Przedmiotu, 71284) and
	// add (Wzmocnienie Przedmiotu, 71285) - unlike 71084/71085 they carry no
	// ANTI_MYSHOP. The add at his 5 000 000; the change at what 69 SM (its
	// price in the ItemShop) is worth by the Kupon SM (50) (80017) the bots'
	// price sheet puts at 1 000 000: 69 / 50 x 1 000 000 = 1 380 000. V3 (the
	// owner, 8 October: "ceny maja podlegac inflacji i wszystkim zaleznosciom
	// jak kazda cena w grze"): both are the price sheet's bases now
	// (playerbot_price_tables.h), through the yang-rate curve, the inflation,
	// the markdown and the sale memory like any sheet price - no longer the
	// owner's fixed prices below. V2 (the owner, 8 October:
	// "niech boty tez ich uzywaja, kiedy potrzebuja"): a bot of
	// PLAYERBOT_TRADEABLE_BONUS_MIN_LEVEL and up spends them on its own gear
	// like 71084/71085 - those first (ReadPlayerBotBonusBag) - keeps
	// PLAYERBOT_TRADEABLE_BONUS_KEEP of a kind for that and lists the rest, and
	// buys one off a counter at the fixed price at most when it holds none of
	// the kind (playerbot_market.h). Under that level every one is goods.
	const DWORD PLAYERBOT_TRADEABLE_CHANGE_VNUM = 71284;
	const DWORD PLAYERBOT_TRADEABLE_ADD_VNUM = 71285;
	const DWORD PLAYERBOT_TRADEABLE_ADD_PRICE = 5000000;
	const DWORD PLAYERBOT_SM_COUPON_50_PRICE = 1000000;	// playerbot_price_tables.h, 80017
	const DWORD PLAYERBOT_TRADEABLE_CHANGE_SM = 69;
	const DWORD PLAYERBOT_TRADEABLE_CHANGE_PRICE = PLAYERBOT_SM_COUPON_50_PRICE / 50 * PLAYERBOT_TRADEABLE_CHANGE_SM;
	const int PLAYERBOT_TRADEABLE_BONUS_MIN_LEVEL = 40;
	const int PLAYERBOT_TRADEABLE_BONUS_KEEP = 3;
	const int PLAYERBOT_TRADEABLE_BONUS_BUY_PURSE_PERCENT = 20;

	bool IsPlayerBotTradeableBonusVnum(DWORD vnum)
	{
		return vnum == PLAYERBOT_TRADEABLE_CHANGE_VNUM || vnum == PLAYERBOT_TRADEABLE_ADD_VNUM;
	}

	// MT2009_PLUS_SHEET_PRICES_ONLY_V1 (the owner, 8 October: "na rynku nie ma
	// stalych cen"): the owner's fixed prices are gone. The shard (30 000), the
	// eggs (2 000 000), the tradeable change and add (1 380 000 / 5 000 000)
	// are the price sheet's bases (playerbot_price_tables.h) and the talisman's
	// grade price above is the base of its asking price
	// (GetPlayerBotShopAskingPriceRaw) - all through the yang-rate curve, the
	// inflation, the markdown, the markup and the sale memory.

	// ------------------------------------------------------------ the belts' keep

	std::map<DWORD, int> s_mapPlayerBotEnergyShardKeep;

	// How many shards this bot holds back from its counter (a belt recipe of
	// its own). 0 or less forgets the keep.
	void SetPlayerBotEnergyShardKeep(DWORD pid, int keep)
	{
		if (keep <= 0)
			s_mapPlayerBotEnergyShardKeep.erase(pid);
		else
			s_mapPlayerBotEnergyShardKeep[pid] = keep;
	}

	int GetPlayerBotEnergyShardKeep(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		std::map<DWORD, int>::const_iterator it = s_mapPlayerBotEnergyShardKeep.find(ch->GetPlayerID());
		return it == s_mapPlayerBotEnergyShardKeep.end() ? 0 : it->second;
	}

	int CountPlayerBotEnergyShards(LPCHARACTER ch)
	{
		return ch && ch->IsItemLoaded() ? (int)ch->CountSpecifyItem(PLAYERBOT_ENERGY_SHARD_VNUM) : 0;
	}

	// The shards over the keep: what the counter may have, in whole packs.
	int GetPlayerBotEnergyShardsForSale(LPCHARACTER ch)
	{
		return std::max(0, CountPlayerBotEnergyShards(ch) - GetPlayerBotEnergyShardKeep(ch));
	}

	// ------------------------------------------------------------ the counters

	struct TPlayerBotEnergyShardCensus
	{
		DWORD at;
		int units;
		std::set<DWORD> shops;	// owner pids of the bot counters showing shards
		TPlayerBotEnergyShardCensus() : at(0), units(0) {}
	};
	TPlayerBotEnergyShardCensus s_kPlayerBotEnergyShardCensus;
	// A line put up (or taken home) since the census, by owner: units and when.
	std::map<DWORD, std::pair<int, DWORD> > s_mapPlayerBotEnergyShardPending;

	void RefreshPlayerBotEnergyShardCensus(DWORD now)
	{
		TPlayerBotEnergyShardCensus& c = s_kPlayerBotEnergyShardCensus;
		if (c.at != 0 && now - c.at < PLAYERBOT_ENERGY_SHARD_CENSUS_MS)
			return;
		c.at = now ? now : 1;
		c.units = 0;
		c.shops.clear();
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		// Every bot stand the shop manager holds, whatever its channel: the cap
		// is the world's. A stand that ran out of time shows nothing to a buyer
		// and is on no count (as on the market ledger).
		for (const auto& [owner, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || shop->GetDuration() == 0 ||
					!CPlayerBotManager::instance().IsRegisteredBotPID(shop->GetOwnerPID()))
				continue;
			int units = 0;
			for (const auto& [id, line] : shop->GetItems())
				if (line && IsPlayerBotEnergyShardVnum(line->GetInfo().vnum))
					units += (int)line->GetInfo().count;
			if (units > 0)
			{
				c.units += units;
				c.shops.insert(shop->GetOwnerPID());
			}
		}
#endif
		for (std::map<DWORD, std::pair<int, DWORD> >::iterator it = s_mapPlayerBotEnergyShardPending.begin();
				it != s_mapPlayerBotEnergyShardPending.end(); )
		{
			if (now - it->second.second >= PLAYERBOT_ENERGY_SHARD_PENDING_MS)
				s_mapPlayerBotEnergyShardPending.erase(it++);
			else
				++it;
		}
	}

	// The units on the counters and the counters showing them, the pending
	// lines included.
	void GetPlayerBotEnergyShardMarket(DWORD now, int& units, std::set<DWORD>& shops)
	{
		RefreshPlayerBotEnergyShardCensus(now);
		units = s_kPlayerBotEnergyShardCensus.units;
		shops = s_kPlayerBotEnergyShardCensus.shops;
		for (std::map<DWORD, std::pair<int, DWORD> >::const_iterator it = s_mapPlayerBotEnergyShardPending.begin();
				it != s_mapPlayerBotEnergyShardPending.end(); ++it)
		{
			if (now - it->second.second >= PLAYERBOT_ENERGY_SHARD_PENDING_MS)
				continue;
			units += it->second.first;
			if (it->second.first > 0)
				shops.insert(it->first);
		}
		units = std::max(0, units);
	}

	// A line put up (units > 0) or taken home (units < 0) by this owner.
	void NotePlayerBotEnergyShardLine(DWORD pid, int units, DWORD now)
	{
		std::pair<int, DWORD>& p = s_mapPlayerBotEnergyShardPending[pid];
		if (now - p.second >= PLAYERBOT_ENERGY_SHARD_PENDING_MS)
			p.first = 0;
		p.first += units;
		p.second = now ? now : 1;
	}

	// The lines of ten this owner may still put up under the world's caps.
	int GetPlayerBotEnergyShardLineRoom(DWORD pid, DWORD now)
	{
		int units = 0;
		std::set<DWORD> shops;
		GetPlayerBotEnergyShardMarket(now, units, shops);
		return std::max(0, PLAYERBOT_ENERGY_SHARD_MARKET_UNITS - units) / PLAYERBOT_ENERGY_SHARD_LINE_UNITS;
	}

	// The packs of ten this bot puts up now: its spare in whole packs, as far
	// as the caps allow.
	int GetPlayerBotEnergyShardLinesForSale(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		const int packs = GetPlayerBotEnergyShardsForSale(ch) / PLAYERBOT_ENERGY_SHARD_LINE_UNITS;
		if (packs <= 0)
			return 0;
		return std::min(packs, GetPlayerBotEnergyShardLineRoom(ch->GetPlayerID(), get_dword_time()));
	}

	// Whether a shard line of `count` units standing on this owner's counter
	// comes home: a line of any other size than a pack, or the world's counters
	// past the units' cap - any counter with shards gives one back.
	bool IsPlayerBotEnergyShardLineUnwanted(DWORD pid, int count, DWORD now, const char** why)
	{
		if (count != PLAYERBOT_ENERGY_SHARD_LINE_UNITS)
		{
			if (why) *why = "energy_shard_pack";
			return true;
		}
		int units = 0;
		std::set<DWORD> shops;
		GetPlayerBotEnergyShardMarket(now, units, shops);
		if (units > PLAYERBOT_ENERGY_SHARD_MARKET_UNITS)
		{
			if (why) *why = "energy_shard_units";
			return true;
		}
		return false;
	}

	// ------------------------------------------------------------ the Alchemist

	// energia_alchemik.quest, can_make.setting(): the cumulative odds of each
	// band and the shards of each step.
	int RollPlayerBotEnergyShards(int levelLimit)
	{
		static const int s_acc[3][10] = {
			{ 30, 55, 70, 80, 90, 95, 97, 98, 99, 100 },	// "35to50"
			{ 20, 40, 60, 75, 85, 91, 96, 98, 99, 100 },	// "51to70"
			{ 10, 25, 45, 65, 80, 88, 94, 97, 99, 100 },	// "upto70"
		};
		static const int s_num[10] = { 0, 1, 2, 3, 4, 6, 8, 10, 12, 15 };
		const int band = levelLimit <= 50 ? 0 : (levelLimit <= 70 ? 1 : 2);
		const int r = number(1, 100);
		// getItemNum: the first step whose odds r is under; r = 100 is under
		// none of them and gives nothing, as in the quest.
		for (int i = 0; i < 10; ++i)
			if (r < s_acc[band][i])
				return s_num[i];
		return 0;
	}

	// The quest's own test of the piece (20001.take): a weapon but an arrow,
	// or an armour (the jewellery is armour), of level 35 or more. Never a
	// talisman: 700 000 yang is more than fifteen shards.
	bool IsPlayerBotEnergyScrapPiece(LPITEM item)
	{
		if (!item || IsPlayerBotFixedPriceTalismanVnum(item->GetVnum()))
			return false;
		if (item->GetType() == ITEM_WEAPON)
		{
			if (item->GetSubType() == WEAPON_ARROW)
				return false;
		}
		else if (item->GetType() != ITEM_ARMOR)
			return false;
		return item->GetLevelLimit() >= PLAYERBOT_ENERGY_MIN_LEVEL;
	}

	// A piece of this bot's that the merchant would buy and the Alchemist
	// takes: junk by every rule there is, and nothing the operator named.
	bool IsPlayerBotEnergyScrap(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || (int)ch->GetLevel() < PLAYERBOT_ENERGY_MIN_LEVEL || item->IsEquipped() ||
				item->isLocked() || !IsPlayerBotEnergyScrapPiece(item))
			return false;
		if (IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		if (GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE)
			return false;
		return IsPlayerBotJunkItem(ch, item);
	}

	// Since when this bot holds scrap for the Alchemist (the first piece held).
	std::map<DWORD, DWORD> s_mapPlayerBotEnergyScrapSince;

	bool IsPlayerBotEnergyScrapHoldOver(DWORD pid, DWORD now)
	{
		std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotEnergyScrapSince.find(pid);
		return it != s_mapPlayerBotEnergyScrapSince.end() && now - it->second >= PLAYERBOT_ENERGY_SCRAP_HOLD_MS;
	}

	// Asked by the merchant's sale of a piece it is about to buy: stays in the
	// bag for the Alchemist instead.
	bool ShouldPlayerBotKeepScrapForAlchemist(LPCHARACTER ch, LPITEM item, DWORD now)
	{
		if (!IsPlayerBotEnergyScrap(ch, item))
			return false;
		playerbot_empire_rules::TPoint alchemist;
		if (!playerbot_empire_rules::GetAlchemist(ch->GetMapIndex(), alchemist))
			return false;
		if (IsPlayerBotBagUnderPressure(ch) || IsPlayerBotEnergyScrapHoldOver(ch->GetPlayerID(), now))
			return false;
		return true;
	}

	int CollectPlayerBotEnergyScrap(LPCHARACTER ch, std::vector<LPITEM>* out);

	// After a merchant's round: what it left in the bag for the Alchemist.
	// Nothing held and no held piece left (the weapon and the armour merchant
	// are two rounds of one visit) - the hold is over: sold, or there was none.
	void NotePlayerBotEnergyScrapHeld(LPCHARACTER ch, int held, DWORD now)
	{
		if (!ch)
			return;
		if (held <= 0)
		{
			if (CollectPlayerBotEnergyScrap(ch, NULL) == 0)
				s_mapPlayerBotEnergyScrapSince.erase(ch->GetPlayerID());
			return;
		}
		if (s_mapPlayerBotEnergyScrapSince.insert(std::make_pair(ch->GetPlayerID(), now ? now : 1)).second)
			sys_log(0, "PLAYERBOT_ENERGY: scrap held for the Alchemist pid=%u name=%s pieces=%d map=%ld",
					ch->GetPlayerID(), ch->GetName(), held, ch->GetMapIndex());
	}

	// The held scrap in the bag, for the walk and the counter.
	int CollectPlayerBotEnergyScrap(LPCHARACTER ch, std::vector<LPITEM>* out)
	{
		int pieces = 0;
		if (!ch || !ch->IsItemLoaded())
			return 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotEnergyScrap(ch, item))
				continue;
			++pieces;
			if (out)
				out->push_back(item);
		}
		return pieces;
	}

	// Whether the Alchemist's errand goes for the held scrap now: the merchant
	// held some on this visit (the bot is due), and some is still in the bag.
	bool WantsPlayerBotEnergyScrapVisit(LPCHARACTER ch, DWORD now)
	{
		if (!ch || s_mapPlayerBotEnergyScrapSince.find(ch->GetPlayerID()) == s_mapPlayerBotEnergyScrapSince.end())
			return false;
		playerbot_empire_rules::TPoint alchemist;
		if (IsPlayerBotEnergyScrapHoldOver(ch->GetPlayerID(), now) ||
				!playerbot_empire_rules::GetAlchemist(ch->GetMapIndex(), alchemist))
			return false;
		return CollectPlayerBotEnergyScrap(ch, NULL) > 0;
	}

	// The walk to him failed: the hold is over, and the next merchant's round
	// sells what was held, as it did before.
	void GiveUpPlayerBotEnergyScrap(LPCHARACTER ch, DWORD now)
	{
		std::map<DWORD, DWORD>::iterator it = ch ? s_mapPlayerBotEnergyScrapSince.find(ch->GetPlayerID())
				: s_mapPlayerBotEnergyScrapSince.end();
		if (it != s_mapPlayerBotEnergyScrapSince.end())
			it->second = now - PLAYERBOT_ENERGY_SCRAP_HOLD_MS;
	}

	// At the Alchemist's counter: every held piece is dismantled the quest's
	// way, one roll a piece. The shards made.
	int DismantlePlayerBotEnergyScrap(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		std::vector<LPITEM> scrap;
		CollectPlayerBotEnergyScrap(ch, &scrap);
		s_mapPlayerBotEnergyScrapSince.erase(ch->GetPlayerID());
		if (scrap.empty())
			return 0;
		int shards = 0, empty = 0;
		for (size_t i = 0; i < scrap.size(); ++i)
		{
			LPITEM item = scrap[i];
			const int levelLimit = item->GetLevelLimit();
			const DWORD vnum = item->GetVnum();
			ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_ENERGY_SHARDS");
			const int n = RollPlayerBotEnergyShards(levelLimit);
			if (n == 0)
				++empty;
			shards += n;
			sys_log(1, "PLAYERBOT_ENERGY: dismantled pid=%u vnum=%u level=%d shards=%d",
					ch->GetPlayerID(), vnum, levelLimit, n);
		}
		// The pieces' cells are free now, so the shards always have one.
		for (int left = shards; left > 0; )
		{
			const int chunk = std::min(left, 200);
			ch->AutoGiveItem(PLAYERBOT_ENERGY_SHARD_VNUM, chunk, -1, false);
			left -= chunk;
		}
		sys_log(0, "PLAYERBOT_ENERGY: at the Alchemist pid=%u name=%s pieces=%u shards=%d nothing=%d held_shards=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)scrap.size(), shards, empty,
				CountPlayerBotEnergyShards(ch));
		return shards;
	}
}

#endif
