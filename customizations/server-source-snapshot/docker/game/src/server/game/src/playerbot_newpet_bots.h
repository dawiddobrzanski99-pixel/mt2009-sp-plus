#ifndef __INC_METIN2_PLAYERBOT_NEWPET_BOTS_H__
#define __INC_METIN2_PLAYERBOT_NEWPET_BOTS_H__

// MT2009_PLUS_NEWPET_BOTS_V1 - the bots and the New Pet System (the owner,
// 8 October: "obniz cene jajka peta domowego do 2kk i zacznij uczyc boty, zeby
// ich uzywaly: rozwijaly, expily, ewoluowaly itd.").
//
// The pet lives in player.newpet_pet (playerbot_newpet.h) and its window is
// fed over chat commands a bot never sends, so a bot does what the window's
// commands do by calling the very functions they call - Hatch, UseProtein,
// UseTreat, UseDew, UseBook, UseBookChest, Evolve, Summon - for its own rows,
// as playerbot_alchemy.h stands in for the Alchemist's window. Every write is
// theirs: a compare-and-set on the bot's own row (WHERE id AND pid AND the old
// value), the item taken only when the row changed. A bot never touches a row
// of another pid, and the kill experience reaches only an Owner this file made
// (NewPetOnExp, FindOwner), so a person's pet is never a bot's business.
//
// Who: PLAYERBOT_NEWPET_SHARE_PERCENT of the bots (by player id, so a bot is
// one or the other for good) from PLAYERBOT_NEWPET_MIN_LEVEL - the level from
// which the purses carry the hatching's 100 000 and an egg's 2 000 000 - and a
// player's companion (playerbot_sidekick.h) whatever its id, with a rule of its
// own below. The rest list every pet item they hold.
//
// What a keeper does, at a look every PLAYERBOT_NEWPET_LOOK_MIN_MS to _MAX_MS
// (no query unless it acts - the pets are read once when the bot comes to the
// core, GetOwner, and again by each change):
//   - with no pet, it hatches the egg in its bag (the Flower Event's boxes put
//     some 24 000 of them in the bots' bags before this: test world, 8 October)
//     and names it after its species (MakePlayerBotPetName); with no egg it
//     buys one off a counter at no more than PLAYERBOT_NEWPET_EGG_PRICE;
//   - the pet is out whenever it has life energy, and takes the experience of
//     every kill (playerbot_newpet.h, BOT_FLUSH_MS);
//   - under PLAYERBOT_NEWPET_FEED_BELOW_DAYS of life it eats a Proteinowa
//     Przekaska, and the bot keeps PLAYERBOT_NEWPET_PROTEIN_KEEP of them,
//     bought off the counters when short;
//   - a Smakolyk / Smakolyk+ it holds is eaten while the pet can still grow;
//   - an elixir of the size a bonus is at is drunk once the pet's level allows
//     the size; it buys the next one or two of the bonus it is raising;
//   - books: three skills chosen for a hunter (GetPlayerBotNewPetSkills) and a
//     fourth for the slot of a heroic pet; a book of a known skill raises it, a
//     wanted skill's book fills a free slot, the book chest is opened;
//   - at the evolution's level cap it evolves with the materials and the yang
//     (mt2009_newpet::EVOLUTION_COSTS), buying the materials it lacks off the
//     counters - only when every one of them is in its bag or on a counter
//     (the Heroiczny step's 31005/31006 drop nowhere in this world, so no bot
//     buys Cors for it) and the yang of the step stays in the purse.
// What it does not use - a second egg, a book of a skill it did not choose,
// the transporter, the reverti, the scrolls - goes on its counter, one unit a
// line (GetPlayerBotNewPetKeep, the economy's line rules). Nobody packs a pet:
// a transporter with a pet (55007) is a person's trade.
//
// MT2009_PLUS_NEWPET_EGG_RANK_V1 (the owner, 8 October: "Malpki i Pajaczki
// to najslabsze pety - jesli boty maja wybor, biora innego peta, a te
// sprzedaja u handlarza"): the species are ranked (PLAYERBOT_NEWPET_EGG_RANK).
// Every species gives the same bonuses here (the pet's bonuses and skills are
// its own, not its species'), so the order is the owner's word and rarity: the
// minis of the great bosses first - Piskle Exedyara, Mini Razador, Mini
// Nemere - then Czerwony Smoczek, Maly Baashido, Nessie, Smoczek, and last the
// two the owner named, Pajaczek and Malpka (the weak eggs). A keeper hatches
// its best egg; a weak one only when no other is in its bag and none can be
// had (no counter holds one, or its purse would not pay 2 000 000) or it has
// waited PLAYERBOT_NEWPET_WEAK_WAIT_MS for one. A keeper whose pet is a weak
// species hatches a better egg as its next pet (MAX_PETS allowing) and makes it
// the active one (Select). A weak egg is never a counter's and never bought:
// what nobody keeps goes to the merchant (IsPlayerBotNewPetJunkEgg). The other
// eggs stand at the fixed 2 000 000, three lines a counter, and no bot puts up
// one more while the world's counters hold PLAYERBOT_NEWPET_EGG_WORLD_LINES.
//
// The companion: it hatches an egg its player handed it, feeds, raises and
// evolves its pet from its own bag and purse and summons it at its player's
// side, but it buys nothing for it and lists nothing of it - its bag is its
// player's business (playerbot_sidekick.h).
//
// The multi-core rule: a bot moves between cores; the row is the truth. The
// Owner of mt2009_newpet goes when the bot leaves a core (its tick flushes the
// experience) and the next core reads the row again at the bot's first look.
// The view below is only this core's memory of the last look, for the market's
// questions (which must not query); every act goes through the row.
//
// Logs: PLAYERBOT_NEWPET: hatched / fed / treat / elixir / skill / chest /
// evolved / summoned (and levelup from playerbot_newpet.h), and every
// PLAYERBOT_NEWPET_CENSUS_MS a census of this core's keepers and of every bot's
// row in the database.
//
// An implementation fragment in the sense playerbot_types.h describes: included
// once, from playerbot_manager.cpp, after playerbot_newpet.h and before
// playerbot_energy_shards.h (the egg's fixed price) and playerbot_economy.h.

namespace
{
	DWORD GetPlayerBotShopAskingPrice(LPITEM item);
	bool PlayerBotHasGrandMasterToTrain(LPCHARACTER ch);

	const int PLAYERBOT_NEWPET_SHARE_PERCENT = 50;
	const int PLAYERBOT_NEWPET_MIN_LEVEL = 30;
	// The owner, 8 October: "obniz cene jajka peta domowego do 2kk" - every
	// species; since MT2009_PLUS_SHEET_PRICES_ONLY_V1 ("na rynku nie ma stalych
	// cen") the price sheet's base (playerbot_price_tables.h), through the
	// yang-rate curve and the inflation like every sheet price: a buyer's cap
	// is the scaled one (GetPlayerBotNewPetEggPrice).
	const DWORD PLAYERBOT_NEWPET_EGG_PRICE = 2000000;
	DWORD ScalePlayerBotIwakuraPrice(DWORD base);
	DWORD GetPlayerBotNewPetEggPrice()
	{
		return ScalePlayerBotIwakuraPrice(PLAYERBOT_NEWPET_EGG_PRICE);
	}
	const DWORD PLAYERBOT_NEWPET_LOOK_MIN_MS = 90 * 1000;
	const DWORD PLAYERBOT_NEWPET_LOOK_MAX_MS = 180 * 1000;
	const DWORD PLAYERBOT_NEWPET_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_NEWPET_FEED_BELOW_DAYS = 14;
	// Proteins bought while the pet has less than this many days of life.
	const int PLAYERBOT_NEWPET_PROTEIN_BUY_BELOW_DAYS = 42;
	const int PLAYERBOT_NEWPET_PROTEIN_KEEP = 4;
	// Elixirs of the size the bonus is at, bought ahead.
	const int PLAYERBOT_NEWPET_DEW_BUY_AHEAD = 2;
	// Books of a chosen skill not learnt yet (no free slot), kept for it.
	const int PLAYERBOT_NEWPET_BOOK_WAIT_KEEP = 3;
	// The purse: the egg out of this share of what the bot can spare, the
	// rest of the pet's goods out of the smaller one; no line over the price
	// list's fair price by more than PLAYERBOT_NEWPET_FAIR_PERCENT.
	const int PLAYERBOT_NEWPET_EGG_PURSE_PERCENT = 60;
	const int PLAYERBOT_NEWPET_GOODS_PURSE_PERCENT = 25;
	const int PLAYERBOT_NEWPET_FAIR_PERCENT = 130;
	// Acts a look: a few, so one look never runs a burst of queries.
	const int PLAYERBOT_NEWPET_ACTS_PER_LOOK = 6;

	// MT2009_PLUS_NEWPET_EGG_RANK_V1: the species, best first; the weak two last.
	const DWORD PLAYERBOT_NEWPET_EGG_RANK[] = { 55411, 55403, 55404, 55406, 55409, 55410, 55405, 55402, 55401 };
	const DWORD PLAYERBOT_NEWPET_WEAK_WAIT_MS = 2 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_NEWPET_EGG_WORLD_LINES = 100;

	const DWORD PLAYERBOT_NEWPET_BOOK_LAST = mt2009_newpet::ITEM_BOOK_FIRST + mt2009_newpet::SKILL_COUNT - 1;

	bool IsPlayerBotNewPetEggVnum(DWORD vnum)
	{
		return mt2009_newpet::FindSpecies(vnum) != NULL;
	}

	// 0 the best species, 98 an egg out of the table, 99 not an egg.
	int GetPlayerBotNewPetEggRank(DWORD vnum)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_NEWPET_EGG_RANK) / sizeof(PLAYERBOT_NEWPET_EGG_RANK[0]); ++i)
			if (PLAYERBOT_NEWPET_EGG_RANK[i] == vnum)
				return (int)i;
		return IsPlayerBotNewPetEggVnum(vnum) ? 98 : 99;
	}

	// Malpka (55401) and Pajaczek (55402): the owner's weakest.
	bool IsPlayerBotNewPetWeakEgg(DWORD vnum)
	{
		return vnum == 55401 || vnum == 55402;
	}

	bool IsPlayerBotNewPetGoodEgg(DWORD vnum)
	{
		return IsPlayerBotNewPetEggVnum(vnum) && !IsPlayerBotNewPetWeakEgg(vnum);
	}

	bool IsPlayerBotNewPetBookVnum(DWORD vnum)
	{
		return vnum >= mt2009_newpet::ITEM_BOOK_FIRST && vnum <= PLAYERBOT_NEWPET_BOOK_LAST;
	}

	// The elixir's bonus (0-2) and size (0-3), or false.
	bool GetPlayerBotNewPetDew(DWORD vnum, int& bonus, int& step)
	{
		for (int b = 0; b < mt2009_newpet::BONUS_COUNT; ++b)
			if (vnum >= mt2009_newpet::DEW_FIRST[b] && vnum < mt2009_newpet::DEW_FIRST[b] + 4)
			{
				bonus = b;
				step = (int)(vnum - mt2009_newpet::DEW_FIRST[b]);
				return true;
			}
		return false;
	}

	// The pet goods a counter takes: the eggs, the food, the books and their
	// chest, the elixirs, the scrolls and the empty transporter. Not the
	// transporter with a pet (55007): a person's trade.
	bool IsPlayerBotNewPetGoodsVnum(DWORD vnum)
	{
		using namespace mt2009_newpet;
		int b = 0, s = 0;
		return IsPlayerBotNewPetEggVnum(vnum) || IsPlayerBotNewPetBookVnum(vnum) || GetPlayerBotNewPetDew(vnum, b, s) ||
				vnum == ITEM_PROTEIN || vnum == ITEM_TRANSPORT_EMPTY || vnum == ITEM_RENAME || vnum == ITEM_BOOK_CHEST ||
				vnum == ITEM_TREAT || vnum == ITEM_TREAT_PLUS || vnum == ITEM_REVERTI || vnum == ITEM_REVERTUS ||
				vnum == ITEM_OPEN_SLOT;
	}

	bool IsPlayerBotNewPetBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() &&
				CPlayerBotManager::instance().IsManaged(ch->GetPlayerID());
	}

	bool IsPlayerBotNewPetCompanion(LPCHARACTER ch)
	{
		return ch && IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	// A bot that keeps a pet: its share by id from the level, or a companion.
	bool IsPlayerBotNewPetKeeper(LPCHARACTER ch)
	{
		if (!IsPlayerBotNewPetBot(ch))
			return false;
		if (IsPlayerBotNewPetCompanion(ch))
			return true;
		if (ch->GetLevel() < PLAYERBOT_NEWPET_MIN_LEVEL)
			return false;
		return (int)(((ch->GetPlayerID() ^ 0x50455453U) * 2654435761U >> 16) % 100U) < PLAYERBOT_NEWPET_SHARE_PERCENT;
	}

	// This core's memory of a keeper's last look.
	struct TPlayerBotNewPetView
	{
		DWORD nextLook;
		bool known;
		int pets;
		bool hasPet;
		DWORD petId;
		DWORD egg;
		int level;
		int evolution;
		bool atCap;
		DWORD lifeUntil;
		int bonus[mt2009_newpet::BONUS_COUNT];
		BYTE skillType[mt2009_newpet::SKILL_SLOTS];
		BYTE skillLevel[mt2009_newpet::SKILL_SLOTS];
		DWORD lastSeen;
		bool out;
		bool weakPet;		// the active pet is a weak species
		DWORD weakWaitSince;	// since when it holds only a weak egg and no pet
		TPlayerBotNewPetView() : weakPet(false), weakWaitSince(0), nextLook(0), known(false), pets(0), hasPet(false), petId(0), egg(0), level(0), evolution(0),
				atCap(false), lifeUntil(0), lastSeen(0), out(false)
		{
			for (int i = 0; i < mt2009_newpet::BONUS_COUNT; ++i)
				bonus[i] = 0;
			for (int i = 0; i < mt2009_newpet::SKILL_SLOTS; ++i)
			{
				skillType[i] = mt2009_newpet::SKILL_LOCKED;
				skillLevel[i] = 0;
			}
		}
	};

	std::map<DWORD, TPlayerBotNewPetView> s_mapPlayerBotNewPet;

	struct TPlayerBotNewPetStats
	{
		DWORD hatched, hatchFails, fed, treats, elixirs, skills, chests, evolved, evolveFails, summoned;
		TPlayerBotNewPetStats() : hatched(0), hatchFails(0), fed(0), treats(0), elixirs(0), skills(0), chests(0), evolved(0),
				evolveFails(0), summoned(0) {}
	};
	TPlayerBotNewPetStats s_kPlayerBotNewPetStats;
	DWORD s_dwPlayerBotNewPetCensusAt = 0;

	const TPlayerBotNewPetView* GetPlayerBotNewPetView(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		std::map<DWORD, TPlayerBotNewPetView>::const_iterator it = s_mapPlayerBotNewPet.find(ch->GetPlayerID());
		return it == s_mapPlayerBotNewPet.end() || !it->second.known ? NULL : &it->second;
	}

	void NotePlayerBotNewPetView(LPCHARACTER ch, mt2009_newpet::Owner& owner, DWORD dwNow)
	{
		using namespace mt2009_newpet;
		TPlayerBotNewPetView& v = s_mapPlayerBotNewPet[ch->GetPlayerID()];
		v.known = true;
		v.lastSeen = dwNow;
		v.pets = (int)owner.pets.size();
		const Pet* pet = ActivePet(owner);
		v.hasPet = pet != NULL;
		v.out = IsOut(owner);
		if (!pet)
		{
			v.petId = v.egg = 0;
			v.weakPet = false;
			v.level = v.evolution = 0;
			v.atCap = false;
			v.lifeUntil = 0;
			return;
		}
		v.petId = pet->id;
		v.egg = pet->egg;
		v.weakPet = IsPlayerBotNewPetWeakEgg(pet->egg);
		v.level = pet->level;
		v.evolution = pet->evolution;
		v.atCap = pet->level >= Cap(pet->evolution);
		v.lifeUntil = pet->lifeUntil;
		for (int b = 0; b < BONUS_COUNT; ++b)
			v.bonus[b] = pet->bonus[b];
		for (int i = 0; i < SKILL_SLOTS; ++i)
		{
			v.skillType[i] = pet->skillType[i];
			v.skillLevel[i] = pet->skillLevel[i];
		}
	}

	// The skills a bot raises, in the order it fills the slots: the monsters'
	// bonus first (it hunts), then the Metins' or the bosses' by its id, then
	// its class's damage - a magic class's skills, a fighter's normal hits -
	// and for the heroic pet's slot the experience, drop and yang one.
	int GetPlayerBotNewPetSkills(LPCHARACTER ch, int out[4])
	{
		const DWORD seed = (ch->GetPlayerID() * 2654435761U) >> 12;
		out[0] = 6;							// Sztuka Lowcy Potworow
		out[1] = (seed % 3) == 0 ? 2 : 1;	// Lowcy Bossow / Lowcy Metinow
		const int job = (int)ch->GetJob();
		out[2] = (job == JOB_SURA || job == JOB_SHAMAN) ? 10 : 11;	// Lowcy Magii (skills) / Lowcy Broni (normal hits)
		out[3] = 20;						// experience, drop, yang
		return 4;
	}

	bool IsPlayerBotNewPetWantedSkill(LPCHARACTER ch, int skill)
	{
		int wanted[4];
		const int n = GetPlayerBotNewPetSkills(ch, wanted);
		for (int i = 0; i < n; ++i)
			if (wanted[i] == skill)
				return true;
		return false;
	}

	// The slot of a skill, or -1; a free (open, empty) slot's count.
	int FindPlayerBotNewPetSkillSlot(const TPlayerBotNewPetView& v, int skill)
	{
		for (int i = 0; i < mt2009_newpet::SKILL_SLOTS; ++i)
			if (v.skillType[i] == skill)
				return i;
		return -1;
	}

	int CountPlayerBotNewPetFreeSlots(const TPlayerBotNewPetView& v)
	{
		int n = 0;
		for (int i = 0; i < mt2009_newpet::SKILL_SLOTS; ++i)
			if (v.skillType[i] == 0)
				++n;
		return n;
	}

	// The eggs in the bag of the good species (not Malpka, not Pajaczek).
	int CountPlayerBotNewPetGoodEggs(LPCHARACTER ch)
	{
		int n = 0;
		for (size_t i = 0; i < mt2009_newpet::SPECIES_COUNT; ++i)
			if (IsPlayerBotNewPetGoodEgg(mt2009_newpet::SPECIES[i].egg))
				n += (int)ch->CountSpecifyItem(mt2009_newpet::SPECIES[i].egg);
		return n;
	}

	int CountPlayerBotNewPetWeakEggs(LPCHARACTER ch)
	{
		return (int)ch->CountSpecifyItem(55401) + (int)ch->CountSpecifyItem(55402);
	}

	// The good eggs' units on the world's counters (the ledger; one a line).
	DWORD CountPlayerBotNewPetGoodEggSupply()
	{
		DWORD units = 0;
		for (size_t i = 0; i < mt2009_newpet::SPECIES_COUNT; ++i)
			if (IsPlayerBotNewPetGoodEgg(mt2009_newpet::SPECIES[i].egg))
				if (const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(mt2009_newpet::SPECIES[i].egg))
					units += e->dwSupplyUnits;
		return units;
	}

	long long GetPlayerBotNewPetSpare(LPCHARACTER ch);

	// A good egg could be had: some counter holds one and the purse pays it.
	bool CanPlayerBotGetGoodNewPetEgg(LPCHARACTER ch)
	{
		return GetPlayerBotNewPetSpare(ch) * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100 >= (long long)GetPlayerBotNewPetEggPrice() &&
				CountPlayerBotNewPetGoodEggSupply() > 0;
	}

	// The bot looks for a good egg: no pet, or a weak one with room for another.
	bool PlayerBotSeeksGoodNewPetEgg(const TPlayerBotNewPetView& v)
	{
		return (!v.hasPet && v.pets == 0) || (v.hasPet && v.weakPet && v.pets < (int)mt2009_newpet::MAX_PETS);
	}

	// The materials of the pet's next evolution, with the Kamien Duchowy the
	// bot's own Grand Master training keeps on top (playerbot_economy.h).
	int GetPlayerBotNewPetMaterialNeed(LPCHARACTER ch, DWORD vnum, DWORD count)
	{
		int need = (int)count;
		if (vnum == PLAYERBOT_GRAND_MASTER_STONE_VNUM && PlayerBotHasGrandMasterToTrain(ch))
			need += PLAYERBOT_GRAND_MASTER_STONE_KEEP;
		return need;
	}

	long long GetPlayerBotNewPetSpare(LPCHARACTER ch)
	{
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return std::max<long long>(0, spare);
	}

	// The next evolution's step, while the pet waits at its cap for one; NULL
	// otherwise.
	const mt2009_newpet::EvolutionCost* GetPlayerBotNewPetEvolution(const TPlayerBotNewPetView& v)
	{
		if (!v.hasPet || !v.atCap || v.evolution >= mt2009_newpet::EVOLUTION_MAX)
			return NULL;
		return &mt2009_newpet::EVOLUTION_COSTS[v.evolution];
	}

	// Whether every material of the step is in the bag or on some counter (the
	// ledger), so buying a part of it is not money thrown at a step that cannot
	// be finished.
	bool IsPlayerBotNewPetEvolutionReachable(LPCHARACTER ch, const mt2009_newpet::EvolutionCost& cost)
	{
		for (int i = 0; i < mt2009_newpet::EVOLUTION_ITEMS; ++i)
		{
			if (!cost.vnum[i] || !cost.count[i])
				continue;
			const int missing = GetPlayerBotNewPetMaterialNeed(ch, cost.vnum[i], cost.count[i]) -
					(int)ch->CountSpecifyItem(cost.vnum[i]);
			if (missing <= 0)
				continue;
			const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(cost.vnum[i]);
			if (!entry || (int)entry->dwSupplyUnits < missing)
				return false;
		}
		return true;
	}

	// How many units of the vnum a keeper would buy now (never a companion's).
	int GetPlayerBotNewPetWant(LPCHARACTER ch, DWORD vnum)
	{
		using namespace mt2009_newpet;
		if (!IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !ch->IsItemLoaded())
			return 0;
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		if (!v)
			return 0;
		// MT2009_PLUS_NEWPET_EGG_RANK_V1: never a weak egg; a good one while it
		// has no pet, or a weak pet and room for a better one.
		if (IsPlayerBotNewPetEggVnum(vnum))
			return IsPlayerBotNewPetGoodEgg(vnum) && PlayerBotSeeksGoodNewPetEgg(*v) && CountPlayerBotNewPetGoodEggs(ch) == 0 ? 1 : 0;
		if (!v->hasPet)
			return 0;
		const DWORD unixNow = (DWORD)time(NULL);
		if (vnum == ITEM_PROTEIN)
			return v->lifeUntil < unixNow + PLAYERBOT_NEWPET_PROTEIN_BUY_BELOW_DAYS * DAY
					? std::max(0, PLAYERBOT_NEWPET_PROTEIN_KEEP - (int)ch->CountSpecifyItem(vnum)) : 0;
		int bonus = 0, step = 0;
		if (GetPlayerBotNewPetDew(vnum, bonus, step))
		{
			const int have = v->bonus[bonus];
			if (have >= BONUS_LEVEL_MAX || have / 5 != step || v->level < DEW_PET_LEVEL[step])
				return 0;
			const int left = (step + 1) * 5 - have;
			return std::max(0, std::min(left, PLAYERBOT_NEWPET_DEW_BUY_AHEAD) - (int)ch->CountSpecifyItem(vnum));
		}
		if (IsPlayerBotNewPetBookVnum(vnum))
		{
			const int skill = (int)(vnum - ITEM_BOOK_FIRST + 1);
			const int slot = FindPlayerBotNewPetSkillSlot(*v, skill);
			const bool raise = slot >= 0 && v->skillLevel[slot] < SKILL_LEVEL_MAX;
			const bool learn = slot < 0 && IsPlayerBotNewPetWantedSkill(ch, skill) && CountPlayerBotNewPetFreeSlots(*v) > 0;
			return (raise || learn) && ch->CountSpecifyItem(vnum) == 0 ? 1 : 0;
		}
		const EvolutionCost* cost = GetPlayerBotNewPetEvolution(*v);
		if (!cost)
			return 0;
		for (int i = 0; i < EVOLUTION_ITEMS; ++i)
			if (cost->vnum[i] == vnum && cost->count[i])
			{
				if (GetPlayerBotNewPetSpare(ch) < cost->gold || !IsPlayerBotNewPetEvolutionReachable(ch, *cost))
					return 0;
				return std::max(0, GetPlayerBotNewPetMaterialNeed(ch, vnum, cost->count[i]) - (int)ch->CountSpecifyItem(vnum));
			}
		return 0;
	}

	bool IsPlayerBotNewPetEvolutionMaterial(LPCHARACTER ch, DWORD vnum)
	{
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		const mt2009_newpet::EvolutionCost* cost = v ? GetPlayerBotNewPetEvolution(*v) : NULL;
		if (!cost)
			return false;
		for (int i = 0; i < mt2009_newpet::EVOLUTION_ITEMS; ++i)
			if (cost->vnum[i] == vnum && cost->count[i])
				return true;
		return false;
	}

	// A counter's line the bot takes for its pet: what it wants, no more.
	bool WantsPlayerBotNewPetOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer)
			return false;
		const int want = GetPlayerBotNewPetWant(ch, offer->GetVnum());
		return want > 0 && (int)offer->GetCount() <= want;
	}

	// The price: an egg at no more than the owner's 2 000 000 a piece, out of
	// PLAYERBOT_NEWPET_EGG_PURSE_PERCENT of the spare; the rest near the price
	// list, out of the goods' share - and an evolution's material only while
	// the step's yang stays in the purse.
	bool CanPlayerBotPayForNewPetOffer(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0 || !WantsPlayerBotNewPetOffer(ch, item))
			return false;
		const long long count = std::max<long long>(1, (long long)item->GetCount());
		const long long spare = GetPlayerBotNewPetSpare(ch);
		if (IsPlayerBotNewPetEggVnum(item->GetVnum()))
			return price / count <= (long long)GetPlayerBotNewPetEggPrice() &&
					price <= spare * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100;
		const long long fair = (long long)GetPlayerBotShopAskingPrice(item);
		if (fair <= 0 || price * 100 > fair * PLAYERBOT_NEWPET_FAIR_PERCENT)
			return false;
		if (IsPlayerBotNewPetEvolutionMaterial(ch, item->GetVnum()))
		{
			const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
			const mt2009_newpet::EvolutionCost* cost = v ? GetPlayerBotNewPetEvolution(*v) : NULL;
			return cost && spare - price >= cost->gold;
		}
		return price <= spare * PLAYERBOT_NEWPET_GOODS_PURSE_PERCENT / 100;
	}

	// For the stands' scan (FindPlayerBotGambleMaterialPick) and the walk to
	// the market: what the pet lacks, and the most one line may cost.
	long long CollectPlayerBotNewPetMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		using namespace mt2009_newpet;
		if (!ch || !IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !GetPlayerBotNewPetView(ch))
			return 0;
		const long long spare = GetPlayerBotNewPetSpare(ch);
		if (spare <= 0)
			return 0;
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		if (GetPlayerBotNewPetWant(ch, PLAYERBOT_NEWPET_EGG_RANK[0]) > 0)
		{
			for (size_t i = 0; i < SPECIES_COUNT; ++i)
				if (IsPlayerBotNewPetGoodEgg(SPECIES[i].egg))
					missing[SPECIES[i].egg] = 1;
			if (!v->hasPet)
				return std::min<long long>(spare * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100, (long long)GetPlayerBotNewPetEggPrice());
		}
		if (!v->hasPet)
			return 0;
		std::vector<DWORD> candidates;
		candidates.push_back(ITEM_PROTEIN);
		for (int b = 0; b < BONUS_COUNT; ++b)
			if (v->bonus[b] < BONUS_LEVEL_MAX)
				candidates.push_back(DEW_FIRST[b] + std::min(3, v->bonus[b] / 5));
		for (DWORD book = ITEM_BOOK_FIRST; book <= PLAYERBOT_NEWPET_BOOK_LAST; ++book)
			candidates.push_back(book);
		long long cap = spare * PLAYERBOT_NEWPET_GOODS_PURSE_PERCENT / 100;
		if (!missing.empty())	// a better egg than its weak pet
			cap = std::max(cap, std::min<long long>(spare * PLAYERBOT_NEWPET_EGG_PURSE_PERCENT / 100,
					(long long)GetPlayerBotNewPetEggPrice()));
		if (const EvolutionCost* cost = GetPlayerBotNewPetEvolution(*v))
		{
			for (int i = 0; i < EVOLUTION_ITEMS; ++i)
				if (cost->vnum[i] && cost->count[i])
					candidates.push_back(cost->vnum[i]);
			cap = std::max(cap, spare - cost->gold);
		}
		for (size_t i = 0; i < candidates.size(); ++i)
		{
			const int want = GetPlayerBotNewPetWant(ch, candidates[i]);
			if (want > 0)
				missing[candidates[i]] = want;
		}
		return missing.empty() ? 0 : cap;
	}

	// Worth a walk to the market: something of it lacking that a counter has
	// (the ledger). Remembered a minute a bot: the walk's question is asked often.
	std::map<DWORD, std::pair<DWORD, bool> > s_mapPlayerBotNewPetMarketAnswer;

	bool PlayerBotWantsNewPetFromMarket(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotNewPetKeeper(ch) || IsPlayerBotNewPetCompanion(ch) || !GetPlayerBotNewPetView(ch))
			return false;
		const DWORD now = get_dword_time();
		std::pair<DWORD, bool>& answer = s_mapPlayerBotNewPetMarketAnswer[ch->GetPlayerID()];
		if (answer.first != 0 && (int)(now - answer.first) < 60000)
			return answer.second;
		std::map<DWORD, int> missing;
		bool any = false;
		if (CollectPlayerBotNewPetMissing(ch, missing) > 0)
			for (std::map<DWORD, int>::const_iterator it = missing.begin(); it != missing.end() && !any; ++it)
			{
				const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(it->first);
				any = entry && entry->dwSupplyUnits > 0;
			}
		answer = std::make_pair(now, any);
		return any;
	}

	// The units of a pet good the bot keeps off its counter: everything for a
	// keeper not looked at yet on this core, its own pet's stock otherwise -
	// and nothing at all for a bot without a pet of its own to keep.
	int GetPlayerBotNewPetKeep(LPCHARACTER ch, DWORD vnum)
	{
		using namespace mt2009_newpet;
		if (!ch || !IsPlayerBotNewPetKeeper(ch))
			return 0;
		if (IsPlayerBotNewPetCompanion(ch))
			return 1000000;	// its player's business
		const TPlayerBotNewPetView* v = GetPlayerBotNewPetView(ch);
		if (!v)
			return 1000000;
		// MT2009_PLUS_NEWPET_EGG_RANK_V1: one good egg while it seeks one; a weak
		// egg only with no pet and no good egg in the bag (it may hatch it).
		if (IsPlayerBotNewPetWeakEgg(vnum))
			return !v->hasPet && v->pets == 0 && CountPlayerBotNewPetGoodEggs(ch) == 0 ? 1 : 0;
		if (IsPlayerBotNewPetEggVnum(vnum))
			return PlayerBotSeeksGoodNewPetEgg(*v) ? 1 : 0;
		if (!v->hasPet)
			return 0;
		if (vnum == ITEM_PROTEIN)
			return PLAYERBOT_NEWPET_PROTEIN_KEEP;
		if (vnum == ITEM_BOOK_CHEST)
			return 1000000;	// opened at the next look
		if (vnum == ITEM_TREAT || vnum == ITEM_TREAT_PLUS)
			return v->level < LEVEL_CAPS[EVOLUTION_MAX] ? 1000000 : 0;
		int bonus = 0, step = 0;
		if (GetPlayerBotNewPetDew(vnum, bonus, step))
		{
			// What this size still raises: up to its five, from where the
			// bonus is (an elixir of a size the bonus has passed is goods).
			const int have = std::max(v->bonus[bonus], step * 5);
			return std::max(0, (step + 1) * 5 - have);
		}
		if (IsPlayerBotNewPetBookVnum(vnum))
		{
			const int skill = (int)(vnum - ITEM_BOOK_FIRST + 1);
			const int slot = FindPlayerBotNewPetSkillSlot(*v, skill);
			if (slot >= 0)
				return SKILL_LEVEL_MAX - (int)v->skillLevel[slot];
			return IsPlayerBotNewPetWantedSkill(ch, skill) ? PLAYERBOT_NEWPET_BOOK_WAIT_KEEP : 0;
		}
		// The evolution's materials are not pet goods; the rest - the
		// transporter, the scrolls, the slot key - go up.
		return 0;
	}

	// The units of the item's kind over the keep: > 0 makes it a line.
	int GetPlayerBotNewPetGoodsForSale(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotNewPetGoodsVnum(item->GetVnum()))
			return 0;
		// MT2009_PLUS_NEWPET_EGG_RANK_V1: a weak egg is never a counter's (the
		// merchant's, IsPlayerBotNewPetJunkEgg), and no more good eggs go up
		// while the world's counters hold PLAYERBOT_NEWPET_EGG_WORLD_LINES.
		if (IsPlayerBotNewPetWeakEgg(item->GetVnum()))
			return 0;
		if (IsPlayerBotNewPetEggVnum(item->GetVnum()) && CountPlayerBotNewPetGoodEggSupply() >= PLAYERBOT_NEWPET_EGG_WORLD_LINES)
			return 0;
		return (int)ch->CountSpecifyItem(item->GetVnum()) - GetPlayerBotNewPetKeep(ch, item->GetVnum());
	}

	// MT2009_PLUS_NEWPET_EGG_RANK_V1: a weak egg's stack the bot does not keep
	// goes to the merchant (IsPlayerBotJunkItem) - a companion's never.
	bool IsPlayerBotNewPetJunkEgg(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotNewPetWeakEgg(item->GetVnum()) || !IsPlayerBotNewPetBot(ch) ||
				IsPlayerBotNewPetCompanion(ch))
			return false;
		const int spare = (int)ch->CountSpecifyItem(item->GetVnum()) - GetPlayerBotNewPetKeep(ch, item->GetVnum());
		return spare >= (int)item->GetCount();
	}

	// ---- the look -------------------------------------------------------

	LPITEM FindPlayerBotNewPetItem(LPCHARACTER ch, DWORD vnum)
	{
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (item && item->GetVnum() == vnum && item->GetCount() > 0 && !item->isLocked() && !item->IsExchanging())
				return item;
		}
		return NULL;
	}

	// A name after its species, in letters and digits (ValidName): a few of
	// each, a common one, and now and then a number after it.
	std::string MakePlayerBotPetName(LPCHARACTER ch, DWORD egg, int attempt)
	{
		static const char* const COMMON[] = { "Puszek", "Kropka", "Tofik", "Fafik", "Lunka", "Azor", "Mruczek", "Bobo", "Kajtek", "Pimpek" };
		struct SNames { DWORD egg; const char* names[6]; };
		static const SNames BY_EGG[] = {
			{ 55401, { "Bananek", "Psotka", "Kiki", "Hopek", "Figiel", "Czika" } },
			{ 55402, { "Siecik", "Tkacz", "Nitka", "Pajonk", "Kosmatek", "Szpilka" } },
			{ 55403, { "Plomyk", "Zarek", "Iskra", "Razik", "Wulkan", "Ognik" } },
			{ 55404, { "Szronek", "Sopel", "Mrozik", "Sniezek", "Nemik", "Lodzik" } },
			{ 55405, { "Smoczus", "Drako", "Lusek", "Pazurek", "Smokus", "Dracik" } },
			{ 55406, { "Rubin", "Czerwik", "Ognisty", "Zar", "Smoczyca", "Rubik" } },
			{ 55409, { "Baszek", "Rogacz", "Kopytko", "Baashi", "Rogalik", "Bashi" } },
			{ 55410, { "Nessi", "Plusk", "Fala", "Bulbul", "Wodnik", "Glebia" } },
			{ 55411, { "Pierzak", "Cwirek", "Exi", "Skrzydlo", "Pisklak", "Puch" } },
		};
		const DWORD seed = (ch->GetPlayerID() * 2654435761U) ^ (egg * 40503U) ^ ((DWORD)attempt * 977U);
		const char* base = COMMON[(seed >> 8) % (sizeof(COMMON) / sizeof(COMMON[0]))];
		if ((seed >> 4) % 10 < 7)
			for (size_t i = 0; i < sizeof(BY_EGG) / sizeof(BY_EGG[0]); ++i)
				if (BY_EGG[i].egg == egg)
					base = BY_EGG[i].names[(seed >> 12) % 6];
		std::string name(base);
		if ((seed >> 20) % 100 < 15 || attempt > 0)
		{
			char digits[8];
			snprintf(digits, sizeof(digits), "%u", (unsigned int)((seed >> 3) % 99 + 1));
			name += digits;
		}
		if (name.size() > (size_t)mt2009_newpet::PET_NAME_LEN_MAX)
			name.resize(mt2009_newpet::PET_NAME_LEN_MAX);
		return name;
	}

	// The best egg of the bag (PLAYERBOT_NEWPET_EGG_RANK) hatched; with
	// goodOnly, a weak one never. The new pet's id, or 0.
	DWORD HatchPlayerBotPet(LPCHARACTER ch, mt2009_newpet::Owner& owner, bool goodOnly)
	{
		using namespace mt2009_newpet;
		if (owner.pets.size() >= (size_t)MAX_PETS || (long long)ch->GetGold() < HATCH_PRICE + (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR)
			return 0;
		LPITEM egg = NULL;
		const int cells = std::min<int>(ch->GetInventoryMaxCount(), INVENTORY_MAX_NUM);
		for (int i = 0; i < cells; ++i)
		{
			LPITEM item = ch->GetInventoryItem((WORD)i);
			if (IsHatchableEgg(item) && (!goodOnly || IsPlayerBotNewPetGoodEgg(item->GetVnum())) &&
					(!egg || GetPlayerBotNewPetEggRank(item->GetVnum()) < GetPlayerBotNewPetEggRank(egg->GetVnum())))
				egg = item;
		}
		if (!egg)
			return 0;
		const DWORD vnum = egg->GetVnum();
		std::string name;
		for (int attempt = 0; attempt < 3; ++attempt)
		{
			name = MakePlayerBotPetName(ch, vnum, attempt);
			if (ValidName(name.c_str()))
				break;
			name.clear();
		}
		if (name.empty())
			return 0;
		// The window's way: the egg's id and vnum remembered, its cell sent.
		owner.hatchEggId = egg->GetID();
		owner.hatchEggVnum = vnum;
		char cell[16];
		snprintf(cell, sizeof(cell), "%d", (int)egg->GetCell());
		const size_t before = owner.pets.size();
		std::set<DWORD> known;
		for (size_t i = 0; i < owner.pets.size(); ++i)
			known.insert(owner.pets[i].id);
		const long long gold = (long long)ch->GetGold();
		Hatch(ch, cell, name.c_str());
		owner.hatchEggId = owner.hatchEggVnum = 0;
		if (owner.pets.size() <= before)
		{
			++s_kPlayerBotNewPetStats.hatchFails;
			sys_log(0, "PLAYERBOT_NEWPET: hatch failed pid=%u name=%s egg=%u pet_name=%s", ch->GetPlayerID(), ch->GetName(), vnum, name.c_str());
			return 0;
		}
		DWORD fresh = 0;
		for (size_t i = 0; i < owner.pets.size() && !fresh; ++i)
			if (known.find(owner.pets[i].id) == known.end())
				fresh = owner.pets[i].id;
		++s_kPlayerBotNewPetStats.hatched;
		sys_log(0, "PLAYERBOT_NEWPET: hatched pid=%u name=%s lv=%d egg=%u species=%s pet_name=%s paid=%lld gold=%lld companion=%d",
				ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), vnum, SpeciesName(vnum), name.c_str(),
				gold - (long long)ch->GetGold(), (long long)ch->GetGold(), IsPlayerBotNewPetCompanion(ch) ? 1 : 0);
		return fresh;
	}

	// MT2009_PLUS_NEWPET_EGG_RANK_V1: no pet - the best egg, a weak one only
	// when no good egg can be had or it has waited PLAYERBOT_NEWPET_WEAK_WAIT_MS;
	// a weak pet - a good egg hatched as the next pet and made the active one.
	void ChoosePlayerBotNewPet(LPCHARACTER ch, mt2009_newpet::Owner& owner, TPlayerBotNewPetView& view, DWORD dwNow)
	{
		using namespace mt2009_newpet;
		Pet* pet = ActivePet(owner);
		if (!pet)
		{
			if (CountPlayerBotNewPetGoodEggs(ch) > 0)
			{
				view.weakWaitSince = 0;
				HatchPlayerBotPet(ch, owner, true);
				return;
			}
			if (CountPlayerBotNewPetWeakEggs(ch) == 0)
				return;
			const bool companion = IsPlayerBotNewPetCompanion(ch);
			if (!companion && CanPlayerBotGetGoodNewPetEgg(ch))
			{
				if (view.weakWaitSince == 0)
					view.weakWaitSince = dwNow;
				if ((DWORD)(dwNow - view.weakWaitSince) < PLAYERBOT_NEWPET_WEAK_WAIT_MS)
					return;	// a good egg from a counter first
			}
			view.weakWaitSince = 0;
			HatchPlayerBotPet(ch, owner, false);
			return;
		}
		if (!IsPlayerBotNewPetWeakEgg(pet->egg) || owner.pets.size() >= (size_t)MAX_PETS ||
				CountPlayerBotNewPetGoodEggs(ch) == 0)
			return;
		const DWORD weak = pet->id;
		const DWORD fresh = HatchPlayerBotPet(ch, owner, true);
		if (!fresh)
			return;
		char id[16];
		snprintf(id, sizeof(id), "%u", fresh);
		Select(ch, id);
		const Pet* now = ActivePet(owner);
		sys_log(0, "PLAYERBOT_NEWPET: upgraded pid=%u name=%s from_pet=%u to_pet=%u active=%u egg=%u pets=%u",
				ch->GetPlayerID(), ch->GetName(), weak, fresh, now ? now->id : 0, now ? now->egg : 0,
				(unsigned int)owner.pets.size());
	}

	// One act on the pet, or false: feed, treat, elixir, book, chest, evolve.
	// A refused act ends the look too: the functions read the rows again
	// (Change, Reload) whether the row changed or not, so the Pet in hand is
	// gone, and the checks before each call are the function's own - a refusal
	// is a row another core moved, for the next look.
	bool ActPlayerBotNewPet(LPCHARACTER ch, mt2009_newpet::Owner& owner)
	{
		using namespace mt2009_newpet;
		Pet* pet = ActivePet(owner);
		if (!pet)
			return false;
		const DWORD unixNow = (DWORD)time(NULL);
		const DWORD petId = pet->id;
		const std::string petName = pet->name;

		// Food, under PLAYERBOT_NEWPET_FEED_BELOW_DAYS of life.
		if (pet->lifeUntil < unixNow + PLAYERBOT_NEWPET_FEED_BELOW_DAYS * DAY)
			if (LPITEM food = FindPlayerBotNewPetItem(ch, ITEM_PROTEIN))
			{
				if (!UseProtein(ch, food, owner, *pet))
					return false;
				++s_kPlayerBotNewPetStats.fed;
				const Pet* now = ActivePet(owner);
				sys_log(0, "PLAYERBOT_NEWPET: fed pid=%u name=%s pet=%u pet_name=%s days_left=%u proteins_left=%d",
						ch->GetPlayerID(), ch->GetName(), petId, petName.c_str(),
						now && now->lifeUntil > unixNow ? (now->lifeUntil - unixNow) / DAY : 0U,
						(int)ch->CountSpecifyItem(ITEM_PROTEIN));
				return true;
			}

		// A treat while the pet can still grow (UseTreat refuses at the cap).
		if (pet->level < Cap(pet->evolution))
		{
			static const DWORD treats[2] = { ITEM_TREAT_PLUS, ITEM_TREAT };
			for (int t = 0; t < 2; ++t)
				if (LPITEM treat = FindPlayerBotNewPetItem(ch, treats[t]))
				{
					const int level = pet->level;
					if (!UseTreat(ch, treat, owner, *pet, treats[t] == ITEM_TREAT_PLUS))
						return false;
					++s_kPlayerBotNewPetStats.treats;
					const Pet* now = ActivePet(owner);
					sys_log(0, "PLAYERBOT_NEWPET: treat pid=%u name=%s pet=%u pet_name=%s item=%u level=%d->%d",
							ch->GetPlayerID(), ch->GetName(), petId, petName.c_str(), treats[t], level, now ? now->level : level);
					return true;
				}
		}

		// An elixir of the size each bonus is at, the pet's level allowing.
		for (int b = 0; b < BONUS_COUNT; ++b)
		{
			const int have = pet->bonus[b];
			if (have >= BONUS_LEVEL_MAX)
				continue;
			const int step = std::min(3, have / 5);
			if (pet->level < DEW_PET_LEVEL[step])
				continue;
			LPITEM dew = FindPlayerBotNewPetItem(ch, DEW_FIRST[b] + step);
			if (!dew)
				continue;
			if (!UseDew(ch, dew, owner, *pet, b, step))
				return false;
			++s_kPlayerBotNewPetStats.elixirs;
			sys_log(0, "PLAYERBOT_NEWPET: elixir pid=%u name=%s pet=%u pet_name=%s bonus=%d level=%d->%d item=%u",
					ch->GetPlayerID(), ch->GetName(), petId, petName.c_str(), b, have, have + 1, DEW_FIRST[b] + step);
			return true;
		}

		// Books: the chosen skills in their order, then any skill it knows.
		{
			int wanted[4];
			const int n = GetPlayerBotNewPetSkills(ch, wanted);
			std::vector<int> order(wanted, wanted + n);
			for (int i = 0; i < SKILL_SLOTS; ++i)
				if (pet->skillType[i] >= 1 && pet->skillType[i] <= SKILL_COUNT &&
						std::find(order.begin(), order.end(), (int)pet->skillType[i]) == order.end())
					order.push_back(pet->skillType[i]);
			for (size_t k = 0; k < order.size(); ++k)
			{
				const int skill = order[k];
				int slot = -1, free = -1;
				for (int i = 0; i < SKILL_SLOTS; ++i)
				{
					if (pet->skillType[i] == skill)
						slot = i;
					else if (pet->skillType[i] == 0 && free < 0)
						free = i;
				}
				if (slot >= 0 ? pet->skillLevel[slot] >= SKILL_LEVEL_MAX : free < 0)
					continue;
				LPITEM book = FindPlayerBotNewPetItem(ch, ITEM_BOOK_FIRST + skill - 1);
				const int before = slot >= 0 ? (int)pet->skillLevel[slot] : 0;
				if (!book)
					continue;
				if (!UseBook(ch, book, owner, *pet))
					return false;
				++s_kPlayerBotNewPetStats.skills;
				sys_log(0, "PLAYERBOT_NEWPET: skill pid=%u name=%s pet=%u pet_name=%s skill=%d level=%d->%d new=%d",
						ch->GetPlayerID(), ch->GetName(), petId, petName.c_str(), skill, before, before + 1, slot < 0 ? 1 : 0);
				return true;
			}
		}

		// The book chest: a random book (UseBookChest), for the rule above or a counter.
		if (LPITEM chest = FindPlayerBotNewPetItem(ch, ITEM_BOOK_CHEST))
			if (ch->GetEmptyInventory(1) >= 0 && UseBookChest(ch, chest))
			{
				++s_kPlayerBotNewPetStats.chests;
				sys_log(0, "PLAYERBOT_NEWPET: chest pid=%u name=%s pet=%u", ch->GetPlayerID(), ch->GetName(), petId);
				return true;
			}

		// The evolution, at the cap, with the materials and the yang over the
		// bot's reserve (and the Grand Master's stones).
		if (pet->evolution < EVOLUTION_MAX && pet->level >= Cap(pet->evolution))
		{
			const EvolutionCost& cost = EVOLUTION_COSTS[pet->evolution];
			bool ready = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) >= cost.gold;
			for (int i = 0; i < EVOLUTION_ITEMS && ready; ++i)
				if (cost.vnum[i] && cost.count[i])
					ready = (int)ch->CountSpecifyItem(cost.vnum[i]) >= GetPlayerBotNewPetMaterialNeed(ch, cost.vnum[i], cost.count[i]);
			if (ready)
			{
				const int evolution = pet->evolution;
				const long long gold = (long long)ch->GetGold();
				Evolve(ch);
				const Pet* now = ActivePet(owner);
				if (now && now->id == petId && now->evolution > evolution)
				{
					++s_kPlayerBotNewPetStats.evolved;
					sys_log(0, "PLAYERBOT_NEWPET: evolved pid=%u name=%s pet=%u pet_name=%s evolution=%d(%s) level=%d paid=%lld gold=%lld",
							ch->GetPlayerID(), ch->GetName(), petId, petName.c_str(), now->evolution,
							EVOLUTION_NAMES[MINMAX(0, now->evolution, (int)EVOLUTION_MAX)], now->level,
							gold - (long long)ch->GetGold(), (long long)ch->GetGold());
					return true;
				}
				++s_kPlayerBotNewPetStats.evolveFails;
				sys_log(0, "PLAYERBOT_NEWPET: evolve failed pid=%u name=%s pet=%u evolution=%d", ch->GetPlayerID(), ch->GetName(),
						petId, evolution);
			}
		}
		return false;
	}

	void LogPlayerBotNewPetCensus(DWORD dwNow)
	{
		using namespace mt2009_newpet;
		// This core's keepers, from their last looks and the live Owners.
		DWORD keepers = 0, withPet = 0, out = 0, hungry = 0, atCap = 0, levelSum = 0, levelMax = 0;
		DWORD evo[EVOLUTION_MAX + 1] = { 0 };
		const DWORD unixNow = (DWORD)time(NULL);
		for (std::map<DWORD, TPlayerBotNewPetView>::iterator it = s_mapPlayerBotNewPet.begin(); it != s_mapPlayerBotNewPet.end(); )
		{
			// A bot gone from this core for an hour is forgotten.
			if ((int)(dwNow - it->second.lastSeen) > 60 * 60 * 1000)
			{
				s_mapPlayerBotNewPetMarketAnswer.erase(it->first);
				s_mapPlayerBotNewPet.erase(it++);
				continue;
			}
			const TPlayerBotNewPetView& v = it->second;
			++it;
			if (!v.known || (int)(dwNow - v.lastSeen) > (int)(2 * PLAYERBOT_NEWPET_LOOK_MAX_MS))
				continue;
			++keepers;
			if (!v.hasPet)
				continue;
			++withPet;
			out += v.out ? 1 : 0;
			hungry += v.lifeUntil <= unixNow ? 1 : 0;
			atCap += v.atCap && v.evolution < EVOLUTION_MAX ? 1 : 0;
			levelSum += (DWORD)v.level;
			levelMax = std::max<DWORD>(levelMax, (DWORD)v.level);
			++evo[MINMAX(0, v.evolution, (int)EVOLUTION_MAX)];
		}
		DWORD botOwners = 0;
		for (std::map<DWORD, Owner>::const_iterator it = s_owners.begin(); it != s_owners.end(); ++it)
			botOwners += it->second.bot ? 1 : 0;
		const TPlayerBotNewPetStats& s = s_kPlayerBotNewPetStats;
		sys_log(0, "PLAYERBOT_NEWPET: census core keepers=%u with_pet=%u out=%u hungry=%u at_cap=%u lv_avg=%u lv_max=%u "
				"evo=%u/%u/%u/%u owners=%u | hatched=%u hatch_fails=%u fed=%u treats=%u elixirs=%u skills=%u chests=%u "
				"evolved=%u evolve_fails=%u summoned=%u levelups=%u level_flushes=%u",
				keepers, withPet, out, hungry, atCap, withPet ? levelSum / withPet : 0, levelMax,
				evo[0], evo[1], evo[2], evo[3], botOwners, s.hatched, s.hatchFails, s.fed, s.treats, s.elixirs, s.skills,
				s.chests, s.evolved, s.evolveFails, s.summoned, s_dwBotLevelUps, s_dwBotLevelUpFlushes);
		s_kPlayerBotNewPetStats = TPlayerBotNewPetStats();
		s_dwBotLevelUps = s_dwBotLevelUpFlushes = 0;
		// Every bot's row in the world (one aggregate of a small table, once
		// a census): how many bots own a pet, their levels and evolutions.
		if (!EnsureTables())
			return;
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"SELECT COUNT(*), COUNT(DISTINCT n.pid), IFNULL(ROUND(AVG(n.level)),0), IFNULL(MAX(n.level),0), "
				"IFNULL(SUM(n.evolution=0),0), IFNULL(SUM(n.evolution=1),0), IFNULL(SUM(n.evolution=2),0), IFNULL(SUM(n.evolution=3),0), "
				"IFNULL(SUM(n.life_until < UNIX_TIMESTAMP()),0), IFNULL(SUM(n.skills REGEXP '(^|,)([1-9]|1[0-9]|2[0-2])\\\\.'),0) "
				"FROM player.newpet_pet n JOIN player.player p ON p.id = n.pid JOIN account.account a ON a.id = p.account_id "
				"WHERE a.login LIKE 'playerbot\\\\_%'"));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
			return;
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		if (!row)
			return;
		sys_log(0, "PLAYERBOT_NEWPET: census world pets=%s owners=%s lv_avg=%s lv_max=%s evo=%s/%s/%s/%s hungry=%s with_skills=%s",
				row[0] ? row[0] : "0", row[1] ? row[1] : "0", row[2] ? row[2] : "0", row[3] ? row[3] : "0",
				row[4] ? row[4] : "0", row[5] ? row[5] : "0", row[6] ? row[6] : "0", row[7] ? row[7] : "0",
				row[8] ? row[8] : "0", row[9] ? row[9] : "0");
	}

	// The tick's call (playerbot_manager.cpp, beside the rank points).
	void ManagePlayerBotNewPet(LPCHARACTER ch, DWORD dwNow)
	{
		using namespace mt2009_newpet;
		if (s_dwPlayerBotNewPetCensusAt == 0 || (int)(dwNow - s_dwPlayerBotNewPetCensusAt) >= 0)
		{
			if (s_dwPlayerBotNewPetCensusAt != 0)
				LogPlayerBotNewPetCensus(dwNow);
			s_dwPlayerBotNewPetCensusAt = dwNow + PLAYERBOT_NEWPET_CENSUS_MS;
		}
		if (!ch || ch->IsDead() || !ch->IsItemLoaded() || !IsPlayerBotNewPetKeeper(ch))
			return;
		TPlayerBotNewPetView& view = s_mapPlayerBotNewPet[ch->GetPlayerID()];
		view.lastSeen = dwNow;
		if (view.nextLook != 0 && (int)(dwNow - view.nextLook) < 0)
		{
			// Between the looks the pet is only brought out again after a
			// warp or a death took it (no query: memory alone).
			Owner* owner = FindOwner(ch->GetPlayerID());
			if (owner)
				view.out = IsOut(*owner);
			return;
		}
		view.nextLook = dwNow + (view.nextLook == 0 ? (DWORD)number(5000, 60000)
				: (DWORD)number(PLAYERBOT_NEWPET_LOOK_MIN_MS, PLAYERBOT_NEWPET_LOOK_MAX_MS));
		if (ch->GetExchange() || ch->GetMyShop() || ch->IsObserverMode() || !EnsureTables())
			return;
		Owner& owner = GetOwner(ch);
		owner.bot = true;
		ChoosePlayerBotNewPet(ch, owner, view, dwNow);	// MT2009_PLUS_NEWPET_EGG_RANK_V1
		for (int acts = 0; acts < PLAYERBOT_NEWPET_ACTS_PER_LOOK && ActivePet(owner); ++acts)
			if (!ActPlayerBotNewPet(ch, owner))
				break;
		Pet* pet = ActivePet(owner);
		if (pet && !IsOut(owner) && pet->lifeUntil > (DWORD)time(NULL) && ch->GetSectree())
			if (Summon(ch, owner, true))
			{
				++s_kPlayerBotNewPetStats.summoned;
				pet = ActivePet(owner);
				if (pet)
					sys_log(0, "PLAYERBOT_NEWPET: summoned pid=%u name=%s map=%ld pet=%u pet_name=%s level=%d evolution=%d days_left=%u",
							ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), pet->id, pet->name.c_str(), pet->level,
							pet->evolution, (pet->lifeUntil - (DWORD)time(NULL)) / DAY);
			}
		NotePlayerBotNewPetView(ch, owner, dwNow);
	}
}

#endif
