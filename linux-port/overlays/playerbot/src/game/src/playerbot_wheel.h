// MT2009 PLUS Kolo Fortuny (the operator, 28 September: dracaryS's "Wheel of
// Fortune" on our chat-command protocol - no packet and no change to the
// client's exe; the window is root/uiwheel.py, F12).
//
// A spin costs a ticket - "Bilet Kola Fortuny" (80030), sold in the ItemShop
// for Smocze Monety - and gives one reward of a weighted pool. Everything the
// operator sets lives in the database, edited on the Seban Panel's "Kolo
// Fortuny" page, and the game reads it again every 30 seconds:
//   player.wheel_config - one row: on/off, the ticket's vnum and how many a
//                         spin takes;
//   player.wheel_reward - the pool: vnum, count, weight (the chance is the
//                         weight over the sum of the active weights), rare
//                         (the window's jackpot light), active;
//   player.wheel_spin   - every spin: the ten items shown, the slot won, the
//                         reward, the price paid, state 0 pending / 1 given.
//
// The server decides everything. "/kolo krec" takes the ticket, draws the
// reward by weight (the nine other slots are only for show), writes the spin
// row and sends it; the window turns the wheel and asks "/kolo odbierz <id>".
// The reward is given only by the core whose conditional UPDATE (state 0 ->
// 1) changes the row - a player's characters move between cores (each hosts
// other maps), so no core holds a spin in memory. A spin the window never
// claimed (a teleport, a lost connection, a closed client) is given the next
// time the player opens the wheel or spins again, or by the minute tick of
// the core the player stands on, two minutes after it was drawn: a ticket is
// never lost. Bots do not play.
//
// To the client, one command with a sub-command (game.py "WOF"):
//   WOF info <enabled> <ticket vnum> <tickets per spin> <tickets held>
//   WOF poolbegin <sum of weights>
//   WOF pool <vnum>|<count>|<rare>|<chance in 1/10000>#...   (several lines)
//   WOF poolend
//   WOF items <spin id> <vnum>|<count>|<rare>#... (ten slots)
//   WOF spin <spin id> <slot 0-9>
//   WOF gift <vnum> <count> <rare>
//   WOF fail                  - the spin was refused (the window unlocks)
//
// MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion] - "spin N times" (N of 1, 2, 5, 10, 25, 50):
// "/kolo krec <n>" takes n x the tickets and draws n rewards, as ONE spin row:
// its vnum/count/rare/slot are the reward the wheel shows (a rare one when
// there is one), the new column `rewards` holds all n ("vnum|count|rare#...")
// and `spins` is n. The window turns once ("WOF spin <id> <slot> <n>") and
// asks "/kolo odbierz <id>" as before; the row's one UPDATE (state 0 -> 1)
// still decides which core gives - all n at once. Rewards that find no room
// go into a new pending row (cost 0) and come with the next claim. More than
// one reward given by a claim is told as
//   WOF giftsbegin <n> / WOF gifts <vnum>|<count>|<rare>#... / WOF giftsend
// (one stays "WOF gift"). The two columns are added to an existing table at
// the first load; if that fails, only single spins work.
namespace mt2009_wheel
{
	const DWORD TICKET_VNUM = 80030;
	const DWORD RELOAD_MS = 30 * 1000;
	const DWORD COMMAND_GAP_MS = 700;
	const int SLOTS = 10;
	// A pending spin older than this is given by the tick on the player's core.
	const int SETTLE_AFTER_SECONDS = 120;

	struct Reward
	{
		DWORD id;
		DWORD vnum;
		DWORD count;
		DWORD weight;
		bool rare;
	};

	struct Slot
	{
		DWORD vnum;
		DWORD count;
		bool rare;
	};

	typedef Slot Gift;	// a reward given

	// MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]
	const int SPIN_COUNTS[] = { 1, 2, 5, 10, 25, 50 };
	bool s_bMulti = false;	// wheel_spin has the columns `rewards` and `spins`

	bool ValidSpinCount(int spins)
	{
		for (size_t i = 0; i < sizeof(SPIN_COUNTS) / sizeof(SPIN_COUNTS[0]); ++i)
			if (SPIN_COUNTS[i] == spins)
				return true;
		return false;
	}

	// "vnum|count|rare#vnum|count|rare#..."
	std::string FormatGifts(const std::vector<Gift>& gifts, size_t from)
	{
		std::string out;
		for (size_t i = from; i < gifts.size(); ++i)
		{
			char part[48];
			snprintf(part, sizeof(part), "%u|%u|%d#", gifts[i].vnum, gifts[i].count, gifts[i].rare ? 1 : 0);
			out += part;
		}
		return out;
	}

	void ParseGifts(const char* text, std::vector<Gift>& out)
	{
		const char* p = text;
		while (p && *p)
		{
			unsigned int vnum = 0, count = 1, rare = 0;
			if (sscanf(p, "%u|%u|%u", &vnum, &count, &rare) < 2)
				break;
			if (vnum)
			{
				Gift g;
				g.vnum = vnum;
				g.count = std::max<DWORD>(1, count);
				g.rare = rare != 0;
				out.push_back(g);
			}
			p = strchr(p, '#');
			if (p)
				++p;
		}
	}

	std::vector<Reward> s_vecRewards;
	unsigned long long s_ullWeights = 0;
	bool s_bEnabled = true;
	DWORD s_dwCostVnum = TICKET_VNUM;
	DWORD s_dwCostCount = 1;
	DWORD s_dwLoadedAt = 0;
	bool s_bLoaded = false;
	bool s_bTables = false;
	std::map<DWORD, DWORD> s_mapLastCommand;
	LPEVENT s_pkTick = NULL;

	bool Eligible(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}

	bool Query(const char* query)
	{
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		return msg.get() && msg->uiSQLErrno == 0;
	}

	bool EnsureTables()
	{
		if (s_bTables)
			return true;
		const bool config = Query(
				"CREATE TABLE IF NOT EXISTS player.wheel_config ("
				"id TINYINT UNSIGNED NOT NULL PRIMARY KEY, "
				"enabled TINYINT UNSIGNED NOT NULL DEFAULT 1, "
				"cost_vnum INT UNSIGNED NOT NULL DEFAULT 80030, "
				"cost_count INT UNSIGNED NOT NULL DEFAULT 1) ENGINE=InnoDB");
		const bool reward = Query(
				"CREATE TABLE IF NOT EXISTS player.wheel_reward ("
				"id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, "
				"vnum INT UNSIGNED NOT NULL, "
				"count INT UNSIGNED NOT NULL DEFAULT 1, "
				"weight INT UNSIGNED NOT NULL DEFAULT 10, "
				"rare TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"active TINYINT UNSIGNED NOT NULL DEFAULT 1) ENGINE=InnoDB");
		const bool spin = Query(
				"CREATE TABLE IF NOT EXISTS player.wheel_spin ("
				"id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, "
				"pid INT UNSIGNED NOT NULL, "
				"created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
				"items VARCHAR(255) NOT NULL DEFAULT '', "
				"slot TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"vnum INT UNSIGNED NOT NULL, "
				"count INT UNSIGNED NOT NULL DEFAULT 1, "
				"rare TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"cost_vnum INT UNSIGNED NOT NULL DEFAULT 0, "
				"cost_count INT UNSIGNED NOT NULL DEFAULT 0, "
				"state TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"given DATETIME NULL DEFAULT NULL, "
				"KEY pid_state (pid, state), KEY state_created (state, created)) ENGINE=InnoDB");
		s_bTables = config && reward && spin;
		if (!s_bTables)
		{
			sys_err("WHEEL: no tables");
			return false;
		}
		// The starter pool, once - while there is no config row yet (the panel
		// does the same, in the same order): potions, scrolls, upgrade
		// materials, Cor Draconis, and the SM coupons; the 250 coupon - ten
		// tickets' worth - is the jackpot.
		Query("INSERT INTO player.wheel_reward (vnum, count, weight, rare) "
				"SELECT t.v, t.c, t.w, t.r FROM ("
				"SELECT 27002 AS v, 50 AS c, 150 AS w, 0 AS r"
				" UNION ALL SELECT 27005, 50, 150, 0"
				" UNION ALL SELECT 71095, 5, 100, 0"
				" UNION ALL SELECT 50255, 2, 100, 0"
				" UNION ALL SELECT 71001, 1, 70, 0"
				" UNION ALL SELECT 71084, 1, 60, 0"
				" UNION ALL SELECT 71085, 1, 50, 0"
				" UNION ALL SELECT 50513, 1, 50, 0"
				" UNION ALL SELECT 71027, 2, 50, 0"
				" UNION ALL SELECT 71028, 2, 50, 0"
				" UNION ALL SELECT 71026, 1, 40, 0"
				" UNION ALL SELECT 71044, 2, 40, 0"
				" UNION ALL SELECT 71045, 2, 40, 0"
				" UNION ALL SELECT 71025, 1, 30, 0"
				" UNION ALL SELECT 80017, 1, 16, 1"
				" UNION ALL SELECT 80018, 1, 4, 1"
				") AS t WHERE NOT EXISTS (SELECT 1 FROM player.wheel_config) "
				"AND NOT EXISTS (SELECT 1 FROM player.wheel_reward)");
		Query("INSERT IGNORE INTO player.wheel_config (id, enabled, cost_vnum, cost_count) VALUES (1, 1, 80030, 1)");
		// MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]: the columns of a spin of many, added once to
		// a table made before them.
		for (int pass = 0; pass < 2 && !s_bMulti; ++pass)
		{
			std::unique_ptr<SQLMsg> cols(AccountDB::instance().DirectQuery(
					"SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='player' "
					"AND TABLE_NAME='wheel_spin' AND COLUMN_NAME IN ('rewards', 'spins')"));
			if (cols.get() && cols->uiSQLErrno == 0 && cols->Get() && cols->Get()->pSQLResult)
			{
				MYSQL_ROW row = mysql_fetch_row(cols->Get()->pSQLResult);
				int found = 0;
				if (row && row[0])
					str_to_number(found, row[0]);
				s_bMulti = found == 2;
			}
			if (!s_bMulti && pass == 0)
				Query("ALTER TABLE player.wheel_spin ADD COLUMN rewards TEXT NULL, "
						"ADD COLUMN spins INT UNSIGNED NOT NULL DEFAULT 1");
		}
		if (!s_bMulti)
			sys_err("WHEEL: wheel_spin has no rewards/spins columns - only single spins");
		return true;
	}

	void Load(bool force)
	{
		const DWORD now = get_dword_time();
		if (!force && s_bLoaded && now - s_dwLoadedAt < RELOAD_MS)
			return;
		s_dwLoadedAt = now;
		if (!EnsureTables())
			return;
		std::unique_ptr<SQLMsg> config(AccountDB::instance().DirectQuery(
				"SELECT enabled, cost_vnum, cost_count FROM player.wheel_config WHERE id=1"));
		if (config.get() && config->uiSQLErrno == 0 && config->Get() && config->Get()->pSQLResult)
		{
			MYSQL_ROW row = mysql_fetch_row(config->Get()->pSQLResult);
			if (row)
			{
				DWORD enabled = 1, vnum = TICKET_VNUM, count = 1;
				str_to_number(enabled, row[0]);
				str_to_number(vnum, row[1]);
				str_to_number(count, row[2]);
				s_bEnabled = enabled != 0;
				s_dwCostVnum = vnum;
				s_dwCostCount = count;
			}
		}
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"SELECT id, vnum, count, weight, rare FROM player.wheel_reward "
				"WHERE active <> 0 AND weight > 0 AND vnum > 0 ORDER BY id LIMIT 200"));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return;
		std::vector<Reward> fresh;
		unsigned long long weights = 0;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			Reward r;
			DWORD rare = 0;
			r.id = r.vnum = r.count = r.weight = 0;
			str_to_number(r.id, row[0]);
			str_to_number(r.vnum, row[1]);
			str_to_number(r.count, row[2]);
			str_to_number(r.weight, row[3]);
			str_to_number(rare, row[4]);
			r.rare = rare != 0;
			r.count = std::max<DWORD>(1, r.count);
			// An item this world does not have would be a ticket for nothing.
			if (!ITEM_MANAGER::instance().GetTable(r.vnum))
				continue;
			weights += r.weight;
			fresh.push_back(r);
		}
		if (!s_bLoaded || fresh.size() != s_vecRewards.size())
			sys_log(0, "WHEEL: %u rewards, weights %llu, ticket %u x%u, %s", (unsigned int)fresh.size(), weights,
					s_dwCostVnum, s_dwCostCount, s_bEnabled ? "on" : "off");
		s_vecRewards.swap(fresh);
		s_ullWeights = weights;
		s_bLoaded = true;
	}

	// One reward of the pool, by weight (its index). The pool is not empty.
	size_t Roll()
	{
		const unsigned long long roll = (unsigned long long)number(1, (int)std::min<unsigned long long>(s_ullWeights, 0x7FFFFFFF));
		unsigned long long acc = 0;
		for (size_t i = 0; i < s_vecRewards.size(); ++i)
		{
			acc += s_vecRewards[i].weight;
			if (roll <= acc)
				return i;
		}
		return 0;
	}

	// The wheel's ten slots: one for the reward won, the other nine from the
	// rest of the pool in a random order (again when the pool is small).
	void Layout(size_t won, std::vector<Slot>& slots, int& winSlot)
	{
		std::vector<size_t> others;
		for (size_t i = 0; i < s_vecRewards.size(); ++i)
			if (i != won)
				others.push_back(i);
		for (size_t i = others.size(); i > 1; --i)
			std::swap(others[i - 1], others[number(0, (int)i - 1)]);
		winSlot = number(0, SLOTS - 1);
		slots.clear();
		size_t next = 0;
		for (int s = 0; s < SLOTS; ++s)
		{
			size_t pick = won;
			if (s != winSlot)
			{
				if (next < others.size())
					pick = others[next++];
				else
					pick = (size_t)number(0, (int)s_vecRewards.size() - 1);
			}
			Slot slot;
			slot.vnum = s_vecRewards[pick].vnum;
			slot.count = s_vecRewards[pick].count;
			slot.rare = s_vecRewards[pick].rare;
			slots.push_back(slot);
		}
	}

	bool TooSoon(LPCHARACTER ch)
	{
		const DWORD now = get_dword_time();
		DWORD& last = s_mapLastCommand[ch->GetPlayerID()];
		if (last && now - last < COMMAND_GAP_MS)
			return true;
		last = now;
		return false;
	}

	// What a claim gave, to the window: one reward as before, more as a list.
	void SendGifts(LPCHARACTER ch, const std::vector<Gift>& gifts)
	{
		if (gifts.empty())
			return;
		if (gifts.size() == 1)
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF gift %u %u %u", gifts[0].vnum, gifts[0].count, gifts[0].rare ? 1 : 0);
			return;
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF giftsbegin %u", (unsigned int)gifts.size());
		std::string line;
		for (size_t i = 0; i < gifts.size(); ++i)
		{
			char part[48];
			snprintf(part, sizeof(part), "%u|%u|%d#", gifts[i].vnum, gifts[i].count, gifts[i].rare ? 1 : 0);
			if (line.size() + strlen(part) > 400)
			{
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF gifts %s", line.c_str());
				line.clear();
			}
			line += part;
		}
		if (!line.empty())
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF gifts %s", line.c_str());
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF giftsend");
	}

	enum { CLAIM_NONE = 0, CLAIM_GIVEN = 1, CLAIM_NO_ROOM = -1 };

	// Gives one pending spin (all its rewards), once: the core whose UPDATE
	// changes the row. What was given is added to `got` (the caller tells the
	// window). Without room for even the first reward the row is left pending;
	// rewards that do not fit after it go into a new pending row.
	int Claim(LPCHARACTER ch, DWORD spinId, std::vector<Gift>& got, bool quiet)
	{
		char query[256];
		snprintf(query, sizeof(query),
				"SELECT vnum, count, rare%s FROM player.wheel_spin WHERE id=%u AND pid=%u AND state=0",
				s_bMulti ? ", rewards" : "", spinId, ch->GetPlayerID());
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return CLAIM_NONE;
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		if (!row)
			return CLAIM_NONE;
		DWORD vnum = 0, count = 1, rare = 0;
		str_to_number(vnum, row[0]);
		str_to_number(count, row[1]);
		str_to_number(rare, row[2]);
		std::vector<Gift> gifts;
		if (s_bMulti && row[3] && *row[3])
			ParseGifts(row[3], gifts);
		if (gifts.empty() && vnum)
		{
			Gift g;
			g.vnum = vnum;
			g.count = std::max<DWORD>(1, count);
			g.rare = rare != 0;
			gifts.push_back(g);
		}
		if (!gifts.empty())
		{
			const TItemTable* first = ITEM_MANAGER::instance().GetTable(gifts[0].vnum);
			if (first && ch->GetEmptyInventory(first->bSize) < 0)
			{
				if (!quiet)
					ch->ChatPacket(CHAT_TYPE_INFO, "Kolo Fortuny: zrob miejsce w ekwipunku - nagroda czeka.");
				return CLAIM_NO_ROOM;
			}
		}
		snprintf(query, sizeof(query),
				"UPDATE player.wheel_spin SET state=1, given=NOW() WHERE id=%u AND pid=%u AND state=0",
				spinId, ch->GetPlayerID());
		std::unique_ptr<SQLMsg> taken(AccountDB::instance().DirectQuery(query));
		if (!taken.get() || taken->uiSQLErrno != 0 || !taken->Get() || taken->Get()->uiAffectedRows != 1)
			return CLAIM_NONE;

		size_t given = 0;
		for (; given < gifts.size(); ++given)
		{
			const TItemTable* t = ITEM_MANAGER::instance().GetTable(gifts[given].vnum);
			if (!t)
				continue;	// an item this world lost since the spin
			if (given > 0 && ch->GetEmptyInventory(t->bSize) < 0)
				break;
			ch->AutoGiveItem(gifts[given].vnum, (ITEM_COUNT)gifts[given].count);
			got.push_back(gifts[given]);
		}
		sys_log(0, "WHEEL: %s (pid %u) got %u of %u reward(s) from spin %u (shown %u x%u%s)", ch->GetName(), ch->GetPlayerID(),
				(unsigned int)given, (unsigned int)gifts.size(), spinId, vnum, count, rare ? ", rare" : "");

		if (given < gifts.size())
		{
			// The rest waits as a pending row of its own (nothing was paid for it).
			const std::string rest = FormatGifts(gifts, given);
			std::string insert = "INSERT INTO player.wheel_spin (pid, items, slot, vnum, count, rare, cost_vnum, cost_count, rewards, spins) VALUES (";
			char head[160];
			snprintf(head, sizeof(head), "%u, '', 0, %u, %u, %d, 0, 0, '", ch->GetPlayerID(), gifts[given].vnum, gifts[given].count,
					gifts[given].rare ? 1 : 0);
			insert += head;
			insert += rest;
			snprintf(head, sizeof(head), "', %u)", (unsigned int)(gifts.size() - given));
			insert += head;
			std::unique_ptr<SQLMsg> kept(AccountDB::instance().DirectQuery(insert.c_str()));
			if (kept.get() && kept->uiSQLErrno == 0 && kept->Get() && kept->Get()->uiInsertID)
			{
				if (!quiet)
					ch->ChatPacket(CHAT_TYPE_INFO, "Kolo Fortuny: brak miejsca - %u nagrod czeka. Zrob miejsce i otworz kolo ponownie.",
							(unsigned int)(gifts.size() - given));
			}
			else
			{
				// Not written: given all the same (never lost).
				sys_err("WHEEL: the rest of spin %u of %s not written - given without a room check", spinId, ch->GetName());
				for (; given < gifts.size(); ++given)
				{
					if (!ITEM_MANAGER::instance().GetTable(gifts[given].vnum))
						continue;
					ch->AutoGiveItem(gifts[given].vnum, (ITEM_COUNT)gifts[given].count);
					got.push_back(gifts[given]);
				}
			}
		}
		return CLAIM_GIVEN;
	}

	// Every pending spin of the player, given now (until one finds no room).
	int ClaimAll(LPCHARACTER ch, std::vector<Gift>& got, bool quiet)
	{
		char query[160];
		snprintf(query, sizeof(query),
				"SELECT id FROM player.wheel_spin WHERE pid=%u AND state=0 ORDER BY id LIMIT 20", ch->GetPlayerID());
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return 0;
		std::vector<DWORD> ids;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			DWORD id = 0;
			str_to_number(id, row[0]);
			if (id)
				ids.push_back(id);
		}
		int given = 0;
		for (size_t i = 0; i < ids.size(); ++i)
		{
			const int result = Claim(ch, ids[i], got, quiet);
			if (result == CLAIM_NO_ROOM)
				break;
			if (result == CLAIM_GIVEN)
				++given;
		}
		return given;
	}

	EVENTINFO(wheel_tick_info)
	{
		int dummy;
	};

	// Every minute: the spins nobody claimed, of players on this core.
	EVENTFUNC(wheel_tick)
	{
		char query[200];
		snprintf(query, sizeof(query),
				"SELECT id, pid FROM player.wheel_spin WHERE state=0 AND created < NOW() - INTERVAL %d SECOND "
				"ORDER BY id LIMIT 100", SETTLE_AFTER_SECONDS);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (msg.get() && msg->uiSQLErrno == 0 && msg->Get() && msg->Get()->pSQLResult)
		{
			std::vector<std::pair<DWORD, DWORD> > pending;
			MYSQL_ROW row;
			while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				DWORD id = 0, pid = 0;
				str_to_number(id, row[0]);
				str_to_number(pid, row[1]);
				pending.push_back(std::make_pair(id, pid));
			}
			for (size_t i = 0; i < pending.size(); ++i)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pending[i].second);
				if (ch && Eligible(ch) && ch->GetSectree())
				{
					std::vector<Gift> got;
					Claim(ch, pending[i].first, got, true);
					SendGifts(ch, got);
				}
			}
		}
		for (std::map<DWORD, DWORD>::iterator it = s_mapLastCommand.begin(); it != s_mapLastCommand.end(); )
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(it->first))
				s_mapLastCommand.erase(it++);
			else
				++it;
		}
		return PASSES_PER_SEC(60);
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		wheel_tick_info* info = AllocEventInfo<wheel_tick_info>();
		s_pkTick = event_create(wheel_tick, info, PASSES_PER_SEC(60));
	}

	void SendInfo(LPCHARACTER ch)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF info %d %u %u %u", s_bEnabled ? 1 : 0, s_dwCostVnum, s_dwCostCount,
				(unsigned int)ch->CountSpecifyItem(s_dwCostVnum));
	}

	// The window: anything pending given, the price, and the pool with its
	// chances (the info button lists them; the idle wheel shows them).
	void Open(LPCHARACTER ch)
	{
		Load(false);
		EnsureTick();
		{
			std::vector<Gift> got;
			ClaimAll(ch, got, false);
			SendGifts(ch, got);
		}
		SendInfo(ch);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF poolbegin %llu", s_ullWeights);
		std::string line;
		for (size_t i = 0; i < s_vecRewards.size(); ++i)
		{
			const Reward& r = s_vecRewards[i];
			const unsigned int chance = s_ullWeights ? (unsigned int)((unsigned long long)r.weight * 10000ULL / s_ullWeights) : 0;
			char part[64];
			snprintf(part, sizeof(part), "%u|%u|%d|%u#", r.vnum, r.count, r.rare ? 1 : 0, chance);
			if (line.size() + strlen(part) > 400)
			{
				ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF pool %s", line.c_str());
				line.clear();
			}
			line += part;
		}
		if (!line.empty())
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF pool %s", line.c_str());
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF poolend");
	}

	void Fail(LPCHARACTER ch, const char* text)
	{
		if (text)
			ch->ChatPacket(CHAT_TYPE_INFO, "Kolo Fortuny: %s", text);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF fail");
	}

	// spins: 1, or one of SPIN_COUNTS - that many tickets' worth and rewards,
	// one turn of the wheel.
	void Spin(LPCHARACTER ch, int spins)
	{
		Load(false);
		EnsureTick();
		if (!s_bEnabled)
			return Fail(ch, "kolo jest teraz wylaczone.");
		if (!ValidSpinCount(spins))
			return Fail(ch, "niepoprawna liczba losowan.");
		if (spins > 1 && !s_bMulti)
			return Fail(ch, "wiele losowan naraz jest teraz niedostepne.");
		if (!ch->CanHandleItem())
			return Fail(ch, "najpierw zamknij handel, sklep lub ulepszanie.");
		// A spin the window never claimed is given before a new one.
		{
			std::vector<Gift> got;
			ClaimAll(ch, got, false);
			SendGifts(ch, got);
		}
		const DWORD cost = std::max<DWORD>(1, s_dwCostCount) * (DWORD)spins;
		if (!s_dwCostVnum || (DWORD)ch->CountSpecifyItem(s_dwCostVnum) < cost)
		{
			char text[128];
			const TItemTable* ticket = ITEM_MANAGER::instance().GetTable(s_dwCostVnum);
			snprintf(text, sizeof(text), "potrzebujesz %u x %s (ItemShop).", cost,
					ticket ? ticket->szLocaleName : "Bilet Kola Fortuny");
			SendInfo(ch);
			return Fail(ch, text);
		}
		if (s_vecRewards.empty() || s_ullWeights == 0)
			return Fail(ch, "brak nagrod - sprobuj pozniej.");
		// The rewards, each drawn by weight; the wheel shows the first rare one,
		// or the first.
		std::vector<size_t> rolls;
		size_t shown = 0;
		bool shownRare = false;
		for (int i = 0; i < spins; ++i)
		{
			const size_t won = Roll();
			if (!shownRare && s_vecRewards[won].rare)
			{
				shown = rolls.size();
				shownRare = true;
			}
			rolls.push_back(won);
		}
		// The shown reward first: it is the one a claim needs room for.
		std::swap(rolls[0], rolls[shown]);
		std::vector<Slot> slots;
		int winSlot = 0;
		Layout(rolls[0], slots, winSlot);
		const TItemTable* prize = ITEM_MANAGER::instance().GetTable(slots[winSlot].vnum);
		if (!prize || ch->GetEmptyInventory(prize->bSize) < 0)
			return Fail(ch, "zrob miejsce w ekwipunku.");
		const std::string items = FormatGifts(slots, 0);
		std::string rewards;
		if (spins > 1)
		{
			std::vector<Gift> all;
			for (size_t i = 0; i < rolls.size(); ++i)
			{
				Gift g;
				g.vnum = s_vecRewards[rolls[i]].vnum;
				g.count = s_vecRewards[rolls[i]].count;
				g.rare = s_vecRewards[rolls[i]].rare;
				all.push_back(g);
			}
			rewards = FormatGifts(all, 0);
		}
		ch->RemoveSpecifyItem(s_dwCostVnum, cost);
		char head[512];
		snprintf(head, sizeof(head), "%u, '%s', %d, %u, %u, %d, %u, %u",
				ch->GetPlayerID(), items.c_str(), winSlot, slots[winSlot].vnum, slots[winSlot].count,
				slots[winSlot].rare ? 1 : 0, s_dwCostVnum, cost);
		std::string query = "INSERT INTO player.wheel_spin (pid, items, slot, vnum, count, rare, cost_vnum, cost_count";
		if (spins > 1)
			query += ", rewards, spins";
		query += ") VALUES (";
		query += head;
		if (spins > 1)
		{
			char tail[32];
			snprintf(tail, sizeof(tail), "', %d", spins);
			query += ", '";
			query += rewards;
			query += tail;
		}
		query += ")";
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query.c_str()));
		const DWORD spinId = (msg.get() && msg->uiSQLErrno == 0 && msg->Get()) ? msg->Get()->uiInsertID : 0;
		if (!spinId)
		{
			// Not written: the tickets back, nothing drawn.
			ch->AutoGiveItem(s_dwCostVnum, (ITEM_COUNT)cost);
			sys_err("WHEEL: spin of %s not written, ticket returned", ch->GetName());
			return Fail(ch, "blad bazy - bilet zwrocony.");
		}
		sys_log(0, "WHEEL: %s (pid %u) spin %u x%d: slot %d, %u x%u", ch->GetName(), ch->GetPlayerID(), spinId, spins, winSlot,
				slots[winSlot].vnum, slots[winSlot].count);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF items %u %s", spinId, items.c_str());
		if (spins > 1)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF spin %u %d %d", spinId, winSlot, spins);
		else
			ch->ChatPacket(CHAT_TYPE_COMMAND, "WOF spin %u %d", spinId, winSlot);
		SendInfo(ch);
	}
}

// "/kolo" (the window), "/kolo krec [n]", "/kolo odbierz <id>", and for a GM
// "/kolo przeladuj" (server-patches/playerqol, MT2009_PLUS_WHEEL_V1).
void WheelCommand(LPCHARACTER ch, const char* argument)
{
	if (!mt2009_wheel::Eligible(ch))
		return;
	char sub[32], arg[32];
	const char* rest = one_argument(argument, sub, sizeof(sub));
	one_argument(rest, arg, sizeof(arg));
	if (!*sub || !strcmp(sub, "otworz"))
		mt2009_wheel::Open(ch);
	else if (!strcmp(sub, "krec"))
	{
		if (mt2009_wheel::TooSoon(ch))
			return mt2009_wheel::Fail(ch, NULL);
		int spins = 1;	// MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]: "/kolo krec <n>"
		if (*arg)
			str_to_number(spins, arg);
		mt2009_wheel::Spin(ch, spins);
	}
	else if (!strcmp(sub, "odbierz"))
	{
		DWORD id = 0;
		str_to_number(id, arg);
		mt2009_wheel::Load(false);
		std::vector<mt2009_wheel::Gift> got;
		if (!id || mt2009_wheel::Claim(ch, id, got, false) == mt2009_wheel::CLAIM_NONE)
			mt2009_wheel::ClaimAll(ch, got, false);
		mt2009_wheel::SendGifts(ch, got);
		mt2009_wheel::SendInfo(ch);
	}
	else if (!strcmp(sub, "przeladuj") && ch->GetGMLevel() > GM_PLAYER)
	{
		mt2009_wheel::Load(true);
		ch->ChatPacket(CHAT_TYPE_INFO, "Kolo Fortuny: nagrody wczytane ponownie (%u).",
				(unsigned int)mt2009_wheel::s_vecRewards.size());
	}
}
