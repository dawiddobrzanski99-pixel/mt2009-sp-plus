#ifndef __INC_METIN2_PLAYERBOT_MEETUPS_H__
#define __INC_METIN2_PLAYERBOT_MEETUPS_H__

// MT2009_PLUS_BOT_MEETUPS_V1 - two bots arrange a trade on the chat, meet and
// trade in the exchange window.
//
// The owner, 9 October: "Spotkania i wymiany: boty umawiaja sie na czacie na
// kanal, mape i miejsce, przychodza tam i wymieniaja sie w oknie handlu -
// miedzy soba i z graczami". A person's side is the deal of
// playerbot_chat_deals.h (the whisper, the price, the place, the window);
// this file is the bots' side, between themselves:
//
//   - the plan (ManagePlayerBotMeetups, once for the core every
//     PLAYERBOT_MEETUP_GAP_*): a bot short of a material or of a Biologist's
//     specimen (CollectPlayerBotWantedMaterials, GetPlayerBotBiologistPurchaseNeed)
//     and a bot of its kingdom with that piece spare in its bag (over its own
//     reserves); a price from the market's memory (GetPlayerBotDealFairPrice)
//     the buyer can pay out of 60% of its purse; the place: the blacksmith
//     of the kingdom's first village on this channel (each its side of him,
//     GetPlayerBotDealSmithSpot);
//   - the talk, on the trade chat ('@'), as people write it: the buyer's
//     "K> ...", the seller's answer with the price, the channel, the village
//     and the spot, and the buyer's "ok, ide";
//   - the meeting (HandlePlayerBotMeetup, each bot's tick): over to the
//     village (TransitionPlayerBotMap), the walk to the smith, the wait off the
//     horse; when both stand there the seller opens the window, puts the
//     pieces in, the buyer the yang, and both accept - a glance apart.
//
// The order of things (the owner's "jasna kolejnosc zajec", playerbot_priorities.h):
// staying alive comes first - a bot hurt or attacked fights and drinks, and
// the meeting waits; a raid with its party comes before the meeting - a bot
// a raid takes says so and the meeting is off; the meeting comes before a
// full bag and everything else - the tick is its while it goes and waits.
//
// An implementation fragment: include it once, after playerbot_chat_world.h;
// the manager calls ManagePlayerBotMeetups once a tick and HandlePlayerBotMeetup
// for each bot ahead of the deals.

namespace
{
	// MT2009_PLUS_BOT_PRIORITIES_V1 (playerbot_priorities.h, included later).
	bool IsPlayerBotSurvivalFirst(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow);
	bool IsPlayerBotBagFirst(LPCHARACTER ch, const TPlayerBotAIState& state);

	const DWORD PLAYERBOT_MEETUP_FIRST_DELAY_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_MEETUP_GAP_MIN_MS = 2 * 60 * 1000;	// night test 9 Oct: 2 meetings in 2 h - more often
	const DWORD PLAYERBOT_MEETUP_GAP_MAX_MS = 5 * 60 * 1000;
	const size_t PLAYERBOT_MEETUP_MAX_ACTIVE = 3;
	const int PLAYERBOT_MEETUP_BUYER_TRIES = 24;	// was 6: most draws found no bot short of anything
	const int PLAYERBOT_MEETUP_MIN_LEVEL = 20;
	const int PLAYERBOT_MEETUP_MIN_HP_PERCENT = 60;
	// The talk: the seller answers, then the buyer, a few seconds apart.
	const DWORD PLAYERBOT_MEETUP_REPLY_MIN_MS = 5000;
	const DWORD PLAYERBOT_MEETUP_REPLY_MAX_MS = 12000;
	// The whole meeting, the wait once one of them stands there, a try at a
	// map change, the walk to the spot, and the window.
	const DWORD PLAYERBOT_MEETUP_TTL_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_MEETUP_WAIT_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_MEETUP_RETRY_MS = 5000;
	const int PLAYERBOT_MEETUP_TRIES = 4;
	const DWORD PLAYERBOT_MEETUP_WALK_MAX_MS = 2 * 60 * 1000;
	const int PLAYERBOT_MEETUP_STAY = 300;
	const DWORD PLAYERBOT_MEETUP_STEP_MIN_MS = 900;
	const DWORD PLAYERBOT_MEETUP_STEP_MAX_MS = 2200;
	const DWORD PLAYERBOT_MEETUP_WINDOW_MAX_MS = 60 * 1000;

	enum EPlayerBotMeetupStage
	{
		MEETUP_TALK = 0,   // the chat lines are going out; both live on meanwhile
		MEETUP_GOING,      // both on their way to the spot, or waiting there
		MEETUP_WINDOW,     // the window is open
	};

	struct TPlayerBotMeetup
	{
		DWORD seller;
		DWORD buyer;
		DWORD vnum;
		int count;
		long long unit;
		long map;
		long sx, sy;       // the seller's place by the smith
		long bx, by;       // the buyer's, beside it
		BYTE stage;
		int talkStep;
		DWORD at;
		DWORD nextTalkAt;
		DWORD sellerArrived, buyerArrived;
		DWORD sellerWalk, buyerWalk;
		DWORD sellerNextTry, buyerNextTry;
		int sellerTries, buyerTries;
		DWORD windowAt;
		DWORD nextStepAt;
		int windowStep;
		std::string itemName;
		TPlayerBotMeetup() : seller(0), buyer(0), vnum(0), count(0), unit(0), map(0), sx(0), sy(0), bx(0), by(0),
			stage(MEETUP_TALK), talkStep(0), at(0), nextTalkAt(0), sellerArrived(0), buyerArrived(0), sellerWalk(0),
			buyerWalk(0), sellerNextTry(0), buyerNextTry(0), sellerTries(0), buyerTries(0), windowAt(0), nextStepAt(0),
			windowStep(0) {}
	};

	std::map<DWORD, TPlayerBotMeetup> s_mapPlayerBotMeetups;   // by id
	std::map<DWORD, DWORD> s_mapPlayerBotMeetupOf;             // pid -> id
	DWORD s_dwPlayerBotMeetupNextId = 1;
	DWORD s_dwPlayerBotMeetupNextPlan = 0;
	unsigned int s_uPlayerBotMeetupsDone = 0;
	unsigned int s_uPlayerBotMeetupsFailed = 0;

	TPlayerBotMeetup* FindPlayerBotMeetupOf(DWORD pid)
	{
		std::map<DWORD, DWORD>::const_iterator of = s_mapPlayerBotMeetupOf.find(pid);
		if (of == s_mapPlayerBotMeetupOf.end())
			return NULL;
		std::map<DWORD, TPlayerBotMeetup>::iterator it = s_mapPlayerBotMeetups.find(of->second);
		return it == s_mapPlayerBotMeetups.end() ? NULL : &it->second;
	}

	bool IsPlayerBotInMeetup(DWORD pid)
	{
		return s_mapPlayerBotMeetupOf.count(pid) != 0;
	}

	// Free for a meeting at all: alive and well, on an ordinary map of this
	// core, in nobody's company and on no business that outranks it.
	bool IsPlayerBotMeetupFree(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || ch->IsDead() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->IsItemLoaded() ||
				(int)ch->GetLevel() < PLAYERBOT_MEETUP_MIN_LEVEL || !IsPlayerBotPublicSpeaker(ch, PLAYERBOT_MEETUP_MIN_LEVEL))
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotInMeetup(pid) || IsPlayerBotDealMeeting(pid) || IsPlayerBotDropper(state.bPersonality))
			return false;
		if (ch->GetMyShop() || ch->GetExchange() || IsPlayerBotInDungeonBusiness(ch, state) ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || IsPlayerBotHeldForCompany(ch) ||
				IsPlayerBotArezzoHeld(ch) || IsPlayerBotOchaoForced(ch) || state.dwGuildWarEnemyGID != 0 || state.bWorldEventKind != 0 ||
				state.bVisitingShop || state.bFishingSession || state.bRecoveringAfterDeath || state.bTacticalRetreat ||
				state.bMultiPullActive)
			return false;
		if (ch->GetMaxHP() <= 0 || ch->GetHP() * 100 < ch->GetMaxHP() * PLAYERBOT_MEETUP_MIN_HP_PERCENT)
			return false;
		// A full bag goes to town before it is told of a meeting
		// (MT2009_PLUS_BOT_PRIORITIES_V1) - and has no room for the pieces.
		if (IsPlayerBotBagFirst(ch, state) || ch->GetEmptyInventory(2) < 0)
			return false;
		// Not down a Spider Dungeon, nor on the desert crossing to or from one:
		// the way out is a walk across the desert the meeting would hold up.
		const long map = ch->GetMapIndex();
		if (IsPlayerBotSpiderMap(map) || state.lDesertCrossingTo != 0)
			return false;
		return map < PLAYERBOT_INSTANCE_MAP_INDEX_MIN && (IsPlayerBotVillageMap(map) || IsPlayerBotFrontierMapIndex(map));
	}

	// The pieces of it the bot can spare: in the bag, not worn, over what
	// the Biologist and its own anvil still want from it.
	int GetPlayerBotMeetupSpare(LPCHARACTER ch, DWORD vnum)
	{
		const int have = CountPlayerBotDealBagPieces(ch, vnum, 0);
		if (have <= 0)
			return 0;
		return have - GetPlayerBotBiologistReserve(ch, vnum) - GetPlayerBotRefineMaterialReserve(ch, vnum);
	}

	// What the buyer is after, and how many it would take of each.
	void CollectPlayerBotMeetupWants(LPCHARACTER ch, std::map<DWORD, int>& out)
	{
		out.clear();
		std::set<DWORD> wanted;
		CollectPlayerBotWantedMaterials(ch, wanted);
		for (std::set<DWORD>::const_iterator it = wanted.begin(); it != wanted.end(); ++it)
		{
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(*it);
			if (proto && proto->bType != ITEM_SKILLBOOK)
				out[*it] = IS_SET(proto->dwFlags, ITEM_FLAG_STACKABLE) ? 10 : 1;
		}
		// The Biologist's specimens too (MT2009_PLUS_BOT_BIOLOGIST_EAGER_V1).
		for (size_t i = 0; i < PLAYERBOT_BIOLOGIST_MISSION_COUNT; ++i)
		{
			const DWORD vnum = PLAYERBOT_BIOLOGIST_MISSIONS[i].itemVnum;
			const int need = GetPlayerBotBiologistPurchaseNeed(ch, vnum);
			if (need > 0)
				out[vnum] = std::max(out[vnum], need);
		}
	}

	const char* GetPlayerBotMeetupVillageName(long map)
	{
		const char* tag = playerbot_conv::VillageTag(map);
		return tag && *tag ? tag : GetPlayerBotTownName(map);
	}

	void ForgetPlayerBotMeetup(DWORD id)
	{
		std::map<DWORD, TPlayerBotMeetup>::iterator it = s_mapPlayerBotMeetups.find(id);
		if (it == s_mapPlayerBotMeetups.end())
			return;
		s_mapPlayerBotMeetupOf.erase(it->second.seller);
		s_mapPlayerBotMeetupOf.erase(it->second.buyer);
		s_mapPlayerBotMeetups.erase(it);
	}

	// The meeting off, with a word from whoever calls it off (to the other,
	// by whisper - between two bots nobody else reads it, and the log does).
	void EndPlayerBotMeetup(TPlayerBotMeetup& m, bool done, const char* why, LPCHARACTER sayer = NULL, const char* line = NULL)
	{
		LPCHARACTER seller = CHARACTER_MANAGER::instance().FindByPID(m.seller);
		LPCHARACTER buyer = CHARACTER_MANAGER::instance().FindByPID(m.buyer);
		if (seller && seller->GetExchange())
			seller->GetExchange()->Cancel();
		else if (buyer && buyer->GetExchange())
			buyer->GetExchange()->Cancel();
		if (sayer && line && *line)
		{
			LPCHARACTER other = sayer == seller ? buyer : seller;
			if (other)
				SendPlayerBotWhisper(sayer, other, line);
		}
		if (done)
		{
			++s_uPlayerBotMeetupsDone;
			ClosePlayerBotPublicPost(m.buyer, m.vnum);
		}
		else
			++s_uPlayerBotMeetupsFailed;
		sys_log(0, "PLAYERBOT_MEETUP: %s why=%s seller=%u buyer=%u vnum=%u count=%d unit=%lld map=%ld age_s=%u done=%u failed=%u",
				done ? "done" : "off", why, m.seller, m.buyer, m.vnum, m.count, m.unit, m.map,
				(get_dword_time() - m.at) / 1000, s_uPlayerBotMeetupsDone, s_uPlayerBotMeetupsFailed);
		DWORD id = 0;
		std::map<DWORD, DWORD>::const_iterator of = s_mapPlayerBotMeetupOf.find(m.seller);
		if (of != s_mapPlayerBotMeetupOf.end())
			id = of->second;
		ForgetPlayerBotMeetup(id);
	}

	// One pair for the core, if one is to be had.
	bool PlanPlayerBotMeetup(DWORD dwNow)
	{
		// The buyers: a few drawn from the whole core.
		std::vector<LPCHARACTER> buyers;
		{
			std::vector<LPCHARACTER> all;
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
				if (c && IsPlayerBotMeetupFree(c, it->second))
					all.push_back(c);
			}
			if (all.size() < 2)
				return false;
			for (int i = 0; i < PLAYERBOT_MEETUP_BUYER_TRIES && !all.empty(); ++i)
			{
				const size_t k = (size_t)number(0, (int)all.size() - 1);
				buyers.push_back(all[k]);
				all[k] = all.back();
				all.pop_back();
			}
		}
		for (size_t b = 0; b < buyers.size(); ++b)
		{
			LPCHARACTER buyer = buyers[b];
			std::map<DWORD, int> wants;
			CollectPlayerBotMeetupWants(buyer, wants);
			if (wants.empty())
				continue;
			const long village = playerbot_empire_rules::GetHomeMap((int)buyer->GetEmpire(), playerbot_empire_rules::MAP_ROLE_M1);
			if (!IsPlayerBotDealVillage(village))
				continue;
			// A seller of the buyer's kingdom with one of the wants spare.
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				if (it->first == buyer->GetPlayerID())
					continue;
				LPCHARACTER seller = CHARACTER_MANAGER::instance().FindByPID(it->first);
				if (!seller || seller->GetEmpire() != buyer->GetEmpire() || !IsPlayerBotMeetupFree(seller, it->second))
					continue;
				for (std::map<DWORD, int>::const_iterator w = wants.begin(); w != wants.end(); ++w)
				{
					const int spare = GetPlayerBotMeetupSpare(seller, w->first);
					if (spare <= 0)
						continue;
					std::set<DWORD> sellerWants;
					CollectPlayerBotWantedMaterials(seller, sellerWants);
					if (sellerWants.count(w->first))
						continue;
					const TItemTable* proto = ITEM_MANAGER::instance().GetTable(w->first);
					if (!proto)
						continue;
					const long long fair = GetPlayerBotDealFairPrice(w->first);
					if (fair <= 0)
						continue;
					long long unit = HumanizePlayerBotPrice((DWORD)std::min<long long>(fair, 2000000000LL), false);
					// MT2009_PLUS_NPC_PRICE_CAP_V1: under what an NPC sells it for, or the buyer goes
					// to the NPC (GetPlayerBotNpcShopUnitPrice; not equipment, whose bonuses differ).
					const long long npcUnit = proto->bType == ITEM_WEAPON || proto->bType == ITEM_ARMOR
							? 0 : GetPlayerBotNpcShopUnitPrice(w->first);
					if (npcUnit > 0 && unit >= npcUnit)
						unit = HumanizePlayerBotPrice((DWORD)std::min<long long>(npcUnit * 90 / 100, 2000000000LL), false);
					int count = std::min(spare, w->second);
					const long long purse = (long long)buyer->GetGold() * 60 / 100;
					if (unit > 0 && (long long)count * unit > purse)
						count = (int)(purse / unit);
					if (count <= 0 || unit <= 0)
						continue;
					long sx = 0, sy = 0;
					if (!GetPlayerBotDealSmithSpot(village, seller->GetPlayerID(), sx, sy))
						continue;
					TPlayerBotMeetup m;
					m.seller = seller->GetPlayerID();
					m.buyer = buyer->GetPlayerID();
					m.vnum = w->first;
					m.count = count;
					m.unit = unit;
					m.map = village;
					m.sx = sx;
					m.sy = sy;
					m.bx = sx + 160;
					m.by = sy + 120;
					m.at = dwNow;
					m.nextTalkAt = dwNow;
					m.itemName = proto->szLocaleName;
					const DWORD id = s_dwPlayerBotMeetupNextId++;
					s_mapPlayerBotMeetups[id] = m;
					s_mapPlayerBotMeetupOf[m.seller] = id;
					s_mapPlayerBotMeetupOf[m.buyer] = id;
					sys_log(0, "PLAYERBOT_MEETUP: planned id=%u seller=%u(%s) buyer=%u(%s) vnum=%u count=%d unit=%lld map=%ld ch=%u",
							id, m.seller, seller->GetName(), m.buyer, buyer->GetName(), m.vnum, m.count, m.unit, m.map,
							(unsigned int)g_bChannel);
					return true;
				}
			}
		}
		sys_log(0, "PLAYERBOT_MEETUP: no pair buyers=%u", (unsigned int)buyers.size());
		return false;
	}

	// The talk on the trade chat, a line a step.
	void TalkPlayerBotMeetup(TPlayerBotMeetup& m, DWORD dwNow)
	{
		LPCHARACTER seller = CHARACTER_MANAGER::instance().FindByPID(m.seller);
		LPCHARACTER buyer = CHARACTER_MANAGER::instance().FindByPID(m.buyer);
		if (!seller || !buyer)
		{
			EndPlayerBotMeetup(m, false, "gone");
			return;
		}
		char line[CHAT_MAX_LEN + 1];
		const char* village = GetPlayerBotMeetupVillageName(m.map);
		const std::string price = playerbot_conv::FormatYang(m.unit);
		switch (m.talkStep)
		{
			case 0:
			{
				if (m.count > 1)
				{
					static const char* const k[] = { "K> %s x%d, kto ma? pw", "Kupie %s x%d, dobrze place", "B> %s x%d, ktos cos?" };
					snprintf(line, sizeof(line), k[number(0, 2)], m.itemName.c_str(), m.count);
				}
				else
				{
					static const char* const k[] = { "K> %s, kto ma? pw", "Kupie %s, ktos sprzeda?", "B> %s, pilne" };
					snprintf(line, sizeof(line), k[number(0, 2)], m.itemName.c_str());
				}
				SendPlayerBotTradeChat(buyer, line);
				NotePlayerBotPublicLine(buyer, playerbot_conv::PL_BUY, true, line, m.vnum, m.count, (DWORD)m.unit, 0, 0,
						m.itemName.c_str());
				break;
			}
			case 1:
			{
				static const char* const k[] = {
					"%s mam %s x%d, po %s/szt. CH%d, %s przy kowalu?",
					"%s jest %s x%d, %s za sztuke. Wpadaj CH%d %s, kowal",
					"%s moge sprzedac %s x%d po %s. Spotkajmy sie CH%d w %s przy kowalu" };
				snprintf(line, sizeof(line), k[number(0, 2)], buyer->GetName(), m.itemName.c_str(), m.count, price.c_str(),
						(int)g_bChannel, village);
				SendPlayerBotTradeChat(seller, line);
				break;
			}
			default:
			{
				static const char* const k[] = { "%s ok, biore. Ide do kowala w %s, CH%d", "%s pasuje, zaraz bede przy kowalu (%s CH%d)",
					"%s stoi, juz ide - %s, CH%d, kowal" };
				snprintf(line, sizeof(line), k[number(0, 2)], seller->GetName(), village, (int)g_bChannel);
				SendPlayerBotTradeChat(buyer, line);
				m.stage = MEETUP_GOING;
				break;
			}
		}
		++m.talkStep;
		m.nextTalkAt = dwNow + (DWORD)number((int)PLAYERBOT_MEETUP_REPLY_MIN_MS, (int)PLAYERBOT_MEETUP_REPLY_MAX_MS);
	}

	// The core's pass: the talk, the plan, the ends of time.
	void ManagePlayerBotMeetups(DWORD dwNow)
	{
		for (std::map<DWORD, TPlayerBotMeetup>::iterator it = s_mapPlayerBotMeetups.begin(); it != s_mapPlayerBotMeetups.end();)
		{
			TPlayerBotMeetup& m = it->second;
			++it;   // the meeting may end below
			if (dwNow - m.at > PLAYERBOT_MEETUP_TTL_MS)
			{
				EndPlayerBotMeetup(m, false, "expired");
				continue;
			}
			if (m.stage == MEETUP_TALK && (int)(dwNow - m.nextTalkAt) >= 0)
				TalkPlayerBotMeetup(m, dwNow);
		}
		if (!IsPlayerBotTradeChatOn())
			return;
		if (s_dwPlayerBotMeetupNextPlan == 0)
		{
			s_dwPlayerBotMeetupNextPlan = dwNow + PLAYERBOT_MEETUP_FIRST_DELAY_MS;
			return;
		}
		if ((int)(dwNow - s_dwPlayerBotMeetupNextPlan) < 0 || s_mapPlayerBotMeetups.size() >= PLAYERBOT_MEETUP_MAX_ACTIVE)
			return;
		s_dwPlayerBotMeetupNextPlan = dwNow + (DWORD)number((int)PLAYERBOT_MEETUP_GAP_MIN_MS, (int)PLAYERBOT_MEETUP_GAP_MAX_MS);
		PlanPlayerBotMeetup(dwNow);
	}

	// One side's way to its place and the wait there. True while it claims
	// the tick; `arrived` is stamped once it stands there.
	bool WalkPlayerBotToMeetup(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotMeetup& m, long x, long y,
			DWORD& arrived, DWORD& walkSince, DWORD& nextTry, int& tries, DWORD dwNow)
	{
		state.dwLastMeaningfulActivityTime = dwNow;
		state.lLastX = ch->GetX();
		state.lLastY = ch->GetY();
		ch->SetVictim(NULL);
		state.dwTargetVID = 0;
		if (ch->GetMapIndex() != m.map)
		{
			if (arrived != 0)
			{
				EndPlayerBotMeetup(m, false, "moved_away", ch, "Sorki, musialem odejsc. Innym razem.");
				return false;
			}
			if (dwNow < nextTry)
				return true;
			nextTry = dwNow + PLAYERBOT_MEETUP_RETRY_MS;
			if (++tries > PLAYERBOT_MEETUP_TRIES)
			{
				EndPlayerBotMeetup(m, false, "unreachable", ch, "Nie dojde teraz, sorki. Sprobujmy pozniej.");
				return false;
			}
			playerbot_empire_rules::TPoint square;
			if (!playerbot_empire_rules::GetTownPitch(m.map, square))
			{
				square.x = x;
				square.y = y;
			}
			if (TransitionPlayerBotMap(ch, state, m.map, square.x, square.y, dwNow, "meetup"))
				walkSince = dwNow;
			return true;
		}
		const int distance = DISTANCE_APPROX(ch->GetX() - x, ch->GetY() - y);
		if (arrived == 0)
		{
			if (walkSince == 0)
				walkSince = dwNow;
			if (distance > PLAYERBOT_MEETUP_STAY && dwNow - walkSince < PLAYERBOT_MEETUP_WALK_MAX_MS)
			{
				MovePlayerBot(ch, x, y, dwNow, 6, true, true, false, false);
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				return true;
			}
			arrived = dwNow;
			sys_log(0, "PLAYERBOT_MEETUP: at the spot pid=%u name=%s map=%ld distance=%d", ch->GetPlayerID(), ch->GetName(),
					m.map, distance);
		}
		if (distance > PLAYERBOT_MEETUP_STAY * 3)
		{
			MovePlayerBot(ch, x, y, dwNow, 6, true, true, false, false);
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			return true;
		}
		if (!state.vecRoute.empty())
			ClearPlayerBotRoute(state, true);
		if (ch->IsStateMove())
			ch->Stop();
		if (ch->IsRiding())
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "meetup_wait");
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// The window, the seller's tick driving it a step a glance: the pieces,
	// the yang, the buyer's accept, the seller's.
	bool RunPlayerBotMeetupWindow(LPCHARACTER seller, LPCHARACTER buyer, TPlayerBotMeetup& m, DWORD dwNow)
	{
		CExchange* sx = seller->GetExchange();
		CExchange* bx = buyer->GetExchange();
		if (!sx || !bx || sx->GetCompany() != bx)
		{
			EndPlayerBotMeetup(m, false, "window_closed");
			return true;
		}
		if (dwNow - m.windowAt > PLAYERBOT_MEETUP_WINDOW_MAX_MS)
		{
			EndPlayerBotMeetup(m, false, "window_timeout");
			return true;
		}
		if (dwNow < m.nextStepAt)
			return true;
		m.nextStepAt = dwNow + (DWORD)number((int)PLAYERBOT_MEETUP_STEP_MIN_MS, (int)PLAYERBOT_MEETUP_STEP_MAX_MS);
		switch (m.windowStep)
		{
			case 0:
				if (!OfferPlayerBotDealPieces(seller, sx, m.vnum, 0, m.count))
				{
					EndPlayerBotMeetup(m, false, "no_pieces", seller, "Ups, juz tego nie mam, sorki.");
					return true;
				}
				break;
			case 1:
			{
				const long long pay = m.unit * m.count;
				if ((long long)buyer->GetGold() < pay || !bx->AddGold(pay))
				{
					EndPlayerBotMeetup(m, false, "no_gold", buyer, "Kurcze, brakuje mi yang. Sorki.");
					return true;
				}
				break;
			}
			case 2:
				bx->Accept(true);
				break;
			default:
			{
				const long long before = (long long)seller->GetGold();
				sx->Accept(true);
				const bool done = !seller->GetExchange() && (long long)seller->GetGold() > before;
				if (done)
				{
					static const char* const kThanks[] = { "Dzieki, git handel!", "Dzieki :)", "Elegancko, dzieki." };
					static const char* const kBye[] = { "Spoko, powodzenia!", "Nara, milego expa.", "Do uslug :)" };
					SendPlayerBotLocalChat(buyer, kThanks[number(0, 2)]);
					SendPlayerBotLocalChat(seller, kBye[number(0, 2)]);
					TPlayerBotAIStateMap::iterator bs = s_mapPlayerBotAIStates.find(m.buyer);
					if (bs != s_mapPlayerBotAIStates.end())
						bs->second.dwNextEquipmentCheckTime = 0;
				}
				EndPlayerBotMeetup(m, done, done ? "traded" : "refused");
				return true;
			}
		}
		++m.windowStep;
		return true;
	}

	// A bot's tick while it has a meeting. True while the meeting claims it.
	bool HandlePlayerBotMeetup(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || s_mapPlayerBotMeetupOf.empty())
			return false;
		TPlayerBotMeetup* pm = FindPlayerBotMeetupOf(ch->GetPlayerID());
		if (!pm)
			return false;
		TPlayerBotMeetup& m = *pm;
		const bool isSeller = m.seller == ch->GetPlayerID();
		if (ch->IsDead())
			return false;
		// A raid with its party first (IsPlayerBotInDungeonBusiness): it says
		// so, and the meeting is off.
		if (IsPlayerBotInDungeonBusiness(ch, state) || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())))
		{
			EndPlayerBotMeetup(m, false, "raid", ch, "Sorki, ide z ekipa na rajd. Pogadamy pozniej.");
			return false;
		}
		if (m.stage == MEETUP_TALK)
			return false;
		LPCHARACTER other = CHARACTER_MANAGER::instance().FindByPID(isSeller ? m.buyer : m.seller);
		if (!other || !other->GetDesc())
		{
			EndPlayerBotMeetup(m, false, "partner_gone");
			return false;
		}
		if (m.stage == MEETUP_WINDOW)
		{
			ch->SetVictim(NULL);
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			state.dwLastMeaningfulActivityTime = dwNow;
			if (isSeller)
				return RunPlayerBotMeetupWindow(ch, other, m, dwNow);
			return true;
		}
		// Staying alive first: hurt, or something on it - it fights and drinks.
		if (IsPlayerBotSurvivalFirst(ch, state, dwNow))
			return false;
		const DWORD firstArrived = m.sellerArrived && m.buyerArrived ? std::min(m.sellerArrived, m.buyerArrived)
				: (m.sellerArrived ? m.sellerArrived : m.buyerArrived);
		if (firstArrived != 0 && dwNow - firstArrived > PLAYERBOT_MEETUP_WAIT_MS)
		{
			EndPlayerBotMeetup(m, false, "wait_timeout", ch, "Nie doczekalem sie, ide dalej.");
			return false;
		}
		const bool claimed = isSeller
				? WalkPlayerBotToMeetup(ch, state, m, m.sx, m.sy, m.sellerArrived, m.sellerWalk, m.sellerNextTry, m.sellerTries, dwNow)
				: WalkPlayerBotToMeetup(ch, state, m, m.bx, m.by, m.buyerArrived, m.buyerWalk, m.buyerNextTry, m.buyerTries, dwNow);
		if (!claimed || !FindPlayerBotMeetupOf(ch->GetPlayerID()))
			return claimed;
		// Both there: the seller opens the window.
		if (isSeller && m.sellerArrived && m.buyerArrived && other->GetMapIndex() == ch->GetMapIndex() &&
				DISTANCE_APPROX(other->GetX() - ch->GetX(), other->GetY() - ch->GetY()) < EXCHANGE_MAX_DISTANCE - 100 &&
				!ch->GetExchange() && !other->GetExchange())
		{
			if (ch->ExchangeStart(other))
			{
				m.stage = MEETUP_WINDOW;
				m.windowAt = dwNow;
				m.windowStep = 0;
				m.nextStepAt = dwNow + (DWORD)number((int)PLAYERBOT_MEETUP_STEP_MIN_MS, (int)PLAYERBOT_MEETUP_STEP_MAX_MS);
				static const char* const kHi[] = { "Siema, juz daje wymiane.", "Jestem, otwieram handel.", "No to dawaj, wymiana." };
				SendPlayerBotLocalChat(ch, kHi[number(0, 2)]);
				sys_log(0, "PLAYERBOT_MEETUP: window seller=%u buyer=%u", m.seller, m.buyer);
			}
		}
		return true;
	}
}

#endif
