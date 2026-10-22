// MT2009_PLUS_COLLECTOR_STORAGE_V1: "Magazyn kolekcjonera", the collector's
// storage - one store for the whole account beside the classic safebox, at
// the storekeeper, opened from the safebox window (client uicollector.py).
// The upstream window's features, rewritten so that a move is instant
// (playerbot_collector.cpp, the design; server-patches/collector/README.md).
//
// "/kolekcjoner <word> ..." (cmd.cpp, server-patches/collector):
//   open                                   the safebox must be open
//   przedmiot                              MT2009_PLUS_COLLECTOR_ITEM_V1: the
//                                          "Kolekcjoner" item (ITEM_VNUM) in the
//                                          bag instead of the open safebox (its
//                                          use runs this, quest kolekcjoner_item)
//   close
//   put <op> <bag cell> <count>            0 = the whole stack
//   putall <op> <bag cell> [keep=<hex>]    every stack of that kind in the bag
//   take <op> <entry id> <count> <cell>    0 = one stack; cell -1 = anywhere
//   expand <op>                            the next tier, for yang
// and its answers, chat commands "COLL <word> ...":
//   begin <tier> <capacity> <entries> <tiers ok>, e <entry> ..., end
//   set <entry>, del <id>, res <op> <code> <units>, tier <tier> <capacity>,
//   close <reason>, err <code>
// An entry is "id,vnum,count,s0,s1,s2[,type:value;...x7]".
#pragma once

// A normal header, included after stdafx.h (LPCHARACTER, DWORD).

namespace playerbot_collector {

enum EResult {
	RESULT_DONE = 0,
	RESULT_PARTIAL = 1,
	RESULT_BUSY = 2,
	RESULT_NO_SESSION = 3,
	RESULT_NO_ITEM = 4,
	RESULT_REFUSED = 5,
	RESULT_FULL = 6,
	RESULT_NO_ROOM = 7,
	RESULT_TOO_FAR = 8,
	RESULT_BAD_REQUEST = 9,
	RESULT_DEAD = 10,
	RESULT_LEVEL = 11,
	RESULT_GOLD = 12,
	RESULT_MAX_TIER = 13,
	RESULT_COOLDOWN = 14,
	RESULT_LOADING = 15,
	RESULT_DISABLED = 16,
};

enum EOpenError {
	OPEN_NO_SAFEBOX = 1,
	OPEN_BUSY = 2,
	OPEN_DEAD = 3,
	OPEN_DB = 4,
	OPEN_TOO_FAR = 5,
	OPEN_NO_ITEM = 6,	// MT2009_PLUS_COLLECTOR_ITEM_V1: "przedmiot" without the item in the bag
};

enum ECloseReason {
	CLOSE_ASKED = 0,
	CLOSE_FAR = 1,
	CLOSE_GONE = 2,
};

// The tiers (entries, level, yang) - the upstream table of 1 October.
const int TIER_COUNT = 7;
const DWORD TIER_ENTRIES[TIER_COUNT] = { 500, 1000, 2000, 3500, 5000, 7500, 10000 };
const int TIER_LEVEL[TIER_COUNT] = { 0, 20, 35, 50, 65, 80, 90 };
const long long TIER_PRICE[TIER_COUNT] = { 0, 100000LL, 500000LL, 2000000LL, 5000000LL, 10000000LL, 20000000LL };

// A stored entry is the item's own row of player.item: window SAFEBOX, owner
// OWNER_BASE + the account id. No player id or account id comes near it, so
// neither the character load nor the classic safebox load (owner = account,
// ClientManager.cpp) ever reads it, and the db core writes a SAFEBOX row at
// once instead of caching it (QUERY_ITEM_SAVE).
const DWORD OWNER_BASE = 2000000000u;
// An entry's units: unlimited stacking up to here.
const DWORD MAX_ENTRY_COUNT = 2000000000u;
// A move must be within this of where the window was opened.
const int MAX_DISTANCE = 1500;

// MT2009_PLUS_COLLECTOR_ITEM_V1: "Kolekcjoner" (the ItemShop's, 1000 SM; world.item_proto
// from linux-port/docker/mariadb/playerbot/apply.sh, the client's from
// client-patches/client-2.0.30/tools/collectoritem). Not used up: while it is in the bag,
// using it opens this store wherever the character stands, without the storekeeper and
// his safebox (game/quest/kolekcjoner_item.quest -> "/kolekcjoner przedmiot"). The bots
// never buy it (playerbot_itemshop.h leaves its lines out of their catalogue) and never
// open the store (RealPlayer).
const DWORD ITEM_VNUM = 70115;

void Command(LPCHARACTER ch, const char* argument);

}  // namespace playerbot_collector

#include "../../common/tables.h"
namespace playerbot_collector {void WarmRefine(LPCHARACTER ch);bool PayRefine(LPCHARACTER ch,LPITEM refined,LPITEM scroll,const TRefineTable* recipe);}

namespace playerbot_collector {void WarmRefineForRecipe(LPCHARACTER ch,const TRefineTable* recipe);}

namespace playerbot_collector {unsigned long long CountBiologMaterial(LPCHARACTER ch,DWORD vnum);bool ConsumeBiologMaterial(LPCHARACTER ch,DWORD vnum,ITEM_COUNT count);}

namespace playerbot_collector {bool KuzniaAutoStore(LPCHARACTER ch,LPITEM item);} // MT2009_NASZE_INNE_V1 (auto_kolekcjoner)
