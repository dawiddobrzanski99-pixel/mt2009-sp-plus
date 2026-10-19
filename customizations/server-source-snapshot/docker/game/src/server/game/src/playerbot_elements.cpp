// MT2009_PLUS_ELEMENTS_V1 - Elements and talismans ("Zywioly i talizmany"). Autor: Digi Rasta
// (nowy-system 0.28.0, SYSTEMY/zywioly-talizmany.md, his nowy_system_zywioly.cpp), ported into
// MT2009 PLUS with the owner's rules of 7 October 2026 (server-patches/zywioly/README.md).
//
// The engine side is server-patches/zywioly/edits.json: the six element powers are server-only
// points POINT_ENCHANT_ELECT..DARK = POINT_PACKET_NUM (178)..183 (length.h - the points packet and
// the point change still send 0..177, so the client exe's packets do not change), PointChange
// knows them, CalcAttBonus (battle.cpp: plain hits, arrows and skills) calls ElementsAttackBonus,
// the boss drop calls ElementsTalismanDrop and the two refine paths count and take a material
// that is the refined item's own vnum (a Talisman +0 refined with a second Talisman +0) past the
// item itself.
//
// Element power X% of one element (wiki "Sila Zywiolu", his formula): against a monster of that
// element the first 1% is +18% damage, every next one +0.5%, capped at 80% (X = 125); besides,
// every full 10% of one element is +1% damage against everything (at most +20% an element) - as
// he implemented it, so it also counts in PvP, where no element bonus applies (a player has no
// element). Element resistance X%: a monster of that element hits for X% less (cap 80%).
// The monsters' elements are the race flag bits 11-16 (world.mob_proto.setRaceFlag), set by the
// owner's rules (tools/zywioly/gen_zywioly_moby.py -> mariadb/playerbot/zywioly_moby.sql).
#include "stdafx.h"
#include "char.h"
#include "item.h"
#include "item_manager.h"

#ifdef MT2009_PLUS_ELEMENTS_V1

#ifdef ENABLE_12ZI
#include "playerbot_zodiac_temple.h"
#endif

// MT2009_PLUS_ZODIAC_ELEMENTS_V1 - the Swiatynia Zodiaku's element (the owner, 9 October, as the PL wiki):
// every monster, Metin and boss on a temple floor has its sign's element - Zi Mrok, Chou Ziemia, Yin Ogien,
// Mao Wiatr, Chen Blyskawica, Si Lod, Wu Lod, Wei Blyskawica, Shen Ziemia, Yu Wiatr, Xu Mrok, Hai Ogien.
// The temple's monsters and Metins are the same vnums in several signs (group.zodiak.txt, SpawnStone), so the
// element is the floor's, read here at run time from the CZodiac of the victim's (or attacker's) map; on a
// temple floor it replaces the proto's bits. The bosses (2750-2862, ten vnums a sign) carry it in mob_proto
// as well (tools/zywioly rule g), so the client shows their element; the others show none.
static bool ElementsHasFlag(LPCHARACTER mob, DWORD flag)
{
#ifdef ENABLE_12ZI
	const long map = mob->GetMapIndex();
	if (map >= 3580000 && map < 3590000)
	{
		static const DWORD SIGN_FLAG[13] = { 0,
			RACE_FLAG_ATT_DARK, RACE_FLAG_ATT_EARTH, RACE_FLAG_ATT_FIRE, RACE_FLAG_ATT_TEMPLE, RACE_FLAG_ATT_ELEC,
			RACE_FLAG_ATT_ICE, RACE_FLAG_ATT_ICE, RACE_FLAG_ATT_ELEC, RACE_FLAG_ATT_EARTH, RACE_FLAG_ATT_TEMPLE,
			RACE_FLAG_ATT_DARK, RACE_FLAG_ATT_FIRE };
		LPZODIAC z = CZodiacManager::instance().FindByMapIndex(map);
		const BYTE sign = z ? z->GetPortal() : 0;
		if (sign >= 1 && sign <= 12)
			return flag == SIGN_FLAG[sign];
	}
#endif
	return mob->IsRaceFlag(flag);
}

// A Talisman +0 from a boss (rank >= boss) of its element 5%, from a Metin stone of its element
// 2% - the element read from the monster's race flags, as for the damage. Called beside the
// boss / mod drop in CHARACTER::Reward (char_battle.cpp). Under the owner's rules no Metin
// stone has an element, so only the bosses (and the Razador / Nemere chests) give talismans.
bool ElementsTalismanDrop(LPCHARACTER victim, LPCHARACTER killer, std::vector<LPITEM>& vec_item)
{
	if (!victim || !killer || !victim->IsNPC())
		return false;

	const bool metin = victim->IsStone();
	if (!metin && victim->GetMobRank() < MOB_RANK_BOSS)
		return false;

	static const struct { DWORD flag; DWORD vnum; } TALISMAN_OF[] = {
		{ RACE_FLAG_ATT_FIRE, 94000 }, { RACE_FLAG_ATT_ELEC, 94250 }, { RACE_FLAG_ATT_ICE, 94500 },
		{ RACE_FLAG_ATT_TEMPLE, 94750 }, { RACE_FLAG_ATT_EARTH, 95000 }, { RACE_FLAG_ATT_DARK, 95250 },
	};

	bool dropped = false;
	for (const auto& t : TALISMAN_OF)
	{
		if (!ElementsHasFlag(victim, t.flag) || number(1, 1000) > (metin ? 20 : 50))
			continue;

		LPITEM item = ITEM_MANAGER::instance().CreateItem(t.vnum, 1, 0, true);
		if (!item)
		{
			sys_err("ZYWIOLY: no talisman %u in item_proto (drop of %u)", t.vnum, victim->GetRaceNum());
			continue;
		}
		vec_item.emplace_back(item);
		dropped = true;
	}
	return dropped;
}

// The refine material whose vnum is the refined item's own (a Talisman +0 when refining
// Talisman +0 -> +1): counted without the refined item...
ITEM_COUNT ElementsRefineMaterialCount(LPCHARACTER ch, LPITEM refined, DWORD vnum)
{
	ITEM_COUNT count = ch->CountSpecifyItem(vnum);
	if (refined && refined->GetVnum() == vnum)
		count -= MIN(count, refined->GetCount());
	return count;
}

// ...and taken from the other pieces only.
void ElementsRefineMaterialRemove(LPCHARACTER ch, LPITEM refined, DWORD vnum, ITEM_COUNT count)
{
	if (!refined || refined->GetVnum() != vnum)
	{
		ch->RemoveSpecifyItem(vnum, count);
		return;
	}

	for (UINT i = 0; i < INVENTORY_MAX_NUM && count; ++i)
	{
		LPITEM it = ch->GetInventoryItem(i);
		if (!it || it == refined || it->GetVnum() != vnum)
			continue;

		const ITEM_COUNT take = MIN(count, it->GetCount());
		it->SetCount(it->GetCount() - take);
		count -= take;
	}
}

namespace
{
	struct TElement
	{
		DWORD flag;
		BYTE power;
		BYTE resist;
	};

	// The race flag bits 11-16. Bit 14 is RACE_FLAG_ATT_TEMPLE here and RACE_FLAG_ATT_WIND in the client.
	const TElement ELEMENTS[] = {
		{ RACE_FLAG_ATT_ELEC,	POINT_ENCHANT_ELECT,	POINT_RESIST_ELEC },
		{ RACE_FLAG_ATT_FIRE,	POINT_ENCHANT_FIRE,		POINT_RESIST_FIRE },
		{ RACE_FLAG_ATT_ICE,	POINT_ENCHANT_ICE,		POINT_RESIST_ICE },
		{ RACE_FLAG_ATT_TEMPLE,	POINT_ENCHANT_WIND,		POINT_RESIST_WIND },
		{ RACE_FLAG_ATT_EARTH,	POINT_ENCHANT_EARTH,	POINT_RESIST_EARTH },
		{ RACE_FLAG_ATT_DARK,	POINT_ENCHANT_DARK,		POINT_RESIST_DARK },
	};

	const int ELEMENT_CAP_PERCENT = 80;
	const int GENERAL_MAX_PERCENT = 20;

	// The bonus against the element in half percents: 1% of power = 36 (18%), each next +1 (0.5%).
	int ElementHalfPercents(int power)
	{
		if (power <= 0)
			return 0;
		return MIN(36 + (power - 1), ELEMENT_CAP_PERCENT * 2);
	}
}

int ElementsAttackBonus(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, int iAtk)
{
	if (!pkAttacker || !pkVictim || iAtk <= 0)
		return iAtk;

	if (pkAttacker->IsPC())
	{
		int halves = 0;
		int general = 0;

		for (const TElement& e : ELEMENTS)
		{
			const int power = pkAttacker->GetPoint(e.power);
			if (power <= 0)
				continue;

			general += MIN(power / 10, GENERAL_MAX_PERCENT);
			if (pkVictim->IsNPC() && ElementsHasFlag(pkVictim, e.flag))
				halves += ElementHalfPercents(power);
		}

		if (halves || general)
		{
			const int before = iAtk;
			iAtk += (int)((long long)iAtk * (halves + general * 2) / 200);
			if (pkAttacker->GetGMLevel() > GM_PLAYER)	// the GM's diagnosis (syslog)
				sys_log(0, "ZYWIOLY: %s -> %s (%u): %d -> %d (element +%d.%d%%, general +%d%%)", pkAttacker->GetName(),
						pkVictim->GetName(), pkVictim->GetRaceNum(), before, iAtk, halves / 2, halves % 2 ? 5 : 0, general);
		}
	}
	else if (pkAttacker->IsNPC() && pkVictim->IsPC())
	{
		int resist = 0;

		for (const TElement& e : ELEMENTS)
			if (ElementsHasFlag(pkAttacker, e.flag))
				resist = MAX(resist, MIN(pkVictim->GetPoint(e.resist), ELEMENT_CAP_PERCENT));

		if (resist > 0)
		{
			const int before = iAtk;
			iAtk -= (int)((long long)iAtk * resist / 100);
			if (pkVictim->GetGMLevel() > GM_PLAYER)	// the GM's diagnosis (syslog)
				sys_log(0, "ZYWIOLY: %s (%u) -> %s: %d -> %d (resist %d%%)", pkAttacker->GetName(),
						pkAttacker->GetRaceNum(), pkVictim->GetName(), before, iAtk, resist);
		}
	}

	return iAtk;
}

#endif // MT2009_PLUS_ELEMENTS_V1
