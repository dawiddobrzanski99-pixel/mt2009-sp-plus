// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "db.h"
#include "item.h"
#include "item_manager.h"
#include "locale_service.h"
#include "mob_manager.h"
#include "party.h"
#include "dungeon.h"
#include "sectree_manager.h"
#include "regen.h"
#include "packet.h"
#include "cmd.h"
#include "questmanager.h"
#include "playerbot_zodiac_temple.h"

#include "../../common/CommonDefines.h"

// ZODIAK: definicje wyciete z char.cpp, dungeon.cpp, party.cpp, char_manager.cpp, questmanager.cpp i cmd_general.cpp,
// zeby w plikach moda zostaly tylko krotkie haki (Serwer/nowy-system/zodiak_haki.py).

#ifdef ENABLE_12ZI

// ---- CHARACTER
void CHARACTER::SetZodiac(LPZODIAC pkZodiac)
{
	if (pkZodiac && m_pkZodiac)
		sys_err("%s is trying to reassigning zodiac (current %p, new party %p)", GetName(), get_pointer(m_pkZodiac), get_pointer(pkZodiac));

	if (m_pkZodiac == pkZodiac)
	{
		return;
	}

	if (m_pkZodiac)
	{
		if (IsPC())
		{
			if (GetParty())
				m_pkZodiac->DecPartyMember(GetParty(), this);
			else
				m_pkZodiac->DecMember(this);
		}
		else if (IsMonster() || IsStone())
		{
			m_pkZodiac->DecMonster();
		}
	}

	m_pkZodiac = pkZodiac;

	if (pkZodiac)
	{
		sys_log(0, "%s ZODIAC set to %p, PARTY is %p", GetName(), get_pointer(pkZodiac), get_pointer(m_pkParty));

		if (IsPC())
		{
			if (GetParty())
				m_pkZodiac->IncPartyMember(GetParty(), this);
			else
				m_pkZodiac->IncMember(this);
		}
		else if (IsMonster() || IsStone())
		{
			m_pkZodiac->IncMonster();
		}
	}
}

LPZODIAC CHARACTER::GetZodiacForce() const
{
	if (m_lWarpMapIndex > 10000)
		return CZodiacManager::instance().FindByMapIndex(m_lWarpMapIndex);

	return m_pkZodiac;
}


void CHARACTER::BeadTime()
{
	int animaSphere = GetAnimaSphere();
	int lastTime = GetQuestFlag("12zi_temple.beadtime");
	int remainTime = 3600 - (get_global_time() - lastTime);

	if (animaSphere >= 36)
	{
		ChatPacket(CHAT_TYPE_COMMAND, "Bead_count %d", GetAnimaSphere());
		ChatPacket(CHAT_TYPE_COMMAND, "Bead_time %d", 0);
		return;
	}

	if ((animaSphere == 0) && (lastTime == 0))
	{
		SetAnimaSphere(36);
		SetQuestFlag("12zi_temple.beadtime", get_global_time());
		ChatPacket(CHAT_TYPE_COMMAND, "Bead_count %d", GetAnimaSphere());
		ChatPacket(CHAT_TYPE_COMMAND, "Bead_time %d", 0);
		return;
	}

	if (animaSphere < 36 && ((get_global_time() - lastTime) > 3600))
	{
		int iTime = get_global_time() - lastTime;
		int iCount = iTime/3600;

		if ((animaSphere+iCount) <= 36)
		{
			SetAnimaSphere(iCount);
		}
		else if ((animaSphere+iCount) > 36)
		{
			int jCount = 36-animaSphere;
			if (jCount <= 36)
				SetAnimaSphere(jCount);

			ChatPacket(CHAT_TYPE_COMMAND, "Bead_count %d", GetAnimaSphere());
			ChatPacket(CHAT_TYPE_COMMAND, "Bead_time %d", 0);
		}

		SetQuestFlag("12zi_temple.beadtime", get_global_time());
		ChatPacket(CHAT_TYPE_COMMAND, "Bead_count %d", GetAnimaSphere());
		ChatPacket(CHAT_TYPE_COMMAND, "Bead_time %d", remainTime);
		return;
	}

	ChatPacket(CHAT_TYPE_COMMAND, "Bead_count %d", animaSphere);
	ChatPacket(CHAT_TYPE_COMMAND, "Bead_time %d", remainTime);
}

void CHARACTER::MarkTime()
{
	int markLastTime = GetQuestFlag("12zi_temple.MarkTime");
	int markRemainTime = markLastTime - get_global_time();

	if (markRemainTime <= 0)
	{
		if (FindAffect(AFFECT_CZ_UNLIMIT_ENTER))
			RemoveAffect(AFFECT_CZ_UNLIMIT_ENTER);
	}
	else
	{
		RemoveAffect(AFFECT_CZ_UNLIMIT_ENTER);
		AddAffect(AFFECT_CZ_UNLIMIT_ENTER, 0, 0, AFF_CZ_UNLIMIT_ENTER, markRemainTime, 0, false);
	}
}

int CHARACTER::GetAnimaSphere()
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT bead FROM player.player WHERE id = '%d';", GetPlayerID()));
	if (pMsg->Get()->uiNumRows == 0)
		return 0;

	MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
	int bBead = 0;
	str_to_number(bBead, row[0]);
	return bBead;
}

void CHARACTER::SetAnimaSphere(int amount)
{
	int value = abs(amount);

	if (amount > 0)
	{
		DBManager::instance().DirectQuery("UPDATE player.player SET bead = bead + '%d' WHERE id = '%d'", value, GetPlayerID());
	}
	else
	{
		SetQuestFlag("12zi_temple.beadtime", get_global_time());
		DBManager::instance().DirectQuery("UPDATE player.player SET bead = bead - '%d' WHERE id = '%d'", value, GetPlayerID());
	}

	ChatPacket(CHAT_TYPE_COMMAND, "Bead_count %d", GetAnimaSphere());
}

void CHARACTER::IsZodiacEffectMob()
{
	if (!this)
		return;

	if (!IsMonster())
		return;

	if (IsDead())
		return;

	DWORD Monster = GetRaceNum();

	if (!Monster || Monster == 0)
		return;

	if (Monster == 2750 || Monster == 2860) //Officer (Zi or Hai)
	{
		if (number(1, 2) == 1)
		{
			EffectPacket(SE_SKILL_DAMAGE_ZONE);
		}
		else
		{
			EffectPacket(SE_SKILL_SAFE_ZONE);
		}
	}
}

void CHARACTER::IsZodiacEffectPC(DWORD Monster)
{
	if (!this)
		return;

	if (!IsPC())
		return;

	if (IsDead())
		return;

	if (!Monster || Monster == 0)
		return;

	if (!GetDesc() || !GetDesc()->GetCharacter())
	{
		sys_err("Character::IsZodiacEffectPC : cannot get desc or character");
		return;
	}

	if (Monster == 20464) //Canon
		EffectPacket(SE_DEAPO_BOOM);
	else if (Monster == 2770 || Monster == 2771 || Monster == 2772) //Yin
		EffectPacket(SE_METEOR);
	else if (Monster == 2790 || Monster == 2791 || Monster == 2792) //Chen
		EffectPacket(SE_BEAD_RAIN);
	else if (Monster == 2830 || Monster == 2831 || Monster == 2832) //Shen
		EffectPacket(SE_FALL_ROCK);
	else if (Monster == 2800 || Monster == 2801 || Monster == 2802) //Si
		EffectPacket(SE_ARROW_RAIN);
	else if (Monster == 2810 || Monster == 2811 || Monster == 2812) //Wu
		EffectPacket(SE_HORSE_DROP);
	else if (Monster == 2840 || Monster == 2841 || Monster == 2842) //Yu
		EffectPacket(SE_EGG_DROP);
}

void CHARACTER::ZodiacFloorMessage(BYTE Floor)
{
	if (!IsPC())
		return;

#ifdef ENABLE_CHAT_MISSION_ALTERNATIVE
	if ((Floor >= 1 && Floor <= 5) || (Floor == 9) || (Floor == 10) || (Floor == 16) || (Floor == 20) || (Floor == 23) || (Floor == 25) || (Floor == 26) || (Floor >= 31 && Floor <= 33))
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat_all_monsters.")); //246
	else if (Floor == 6)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat_the_Zodiac_boss_without_dying.")); //256
	else if (Floor == 7 || Floor == 21)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Destroy_a_Metin_stone._If_you_are_successful,_you'll_receive_a_bonus_buff.")); //262
	else if (Floor == 8 || Floor == 27 || Floor == 30)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Destroy_all_Metin_stones.")); //242
	else if (Floor == 11 || Floor == 17)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat_the_Zodiac_boss.")); //254
	else if (Floor == 12 || Floor == 19 || Floor == 24)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat_all_monsters_without_dying.")); //257
	else if (Floor == 13 || Floor == 18 || Floor == 29)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Destroy_Metin_stones.")); //234
	else if (Floor == 14 || Floor == 28)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Bonus_level:_Destroy_Metin_stones.")); //235
	else if (Floor == 15 || Floor == 34)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat_monsters.")); //248
	else if (Floor == 22)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat_all_Zodiac_bosses.")); //252
	else if (Floor >= 35 && Floor <= 39)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Bonus_level:_Destroy_a_Metin_stone.")); //261
	else if (Floor == 40)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Bonus_level:_You_have_5_minutes_to_trade_with_the_merchant_and_stock_up_on_supplies.")); //239
	else if (Floor == 41)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("The_mission_was_unsuccessful.")); //225
	else if (Floor == 42)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("You_just_missed_the_bonus_level.")); //251
	else if (Floor == 43)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Time's_up.")); //227
#else
	if ((Floor >= 1 && Floor <= 5) || (Floor == 9) || (Floor == 10) || (Floor == 16) || (Floor == 20) || (Floor == 23) || (Floor == 25) || (Floor == 26) || (Floor >= 31 && Floor <= 33))
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat all monsters.")); //246
	else if (Floor == 6)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat the Zodiac boss without dying.")); //256
	else if (Floor == 7 || Floor == 21)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Destroy a Metin stone. If you are successful, you'll receive a bonus buff.")); //262
	else if (Floor == 8 || Floor == 27 || Floor == 30)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Destroy all Metin stones.")); //242
	else if (Floor == 11 || Floor == 17)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat the Zodiac boss.")); //254
	else if (Floor == 12 || Floor == 19 || Floor == 24)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat all monsters without dying.")); //257
	else if (Floor == 13 || Floor == 18 || Floor == 29)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Destroy Metin stones.")); //234
	else if (Floor == 14 || Floor == 28)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Bonus level: Destroy Metin stones.")); //235
	else if (Floor == 15 || Floor == 34)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat monsters.")); //248
	else if (Floor == 22)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Defeat all Zodiac bosses.")); //252
	else if (Floor >= 35 && Floor <= 39)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Bonus level: Destroy a Metin stone.")); //261
	else if (Floor == 40)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Bonus level: You have 5 minutes to trade with the merchant and stock up on supplies.")); //239
	else if (Floor == 41)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("The mission was unsuccessful.")); //225
	else if (Floor == 42)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("You just missed the bonus level.")); //251
	else if (Floor == 43)
		ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("Time's up.")); //227
#endif
}

void CHARACTER::EffectZodiacPacket(long X, long Y, int enumEffectType, int enumEffectType2)
{
	TPacketGCSpecialZodiacEffect p;

	p.header = HEADER_GC_SEPCIAL_ZODIAC_EFFECT;
	p.type = enumEffectType;
	p.type2 = enumEffectType2;
	p.vid = GetVID();
	p.x = X;
	p.y = Y;

	PacketAround(&p, sizeof(p));
}

DWORD CHARACTER::CountZodiacItems(DWORD Vnum)
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT count FROM player.zodiac_npc WHERE item_vnum = '%u' and owner_id = '%d'", Vnum, GetPlayerID()));
	if (pMsg->Get()->uiNumRows == 0)
		return 0;

	MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
	DWORD dwCount = 0;
	str_to_number(dwCount, row[0]);
	return dwCount;
}

void CHARACTER::SetZodiacItems(DWORD Vnum, int Count)
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT owner_id FROM player.zodiac_npc WHERE item_vnum = '%u' and owner_id = '%u'", Vnum, GetPlayerID()));
	if (pMsg->Get()->uiNumRows == 0)
	{
		char szQuery[512];
		snprintf(szQuery, sizeof(szQuery), "INSERT INTO player.zodiac_npc(owner_id, item_vnum, count) VALUES(%u, %u, %d)", GetPlayerID(), Vnum, Count);
		DBManager::Instance().DirectQuery(szQuery);
		return;
	}
	else
	{
		char szQuery2[512];
		snprintf(szQuery2, sizeof(szQuery2), "UPDATE player.zodiac_npc SET count = '%d' WHERE item_vnum = %u and owner_id = '%u'", Count, Vnum, GetPlayerID());
		DBManager::Instance().DirectQuery(szQuery2);
	}
}

DWORD CHARACTER::PurchaseCountZodiacItems(DWORD Vnum)
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT count FROM player.zodiac_npc_sold WHERE item_vnum = '%u' and owner_id = '%d'", Vnum, GetPlayerID()));
	if (pMsg->Get()->uiNumRows == 0)
		return 0;

	MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
	DWORD dwCount = 0;
	str_to_number(dwCount, row[0]);
	return dwCount;
}

void CHARACTER::SetPurchaseZodiacItems(DWORD Vnum, int Count)
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT owner_id FROM player.zodiac_npc_sold WHERE item_vnum = '%u' and owner_id = '%u'", Vnum, GetPlayerID()));
	if (pMsg->Get()->uiNumRows == 0)
	{
		char szQuery[512];
		snprintf(szQuery, sizeof(szQuery), "INSERT INTO player.zodiac_npc_sold(owner_id, item_vnum, count) VALUES(%u, %u, %d)", GetPlayerID(), Vnum, Count);
		DBManager::Instance().DirectQuery(szQuery);
		return;
	}
	else
	{
		char szQuery2[512];
		snprintf(szQuery2, sizeof(szQuery2), "UPDATE player.zodiac_npc_sold SET count = '%d' WHERE item_vnum = '%u' and owner_id = '%u'", Count, Vnum, GetPlayerID());
		DBManager::Instance().DirectQuery(szQuery2);
	}
}


// ---- CDungeon
namespace
{
	struct FZodiacNotice
	{
		FZodiacNotice(const char * psz) : m_psz(psz)
		{
		}

		void operator() (LPENTITY ent)
		{
			if (ent->IsType(ENTITY_CHARACTER))
			{
				LPCHARACTER ch = (LPCHARACTER) ent;
				if (!ch)
					return;

				if (ch->IsPC())
					ch->ChatPacket(CHAT_TYPE_MISSION, "%s", m_psz);
			}
		}

		const char * m_psz;
	};
}

void CDungeon::ZodiacMessage(const char* msg)
{
	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacNotice f(msg);
	pMap->for_each(f);
}

namespace
{
	struct FZodiacNoticeClear
	{
		void operator() (LPENTITY ent)
		{
			if (ent->IsType(ENTITY_CHARACTER))
			{
				LPCHARACTER ch = (LPCHARACTER) ent;
				if (!ch)
					return;

				if (ch->IsPC())
					ch->ChatPacket(CHAT_TYPE_CLEAR_MISSION, "Zodiac");
			}
		}
	};
}

void CDungeon::ZodiacMessageClear()
{
	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacNoticeClear f;
	pMap->for_each(f);
}

namespace
{
	struct FZodiacTime
	{
		BYTE currentfloor, nextfloor;
		int time;

		FZodiacTime(BYTE c, BYTE n, int t)
			: currentfloor(c), nextfloor(n), time(t)
		{}

		void operator() (LPENTITY ent)
		{
			if (ent->IsType(ENTITY_CHARACTER))
			{
				LPCHARACTER ch = (LPCHARACTER) ent;
				if (!ch)
					return;

				if (ch->IsPC())
					ch->ChatPacket(CHAT_TYPE_COMMAND, "ZodiacTime %d %d %d", currentfloor, nextfloor, time);
			}
		}
	};
}

void CDungeon::ZodiacTime(BYTE currentfloor, BYTE nextfloor, int time)
{
	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacTime f(currentfloor, nextfloor, time);
	pMap->for_each(f);
}

namespace
{
	struct FZodiacTimeClear
	{
		void operator() (LPENTITY ent)
		{
			if (ent->IsType(ENTITY_CHARACTER))
			{
				LPCHARACTER ch = (LPCHARACTER) ent;
				if (!ch)
					return;

				if (ch->IsPC())
					ch->ChatPacket(CHAT_TYPE_COMMAND, "ZodiacTimeClear");
			}
		}
	};
}

void CDungeon::ZodiacTimeClear()
{
	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacTimeClear f;
	pMap->for_each(f);
}

// ---- CParty
void CParty::SetZodiac(LPZODIAC pZodiac)
{
	m_pkZodiac = pZodiac;
	m_map_iFlag.clear();
}

LPZODIAC CParty::GetZodiac()
{
	return m_pkZodiac;
}

void CParty::SetZodiac_for_Only_party(LPZODIAC pZodiac)
{
	m_pkZodiac_for_Only_party = pZodiac;
}

LPZODIAC CParty::GetZodiac_for_Only_party()
{
	return m_pkZodiac_for_Only_party;
}

// ---- CHARACTER_MANAGER

LPCHARACTER CHARACTER_MANAGER::SpawnMobRange(DWORD dwVnum, long lMapIndex, int sx, int sy, int ex, int ey, bool bIsException, bool bSpawnMotion, bool bAggressive, BYTE bLevel)
{
	LPCHARACTER ch = SpawnMobRange(dwVnum, lMapIndex, sx, sy, ex, ey, bIsException, bSpawnMotion, bAggressive);

	if (ch && bLevel > 0)
	{
		if (ch->IsZodiacBoss())
		{
			int New_HP = ch->GetMaxHP()-((135-bLevel)*3000);
			ch->SetMaxHP(New_HP);
			ch->SetHP(New_HP);
		}

		ch->SetLevel(bLevel);
		ch->UpdatePacket();
	}

	return ch;
}

bool CHARACTER_MANAGER::SpawnGroupGroupZodiac(DWORD dwVnum, long lMapIndex, int sx, int sy, int ex, int ey, LPREGEN pkRegen, bool bAggressive_, LPZODIAC pZodiac, BYTE bLevel)
{
	const DWORD dwGroupID = CMobManager::Instance().GetGroupFromGroupGroup(dwVnum);

	if( dwGroupID != 0 )
	{
		return SpawnGroupZodiac(dwGroupID, lMapIndex, sx, sy, ex, ey, pkRegen, bAggressive_, pZodiac, bLevel);
	}
	else
	{
		sys_err( "NOT_EXIST_GROUP_GROUP_VNUM(%u) MAP(%ld)", dwVnum, lMapIndex );
		return false;
	}
}

LPCHARACTER CHARACTER_MANAGER::SpawnGroupZodiac(DWORD dwVnum, long lMapIndex, int sx, int sy, int ex, int ey, LPREGEN pkRegen, bool bAggressive_, LPZODIAC pZodiac, BYTE bLevel)
{
	CMobGroup * pkGroup = CMobManager::Instance().GetGroup(dwVnum);

	if (!pkGroup)
	{
		sys_err("NOT_EXIST_GROUP_VNUM(%u) Map(%u) ", dwVnum, lMapIndex);
		return NULL;
	}

	LPCHARACTER pkChrMaster = NULL;
	LPPARTY pkParty = NULL;

	const std::vector<DWORD> & c_rdwMembers = pkGroup->GetMemberVector();

	bool bSpawnedByStone = false;
	bool bAggressive = bAggressive_;

	if (m_pkChrSelectedStone)
	{
		bSpawnedByStone = true;

		if (m_pkChrSelectedStone->GetZodiac())
			bAggressive = true;
	}

	LPCHARACTER chLeader = NULL;

	for (DWORD i = 0; i < c_rdwMembers.size(); ++i)
	{
		LPCHARACTER tch = SpawnMobRange(c_rdwMembers[i], lMapIndex, sx, sy, ex, ey, true, bSpawnedByStone, false, bLevel);

		if (!tch)
		{
			if (i == 0)	// 못만든 몬스터가 대장일 경우에는 그냥 실패
				return NULL;

			continue;
		}

		if (i == 0)
			chLeader = tch;

		tch->SetZodiac(pZodiac);

		sx = tch->GetX() - number(300, 500);
		sy = tch->GetY() - number(300, 500);
		ex = tch->GetX() + number(300, 500);
		ey = tch->GetY() + number(300, 500);

		if (m_pkChrSelectedStone)
			tch->SetStone(m_pkChrSelectedStone);
		else if (pkParty)
		{
			pkParty->Join(tch->GetVID());
			pkParty->Link(tch);
		}
		else if (!pkChrMaster)
		{
			pkChrMaster = tch;
			pkChrMaster->SetRegen(pkRegen);

			pkParty = CPartyManager::instance().CreateParty(pkChrMaster);
		}

		if (bAggressive)
			tch->SetAggressive();
	}

	return chLeader;
}

// ---- CQuestManager
namespace quest
{
	LPZODIAC CQuestManager::GetCurrentZodiac()
	{
		LPCHARACTER ch = GetCurrentCharacterPtr();

		if (!ch)
		{
			if (m_pSelectedZodiac)
				return m_pSelectedZodiac;

			return NULL;
		}

		return ch->GetZodiacForce();
	}

	void CQuestManager::SelectZodiac(LPZODIAC pZodiac)
	{
		m_pSelectedZodiac = pZodiac;
	}

}

// ---- polecenia
ACMD(do_cz_check_box)
{
	const char *line;
	char arg1[256], arg2[256];
	line = two_arguments (argument, arg1, sizeof(arg1), arg2, sizeof(arg2));

	if (0 == arg1[0] || 0 == arg2[0])
		return;

	int color = atoi(arg1);
	int index = atoi(arg2);

	if (color < 0 || color > 1)
		return;

	if (index < 0 || index > 29)
		return;

	ch->ZTT_CHECK_BOX(color,index);
	ch->ZTT_LOAD_INFO();

}

ACMD(do_cz_reward)
{
	char arg1[256];
	one_argument (argument, arg1, sizeof(arg1));

	if (0 == arg1[0])
		return;

	int type = atoi(arg1);

	if(type < 1 || type > 3)
		return;

	ch->ZTT_REWARD(type);
}

ACMD(do_revivedialog)
{
	if (!ch)
		return;

	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));

	if (!*arg1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Missing data. Please, contact an administrator."));
		return;
	}

	DWORD vid = 0;
	str_to_number(vid, arg1);
	LPCHARACTER tch = CHARACTER_MANAGER::instance().Find(vid);

	if (!tch)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("There is no one to resuscitate."));
		return;
	}

	if (!tch->IsPC())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("The person you are trying to revive is not human."));
		return;
	}

	if (!tch->IsDead())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You can not resurrect someone who is alive."));
		return;
	}

	BYTE bNeedPrism;
	if (tch->GetQuestFlag("12zi_temple.IsDead") == 1 || tch->GetQuestFlag("12zi_temple.PrismNeed") > 0)
	{
		if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 1)
			bNeedPrism = 1;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 2)
			bNeedPrism = 2;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 3)
			bNeedPrism = 4;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 4)
			bNeedPrism = 8;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") >= 5)
			bNeedPrism = 10;
		else
			bNeedPrism = tch->GetQuestFlag("12zi_temple.PrismNeed");
	}
	else
	{
		if (tch->GetDeadCount() == 3)
			bNeedPrism = 4;
		else if (tch->GetDeadCount() == 4)
			bNeedPrism = 8;
		else if (tch->GetDeadCount() >= 5)
			bNeedPrism = 10;
		else
			bNeedPrism = tch->GetDeadCount();
	}

	ch->ChatPacket(CHAT_TYPE_COMMAND, "OpenReviveDialog %u %u", (DWORD)tch->GetVID(), bNeedPrism);
}

ACMD(do_revive)
{
	if (!ch)
		return;

	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));

	if (!*arg1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Missing data. Please, contact an administrator."));
		return;
	}

	DWORD vid = 0;
	str_to_number(vid, arg1);
	LPCHARACTER tch = CHARACTER_MANAGER::instance().Find(vid);

	if (!tch)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("There is no one to resuscitate."));
		return;
	}

	if (!tch->IsPC())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("The person you are trying to revive is not human."));
		return;
	}

	if (!tch->IsDead())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You can not resurrect someone who is alive."));
		return;
	}

	if (!(ch->GetMapIndex() >= 3580000 && ch->GetMapIndex() < 3590000) || !(tch->GetMapIndex() >= 3580000 && tch->GetMapIndex() < 3590000))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("This action can only be done in the Zodiac Temple."));
		return;
	}

	BYTE bNeedPrism;
	if (tch->GetQuestFlag("12zi_temple.IsDead") == 1 || tch->GetQuestFlag("12zi_temple.PrismNeed") > 0)
	{
		if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 1)
			bNeedPrism = 1;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 2)
			bNeedPrism = 2;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 3)
			bNeedPrism = 4;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") == 4)
			bNeedPrism = 8;
		else if (tch->GetQuestFlag("12zi_temple.PrismNeed") >= 5)
			bNeedPrism = 10;
		else
			bNeedPrism = tch->GetQuestFlag("12zi_temple.PrismNeed");
	}
	else
	{
		if (tch->GetDeadCount() == 3)
			bNeedPrism = 4;
		else if (tch->GetDeadCount() == 4)
			bNeedPrism = 8;
		else if (tch->GetDeadCount() >= 5)
			bNeedPrism = 10;
		else
			bNeedPrism = tch->GetDeadCount();
	}

	int iPrismCount = (ch->CountSpecifyItem(33025) + ch->CountSpecifyItem(33032));
	if (iPrismCount < (int)bNeedPrism)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "NotEnoughPrism %u", bNeedPrism);
		return;
	}

	int iDelPrism = bNeedPrism-ch->CountSpecifyItem(33032);
	if (iDelPrism <= 0)
	{
		ch->RemoveSpecifyItem(33032, bNeedPrism);
	}
	else
	{
		ch->RemoveSpecifyItem(33025, bNeedPrism-ch->CountSpecifyItem(33032));
		ch->RemoveSpecifyItem(33032, ch->CountSpecifyItem(33032));
	}

	tch->ChatPacket(CHAT_TYPE_COMMAND, "CloseRestartWindow");
	tch->GetDesc()->SetPhase(PHASE_GAME);
	tch->SetPosition(POS_STANDING);
	tch->StartRecoveryEvent();
	tch->RestartAtSamePos();
	tch->PointChange(POINT_HP, tch->GetMaxHP() - tch->GetHP());
	tch->PointChange(POINT_SP, tch->GetMaxSP() - tch->GetSP());
	tch->ReviveInvisible(5);
	tch->SetQuestFlag("12zi_temple.IsDead", 0);
	sys_log(0, "do_restart: restart here zodiac");
}

ACMD(do_jump_floor)
{
	if (ch)
	{
		if ((ch->GetParty() && ch->GetParty()->GetLeaderPID() == ch->GetPlayerID()) || !ch->GetParty())
		{
			LPZODIAC pkZodiac = CZodiacManager::instance().FindByMapIndex(ch->GetMapIndex());
			if (pkZodiac && pkZodiac->IsNextFloor() == true)
			{
				pkZodiac->NewFloor(pkZodiac->GetNextFloor());
			}
		}
	}
}

ACMD(do_next_floor)
{
	if (ch)
	{
		if ((ch->GetParty() && ch->GetParty()->GetLeaderPID() == ch->GetPlayerID()) || !ch->GetParty())
		{
			LPZODIAC pkZodiac = CZodiacManager::instance().FindByMapIndex(ch->GetMapIndex());
			if (pkZodiac && pkZodiac->IsNextFloor() == true)
			{
				pkZodiac->NewFloor(pkZodiac->GetFloor()+1);
			}
		}
	}
}

ACMD(do_cz_complete_reward)
{
	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));
	if (!*arg1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: cz_complete_reward <color>");
		ch->ChatPacket(CHAT_TYPE_INFO, "List of the available colors:");
		ch->ChatPacket(CHAT_TYPE_INFO, " yellow");
		ch->ChatPacket(CHAT_TYPE_INFO, " green");
		ch->ChatPacket(CHAT_TYPE_INFO, " all");
		return;
	}

	std::string strArg(arg1);
	if (!strArg.compare(0, 6, "yellow"))
	{
		if (ch->IsGM())
		{
			ch->SetQuestFlag("12zi_temple.zt_color_0", 1073741823);
			ch->ZTT_CHECK_REWARD();
			ch->ZTT_LOAD_INFO();
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Only GM have access to this command"));
	}
	else if (!strArg.compare(0, 5, "green"))
	{
		if (ch->IsGM())
		{
			ch->SetQuestFlag("12zi_temple.zt_color_1", 1073741823);
			ch->ZTT_CHECK_REWARD();
			ch->ZTT_LOAD_INFO();
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Only GM have access to this command"));
	}
	else if (!strArg.compare(0, 3, "all"))
	{
		if (ch->IsGM())
		{
			ch->SetQuestFlag("12zi_temple.zt_color_0", 1073741823);
			ch->SetQuestFlag("12zi_temple.zt_color_1", 1073741823);
			ch->ZTT_CHECK_REWARD();
			ch->ZTT_LOAD_INFO();
		}
		else
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Only GM have access to this command"));
	}
}

#endif // ENABLE_12ZI
