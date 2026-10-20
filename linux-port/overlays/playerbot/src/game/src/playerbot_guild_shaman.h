#ifndef __INC_METIN2_PLAYERBOT_GUILD_SHAMAN_H__
#define __INC_METIN2_PLAYERBOT_GUILD_SHAMAN_H__

// MT2009_PLUS_BOT_GUILD_SHAMAN_V1 - a guild's Shaman goes along.
//
// The owner, 10 October: "Bot idacy expic na mocna mape (Lochy Pajakow,
// Hwang, Sohan, Lasy, Doyyumhwaji, Groty) bierze ze soba wolnego szamana ze
// swojej gildii i expia razem w druzynie" - and, the same day, the Temple of
// Ochao and the Enchanted Forest (the Las) on the list too, and not every
// bot: only one that does not manage there without the buffs. A strong bot
// hunts alone as before.
//
// Who needs one (WhyPlayerBotWantsShaman, logged as "shaman wanted
// reason=..." or "shaman not needed"): its history on that map over the
// last hours (NotePlayerBotStrongMapHardship - the deaths, the tactical
// retreats and the red potions drunk there, kept per map and halved every
// PLAYERBOT_SHAMAN_WANT_WINDOW_MS), its health against the bots of its class
// and level ("hp"), and its strength - the guilds' census of gear and level
// - against theirs ("gear").
//
// A bot that has just come onto one of those maps for its experience (the
// planner's trip: "level_to_", "m1_direct_to_", the desert gate into V1 -
// NotePlayerBotExpTrip, called by TransitionPlayerBotMap), or that has just
// crossed the deaths' or the retreats' line there, and needs one, looks for
// a Shaman of its guild who is free: a bot
// of the leader's level give or take PLAYERBOT_SHAMAN_ESCORT_LEVEL_DELTA, in
// no party at all, and free by the dungeon finder's own measure
// (GetPlayerBotLfgRefusal - no person it serves, no companion, no mercenary,
// no Arezzo or Ochao cohort, no raid, war, duel, counter, rod or pickaxe, no
// dropper), not in town on its errands, with its potions. The Shaman is
// brought to the leader (the raid's way of bringing a member, a map change),
// the two make a party and hunt as one - but in the Temple of Ochao and the
// Las nobody is brought: their ways in and out are their own (Ochao's
// Guardian and test group, the Las an expedition left at most every two
// hours), so there the Shaman is one already on the map, within a short walk
// (PLAYERBOT_SHAMAN_ESCORT_SAME_MAP_WALK), and both stay under their map's
// rules - the pair only hunts as a party; any arrival there counts as a
// trip. The follower's walk to its leader
// and the Shaman's party buffs and heals are every bot party's
// (ManagePlayerBotWandering, ManagePlayerBotCombatBuffs).
//
// The pair is kept out of the party pass's cohort and rotation
// (KeepPlayerBotShamanDuo) for PLAYERBOT_SHAMAN_ESCORT_MIN_MS to _MAX_MS -
// until then only its own end ends it: one of them gone or on another map
// (a map change leaves a bot party), the party broken, or a person in it,
// whose party it then is under the party rules as ever. A person's party,
// the Arezzo maps and a companion are never touched: none of them is free.
//
// An implementation fragment: include it once, after playerbot_guild_lfg.h
// (it asks the dungeon finder's refusal, the meetings and the companions).

namespace
{
	const int PLAYERBOT_SHAMAN_ESCORT_LEVEL_DELTA = 4;
	const DWORD PLAYERBOT_SHAMAN_ESCORT_SETTLE_MS = 3000;
	const DWORD PLAYERBOT_SHAMAN_ESCORT_PENDING_MS = 60000;
	const DWORD PLAYERBOT_SHAMAN_ESCORT_MIN_MS = 40 * 60 * 1000;
	const DWORD PLAYERBOT_SHAMAN_ESCORT_MAX_MS = 70 * 60 * 1000;
	const size_t PLAYERBOT_SHAMAN_ESCORT_MAX_DUOS = 60;
	const size_t PLAYERBOT_SHAMAN_ESCORT_MIN_RED_POTIONS = 20;
	const size_t PLAYERBOT_SHAMAN_ESCORT_MIN_BLUE_POTIONS = 10;
	const DWORD PLAYERBOT_SHAMAN_ESCORT_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_SHAMAN_ESCORT_SAME_MAP_WALK = 4000;
	// Who needs one: on the map, within the window (halved at its end), this
	// many deaths, or retreats, or this many red potions an hour over at
	// least PRESENCE_MIN of hunting there; or a maximum health under HP_PERCENT
	// of the bots of its class within PEER_LEVELS levels (PEERS of them at
	// least), or a strength under GEAR_PERCENT of theirs.
	const DWORD PLAYERBOT_SHAMAN_WANT_WINDOW_MS = 6 * 60 * 60 * 1000;
	const int PLAYERBOT_SHAMAN_WANT_DEATHS = 2;
	const int PLAYERBOT_SHAMAN_WANT_RETREATS = 4;
	const int PLAYERBOT_SHAMAN_WANT_POTIONS_PER_HOUR = 60;
	const DWORD PLAYERBOT_SHAMAN_WANT_PRESENCE_MIN_MS = 20 * 60 * 1000;
	const int PLAYERBOT_SHAMAN_WANT_HP_PERCENT = 80;
	const int PLAYERBOT_SHAMAN_WANT_GEAR_PERCENT = 75;
	const int PLAYERBOT_SHAMAN_WANT_PEER_LEVELS = 2;
	const int PLAYERBOT_SHAMAN_WANT_PEERS = 5;
	const DWORD PLAYERBOT_SHAMAN_ESCORT_RETRY_MS = 10 * 60 * 1000;

	// How long a brought Shaman may be on another map (its warp and loading).
	const DWORD PLAYERBOT_SHAMAN_DUO_ARRIVE_MS = 3 * 60 * 1000;
	// How long a duo stays while one of them is in town for its services.
	const DWORD PLAYERBOT_SHAMAN_DUO_SERVICES_MS = 12 * 60 * 1000;
	struct TPlayerBotShamanDuo
	{
		DWORD leader;
		DWORD shaman;
		long map;
		DWORD since;
		DWORD until;
		DWORD lastTogether;	// the last check that found them on one map
	};
	// By the leader's pid; the Shaman's pid leads to its leader.
	std::map<DWORD, TPlayerBotShamanDuo> s_mapPlayerBotShamanDuos;
	std::map<DWORD, DWORD> s_mapPlayerBotShamanDuoOf;
	// A leader's trip waiting for its look: the map and when it came.
	std::map<DWORD, std::pair<long, DWORD> > s_mapPlayerBotShamanEscortPending;
	unsigned int s_uPlayerBotShamanDuosFormed = 0;
	unsigned int s_uPlayerBotShamanDuosNone = 0;
	DWORD s_dwPlayerBotShamanEscortCensusAt = 0;

	bool IsPlayerBotShamanEscortMap(long map)
	{
		switch (map)
		{
			case PLAYERBOT_MAP_SPIDER_V1: case PLAYERBOT_MAP_SPIDER_V2:
			case PLAYERBOT_MAP_HWANG: case PLAYERBOT_MAP_SOHAN:
			case PLAYERBOT_MAP_FOREST: case PLAYERBOT_MAP_RED_FOREST:
			case PLAYERBOT_MAP_FIRE_LAND:
			case PLAYERBOT_MAP_GROTTO_V1: case PLAYERBOT_MAP_GROTTO_V2:
			case PLAYERBOT_MAP_OCHAO: case PLAYERBOT_MAP_AREZZO_FOREST:
				return true;
			default:
				return false;
		}
	}

	// The two whose ways are their own: the Shaman is one already there.
	bool IsPlayerBotShamanSameMapOnly(long map)
	{
		return map == PLAYERBOT_MAP_OCHAO || map == PLAYERBOT_MAP_AREZZO_FOREST;
	}

	// ------------------------------------------------- who needs a Shaman

	struct TPlayerBotStrongMapHardship
	{
		int deaths;
		int retreats;
		int potions;
		DWORD presenceMs;
		DWORD windowStart;
		DWORD lastTick;
		TPlayerBotStrongMapHardship() : deaths(0), retreats(0), potions(0), presenceMs(0), windowStart(0), lastTick(0) {}
	};
	std::map<std::pair<DWORD, long>, TPlayerBotStrongMapHardship> s_mapPlayerBotStrongMapHardship;
	std::map<DWORD, DWORD> s_mapPlayerBotShamanEscortTriedAt;

	TPlayerBotStrongMapHardship& GetPlayerBotStrongMapHardship(DWORD pid, long map, DWORD dwNow)
	{
		TPlayerBotStrongMapHardship& h = s_mapPlayerBotStrongMapHardship[std::make_pair(pid, map)];
		if (h.windowStart == 0)
			h.windowStart = dwNow ? dwNow : 1;
		else if (dwNow - h.windowStart >= PLAYERBOT_SHAMAN_WANT_WINDOW_MS)
		{
			h.deaths /= 2;
			h.retreats /= 2;
			h.potions /= 2;
			h.presenceMs /= 2;
			h.windowStart = dwNow ? dwNow : 1;
		}
		return h;
	}

	// gear.h (a red potion drunk) and survival.h (a death, a tactical
	// retreat) report here; kind 0 a death, 1 a retreat, 2 a potion.
	void NotePlayerBotStrongMapHardship(LPCHARACTER ch, int kind)
	{
		if (!ch || !IsPlayerBotShamanEscortMap(ch->GetMapIndex()) || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			return;
		const DWORD dwNow = get_dword_time();
		TPlayerBotStrongMapHardship& h = GetPlayerBotStrongMapHardship(ch->GetPlayerID(), ch->GetMapIndex(), dwNow);
		if (kind == 0)
			++h.deaths;
		else if (kind == 1)
			++h.retreats;
		else
			++h.potions;
		// The line crossed in the middle of a visit: a look now, as on arrival
		// (after a death the bot is mostly back in town, and the next visit's
		// arrival asks again).
		if ((kind == 1 && h.retreats == PLAYERBOT_SHAMAN_WANT_RETREATS) ||
				(kind == 0 && h.deaths == PLAYERBOT_SHAMAN_WANT_DEATHS))
			s_mapPlayerBotShamanEscortPending[ch->GetPlayerID()] = std::make_pair(ch->GetMapIndex(), dwNow ? dwNow : 1);
	}

	// Why this bot does not manage on this map without a Shaman; NULL when it
	// does. `detail` gets the numbers for the line.
	const char* WhyPlayerBotWantsShaman(LPCHARACTER ch, long map, DWORD dwNow, char* detail, size_t detailSize)
	{
		const TPlayerBotStrongMapHardship& h = GetPlayerBotStrongMapHardship(ch->GetPlayerID(), map, dwNow);
		const int perHour = h.presenceMs >= PLAYERBOT_SHAMAN_WANT_PRESENCE_MIN_MS
				? (int)((long long)h.potions * 3600000LL / std::max<DWORD>(1, h.presenceMs)) : -1;
		// The bots of its class within a couple of levels, wherever they are.
		long long hpSum = 0, strengthSum = 0;
		int peers = 0, strengthPeers = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			if (it->first == ch->GetPlayerID())
				continue;
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || c->GetJob() != ch->GetJob() ||
					abs((int)c->GetLevel() - (int)ch->GetLevel()) > PLAYERBOT_SHAMAN_WANT_PEER_LEVELS || c->GetMaxHP() <= 0)
				continue;
			hpSum += c->GetMaxHP();
			++peers;
			const int strength = GetPlayerBotStrengthCached(it->first);
			if (strength > 0)
			{
				strengthSum += strength;
				++strengthPeers;
			}
		}
		const long long hpAverage = peers > 0 ? hpSum / peers : 0;
		const long long strengthAverage = strengthPeers > 0 ? strengthSum / strengthPeers : 0;
		const int strength = GetPlayerBotStrengthCached(ch->GetPlayerID());
		snprintf(detail, detailSize, "deaths=%d retreats=%d potions=%d presence_min=%u potions_h=%d hp=%d hp_avg=%lld peers=%d strength=%d strength_avg=%lld",
				h.deaths, h.retreats, h.potions, h.presenceMs / 60000U, perHour, ch->GetMaxHP(), hpAverage, peers,
				strength, strengthAverage);
		if (h.deaths >= PLAYERBOT_SHAMAN_WANT_DEATHS)
			return "deaths";
		if (h.retreats >= PLAYERBOT_SHAMAN_WANT_RETREATS)
			return "retreats";
		if (perHour >= PLAYERBOT_SHAMAN_WANT_POTIONS_PER_HOUR)
			return "potions";
		if (peers >= PLAYERBOT_SHAMAN_WANT_PEERS &&
				(long long)ch->GetMaxHP() * 100 < hpAverage * PLAYERBOT_SHAMAN_WANT_HP_PERCENT)
			return "hp";
		if (strengthPeers >= PLAYERBOT_SHAMAN_WANT_PEERS && strength > 0 &&
				(long long)strength * 100 < strengthAverage * PLAYERBOT_SHAMAN_WANT_GEAR_PERCENT)
			return "gear";
		return NULL;
	}

	bool IsPlayerBotExpTripReason(const char* reason)
	{
		return reason && (strncmp(reason, "level_to_", 9) == 0 || strncmp(reason, "m1_direct_to_", 13) == 0 ||
				strcmp(reason, "desert_gate_to_v1") == 0);
	}

	void NotePlayerBotExpTrip(LPCHARACTER ch, long targetMap, const char* reason, DWORD dwNow)
	{
		if (!ch || !IsPlayerBotShamanEscortMap(targetMap) ||
				(!IsPlayerBotExpTripReason(reason) && !IsPlayerBotShamanSameMapOnly(targetMap)) ||
				ch->GetJob() == JOB_SHAMAN || !ch->GetGuild())
			return;
		s_mapPlayerBotShamanEscortPending[ch->GetPlayerID()] = std::make_pair(targetMap, dwNow ? dwNow : 1);
	}

	bool IsPlayerBotDuoShaman(DWORD pid)
	{
		return s_mapPlayerBotShamanDuoOf.count(pid) != 0;
	}

	// Where a duo's Shaman goes back to: its leader, standing on the duo's
	// map (a leader away in town gives no spot - the Shaman waits).
	bool GetPlayerBotDuoShamanLeaderSpot(DWORD shamanPid, long& map, long& x, long& y)
	{
		std::map<DWORD, DWORD>::const_iterator of = s_mapPlayerBotShamanDuoOf.find(shamanPid);
		if (of == s_mapPlayerBotShamanDuoOf.end())
			return false;
		std::map<DWORD, TPlayerBotShamanDuo>::const_iterator it = s_mapPlayerBotShamanDuos.find(of->second);
		if (it == s_mapPlayerBotShamanDuos.end())
			return false;
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(it->second.leader);
		if (!leader || leader->GetMapIndex() != it->second.map || IsPlayerBotShamanSameMapOnly(it->second.map))
			return false;
		map = leader->GetMapIndex();
		x = leader->GetX();
		y = leader->GetY();
		return true;
	}

	bool IsPlayerBotShamanDuoMember(DWORD pid)
	{
		return s_mapPlayerBotShamanDuos.count(pid) != 0 || s_mapPlayerBotShamanDuoOf.count(pid) != 0;
	}

	void EndPlayerBotShamanDuo(DWORD leaderPid, const char* why)
	{
		std::map<DWORD, TPlayerBotShamanDuo>::iterator it = s_mapPlayerBotShamanDuos.find(leaderPid);
		if (it == s_mapPlayerBotShamanDuos.end())
			return;
		sys_log(0, "PLAYERBOT_GUILD_SHAMAN: duo over leader=%u shaman=%u map=%ld after_s=%u why=%s",
				it->second.leader, it->second.shaman, it->second.map,
				(get_dword_time() - it->second.since) / 1000U, why);
		s_mapPlayerBotShamanDuoOf.erase(it->second.shaman);
		s_mapPlayerBotShamanDuos.erase(it);
	}

	// The party pass's question for either of the pair: true while the duo
	// stands and the pass is to leave its party alone.
	bool KeepPlayerBotShamanDuo(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return false;
		DWORD leaderPid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::const_iterator of = s_mapPlayerBotShamanDuoOf.find(leaderPid);
		if (of != s_mapPlayerBotShamanDuoOf.end())
			leaderPid = of->second;
		std::map<DWORD, TPlayerBotShamanDuo>::const_iterator it = s_mapPlayerBotShamanDuos.find(leaderPid);
		if (it == s_mapPlayerBotShamanDuos.end())
			return false;
		const TPlayerBotShamanDuo duo = it->second;
		LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(duo.leader);
		LPCHARACTER shaman = CHARACTER_MANAGER::instance().FindByPID(duo.shaman);
		const char* why = NULL;
		if (!leader || !shaman)
			why = "gone";
		else if (dwNow >= duo.until)
			why = "time";
		// MT2009_PLUS_BOT_GUILD_SHAMAN_V1 (night test 10 October: 30 of 32 duos
		// ended 2-13 s after forming, "maps_apart" - the brought Shaman was still
		// on its way): the first minutes of a duo give the Shaman's warp its time.
		else if (leader->GetMapIndex() != shaman->GetMapIndex())
		{
			if (dwNow - duo.since < PLAYERBOT_SHAMAN_DUO_ARRIVE_MS)
				return true;	// still on its way - no party check either
			// MT2009_PLUS_BOT_GUILD_SHAMAN_V2: either of them in a village (the
			// town's services) keeps the duo for a while - the Shaman comes back
			// (TransitionPlayerBotMap's "guild_shaman_return").
			if ((IsPlayerBotVillageMap(shaman->GetMapIndex()) || IsPlayerBotVillageMap(leader->GetMapIndex())) &&
					dwNow - duo.lastTogether < PLAYERBOT_SHAMAN_DUO_SERVICES_MS)
				return true;
			why = "maps_apart";
		}
		else if (!leader->GetParty() || leader->GetParty() != shaman->GetParty())
		{
			// MT2009_PLUS_BOT_GUILD_SHAMAN_V2 (10 October: 38 of 50 duos ended
			// "party_broken" - the party was made while the Shaman was still on
			// its warp, and the warp left it out): on one map, with neither of
			// them in somebody else's party, the pair's party is made again.
			LPPARTY lp = leader->GetParty();
			LPPARTY sp = shaman->GetParty();
			if ((sp && sp != lp) || (lp && lp->GetLeaderPID() != leader->GetPlayerID() && !sp))
				why = "party_broken";
			else
			{
				if (!lp)
				{
					lp = CPartyManager::instance().CreateParty(leader);
					if (lp)
						lp->Link(leader);
				}
				if (lp && !sp && lp->GetMemberCount() < PARTY_MAX_MEMBER)
				{
					lp->Join(shaman->GetPlayerID());
					lp->Link(shaman);
				}
				if (!lp || shaman->GetParty() != lp)
					why = "party_broken";
				else
					sys_log(0, "PLAYERBOT_GUILD_SHAMAN: duo party mended leader=%u shaman=%u", duo.leader, duo.shaman);
			}
		}
		else if (IsPlayerBotHumanLedParty(leader->GetParty()) || IsPlayerBotPartyWithHuman(leader->GetParty()))
			why = "person";
		if (why)
		{
			EndPlayerBotShamanDuo(duo.leader, why);
			return false;
		}
		s_mapPlayerBotShamanDuos[duo.leader].lastTogether = dwNow;	// MT2009_PLUS_BOT_GUILD_SHAMAN_V2
		if (leader->GetParty()->GetExpDistributionMode() != PARTY_EXP_DISTRIBUTION_PARITY)
			leader->GetParty()->SetParameter(PARTY_EXP_DISTRIBUTION_PARITY);
		return true;
	}

	// Why this Shaman is not free for the trip; NULL when it is.
	const char* GetPlayerBotShamanEscortRefusal(LPCHARACTER leader, LPCHARACTER c, const TPlayerBotAIState& st,
			long map, DWORD dwNow)
	{
		if (c == leader || c->GetJob() != JOB_SHAMAN || c->GetGuild() != leader->GetGuild())
			return "not_ours";
		if (abs((int)c->GetLevel() - (int)leader->GetLevel()) > PLAYERBOT_SHAMAN_ESCORT_LEVEL_DELTA)
			return "level";
		if (c->GetSkillGroup() == 0)
			return "no_skills";
		if (c->GetParty())
			return "party";
		const DWORD pid = c->GetPlayerID();
		if (IsPlayerBotShamanDuoMember(pid) || IsPlayerBotSidekickOwnerPID(pid) || IsPlayerBotSidekickLeashed(c))
			return "company";
		// In the temple and the Las: one already there, near, under the map's
		// own rules - its cohort and its map are no refusal there.
		const bool sameMapOnly = IsPlayerBotShamanSameMapOnly(map);
		if (sameMapOnly)
		{
			if (c->GetMapIndex() != map)
				return "not_on_map";
			const int walk = map == PLAYERBOT_MAP_OCHAO ? GetPlayerBotOchaoWalk(c, leader->GetX(), leader->GetY())
					: GetPlayerBotArezzoWalk(c, leader->GetX(), leader->GetY());
			if (walk > PLAYERBOT_SHAMAN_ESCORT_SAME_MAP_WALK)
				return "walk";
			if ((map == PLAYERBOT_MAP_OCHAO && IsPlayerBotOchaoLeaving(c)) ||
					(map == PLAYERBOT_MAP_AREZZO_FOREST && IsPlayerBotArezzoLeaving(c)))
				return "leaving";
		}
		const char* lfg = GetPlayerBotLfgRefusal(c, st, dwNow);
		if (lfg && !(sameMapOnly && (strcmp(lfg, "cohort") == 0 || strcmp(lfg, "far_map") == 0)))
			return lfg;
		if (IsPlayerBotOnDungeonRun(pid) || IsPlayerBotDungeonLfgHeld(pid) || IsPlayerBotGuildLfgHeld(pid) ||
				playerbot_bpbots::IsOnErrand(pid) || IsPlayerBotInMeetup(pid) || IsPlayerBotOnAnyHorseTrial(c))
			return "errand";
		if (st.bTownVisitPhase != BOT_TOWN_PHASE_NONE || BlocksPlayerBotTravel(c))
			return "town";
		if (!sameMapOnly && (IsPlayerBotArezzoMap(c->GetMapIndex()) || c->GetMapIndex() == PLAYERBOT_MAP_OCHAO ||
				IsPlayerBotMonkeyMap(c->GetMapIndex()) || c->GetMapIndex() == PLAYERBOT_MAP_DEMON_TOWER ||
				IsPlayerBotDemonTowerInstance(c->GetMapIndex())))
			return "far_map";
		if (IsPlayerBotPersonaEnabled() && st.persona.bRestored &&
				(st.persona.bBagFull || GetPlayerBotRareNow(st.persona, dwNow) != 0))
			return "persona";
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(c, red, blue);
		if (red < PLAYERBOT_SHAMAN_ESCORT_MIN_RED_POTIONS || blue < PLAYERBOT_SHAMAN_ESCORT_MIN_BLUE_POTIONS)
			return "potions";
		return NULL;
	}

	// The leader's look, a few seconds after it has come onto the map.
	void TryPlayerBotShamanEscort(LPCHARACTER ch, TPlayerBotAIState& state, long map, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		if (ch->GetMapIndex() != map || ch->IsDead() || !ch->GetGuild() || ch->GetJob() == JOB_SHAMAN)
			return;
		const char* leaderWhy = NULL;
		if (ch->GetParty())
			leaderWhy = "in_party";
		else if (IsPlayerBotShamanDuoMember(pid))
			leaderWhy = "duo";
		else if (IsPlayerBotSidekickPID(pid) || IsPlayerBotSidekickOwnerPID(pid) || IsPlayerBotSidekickLeashed(ch) ||
				IsPlayerBotOnMercContract(pid) || IsPlayerBotHeldForCompany(ch) || IsPlayerBotSummoned(pid))
			leaderWhy = "company";
		else if ((IsPlayerBotArezzoBound(ch) && !IsPlayerBotShamanSameMapOnly(map)) || state.wBossRaidRace != 0 ||
				IsPlayerBotInDungeonBusiness(ch, state) || IsPlayerBotOnDungeonRun(pid))
			leaderWhy = "busy";
		else if ((map == PLAYERBOT_MAP_OCHAO && IsPlayerBotOchaoLeaving(ch)) ||
				(map == PLAYERBOT_MAP_AREZZO_FOREST && IsPlayerBotArezzoLeaving(ch)))
			leaderWhy = "leaving";
		else if (s_mapPlayerBotShamanDuos.size() >= PLAYERBOT_SHAMAN_ESCORT_MAX_DUOS)
			leaderWhy = "cap";
		if (leaderWhy)
		{
			sys_log(0, "PLAYERBOT_GUILD_SHAMAN: no escort leader=%u name=%s map=%ld why=%s",
					pid, ch->GetName(), map, leaderWhy);
			return;
		}
		// The owner's rule: only a bot that does not manage there alone.
		char detail[256];
		const char* need = WhyPlayerBotWantsShaman(ch, map, dwNow, detail, sizeof(detail));
		if (!need)
		{
			sys_log(0, "PLAYERBOT_GUILD_SHAMAN: shaman not needed leader=%u name=%s level=%u job=%u map=%ld %s",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetJob(), map, detail);
			return;
		}
		sys_log(0, "PLAYERBOT_GUILD_SHAMAN: shaman wanted reason=%s leader=%u name=%s level=%u job=%u map=%ld %s",
				need, pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetJob(), map, detail);
		std::map<DWORD, DWORD>::const_iterator tried = s_mapPlayerBotShamanEscortTriedAt.find(pid);
		if (tried != s_mapPlayerBotShamanEscortTriedAt.end() && dwNow - tried->second < PLAYERBOT_SHAMAN_ESCORT_RETRY_MS)
			return;
		s_mapPlayerBotShamanEscortTriedAt[pid] = dwNow ? dwNow : 1;
		// The nearest in level of the guild's free Shamans; the reasons the
		// others were not, counted for the line.
		LPCHARACTER best = NULL;
		TPlayerBotAIState* bestState = NULL;
		int bestDelta = 0;
		std::map<std::string, int> why;
		for (TPlayerBotAIStateMap::iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || c->GetJob() != JOB_SHAMAN || c->GetGuild() != ch->GetGuild() || c == ch)
				continue;
			const char* w = GetPlayerBotShamanEscortRefusal(ch, c, it->second, map, dwNow);
			if (w)
			{
				++why[w];
				continue;
			}
			const int delta = abs((int)c->GetLevel() - (int)ch->GetLevel());
			if (!best || delta < bestDelta)
			{
				best = c;
				bestState = &it->second;
				bestDelta = delta;
			}
		}
		if (!best)
		{
			++s_uPlayerBotShamanDuosNone;
			std::string list;
			for (std::map<std::string, int>::const_iterator w = why.begin(); w != why.end(); ++w)
			{
				char one[48];
				snprintf(one, sizeof(one), " %s=%d", w->first.c_str(), w->second);
				list += one;
			}
			sys_log(0, "PLAYERBOT_GUILD_SHAMAN: no free shaman leader=%u name=%s level=%u guild=%u map=%ld%s",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetGuild()->GetID(), map,
					list.c_str());
			return;
		}
		// Brought beside the leader, on its ground - but in the temple and the
		// Las it is there already and walks to its leader as a party member.
		const long fromMap = best->GetMapIndex();
		const bool bring = !IsPlayerBotShamanSameMapOnly(map);
		long x = ch->GetX(), y = ch->GetY();
		long openX = 0, openY = 0;
		const int angle = (int)(PlayerBotNavHash(best->GetPlayerID() ^ 0x53484d4eU) % 360U);
		float fx = 0.0f, fy = 0.0f;
		GetDeltaByDegree((float)angle, 300.0f, &fx, &fy);
		if (bring && FindPlayerBotWarGround(map, x + (long)fx, y + (long)fy, 400, openX, openY))
		{
			CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(map);
			if (!navigation.Init(map) ||
					navigation.GetComponentAtWorld(openX, openY, 4) == navigation.GetComponentAtWorld(x, y))
			{
				x = openX;
				y = openY;
			}
		}
		if (bring && !TransitionPlayerBotMap(best, *bestState, map, x, y, dwNow, "guild_shaman_escort"))
		{
			sys_log(0, "PLAYERBOT_GUILD_SHAMAN: escort move failed leader=%u shaman=%u name=%s from=%ld to=%ld",
					pid, best->GetPlayerID(), best->GetName(), fromMap, map);
			return;
		}
		LPPARTY party = CPartyManager::instance().CreateParty(ch);
		if (!party)
			return;
		party->Link(ch);
		party->SetParameter(PARTY_EXP_DISTRIBUTION_PARITY);
		party->Join(best->GetPlayerID());
		party->Link(best);
		if (best->GetParty() != party)
		{
			sys_log(0, "PLAYERBOT_GUILD_SHAMAN: party refused leader=%u shaman=%u", pid, best->GetPlayerID());
			return;
		}
		state.dwPartyExpireTime = 0;
		bestState->dwPartyExpireTime = 0;
		TPlayerBotShamanDuo duo;
		duo.leader = pid;
		duo.shaman = best->GetPlayerID();
		duo.map = map;
		duo.since = dwNow;
		duo.lastTogether = dwNow;
		duo.until = dwNow + PLAYERBOT_SHAMAN_ESCORT_MIN_MS +
				PlayerBotNavHash(pid ^ best->GetPlayerID() ^ 0x44554f53U) %
				(PLAYERBOT_SHAMAN_ESCORT_MAX_MS - PLAYERBOT_SHAMAN_ESCORT_MIN_MS);
		s_mapPlayerBotShamanDuos[pid] = duo;
		s_mapPlayerBotShamanDuoOf[duo.shaman] = pid;
		++s_uPlayerBotShamanDuosFormed;
		RememberPlayerBotEncounter(ch, best, PLAYERBOT_FRIEND_PARTY_POINTS, dwNow);
		const char* where = GetPlayerBotMapDestinationPl(map);
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "Ide expic %s, %s idzie ze mna jako szaman.", where && *where ? where : "",
				best->GetName());
		ch->GetGuild()->Chat(msg);
		sys_log(0, "PLAYERBOT_GUILD_SHAMAN: duo formed reason=%s leader=%u name=%s level=%u shaman=%u shaman_name=%s shaman_level=%u guild=%u map=%ld from=%ld brought=%d minutes=%u",
				need, pid, ch->GetName(), (unsigned int)ch->GetLevel(), best->GetPlayerID(), best->GetName(),
				(unsigned int)best->GetLevel(), (unsigned int)ch->GetGuild()->GetID(), map, fromMap, bring ? 1 : 0,
				(duo.until - dwNow) / 60000U);
	}

	// The per-bot hook, before the party pass: a pending trip's look, and the
	// census every ten minutes.
	void ManagePlayerBotShamanEscort(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_dwPlayerBotShamanEscortCensusAt == 0 || dwNow - s_dwPlayerBotShamanEscortCensusAt >= PLAYERBOT_SHAMAN_ESCORT_CENSUS_MS)
		{
			s_dwPlayerBotShamanEscortCensusAt = dwNow ? dwNow : 1;
			sys_log(0, "PLAYERBOT_GUILD_SHAMAN: census duos=%u formed=%u no_shaman=%u pending=%u",
					(unsigned int)s_mapPlayerBotShamanDuos.size(), s_uPlayerBotShamanDuosFormed,
					s_uPlayerBotShamanDuosNone, (unsigned int)s_mapPlayerBotShamanEscortPending.size());
		}
		if (!ch)
			return;
		// The time hunted on a strong map, for the potions an hour.
		if (IsPlayerBotShamanEscortMap(ch->GetMapIndex()) && !ch->IsDead())
		{
			TPlayerBotStrongMapHardship& h = GetPlayerBotStrongMapHardship(ch->GetPlayerID(), ch->GetMapIndex(), dwNow);
			if (h.lastTick != 0 && dwNow - h.lastTick < 10000)
				h.presenceMs += dwNow - h.lastTick;
			h.lastTick = dwNow ? dwNow : 1;
		}
		std::map<DWORD, std::pair<long, DWORD> >::iterator it = s_mapPlayerBotShamanEscortPending.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotShamanEscortPending.end())
			return;
		const long map = it->second.first;
		const DWORD at = it->second.second;
		if (dwNow - at < PLAYERBOT_SHAMAN_ESCORT_SETTLE_MS)
			return;
		s_mapPlayerBotShamanEscortPending.erase(it);
		if (dwNow - at > PLAYERBOT_SHAMAN_ESCORT_PENDING_MS)
			return;
		TryPlayerBotShamanEscort(ch, state, map, dwNow);
	}
}

#endif
