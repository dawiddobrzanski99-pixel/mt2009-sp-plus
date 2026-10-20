// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
#include "stdafx.h"
#include "questlua.h"
#include "questmanager.h"
#include "playerbot_zodiac_temple.h"
#include "war_map.h"
#include "char.h"

#include "../../common/CommonDefines.h"

#ifdef ENABLE_12ZI

#undef sys_err
#ifndef __WIN32__
#define sys_err(fmt, args...) quest::CQuestManager::instance().QuestError(__FUNCTION__, __LINE__, fmt, ##args)
#else
#define sys_err(fmt, ...) quest::CQuestManager::instance().QuestError(__FUNCTION__, __LINE__, fmt, __VA_ARGS__)
#endif

namespace quest
{
	int zodiac_temple_starttemple(lua_State* L)
	{
		if (!lua_isnumber(L, 1))
		{
			sys_err("wrong argument");
			return 0;
		}

		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch)
			return 0;

		CZodiacManager::instance().StartTemple(ch, (BYTE)lua_tonumber(L, 1));
		return 0;
	}

	int zodiac_temple_new_floor(lua_State* L)
	{
		if (!lua_isnumber(L, 1))
		{
			sys_err("wrong argument");
			return 0;
		}

		quest::CQuestManager& q = quest::CQuestManager::instance();
		LPZODIAC pZodiac = q.GetCurrentZodiac();
		if (!pZodiac)
			return 0;

		BYTE Floor = (BYTE)lua_tonumber(L, 1);
		pZodiac->NewFloor(Floor);
		return 0;
	}

	int zodiac_temple_setflag(lua_State* L)
	{
		if (!lua_isstring(L,1) || !lua_isnumber(L,2))
		{
			sys_err("wrong set flag");
		}
		else
		{
			CQuestManager& q = CQuestManager::instance();
			LPZODIAC pZodiac = q.GetCurrentZodiac();

			if (pZodiac)
			{
				const char* sz = lua_tostring(L,1);
				int value = int(lua_tonumber(L, 2));
				pZodiac->SetFlag(sz, value);
			}
			else
			{
				sys_err("no zodiac !!!");
			}
		}
		return 0;
	}

	int zodiac_temple_getflag(lua_State* L)
	{
		if (!lua_isstring(L,1))
		{
			sys_err("wrong get flag");
		}

		CQuestManager& q = CQuestManager::instance();
		LPZODIAC pZodiac = q.GetCurrentZodiac();

		if (pZodiac)
		{
			const char* sz = lua_tostring(L,1);
			lua_pushnumber(L, pZodiac->GetFlag(sz));
		}
		else
		{
			sys_err("no zodiac !!!");
			lua_pushnumber(L, 0);
		}

		return 1;
	}

	// --- funkcje dopisane do tabel dungeon / game / pc (AppendLuaFunctionTable)
	// int dungeon_zodiac_clear (lua_State* L)
	ALUA(dungeon_zodiac_clear)
	{
		CQuestManager& q = CQuestManager::instance();
		LPDUNGEON pDungeon = q.GetCurrentDungeon();

		if (pDungeon)
			pDungeon->ZodiacMessageClear();

		return 0;
	}

	// int dungeon_zodiac_notice (lua_State* L)
	ALUA(dungeon_zodiac_notice)
	{
		if (!lua_isstring(L, 1))
			return 0;

		CQuestManager& q = CQuestManager::instance();
		LPDUNGEON pDungeon = q.GetCurrentDungeon();

		if (pDungeon)
			pDungeon->ZodiacMessage(lua_tostring(L, 1));

		return 0;
	}

	// int dungeon_zodiac_time (lua_State* L)
	ALUA(dungeon_zodiac_time)
	{
		if (!lua_isnumber(L,1) || !lua_isnumber(L,2) || !lua_isnumber(L,3))
			return 0;

		BYTE current = (BYTE)lua_tonumber(L, 1);
		BYTE next = (BYTE)lua_tonumber(L, 2);
		int time = (int)lua_tonumber(L, 3);

		CQuestManager& q = CQuestManager::instance();
		LPDUNGEON pDungeon = q.GetCurrentDungeon();

		if (pDungeon)
			pDungeon->ZodiacTime(current, next, time);

		return 0;
	}

	// int dungeon_zodiac_time_clear (lua_State* L)
	ALUA(dungeon_zodiac_time_clear)
	{
		CQuestManager& q = CQuestManager::instance();
		LPDUNGEON pDungeon = q.GetCurrentDungeon();

		if (pDungeon)
			pDungeon->ZodiacTimeClear();

		return 0;
	}

	// int game_open_zodiac_temple_table(lua_State*)
	ALUA(game_open_zodiac_temple_table)
	{
		CQuestManager& q = CQuestManager::instance();
		LPCHARACTER ch = q.GetCurrentCharacterPtr();
		ch->ZTT_LOAD_INFO();
		return 0;
	}

	// int pc_set_animasphere(lua_State * L)
	ALUA(pc_set_animasphere)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch)
			return 0;

		if (!lua_isnumber(L,1))
		{
			lua_pushnumber(L, 0);
			return 1;
		}

		int animasphere = (int)lua_tonumber(L, 1);
		ch->SetAnimaSphere(animasphere);
		lua_pushnumber(L, animasphere);
		return 1;
	}

	// int pc_get_animasphere(lua_State * L)
	ALUA(pc_get_animasphere)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch)
			return 0;

		lua_pushnumber(L, ch->GetAnimaSphere());
		return 1;
	}

	// int pc_delete_animasphere(lua_State * L)
	ALUA(pc_delete_animasphere)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch)
			return 0;

		if (ch->GetAnimaSphere() < 12)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You haven't enough animasphere."));
			return 0;
		}

		ch->SetAnimaSphere(-12);
		return 1;
	}

	// int pc_if_cz_unlimit_enter(lua_State * L)
	ALUA(pc_if_cz_unlimit_enter)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushboolean(L, ch->IsAffectFlag(AFF_CZ_UNLIMIT_ENTER));
		return 1;
	}

	// int pc_sf_cz_unlimit_enter(lua_State * L)
	ALUA(pc_sf_cz_unlimit_enter)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if(lua_toboolean(L, 1))
			ch->AddAffect(AFFECT_CZ_UNLIMIT_ENTER, 0, 0, AFF_CZ_UNLIMIT_ENTER, 10800, 0, 1, 0);
		else
			ch->RemoveAffect(AFFECT_CZ_UNLIMIT_ENTER);
		return 0;
	}

	void RegisterZodiacTempleFunctionTable()
	{
		luaL_reg zodiac_dungeon_functions[] =
		{
			{ "zodiac_notice_clear",	dungeon_zodiac_clear },
			{ "zodiac_notice",	dungeon_zodiac_notice },
			{ "zodiac_time",	dungeon_zodiac_time },
			{ "zodiac_time_clear",	dungeon_zodiac_time_clear },
			{ NULL, NULL }
		};
		CQuestManager::instance().AppendLuaFunctionTable("d", zodiac_dungeon_functions);
		luaL_reg zodiac_game_functions[] =
		{
			{ "zodiac_temple_table",	game_open_zodiac_temple_table },
			{ NULL, NULL }
		};
		CQuestManager::instance().AppendLuaFunctionTable("game", zodiac_game_functions);
		luaL_reg zodiac_pc_functions[] =
		{
			{ "set_animasphere",	pc_set_animasphere },
			{ "get_animasphere",	pc_get_animasphere },
			{ "delete_animasphere",	pc_delete_animasphere },
			{ "is_flag_cz_ulimit_enter",	pc_if_cz_unlimit_enter },
			{ "set_flag_cz_ulimit_enter",	pc_sf_cz_unlimit_enter },
			{ NULL, NULL }
		};
		CQuestManager::instance().AppendLuaFunctionTable("pc", zodiac_pc_functions);

		luaL_reg zodiac_temple_functions[] =
		{
			{"starttemple", zodiac_temple_starttemple},
			{"new_floor", zodiac_temple_new_floor},
			{"setflag", zodiac_temple_setflag},
			{"getflag", zodiac_temple_getflag},

			{NULL, NULL}
		};

		CQuestManager::instance().AddLuaFunctionTable("zodiac_temple", zodiac_temple_functions);
	}
}
#endif // ENABLE_12ZI
