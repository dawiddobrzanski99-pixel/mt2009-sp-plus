#ifndef __INC_METIN2_PLAYERBOT_RANK_FRUIT_MARKET_H__
#define __INC_METIN2_PLAYERBOT_RANK_FRUIT_MARKET_H__

// MT2009_PLUS_RANK_FRUIT_MARKET_V1 - the bots buy the rank fruit they can eat
// (the owner, 8 October: "dlaczego boty wystawiaja tyle jablek, a ich nie
// uzywaja ani nie kupuja? Niech wiedza, ze ranga daje bonusy ... ci, ktorzy maja
// range juz poza zakresem jablek, niech wystawiaja jablka i kupuja gruszki").
//
// The fruits 80050-80054 (playerbot_rank_points.h) work in one range of the
// total each: Jablko under 20 000, Gruszka 20 000-40 000, and so on. A bot ate
// the fitting ones its own kills dropped and listed the rest - and nobody
// bought: no buying rule knew the fruits. So the counters filled with the
// fruits of the bands their keepers were past (test world, 8 October: 919
// Gruszki on 484 lines, kept by bots under 20 000 that can not eat them, and 79
// Jablka on 34 lines, all kept by bots at the alignment's cap), while 4 414 bot
// characters stood under 20 000, hungry for Jablka that their level's Metins
// no longer drop (Jablko is the fruit of monsters up to 53).
//
// Now an eater (IsPlayerBotRankFruitEater, three bots in four, never a
// trader) buys the fruit of its total off the counters - on every stand of its
// map, the gambler's way (FindPlayerBotGambleMaterialPick) - up to
// PLAYERBOT_RANK_FRUIT_BUY_AHEAD pieces ahead and no more than its range still
// takes, at most PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT of the price table
// (GetPlayerBotRankFruitPrice) a piece and out of
// PLAYERBOT_RANK_FRUIT_PURSE_PERCENT of what it can spare. It eats them at its
// next look (ManagePlayerBotRankPoints). The other bots list every fruit they
// hold, and every bot lists a fruit out of its range.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, from playerbot_manager.cpp, before playerbot_market.h.

namespace
{
	int GetPlayerBotReservedGold(LPCHARACTER ch);

	const int PLAYERBOT_RANK_FRUIT_BUY_AHEAD = 10;
	const int PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT = 130;
	const int PLAYERBOT_RANK_FRUIT_PURSE_PERCENT = 30;

	// The fruit this bot eats now, or NULL: an eater, its total read, in a range.
	const mt2009_rankp::SFruit* GetPlayerBotRankFruitToEat(LPCHARACTER ch)
	{
		using namespace mt2009_rankp;
		if (!ch || !Enabled() || !IsPlayerBotRankFruitEater(ch) || !Known(ch))
			return NULL;
		return FruitForPoints(KnownPoints(ch));
	}

	// How many more pieces of its fruit the bot buys: what its range still
	// takes, PLAYERBOT_RANK_FRUIT_BUY_AHEAD at most, less what it holds.
	int GetPlayerBotRankFruitWant(LPCHARACTER ch, DWORD* vnumOut = NULL)
	{
		const mt2009_rankp::SFruit* fruit = GetPlayerBotRankFruitToEat(ch);
		if (vnumOut)
			*vnumOut = fruit ? fruit->vnum : 0;
		if (!fruit || !ch->IsItemLoaded() || fruit->gain <= 0)
			return 0;
		const int left = fruit->to - mt2009_rankp::KnownPoints(ch);
		const int range = std::max(1, (left + fruit->gain - 1) / fruit->gain);
		return std::max(0, std::min(range, PLAYERBOT_RANK_FRUIT_BUY_AHEAD) - (int)ch->CountSpecifyItem(fruit->vnum));
	}

	// A counter's line the bot would eat: its fruit, no more than it wants.
	bool WantsPlayerBotRankFruitOffer(LPCHARACTER ch, LPITEM offer)
	{
		DWORD vnum = 0;
		const int want = GetPlayerBotRankFruitWant(ch, &vnum);
		return offer && want > 0 && offer->GetVnum() == vnum && (int)offer->GetCount() <= want;
	}

	// What an eater spends on fruit: a share of what it can spare.
	long long GetPlayerBotRankFruitBudget(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return spare > 0 ? spare * PLAYERBOT_RANK_FRUIT_PURSE_PERCENT / 100 : 0;
	}

	// The price: no more than the table's a piece and the tolerance, out of the
	// fruit's share of the purse.
	bool CanPlayerBotPayForRankFruit(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long unit = price / std::max<long long>(1, (long long)item->GetCount());
		const long long table = (long long)GetPlayerBotRankFruitPrice(item->GetVnum());
		return table > 0 && unit <= table * PLAYERBOT_RANK_FRUIT_BUY_OVER_PERCENT / 100 &&
				price <= GetPlayerBotRankFruitBudget(ch);
	}

	// Worth a walk to the market: it wants its fruit, a counter has some (the
	// ledger) and the purse pays one at the table's price.
	bool PlayerBotWantsRankFruitFromMarket(LPCHARACTER ch)
	{
		DWORD vnum = 0;
		if (GetPlayerBotRankFruitWant(ch, &vnum) <= 0 || vnum == 0)
			return false;
		const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnum);
		return entry && entry->dwSupplyUnits > 0 &&
				GetPlayerBotRankFruitBudget(ch) >= (long long)GetPlayerBotRankFruitPrice(vnum);
	}

	// For the stands' scan (FindPlayerBotGambleMaterialPick): the fruit and how
	// many, and the most one line may cost. 0 - nothing wanted.
	long long CollectPlayerBotRankFruitMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		DWORD vnum = 0;
		const int want = GetPlayerBotRankFruitWant(ch, &vnum);
		if (want <= 0 || vnum == 0)
			return 0;
		const long long budget = GetPlayerBotRankFruitBudget(ch);
		if (budget < (long long)GetPlayerBotRankFruitPrice(vnum))
			return 0;
		missing[vnum] = want;
		return budget;
	}
}

#endif
