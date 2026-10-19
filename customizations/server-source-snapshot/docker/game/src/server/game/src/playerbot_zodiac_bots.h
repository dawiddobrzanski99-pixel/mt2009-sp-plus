#ifndef __INC_METIN2_PLAYERBOT_ZODIAC_BOTS_H__
#define __INC_METIN2_PLAYERBOT_ZODIAC_BOTS_H__

// MT2009_PLUS_ZODIAC_BOTS_V1 - a person's party bots in the Swiatynia Zodiaku
// (MT2009_PLUS_ZODIAC_V1, server-patches/zodiak; Autor: Digi Rasta).
//
// The temple is not a CDungeon: its floors are private copies of 358
// (3580000-3589999) owned by a CZodiac (playerbot_zodiac_temple.h), whose
// member count ends the temple when the last character is out. So a bot:
//
//   - is a member of the temple whose floor it stands on, and of no other -
//     CPlayerBotManager::WarpBot calls SyncPlayerBotZodiac after every map
//     change it makes (the temple's own JumpParty and JoinParty warp the
//     party's bots that way, and the party dungeon pass puts a bot after its
//     person by it); a person gets that from input_login.cpp's hook;
//   - goes in after its person like into any party dungeon
//     (playerbot_party_dungeon.h: 358 is one of IsPlayerBotPartyDungeonMap's
//     maps, the instance is let through when the temple exists), fights
//     beside the person and leaves with the person;
//   - leaves the statues (20452-20463) and the cannon (20464) to the person:
//     a statue takes 1 point a blow and the cannon fires on its own when hit -
//     a bot hits them only when the person does;
//   - stands up where it fell with the temple's Prisms (33025, 33032) it
//     carries, the person's price (do_revive on itself: 1, 2, 4, 8, 10 by the
//     deaths); a bot without enough of them stands up for free - restart_here
//     would only send it the temple's revive window, which a bot never answers,
//     and leave it lying for good. The temple's death flags are cleared once
//     the bot is out. MT2009_PLUS_SIDEKICK_ZODIAC_V1: except a person's own
//     Towarzysz while the person stands on its floor - it keeps the temple's
//     rule and waits for Prisms (HoldPlayerBotSidekickInZodiac,
//     playerbot_sidekick.h); every map change of a bot (TransitionPlayerBotMap,
//     PlacePlayerBotSidekickAt) syncs its temple now, not WarpBot's alone.
//   - the person's Anima Spheres pay the entry: the quest zodiac_temples does
//     not count a bot of the party (pc.is_playerbot()).
//
// The bots' own temple runs are not here (see server-patches/zodiak/README.md,
// "Boty").

#ifdef ENABLE_12ZI
#include "playerbot_zodiac_temple.h"
#endif

namespace
{
	const long PLAYERBOT_ZODIAC_MAP = 358;
	const long PLAYERBOT_ZODIAC_INSTANCE_MIN = 3580000;
	const long PLAYERBOT_ZODIAC_INSTANCE_MAX = 3589999;
	const DWORD PLAYERBOT_ZODIAC_PRISM = 33025;
	const DWORD PLAYERBOT_ZODIAC_PRISM_AWAKENING = 33032;
	unsigned int s_uPlayerBotZodiacFreeRevives = 0;
	// MT2009_PLUS_ZODIAC_RUNS_V1: the bots' own runs count their deaths (playerbot_zodiac_runs.h, later).
	void NotePlayerBotZodiacRunRevive(DWORD pid, bool prisms);
	unsigned int s_uPlayerBotZodiacPrismRevives = 0;

	bool IsPlayerBotZodiacInstance(long mapIndex)
	{
		return mapIndex >= PLAYERBOT_ZODIAC_INSTANCE_MIN && mapIndex <= PLAYERBOT_ZODIAC_INSTANCE_MAX;
	}

	// The temple's statues and its cannon: the person's to hit.
	bool IsPlayerBotZodiacLeftToPerson(DWORD race)
	{
		return race >= 20452 && race <= 20464;
	}

	// A temple floor that exists now (the instance is the CZodiac's).
	bool IsPlayerBotZodiacLive(long mapIndex)
	{
#ifdef ENABLE_12ZI
		return IsPlayerBotZodiacInstance(mapIndex) && CZodiacManager::instance().FindByMapIndex(mapIndex) != NULL;
#else
		(void)mapIndex;
		return false;
#endif
	}

	// After a map change the bot's temple is the one of the floor it stands
	// on; out of the temple its death count and flags go.
	void SyncPlayerBotZodiac(LPCHARACTER bot, long mapIndex)
	{
#ifdef ENABLE_12ZI
		if (!bot)
			return;
		LPZODIAC want = IsPlayerBotZodiacInstance(mapIndex) ? CZodiacManager::instance().FindByMapIndex(mapIndex) : NULL;
		LPZODIAC had = bot->GetZodiac();
		if (had != want)
		{
			if (had)
				bot->SetZodiac(NULL);
			if (want)
				bot->SetZodiac(want);
			sys_log(0, "PLAYERBOT_ZODIAC: member pid=%u name=%s map=%ld temple=%s",
					bot->GetPlayerID(), bot->GetName(), mapIndex, want ? "in" : "out");
		}
		if (!want)
		{
			bot->SetDeadCount(0);
			if (bot->GetQuestFlag("12zi_temple.IsDead") != 0)
				bot->SetQuestFlag("12zi_temple.IsDead", 0);
			if (bot->GetQuestFlag("12zi_temple.PrismNeed") != 0)
				bot->SetQuestFlag("12zi_temple.PrismNeed", 0);
		}
#else
		(void)bot;
		(void)mapIndex;
#endif
	}

	// MT2009_PLUS_SIDEKICK_ZODIAC_V1: the temple's death count and flags of a
	// bot that stands outside every temple floor - one taken off a floor some
	// other way than a warp of this core's (the floor closed under it and the
	// bot loaded anew on 358, an old one from before this was kept) still had
	// "12zi_temple.IsDead" and "PrismNeed", and on its next floor the temple
	// asked it for the Prisms of the deaths before. Membership is not touched
	// here: SyncPlayerBotZodiac is the only one that sets it.
	void ClearPlayerBotZodiacFlagsOutside(LPCHARACTER bot)
	{
#ifdef ENABLE_12ZI
		if (!bot || IsPlayerBotZodiacInstance(bot->GetMapIndex()))
			return;
		if (bot->GetDeadCount() != 0)
			bot->SetDeadCount(0);
		if (bot->GetQuestFlag("12zi_temple.IsDead") != 0)
			bot->SetQuestFlag("12zi_temple.IsDead", 0);
		if (bot->GetQuestFlag("12zi_temple.PrismNeed") != 0)
			bot->SetQuestFlag("12zi_temple.PrismNeed", 0);
#else
		(void)bot;
#endif
	}

	// The Prisms the temple asks of a revive after the bot's deaths there:
	// 1, 2, 4, 8, then 10 (cmd_general.cpp's restart hook, do_revive).
	int GetPlayerBotZodiacPrismNeed(LPCHARACTER ch)
	{
#ifdef ENABLE_12ZI
		const int n = std::max<int>(ch->GetQuestFlag("12zi_temple.PrismNeed"), (int)ch->GetDeadCount());
		if (n <= 2)
			return std::max(1, n);
		if (n == 3)
			return 4;
		if (n == 4)
			return 8;
		return 10;
#else
		(void)ch;
		return 0;
#endif
	}

	// HandleDeath (playerbot_survival.h): true when the bot lies on a temple
	// floor - it stood up here (prisms or not), restart_here is not for it.
	bool RevivePlayerBotInZodiac(LPCHARACTER ch)
	{
#ifdef ENABLE_12ZI
		if (!ch || !ch->IsDead() || !IsPlayerBotZodiacInstance(ch->GetMapIndex()))
			return false;
		const int need = GetPlayerBotZodiacPrismNeed(ch);
		const int have = (int)(ch->CountSpecifyItem(PLAYERBOT_ZODIAC_PRISM) + ch->CountSpecifyItem(PLAYERBOT_ZODIAC_PRISM_AWAKENING));
		if (have >= need)
		{
			char cmd[64];
			snprintf(cmd, sizeof(cmd), "revive %u", (unsigned int)ch->GetVID());
			interpret_command(ch, cmd, strlen(cmd));
			if (!ch->IsDead())
			{
				NotePlayerBotZodiacRunRevive(ch->GetPlayerID(), true);
				++s_uPlayerBotZodiacPrismRevives;
				sys_log(0, "PLAYERBOT_ZODIAC: revived pid=%u name=%s map=%ld prisms=%d left=%d deaths=%u total=%u",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), need, have - need,
						(unsigned int)ch->GetDeadCount(), s_uPlayerBotZodiacPrismRevives);
				return true;
			}
		}
		// No prisms (or the revive refused): the bot's own stand-up, as
		// restart_here does it anywhere else.
		ch->ChatPacket(CHAT_TYPE_COMMAND, "CloseRestartWindow");
		ch->SetPosition(POS_STANDING);
		ch->StartRecoveryEvent();
		ch->RestartAtSamePos();
		ch->PointChange(POINT_HP, 50 - ch->GetHP());
		ch->ReviveInvisible(5);
		ch->SetQuestFlag("12zi_temple.IsDead", 0);
		++s_uPlayerBotZodiacFreeRevives;
		NotePlayerBotZodiacRunRevive(ch->GetPlayerID(), false);
		sys_log(0, "PLAYERBOT_ZODIAC: stood up pid=%u name=%s map=%ld prisms_needed=%d had=%d deaths=%u total=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), need, have, (unsigned int)ch->GetDeadCount(),
				s_uPlayerBotZodiacFreeRevives);
		return true;
#else
		(void)ch;
		return false;
#endif
	}
}

#endif
