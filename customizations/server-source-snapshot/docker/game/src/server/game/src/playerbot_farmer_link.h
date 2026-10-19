#ifndef __INC_METIN2_PLAYERBOT_FARMER_LINK_H__
#define __INC_METIN2_PLAYERBOT_FARMER_LINK_H__

// MT2009_PLUS_FARMER_LINK_V1: every farmer ("dropek") works for a main
// character of its own (the owner, 7 October): "kazdy dropek na serwerze ma
// byc polaczony z postacia innego bota. Dropek pracuje i zarabia yang na
// rozwoj postaci glownej" - of, say, twenty million a medal dropper made, a
// smaller part goes on its own character so it farms better, and the rest
// goes to the one character it is linked to, which develops with it. In the
// end half of the bots should have a farmer of their own, on every ground
// from the first village to the Orc Valley and the Demon Tower, so the table
// of grounds is data, and the panel shows both ends: "DROPEKMEDALI jest
// dropkiem postaci FUBU" and, on FUBU's card, "Dropek: DROPEKMEDALI".
//
//   - the link: player.playerbot_farmer_link, one row a farmer (farmer_pid
//     is the key, main_pid is unique - one farmer a main, one main a
//     farmer), made by the core the farmer plays on, with a main of the same
//     kingdom playing on the same core at that moment, so everything about
//     the main can be asked of the character itself (one bot account holds
//     one character, so "the same account" never applies). The migrator
//     creates the tables too (apply.sh); this file creates and repairs them
//     when they are missing;
//   - who is a farmer: every dropper (IsPlayerBotDropper - medal, M2, M3,
//     Metin, the guild materials dropper, the level-30 weapon dropper, the
//     ornament farmer of the second village's Sworn camps - and
//     the operator's medal cohort), linked as soon as a main can be found;
//     and the spot farmers - ordinary bots given a ground of
//     PLAYERBOT_FARMER_SPOTS for their level, held at its lock (the hook in
//     ManagePlayerBotExpLock) and sent there (the hook in
//     GetPlayerBotFrontierMapForLevelRaw). Their number grows towards the
//     panel's share (target_pct: the share of the other bots that have a
//     farmer, 50 = "polowa botow ma swojego dropka"), one new farmer a core
//     at a time and no more than new_per_hour an hour, never in the first ten
//     minutes of a core, and falls the same way, one released a pass;
//   - the money: the farmer's purse is watched every pass, and of what it
//     grows by (its sales, its counter's takings) keep_pct stays with the
//     farmer - the dropper's own investment (MT2009_PLUS_DROPPER_INVEST_V1)
//     and a spot farmer's ordinary shopping spend it - and the rest is owed
//     to the main. Every ten to fifteen minutes the owed yang over
//     min_transfer (or all of it, once an hour) leaves the farmer's purse,
//     keeping reserve for its potions, into the link's "pending" - the bank
//     between two cores - and the main takes it the next pass it is online
//     on any core, within its yang limit (MT2009_PLUS_YANG_LIMITS_V1: 2 bn
//     for a bot). Nothing in this code base moves yang between two bots - the
//     companion's "eq yang" (MovePlayerBotSidekickYang) is the one transfer
//     there is, and it is a server-side one with a CharLog line - and a
//     meeting and a trade window would need both bots on one map of one
//     core, which a farmer in the Monkey Dungeon and a main in the Grotto
//     never are; so it is the same: a transfer, a PLAYERBOT_FARMER line in
//     the syslog, a CharLog line and a row of player.playerbot_farmer_transfer,
//     with the totals on the link for the panel. The main spends it the way
//     it spends any yang: its gear upgrades, the counters, the shops;
//   - the end: a dropper that stops being one, or a spot farmer the share
//     no longer wants, is unlinked; what it had already sent still reaches
//     the main (the row stays inactive until it has). A main that turns out
//     to be no main (a dropper, a companion, a shouter) lets its farmer go,
//     and the farmer is linked again elsewhere at its core's next pass;
//   - the switch: player.playerbot_farmer_config (the panel's "Dropki"
//     page). Off, nobody new is linked, nothing is skimmed and the spot
//     farmers' grounds and locks are lifted; what is pending is still paid
//     out.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, after playerbot_l30_dropper.h (it asks the checklist's
// eligibility and every cohort before it).

namespace
{
	// The grounds of the spot farmers: the key the panel names, the map (0 =
	// its own villages, where its level puts it), the level it is chosen from
	// and the level it is held at. The bands sit inside the operator's map
	// table (playerbot_progression_rules.h, MAP_DEFAULTS) so the ground is
	// one the bot's level would take it to anyway. Append rows; the key is
	// what the database stores.
	struct TPlayerBotFarmerSpot
	{
		const char* key;
		long map;
		BYTE minLevel;
		BYTE lock;
	};

	const TPlayerBotFarmerSpot PLAYERBOT_FARMER_SPOTS[] = {
		{ "m1",          0,                          8, 14 },
		{ "m2",          0,                         18, 26 },
		{ "orc_islands", PLAYERBOT_MAP_ORC_VALLEY,  30, 34 },
		{ "desert",      PLAYERBOT_MAP_DESERT,      36, 41 },
		{ "orc_valley",  PLAYERBOT_MAP_ORC_VALLEY,  40, 46 },
		{ "sohan",       PLAYERBOT_MAP_SOHAN,       48, 54 },
		{ "spider1",     PLAYERBOT_MAP_SPIDER_V1,   50, 56 },
		{ "hwang",       PLAYERBOT_MAP_HWANG,       53, 59 },
		{ "demon_tower", PLAYERBOT_MAP_DEMON_TOWER, 57, 63 },
		{ "fire_land",   PLAYERBOT_MAP_FIRE_LAND,   66, 72 },
		{ "red_forest",  PLAYERBOT_MAP_RED_FOREST,  74, 79 },
	};
	const int PLAYERBOT_FARMER_SPOT_COUNT = (int)(sizeof(PLAYERBOT_FARMER_SPOTS) / sizeof(PLAYERBOT_FARMER_SPOTS[0]));

	enum EPlayerBotFarmerKind
	{
		PLAYERBOT_FARMER_KIND_NONE = 0,
		PLAYERBOT_FARMER_KIND_MEDAL,
		PLAYERBOT_FARMER_KIND_M2,
		PLAYERBOT_FARMER_KIND_M3,
		PLAYERBOT_FARMER_KIND_METIN,
		PLAYERBOT_FARMER_KIND_GUILD,
		PLAYERBOT_FARMER_KIND_L30,
		PLAYERBOT_FARMER_KIND_SPOT,
		PLAYERBOT_FARMER_KIND_ORNAMENT, // MT2009_PLUS_ORNAMENT_FARMERS_V1 (appended: the key is stored)
		PLAYERBOT_FARMER_KIND_COUNT
	};

	const char* const PLAYERBOT_FARMER_KIND_KEYS[PLAYERBOT_FARMER_KIND_COUNT] = {
		"", "medal", "m2", "m3", "metin", "guild", "l30", "spot", "ornament"
	};

	const DWORD PLAYERBOT_FARMER_PASS_MS = 60 * 1000;
	const DWORD PLAYERBOT_FARMER_SETTLE_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_FLUSH_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_SEND_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_SEND_JITTER_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_SEND_ALL_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_RELEASE_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_FARMER_PRUNE_MS = 60 * 60 * 1000;
	// A main stands at least this far over its farmer when one so far over
	// it plays on the core; else the highest one over it.
	const int PLAYERBOT_FARMER_MAIN_LEVEL_GAP = 5;
	const int PLAYERBOT_FARMER_MAIN_MIN_LEVEL = 10;
	// Droppers linked in one pass, at most: each is a query or two.
	const int PLAYERBOT_FARMER_LINKS_PER_PASS = 25;
	const DWORD PLAYERBOT_FARMER_SEED = 0x46524d4cU;

	struct TPlayerBotFarmerConfig
	{
		bool enabled;
		int targetPct;
		int keepPct;
		int newPerHour;
		long long minTransfer;
		long long reserve;
	};

	TPlayerBotFarmerConfig s_kPlayerBotFarmerConfig = { true, 50, 30, 12, 500000LL, 250000LL };

	struct TPlayerBotFarmerLink
	{
		DWORD main;
		BYTE empire;
		BYTE kind;
		int spot;            // PLAYERBOT_FARMER_SPOTS index of a spot farmer, else -1
		std::string spotKey; // as stored
		bool active;
		long long owed;
		long long pending;
	};

	typedef std::map<DWORD, TPlayerBotFarmerLink> TPlayerBotFarmerLinkMap;
	TPlayerBotFarmerLinkMap s_mapPlayerBotFarmerLinks;   // by the farmer's pid
	std::map<DWORD, DWORD> s_mapPlayerBotFarmerByMain;   // main -> farmer, inactive rows too

	// What this core knows of a farmer's purse since it came here.
	struct TPlayerBotFarmerPurse
	{
		long long baseline;
		long long gain;
		DWORD nextFlush;
		DWORD nextSend;
		DWORD lastSend;
	};
	std::map<DWORD, TPlayerBotFarmerPurse> s_mapPlayerBotFarmerPurse;

	bool s_bPlayerBotFarmerTables = false;
	DWORD s_dwPlayerBotFarmerFirstPass = 0;
	DWORD s_dwPlayerBotFarmerNextPass = 0;
	DWORD s_dwPlayerBotFarmerNextCensus = 0;
	DWORD s_dwPlayerBotFarmerNextNew = 0;
	DWORD s_dwPlayerBotFarmerNextRelease = 0;
	DWORD s_dwPlayerBotFarmerNextPrune = 0;
	// Since the last census: yang sent and taken on this core, transfers.
	long long s_llPlayerBotFarmerSent = 0;
	long long s_llPlayerBotFarmerTaken = 0;
	int s_iPlayerBotFarmerSends = 0;
	int s_iPlayerBotFarmerTakes = 0;

	int FindPlayerBotFarmerSpot(const char* key)
	{
		if (!key || !*key)
			return -1;
		for (int i = 0; i < PLAYERBOT_FARMER_SPOT_COUNT; ++i)
			if (!strcmp(PLAYERBOT_FARMER_SPOTS[i].key, key))
				return i;
		return -1;
	}

	BYTE FindPlayerBotFarmerKind(const char* key)
	{
		if (!key || !*key)
			return PLAYERBOT_FARMER_KIND_NONE;
		for (int i = 1; i < PLAYERBOT_FARMER_KIND_COUNT; ++i)
			if (!strcmp(PLAYERBOT_FARMER_KIND_KEYS[i], key))
				return (BYTE)i;
		return PLAYERBOT_FARMER_KIND_NONE;
	}

	// ---------------------------------------------------------------------
	// Asked every tick by the lock and the travel: cheap map lookups.
	// ---------------------------------------------------------------------

	const TPlayerBotFarmerSpot* GetPlayerBotFarmerSpotOf(DWORD pid)
	{
		if (!s_kPlayerBotFarmerConfig.enabled)
			return NULL;
		TPlayerBotFarmerLinkMap::const_iterator it = s_mapPlayerBotFarmerLinks.find(pid);
		if (it == s_mapPlayerBotFarmerLinks.end() || !it->second.active ||
				it->second.kind != PLAYERBOT_FARMER_KIND_SPOT ||
				it->second.spot < 0 || it->second.spot >= PLAYERBOT_FARMER_SPOT_COUNT)
			return NULL;
		return &PLAYERBOT_FARMER_SPOTS[it->second.spot];
	}

	// The level a spot farmer is held at, or 0 (ManagePlayerBotExpLock).
	BYTE GetPlayerBotFarmerSpotLock(DWORD pid)
	{
		const TPlayerBotFarmerSpot* spot = GetPlayerBotFarmerSpotOf(pid);
		return spot ? spot->lock : 0;
	}

	// The map a spot farmer hunts, or 0 for its villages and for everybody
	// else (GetPlayerBotFrontierMapForLevelRaw).
	long GetPlayerBotFarmerSpotMap(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		const TPlayerBotFarmerSpot* spot = GetPlayerBotFarmerSpotOf(ch->GetPlayerID());
		return spot && spot->map != 0 && ch->GetLevel() >= spot->minLevel ? spot->map : 0;
	}

	bool IsPlayerBotFarmerPID(DWORD pid)
	{
		TPlayerBotFarmerLinkMap::const_iterator it = s_mapPlayerBotFarmerLinks.find(pid);
		return it != s_mapPlayerBotFarmerLinks.end() && it->second.active;
	}

	bool IsPlayerBotFarmerMainPID(DWORD pid)
	{
		return s_mapPlayerBotFarmerByMain.find(pid) != s_mapPlayerBotFarmerByMain.end();
	}

	// ---------------------------------------------------------------------
	// The tables.
	// ---------------------------------------------------------------------

	// AccountDB's DirectQuery takes a finished statement; the link's are
	// formatted here (pids and fixed keys only - nothing a person typed).
	std::unique_ptr<SQLMsg> PlayerBotFarmerQuery(const char* format, ...)
	{
		char query[2048];
		va_list args;
		va_start(args, format);
		vsnprintf(query, sizeof(query), format, args);
		va_end(args);
		return AccountDB::instance().DirectQuery(query);
	}

	bool PlayerBotFarmerSqlOk(const std::unique_ptr<SQLMsg>& msg)
	{
		return msg.get() && msg->uiSQLErrno == 0 && msg->Get();
	}

	bool PlayerBotFarmerSqlOne(const std::unique_ptr<SQLMsg>& msg)
	{
		return PlayerBotFarmerSqlOk(msg) && msg->Get()->uiAffectedRows == 1;
	}

	// The migrator makes them (apply.sh); a core that starts before a migrator
	// of this version has run, or a database somebody dropped them from,
	// still gets them. Asked until it works, then never again.
	bool EnsurePlayerBotFarmerTables()
	{
		if (s_bPlayerBotFarmerTables)
			return true;
		std::unique_ptr<SQLMsg> link(PlayerBotFarmerQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_farmer_link ("
				"farmer_pid INT UNSIGNED NOT NULL PRIMARY KEY, "
				"main_pid INT UNSIGNED NOT NULL, "
				"empire TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"kind VARCHAR(16) NOT NULL DEFAULT '', "
				"spot VARCHAR(24) NOT NULL DEFAULT '', "
				"active TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"keep_pct TINYINT UNSIGNED NOT NULL DEFAULT 30, "
				"earned BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"kept BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"owed BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"pending BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"transferred BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"transfers INT UNSIGNED NOT NULL DEFAULT 0, "
				"linked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
				"last_sent DATETIME NULL, "
				"last_received DATETIME NULL, "
				"updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
				"UNIQUE KEY main_pid (main_pid), KEY active_kind (active, kind)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> transfer(PlayerBotFarmerQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_farmer_transfer ("
				"id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, "
				"at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
				"farmer_pid INT UNSIGNED NOT NULL, "
				"main_pid INT UNSIGNED NOT NULL, "
				"amount BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"stage TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"KEY at_idx (at), KEY farmer_idx (farmer_pid), KEY main_idx (main_pid)) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> config(PlayerBotFarmerQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_farmer_config ("
				"id TINYINT UNSIGNED NOT NULL PRIMARY KEY, "
				"enabled TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"target_pct TINYINT UNSIGNED NOT NULL DEFAULT 50, "
				"keep_pct TINYINT UNSIGNED NOT NULL DEFAULT 30, "
				"new_per_hour SMALLINT UNSIGNED NOT NULL DEFAULT 12, "
				"min_transfer BIGINT UNSIGNED NOT NULL DEFAULT 500000, "
				"reserve BIGINT UNSIGNED NOT NULL DEFAULT 250000, "
				"updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB"));
		std::unique_ptr<SQLMsg> row(PlayerBotFarmerQuery(
				"INSERT IGNORE INTO player.playerbot_farmer_config (id) VALUES (1)"));
		s_bPlayerBotFarmerTables = PlayerBotFarmerSqlOk(link) && PlayerBotFarmerSqlOk(transfer) &&
				PlayerBotFarmerSqlOk(config) && PlayerBotFarmerSqlOk(row);
		if (!s_bPlayerBotFarmerTables)
			sys_err("PLAYERBOT_FARMER: the tables cannot be created link=%u transfer=%u config=%u row=%u",
					link.get() ? link->uiSQLErrno : 0U, transfer.get() ? transfer->uiSQLErrno : 0U,
					config.get() ? config->uiSQLErrno : 0U, row.get() ? row->uiSQLErrno : 0U);
		return s_bPlayerBotFarmerTables;
	}

	void LoadPlayerBotFarmerConfig()
	{
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"SELECT enabled, target_pct, keep_pct, new_per_hour, min_transfer, reserve "
				"FROM player.playerbot_farmer_config WHERE id=1"));
		if (!PlayerBotFarmerSqlOk(msg) || !msg->Get()->pSQLResult)
			return;
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		if (!row)
			return;
		TPlayerBotFarmerConfig c = s_kPlayerBotFarmerConfig;
		int enabled = 1;
		if (row[0]) str_to_number(enabled, row[0]);
		if (row[1]) str_to_number(c.targetPct, row[1]);
		if (row[2]) str_to_number(c.keepPct, row[2]);
		if (row[3]) str_to_number(c.newPerHour, row[3]);
		if (row[4]) str_to_number(c.minTransfer, row[4]);
		if (row[5]) str_to_number(c.reserve, row[5]);
		c.enabled = enabled != 0;
		c.targetPct = std::max(0, std::min(100, c.targetPct));
		c.keepPct = std::max(0, std::min(90, c.keepPct));
		c.newPerHour = std::max(0, std::min(120, c.newPerHour));
		c.minTransfer = std::max(10000LL, std::min(1000000000LL, c.minTransfer));
		c.reserve = std::max(0LL, std::min(1000000000LL, c.reserve));
		if (c.enabled != s_kPlayerBotFarmerConfig.enabled || c.targetPct != s_kPlayerBotFarmerConfig.targetPct ||
				c.keepPct != s_kPlayerBotFarmerConfig.keepPct || c.newPerHour != s_kPlayerBotFarmerConfig.newPerHour ||
				c.minTransfer != s_kPlayerBotFarmerConfig.minTransfer || c.reserve != s_kPlayerBotFarmerConfig.reserve)
			sys_log(0, "PLAYERBOT_FARMER: config enabled=%d target=%d%% keep=%d%% new_per_hour=%d min_transfer=%lld reserve=%lld",
					c.enabled ? 1 : 0, c.targetPct, c.keepPct, c.newPerHour, c.minTransfer, c.reserve);
		s_kPlayerBotFarmerConfig = c;
	}

	// Every row, every pass: a farmer made on another core is known here, a
	// main another core's farmer paid is paid here. A failed read keeps what
	// was known.
	void LoadPlayerBotFarmerLinks()
	{
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"SELECT farmer_pid, main_pid, empire, kind, spot, active, owed, pending "
				"FROM player.playerbot_farmer_link"));
		if (!PlayerBotFarmerSqlOk(msg) || !msg->Get()->pSQLResult)
			return;
		TPlayerBotFarmerLinkMap links;
		std::map<DWORD, DWORD> byMain;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			DWORD farmer = 0;
			TPlayerBotFarmerLink l;
			unsigned int empire = 0, active = 0;
			l.main = 0;
			l.owed = 0;
			l.pending = 0;
			if (row[0]) str_to_number(farmer, row[0]);
			if (row[1]) str_to_number(l.main, row[1]);
			if (row[2]) str_to_number(empire, row[2]);
			if (row[5]) str_to_number(active, row[5]);
			if (row[6]) str_to_number(l.owed, row[6]);
			if (row[7]) str_to_number(l.pending, row[7]);
			if (farmer == 0 || l.main == 0)
				continue;
			l.empire = (BYTE)empire;
			l.kind = FindPlayerBotFarmerKind(row[3]);
			l.spotKey = row[4] ? row[4] : "";
			l.spot = l.kind == PLAYERBOT_FARMER_KIND_SPOT ? FindPlayerBotFarmerSpot(l.spotKey.c_str()) : -1;
			l.active = active != 0;
			links[farmer] = l;
			byMain[l.main] = farmer;
		}
		s_mapPlayerBotFarmerLinks.swap(links);
		s_mapPlayerBotFarmerByMain.swap(byMain);
	}

	// ---------------------------------------------------------------------
	// Who.
	// ---------------------------------------------------------------------

	// The kind of dropper a bot is, or NONE.
	BYTE GetPlayerBotFarmerDropperKind(DWORD pid, const TPlayerBotAIState& state)
	{
		switch (state.bPersonality)
		{
			case BOT_PERSONALITY_MEDAL_DROPPER: return PLAYERBOT_FARMER_KIND_MEDAL;
			case BOT_PERSONALITY_M2_DROPPER: return PLAYERBOT_FARMER_KIND_M2;
			case BOT_PERSONALITY_M3_DROPPER: return PLAYERBOT_FARMER_KIND_M3;
			case BOT_PERSONALITY_METIN_DROPPER: return PLAYERBOT_FARMER_KIND_METIN;
			case BOT_PERSONALITY_GUILD_DROPPER: return PLAYERBOT_FARMER_KIND_GUILD;
			case BOT_PERSONALITY_L30_WEAPON_DROPPER: return PLAYERBOT_FARMER_KIND_L30;
			case BOT_PERSONALITY_ORNAMENT_FARMER: return PLAYERBOT_FARMER_KIND_ORNAMENT;
			default: break;
		}
		// The operator's medal cohort farms medals whatever its drawn character.
		if (CPlayerBotManager::instance().IsMedalDropperCohortPID(pid))
			return PLAYERBOT_FARMER_KIND_MEDAL;
		return PLAYERBOT_FARMER_KIND_NONE;
	}

	// Where a dropper works, for the panel.
	std::string GetPlayerBotFarmerDropperSpot(BYTE kind, DWORD pid)
	{
		switch (kind)
		{
			case PLAYERBOT_FARMER_KIND_MEDAL: return "monkey";
			case PLAYERBOT_FARMER_KIND_M2: return "m2_bestials";
			case PLAYERBOT_FARMER_KIND_M3: return "m3_waryong";
			case PLAYERBOT_FARMER_KIND_METIN: return "metins";
			case PLAYERBOT_FARMER_KIND_L30: return "orc_island";
			case PLAYERBOT_FARMER_KIND_ORNAMENT: return "m2_sworn";
			case PLAYERBOT_FARMER_KIND_GUILD:
			{
				const long map = GetPlayerBotGuildDropperGround(pid).map;
				return map == PLAYERBOT_MAP_SOHAN ? "guild_sohan" : map == PLAYERBOT_MAP_FIRE_LAND ? "guild_fire_land" : "guild_hwang";
			}
			default: return "";
		}
	}

	bool IsPlayerBotFarmerExcluded(DWORD pid)
	{
		return IsPlayerBotSidekickPID(pid) || IsPlayerBotShouterPID(pid);
	}

	// A bot a farmer may work for: an ordinary bot the checklist would take
	// (no dropper, no cohort, no companion, no shouter, no Arezzo or Ochao
	// cohort), not a farmer itself and nobody's main yet.
	bool IsPlayerBotFarmerMainCandidate(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || ch->GetEmpire() < 1 || ch->GetEmpire() > 3 || ch->GetLevel() < PLAYERBOT_FARMER_MAIN_MIN_LEVEL)
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotMedalShouterPID(pid) || s_mapPlayerBotFarmerLinks.find(pid) != s_mapPlayerBotFarmerLinks.end() ||
				IsPlayerBotFarmerMainPID(pid))
			return false;
		if (IsPlayerBotPersonaEnabled() && !state.persona.bRestored)
			return false;
		return IsPlayerBotProgressionEligible(ch, state);
	}

	// The ground a bot of this level would be given, or -1: of those its
	// level fits (up to the two levels every dropper may stand over its lock)
	// and this core can send it to, the one with the fewest farmers.
	int ChoosePlayerBotFarmerSpot(LPCHARACTER ch, const int* perSpot)
	{
		int best = -1;
		for (int i = 0; i < PLAYERBOT_FARMER_SPOT_COUNT; ++i)
		{
			const TPlayerBotFarmerSpot& s = PLAYERBOT_FARMER_SPOTS[i];
			if (ch->GetLevel() < s.minLevel || ch->GetLevel() > s.lock + PLAYERBOT_DROPPER_OUTGROWN_LEVELS)
				continue;
			if (s.map != 0 && !IsPlayerBotMapHostedHere(s.map))
				continue;
			if (best < 0 || perSpot[i] < perSpot[best])
				best = i;
		}
		return best;
	}

	// An ordinary bot that could be made a spot farmer.
	bool IsPlayerBotFarmerSpotCandidate(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		if (!ch || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotMedalShouterPID(pid) || s_mapPlayerBotFarmerLinks.find(pid) != s_mapPlayerBotFarmerLinks.end() ||
				IsPlayerBotFarmerMainPID(pid))
			return false;
		if (IsPlayerBotPersonaEnabled() && !state.persona.bRestored)
			return false;
		// A trader trades and a party fighter or a stone hunter by role keeps
		// its role; a bot in a person's party is that person's.
		if (state.bPersonality == BOT_PERSONALITY_MERCHANT || state.bBotRole != BOT_ROLE_MOB_GRINDER)
			return false;
		if (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty()))
			return false;
		return IsPlayerBotProgressionEligible(ch, state);
	}

	// ---------------------------------------------------------------------
	// Link and unlink.
	// ---------------------------------------------------------------------

	bool LinkPlayerBotFarmer(LPCHARACTER farmer, BYTE kind, int spot, const std::string& spotKey,
			LPCHARACTER mainCh, const char* why)
	{
		const DWORD pid = farmer->GetPlayerID();
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"INSERT INTO player.playerbot_farmer_link (farmer_pid, main_pid, empire, kind, spot, active, keep_pct, linked_at) "
				"VALUES (%u, %u, %u, '%s', '%s', 1, %d, NOW())",
				pid, mainCh->GetPlayerID(), (unsigned)farmer->GetEmpire(), PLAYERBOT_FARMER_KIND_KEYS[kind],
				spotKey.c_str(), s_kPlayerBotFarmerConfig.keepPct));
		if (!PlayerBotFarmerSqlOne(msg))
		{
			// Most often another core's farmer took this main a moment ago
			// (the unique key); the next pass looks again.
			sys_log(0, "PLAYERBOT_FARMER: link refused farmer=%u main=%u errno=%u", pid, mainCh->GetPlayerID(),
					msg.get() ? msg->uiSQLErrno : 0U);
			return false;
		}
		TPlayerBotFarmerLink l;
		l.main = mainCh->GetPlayerID();
		l.empire = farmer->GetEmpire();
		l.kind = kind;
		l.spot = spot;
		l.spotKey = spotKey;
		l.active = true;
		l.owed = 0;
		l.pending = 0;
		s_mapPlayerBotFarmerLinks[pid] = l;
		s_mapPlayerBotFarmerByMain[l.main] = pid;
		s_mapPlayerBotFarmerPurse.erase(pid);
		sys_log(0, "PLAYERBOT_FARMER: linked farmer=%u name=%s level=%u kind=%s spot=%s main=%u main_name=%s main_level=%u empire=%u channel=%u why=%s",
				pid, farmer->GetName(), (unsigned)farmer->GetLevel(), PLAYERBOT_FARMER_KIND_KEYS[kind], spotKey.c_str(),
				mainCh->GetPlayerID(), mainCh->GetName(), (unsigned)mainCh->GetLevel(), (unsigned)farmer->GetEmpire(),
				(unsigned)g_bChannel, why);
		return true;
	}

	// An inactive row of this farmer's (it was unlinked with yang still on
	// its way) is taken up again with the same main.
	bool RelinkPlayerBotFarmer(LPCHARACTER farmer, TPlayerBotFarmerLink& l, BYTE kind, int spot, const std::string& spotKey)
	{
		const DWORD pid = farmer->GetPlayerID();
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"UPDATE player.playerbot_farmer_link SET active=1, kind='%s', spot='%s', owed=0 WHERE farmer_pid=%u AND active=0",
				PLAYERBOT_FARMER_KIND_KEYS[kind], spotKey.c_str(), pid));
		if (!PlayerBotFarmerSqlOne(msg))
			return false;
		l.active = true;
		l.kind = kind;
		l.spot = spot;
		l.spotKey = spotKey;
		l.owed = 0;
		s_mapPlayerBotFarmerPurse.erase(pid);
		sys_log(0, "PLAYERBOT_FARMER: linked again farmer=%u name=%s kind=%s spot=%s main=%u",
				pid, farmer->GetName(), PLAYERBOT_FARMER_KIND_KEYS[kind], spotKey.c_str(), l.main);
		return true;
	}

	// The kind or the ground changed (a spot farmer drawn a dropper, a guild
	// dropper's ground): the row says what it is now.
	void UpdatePlayerBotFarmerKind(DWORD pid, TPlayerBotFarmerLink& l, BYTE kind, int spot, const std::string& spotKey)
	{
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"UPDATE player.playerbot_farmer_link SET kind='%s', spot='%s' WHERE farmer_pid=%u",
				PLAYERBOT_FARMER_KIND_KEYS[kind], spotKey.c_str(), pid));
		if (!PlayerBotFarmerSqlOk(msg))
			return;
		sys_log(0, "PLAYERBOT_FARMER: kind farmer=%u %s/%s -> %s/%s", pid, PLAYERBOT_FARMER_KIND_KEYS[l.kind],
				l.spotKey.c_str(), PLAYERBOT_FARMER_KIND_KEYS[kind], spotKey.c_str());
		l.kind = kind;
		l.spot = spot;
		l.spotKey = spotKey;
	}

	// The farmer goes; what it already sent still reaches its main, so a row
	// with yang pending stays (inactive) until the main has taken it.
	void UnlinkPlayerBotFarmer(DWORD pid, const char* why)
	{
		TPlayerBotFarmerLinkMap::iterator it = s_mapPlayerBotFarmerLinks.find(pid);
		if (it == s_mapPlayerBotFarmerLinks.end())
			return;
		std::unique_ptr<SQLMsg> del(PlayerBotFarmerQuery(
				"DELETE FROM player.playerbot_farmer_link WHERE farmer_pid=%u AND pending=0", pid));
		bool gone = PlayerBotFarmerSqlOne(del);
		if (!gone)
		{
			std::unique_ptr<SQLMsg> upd(PlayerBotFarmerQuery(
					"UPDATE player.playerbot_farmer_link SET active=0, owed=0 WHERE farmer_pid=%u", pid));
			if (!PlayerBotFarmerSqlOk(upd))
				return;
		}
		sys_log(0, "PLAYERBOT_FARMER: unlinked farmer=%u main=%u kind=%s spot=%s pending=%lld why=%s",
				pid, it->second.main, PLAYERBOT_FARMER_KIND_KEYS[it->second.kind], it->second.spotKey.c_str(),
				it->second.pending, why);
		s_mapPlayerBotFarmerPurse.erase(pid);
		if (gone)
		{
			s_mapPlayerBotFarmerByMain.erase(it->second.main);
			s_mapPlayerBotFarmerLinks.erase(it);
		}
		else
		{
			it->second.active = false;
			it->second.owed = 0;
		}
	}

	// ---------------------------------------------------------------------
	// The money.
	// ---------------------------------------------------------------------

	long long GetPlayerBotFarmerGoldCap(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009)
		return (long long)ch->Mt2009PlusGoldMax();
#else
		(void)ch;
		return 2000000000LL;
#endif
	}

	void LogPlayerBotFarmerTransfer(DWORD farmer, DWORD mainPid, long long amount, int stage)
	{
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"INSERT INTO player.playerbot_farmer_transfer (farmer_pid, main_pid, amount, stage) VALUES (%u, %u, %lld, %d)",
				farmer, mainPid, amount, stage));
	}

	// The farmer's side, every pass it plays here: what its purse grew by,
	// the keeper's share and the main's, and now and then the main's on its way.
	void ServePlayerBotFarmerPurse(LPCHARACTER ch, TPlayerBotFarmerLink& l, DWORD dwNow)
	{
		const TPlayerBotFarmerConfig& cfg = s_kPlayerBotFarmerConfig;
		const DWORD pid = ch->GetPlayerID();
		const long long gold = (long long)ch->GetGold();
		std::map<DWORD, TPlayerBotFarmerPurse>::iterator pit = s_mapPlayerBotFarmerPurse.find(pid);
		if (pit == s_mapPlayerBotFarmerPurse.end())
		{
			// First seen on this core: what it holds is its starting point,
			// not its earnings.
			TPlayerBotFarmerPurse p;
			p.baseline = gold;
			p.gain = 0;
			p.nextFlush = dwNow + PLAYERBOT_FARMER_FLUSH_MS;
			p.nextSend = dwNow + PLAYERBOT_FARMER_SEND_MS + PlayerBotNavHash(pid ^ dwNow) % PLAYERBOT_FARMER_SEND_JITTER_MS;
			p.lastSend = dwNow;
			s_mapPlayerBotFarmerPurse[pid] = p;
			return;
		}
		TPlayerBotFarmerPurse& p = pit->second;
		if (gold > p.baseline)
			p.gain += gold - p.baseline;
		p.baseline = gold;

		const long long share = p.gain * (100 - cfg.keepPct) / 100;
		const long long owedNow = l.owed + share;
		if ((int)(dwNow - p.nextSend) >= 0)
		{
			long long amount = std::min(owedNow, gold - cfg.reserve);
			const bool sendAll = amount > 0 && amount == owedNow && dwNow - p.lastSend >= PLAYERBOT_FARMER_SEND_ALL_MS;
			if (amount > 0 && (amount >= cfg.minTransfer || sendAll) && ch->GetExchange() == NULL)
			{
				std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
						"UPDATE player.playerbot_farmer_link SET earned=earned+%lld, kept=kept+%lld, "
						"owed=owed+%lld-%lld, pending=pending+%lld, transfers=transfers+1, last_sent=NOW() "
						"WHERE farmer_pid=%u AND active=1 AND owed+%lld>=%lld",
						p.gain, p.gain - share, share, amount, amount, pid, share, amount));
				if (PlayerBotFarmerSqlOne(msg))
				{
					PlayerBotChangeGold(ch, -amount);
					char hint[32];
					snprintf(hint, sizeof(hint), "main=%u", l.main);
					LogManager::instance().CharLog(ch, amount, "PLAYERBOT_FARMER_SEND", hint);
					LogPlayerBotFarmerTransfer(pid, l.main, amount, 1);
					sys_log(0, "PLAYERBOT_FARMER: sent farmer=%u name=%s main=%u amount=%lld earned_since=%lld kept=%lld owed_left=%lld gold_left=%lld",
							pid, ch->GetName(), l.main, amount, p.gain, p.gain - share, owedNow - amount, (long long)ch->GetGold());
					l.owed = owedNow - amount;
					l.pending += amount;
					p.gain = 0;
					p.baseline = (long long)ch->GetGold();
					p.nextFlush = dwNow + PLAYERBOT_FARMER_FLUSH_MS;
					p.lastSend = dwNow;
					s_llPlayerBotFarmerSent += amount;
					++s_iPlayerBotFarmerSends;
				}
				p.nextSend = dwNow + PLAYERBOT_FARMER_SEND_MS + PlayerBotNavHash(pid ^ dwNow) % PLAYERBOT_FARMER_SEND_JITTER_MS;
				return;
			}
			p.nextSend = dwNow + PLAYERBOT_FARMER_FLUSH_MS;
		}
		// The totals for the panel, every five minutes.
		if (p.gain > 0 && (int)(dwNow - p.nextFlush) >= 0)
		{
			std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
					"UPDATE player.playerbot_farmer_link SET earned=earned+%lld, kept=kept+%lld, owed=owed+%lld "
					"WHERE farmer_pid=%u AND active=1", p.gain, p.gain - share, share, pid));
			if (PlayerBotFarmerSqlOne(msg))
			{
				l.owed = owedNow;
				p.gain = 0;
			}
			p.nextFlush = dwNow + PLAYERBOT_FARMER_FLUSH_MS;
		}
	}

	// The main's side: the yang its farmer sent, as much as its purse may
	// hold; the rest waits for room.
	void CollectPlayerBotFarmerPending(LPCHARACTER mainCh, DWORD farmer, TPlayerBotFarmerLink& l)
	{
		if (l.pending <= 0 || mainCh->GetExchange() != NULL)
			return;
		const long long room = GetPlayerBotFarmerGoldCap(mainCh) - 1 - (long long)mainCh->GetGold();
		const long long amount = std::min(l.pending, room);
		if (amount <= 0)
			return;
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"UPDATE player.playerbot_farmer_link SET pending=pending-%lld, transferred=transferred+%lld, "
				"last_received=NOW() WHERE farmer_pid=%u AND main_pid=%u AND pending>=%lld",
				amount, amount, farmer, mainCh->GetPlayerID(), amount));
		if (!PlayerBotFarmerSqlOne(msg))
			return;
		PlayerBotChangeGold(mainCh, amount);
		char hint[32];
		snprintf(hint, sizeof(hint), "farmer=%u", farmer);
		LogManager::instance().CharLog(mainCh, amount, "PLAYERBOT_FARMER_RECV", hint);
		LogPlayerBotFarmerTransfer(farmer, mainCh->GetPlayerID(), amount, 2);
		l.pending -= amount;
		s_llPlayerBotFarmerTaken += amount;
		++s_iPlayerBotFarmerTakes;
		sys_log(0, "PLAYERBOT_FARMER: received main=%u name=%s farmer=%u amount=%lld gold=%lld pending_left=%lld",
				mainCh->GetPlayerID(), mainCh->GetName(), farmer, amount, (long long)mainCh->GetGold(), l.pending);
		if (!l.active && l.pending <= 0)
		{
			std::unique_ptr<SQLMsg> del(PlayerBotFarmerQuery(
					"DELETE FROM player.playerbot_farmer_link WHERE farmer_pid=%u AND active=0 AND pending=0", farmer));
			if (PlayerBotFarmerSqlOne(del))
			{
				s_mapPlayerBotFarmerByMain.erase(l.main);
				s_mapPlayerBotFarmerLinks.erase(farmer);
			}
		}
	}

	// A main playing here that is no main any more (a dropper drawn, a
	// companion, a shouter, a farmer itself): once it has what was sent, its
	// farmer is let go and linked elsewhere by its own core.
	bool IsPlayerBotFarmerMainStillValid(LPCHARACTER mainCh)
	{
		const DWORD pid = mainCh->GetPlayerID();
		if (IsPlayerBotFarmerExcluded(pid) || IsPlayerBotMedalShouterPID(pid) || IsPlayerBotFarmerPID(pid))
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(pid);
		if (st == s_mapPlayerBotAIStates.end())
			return true; // a person playing it now (a takeover): still its main
		return GetPlayerBotFarmerDropperKind(pid, st->second) == PLAYERBOT_FARMER_KIND_NONE;
	}

	// ---------------------------------------------------------------------
	// The pass.
	// ---------------------------------------------------------------------

	LPCHARACTER ChoosePlayerBotFarmerMain(LPCHARACTER farmer,
			std::vector<std::pair<DWORD, DWORD> >& pool)
	{
		// pool: (hash, pid) of the main candidates of the farmer's kingdom,
		// sorted; the first far enough over the farmer, else the highest over it.
		int best = -1;
		int bestLevel = (int)farmer->GetLevel();
		for (size_t i = 0; i < pool.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pool[i].second);
			if (!ch)
				continue;
			const int level = (int)ch->GetLevel();
			if (level >= (int)farmer->GetLevel() + PLAYERBOT_FARMER_MAIN_LEVEL_GAP)
			{
				best = (int)i;
				break;
			}
			if (level > bestLevel)
			{
				best = (int)i;
				bestLevel = level;
			}
		}
		if (best < 0)
			return NULL;
		LPCHARACTER chosen = CHARACTER_MANAGER::instance().FindByPID(pool[best].second);
		pool.erase(pool.begin() + best);
		return chosen;
	}

	void ManagePlayerBotFarmerLinks(DWORD dwNow)
	{
		if (s_dwPlayerBotFarmerNextPass != 0 && (int)(dwNow - s_dwPlayerBotFarmerNextPass) < 0)
			return;
		s_dwPlayerBotFarmerNextPass = dwNow + PLAYERBOT_FARMER_PASS_MS;
		if (s_dwPlayerBotFarmerFirstPass == 0)
			s_dwPlayerBotFarmerFirstPass = dwNow;
		if (!EnsurePlayerBotFarmerTables())
			return;
		LoadPlayerBotFarmerConfig();
		LoadPlayerBotFarmerLinks();
		const TPlayerBotFarmerConfig& cfg = s_kPlayerBotFarmerConfig;
		const bool settled = dwNow - s_dwPlayerBotFarmerFirstPass >= PLAYERBOT_FARMER_SETTLE_MS;

		// The mains playing here take what was sent - with the system off too.
		{
			std::vector<DWORD> farmers;
			for (TPlayerBotFarmerLinkMap::const_iterator it = s_mapPlayerBotFarmerLinks.begin();
					it != s_mapPlayerBotFarmerLinks.end(); ++it)
				farmers.push_back(it->first);
			for (size_t i = 0; i < farmers.size(); ++i)
			{
				TPlayerBotFarmerLinkMap::iterator it = s_mapPlayerBotFarmerLinks.find(farmers[i]);
				if (it == s_mapPlayerBotFarmerLinks.end())
					continue;
				LPCHARACTER mainCh = CHARACTER_MANAGER::instance().FindByPID(it->second.main);
				if (!mainCh || !mainCh->IsPC())
					continue;
				CollectPlayerBotFarmerPending(mainCh, farmers[i], it->second);
				it = s_mapPlayerBotFarmerLinks.find(farmers[i]);
				if (it != s_mapPlayerBotFarmerLinks.end() && it->second.active && it->second.pending <= 0 &&
						cfg.enabled && !IsPlayerBotFarmerMainStillValid(mainCh))
					UnlinkPlayerBotFarmer(farmers[i], "main_not_valid");
			}
		}

		int perSpot[PLAYERBOT_FARMER_SPOT_COUNT];
		memset(perSpot, 0, sizeof(perSpot));
		for (TPlayerBotFarmerLinkMap::const_iterator it = s_mapPlayerBotFarmerLinks.begin();
				it != s_mapPlayerBotFarmerLinks.end(); ++it)
			if (it->second.active && it->second.kind == PLAYERBOT_FARMER_KIND_SPOT &&
					it->second.spot >= 0 && it->second.spot < PLAYERBOT_FARMER_SPOT_COUNT)
				++perSpot[it->second.spot];

		int online = 0, farmersHere = 0, spotHere = 0, droppersWaiting = 0;
		std::vector<std::pair<DWORD, DWORD> > droppers;         // (hash, pid), unlinked
		std::vector<std::pair<DWORD, DWORD> > spotCandidates;   // (hash, pid)
		std::vector<std::pair<DWORD, DWORD> > spotFarmers;      // (hash, pid), linked here
		std::vector<std::pair<DWORD, DWORD> > mains[4];         // (hash, pid) per kingdom
		for (TPlayerBotAIStateMap::iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			const DWORD pid = it->first;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!ch || !ch->IsPC() || IsPlayerBotFarmerExcluded(pid))
				continue;
			TPlayerBotAIState& state = it->second;
			++online;
			const BYTE dropperKind = GetPlayerBotFarmerDropperKind(pid, state);
			TPlayerBotFarmerLinkMap::iterator link = s_mapPlayerBotFarmerLinks.find(pid);
			const DWORD hash = PlayerBotNavHash(pid ^ PLAYERBOT_FARMER_SEED ^ ((DWORD)g_bChannel << 24));
			if (link != s_mapPlayerBotFarmerLinks.end() && link->second.active)
			{
				if (!cfg.enabled)
				{
					++farmersHere;
					continue;
				}
				if (dropperKind != PLAYERBOT_FARMER_KIND_NONE)
				{
					const std::string spotKey = GetPlayerBotFarmerDropperSpot(dropperKind, pid);
					if (link->second.kind != dropperKind || link->second.spotKey != spotKey)
						UpdatePlayerBotFarmerKind(pid, link->second, dropperKind, -1, spotKey);
				}
				else if (link->second.kind == PLAYERBOT_FARMER_KIND_SPOT)
				{
					const int s = link->second.spot;
					if (s < 0 || s >= PLAYERBOT_FARMER_SPOT_COUNT)
					{
						UnlinkPlayerBotFarmer(pid, "unknown_spot");
						continue;
					}
					if (ch->GetLevel() > PLAYERBOT_FARMER_SPOTS[s].lock + PLAYERBOT_DROPPER_OUTGROWN_LEVELS)
					{
						UnlinkPlayerBotFarmer(pid, "past_spot");
						continue;
					}
					if (!IsPlayerBotProgressionEligible(ch, state) || state.bPersonality == BOT_PERSONALITY_MERCHANT)
					{
						UnlinkPlayerBotFarmer(pid, "not_eligible");
						continue;
					}
					++spotHere;
					spotFarmers.push_back(std::make_pair(hash, pid));
				}
				else
				{
					UnlinkPlayerBotFarmer(pid, "no_longer_dropper");
					continue;
				}
				++farmersHere;
				// A person playing the farmer (a takeover) keeps its yang.
				if (CPlayerBotManager::instance().IsManaged(pid))
					ServePlayerBotFarmerPurse(ch, link->second, dwNow);
				continue;
			}
			if (!cfg.enabled)
				continue;
			if (dropperKind != PLAYERBOT_FARMER_KIND_NONE)
			{
				droppers.push_back(std::make_pair(hash, pid));
				continue;
			}
			if (IsPlayerBotFarmerMainCandidate(ch, state))
				mains[ch->GetEmpire()].push_back(std::make_pair(PlayerBotNavHash(pid ^ 0x4d41494eU), pid));
			if (settled && IsPlayerBotFarmerSpotCandidate(ch, state) && ChoosePlayerBotFarmerSpot(ch, perSpot) >= 0)
				spotCandidates.push_back(std::make_pair(hash, pid));
		}

		if (cfg.enabled)
		{
			for (int e = 1; e <= 3; ++e)
				std::sort(mains[e].begin(), mains[e].end());

			// Every dropper gets its main.
			std::sort(droppers.begin(), droppers.end());
			int linked = 0;
			for (size_t i = 0; i < droppers.size(); ++i)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(droppers[i].second);
				TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(droppers[i].second);
				if (!ch || st == s_mapPlayerBotAIStates.end())
					continue;
				const BYTE kind = GetPlayerBotFarmerDropperKind(droppers[i].second, st->second);
				const std::string spotKey = GetPlayerBotFarmerDropperSpot(kind, droppers[i].second);
				TPlayerBotFarmerLinkMap::iterator old = s_mapPlayerBotFarmerLinks.find(droppers[i].second);
				if (old != s_mapPlayerBotFarmerLinks.end())
				{
					if (RelinkPlayerBotFarmer(ch, old->second, kind, -1, spotKey))
						++farmersHere;
					continue;
				}
				if (linked >= PLAYERBOT_FARMER_LINKS_PER_PASS)
				{
					++droppersWaiting;
					continue;
				}
				LPCHARACTER mainCh = ChoosePlayerBotFarmerMain(ch, mains[ch->GetEmpire()]);
				if (!mainCh)
				{
					++droppersWaiting;
					continue;
				}
				++linked;
				if (LinkPlayerBotFarmer(ch, kind, -1, spotKey, mainCh, "dropper"))
					++farmersHere;
			}

			// The spot farmers towards the share: farmers / everybody else.
			const int cap = online * cfg.targetPct / (100 + cfg.targetPct);
			if (farmersHere < cap && cfg.newPerHour > 0 &&
					(s_dwPlayerBotFarmerNextNew == 0 || (int)(dwNow - s_dwPlayerBotFarmerNextNew) >= 0))
			{
				std::sort(spotCandidates.begin(), spotCandidates.end());
				for (size_t i = 0; i < spotCandidates.size(); ++i)
				{
					LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(spotCandidates[i].second);
					if (!ch || IsPlayerBotFarmerMainPID(spotCandidates[i].second))
						continue;
					const int spot = ChoosePlayerBotFarmerSpot(ch, perSpot);
					if (spot < 0)
						continue;
					// Not the bot it would work for.
					std::vector<std::pair<DWORD, DWORD> >& pool = mains[ch->GetEmpire()];
					for (size_t m = 0; m < pool.size(); ++m)
						if (pool[m].second == spotCandidates[i].second)
						{
							pool.erase(pool.begin() + m);
							break;
						}
					LPCHARACTER mainCh = ChoosePlayerBotFarmerMain(ch, pool);
					if (!mainCh)
						continue;
					if (LinkPlayerBotFarmer(ch, PLAYERBOT_FARMER_KIND_SPOT, spot, PLAYERBOT_FARMER_SPOTS[spot].key, mainCh, "spot"))
					{
						++perSpot[spot];
						++farmersHere;
						++spotHere;
						// It starts hunting its ground at once.
						TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(spotCandidates[i].second);
						if (st != s_mapPlayerBotAIStates.end())
							st->second.dwHubChosenTime = 0;
						break;
					}
				}
				s_dwPlayerBotFarmerNextNew = dwNow + 3600000U / (DWORD)std::max(1, cfg.newPerHour);
			}
			// And back down when the panel lowered the share: one spot farmer
			// every few minutes, the droppers never.
			else if (settled && spotHere > 0 && farmersHere > cap + std::max(2, cap / 20) &&
					(s_dwPlayerBotFarmerNextRelease == 0 || (int)(dwNow - s_dwPlayerBotFarmerNextRelease) >= 0))
			{
				std::sort(spotFarmers.begin(), spotFarmers.end());
				UnlinkPlayerBotFarmer(spotFarmers.back().second, "over_share");
				s_dwPlayerBotFarmerNextRelease = dwNow + PLAYERBOT_FARMER_RELEASE_MS;
			}
		}

		if (s_dwPlayerBotFarmerNextPrune == 0 || (int)(dwNow - s_dwPlayerBotFarmerNextPrune) >= 0)
		{
			s_dwPlayerBotFarmerNextPrune = dwNow + PLAYERBOT_FARMER_PRUNE_MS;
			std::unique_ptr<SQLMsg> prune(PlayerBotFarmerQuery(
					"DELETE FROM player.playerbot_farmer_transfer WHERE at < NOW() - INTERVAL 30 DAY"));
		}
		if (s_dwPlayerBotFarmerNextCensus == 0 || (int)(dwNow - s_dwPlayerBotFarmerNextCensus) >= 0)
		{
			s_dwPlayerBotFarmerNextCensus = dwNow + PLAYERBOT_FARMER_CENSUS_MS;
			int active = 0;
			for (TPlayerBotFarmerLinkMap::const_iterator it = s_mapPlayerBotFarmerLinks.begin();
					it != s_mapPlayerBotFarmerLinks.end(); ++it)
				if (it->second.active)
					++active;
			sys_log(0, "PLAYERBOT_FARMER: census channel=%u enabled=%d online=%d farmers_here=%d spot_here=%d cap=%d droppers_waiting=%d links=%d sent=%lld/%d taken=%lld/%d",
					(unsigned)g_bChannel, cfg.enabled ? 1 : 0, online, farmersHere, spotHere,
					online * cfg.targetPct / (100 + cfg.targetPct), droppersWaiting, active,
					s_llPlayerBotFarmerSent, s_iPlayerBotFarmerSends, s_llPlayerBotFarmerTaken, s_iPlayerBotFarmerTakes);
			s_llPlayerBotFarmerSent = s_llPlayerBotFarmerTaken = 0;
			s_iPlayerBotFarmerSends = s_iPlayerBotFarmerTakes = 0;
		}
	}
}

#endif
