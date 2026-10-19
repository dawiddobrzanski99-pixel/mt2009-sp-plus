#ifndef __INC_METIN2_PLAYERBOT_PRIORITIES_H__
#define __INC_METIN2_PLAYERBOT_PRIORITIES_H__

// MT2009_PLUS_BOT_PRIORITIES_V1 - the order of a bot's business.
//
// The owner, 9 October: "Boty maja jasna kolejnosc zajec: przetrwanie, rajd
// z druzyna, umowione spotkanie i pelny plecak ida przed reszta". The tick
// was already an order - each pass claims it or hands it on - but four
// things could be overtaken by what stood above them. Now, highest first:
//
//   1. SURVIVAL - hurt (PLAYERBOT_PRIORITY_SURVIVAL_HP_PERCENT), in a
//      retreat or a recovery after death, or with something hitting it:
//      no meeting walk, no deal walk; the fight, the potions and the
//      retreat have the tick (IsPlayerBotSurvivalFirst).
//   2. A RAID WITH ITS PARTY - the tower, a boss, the Catacomb, the bots'
//      dungeon runs (IsPlayerBotInDungeonBusiness): a meeting a bot had is
//      called off with a word, and no deal or meeting is taken meanwhile
//      (the deal's "jestem w dungu", the meeting's plan).
//   3. AN AGREED MEETING - a deal with a person (playerbot_chat_deals.h) or
//      with a bot (playerbot_meetups.h): ahead of every errand and of the
//      full bag (their handlers sit above them in the tick).
//   4. A FULL BAG - the leisure errands (the horse, the rod, the pickaxe,
//      the herbs, Uriel, Mistrz, the stay in town, Baek-Go's board) stand
//      down while the bag is full, so the town visit and the way to town
//      have the bot (IsPlayerBotBagFirst).
//   5. The rest, in the tick's order as before.
//
// An implementation fragment: include it once, after playerbot_targeting.h
// (FindPlayerBotEngagedTarget); the deals and the meetings declare what
// they ask of it.

namespace
{
	const int PLAYERBOT_PRIORITY_SURVIVAL_HP_PERCENT = 40;

	bool IsPlayerBotSurvivalFirst(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead())
			return true;
		if (state.bRecoveringAfterDeath || state.bTacticalRetreat)
			return true;
		if (ch->GetMaxHP() > 0 && ch->GetHP() * 100 < ch->GetMaxHP() * PLAYERBOT_PRIORITY_SURVIVAL_HP_PERCENT)
			return true;
		return !ch->GetExchange() && FindPlayerBotEngagedTarget(ch, &state, dwNow) != NULL;
	}

	bool IsPlayerBotBagFirst(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotInDungeonBusiness(ch, state))
			return false;
		return (IsPlayerBotPersonaEnabled() ? IsPlayerBotBagFull(ch) : false) || ch->GetEmptyInventory(3) < 0;
	}
}

#endif
