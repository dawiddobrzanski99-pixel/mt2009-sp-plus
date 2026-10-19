#ifndef __INC_METIN2_PLAYERBOT_ORNAMENT_FARMERS_H__
#define __INC_METIN2_PLAYERBOT_ORNAMENT_FARMERS_H__

// MT2009_PLUS_ORNAMENT_FARMERS_V1: the ornament farmers of the second villages
// (the owner, 7 October: "dropki ornamentow na m2"). Ornament (30031) is the
// talisman's refine material - every step at the Blacksmith takes 10 Kwiat
// Zywiolu, 1 Ornament and a Talisman +0 (refine_proto 20001-21200,
// server-patches/zywioly) - and it came only from the Sworn Archers' etc drop
// (0.9%). The Sworn Archers (Zaprzys. Lucznik 302, its twin 332, level 20) at
// the start of each kingdom's second village drop it 2% a kill more now
// (linux-port/docker/game/mob_drop_item.ornaments.append.txt), and a few low
// bots farm them for the market, the way the level-30 weapon droppers farm
// their Bestial (playerbot_l30_dropper.h - this is its pattern):
//
//   - who: on each core that hosts a kingdom's second village, every minute,
//     the kingdom's count is made up to PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM
//     from the bots playing here - ordinary ones the checklist would take
//     (IsPlayerBotProgressionEligible: no dropper, no cohort, no companion, no
//     shouter), no trader, no party fighter, of PLAYERBOT_ORNAMENT_FARMER_MIN_LEVEL
//     to the lock and the two levels every dropper is allowed past it. A bot
//     that was one before (its quest flag) first, then one already at its
//     working level, then the lowest hash of pid, channel and kingdom - the
//     same bots after every restart; the first ten minutes of a core only
//     take back the flagged ones. MT2009_PLUS_ORNAMENT_FARMERS_V2: from level
//     twelve, the higher first, and with nobody of the band in play the
//     identities of the band are called from the registry (the test world
//     played six bots of 15-25 on that core, all of them taken);
//   - what it is: BOT_PERSONALITY_ORNAMENT_FARMER, a dropper like the others
//     (IsPlayerBotDropper: a stall keeper's counter, no Metin expedition),
//     held at PLAYERBOT_EXP_LOCK_ORNAMENT_FARMER (ManagePlayerBotExpLock), no
//     M3, no Monkey Dungeon, no frontier;
//   - where: from PLAYERBOT_ORNAMENT_FARMER_WORK_LEVEL (the second village's
//     own first level) its kingdom's second village, and there the Sworn
//     camps at its start (PLAYERBOT_ORNAMENT_FARMER_SPOTS, the cluster centres
//     of the camps' spawn points - group_group 206 of regen.txt), going round
//     them (ManagePlayerBotWander);
//   - what it kills: every Sworn monster there - soldiers, archers, generals,
//     commanders (301-304, 331-334; the owner's word: the farmer clears the
//     whole Sworn group, the drop is the archers') - as a priority target the
//     way the Bestials are the M2 dropper's (playerbot_targeting.h);
//   - what it sells: the ornaments are a refine material
//     (IsPlayerBotTradeableMaterial - the talisman recipes consume them), so
//     its counter lists them in the sizes a player cuts, and every bot and
//     player can buy them for a talisman.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, from playerbot_manager.cpp, before playerbot_travel.h (the
// world travel, the wander and the targeting ask it).

namespace
{
	// Defined further down the unit.
	BYTE GetPlayerBotStablePersonality(LPCHARACTER ch, BYTE role);
	BYTE GetPlayerBotStableAmbition(LPCHARACTER ch, BYTE personality);
	bool IsPlayerBotPastDropperBand(LPCHARACTER ch, BYTE personality);
	bool IsPlayerBotProgressionEligible(LPCHARACTER ch, const TPlayerBotAIState& state);
	BYTE GetPlayerBotCharakter(BYTE drawn);
	bool IsPlayerBotHumanLedParty(LPPARTY party);
	bool IsPlayerBotMapHostedHere(long mapIndex);
	// MT2009_PLUS_FARMER_LINK_V1 (playerbot_farmer_link.h, included later): a
	// spot farmer already has its ground, and a main is somebody's main.
	bool IsPlayerBotFarmerPID(DWORD pid);
	bool IsPlayerBotFarmerMainPID(DWORD pid);

	const DWORD PLAYERBOT_ORNAMENT_VNUM = 30031;
	const char* const PLAYERBOT_ORNAMENT_FARMER_FLAG = "playerbot.ornament_farmer";
	const DWORD PLAYERBOT_ORNAMENT_FARMER_SEED = 0x4f524e41U;
	const int PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM = 2;
	// MT2009_PLUS_ORNAMENT_FARMERS_V2: twelve, not seventeen - the test world
	// had six bots of 15-25 in play on the core of the second villages (of
	// 1244), every one of them already a level-30 weapon dropper, and the
	// pool stood at nothing for hours. One under the working level levels to
	// it first, as any bot of its level does.
	const BYTE PLAYERBOT_ORNAMENT_FARMER_MIN_LEVEL = 12;
	// The second village's first level (the "m2" row of the operator's map
	// table): under it the farmer plays and levels as any bot of its level.
	const BYTE PLAYERBOT_ORNAMENT_FARMER_WORK_LEVEL = 20;
	const DWORD PLAYERBOT_ORNAMENT_FARMER_PASS_MS = 60 * 1000;
	const DWORD PLAYERBOT_ORNAMENT_FARMER_SETTLE_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ORNAMENT_FARMER_CENSUS_MS = 10 * 60 * 1000;
	// The ornaments that open the farmer's counter whatever its roll
	// (GetPlayerBotShopReason, playerbot_town.h).
	const int PLAYERBOT_ORNAMENT_FARMER_STALL_UNITS = 3;
	// MT2009_PLUS_ORNAMENT_FARMERS_V2: with nobody of the band in play, the
	// pass calls identities of the band from the registry
	// (CPlayerBotManager::CollectIdleRegisteredBots / ScheduleExtraBots, the
	// way the Arezzo cohorts come), at most once a kingdom every
	// PLAYERBOT_ORNAMENT_FARMER_SUMMON_MS; a called bot comes before any other
	// candidate for PLAYERBOT_ORNAMENT_FARMER_SUMMON_HOLD_MS.
	const DWORD PLAYERBOT_ORNAMENT_FARMER_SUMMON_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ORNAMENT_FARMER_SUMMON_HOLD_MS = 20 * 60 * 1000;
	std::map<DWORD, DWORD> s_mapPlayerBotOrnamentFarmerSummoned;	// pid -> when called
	DWORD s_adwPlayerBotOrnamentFarmerSummonAt[4] = { 0, 0, 0, 0 };
	int s_aiPlayerBotOrnamentFarmerSummoned[4] = { 0, 0, 0, 0 };	// since the last census

	bool IsPlayerBotOrnamentFarmerSummoned(DWORD pid, DWORD now)
	{
		std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotOrnamentFarmerSummoned.find(pid);
		return it != s_mapPlayerBotOrnamentFarmerSummoned.end() &&
				now - it->second < PLAYERBOT_ORNAMENT_FARMER_SUMMON_HOLD_MS;
	}

	// The Sworn of the second villages' first camps: soldier, archer, general,
	// commander, and their twins 331-334.
	bool IsPlayerBotOrnamentFarmerPrey(DWORD race)
	{
		return (race >= 301 && race <= 304) || (race >= 331 && race <= 334);
	}

	// The Sworn camps of each kingdom's second village: the centres of the
	// clusters of group_group 206's spawn points (regen.txt, measured
	// 7 October), each snapped to a spawn point of its own cluster.
	// Jayang (3): the camps along its east edge; Bokjung (23): its north-west;
	// Bakra (43): its north-east.
	const int PLAYERBOT_ORNAMENT_FARMER_SPOT_COUNT = 5;
	const TPlayerBotMapPoint PLAYERBOT_ORNAMENT_FARMER_SPOTS[3][PLAYERBOT_ORNAMENT_FARMER_SPOT_COUNT] = {
		{ { 395500, 880300 }, { 394800, 892000 }, { 394700, 906200 }, { 387500, 906600 }, { 399600, 905100 } },
		{ { 122000, 231500 }, { 119000, 227500 }, { 118600, 233300 }, { 117000, 226500 }, { 126500, 226500 } },
		{ { 897100, 219400 }, { 902200, 219800 }, { 904100, 226800 }, { 890600, 217800 }, { 906300, 224700 } },
	};

	// Its kingdom's second village.
	long GetPlayerBotOrnamentFarmerMap(BYTE empire)
	{
		return empire >= 1 && empire <= 3
				? playerbot_empire_rules::GetHomeMap((int)empire, playerbot_empire_rules::MAP_ROLE_M2) : 0;
	}

	const TPlayerBotMapPoint* GetPlayerBotOrnamentFarmerSpots(BYTE empire, size_t& count)
	{
		count = 0;
		if (empire < 1 || empire > 3)
			return NULL;
		count = PLAYERBOT_ORNAMENT_FARMER_SPOT_COUNT;
		return PLAYERBOT_ORNAMENT_FARMER_SPOTS[empire - 1];
	}

	// An ornament farmer at its working level: its ground is its kingdom's
	// second village. Under it it plays and levels as any bot of its level.
	bool IsPlayerBotOrnamentFarmerAtWork(LPCHARACTER ch)
	{
		return ch && ch->GetLevel() >= PLAYERBOT_ORNAMENT_FARMER_WORK_LEVEL &&
				GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_ORNAMENT_FARMER;
	}

	// At work and on its ground now.
	bool IsPlayerBotOrnamentFarmerOnGround(LPCHARACTER ch)
	{
		return ch && ch->GetMapIndex() == GetPlayerBotOrnamentFarmerMap(ch->GetEmpire()) &&
				IsPlayerBotOrnamentFarmerAtWork(ch);
	}

	// A Sworn monster this farmer, on its ground, goes for first.
	bool IsPlayerBotOrnamentFarmerTarget(LPCHARACTER ch, LPCHARACTER victim)
	{
		return victim && victim->IsMonster() && IsPlayerBotOrnamentFarmerPrey(victim->GetRaceNum()) &&
				IsPlayerBotOrnamentFarmerOnGround(ch);
	}

	// ------------------------------------------------------------ the pass

	DWORD s_dwPlayerBotOrnamentFarmerFirstPass = 0;
	DWORD s_dwPlayerBotOrnamentFarmerNextPass = 0;
	DWORD s_dwPlayerBotOrnamentFarmerNextCensus = 0;

	bool IsPlayerBotOrnamentFarmerCandidate(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
			return false;
		if (IsPlayerBotPersonaEnabled() && !state.persona.bRestored)
			return false;
		if (ch->GetLevel() < PLAYERBOT_ORNAMENT_FARMER_MIN_LEVEL ||
				ch->GetLevel() > PLAYERBOT_EXP_LOCK_ORNAMENT_FARMER + PLAYERBOT_DROPPER_OUTGROWN_LEVELS)
			return false;
		if (state.bPersonality == BOT_PERSONALITY_MERCHANT || state.bBotRole == BOT_ROLE_PARTY_FIGHTER)
			return false;
		if (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty()))
			return false;
		// MT2009_PLUS_FARMER_LINK_V1: not a spot farmer, not a farmer's main.
		if (IsPlayerBotFarmerPID(ch->GetPlayerID()) || IsPlayerBotFarmerMainPID(ch->GetPlayerID()))
			return false;
		return IsPlayerBotProgressionEligible(ch, state);
	}

	void MakePlayerBotOrnamentFarmer(LPCHARACTER ch, TPlayerBotAIState& state, int count, bool flagged)
	{
		state.bPersonality = BOT_PERSONALITY_ORNAMENT_FARMER;
		state.persona.bDrawnPersonality = BOT_PERSONALITY_ORNAMENT_FARMER;
		state.bBotRole = BOT_ROLE_MOB_GRINDER;
		state.bAmbition = GetPlayerBotStableAmbition(ch, BOT_PERSONALITY_ORNAMENT_FARMER);
		state.dwMetinExpeditionUntil = 0;
		state.dwHubChosenTime = 0;
		ch->SetQuestFlag(PLAYERBOT_ORNAMENT_FARMER_FLAG, 1);
		sys_log(0, "PLAYERBOT_ORNAMENT: %s pid=%u name=%s empire=%u channel=%u level=%u map=%ld count=%d/%d",
				flagged ? "back" : "chosen", ch->GetPlayerID(), ch->GetName(), (unsigned)ch->GetEmpire(),
				(unsigned)g_bChannel, (unsigned)ch->GetLevel(), ch->GetMapIndex(), count,
				PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM);
	}

	void ReleasePlayerBotOrnamentFarmer(LPCHARACTER ch, TPlayerBotAIState& state, const char* why)
	{
		const BYTE drawn = GetPlayerBotStablePersonality(ch, state.bBotRole);
		state.persona.bDrawnPersonality = drawn;
		state.bPersonality = IsPlayerBotPersonaEnabled() ? GetPlayerBotCharakter(drawn) : drawn;
		state.bAmbition = GetPlayerBotStableAmbition(ch, state.bPersonality);
		ch->SetQuestFlag(PLAYERBOT_ORNAMENT_FARMER_FLAG, 0);
		sys_log(0, "PLAYERBOT_ORNAMENT: released pid=%u name=%s empire=%u level=%u why=%s",
				ch->GetPlayerID(), ch->GetName(), (unsigned)ch->GetEmpire(), (unsigned)ch->GetLevel(), why);
	}

	void ManagePlayerBotOrnamentFarmers(DWORD dwNow)
	{
		if (s_dwPlayerBotOrnamentFarmerNextPass != 0 && (int)(dwNow - s_dwPlayerBotOrnamentFarmerNextPass) < 0)
			return;
		s_dwPlayerBotOrnamentFarmerNextPass = dwNow + PLAYERBOT_ORNAMENT_FARMER_PASS_MS;
		if (s_dwPlayerBotOrnamentFarmerFirstPass == 0)
			s_dwPlayerBotOrnamentFarmerFirstPass = dwNow;
		const bool settled = dwNow - s_dwPlayerBotOrnamentFarmerFirstPass >= PLAYERBOT_ORNAMENT_FARMER_SETTLE_MS;
		// MT2009_PLUS_ORNAMENT_FARMERS_V3: farmers are made on the shop channel
		// only. A farmer is a counter keeper, and every counter stands on the
		// first channel (playerbot_channel_rules.h): the six identities the
		// second channel called on the test world (8 October) went to the
		// first to open their stands, or were taken back by the level-30
		// dropper pass, and the second channel was left short and calling
		// again. Two a kingdom for the world, then.
		const bool shopChannel = (int)g_bChannel == playerbot_channel_rules::SHOP_CHANNEL;

		// A kingdom whose second village is on this core, or nobody of it is
		// one here.
		bool hosted[4] = { false, false, false, false };
		for (BYTE empire = 1; empire <= 3; ++empire)
			hosted[empire] = IsPlayerBotMapHostedHere(GetPlayerBotOrnamentFarmerMap(empire));

		int count[4] = { 0, 0, 0, 0 };
		int atWork[4] = { 0, 0, 0, 0 };
		int onGround[4] = { 0, 0, 0, 0 };
		int ornaments[4] = { 0, 0, 0, 0 };
		int pool[4] = { 0, 0, 0, 0 };
		// (flagged or called 0 / at its working level 1 / under it 2 - and the
		// higher level first within it, hash), pid.
		std::vector<std::pair<std::pair<int, DWORD>, DWORD> > candidates[4];
		int called[4] = { 0, 0, 0, 0 };	// called identities waiting to be candidates
		for (TPlayerBotAIStateMap::iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsPC())
				continue;
			TPlayerBotAIState& state = it->second;
			const BYTE empire = ch->GetEmpire();
			if (state.bPersonality == BOT_PERSONALITY_ORNAMENT_FARMER)
			{
				if (empire < 1 || empire > 3 || IsPlayerBotPastDropperBand(ch, BOT_PERSONALITY_ORNAMENT_FARMER))
					ReleasePlayerBotOrnamentFarmer(ch, state, "past_band");
				else if (!hosted[empire])
					ReleasePlayerBotOrnamentFarmer(ch, state, "ground_not_here");
				else if (count[empire] >= PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM)
					ReleasePlayerBotOrnamentFarmer(ch, state, "over_count");
				else
				{
					++count[empire];
					if (IsPlayerBotOrnamentFarmerAtWork(ch))
						++atWork[empire];
					if (IsPlayerBotOrnamentFarmerOnGround(ch))
						++onGround[empire];
					if (ch->IsItemLoaded())
						ornaments[empire] += (int)ch->CountSpecifyItem(PLAYERBOT_ORNAMENT_VNUM);
				}
				continue;
			}
			const bool summoned = IsPlayerBotOrnamentFarmerSummoned(it->first, dwNow);
			if (!shopChannel || empire < 1 || empire > 3 || !hosted[empire] ||
					!IsPlayerBotOrnamentFarmerCandidate(ch, state))
				continue;
			++pool[empire];
			const bool flagged = ch->GetQuestFlag(PLAYERBOT_ORNAMENT_FARMER_FLAG) != 0 || summoned;
			if (!flagged && !settled)
				continue;
			candidates[empire].push_back(std::make_pair(std::make_pair((flagged ? 0 :
					(ch->GetLevel() >= PLAYERBOT_ORNAMENT_FARMER_WORK_LEVEL ? 1 : 2)) * 1000 + (255 - (int)ch->GetLevel()),
					PlayerBotNavHash(it->first ^ PLAYERBOT_ORNAMENT_FARMER_SEED ^ ((DWORD)g_bChannel << 24) ^
						((DWORD)empire * 0x85ebca6bU))), it->first));
		}
		// The identities called and not made farmers yet (on their way into
		// the world, or their persona not read): no second call for them.
		for (std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotOrnamentFarmerSummoned.begin();
				it != s_mapPlayerBotOrnamentFarmerSummoned.end(); ++it)
		{
			const BYTE e = CPlayerBotManager::instance().GetRegisteredEmpire(it->first);
			if (e >= 1 && e <= 3 && dwNow - it->second < PLAYERBOT_ORNAMENT_FARMER_SUMMON_HOLD_MS)
				++called[e];
		}
		for (BYTE empire = 1; empire <= 3; ++empire)
		{
			std::sort(candidates[empire].begin(), candidates[empire].end());
			for (size_t i = 0; i < candidates[empire].size() && count[empire] < PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM; ++i)
			{
				const DWORD pid = candidates[empire][i].second;
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
				TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pid);
				if (!ch || st == s_mapPlayerBotAIStates.end())
					continue;
				++count[empire];
				MakePlayerBotOrnamentFarmer(ch, st->second, count[empire], candidates[empire][i].first.first < 1000);
				if (s_mapPlayerBotOrnamentFarmerSummoned.erase(pid) && called[empire] > 0)
					--called[empire];
			}
			// MT2009_PLUS_ORNAMENT_FARMERS_V2: still short and nobody of the band
			// in play - identities of the band from the registry, the highest
			// first; they become candidates once their persona is read.
			const int missing = PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM - count[empire] - called[empire];
			if (shopChannel && settled && hosted[empire] && missing > 0 &&
					(s_adwPlayerBotOrnamentFarmerSummonAt[empire] == 0 ||
					 dwNow - s_adwPlayerBotOrnamentFarmerSummonAt[empire] >= PLAYERBOT_ORNAMENT_FARMER_SUMMON_MS))
			{
				s_adwPlayerBotOrnamentFarmerSummonAt[empire] = dwNow;
				std::vector<DWORD> pids;
				CPlayerBotManager::instance().CollectIdleRegisteredBots(empire, PLAYERBOT_ORNAMENT_FARMER_MIN_LEVEL,
						PLAYERBOT_EXP_LOCK_ORNAMENT_FARMER, pids, (size_t)missing);
				const size_t scheduled = pids.empty() ? 0 : CPlayerBotManager::instance().ScheduleExtraBots(pids);
				for (size_t p = 0; p < pids.size(); ++p)
					s_mapPlayerBotOrnamentFarmerSummoned[pids[p]] = dwNow ? dwNow : 1;
				s_aiPlayerBotOrnamentFarmerSummoned[empire] += (int)scheduled;
				sys_log(0, "PLAYERBOT_ORNAMENT: called from the registry channel=%u empire=%u missing=%d found=%u scheduled=%u",
						(unsigned)g_bChannel, (unsigned)empire, missing, (unsigned)pids.size(), (unsigned)scheduled);
			}
		}
		for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotOrnamentFarmerSummoned.begin();
				it != s_mapPlayerBotOrnamentFarmerSummoned.end(); )
		{
			if (dwNow - it->second >= PLAYERBOT_ORNAMENT_FARMER_SUMMON_HOLD_MS)
				s_mapPlayerBotOrnamentFarmerSummoned.erase(it++);
			else
				++it;
		}
		if (s_dwPlayerBotOrnamentFarmerNextCensus == 0 || (int)(dwNow - s_dwPlayerBotOrnamentFarmerNextCensus) >= 0)
		{
			s_dwPlayerBotOrnamentFarmerNextCensus = dwNow + PLAYERBOT_ORNAMENT_FARMER_CENSUS_MS;
			sys_log(0, "PLAYERBOT_ORNAMENT: census channel=%u farmers=%d/%d/%d at_work=%d/%d/%d on_ground=%d/%d/%d ornaments_in_bags=%d/%d/%d pool=%d/%d/%d called=%d/%d/%d target=%d",
					(unsigned)g_bChannel, count[1], count[2], count[3], atWork[1], atWork[2], atWork[3],
					onGround[1], onGround[2], onGround[3], ornaments[1], ornaments[2], ornaments[3],
					pool[1], pool[2], pool[3], s_aiPlayerBotOrnamentFarmerSummoned[1],
					s_aiPlayerBotOrnamentFarmerSummoned[2], s_aiPlayerBotOrnamentFarmerSummoned[3],
					PLAYERBOT_ORNAMENT_FARMERS_PER_KINGDOM);
			for (int e = 0; e < 4; ++e)
				s_aiPlayerBotOrnamentFarmerSummoned[e] = 0;
		}
	}
}

#endif
