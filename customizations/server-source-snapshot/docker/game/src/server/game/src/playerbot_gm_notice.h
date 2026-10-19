#ifndef __INC_METIN2_PLAYERBOT_GM_NOTICE_H__
#define __INC_METIN2_PLAYERBOT_GM_NOTICE_H__

// MT2009_PLUS_GM_SM_EVENT_V1 - the bots and a GM's notice.
//
// The owner, 6 October: "Jak sie napisze cos z GM, to niech boty odpowiadaja,
// szczegolnie jak GM napisze /b !SM, to wtedy niech wszystkie boty spamia na
// wolaj SM przez 30-40 sekund." The old event: a GM announces "!SM" and the
// first to write "SM" on the shout wins the Dragon Coins.
//
//   - THE SM RACE. A GM's notice ("/b" = big_notice, "/n" = notice,
//     gm_notice, the map notices) or a GM's own shout with "!SM" in it
//     ("!sm", "! SM"; not "!smok") opens a window of 30-40 s on every core:
//     the GM's core from the command (cmd_gm.cpp), the others from the P2P
//     notice (CInputP2P::Notice) - each core its own bots. 30-60% of the
//     core's bots that may shout (IsPlayerBotPublicSpeaker, the shout's level)
//     take part, at most GM_SM_MAX_BOTS; each starts 0-3 s in and shouts
//     "SM" (or "sm", "SM!", "SMMM", "SM SM", now and then "SMka") 2-6 times,
//     3-10 s apart, on its own kingdom's shout. A core sends at most
//     GM_SM_SHOUTS_PER_SEC of them a second; a line held back past the window
//     is dropped.
//   - THE REACTIONS. Any other GM notice: now and then (GM_REACT_PERCENT) 1-4
//     bots of the core say a short line on their shout 2-12 s later ("o gm",
//     "co jest?", "eventy?"), at most one round every GM_REACT_GAP_MS. From
//     another core only a big notice or a GM notice counts - the plain
//     notice there is also the server's own (the events, the raids).
//
// The SHOUT_ANSWER switch (playerbot_config.h) at 0 silences both, as it
// silences the bots' answers on the shout channel.
//
// An implementation fragment: include it once, after playerbot_chat_world.h.

namespace
{
	const DWORD GM_SM_WINDOW_MIN_MS = 30000;
	const DWORD GM_SM_WINDOW_MAX_MS = 40000;
	const int GM_SM_JOIN_MIN_PERCENT = 30;
	const int GM_SM_JOIN_MAX_PERCENT = 60;
	const size_t GM_SM_MAX_BOTS = 90;
	const int GM_SM_START_SPREAD_MS = 3000;
	const int GM_SM_GAP_MIN_MS = 3000;
	const int GM_SM_GAP_MAX_MS = 10000;
	const int GM_SM_SHOUTS_PER_SEC = 8;
	const int GM_REACT_PERCENT = 55;
	const DWORD GM_REACT_GAP_MS = 45000;

	struct TPlayerBotSMShouter
	{
		DWORD pid;
		DWORD due;
		int left;
	};
	std::vector<TPlayerBotSMShouter> s_vecPlayerBotSMShouters;
	DWORD s_dwPlayerBotSMEnd = 0;
	bool s_bPlayerBotSMActive = false;
	unsigned int s_uPlayerBotSMLines = 0;
	// The core's own shout budget for the race: a token a 1/8 s, at most a second's worth.
	DWORD s_dwPlayerBotSMBudgetAt = 0;
	int s_iPlayerBotSMBudget = 0;

	struct TPlayerBotGMReaction
	{
		DWORD pid;
		DWORD due;
		const char* line;
	};
	std::vector<TPlayerBotGMReaction> s_vecPlayerBotGMReactions;
	DWORD s_dwPlayerBotGMReactAt = 0;

	// "!SM", "!sm", "! SM", "!SM!" - not "!smok", "!smocze".
	bool PlayerBotNoticeCallsSM(const char* text)
	{
		if (!text)
			return false;
		for (const char* p = text; *p; ++p)
		{
			if (*p != '!')
				continue;
			const char* q = p + 1;
			while (*q == ' ')
				++q;
			if ((q[0] == 's' || q[0] == 'S') && (q[1] == 'm' || q[1] == 'M') &&
					!isalnum((unsigned char) q[2]) && !((unsigned char) q[2] & 0x80))
				return true;
		}
		return false;
	}

	const char* PickPlayerBotSMLine()
	{
		const int r = number(1, 100);
		if (r <= 45) return "SM";
		if (r <= 63) return "sm";
		if (r <= 75) return "SM!";
		if (r <= 83) return "SMMM";
		if (r <= 90) return "SM SM";
		if (r <= 94) return "Sm";
		if (r <= 97) return "SM!!";
		return "SMka";
	}

	const char* const s_apszPlayerBotGMReactions[] =
	{
		"o gm", "co jest?", "eventy?", "o gm na serwie", "jakis event?", "elo gm", "witaj gm",
		"co sie dzieje?", "gm pozdro xD", "a co to?", "ooo cos sie dzieje", "kiedy event?",
		"gm daj cos xD", "o, gm", "event bedzie?", "siema gm", "co za event?", "gm <3",
	};

	bool PlayerBotGMChannelOpen()
	{
		return s_iPlayerBotShoutAnswerPercent > 0;
	}

	// The race's start - once, while no race is running on this core.
	void StartPlayerBotSMRace(DWORD dwNow, const char* source)
	{
		if (!PlayerBotGMChannelOpen() || s_bPlayerBotSMActive)
			return;
		const int joinPercent = number(GM_SM_JOIN_MIN_PERCENT, GM_SM_JOIN_MAX_PERCENT);
		std::vector<DWORD> pids;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!c || !IsPlayerBotPublicSpeaker(c, g_iShoutLimitLevel) || c->GetEmpire() < 1 || c->GetEmpire() > 3)
				continue;
			if (number(1, 100) <= joinPercent)
				pids.push_back(it->first);
		}
		// Too many: a random GM_SM_MAX_BOTS of them.
		for (size_t i = 0; i < pids.size() && i < GM_SM_MAX_BOTS; ++i)
			std::swap(pids[i], pids[i + number(0, (int)(pids.size() - i - 1))]);
		if (pids.size() > GM_SM_MAX_BOTS)
			pids.resize(GM_SM_MAX_BOTS);
		s_vecPlayerBotSMShouters.clear();
		for (size_t i = 0; i < pids.size(); ++i)
		{
			TPlayerBotSMShouter s;
			s.pid = pids[i];
			s.due = dwNow + number(0, GM_SM_START_SPREAD_MS);
			s.left = number(2, 6);
			s_vecPlayerBotSMShouters.push_back(s);
		}
		s_dwPlayerBotSMEnd = dwNow + number((int)GM_SM_WINDOW_MIN_MS, (int)GM_SM_WINDOW_MAX_MS);
		s_bPlayerBotSMActive = true;
		s_uPlayerBotSMLines = 0;
		s_dwPlayerBotSMBudgetAt = dwNow;
		s_iPlayerBotSMBudget = 0;
		// A race is no time for "o gm".
		s_vecPlayerBotGMReactions.clear();
		s_dwPlayerBotGMReactAt = dwNow;
		sys_log(0, "PLAYERBOT_GM_SM: start (%s) bots=%u join=%d%% window=%ums",
				source, (unsigned int)s_vecPlayerBotSMShouters.size(), joinPercent, s_dwPlayerBotSMEnd - dwNow);
	}

	// A short line or two after an ordinary GM notice, rate-limited.
	void StartPlayerBotGMReactions(DWORD dwNow)
	{
		if (!PlayerBotGMChannelOpen() || s_bPlayerBotSMActive)
			return;
		if (s_dwPlayerBotGMReactAt != 0 && dwNow - s_dwPlayerBotGMReactAt < GM_REACT_GAP_MS)
			return;
		if (number(1, 100) > GM_REACT_PERCENT)
			return;
		s_dwPlayerBotGMReactAt = dwNow;
		std::vector<DWORD> pids;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (c && IsPlayerBotPublicSpeaker(c, g_iShoutLimitLevel) && c->GetEmpire() >= 1 && c->GetEmpire() <= 3)
				pids.push_back(it->first);
		}
		const int want = number(1, 4);
		std::vector<const char*> used;
		for (int n = 0; n < want && !pids.empty(); ++n)
		{
			const size_t k = number(0, (int)pids.size() - 1);
			TPlayerBotGMReaction r;
			r.pid = pids[k];
			r.due = dwNow + number(2000, 12000);
			// No two bots of the round with the same line.
			r.line = PickPlayerBotChatLine(s_apszPlayerBotGMReactions);
			for (int tries = 0; tries < 4 && std::find(used.begin(), used.end(), r.line) != used.end(); ++tries)
				r.line = PickPlayerBotChatLine(s_apszPlayerBotGMReactions);
			used.push_back(r.line);
			s_vecPlayerBotGMReactions.push_back(r);
			pids.erase(pids.begin() + k);
		}
	}

	// A notice a GM sent (bFromGM: the command on this core) or another
	// core's notice of the given chat type.
	void ReadPlayerBotGMNotice(const char* text, bool bFromGM, BYTE bChatType)
	{
		if (!text || !*text)
			return;
		const DWORD dwNow = get_dword_time();
		if (PlayerBotNoticeCallsSM(text))
		{
			StartPlayerBotSMRace(dwNow, bFromGM ? "gm" : "p2p");
			return;
		}
		bool react = bFromGM;
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (bChatType == CHAT_TYPE_BIG_NOTICE || bChatType == CHAT_TYPE_GAMEMASTER_NOTICE)
			react = true;
#else
		(void) bChatType;
#endif
		if (react)
			StartPlayerBotGMReactions(dwNow);
	}

	void SendPlayerBotGMLine(LPCHARACTER c, const char* line)
	{
		char msg[CHAT_MAX_LEN + 1];
		snprintf(msg, sizeof(msg), "%s : %s", c->GetName(), line);
		SendPlayerBotShout(msg, c->GetEmpire());
		BattlePassOnShout(c);
	}

	// Once a manager tick (4 a second).
	void ManagePlayerBotGMNotice(DWORD dwNow)
	{
		if (s_bPlayerBotSMActive)
		{
			if ((int)(dwNow - s_dwPlayerBotSMEnd) >= 0 || s_vecPlayerBotSMShouters.empty() || !PlayerBotGMChannelOpen())
			{
				sys_log(0, "PLAYERBOT_GM_SM: end lines=%u", s_uPlayerBotSMLines);
				s_vecPlayerBotSMShouters.clear();
				s_bPlayerBotSMActive = false;
			}
			else
			{
				// The budget: GM_SM_SHOUTS_PER_SEC a second, never more than a second's saved.
				const DWORD step = 1000 / GM_SM_SHOUTS_PER_SEC;
				while (dwNow - s_dwPlayerBotSMBudgetAt >= step)
				{
					s_dwPlayerBotSMBudgetAt += step;
					if (s_iPlayerBotSMBudget < GM_SM_SHOUTS_PER_SEC)
						++s_iPlayerBotSMBudget;
				}
				for (size_t i = 0; i < s_vecPlayerBotSMShouters.size() && s_iPlayerBotSMBudget > 0; )
				{
					TPlayerBotSMShouter& s = s_vecPlayerBotSMShouters[i];
					if ((int)(dwNow - s.due) < 0)
					{
						++i;
						continue;
					}
					LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(s.pid);
					if (!c || !IsPlayerBotPublicSpeaker(c, g_iShoutLimitLevel) || c->GetEmpire() < 1 || c->GetEmpire() > 3)
					{
						s_vecPlayerBotSMShouters.erase(s_vecPlayerBotSMShouters.begin() + i);
						continue;
					}
					SendPlayerBotGMLine(c, PickPlayerBotSMLine());
					--s_iPlayerBotSMBudget;
					++s_uPlayerBotSMLines;
					if (--s.left <= 0)
					{
						s_vecPlayerBotSMShouters.erase(s_vecPlayerBotSMShouters.begin() + i);
						continue;
					}
					s.due = dwNow + number(GM_SM_GAP_MIN_MS, GM_SM_GAP_MAX_MS);
					++i;
				}
			}
		}
		for (size_t i = 0; i < s_vecPlayerBotGMReactions.size(); )
		{
			const TPlayerBotGMReaction& r = s_vecPlayerBotGMReactions[i];
			if ((int)(dwNow - r.due) < 0)
			{
				++i;
				continue;
			}
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(r.pid);
			if (c && PlayerBotGMChannelOpen() && IsPlayerBotPublicSpeaker(c, g_iShoutLimitLevel) &&
					c->GetEmpire() >= 1 && c->GetEmpire() <= 3)
			{
				SendPlayerBotGMLine(c, r.line);
				sys_log(0, "PLAYERBOT_GM_REACT: pid=%u name=%s text=\"%s\"", c->GetPlayerID(), c->GetName(), r.line);
			}
			s_vecPlayerBotGMReactions.erase(s_vecPlayerBotGMReactions.begin() + i);
		}
	}
}

#endif
