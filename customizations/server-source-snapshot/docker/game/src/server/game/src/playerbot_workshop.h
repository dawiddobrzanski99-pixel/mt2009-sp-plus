#ifndef __INC_METIN2_PLAYERBOT_WORKSHOP_H__
#define __INC_METIN2_PLAYERBOT_WORKSHOP_H__

// MT2009_PLUS_BOT_WORKSHOP_V1: the errand of the belts and the talismans (playerbot_belts.h,
// playerbot_talismans.h) - Mistrz (20082) and the Blacksmith beside him in a first village.
//
// Now and then (PLAYERBOT_WORKSHOP_CHECK_*) a bot looks at its belt and talisman work: a belt to
// make (the target's materials in the bag or owed by a gift), the worn belt under its aim, a
// talisman step it can pay for. With any, it goes to the first village of its kingdom (the road
// Uriel's errand takes, playerbot_sash.h), to Mistrz first - the belt attempts, and the Kwiat
// Zywiolu of the talisman steps from his shop 9550 - then to the Blacksmith 500 units away for
// the talisman steps and the belt's. Every step is the engine's (DoRefine) or done the way the
// engine does it (the cube recipe, the shop's price), a few seconds apart, at most
// PLAYERBOT_WORKSHOP_VISIT_MS a visit.
//
// Besides the errand, on a short clock of its own: the field map the bot hunts on is noted (the
// talisman is chosen for it), the gifts are decided once, the best talisman for the map goes
// on, and the belt's pouch is filled or emptied. And the hooks the other passes ask: what is
// kept of the materials (GetPlayerBotRefineMaterialReserve, the merchant, the counter), what the
// market should sell this bot and at what price. Event flag m2_bot_workshop_off stops the errand
// and the gifts' hand-over (the wear pass and the pouch stay).

namespace
{
	const DWORD PLAYERBOT_WORKSHOP_CHECK_MIN_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_WORKSHOP_CHECK_MAX_MS = 8 * 60 * 1000;
	const DWORD PLAYERBOT_WORKSHOP_LIGHT_MIN_MS = 40 * 1000;
	const DWORD PLAYERBOT_WORKSHOP_LIGHT_MAX_MS = 80 * 1000;
	const DWORD PLAYERBOT_WORKSHOP_VISIT_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_WORKSHOP_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_MISTRZ_VNUM = 20082;

	enum
	{
		PLAYERBOT_WORKSHOP_NONE,
		PLAYERBOT_WORKSHOP_MISTRZ,
		PLAYERBOT_WORKSHOP_SMITH,
	};

	struct TPlayerBotWorkshop
	{
		BYTE phase;
		BYTE steps;
		BYTE beltAttempts;
		BYTE talismanSteps;
		BYTE beltRefines;
		bool flowersBought;
		DWORD nextCheck;
		DWORD nextLight;
		DWORD nextAction;
		DWORD visitStart;
		long fieldMap;
	};
	std::map<DWORD, TPlayerBotWorkshop> s_mapPlayerBotWorkshop;

	TPlayerBotWorkshop& GetPlayerBotWorkshop(DWORD pid)
	{
		std::map<DWORD, TPlayerBotWorkshop>::iterator it = s_mapPlayerBotWorkshop.find(pid);
		if (it == s_mapPlayerBotWorkshop.end())
		{
			TPlayerBotWorkshop fresh;
			memset(&fresh, 0, sizeof(fresh));
			it = s_mapPlayerBotWorkshop.insert(std::make_pair(pid, fresh)).first;
		}
		return it->second;
	}

	long GetPlayerBotHuntingMap(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		const long map = ch->GetMapIndex();
		if (!IsPlayerBotVillageMap(map))
			return map;
		std::map<DWORD, TPlayerBotWorkshop>::const_iterator it = s_mapPlayerBotWorkshop.find(ch->GetPlayerID());
		return it != s_mapPlayerBotWorkshop.end() && it->second.fieldMap != 0 ? it->second.fieldMap : map;
	}

	bool IsPlayerBotWorkshopOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_workshop_off") != 0;
	}

	// Mistrz in the first villages: npc.txt cells (675,560), (598,695) and (394,702) (the
	// Dockerfile's MT2009_PLUS_BELTS_V1 lines) on the bases (409600,896000), (0,102400) and
	// (921600,204800) - 300 to 1000 units from the Blacksmith.
	bool GetPlayerBotMistrz(long mapIndex, playerbot_empire_rules::TPoint& out)
	{
		switch (mapIndex)
		{
			case 1:  out.x = 477100; out.y = 952000; return true;
			case 21: out.x = 59800;  out.y = 172000; return true;
			case 41: out.x = 961000; out.y = 275000; return true;
			default: return false;
		}
	}

	// ---- the hooks ------------------------------------------------------------------------

	int GetPlayerBotCraftMaterialKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || vnum == 0 || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		return std::max(GetPlayerBotBeltMaterialKeep(ch, vnum), GetPlayerBotTalismanMaterialKeep(ch, vnum));
	}

	// Not the merchant's and not the counter's: the talisman worn best or worked on, and the
	// units of a material within what its craft keeps (the stacks before this one counted first).
	bool IsPlayerBotKeptCraftGoods(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item)
			return false;
		if (IsPlayerBotKeptTalisman(ch, item))
			return true;
		const int keep = GetPlayerBotCraftMaterialKeep(ch, item->GetVnum());
		return keep > 0 && CountPlayerBotVnumUnitsAhead(ch, item) < keep;
	}

	bool WantsPlayerBotCraftOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || IsPlayerBotSidekickPID(ch->GetPlayerID()) || IsPlayerBotWorkshopOff())
			return false;
		return WantsPlayerBotBeltOffer(ch, offer) || WantsPlayerBotTalismanOffer(ch, offer);
	}

	bool CanPlayerBotPayForCraftOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (WantsPlayerBotBeltOffer(ch, offer) && CanPlayerBotPayForBeltOffer(ch, offer, price))
			return true;
		return WantsPlayerBotTalismanOffer(ch, offer) && CanPlayerBotPayForTalismanOffer(ch, offer, price);
	}

	// Every material the two crafts lack, for the walk over the stands; the cap is what one
	// line may cost.
	long long CollectPlayerBotCraftMissing(LPCHARACTER ch, std::map<DWORD, int>& missing, long long budget)
	{
		missing.clear();
		if (!ch || IsPlayerBotSidekickPID(ch->GetPlayerID()) || IsPlayerBotWorkshopOff())
			return 0;
		CollectPlayerBotBeltMissing(ch, missing);
		CollectPlayerBotTalismanMissing(ch, missing);
		return budget * 40 / 100;
	}

	// Asked before the walk to the market, without reading a counter: something missing that
	// the ledger says a counter holds.
	bool PlayerBotWantsCraftFromMarket(LPCHARACTER ch)
	{
		std::map<DWORD, int> missing;
		if (CollectPlayerBotCraftMissing(ch, missing, 1) < 0 || missing.empty())
			return false;
		for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end(); ++it)
		{
			const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(it->first);
			if (e && e->dwSupplyUnits > 0)
				return true;
		}
		return false;
	}

	void NotePlayerBotCraftBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		NotePlayerBotBeltBought(ch, vnum, price);
		NotePlayerBotTalismanBought(ch, vnum, price);
	}

	// ---- the errand -----------------------------------------------------------------------

	bool HasPlayerBotMistrzWork(LPCHARACTER ch, const TPlayerBotWorkshop& w)
	{
		if (w.beltAttempts < PLAYERBOT_BELT_VISIT_ATTEMPTS && HasPlayerBotBeltCraftWork(ch))
			return true;
		return !w.flowersBought && HasPlayerBotTalismanWork(ch);
	}

	bool HasPlayerBotWorkshopWork(LPCHARACTER ch)
	{
		return HasPlayerBotBeltCraftWork(ch) || HasPlayerBotBeltRefineWork(ch) || HasPlayerBotTalismanWork(ch);
	}

	void EndPlayerBotWorkshopVisit(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotWorkshop& w, DWORD dwNow,
			const char* why)
	{
		if (w.phase != PLAYERBOT_WORKSHOP_NONE && ch)
		{
			WearPlayerBotBestTalisman(ch);
			sys_log(0, "PLAYERBOT_WORKSHOP: visit over pid=%u name=%s why=%s belt_attempts=%d belt_refines=%d talisman_steps=%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), why, (int)w.beltAttempts, (int)w.beltRefines,
					(int)w.talismanSteps, (long long)ch->GetGold());
		}
		w.phase = PLAYERBOT_WORKSHOP_NONE;
		w.nextAction = 0;
		w.nextCheck = dwNow + number(PLAYERBOT_WORKSHOP_CHECK_MIN_MS, PLAYERBOT_WORKSHOP_CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
	}

	// The light pass, on its own clock.
	void ManagePlayerBotWorkshopLight(LPCHARACTER ch, TPlayerBotWorkshop& w, DWORD dwNow)
	{
		const long map = ch->GetMapIndex();
		if (!IsPlayerBotVillageMap(map))
			w.fieldMap = map;
		if (w.nextLight != 0 && (int)(dwNow - w.nextLight) < 0)
			return;
		w.nextLight = dwNow + number(PLAYERBOT_WORKSHOP_LIGHT_MIN_MS, PLAYERBOT_WORKSHOP_LIGHT_MAX_MS);
		if (!IsPlayerBotWorkshopOff())
		{
			DecidePlayerBotBeltSeed(ch);
			DecidePlayerBotTalismanSeed(ch);
		}
		WearPlayerBotBestTalisman(ch);
		ManagePlayerBotBeltPouch(ch);
		// The shards a maker's belt needs stay off the counters (playerbot_energy_shards.h:
		// the Alchemist's shards are listed over this keep only).
		SetPlayerBotEnergyShardKeep(ch->GetPlayerID(), GetPlayerBotBeltMaterialKeep(ch, PLAYERBOT_ENERGY_SHARD_VNUM));
	}

	// Walks to the point; true while still walking (or stuck - the visit then ends).
	bool WalkPlayerBotWorkshopLeg(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotWorkshop& w, DWORD dwNow,
			long x, long y, DWORD salt, bool& failed)
	{
		failed = false;
		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), x, y, salt, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) <= 650)
			return false;
		if (!MovePlayerBot(ch, approachX, approachY, dwNow, 20, true, true, false, true) && state.bStuckCounter >= 6)
		{
			sys_err("PLAYERBOT_WORKSHOP: route failed pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), approachX, approachY);
			failed = true;
		}
		return true;
	}

	DWORD s_dwPlayerBotWorkshopCensusAt = 0;

	// The tick, beside Uriel's errand (playerbot_manager.cpp) and for its reason: above the
	// travel pass, which would walk the bot out of the village it was brought to.
	bool ManagePlayerBotWorkshop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		if (s_dwPlayerBotWorkshopCensusAt == 0 || (int)(dwNow - s_dwPlayerBotWorkshopCensusAt) >= 0)
		{
			if (s_dwPlayerBotWorkshopCensusAt != 0)
			{
				LogPlayerBotBeltCensus();
				LogPlayerBotTalismanCensus();
			}
			s_dwPlayerBotWorkshopCensusAt = dwNow + PLAYERBOT_WORKSHOP_CENSUS_MS;
		}
		TPlayerBotWorkshop& w = GetPlayerBotWorkshop(ch->GetPlayerID());
		ManagePlayerBotWorkshopLight(ch, w, dwNow);

		// Another errand has the bot, or somebody else does: no visit now.
		const bool otherErrand = state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingStable || state.bVisitingAlchemist || state.bVisitingUriel || state.bFishingSession ||
				state.bMarketTrip || state.bVisitingYonah;
		if (otherErrand || IsPlayerBotWorkshopOff() || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
				IsPlayerBotHeldForCompany(ch) || ch->GetMyShop() != NULL || ch->GetExchange() ||
				IsPlayerBotArezzoHeldHere(ch))
		{
			if (w.phase != PLAYERBOT_WORKSHOP_NONE)
				EndPlayerBotWorkshopVisit(ch, state, w, dwNow, "interrupted");
			return false;
		}
		if (w.phase == PLAYERBOT_WORKSHOP_NONE && (int)(dwNow - w.nextCheck) < 0)
			return false;

		if (w.phase == PLAYERBOT_WORKSHOP_NONE)
		{
			w.nextCheck = dwNow + number(PLAYERBOT_WORKSHOP_CHECK_MIN_MS, PLAYERBOT_WORKSHOP_CHECK_MAX_MS);
			if (!HasPlayerBotWorkshopWork(ch))
				return false;
			playerbot_empire_rules::TPoint mistrz;
			if (!GetPlayerBotMistrz(ch->GetMapIndex(), mistrz))
			{
				long homeMap = 0, homeX = 0, homeY = 0;
				if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, homeMap, homeX, homeY) ||
						!IsPlayerBotMapHostedHere(homeMap) || !GetPlayerBotMistrz(homeMap, mistrz))
					return false;
				// Not from a fight: the next look, then.
				if (ch->GetVictim() != NULL || state.dwTargetVID != 0)
				{
					w.nextCheck = dwNow + number(20000, 60000);
					return false;
				}
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				if (!TransitionPlayerBotMap(ch, state, homeMap, homeX, homeY, dwNow, "workshop_to_mistrz"))
					return false;
				// Straight to Mistrz once it stands in the village.
				w.nextCheck = 0;
				return true;
			}
			w.phase = PLAYERBOT_WORKSHOP_MISTRZ;
			w.steps = w.beltAttempts = w.talismanSteps = w.beltRefines = 0;
			w.flowersBought = false;
			w.nextAction = 0;
			w.visitStart = dwNow;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_WORKSHOP: going to Mistrz pid=%u name=%s lv=%d belt_craft=%d belt_refine=%d talisman=%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), HasPlayerBotBeltCraftWork(ch) ? 1 : 0,
					HasPlayerBotBeltRefineWork(ch) ? 1 : 0, HasPlayerBotTalismanWork(ch) ? 1 : 0,
					(long long)ch->GetGold());
		}

		playerbot_empire_rules::TPoint mistrz;
		playerbot_empire_rules::TTownServices svc;
		if (!GetPlayerBotMistrz(ch->GetMapIndex(), mistrz) ||
				!playerbot_empire_rules::GetTownServices(ch->GetMapIndex(), svc))
		{
			EndPlayerBotWorkshopVisit(ch, state, w, dwNow, "left_village");
			return false;
		}
		if (dwNow - w.visitStart > PLAYERBOT_WORKSHOP_VISIT_MS)
		{
			EndPlayerBotWorkshopVisit(ch, state, w, dwNow, "timeout");
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		const bool atMistrz = w.phase == PLAYERBOT_WORKSHOP_MISTRZ;
		bool failed = false;
		if (WalkPlayerBotWorkshopLeg(ch, state, w, dwNow, atMistrz ? mistrz.x : svc.blacksmith.x,
				atMistrz ? mistrz.y : svc.blacksmith.y, atMistrz ? 0x4d495354U : 0x4b4f574cU, failed))
		{
			if (failed)
				EndPlayerBotWorkshopVisit(ch, state, w, dwNow, "route_failed");
			return !failed;
		}

		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (w.nextAction == 0)
		{
			w.nextAction = dwNow + number(3000, 7000);
			return true;
		}
		if ((int)(dwNow - w.nextAction) < 0)
			return true;

		bool did = false;
		if (atMistrz)
		{
			// A belt attempt, else the flowers of the talisman steps, else on to the anvil.
			if (w.beltAttempts < PLAYERBOT_BELT_VISIT_ATTEMPTS && HasPlayerBotBeltCraftWork(ch))
			{
				++w.beltAttempts;
				did = CraftPlayerBotBelt(ch);
				// Refused (no room, the yang): not again this visit.
				if (!did)
					w.beltAttempts = PLAYERBOT_BELT_VISIT_ATTEMPTS;
			}
			if (!did && !w.flowersBought && HasPlayerBotTalismanWork(ch))
			{
				w.flowersBought = true;
				did = BuyPlayerBotTalismanFlowers(ch, PLAYERBOT_TALISMAN_VISIT_STEPS) > 0;
			}
			if (!did && !HasPlayerBotMistrzWork(ch, w))
			{
				// The belt a craft made goes on (the pouch of the old one emptied first), and
				// then the anvil, when it has anything.
				ManagePlayerBotBeltPouch(ch);
				if (!HasPlayerBotBeltRefineWork(ch) && !HasPlayerBotTalismanWork(ch))
				{
					EndPlayerBotWorkshopVisit(ch, state, w, dwNow, "done");
					return false;
				}
				w.phase = PLAYERBOT_WORKSHOP_SMITH;
				w.nextAction = 0;
				ClearPlayerBotRoute(state, true);
				return true;
			}
		}
		else
		{
			if (w.talismanSteps < PLAYERBOT_TALISMAN_VISIT_STEPS && HasPlayerBotTalismanWork(ch) &&
					RefinePlayerBotTalismanStep(ch))
			{
				++w.talismanSteps;
				did = true;
			}
			else if (w.beltRefines < PLAYERBOT_BELT_VISIT_REFINES && HasPlayerBotBeltRefineWork(ch) &&
					RefinePlayerBotBeltStep(ch))
			{
				++w.beltRefines;
				did = true;
			}
			if (!did)
			{
				EndPlayerBotWorkshopVisit(ch, state, w, dwNow, "done");
				return false;
			}
		}
		++w.steps;
		w.nextAction = dwNow + number(2500, 5000);
		return true;
	}
}

#endif
