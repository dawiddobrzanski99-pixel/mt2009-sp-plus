#pragma once
// MT2009_PLUS_GM_DUNGEON_RESET_V1: a GM resets a character's daily dungeon limit (the owner,
// 6 October: "Dodaj komende dla GM-a, ktora bedzie resetowala limit dziennych dungeonow dla
// jakiejs postaci").
//
//   /dungeon_reset <name> [dungeon|all]        (Polish alias: /resetdungi)
//
// GM_HIGH_WIZARD, as the other GM switches of ours (/lochy reload, /goblin gm, /ingame_event gm).
// The dungeon is a key of dungeon_info.txt (biblioteka, wukong, razador, skorpion, nemere, smok,
// dzungla, katakumby) or its quest's name; none or "all" means every one.
//
// What is reset: the day's count of expeditions the quests' pay_entry() keeps, <quest>.runs
// (read only while <quest>.day is today, Polish midnight) - the five a day of the Arezzo
// dungeons, Razador, Nemere and the Blue Dragon. A playerbot also loses the rest it takes between
// runs: the dungeon's cooldown flag (<quest>.entry, devilcatacomb_zone.last_exit_time - a person
// no longer waits, MT2009_PLUS_DUNGEON_NO_PLAYER_COOLDOWN_V1, and his entry flag is the rejoin's,
// so it is left alone) and the core's own rest after a bot run (playerbot_dungeon_runs.h). The
// Demon Tower has no limit.
//
// Where the character is:
//   - on this core: the flags are written at once, the GM gets what the counts were, the
//     character "GM zresetowal Twoj limit dziennych dungeonow";
//   - on another core or channel (P2P): a row "DG_RESET" in player.web_admin_queue, carried out
//     within about three seconds by web_admin.quest on the character's own core (the same
//     queue the Seban panel's actions use) - the character gets the same message there;
//   - offline: its <quest>.runs rows in player.quest are deleted (a zero flag is no row, as the
//     db core's QUERY_QUEST_SAVE writes it), so the next login loads a fresh day.
// The Seban panel's character page has the same reset ("Limit dungeonow", app.py).

namespace mt2009_dgreset
{
	struct TDef
	{
		const char* key;	// dungeon_info.txt's key
		const char* quest;	// the quest whose flags these are
		bool daily;		// <quest>.day / <quest>.runs: a daily limit
		const char* rest;	// a bot's cooldown flag
		const char* name;	// for the GM's reply (CP1250)
	};

	const TDef DEFS[] = {
		{ "biblioteka", "biblioteka_wiedzy", true, "entry", "Biblioteka Wiedzy" },
		{ "wukong", "wzgorze_wukonga", true, "entry", "Wzg\xf3rze Wukonga" },
		{ "razador", "razador_dungeon", true, "entry", "Razador" },
		{ "skorpion", "ruiny_skorpiona", true, "entry", "Ruiny Skorpiona" },
		{ "nemere", "nemere_dungeon", true, "entry", "Nemere" },
		{ "smok", "blue_dragon_lair", true, "entry", "Niebieski Smok" },
		{ "dzungla", "starozytna_dzungla", true, "entry", "Staro\xbfytna D\xbfungla" },
		{ "atlantyda", "ruiny_atlantydy", true, "entry", "Ruiny Atlantydy" },	// MT2009_PLUS_ATLANTYDA_V1
		{ "katakumby", "devilcatacomb_zone", false, "last_exit_time", "Katakumby Diab\xb3" "a" },
	};
	const size_t DEF_COUNT = sizeof(DEFS) / sizeof(DEFS[0]);

	int Today()
	{
		return (int)((get_global_time() + 7200) / 86400);
	}

	// -1: unknown; DEF_COUNT: all.
	int Pick(const char* arg)
	{
		if (!arg || !*arg || !strcasecmp(arg, "all") || !strcasecmp(arg, "wszystko") || !strcasecmp(arg, "wszystkie"))
			return (int)DEF_COUNT;
		for (size_t i = 0; i < DEF_COUNT; ++i)
			if (!strcasecmp(arg, DEFS[i].key) || !strcasecmp(arg, DEFS[i].quest))
				return (int)i;
		return -1;
	}

	bool Selected(int pick, size_t i)
	{
		return pick == (int)DEF_COUNT || pick == (int)i;
	}

	// The flags of a character on this core. `what` gets "Name 3/5, ..." of the counts reset.
	void ResetOnline(LPCHARACTER tch, int pick, std::string& what, bool& bot)
	{
		const int today = Today();
		bot = tch->GetDesc() && tch->GetDesc()->IsBot();
		for (size_t i = 0; i < DEF_COUNT; ++i)
		{
			if (!Selected(pick, i))
				continue;
			const TDef& d = DEFS[i];
			const std::string q(d.quest);
			if (d.daily)
			{
				const int runs = tch->GetQuestFlag(q + ".day") == today ? tch->GetQuestFlag(q + ".runs") : 0;
				if (tch->GetQuestFlag(q + ".runs") != 0)
					tch->SetQuestFlag(q + ".runs", 0);
				if (runs > 0)
				{
					char buf[96];
					snprintf(buf, sizeof(buf), "%s%s %d", what.empty() ? "" : ", ", d.name, runs);
					what += buf;
				}
			}
			if (bot && d.rest && tch->GetQuestFlag(q + "." + d.rest) != 0)
				tch->SetQuestFlag(q + "." + d.rest, 0);
		}
		if (bot)
			s_mapPlayerBotDgRunRest.erase(tch->GetPlayerID());
	}

	void Escape(char* out, size_t size, const char* in)
	{
		size_t n = 0;
		for (const char* c = in; *c && n + 2 < size; ++c)
		{
			if (*c == '\\' || *c == '\'')
				out[n++] = '\\';
			out[n++] = *c;
		}
		out[n] = '\0';
	}

	// "'a','b',..." - the quests of the pick that have a daily limit.
	std::string QuestList(int pick)
	{
		std::string list;
		for (size_t i = 0; i < DEF_COUNT; ++i)
		{
			if (!Selected(pick, i) || !DEFS[i].daily)
				continue;
			if (!list.empty())
				list += ",";
			list += "'";
			list += DEFS[i].quest;
			list += "'";
		}
		return list;
	}
}

void GmDungeonResetCommand(LPCHARACTER ch, const char* argument)
{
	using namespace mt2009_dgreset;
	if (!ch || ch->GetGMLevel() < GM_HIGH_WIZARD)
		return;
	char name[CHARACTER_NAME_MAX_LEN + 1] = "", which[32] = "";
	const char* rest = one_argument(argument, name, sizeof(name));
	one_argument(rest, which, sizeof(which));
	if (!*name)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "/dungeon_reset <nick> [loch|all] (/resetdungi) - zeruje dzisiejszy limit wypraw postaci.");
		ch->ChatPacket(CHAT_TYPE_INFO, "Lochy: biblioteka, wukong, razador, skorpion, nemere, smok, dzungla, atlantyda, katakumby (tylko odpoczynek bota); bez lochu albo all - wszystkie.");
		return;
	}
	const int pick = Pick(which);
	if (pick < 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nieznany loch \"%s\". Lochy: biblioteka, wukong, razador, skorpion, nemere, smok, dzungla, atlantyda, katakumby albo all.", which);
		return;
	}
	const char* scope = pick == (int)DEF_COUNT ? "wszystkich loch\xf3w" : DEFS[pick].name;

	// On this core.
	LPCHARACTER tch = CHARACTER_MANAGER::instance().FindPC(name);
	if (tch && tch->IsPC())
	{
		std::string what;
		bool bot = false;
		ResetOnline(tch, pick, what, bot);
		ch->ChatPacket(CHAT_TYPE_INFO, "Zresetowano dzienny limit (%s) postaci %s%s: %s.", scope, tch->GetName(),
				bot ? " (bot, tak\xbf" "e odpoczynek)" : "", what.empty() ? "dzi\x9c nie by\xb3" "o wypraw" : what.c_str());
		if (tch != ch)
			tch->ChatPacket(CHAT_TYPE_INFO, "GM zresetowa\xb3 Tw\xf3j limit dziennych dungeon\xf3w.");
		sys_log(0, "GM_DUNGEON_RESET: %s reset %s of %s (online): %s", ch->GetName(), pick == (int)DEF_COUNT ? "all" : DEFS[pick].key,
				tch->GetName(), what.c_str());
		return;
	}

	char escName[CHARACTER_NAME_MAX_LEN * 2 + 1];
	Escape(escName, sizeof(escName), name);
	char query[1024];

	// On another core: the queue web_admin.quest serves there.
	CCI* cci = P2P_MANAGER::instance().Find(name);
	if (cci)
	{
		snprintf(query, sizeof(query),
				"INSERT INTO player.web_admin_queue (player_name,cmd,arg1,arg2) VALUES ('%s','DG_RESET','%s','')",
				escName, pick == (int)DEF_COUNT ? "all" : DEFS[pick].key);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s jest na innym rdzeniu (kana\xb3 %u), a kolejka player.web_admin_queue nie przyj\xea\xb3" "a zlecenia.",
					cci->szName, (unsigned) cci->bChannel);
			return;
		}
		ch->ChatPacket(CHAT_TYPE_INFO, "%s jest na kanale %u - reset (%s) zlecony; wykona si\xea tam w ci\xb9gu kilku sekund.",
				cci->szName, (unsigned) cci->bChannel, scope);
		sys_log(0, "GM_DUNGEON_RESET: %s queued %s for %s (channel %u)", ch->GetName(),
				pick == (int)DEF_COUNT ? "all" : DEFS[pick].key, cci->szName, (unsigned) cci->bChannel);
		return;
	}

	// Offline: the saved flags.
	snprintf(query, sizeof(query), "SELECT id, name FROM player.player WHERE name='%s' LIMIT 1", escName);
	std::unique_ptr<SQLMsg> who(AccountDB::instance().DirectQuery(query));
	if (!who.get() || who->uiSQLErrno != 0 || !who->Get() || !who->Get()->pSQLResult || who->Get()->uiNumRows == 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie ma postaci %s.", name);
		return;
	}
	MYSQL_ROW row = mysql_fetch_row(who->Get()->pSQLResult);
	DWORD pid = 0;
	if (!row || !row[0] || !str_to_number(pid, row[0]) || !pid)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie ma postaci %s.", name);
		return;
	}
	const std::string realName = row[1] ? row[1] : name;
	const std::string quests = QuestList(pick);
	if (quests.empty())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s: %s nie ma dziennego limitu (odpoczynek jest tylko botom w grze).", realName.c_str(), scope);
		return;
	}

	// What it was today, for the reply.
	std::string what;
	snprintf(query, sizeof(query),
			"SELECT r.szName, r.lValue FROM player.quest r JOIN player.quest d ON d.dwPID = r.dwPID AND d.szName = r.szName "
			"AND d.szState = 'day' AND d.lValue = %d WHERE r.dwPID = %u AND r.szState = 'runs' AND r.lValue > 0 AND r.szName IN (%s)",
			Today(), pid, quests.c_str());
	std::unique_ptr<SQLMsg> was(AccountDB::instance().DirectQuery(query));
	if (was.get() && was->uiSQLErrno == 0 && was->Get() && was->Get()->pSQLResult)
	{
		MYSQL_ROW r;
		while (NULL != (r = mysql_fetch_row(was->Get()->pSQLResult)))
		{
			const char* label = r[0] ? r[0] : "?";
			for (size_t i = 0; i < DEF_COUNT; ++i)
				if (r[0] && !strcmp(r[0], DEFS[i].quest))
					label = DEFS[i].name;
			if (!what.empty())
				what += ", ";
			what += label;
			what += " ";
			what += r[1] ? r[1] : "?";
		}
	}

	snprintf(query, sizeof(query),
			"DELETE FROM player.quest WHERE dwPID = %u AND szState = 'runs' AND szName IN (%s)", pid, quests.c_str());
	std::unique_ptr<SQLMsg> del(AccountDB::instance().DirectQuery(query));
	if (!del.get() || del->uiSQLErrno != 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s (offline): zapis do player.quest si\xea nie uda\xb3.", realName.c_str());
		return;
	}
	ch->ChatPacket(CHAT_TYPE_INFO, "Zresetowano dzienny limit (%s) postaci %s (offline): %s.", scope, realName.c_str(),
			what.empty() ? "dzi\x9c nie by\xb3" "o wypraw" : what.c_str());
	sys_log(0, "GM_DUNGEON_RESET: %s reset %s of %s (offline, pid %u): %s", ch->GetName(),
			pick == (int)DEF_COUNT ? "all" : DEFS[pick].key, realName.c_str(), pid, what.c_str());
}
