#ifndef __INC_METIN2_PLAYERBOT_RANK_POINTS_H__
#define __INC_METIN2_PLAYERBOT_RANK_POINTS_H__

// Punkty Rangi - ONE scale of rank points (MT2009_PLUS_RANK_POINTS_V2; V1 kept
// a separate counter next to the alignment).
//
// Arezzo's "dodatkowe rangi" (its fruits 80050-80054, their icons and names, the
// rank names and their colours come from the Arezzo client), with the owner's
// numbers (6 October). V2 (the owner, 6 October: "rangi arezzo maja byc
// kontynuacja punktow rangi zwyklej, ktore sa do 20000, a od 20000 zaczynaja
// sie punkty arezzo"):
//
//   * The scale: the game's own alignment ("Punkty Rangi", shown as
//     GetRealAlignment() / 10, -20 000 .. +20 000) is the bottom of the scale;
//     the Arezzo points above it are kept per player (player.mt2009_rank_points,
//     the "extra", 0 .. 180 000). The total, the only number a player sees:
//         total = alignment              while alignment < 20 000
//         total = 20 000 + extra         once alignment stands at its cap (20 000)
//     When the alignment drops below 20 000 again (a player killed, a skill
//     bought with rank), the extra stays stored but counts for nothing - the
//     total is the alignment, the rank's bonus and title are gone - until the
//     alignment is back at 20 000, when the extra counts again at once.
//   * Fruits: Metins and bosses drop 1-2 pieces at 30%, the fruit of the KILLED
//     monster's level band: Jablko 1-53 (to the Orc Valley), Gruszka 54-74,
//     Winogrono 75-99, Arbuz 100-109, Ananas 110 and up. A player's on the
//     ground for the killer (two minutes), a bot's into its bag (a full bag
//     gets nothing). Log [RANGA_DROP].
//   * A fruit works only in its range of the total: Jablko 0-20 000 (+200 to the
//     ALIGNMENT itself - UpdateAlignment(+2000), up to the engine's cap), Gruszka
//     20 000-40 000 (+200), Winogrono 40 000-80 000 (+400), Arbuz 80 000-120 000
//     (+400), Ananas 120 000-200 000 (+400) (the owner, 6 October: four times
//     V1's 50 / 50 / 100 / 100 / 100) - these four to the extra, so only
//     with the alignment at 20 000; 200 000 is the cap. Out of its range it is
//     refused with the fruit wanted now; under 0 (a negative alignment) with
//     "fruits work from 0". Log [RANGA_USE].
//   * The rank's bonus by the total, one tier at a time (not added up), on
//     hidden affects of type AFFECT_RANK_POINTS (580; 500-599 survive a death),
//     put right at login, after every fruit, whenever the alignment crosses its
//     cap (CHARACTER::UpdateAlignment, RankPointsOnAlignment) and every few
//     seconds while the affects are not loaded yet:
//         21 000 Waleczny    +10% monsters, +10% people,                           +1000 HP
//         31 000 Mocarny     +12% / +12%,                                          +1500 HP
//         41 000 Potezny     +15% / +15%,                                          +1900 HP
//         51 000 Wladca      +18% / +18%,                                          +2200 HP
//         81 000 Arcymistrz  +18% / +18%, +10% Metins,                             +2900 HP
//        101 000 Legenda     +18% / +18%, +15% Metins, +10% bosses,                +3500 HP
//        121 000 Legenda     +18% / +18%, +15% Metins, +15% bosses,                +4000 HP
//        200 000 Legenda     +20% / +20%, +18% Metins, +18% bosses, +10% average   +5000 HP
//     (POINT_ATTBONUS_MONSTER, _HUMAN, _STONE, _BOSS, POINT_NORMAL_HIT_DAMAGE_BONUS
//     - "srednie obrazenia" - and POINT_MAX_HP). Under 20 000 the total can not
//     reach a tier, so only the alignment's crossing of its cap changes one.
//   * The title: from 21 000 the rank's name, in its colour, stands where the
//     alignment title stood. The client hears "RANGA tail <vid> <tier>" when a
//     character comes into its view (char.cpp, EncodeInsertPacket) and around
//     a character whose tier changes; "RANGA self <total> <tier>" tells the
//     player its own total (the character window's alignment tooltip shows ONE
//     "Punkty Rangi: <total>"; under 20 000 the client takes its live alignment,
//     so "self" is sent at login, after a fruit or /ranga ustaw and when the
//     alignment crosses its cap). Tier 0: the alignment title as before.
//     Client: root/rankpoints.py; the exe's chrmgr.SetRankTitle
//     (client-patches/exe, ENABLE_RANK_TITLE), with an older exe the title is
//     put back over the alignment's every half second.
//   * Storage: player.mt2009_rank_points (pid, points = the extra, scale), read
//     at login (a bot: at its first look on this core), written after every
//     change. Migration from V1 (whose points were the whole separate scale,
//     0..200 000): rows with scale = 1 (the column's default - V1 never wrote
//     it, so a row an old binary writes later is caught too) become
//     extra = max(0, points - 20 000), scale = 2; once at the first table use
//     on a core (EnsureTable) and again on reading such a row (Load).
//     Idempotent. The alignment itself is the engine's (player.alignment).
//   * /ranga: the player's total, rank, bonus and the fruit wanted now. A GM
//     (GM_HIGH_WIZARD): /ranga ustaw <nick> <total> - under 20 000 it sets the
//     alignment (and the extra to 0), from 20 000 the alignment to its cap and
//     the extra to total - 20 000.
//   * Bots: their kills' fruits into the bag; one that fits their total is
//     eaten at their next look (ManagePlayerBotRankPoints), any other goes on
//     their counter at the tier's price (GetPlayerBotRankFruitPrice) or to the
//     merchant from a bot with no counter (playerbot_economy.h / _town.h).
//   * M2_RANK_POINTS=0 (the game container's environment) switches the system
//     off: no drops, the fruits do nothing, the bonuses and titles come off at
//     the next login (the alignment works as in the base game).
//
// The engine's calls are server-patches/rankpoints (edits.json).

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <map>
#include <memory>
#include <set>
#include <string>

namespace mt2009_rankp
{
	const DWORD AFFECT_RANK_POINTS = 580;
	const int POINTS_MAX = 200000;		// the total's cap
	const int ALIGN_CAP = 20000;		// the alignment's cap as shown (the engine's 200 000 / 10)
	const int ALIGN_UNIT = 10;		// engine alignment units a shown point
	const int EXTRA_MAX = POINTS_MAX - ALIGN_CAP;
	const int DROP_PERCENT = 30;
	const int SYNC_TICK_SEC = 5;

	struct SFruit
	{
		DWORD vnum;
		const char* name;		// CP1250
		int maxLevel;			// the killed monster's level band's top
		int from, to;			// the range of points it works in: from <= points < to
		int gain;
	};

	const SFruit FRUITS[] =
	{
		{ 80050, "Jab" "\xb3" "ko",    53,      0,  20000, 200 },	// the alignment itself
		{ 80051, "Gruszka",   74,  20000,  40000, 200 },	// these four: the extra
		{ 80052, "Winogrono", 99,  40000,  80000, 400 },
		{ 80053, "Arbuz",    109,  80000, 120000, 400 },
		{ 80054, "Ananas",  1000, 120000, 200000, 400 },
	};
	const int FRUIT_COUNT = (int)(sizeof(FRUITS) / sizeof(FRUITS[0]));

	enum EBonus { B_MONSTER, B_HUMAN, B_STONE, B_BOSS, B_NORMAL_HIT, B_HP, B_COUNT };
	const BYTE BONUS_POINTS[B_COUNT] =
	{
		POINT_ATTBONUS_MONSTER, POINT_ATTBONUS_HUMAN, POINT_ATTBONUS_STONE, POINT_ATTBONUS_BOSS,
		POINT_NORMAL_HIT_DAMAGE_BONUS, POINT_MAX_HP
	};

	struct STier
	{
		int from;
		const char* name;		// CP1250
		long bonus[B_COUNT];
	};

	// Tier 0: under 21 000, nothing.
	// MT2009_RANK_BADGES_V4
	const STier TIERS[] =
	{
		{0, "", {0,0,0,0,0,0}},
		{0, "Turysta z M1", {0,0,0,0,0,0}},
		{1000, "Klepacz Dzik\363w", {0,0,0,0,0,0}},
		{3000, "S\271siad Kowala", {0,0,0,0,0,0}},
		{6000, "Sponsor Kowala", {0,0,0,0,0,0}},
		{10000, "Czytelnik Nieudanych KU", {0,0,0,0,0,0}},
		{16000, "M\263ot na Metiny", {0,0,0,0,0,0}},
		{30000, "Sta\263y Klient Dozorcy", {0,0,0,0,0,0}},
		{50000, "Lokator Loch\363w", {0,0,0,0,0,0}},
		{80000, "Windykator Boss\363w", {0,0,0,0,0,0}},
		{110000, "Postrach Serwera", {0,0,0,0,0,0}},
		{150000, "Ostatni Przed Emerytur\271", {0,0,0,0,0,0}},
		{200000, "Emeryt Olimpu", {0,0,0,0,0,0}},
	};
	const int TIER_COUNT = (int)(sizeof(TIERS) / sizeof(TIERS[0]));

	// The players' texts, CP1250 as escapes (a hex digit never follows one -
	// the literals are split there).
	const char* const MSG_DISABLED = "Punkty Rangi s" "\xb9" " wy" "\xb3" "\xb9" "czone na tym serwerze.";
	const char* const MSG_MAX = "Masz ju" "\xbf" " maksymaln" "\xb9" " liczb" "\xea" " Punkt" "\xf3" "w Rangi (200 000).";
	const char* const MSG_WRONG = "Ten owoc teraz nie zadzia" "\xb3" "a. Masz %d Punkt" "\xf3" "w Rangi - teraz potrzebujesz: %s (od %d do %d punkt" "\xf3" "w).";
	const char* const MSG_GAIN = "Punkty Rangi: +%d (masz %d / 200 000).";
	const char* const MSG_TIER_UP = "Awansujesz na rang" "\xea" ": %s!";
	const char* const MSG_INFO = "Ranga: %s, Punkty Rangi: %d / 200 000.";
	const char* const MSG_INFO_NONE = "Ranga: brak (ujemne punkty). Punkty Rangi: %d / 200 000.";
	const char* const MSG_NEXT = "Nast" "\xea" "pna ranga: %s od %d punkt" "\xf3" "w. Teraz jedz: %s (+%d za sztuk" "\xea" ").";
	const char* const MSG_NEXT_MAX = "To najwy" "\xbf" "sza ranga.";
	const char* const MSG_FRUITS = "Owoce wypadaj" "\xb9" " z Metin" "\xf3" "w i boss" "\xf3" "w (30%%, 1-2 szt.): Jab" "\xb3" "ko do 53 poz., Gruszka 54-74, Winogrono 75-99, Arbuz 100-109, Ananas od 110.";
	const char* const MSG_BONUS_HEAD = "Bonus rangi:";
	const char* const MSG_SET_USAGE = "U" "\xbf" "ycie: /ranga ustaw <nick> <punkty>";
	const char* const MSG_SET_NOBODY = "Nie ma takiej postaci na tym rdzeniu.";
	const char* const MSG_SET_DONE = "%s: Punkty Rangi = %d.";
	const char* const MSG_NEGATIVE = "Masz %d Punkt" "\xf3" "w Rangi - owoce rangi dzia" "\xb3" "aj" "\xb9" " dopiero od 0. Najpierw podnie" "\x9c" " rang" "\xea" " (np. zabijaj" "\xb9" "c potwory).";
	const char* const MSG_SCALE = "Do 20 000 to zwyk" "\xb3" "a ranga (podnosi j" "\xb9" " Jab" "\xb3" "ko), od 20 000 dalej licz" "\xb9" " si" "\xea" " punkty Arezzo (Gruszka, Winogrono, Arbuz, Ananas).";
	const char* const MSG_KEPT = "Zachowane punkty ponad 20 000: %d - licz" "\xb9" " si" "\xea" " znowu, gdy ranga wr" "\xf3" "ci do 20 000.";

	// ---------------------------------------------------------------- the switch

	// M2_RANK_POINTS in the game container's environment, read once: on unless
	// "0", "off", "no" or "false".
	bool Enabled()
	{
		static int s_enabled = -1;
		if (s_enabled < 0)
		{
			const char* value = getenv("M2_RANK_POINTS");
			s_enabled = 1;
			if (value && (!strcmp(value, "0") || !strcasecmp(value, "off") || !strcasecmp(value, "no") || !strcasecmp(value, "false")))
				s_enabled = 0;
			sys_log(0, "RANK_POINTS: %s (M2_RANK_POINTS=%s)", s_enabled ? "on" : "off", value ? value : "");
		}
		return s_enabled != 0;
	}

	// ---------------------------------------------------------------- tables

	const SFruit* FruitByVnum(DWORD vnum)
	{
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if (FRUITS[i].vnum == vnum)
				return &FRUITS[i];
		return NULL;
	}

	// The fruit that works at these points (NULL at the cap).
	const SFruit* FruitForPoints(int points)
	{
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if (points >= FRUITS[i].from && points < FRUITS[i].to)
				return &FRUITS[i];
		return NULL;
	}

	const SFruit* FruitForLevel(int level)
	{
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if (level <= FRUITS[i].maxLevel)
				return &FRUITS[i];
		return &FRUITS[FRUIT_COUNT - 1];
	}

	int TierOf(int points)
	{
		int tier = 0;
		for (int i = 1; i < TIER_COUNT; ++i)
			if (points >= TIERS[i].from)
				tier = i;
		return tier;
	}

	// ---------------------------------------------------------------- the points

	// A character's stored Arezzo points above 20 000 (the "extra"; the total
	// adds them only while the alignment stands at its cap - the header).
	struct SEntry
	{
		int extra;
		const void* who;		// the CHARACTER read for: a bot is read again when it comes back as another
		SEntry() : extra(0), who(NULL) {}
	};

	std::map<DWORD, SEntry> s_points;		// pid -> extra, characters read on this core
	std::map<DWORD, int> s_needSync;		// pids whose bonuses wait for their affects -> since when
	LPEVENT s_pkTick = NULL;
	bool s_bOwnAlignment = false;			// our own UpdateAlignment: RankPointsOnAlignment leaves it to us

	bool IsBot(LPCHARACTER ch)
	{
		return CPlayerBotManager::instance().IsManaged(ch->GetPlayerID());
	}

	bool Counts(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetPlayerID() != 0;
	}

	// The alignment as the game shows it (-20 000 .. 20 000).
	int AlignmentShown(LPCHARACTER ch)
	{
		return ch->GetRealAlignment() / ALIGN_UNIT;
	}

	int TotalOf(int alignmentShown, int extra)
	{
		return alignmentShown < ALIGN_CAP ? alignmentShown : ALIGN_CAP + std::max(0, std::min(extra, EXTRA_MAX));
	}

	// V1's whole separate scale -> V2's extra above 20 000.
	int MigrateV1(int points)
	{
		return std::max(0, std::min(points, POINTS_MAX) - ALIGN_CAP);
	}

	void EnsureTable()
	{
		static bool s_done = false;
		if (s_done)
			return;
		s_done = true;
		std::unique_ptr<SQLMsg> create(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS player.mt2009_rank_points ("
				"pid INT UNSIGNED NOT NULL PRIMARY KEY, "
				"points INT NOT NULL DEFAULT 0, "
				"scale TINYINT NOT NULL DEFAULT 1, "
				"updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
				") ENGINE=InnoDB"));
		// V1's table: no scale column - its rows get 1 (the old scale).
		std::unique_ptr<SQLMsg> alter(DBManager::instance().DirectQuery(
				"ALTER TABLE player.mt2009_rank_points ADD COLUMN IF NOT EXISTS scale TINYINT NOT NULL DEFAULT 1 AFTER points"));
		std::unique_ptr<SQLMsg> migrate(DBManager::instance().DirectQuery(
				"UPDATE player.mt2009_rank_points SET points = GREATEST(0, LEAST(points, %d) - %d), scale = 2 WHERE scale = 1",
				POINTS_MAX, ALIGN_CAP));
		const unsigned long long rows = (migrate.get() && migrate->Get()) ? (unsigned long long)migrate->Get()->uiAffectedRows : 0ULL;
		sys_log(0, "[RANGA_MIGRATE] V1 rows moved to the V2 scale (extra = points - 20000): %llu", rows);
	}

	// The character's extra from the table (synchronous: at login, or a bot's first look).
	int Load(LPCHARACTER ch)
	{
		EnsureTable();
		int extra = 0;
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"SELECT points, scale FROM player.mt2009_rank_points WHERE pid=%u", ch->GetPlayerID()));
		if (msg.get() && msg->Get() && msg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
			if (row && row[0])
			{
				extra = atoi(row[0]);
				if (!row[1] || atoi(row[1]) < 2)	// written by a V1 binary after the migration
				{
					extra = MigrateV1(extra);
					DBManager::instance().Query("UPDATE player.mt2009_rank_points SET points=%d, scale=2 WHERE pid=%u AND scale<2",
							extra, ch->GetPlayerID());
				}
			}
		}
		extra = std::max(0, std::min(extra, EXTRA_MAX));
		SEntry& e = s_points[ch->GetPlayerID()];
		e.extra = extra;
		e.who = ch;
		return extra;
	}

	bool Known(LPCHARACTER ch)
	{
		std::map<DWORD, SEntry>::const_iterator it = s_points.find(ch->GetPlayerID());
		return it != s_points.end() && it->second.who == ch;
	}

	int Extra(LPCHARACTER ch)
	{
		std::map<DWORD, SEntry>::const_iterator it = s_points.find(ch->GetPlayerID());
		return (it != s_points.end() && it->second.who == ch) ? it->second.extra : Load(ch);
	}

	// The extra of a character in view, without asking the table (0 when not read yet).
	int KnownExtra(LPCHARACTER ch)
	{
		std::map<DWORD, SEntry>::const_iterator it = s_points.find(ch->GetPlayerID());
		return it != s_points.end() ? it->second.extra : 0;
	}

	// The total (the one number the player sees), the extra read when it is not yet.
	int Points(LPCHARACTER ch)
	{
		return TotalOf(AlignmentShown(ch), Extra(ch));
	}

	// The total without asking the table.
	int KnownPoints(LPCHARACTER ch)
	{
		return TotalOf(AlignmentShown(ch), KnownExtra(ch));
	}

	void Save(LPCHARACTER ch, int extra)
	{
		DBManager::instance().Query("REPLACE INTO player.mt2009_rank_points (pid, points, scale) VALUES (%u, %d, 2)",
				ch->GetPlayerID(), extra);
	}

	// ---------------------------------------------------------------- the bonus


	// RANK_CUMULATIVE_REWARDS_V4
	const int REWARD_THRESHOLDS[] = {0,1000,3000,6000,10000,16000,30000,50000,80000,110000,150000,200000};
	const BYTE REWARD_POINTS[] = {
		POINT_DEF_GRADE_BONUS,
		POINT_RESIST_FIRE, POINT_RESIST_ICE, POINT_RESIST_WIND,
		POINT_RESIST_EARTH, POINT_RESIST_ELEC, POINT_RESIST_DARK,
		POINT_ENCHANT_FIRE, POINT_ENCHANT_ICE, POINT_ENCHANT_WIND,
		POINT_ENCHANT_EARTH, POINT_ENCHANT_ELECT, POINT_ENCHANT_DARK,
		POINT_ATT_SPEED, POINT_MOV_SPEED, POINT_ATTBONUS_STONE
	};
	const int REWARD_COUNT = sizeof(REWARD_POINTS) / sizeof(REWARD_POINTS[0]);
	int RewardStage(int points)
	{
		int stage = 0;
		for (int i = 0; i < 12; ++i)
			if (points >= REWARD_THRESHOLDS[i]) stage = i + 1;
		return stage;
	}
	long RewardValue(int stage, int index)
	{
		if (index == 0) return stage * 30 / 12;
		if (index <= 12) return stage * 20 / 12;
		if (index <= 14) return (stage / 2) * 10 / 6;
		return stage / 2;
	}

	void EnsureTick();

	// The tier's bonus on the character's affects: put on, changed or taken off.
	void SyncBonuses(LPCHARACTER ch)
	{
		if (!ch->IsLoadedAffect())
		{
			s_needSync.insert(std::make_pair(ch->GetPlayerID(), (int)get_global_time()));
			EnsureTick();
			return;
		}
		s_needSync.erase(ch->GetPlayerID());
		const BYTE obsolete[] = {POINT_ATTBONUS_MONSTER, POINT_ATTBONUS_HUMAN,
			POINT_ATTBONUS_BOSS, POINT_NORMAL_HIT_DAMAGE_BONUS, POINT_MAX_HP};
		for (unsigned int i = 0; i < sizeof(obsolete) / sizeof(obsolete[0]); ++i)
			while (CAffect* aff = ch->FindAffect(AFFECT_RANK_POINTS, obsolete[i]))
				ch->RemoveAffect(aff);
		const int stage = Enabled() ? RewardStage(KnownPoints(ch)) : 0;
		for (int i = 0; i < REWARD_COUNT; ++i)
		{
			const long want = RewardValue(stage, i);
			CAffect* aff = ch->FindAffect(AFFECT_RANK_POINTS, REWARD_POINTS[i]);
			if (want <= 0)
			{
				if (aff) ch->RemoveAffect(aff);
				continue;
			}
			if (aff && aff->lApplyValue == want) continue;
			ch->AddAffect(AFFECT_RANK_POINTS, REWARD_POINTS[i], want, 0,
				INFINITE_AFFECT_DURATION, 0, true, true);
		}
	}

	// ---------------------------------------------------------------- to the client

	// "RANGA self <total> <tier>"; switched off: the alignment and no tier.
	void SendSelf(LPCHARACTER ch)
	{
		if (!ch->GetDesc() || IsBot(ch))
			return;
		const int points = Enabled() ? KnownPoints(ch) : AlignmentShown(ch);
		ch->ChatPacket(CHAT_TYPE_COMMAND, "RANGA self %d %d", points, Enabled() ? TierOf(points) : 0);
	}

	// "RANGA tail <vid> <tier>" to everyone who sees ch, ch itself too.
	void SendTailAround(LPCHARACTER ch)
	{
		if (!ch->GetSectree())
			return;
		const int tier = Enabled() ? TierOf(KnownPoints(ch)) : 0;
		char command[64];
		int len = snprintf(command, sizeof(command), "RANGA tail %u %d", (unsigned int)ch->GetVID(), tier);
		if (len <= 0 || len >= (int)sizeof(command))
			return;
		++len;   // the trailing NUL every chat packet carries
		TPacketGCChat pack;
		pack.header = HEADER_GC_CHAT;
		pack.size = sizeof(TPacketGCChat) + len;
		pack.type = CHAT_TYPE_COMMAND;
		pack.id = 0;
		pack.bEmpire = 0;
		TEMP_BUFFER buf;
		buf.write(&pack, sizeof(TPacketGCChat));
		buf.write(command, len);
		ch->PacketAround(buf.read_peek(), buf.size());
	}

	// ---------------------------------------------------------------- the points change

	// After the total changed (from tier `before`): the bonus, the player's own
	// line, the title around when the tier moved. Returns the new tier.
	int Refresh(LPCHARACTER ch, int before, bool tell)
	{
		const int points = KnownPoints(ch);
		const int tier = TierOf(points);
		SyncBonuses(ch);
		SendSelf(ch);
		if (tier != before)
		{
			SendTailAround(ch);
			if (tell && tier > before)
				ch->ChatPacket(CHAT_TYPE_INFO, MSG_TIER_UP, TIERS[tier].name);
			sys_log(0, "[RANGA_TIER] pid=%u name=%s points=%d alignment=%d extra=%d tier=%d->%d bot=%d",
					ch->GetPlayerID(), ch->GetName(), points, AlignmentShown(ch), KnownExtra(ch), before, tier,
					IsBot(ch) ? 1 : 0);
		}
		return tier;
	}

	// The alignment moved to `shown` (engine units x10) by ourselves.
	void SetAlignmentShown(LPCHARACTER ch, int shown)
	{
		shown = std::max(-ALIGN_CAP, std::min(shown, ALIGN_CAP));
		int target = shown * ALIGN_UNIT;
		if (shown >= 0 && shown < ALIGN_CAP && ch->GetRealAlignment() >= 0)
			target += ch->GetRealAlignment() % ALIGN_UNIT;	// the engine's tenths kept
		const int delta = target - ch->GetRealAlignment();
		if (!delta)
			return;
		s_bOwnAlignment = true;
		ch->UpdateAlignment(delta);
		s_bOwnAlignment = false;
	}

	// New alignment (shown) and extra for ch: saved, the bonus and the title put
	// right. Returns the new tier.
	int SetState(LPCHARACTER ch, int alignmentShown, int extra, bool tell)
	{
		extra = std::max(0, std::min(extra, EXTRA_MAX));
		const int before = TierOf(Points(ch));	// the extra read first when it is not yet
		SEntry& e = s_points[ch->GetPlayerID()];
		if (e.extra != extra || e.who != ch)
		{
			e.extra = extra;
			e.who = ch;
			Save(ch, extra);
		}
		SetAlignmentShown(ch, alignmentShown);
		return Refresh(ch, before, tell);
	}

	// /ranga ustaw: the total - under 20 000 the alignment (the extra to 0), from
	// 20 000 the alignment at its cap and the extra the rest.
	int SetPoints(LPCHARACTER ch, int points, bool tell)
	{
		points = std::max(-ALIGN_CAP, std::min(points, POINTS_MAX));
		if (points < ALIGN_CAP)
			return SetState(ch, points, 0, tell);
		return SetState(ch, ALIGN_CAP, points - ALIGN_CAP, tell);
	}

	// One fruit eaten: false when it does not fit the total (nothing changes).
	// Jablko (its range under 20 000) raises the alignment itself, the others the extra.
	bool Eat(LPCHARACTER ch, const SFruit& fruit, bool tell)
	{
		const int points = Points(ch);
		if (points < fruit.from || points >= fruit.to)
			return false;
		if (fruit.to <= ALIGN_CAP)
			SetState(ch, std::min(AlignmentShown(ch) + fruit.gain, ALIGN_CAP), KnownExtra(ch), tell);
		else
			SetState(ch, AlignmentShown(ch), KnownExtra(ch) + fruit.gain, tell);
		const int now = KnownPoints(ch);
		if (tell)
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_GAIN, now - points, now);
		sys_log(0, "[RANGA_USE] pid=%u name=%s vnum=%u points=%d->%d alignment=%d extra=%d bot=%d",
				ch->GetPlayerID(), ch->GetName(), fruit.vnum, points, now, AlignmentShown(ch), KnownExtra(ch),
				IsBot(ch) ? 1 : 0);
		return true;
	}

	// ---------------------------------------------------------------- the waiting affects

	EVENTINFO(rank_points_tick_info)
	{
		int dummy;
	};

	EVENTFUNC(rank_points_tick)
	{
		const std::map<DWORD, int> pids(s_needSync);
		const int now = (int)get_global_time();
		for (std::map<DWORD, int>::const_iterator it = pids.begin(); it != pids.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || now - it->second > 600)	// gone, or ten minutes without its affects
				s_needSync.erase(it->first);
			else if (ch->IsLoadedAffect())
				SyncBonuses(ch);
		}
		if (s_needSync.empty())
		{
			s_pkTick = NULL;
			return 0;
		}
		return PASSES_PER_SEC(SYNC_TICK_SEC);
	}

	void EnsureTick()
	{
		if (s_pkTick)
			return;
		rank_points_tick_info* info = AllocEventInfo<rank_points_tick_info>();
		s_pkTick = event_create(rank_points_tick, info, PASSES_PER_SEC(SYNC_TICK_SEC));
	}

	// ---------------------------------------------------------------- the drop

	void Drop(LPCHARACTER killer, LPCHARACTER victim)
	{
		const SFruit* fruit = FruitForLevel(victim->GetLevel());
		const int roll = number(1, 100);
		const bool win = roll <= DROP_PERCENT;
		const int count = number(1, 2);
		sys_log(0, "[RANGA_DROP] mob_vnum=%u mob_lv=%d killer=%s killer_pid=%u roll=%d win=%d vnum=%u count=%d",
				victim->GetRaceNum(), victim->GetLevel(), killer->GetName(), killer->GetPlayerID(), roll, win ? 1 : 0,
				fruit->vnum, count);
		if (!win)
			return;
		LPITEM item = ITEM_MANAGER::instance().CreateItem(fruit->vnum, count);
		if (!item)
			return;
		if (IsBot(killer))
		{
			if (killer->GetEmptyInventory(item->GetSize()) >= 0)
				killer->AutoGiveItem(item);
			else
				M2_DESTROY_ITEM(item);
			return;
		}
		PIXEL_POSITION pos;
		pos.x = victim->GetX() + number(-100, 100);
		pos.y = victim->GetY() + number(-100, 100);
		item->SetOwnership(killer, 120);
		if (!item->AddToGround(victim->GetMapIndex(), pos))
		{
			M2_DESTROY_ITEM(item);
			return;
		}
		item->StartDestroyEvent();
	}

	// ---------------------------------------------------------------- /ranga

	void BonusLines(LPCHARACTER ch, int tier)
	{
		(void)tier;
		const int stage = Enabled() ? RewardStage(KnownPoints(ch)) : 0;
		ch->ChatPacket(CHAT_TYPE_INFO,
			"Bonus rangi: obrona +%ld, sila kazdego zywiolu +%ld%%, odpornosc +%ld%%, szybkosc ataku +%ld%%, ruchu +%ld%%, metiny +%ld%%",
			RewardValue(stage,0), RewardValue(stage,7), RewardValue(stage,1),
			RewardValue(stage,13), RewardValue(stage,14), RewardValue(stage,15));
	}

	void Info(LPCHARACTER ch)
	{
		const int points = Points(ch);
		const int tier = TierOf(points);
		if (tier)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_INFO, TIERS[tier].name, points);
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_INFO_NONE, points);
		BonusLines(ch, tier);
		const SFruit* fruit = FruitForPoints(points);
		if (points < 0)
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_NEGATIVE, points);
		else if (tier + 1 < TIER_COUNT && fruit)
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_NEXT, TIERS[tier + 1].name, TIERS[tier + 1].from, fruit->name, fruit->gain);
		else if (!fruit)
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_NEXT_MAX);
		const int extra = KnownExtra(ch);
		if (points < ALIGN_CAP && extra > 0)
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_KEPT, extra);
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_SCALE);
		ch->ChatPacket(CHAT_TYPE_INFO, MSG_FRUITS);
	}
}

// ---------------------------------------------------------------- the bots

namespace
{
	DWORD ScalePlayerBotIwakuraPrice(DWORD base);

	bool IsPlayerBotRankFruit(DWORD vnum)
	{
		return mt2009_rankp::FruitByVnum(vnum) != NULL;
	}

	// A piece on a counter, by the fruit's tier: 5 000 / 10 000 / 25 000 /
	// 50 000 / 100 000 yang before the sheet's scaling (the merchant pays a
	// fifth - item_proto, apply.sh).
	DWORD GetPlayerBotRankFruitPrice(DWORD vnum)
	{
		// MT2009_PLUS_RANK_FRUIT_PRICE_V2 (the owner, 7 October): Jablko 250 000, each next fruit
		// of the table 50% dearer (Gruszka 375 000, Winogrono 562 500, Arbuz 843 800, Ananas 1 265 600).
		static const DWORD prices[] = { 250000, 375000, 562500, 843800, 1265600 };
		for (int i = 0; i < mt2009_rankp::FRUIT_COUNT; ++i)
			if (mt2009_rankp::FRUITS[i].vnum == vnum)
				return std::max<DWORD>(100, ScalePlayerBotIwakuraPrice(prices[i]) / 100 * 100);
		return 0;
	}

	// MT2009_PLUS_RANK_FRUIT_MARKET_V1 (the owner, 8 October: "niech boty wiedza,
	// ze ranga daje bonusy i chetnie to wykorzystuja: czesc wbija, czesc
	// wystawia"): PLAYERBOT_RANK_FRUIT_EATER_PERCENT of the bots (by player id,
	// never a trader) eat the fruit that fits their total and buy more of it off
	// the counters (playerbot_rank_fruit_market.h); the rest put every fruit on
	// their counter, the fitting one too. A fruit out of a bot's range is goods
	// for every bot, as before.
	const int PLAYERBOT_RANK_FRUIT_EATER_PERCENT = 75;

	bool IsPlayerBotRankFruitEater(LPCHARACTER ch)
	{
		if (!ch || GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_MERCHANT)
			return false;
		return (int)(((ch->GetPlayerID() ^ 0x52414e4bU) * 2654435761U >> 16) % 100U) <
				PLAYERBOT_RANK_FRUIT_EATER_PERCENT;
	}

	// The fruit that fits the bot's points now: its own, eaten at its next look
	// - an eater's (IsPlayerBotRankFruitEater); a trader lists it.
	bool IsPlayerBotKeptRankFruit(LPCHARACTER ch, LPITEM item)
	{
		using namespace mt2009_rankp;
		if (!ch || !item || !Enabled() || !IsPlayerBotRankFruitEater(ch))
			return false;
		const SFruit* fruit = FruitByVnum(item->GetVnum());
		if (!fruit)
			return false;
		const int points = KnownPoints(ch);
		return points >= fruit->from && points < fruit->to;
	}

	std::map<DWORD, DWORD> s_mapPlayerBotRankNextLook;

	// A look every 20-40 s: the points read on this core, the bonus on, the
	// fitting fruits eaten (up to 40 a look).
	void ManagePlayerBotRankPoints(LPCHARACTER ch, DWORD dwNow)
	{
		using namespace mt2009_rankp;
		if (!ch || ch->IsDead() || !Enabled())
			return;
		DWORD& next = s_mapPlayerBotRankNextLook[ch->GetPlayerID()];
		if (next != 0 && (int)(dwNow - next) < 0)
			return;
		next = dwNow + number(20000, 40000);
		if (!Known(ch))
		{
			Load(ch);
			SyncBonuses(ch);
			if (TierOf(KnownPoints(ch)) > 0)
				SendTailAround(ch);
		}
		if (ch->GetExchange() || ch->GetMyShop() || !IsPlayerBotRankFruitEater(ch))	// MT2009_PLUS_RANK_FRUIT_MARKET_V1
			return;
		for (int eaten = 0; eaten < 40; ++eaten)
		{
			const SFruit* fruit = FruitForPoints(KnownPoints(ch));
			if (!fruit || ch->CountSpecifyItem(fruit->vnum) <= 0)
				break;
			ch->RemoveSpecifyItem(fruit->vnum, 1);
			if (!Eat(ch, *fruit, false))
				break;
		}
	}
}

// ---------------------------------------------------------------- the engine's calls (server-patches/rankpoints)

// char_item.cpp, UseItemEx: -1 = not a fruit, 0 = a fruit not eaten, 1 = eaten.
int RankPointsUseItem(LPCHARACTER ch, LPITEM item)
{
	using namespace mt2009_rankp;
	const SFruit* fruit = item ? FruitByVnum(item->GetVnum()) : NULL;
	if (!fruit || !Counts(ch))
		return -1;
	if (!Enabled())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_DISABLED);
		return 0;
	}
	const int points = Points(ch);
	if (points >= POINTS_MAX)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_MAX);
		return 0;
	}
	if (!Eat(ch, *fruit, true))
	{
		if (points < 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, MSG_NEGATIVE, points);
			return 0;
		}
		const SFruit* want = FruitForPoints(points);
		ch->ChatPacket(CHAT_TYPE_INFO, MSG_WRONG, points, want ? want->name : "-", want ? want->from : 0, want ? want->to : 0);
		return 0;
	}
	item->SetCount(item->GetCount() - 1);
	return 1;
}

// char_battle.cpp, after the Monster Cards' call: a Metin's or a boss's fruit.
void RankPointsOnKill(LPCHARACTER killer, LPCHARACTER victim)
{
	using namespace mt2009_rankp;
	if (!Enabled() || !Counts(killer) || !victim || victim->IsPC())
		return;
	if (!victim->IsStone() && victim->GetMobRank() < MOB_RANK_BOSS)
		return;
	Drop(killer, victim);
}

// input_login.cpp, entering the game: the points read again, the bonus and the title.
void RankPointsOnLogin(LPCHARACTER ch)
{
	using namespace mt2009_rankp;
	if (!Counts(ch))
		return;
	Load(ch);
	SyncBonuses(ch);
	SendSelf(ch);
	if (Enabled() && TierOf(KnownPoints(ch)) > 0)
		SendTailAround(ch);
}

// char_battle.cpp, CHARACTER::UpdateAlignment (MT2009_PLUS_RANK_POINTS_V2): the
// alignment moved from `realBefore` (engine units). Under 20 000 the total can
// not reach a tier, so only its crossing of the cap (either way) changes the
// rank: then the bonus, the title and the player's own line. Under the cap the
// client shows its live alignment itself.
void RankPointsOnAlignment(LPCHARACTER ch, int realBefore)
{
	using namespace mt2009_rankp;
	if (s_bOwnAlignment || !Enabled() || !Counts(ch) || !Known(ch))
		return;
	const int shownBefore = realBefore / ALIGN_UNIT;
	const int shownNow = AlignmentShown(ch);
	if (RewardStage(TotalOf(shownBefore, KnownExtra(ch))) == RewardStage(KnownPoints(ch)))
		return;
	Refresh(ch, TierOf(TotalOf(shownBefore, KnownExtra(ch))), true);
}

// char.cpp, EncodeInsertPacket: a character with a rank coming into a player's view.
void RankPointsOnInsert(LPCHARACTER shown, LPCHARACTER viewer)
{
	using namespace mt2009_rankp;
	if (!Enabled() || !shown || !viewer || !shown->IsPC() || !viewer->GetDesc())
		return;
	const int tier = TierOf(KnownPoints(shown));
	viewer->ChatPacket(CHAT_TYPE_COMMAND, "RANGA tail %u %d", (unsigned int)shown->GetVID(), tier);
}

// item_manager.cpp, the drop wiki: the fruit of a monster's level (0: none).
DWORD RankPointsWikiFruit(bool metinOrBoss, int level)
{
	using namespace mt2009_rankp;
	if (!Enabled() || !metinOrBoss)
		return 0;
	return FruitForLevel(level)->vnum;
}

int RankPointsWikiPercent()
{
	return mt2009_rankp::DROP_PERCENT;
}

// "/ranga": the player's points; a GM's "/ranga ustaw <nick> <points>".
ACMD(do_rank_points)
{
	using namespace mt2009_rankp;
	if (!Counts(ch))
		return;
	if (!Enabled())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_DISABLED);
		return;
	}
	char a1[256], a2[256], a3[256];
	const char* rest = one_argument(argument, a1, sizeof(a1));
	if (*a1 && !strcmp(a1, "ustaw") && ch->GetGMLevel() >= GM_HIGH_WIZARD)
	{
		rest = one_argument(rest, a2, sizeof(a2));
		one_argument(rest, a3, sizeof(a3));
		if (!*a2 || !*a3 || !isdigit((unsigned char)a3[0]))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_SET_USAGE);
			return;
		}
		LPCHARACTER target = CHARACTER_MANAGER::instance().FindPC(a2);
		if (!target || !Counts(target))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_SET_NOBODY);
			return;
		}
		const int tier = SetPoints(target, atoi(a3), true);
		ch->ChatPacket(CHAT_TYPE_INFO, MSG_SET_DONE, target->GetName(), KnownPoints(target));
		sys_log(0, "[RANGA_SET] gm=%s target=%s points=%d alignment=%d extra=%d tier=%d", ch->GetName(), target->GetName(),
				KnownPoints(target), AlignmentShown(target), KnownExtra(target), tier);
		return;
	}
	Info(ch);
}

#endif
