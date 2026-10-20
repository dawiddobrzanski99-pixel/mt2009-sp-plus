#ifndef __INC_METIN2_PLAYERBOT_DAY_GOAL_H__
#define __INC_METIN2_PLAYERBOT_DAY_GOAL_H__

// MT2009_PLUS_BOT_DAY_GOAL_V1 - Cel Dnia.
//
// The owner, 9 October: "Cel Dnia: czesc botow losuje cel na sesje (Metiny,
// poziom, yang, boss, ulepszenie...) z poziomem trudnosci; widac go nad glowa
// na niebiesko, a sukces lub porazka zmienia ich nastroj".
//
// A share of the bots (PLAYERBOT_DAY_GOAL_PERCENT) draws a goal a few minutes
// into its session, and one without a goal may draw another every hour or
// two of play (PLAYERBOT_DAY_GOAL_REDRAW_*). A goal is a kind, a difficulty
// and a deadline: break Metins, gain levels, earn yang, kill bosses, land
// refines, or clear monsters, for one, one and a half or two hours. It does
// not steer the bot - it plays as it always does, and the goal is what it
// set itself for the session: the line over its head shows it in blue in
// front of the status (ManagePlayerBotStatusOverhead, a colour tag the
// client draws in any text tail, so no new client is needed), and its end
// moves the mood of Iwakura's system (playerbot_mood.h): a goal met lifts
// it a level, a goal missed lowers it one - not under a lock, as every other
// news.
//
// MT2009_PLUS_BOT_DAY_GOAL_SAVE_V1 - the owner, 10 October: "cel bota nie
// przepada przy wylogowaniu ani zmianie kanalu". The goal lives in the bot's
// quest flags (PLAYERBOT_DAY_GOAL_FLAG_*), written whenever it is drawn, moves
// or ends, and read back once the flags have arrived from the db core
// (quest::PC::IsLoaded, as the mood's). Its start and deadline are kept as
// world time (get_global_time): the clock runs on while the bot is away, so a
// goal whose hour ran out offline ends missed on the next login, and one
// still running goes on with the time it has left. The yang goal keeps its
// progress rather than the purse it started from - the purse after a login
// minus what was earned so far is the same baseline. The next draw after an
// end is kept as world time too, so a channel change does not draw anew.
//
// The counters come from the engine's kill note (BattlePassOnKill and its
// shared half, playerbot_battlepass.h), the refine note (NotePlayerBotMoodRefine)
// and the bot's own level and purse.
//
// An implementation fragment: include it once, after playerbot_status.h; the
// manager's tick calls ManagePlayerBotDayGoal beside AdvancePlayerBotMood.

namespace
{
	enum EPlayerBotDayGoalKind
	{
		DAY_GOAL_NONE = 0,
		DAY_GOAL_METINS,
		DAY_GOAL_LEVEL,
		DAY_GOAL_YANG,
		DAY_GOAL_BOSS,
		DAY_GOAL_REFINE,
		DAY_GOAL_MONSTERS,
		DAY_GOAL_KIND_COUNT
	};

	const int PLAYERBOT_DAY_GOAL_PERCENT = 30;
	const int PLAYERBOT_DAY_GOAL_MIN_LEVEL = 15;
	const DWORD PLAYERBOT_DAY_GOAL_FIRST_MIN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_DAY_GOAL_FIRST_MAX_MS = 6 * 60 * 1000;
	const DWORD PLAYERBOT_DAY_GOAL_REDRAW_MIN_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_DAY_GOAL_REDRAW_MAX_MS = 120 * 60 * 1000;
	const DWORD PLAYERBOT_DAY_GOAL_CHECK_MS = 5000;
	// The goal's line shows this long after the end, with how it ended.
	const DWORD PLAYERBOT_DAY_GOAL_SHOW_END_MS = 3 * 60 * 1000;
	// The client's colour tag: a light blue that reads on the dark sky.
	const char* const PLAYERBOT_DAY_GOAL_COLOUR = "|cFF4D9BFF";
	// MT2009_PLUS_BOT_DAY_GOAL_SAVE_V1: the goal between sessions. Each value
	// is kept plus one, so a flag never written (0) reads as "none".
	const char* const PLAYERBOT_DAY_GOAL_FLAG_KIND = "playerbot.day_goal_kind";        // kind + 16 * difficulty
	const char* const PLAYERBOT_DAY_GOAL_FLAG_TARGET = "playerbot.day_goal_target";
	const char* const PLAYERBOT_DAY_GOAL_FLAG_PROGRESS = "playerbot.day_goal_progress";
	const char* const PLAYERBOT_DAY_GOAL_FLAG_LEVEL = "playerbot.day_goal_level";      // the level it started at
	const char* const PLAYERBOT_DAY_GOAL_FLAG_START = "playerbot.day_goal_start";      // world time
	const char* const PLAYERBOT_DAY_GOAL_FLAG_DEADLINE = "playerbot.day_goal_deadline"; // world time
	const char* const PLAYERBOT_DAY_GOAL_FLAG_NEXT_DRAW = "playerbot.day_goal_next";   // world time

	struct TPlayerBotDayGoal
	{
		BYTE kind;
		BYTE difficulty;     // 0 easy, 1 medium, 2 hard
		int target;
		int progress;
		long long startGold;
		int startLevel;
		DWORD startAt;
		DWORD deadline;
		DWORD sessionSpawn;  // the state's dwSpawnTime the goal belongs to
		DWORD nextDrawAt;
		DWORD nextCheckAt;
		DWORD endedAt;
		bool success;
		// MT2009_PLUS_BOT_DAY_GOAL_SAVE_V1
		bool restored;       // the flags have been read this session
		int savedProgress;   // what the flags hold, so they are written on a change only
		int startWorld;      // world time of the start and the deadline
		int deadlineWorld;
		TPlayerBotDayGoal() : kind(DAY_GOAL_NONE), difficulty(0), target(0), progress(0), startGold(0), startLevel(0),
			startAt(0), deadline(0), sessionSpawn(0), nextDrawAt(0), nextCheckAt(0), endedAt(0), success(false),
			restored(false), savedProgress(-1), startWorld(0), deadlineWorld(0) {}
	};

	std::map<DWORD, TPlayerBotDayGoal> s_mapPlayerBotDayGoals;
	unsigned int s_uPlayerBotDayGoalsMet = 0;
	unsigned int s_uPlayerBotDayGoalsMissed = 0;

	bool IsPlayerBotDayGoalCandidate(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || (int)ch->GetLevel() < PLAYERBOT_DAY_GOAL_MIN_LEVEL)
			return false;
		const DWORD pid = ch->GetPlayerID();
		return !IsPlayerBotSidekickPID(pid) && !IsPlayerBotShouterPID(pid) && !IsPlayerBotMedalShouterPID(pid) &&
				!IsPlayerBotDropper(state.bPersonality);
	}

	DWORD GetPlayerBotDayGoalMinutes(BYTE difficulty)
	{
		return difficulty == 0 ? 60 : difficulty == 1 ? 90 : 120;
	}

	int GetPlayerBotDayGoalTarget(LPCHARACTER ch, BYTE kind, BYTE difficulty)
	{
		const int level = (int)ch->GetLevel();
		const int d = difficulty > 2 ? 2 : difficulty;
		switch (kind)
		{
			case DAY_GOAL_METINS:
			{
				static const int k[3] = { 3, 6, 10 };
				return k[d];
			}
			case DAY_GOAL_LEVEL:
			{
				static const int young[3] = { 2, 3, 5 };
				static const int middle[3] = { 1, 2, 3 };
				static const int old[3] = { 1, 1, 2 };
				return level < 40 ? young[d] : level < 70 ? middle[d] : old[d];
			}
			case DAY_GOAL_YANG:
			{
				static const int mult[3] = { 1, 2, 4 };
				const long long base = std::max<long long>(20000, (long long)level * level * 150);
				return (int)std::min<long long>(base * mult[d], 2000000000LL);
			}
			case DAY_GOAL_BOSS:
			{
				static const int k[3] = { 1, 2, 4 };
				return k[d];
			}
			case DAY_GOAL_REFINE:
			{
				static const int k[3] = { 1, 2, 4 };
				return k[d];
			}
			case DAY_GOAL_MONSTERS:
			{
				static const int k[3] = { 100, 250, 500 };
				return k[d];
			}
		}
		return 0;
	}

	// The kinds this bot can work at at its level and in its world.
	BYTE DrawPlayerBotDayGoalKind(LPCHARACTER ch)
	{
		BYTE kinds[DAY_GOAL_KIND_COUNT];
		int n = 0;
		const int level = (int)ch->GetLevel();
		kinds[n++] = DAY_GOAL_MONSTERS;
		kinds[n++] = DAY_GOAL_YANG;
		if (level >= 20)
			kinds[n++] = DAY_GOAL_METINS;
		if (level < PLAYER_MAX_LEVEL_CONST - 1)
			kinds[n++] = DAY_GOAL_LEVEL;
		if (level >= 40)
			kinds[n++] = DAY_GOAL_BOSS;
		if (level >= 30)
			kinds[n++] = DAY_GOAL_REFINE;
		return kinds[number(0, n - 1)];
	}

	// MT2009_PLUS_BOT_DAY_GOAL_SAVE_V1: the running goal into the flags, or
	// none and when the next one may be drawn.
	void SavePlayerBotDayGoal(LPCHARACTER ch, TPlayerBotDayGoal& g)
	{
		if (!ch || !g.restored)
			return;
		if (g.kind == DAY_GOAL_NONE || g.endedAt != 0)
		{
			ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_KIND, 0);
			const DWORD dwNow = get_dword_time();
			const int left = g.nextDrawAt != 0 && (int)(g.nextDrawAt - dwNow) > 0 ? (int)((g.nextDrawAt - dwNow) / 1000) : 0;
			ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_NEXT_DRAW, left > 0 ? get_global_time() + left + 1 : 0);
			g.savedProgress = -1;
			return;
		}
		ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_KIND, (int)g.kind + 16 * (int)g.difficulty + 1);
		ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_TARGET, g.target + 1);
		ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_PROGRESS, std::max(0, g.progress) + 1);
		ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_LEVEL, g.startLevel + 1);
		ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_START, g.startWorld + 1);
		ch->SetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_DEADLINE, g.deadlineWorld + 1);
		g.savedProgress = g.progress;
	}

	// Once a session, as soon as the flags have arrived: false until then.
	// A goal whose deadline passed while the bot was away is handed back
	// running at its deadline, and the caller's pass ends it missed.
	bool RestorePlayerBotDayGoal(LPCHARACTER ch, TPlayerBotDayGoal& g, DWORD dwNow)
	{
		if (g.restored)
			return true;
		quest::PC* pc = quest::CQuestManager::instance().GetPC(ch->GetPlayerID());
		if (!pc || !pc->IsLoaded())
			return false;
		g.restored = true;
		const int now = get_global_time();
		const int packed = ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_KIND) - 1;
		const int kind = packed >= 0 ? packed % 16 : 0;
		const int difficulty = packed >= 0 ? packed / 16 : 0;
		const int target = ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_TARGET) - 1;
		const int deadlineWorld = ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_DEADLINE) - 1;
		if (kind > DAY_GOAL_NONE && kind < DAY_GOAL_KIND_COUNT && difficulty <= 2 && target > 0 && deadlineWorld > 0)
		{
			g.kind = (BYTE)kind;
			g.difficulty = (BYTE)difficulty;
			g.target = target;
			g.progress = std::max(0, ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_PROGRESS) - 1);
			g.savedProgress = g.progress;
			g.startLevel = std::max(1, ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_LEVEL) - 1);
			g.startGold = (long long)ch->GetGold() - (g.kind == DAY_GOAL_YANG ? (long long)g.progress : 0);
			g.startWorld = ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_START) - 1;
			if (g.startWorld <= 0 || g.startWorld > now)
				g.startWorld = now;
			g.deadlineWorld = deadlineWorld;
			// The bot's own clock, from what is left of the world's.
			g.startAt = dwNow - (DWORD)std::min(now - g.startWorld, 7 * 24 * 3600) * 1000;
			g.deadline = dwNow + (DWORD)std::max(0, deadlineWorld - now) * 1000;
			sys_log(0, "PLAYERBOT_DAY_GOAL: restored pid=%u name=%s kind=%u difficulty=%u progress=%d/%d minutes_left=%d",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)g.kind, (unsigned int)g.difficulty, g.progress,
					g.target, std::max(0, deadlineWorld - now) / 60);
			return true;
		}
		// None running: the first draw a few minutes into the session, or
		// later if the last goal ended a short while ago.
		const int nextDrawWorld = ch->GetQuestFlag(PLAYERBOT_DAY_GOAL_FLAG_NEXT_DRAW) - 1;
		DWORD wait = (DWORD)number((int)PLAYERBOT_DAY_GOAL_FIRST_MIN_MS, (int)PLAYERBOT_DAY_GOAL_FIRST_MAX_MS);
		if (nextDrawWorld > now)
			wait = std::max<DWORD>(wait, (DWORD)std::min(nextDrawWorld - now, 4 * 3600) * 1000);
		g.nextDrawAt = dwNow + wait;
		return true;
	}

	void StartPlayerBotDayGoal(LPCHARACTER ch, TPlayerBotDayGoal& g, DWORD dwNow)
	{
		const DWORD sessionSpawn = g.sessionSpawn;
		g = TPlayerBotDayGoal();
		g.sessionSpawn = sessionSpawn;
		g.kind = DrawPlayerBotDayGoalKind(ch);
		const int roll = number(1, 100);
		g.difficulty = roll <= 50 ? 0 : roll <= 85 ? 1 : 2;
		g.target = std::max(1, GetPlayerBotDayGoalTarget(ch, g.kind, g.difficulty));
		g.startGold = (long long)ch->GetGold();
		g.startLevel = (int)ch->GetLevel();
		g.startAt = dwNow;
		g.deadline = dwNow + GetPlayerBotDayGoalMinutes(g.difficulty) * 60 * 1000;
		g.restored = true;
		g.startWorld = get_global_time();
		g.deadlineWorld = g.startWorld + (int)GetPlayerBotDayGoalMinutes(g.difficulty) * 60;
		SavePlayerBotDayGoal(ch, g);
		sys_log(0, "PLAYERBOT_DAY_GOAL: drawn pid=%u name=%s level=%d kind=%u difficulty=%u target=%d minutes=%u",
				ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), (unsigned int)g.kind,
				(unsigned int)g.difficulty, g.target, GetPlayerBotDayGoalMinutes(g.difficulty));
	}

	// The mood a level down, as every other bad news (OnBigRefineFailure):
	// not under a lock, never below SLABY.
	void LowerPlayerBotMoodForDayGoal(TPlayerBotPersona& p)
	{
		if (playerbot_persona::IsMoodLocked(p.mood) || p.mood.mood <= playerbot_persona::MOOD_SLABY)
			return;
		--p.mood.mood;
		p.bDirty = true;
	}

	void EndPlayerBotDayGoal(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDayGoal& g, bool success, DWORD dwNow)
	{
		g.endedAt = dwNow != 0 ? dwNow : 1;
		g.success = success;
		if (success)
			++s_uPlayerBotDayGoalsMet;
		else
			++s_uPlayerBotDayGoalsMissed;
		const uint8_t before = state.persona.mood.mood;
		if (IsPlayerBotPersonaEnabled() && state.persona.bRestored)
		{
			if (success)
			{
				if (playerbot_persona::OnValuableDrop(state.persona.mood))
					state.persona.bDirty = true;
			}
			else
				LowerPlayerBotMoodForDayGoal(state.persona);
		}
		sys_log(0, "PLAYERBOT_DAY_GOAL: %s pid=%u name=%s kind=%u difficulty=%u progress=%d/%d minutes=%u mood=%s->%s",
				success ? "met" : "missed", ch->GetPlayerID(), ch->GetName(), (unsigned int)g.kind,
				(unsigned int)g.difficulty, g.progress, g.target, (dwNow - g.startAt) / 60000,
				GetPlayerBotMoodName(before), GetPlayerBotMoodName(state.persona.mood.mood));
		// A word to whoever stands round, now and then - as a person says it;
		// not for a goal whose time ran out while the bot was away.
		const bool endedAway = !success && g.deadlineWorld > 0 && get_global_time() - g.deadlineWorld > 60;
		if (!endedAway && number(1, 100) <= 60)
		{
			static const char* const kMet[] = { "Jest! Cel na dzis zrobiony :)", "Udalo sie, plan na dzis wykonany!",
				"No i zrobione, co sobie zaplanowalem.", "Cel dnia zaliczony, mozna odpoczac :D" };
			static const char* const kMissed[] = { "Eh, nie wyrobilem sie z planem na dzis...", "Nie udalo sie, trudno. Jutro bedzie lepiej.",
				"Za ambitnie sobie zalozylem, nie wyszlo.", "No nic, cel dnia przepadl." };
			SendPlayerBotLocalChat(ch, success ? kMet[number(0, 3)] : kMissed[number(0, 3)]);
		}
		g.nextDrawAt = dwNow + (DWORD)number((int)PLAYERBOT_DAY_GOAL_REDRAW_MIN_MS, (int)PLAYERBOT_DAY_GOAL_REDRAW_MAX_MS);
		SavePlayerBotDayGoal(ch, g);
	}

	void ManagePlayerBotDayGoal(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead())
			return;
		TPlayerBotDayGoal& g = s_mapPlayerBotDayGoals[ch->GetPlayerID()];
		if (dwNow < g.nextCheckAt && g.sessionSpawn == state.dwSpawnTime)
			return;
		g.nextCheckAt = dwNow + PLAYERBOT_DAY_GOAL_CHECK_MS;
		// A new session: the goal comes back from the bot's flags
		// (MT2009_PLUS_BOT_DAY_GOAL_SAVE_V1) once they have arrived.
		if (g.sessionSpawn != state.dwSpawnTime)
		{
			g = TPlayerBotDayGoal();
			g.sessionSpawn = state.dwSpawnTime;
		}
		if (!g.restored)
		{
			if (!RestorePlayerBotDayGoal(ch, g, dwNow))
			{
				g.nextCheckAt = dwNow + 1000;
				return;
			}
			g.nextCheckAt = dwNow + PLAYERBOT_DAY_GOAL_CHECK_MS;
		}
		if (g.kind == DAY_GOAL_NONE || g.endedAt != 0)
		{
			if (g.nextDrawAt == 0 || dwNow < g.nextDrawAt)
				return;
			g.nextDrawAt = dwNow + (DWORD)number((int)PLAYERBOT_DAY_GOAL_REDRAW_MIN_MS, (int)PLAYERBOT_DAY_GOAL_REDRAW_MAX_MS);
			if (!IsPlayerBotDayGoalCandidate(ch, state) || number(1, 100) > PLAYERBOT_DAY_GOAL_PERCENT)
				return;
			StartPlayerBotDayGoal(ch, g, dwNow);
			return;
		}
		// The counters the bot's own state answers.
		if (g.kind == DAY_GOAL_LEVEL)
			g.progress = std::max(0, (int)ch->GetLevel() - g.startLevel);
		else if (g.kind == DAY_GOAL_YANG)
			g.progress = (int)std::max<long long>(0, std::min<long long>((long long)ch->GetGold() - g.startGold, 2000000000LL));
		if (g.progress >= g.target)
			EndPlayerBotDayGoal(ch, state, g, true, dwNow);
		else if ((int)(dwNow - g.deadline) >= 0)
			EndPlayerBotDayGoal(ch, state, g, false, dwNow);
		else if (g.progress != g.savedProgress)
			SavePlayerBotDayGoal(ch, g);
	}

	TPlayerBotDayGoal* FindPlayerBotDayGoal(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		std::map<DWORD, TPlayerBotDayGoal>::iterator it = s_mapPlayerBotDayGoals.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotDayGoals.end() || it->second.kind == DAY_GOAL_NONE)
			return NULL;
		return &it->second;
	}

	void AddPlayerBotDayGoalProgress(LPCHARACTER ch, BYTE kind, int amount)
	{
		if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			return;
		TPlayerBotDayGoal* g = FindPlayerBotDayGoal(ch);
		if (!g || g->kind != kind || g->endedAt != 0)
			return;
		g->progress += amount;
		// The end itself waits for the bot's own pass (its state and its mood).
		g->nextCheckAt = 0;
	}

	// The engine's kill note: the killer, and for a stone or a boss everybody
	// who hurt it and the killer's party near it (playerbot_battlepass.h).
	void NotePlayerBotDayGoalKill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || s_mapPlayerBotDayGoals.empty())
			return;
		if (victim->IsStone())
			AddPlayerBotDayGoalProgress(killer, DAY_GOAL_METINS, 1);
		else if (victim->IsMonster())
		{
			AddPlayerBotDayGoalProgress(killer, DAY_GOAL_MONSTERS, 1);
			if (victim->GetMobRank() >= MOB_RANK_BOSS)
				AddPlayerBotDayGoalProgress(killer, DAY_GOAL_BOSS, 1);
		}
	}

	void NotePlayerBotDayGoalSharedKill(LPCHARACTER killer, LPCHARACTER victim, const std::vector<LPCHARACTER>& hurt)
	{
		if (!victim || victim->IsPC() || s_mapPlayerBotDayGoals.empty() ||
				!(victim->IsStone() || victim->GetMobRank() >= MOB_RANK_BOSS))
			return;
		const BYTE kind = victim->IsStone() ? (BYTE)DAY_GOAL_METINS : (BYTE)DAY_GOAL_BOSS;
		std::set<DWORD> done;
		if (killer && killer->IsPC())
			done.insert(killer->GetPlayerID());
		for (size_t i = 0; i < hurt.size(); ++i)
		{
			LPCHARACTER c = hurt[i];
			if (!c || !c->IsPC() || c->GetMapIndex() != victim->GetMapIndex() || !done.insert(c->GetPlayerID()).second)
				continue;
			AddPlayerBotDayGoalProgress(c, kind, 1);
		}
	}

	void NotePlayerBotDayGoalRefine(LPCHARACTER ch, int newPlus)
	{
		if (newPlus > 0)
			AddPlayerBotDayGoalProgress(ch, DAY_GOAL_REFINE, 1);
	}

	// What it says over the head, Polish or English, in the goal's blue.
	void FormatPlayerBotDayGoalYang(long long v, char* out, size_t size)
	{
		if (v >= 1000000)
			snprintf(out, size, "%lld.%lldkk", v / 1000000, (v % 1000000) / 100000);
		else if (v >= 1000)
			snprintf(out, size, "%lldk", v / 1000);
		else
			snprintf(out, size, "%lld", v);
	}

	bool GetPlayerBotDayGoalTag(LPCHARACTER ch, bool en, char* out, size_t size)
	{
		const TPlayerBotDayGoal* g = FindPlayerBotDayGoal(ch);
		if (!g || !out || size == 0)
			return false;
		const DWORD dwNow = get_dword_time();
		if (g->endedAt != 0 && dwNow - g->endedAt > PLAYERBOT_DAY_GOAL_SHOW_END_MS)
			return false;
		static const char* const kDiffPl[3] = { "latwy", "sredni", "trudny" };
		static const char* const kDiffEn[3] = { "easy", "medium", "hard" };
		const char* diff = en ? kDiffEn[g->difficulty % 3] : kDiffPl[g->difficulty % 3];
		char what[64];
		switch (g->kind)
		{
			case DAY_GOAL_METINS: snprintf(what, sizeof(what), en ? "Metins %d/%d" : "Metiny %d/%d", std::min(g->progress, g->target), g->target); break;
			case DAY_GOAL_LEVEL: snprintf(what, sizeof(what), en ? "levels %d/%d" : "poziomy %d/%d", std::min(g->progress, g->target), g->target); break;
			case DAY_GOAL_BOSS: snprintf(what, sizeof(what), en ? "bosses %d/%d" : "bossy %d/%d", std::min(g->progress, g->target), g->target); break;
			case DAY_GOAL_REFINE: snprintf(what, sizeof(what), en ? "refines %d/%d" : "ulepszenia %d/%d", std::min(g->progress, g->target), g->target); break;
			case DAY_GOAL_MONSTERS: snprintf(what, sizeof(what), en ? "monsters %d/%d" : "potwory %d/%d", std::min(g->progress, g->target), g->target); break;
			case DAY_GOAL_YANG:
			{
				char have[24], want[24];
				FormatPlayerBotDayGoalYang(std::min<long long>(g->progress, g->target), have, sizeof(have));
				FormatPlayerBotDayGoalYang(g->target, want, sizeof(want));
				snprintf(what, sizeof(what), "yang %s/%s", have, want);
				break;
			}
			default: return false;
		}
		if (g->endedAt != 0)
			snprintf(out, size, "%s[%s: %s - %s]|r ", PLAYERBOT_DAY_GOAL_COLOUR, en ? "Daily Goal" : "Cel Dnia", what,
					g->success ? (en ? "done!" : "zrobiony!") : (en ? "missed" : "nieudany"));
		else
			snprintf(out, size, "%s[%s (%s): %s]|r ", PLAYERBOT_DAY_GOAL_COLOUR, en ? "Daily Goal" : "Cel Dnia", diff, what);
		return true;
	}

	// A number that changes whenever the tag would: the status line is sent
	// again on a change only (ManagePlayerBotStatusOverhead).
	DWORD GetPlayerBotDayGoalKey(LPCHARACTER ch)
	{
		const TPlayerBotDayGoal* g = FindPlayerBotDayGoal(ch);
		if (!g)
			return 0;
		return ((DWORD)g->kind << 28) ^ ((DWORD)g->progress * 2654435761U) ^ (g->endedAt != 0 ? 0x80000000U : 0) ^
				(g->success ? 0x40000000U : 0) ^ g->startAt;
	}
}

#endif
