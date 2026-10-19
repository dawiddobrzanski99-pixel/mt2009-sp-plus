// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
#include "stdafx.h"
#include "utils.h"
#include "config.h"
#include "desc.h"
#include "desc_manager.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "mob_manager.h"
#include "battle.h"
#include "pvp.h"
#include "skill.h"
#include "start_position.h"
#include "profiler.h"
#include "cmd.h"
#include "dungeon.h"
#include "log.h"
#include "unique_item.h"
#include "priv_manager.h"
#include "db.h"
#include "vector.h"
#include "marriage.h"
#include "arena.h"
#include "regen.h"
#include "monarch.h"
#include "exchange.h"
#include "shop_manager.h"
#include "castle.h"
#include "ani.h"
#include "packet.h"
#include "party.h"
#include "affect.h"
#include "guild.h"
#include "guild_manager.h"
#include "questmanager.h"
#include "questlua.h"
#include "threeway_war.h"
#include "BlueDragon.h"
#include "DragonLair.h"
#include "war_map.h"
#include "playerbot_zodiac_temple.h"

#include "../../common/CommonDefines.h"

#ifdef ENABLE_12ZI


DWORD SKILL_VNUM = 270;

BYTE SKILL_LEVEL(BYTE Level)
{
	if (Level >= 40 && Level < 50)
		return 15;
	if (Level >= 50 && Level < 60)
		return 15;
	else if (Level >= 60 && Level < 70)
		return 20;
	else if (Level >= 70 && Level < 80)
		return 25;
	else if (Level >= 80 && Level < 90)
		return 30;
	else if (Level >= 90 && Level < 100)
		return 30;
	else if (Level >= 100 && Level < 137)
		return 30;
	else
		return 20;
}

bool PolyDog(DWORD Vnum)
{
	/*
	Chen & Wei (stun)
	Yu (reduces atk value)
	the other polymorphs in stone
	*/
	// Guardian, General
	if (Vnum == 2751 || Vnum == 2752 || // Zi
		Vnum == 2781 || Vnum == 2782 || // Mao
		Vnum == 2851 || Vnum == 2852 || // Xu
		Vnum == 2861 || Vnum == 2862)   // Hai
		return true;

	return false;
}

bool CHARACTER::IsZodiacBoss()
{
	if (!IsMonster())
		return false;

	if (GetRaceNum() >= 2750 && GetRaceNum() <= 2862) // Zi Officer ~ Hai General
		return true;

	return false;
}

bool CHARACTER::IsZodiacOfficer()
{
	if (!IsMonster())
		return false;

	if (GetRaceNum() == 2750 || // Zi Officer
		GetRaceNum() == 2760 || // Chou Officer
		GetRaceNum() == 2770 || // Yin Officer
		GetRaceNum() == 2780 || // Mao Officer
		GetRaceNum() == 2790 || // Chen Officer
		GetRaceNum() == 2800 || // Si Officer
		GetRaceNum() == 2810 || // Wu Officer
		GetRaceNum() == 2820 || // Wei Officer
		GetRaceNum() == 2830 || // Shen Officer
		GetRaceNum() == 2840 || // Yu Officer
		GetRaceNum() == 2850 || // Xu Officer
		GetRaceNum() == 2860)   // Hai Officer
		return true;

	return false;
}

bool CHARACTER::IsZodiacStatue()
{
	if (!IsStone())
		return false;

	if (GetRaceNum() >= 20452 && GetRaceNum() <= 20463) // Zi Statue ~ Hai Statue
		return true;

	return false;
}

WORD CHARACTER::GetStatueVnum() const
{
	if (!IsMonster())
	{
		sys_err("char_battle_zodiac.cpp :: GetStatueVnum: Mob not exist!");
		return 0;
	}

	WORD Vnum = GetRaceNum();
	if (Vnum >= 2750 && Vnum <= 2752) // Zi
		return 20452;
	else if (Vnum >= 2760 && Vnum <= 2762) // Chou
		return 20453;
	else if (Vnum >= 2770 && Vnum <= 2772) // Yin
		return 20454;
	else if (Vnum >= 2780 && Vnum <= 2782) // Mao
		return 20455;
	else if (Vnum >= 2790 && Vnum <= 2792) // Chen
		return 20456;
	else if (Vnum >= 2800 && Vnum <= 2802) // Si
		return 20457;
	else if (Vnum >= 2810 && Vnum <= 2812) // Wu
		return 20458;
	else if (Vnum >= 2820 && Vnum <= 2822) // Wei
		return 20459;
	else if (Vnum >= 2830 && Vnum <= 2832) // Shen
		return 20460;
	else if (Vnum >= 2840 && Vnum <= 2842) // Yu
		return 20461;
	else if (Vnum >= 2850 && Vnum <= 2852) // Xu
		return 20462;
	else if (Vnum >= 2860 && Vnum <= 2862) // Hai
		return 20463;

	return 0;
}

struct FAttackSkill1
{
	LPCHARACTER tch;
	FAttackSkill1(LPCHARACTER c) : tch(c) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 1: No exist CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(ch->GetX() - tch->GetX(), ch->GetY() - tch->GetY()) <= 1000)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_1_info)
{
	LPCHARACTER Mob;
	zodiac_skill_1_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_1_event)
{
	zodiac_skill_1_info* info = dynamic_cast<zodiac_skill_1_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_1_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_1_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_1_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill1 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		FAttackSkill1 f(Mob);
		pkMap->for_each(f);
	}

	return 0;
}

struct FAttackSkill2
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill2(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 2: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 400)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!ch->IsPolymorphed() && !tch->IsZodiacOfficer())
					{
						DWORD GetPolyNum = PolyDog(tch->GetRaceNum()) == false ? tch->GetStatueVnum() : 101;
						ch->SetPolymorph(GetPolyNum, false);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_2_info)
{
	LPCHARACTER Mob;
	zodiac_skill_2_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_2_event)
{
	zodiac_skill_2_info* info = dynamic_cast<zodiac_skill_2_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_2_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_2_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_2_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill2 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill2 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill2 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 1300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill2 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 1800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill2 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}
	}

	return 0;
}


struct FAttackSkill3
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill3(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 3: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 490)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!ch->IsPolymorphed() && !tch->IsZodiacOfficer())
					{
						DWORD GetPolyNum = PolyDog(tch->GetRaceNum()) == false ? tch->GetStatueVnum() : 101;
						ch->SetPolymorph(GetPolyNum, false);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_3_info)
{
	LPCHARACTER Mob;
	int EffectType;
	int EffectX1, EffectX2, EffectX3;
	int EffectY1, EffectY2, EffectY3;
	int DamageX1, DamageX2, DamageX3;
	int DamageY1, DamageY2, DamageY3;

	zodiac_skill_3_info()
	: Mob(NULL), EffectType(0), 
		EffectX1(0), EffectX2(0), EffectX3(0), 
		EffectY1(0), EffectY2(0), EffectY3(0),
		DamageX1(0), DamageX2(0), DamageX3(0), 
		DamageY1(0), DamageY2(0), DamageY3(0) 
	{}
};

EVENTFUNC(zodiac_skill_3_event)
{
	zodiac_skill_3_info* info = dynamic_cast<zodiac_skill_3_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_3_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_3_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_3_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill3 = NULL;

	{
		LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());

		{
			Mob->EffectZodiacPacket(info->EffectX1, info->EffectY1, info->EffectType);

			if (pkMap)
			{
				FAttackSkill3 f(Mob, info->DamageX1, info->DamageY1);
				pkMap->for_each(f);
			}
		}

		{
			Mob->EffectZodiacPacket(info->EffectX2, info->EffectY2, info->EffectType);

			if (pkMap)
			{
				FAttackSkill3 f(Mob, info->DamageX2, info->DamageY2);
				pkMap->for_each(f);
			}
		}

		{
			Mob->EffectZodiacPacket(info->EffectX3, info->EffectY3, info->EffectType);

			if (pkMap)
			{
				FAttackSkill3 f(Mob, info->DamageX3, info->DamageY3);
				pkMap->for_each(f);
			}
		}
	}

	return 0;
}


struct FAttackSkill4
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill4(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 4: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 490)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (tch->GetRaceNum() >= 2750 && tch->GetRaceNum() <= 2752) //Zi
					{
						DWORD dwCurTime = get_dword_time();
						tch->SendMovePacket(FUNC_MOB_SKILL, 4, ch->GetX(), ch->GetY(), 0, dwCurTime);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_4_info)
{
	LPCHARACTER Mob;
	int EffectX, EffectY;
	zodiac_skill_4_info() : Mob(NULL), EffectX(0), EffectY(0) {}
};

EVENTFUNC(zodiac_skill_4_event)
{
	zodiac_skill_4_info* info = dynamic_cast<zodiac_skill_4_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_4_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_4_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_4_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill4 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		FAttackSkill4 f(Mob, info->EffectX, info->EffectY);
		pkMap->for_each(f);
	}

	return 0;
}


struct FAttackSkill5
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill5(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 5: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 400)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!ch->IsPolymorphed() && !tch->IsZodiacOfficer())
					{
						DWORD GetPolyNum = PolyDog(tch->GetRaceNum()) == false ? tch->GetStatueVnum() : 101;
						ch->SetPolymorph(GetPolyNum, false);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_5_info)
{
	LPCHARACTER Mob;
	zodiac_skill_5_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_5_event)
{
	zodiac_skill_5_info* info = dynamic_cast<zodiac_skill_5_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_5_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_5_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_5_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill5 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill5 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill5 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 1300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill5 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 1800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill5 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}
	}

	return 0;
}


struct FAttackSkill6
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill6(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 6: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 400)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!ch->IsPolymorphed() && !tch->IsZodiacOfficer())
					{
						DWORD GetPolyNum = PolyDog(tch->GetRaceNum()) == false ? tch->GetStatueVnum() : 101;
						ch->SetPolymorph(GetPolyNum, false);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_6_info)
{
	LPCHARACTER Mob;
	zodiac_skill_6_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_6_event)
{
	zodiac_skill_6_info* info = dynamic_cast<zodiac_skill_6_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_6_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_6_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_6_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill6 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill6 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill6 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 1300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill6 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}
	}

	return 0;
}


struct FAttackSkill7
{
	LPCHARACTER tch;
	FAttackSkill7(LPCHARACTER c) : tch(c) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 7: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(ch->GetX() - tch->GetX(), ch->GetY() - tch->GetY()) <= 1000)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_7_info)
{
	LPCHARACTER Mob;
	zodiac_skill_7_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_7_event)
{
	zodiac_skill_7_info* info = dynamic_cast<zodiac_skill_7_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_7_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_7_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_7_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill7 = NULL;

	LPZODIAC pZodiac = CZodiacManager::instance().FindByMapIndex(Mob->GetMapIndex());
	if (pZodiac)
	{
		pZodiac->PolyCharacter(Mob);
	}

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		FAttackSkill7 f(Mob);
		pkMap->for_each(f);
	}

	return 0;
}


struct FAttackSkill8
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill8(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 8: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 400)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!ch->IsPolymorphed() && !tch->IsZodiacOfficer())
					{
						DWORD GetPolyNum = PolyDog(tch->GetRaceNum()) == false ? tch->GetStatueVnum() : 101;
						ch->SetPolymorph(GetPolyNum, false);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_8_info)
{
	LPCHARACTER Mob;
	zodiac_skill_8_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_8_event)
{
	zodiac_skill_8_info* info = dynamic_cast<zodiac_skill_8_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_8_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_8_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_8_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill8 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill8 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill8 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 1300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill8 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}
	}

	return 0;
}


struct FAttackSkill9
{
	LPCHARACTER tch;
	long Mob_X, Mob_Y;
	FAttackSkill9(LPCHARACTER c, long x, long y) : tch(c), Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 9: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(Mob_X - ch->GetX(), Mob_Y - ch->GetY()) <= 400)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!ch->IsPolymorphed() && !tch->IsZodiacOfficer())
					{
						DWORD GetPolyNum = PolyDog(tch->GetRaceNum()) == false ? tch->GetStatueVnum() : 101;
						ch->SetPolymorph(GetPolyNum, false);
					}
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_9_info)
{
	LPCHARACTER Mob;
	zodiac_skill_9_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_9_event)
{
	zodiac_skill_9_info* info = dynamic_cast<zodiac_skill_9_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_9_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_9_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_9_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill9 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 300, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill9 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}

		{
			float fx, fy;
			GetDeltaByDegree(Mob->GetRotation(), 800, &fx, &fy);

			PIXEL_POSITION pos = Mob->GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			FAttackSkill9 f(Mob, pos.x, pos.y);
			pkMap->for_each(f);
		}
	}

	return 0;
}


struct FAttackSkill10
{
	LPCHARACTER tch;
	FAttackSkill10(LPCHARACTER c) : tch(c) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch || !tch)
			{
				sys_err("Skill 10: No existe CH o TCH!");
				return;
			}

			if (ch->IsPC() && !ch->IsDead())
			{
				if (DISTANCE_APPROX(ch->GetX() - tch->GetX(), ch->GetY() - tch->GetY()) <= 1000)
				{
					BYTE chance = number(0, 5) == 3 ? 1 : 0;
					tch->ZodiacSkillAttack(ch, SKILL_VNUM+chance, SKILL_LEVEL(tch->GetLevel()));

					if (!tch->IsZodiacOfficer())
						ch->AddAffect(AFFECT_STUN, POINT_NONE, 0, AFF_STUN, 5, 0, true);
				}
			}
		}
	}
};

EVENTINFO(zodiac_skill_10_info)
{
	LPCHARACTER Mob;
	zodiac_skill_10_info() : Mob(NULL) {}
};

EVENTFUNC(zodiac_skill_10_event)
{
	zodiac_skill_10_info* info = dynamic_cast<zodiac_skill_10_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_10_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	if (Mob == NULL)
	{
		sys_err("zodiac_skill_10_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_10_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill10 = NULL;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(Mob->GetMapIndex());
	if (pkMap)
	{
		FAttackSkill10 f(Mob);
		pkMap->for_each(f);
	}

	return 0;
}


EVENTINFO(zodiac_skill_11_info)
{
	LPCHARACTER Mob;
	LPCHARACTER Character;
	zodiac_skill_11_info() : Mob(NULL), Character(NULL) {}
};

EVENTFUNC(zodiac_skill_11_event)
{
	zodiac_skill_11_info* info = dynamic_cast<zodiac_skill_11_info*>(event->info);
	if (info == NULL)
	{
		sys_err( "zodiac_skill_11_event> <Factor> Null pointer" );
		return 0;
	}

	LPCHARACTER Mob = info->Mob;
	LPCHARACTER Character = info->Character;
	if (Mob == NULL || Character == NULL)
	{
		sys_err("zodiac_skill_11_event> Cannot Mob");
		return 0;
	}

	if (!Mob->IsMonster() && !Mob->IsStone() && !Mob->IsZodiacBoss())
	{
		sys_err("zodiac_skill_11_event> Is cannot Monster or Stone");
		return 0;
	}

	Mob->m_pkZodiacSkill11 = NULL;

	BYTE chance = number(0, 5) == 3 ? 1 : 0;
	Mob->ZodiacSkillAttack(Character, SKILL_VNUM+chance, SKILL_LEVEL(Mob->GetLevel()));
	return 0;
}


void CHARACTER::ZodiacDamage(BYTE Type, LPCHARACTER Victim)
{
	if (!IsZodiacBoss())
	{
		sys_err("Not zodiac boss! RaceNum::[%u]", GetRaceNum());
		return;
	}

	DWORD dwCurTime = get_dword_time();
	SendMovePacket(FUNC_MOB_SKILL, Type, GetX(), GetY(), 0, dwCurTime);

	/*
		Chou, Yin, Si, Wu, Shen		= PolyStatue
		Zi, Mao, Xu, Hai			= PolyDog
		Chen, Wei					= Stun
		Yu							= atk-
	*/


	if (GetRaceNum() >= 2750 && GetRaceNum() <= 2752) // Zi
	{
		if (Type == 0)
			Type = 3;
		else if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 6;
	}
	else if (GetRaceNum() >= 2760 && GetRaceNum() <= 2762) // Chou
	{
		if (Type == 0)
			Type = 4;
		else if (Type == 1)
			Type = 3;
		else if (Type == 2)
			Type = 0;
	}
	else if (GetRaceNum() >= 2770 && GetRaceNum() <= 2772) // Yin
	{
		if (Type == 0)
			Type = 5;
		else if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 2;
	}
	else if (GetRaceNum() >= 2780 && GetRaceNum() <= 2782) // Mao
	{
		if (Type == 0)
			Type = 7;
		else if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 8;
	}
	else if (GetRaceNum() >= 2790 && GetRaceNum() <= 2792) // Chen
	{
		if (Type == 0)
			Type = 4;
		else if (Type == 1)
			Type = 2;
		else if (Type == 2)
			Type = 9;
	}
	else if (GetRaceNum() >= 2800 && GetRaceNum() <= 2802) // Si
	{
		if (Type == 0)
			Type = 10;
		if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 2;
	}
	else if (GetRaceNum() >= 2810 && GetRaceNum() <= 2812) // Wu
	{
		if (Type == 0)
			Type = 5;
		else if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 2;
	}
	else if (GetRaceNum() >= 2820 && GetRaceNum() <= 2822) // Wei
	{
		if (Type == 0)
			Type = 8;
		else if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 9;
	}
	else if (GetRaceNum() >= 2830 && GetRaceNum() <= 2832) // Shen
	{
		if (Type == 0)
			Type = 0;
		else if (Type == 1)
			Type = 1;
		else if (Type == 2)
			Type = 2;
	}
	else if (GetRaceNum() >= 2840 && GetRaceNum() <= 2842) // Yu
	{
		if (Type == 0)
			Type = 8;
		else if (Type == 1)
			Type = 0;
		else if (Type == 2)
			Type = 2;
	}
	else if (GetRaceNum() >= 2850 && GetRaceNum() <= 2852) // Xu
	{
		if (Type == 0)
			Type = 5;
		else if (Type == 1)
			Type = 3;
		else if (Type == 2)
			Type = 0;
	}
	else if (GetRaceNum() >= 2860 && GetRaceNum() <= 2862) // Hai
	{
		if (Type == 0)
			Type = 0;
		else if (Type == 1)
			Type = 3;
		else if (Type == 2)
			Type = 9;
	}

	if (Type == 0) //SKILL
	{
		long x_amk = GetX();
		long y_amk = GetY();

		x_amk /= 100;
		y_amk /= 100;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			x_amk -= p.x / 100;
			y_amk -= p.y / 100;
		}

		x_amk *= 100;
		y_amk *= 100;

		EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE);

		if (m_pkZodiacSkill1)
		{
			event_cancel(&m_pkZodiacSkill1);
		}

		zodiac_skill_1_info * Info = AllocEventInfo<zodiac_skill_1_info>();
		Info->Mob = this;
		m_pkZodiacSkill1 = event_create(zodiac_skill_1_event, Info, PASSES_PER_SEC(2));
	}
	else if (Type == 1) //POLY
	{
		long XX = 0;
		long YY = 0;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			XX = p.x / 100;
			YY = p.y / 100;
		}

		{
			long x_amk = GetX();
			long y_amk = GetY();

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 600, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 1200, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 1800, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		if (m_pkZodiacSkill2)
		{
			event_cancel(&m_pkZodiacSkill2);
		}

		zodiac_skill_2_info * Info = AllocEventInfo<zodiac_skill_2_info>();
		Info->Mob = this;
		m_pkZodiacSkill2 = event_create(zodiac_skill_2_event, Info, PASSES_PER_SEC(2) - (passes_per_sec / 2));
	}
	else if (Type == 2) //POLY
	{
		if (m_pkZodiacSkill3)
		{
			event_cancel(&m_pkZodiacSkill3);
		}

		zodiac_skill_3_info * Info = AllocEventInfo<zodiac_skill_3_info>();

		Info->Mob = this;

		{
			if (GetRaceNum() >= 2770 && GetRaceNum() <= 2772) // Yin
				Info->EffectType = SE_METEOR;
			else if (GetRaceNum() >= 2790 && GetRaceNum() <= 2792) // Chen
				Info->EffectType = SE_BEAD_RAIN;
			else if (GetRaceNum() >= 2800 && GetRaceNum() <= 2802) // Si
				Info->EffectType = SE_ARROW_RAIN;
			else if (GetRaceNum() >= 2810 && GetRaceNum() <= 2812) // Wu
				Info->EffectType = SE_HORSE_DROP;
			else if (GetRaceNum() >= 2830 && GetRaceNum() <= 2832) // Shen
				Info->EffectType = SE_FALL_ROCK;
			else if (GetRaceNum() >= 2840 && GetRaceNum() <= 2842) // Yu
				Info->EffectType = SE_EGG_DROP;
		}

		long XX = 0;
		long YY = 0;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			XX = p.x / 100;
			YY = p.y / 100;
		}

		int EffectX_1 = 0, EffectX_2 = 0, EffectX_3 = 0;
		int EffectY_1 = 0, EffectY_2 = 0, EffectY_3 = 0;

		EffectX_1 = -(700+number(0, 300));
		EffectY_1 = -(500+number(0, 300));

		EffectX_2 = 0;
		EffectY_2 = (500+number(0, 300));

		EffectX_3 = (700+number(0, 300));
		EffectY_3 = -(500+number(0, 300));

		if (number(0, 2) == 1)
		{
			EffectX_1 *= -1;
			EffectY_1 *= -1;

			EffectX_2 *= -1;
			EffectY_2 *= -1;

			EffectX_3 *= -1;
			EffectY_3 *= -1;
		}

		{
			long x_amk = GetX()+EffectX_1;
			long y_amk = GetY()+EffectY_1;

			Info->DamageX1 = x_amk;
			Info->DamageY1 = y_amk;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			Info->EffectX1 = x_amk;
			Info->EffectY1 = y_amk;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);
		}

		{
			long x_amk = GetX()+EffectX_2;
			long y_amk = GetY()+EffectY_2;

			Info->DamageX2 = x_amk;
			Info->DamageY2 = y_amk;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			Info->EffectX2 = x_amk;
			Info->EffectY2 = y_amk;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);
		}

		{
			long x_amk = GetX()+EffectX_3;
			long y_amk = GetY()+EffectY_3;

			Info->DamageX3 = x_amk;
			Info->DamageY3 = y_amk;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			Info->EffectX3 = x_amk;
			Info->EffectY3 = y_amk;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);
		}

		m_pkZodiacSkill3 = event_create(zodiac_skill_3_event, Info, PASSES_PER_SEC(2));
	}
	else if (Type == 3) //SendMovePacket
	{
		float fx, fy;
		GetDeltaByDegree(GetRotation(), 500, &fx, &fy);

		PIXEL_POSITION pos = GetXYZ();

		pos.x += (long) fx;
		pos.y += (long) fy;

		long x_amk = pos.x;
		long y_amk = pos.y;

		x_amk /= 100;
		y_amk /= 100;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			x_amk -= p.x / 100;
			y_amk -= p.y / 100;
		}

		x_amk *= 100;
		y_amk *= 100;

		EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);

		if (m_pkZodiacSkill4)
		{
			event_cancel(&m_pkZodiacSkill4);
		}

		zodiac_skill_4_info * Info = AllocEventInfo<zodiac_skill_4_info>();
		Info->Mob = this;
		Info->EffectX = x_amk;
		Info->EffectY = y_amk;
		m_pkZodiacSkill4 = event_create(zodiac_skill_4_event, Info, PASSES_PER_SEC(2));
	}
	else if (Type == 4) //POLY
	{
		long XX = 0;
		long YY = 0;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			XX = p.x / 100;
			YY = p.y / 100;
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 200, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 700, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 1200, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 1700, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		if (m_pkZodiacSkill5)
		{
			event_cancel(&m_pkZodiacSkill5);
		}

		zodiac_skill_5_info * Info = AllocEventInfo<zodiac_skill_5_info>();
		Info->Mob = this;
		m_pkZodiacSkill5 = event_create(zodiac_skill_5_event, Info, PASSES_PER_SEC(2) - (passes_per_sec / 2));
	}
	else if (Type == 5) //POLY
	{
		long XX = 0;
		long YY = 0;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			XX = p.x / 100;
			YY = p.y / 100;
		}

		{
			long x_amk = GetX();
			long y_amk = GetY();

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 500, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 1000, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		if (m_pkZodiacSkill6)
		{
			event_cancel(&m_pkZodiacSkill6);
		}

		zodiac_skill_6_info * Info = AllocEventInfo<zodiac_skill_6_info>();
		Info->Mob = this;
		m_pkZodiacSkill6 = event_create(zodiac_skill_6_event, Info, PASSES_PER_SEC(2) - (passes_per_sec / 2));
	}
	else if (Type == 6) //SKILL
	{
		long x_amk = GetX();
		long y_amk = GetY();

		x_amk /= 100;
		y_amk /= 100;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			x_amk -= p.x / 100;
			y_amk -= p.y / 100;
		}

		x_amk *= 100;
		y_amk *= 100;

		EffectZodiacPacket(x_amk, y_amk, SE_SKILL_SAFE_ZONE);

		if (m_pkZodiacSkill7)
		{
			event_cancel(&m_pkZodiacSkill7);
		}

		zodiac_skill_7_info * Info = AllocEventInfo<zodiac_skill_7_info>();
		Info->Mob = this;
		m_pkZodiacSkill7 = event_create(zodiac_skill_7_event, Info, PASSES_PER_SEC(2));
	}
	else if (Type == 7) //POLY
	{
		long XX = 0;
		long YY = 0;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			XX = p.x / 100;
			YY = p.y / 100;
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 200, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_SMALL);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 700, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_MIDDLE);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 1200, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);
		}

		if (m_pkZodiacSkill8)
		{
			event_cancel(&m_pkZodiacSkill8);
		}

		zodiac_skill_8_info * Info = AllocEventInfo<zodiac_skill_8_info>();
		Info->Mob = this;
		m_pkZodiacSkill8 = event_create(zodiac_skill_8_event, Info, PASSES_PER_SEC(2) - (passes_per_sec / 2));
	}
	else if (Type == 8) //POLY
	{
		long XX = 0;
		long YY = 0;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			XX = p.x / 100;
			YY = p.y / 100;
		}

		{
			long x_amk = GetX();
			long y_amk = GetY();

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_BIG);
		}

		{
			float fx, fy;
			GetDeltaByDegree(GetRotation(), 500, &fx, &fy);

			PIXEL_POSITION pos = GetXYZ();

			pos.x += (long) fx;
			pos.y += (long) fy;

			long x_amk = pos.x;
			long y_amk = pos.y;

			x_amk /= 100;
			y_amk /= 100;

			x_amk -= XX;
			y_amk -= YY;

			x_amk *= 100;
			y_amk *= 100;

			EffectZodiacPacket(x_amk, y_amk, SE_SKILL_DAMAGE_ZONE_MIDDLE);
		}

		if (m_pkZodiacSkill9)
		{
			event_cancel(&m_pkZodiacSkill9);
		}

		zodiac_skill_9_info * Info = AllocEventInfo<zodiac_skill_9_info>();
		Info->Mob = this;
		m_pkZodiacSkill9 = event_create(zodiac_skill_9_event, Info, PASSES_PER_SEC(2) - (passes_per_sec / 2));
	}
	else if (Type == 9) //STUN
	{
		long x_amk = GetX();
		long y_amk = GetY();

		x_amk /= 100;
		y_amk /= 100;

		PIXEL_POSITION p;
		if (SECTREE_MANAGER::instance().GetMapBasePosition(GetX(), GetY(), p))
		{
			x_amk -= p.x / 100;
			y_amk -= p.y / 100;
		}

		x_amk *= 100;
		y_amk *= 100;

		EffectZodiacPacket(x_amk, y_amk, SE_SKILL_SAFE_ZONE);

		if (m_pkZodiacSkill10)
		{
			event_cancel(&m_pkZodiacSkill10);
		}

		zodiac_skill_10_info * Info = AllocEventInfo<zodiac_skill_10_info>();
		Info->Mob = this;
		m_pkZodiacSkill10 = event_create(zodiac_skill_10_event, Info, PASSES_PER_SEC(2));
	}
	else if (Type == 10) //SKILL
	{
		if (!Victim || Victim == NULL)
			return;

		Victim->EffectPacket(SE_SKILL_DAMAGE_ZONE_SMALL);

		if (m_pkZodiacSkill11)
		{
			event_cancel(&m_pkZodiacSkill11);
		}

		zodiac_skill_11_info * Info = AllocEventInfo<zodiac_skill_11_info>();
		Info->Mob = this;
		Info->Character = Victim;
		m_pkZodiacSkill11 = event_create(zodiac_skill_11_event, Info, PASSES_PER_SEC(2) - (passes_per_sec / 2));
	}
}

struct FuncZodiacSplashDamage
{
	FuncZodiacSplashDamage(CSkillProto * pkSk, LPCHARACTER pkChr, BYTE bUseSkillPower)
		: m_pkSk(pkSk), m_pkChr(pkChr), m_bUseSkillPower(bUseSkillPower)
	{}

	void operator () (LPCHARACTER pkChrVictim)
	{
		if (!m_pkChr || !pkChrVictim)
		{
			return;
		}

		if (!battle_is_attackable(m_pkChr, pkChrVictim))
		{
			return;
		}

		m_pkSk->SetPointVar("k", 1.0 * m_bUseSkillPower * m_pkSk->bMaxLevel / 100);
		m_pkSk->SetPointVar("lv", m_pkChr->GetLevel());

		m_pkSk->SetPointVar("iq", m_pkChr->GetPoint(POINT_IQ) - (135-m_pkChr->GetLevel()));
		m_pkSk->SetPointVar("str", m_pkChr->GetPoint(POINT_ST) - (135-m_pkChr->GetLevel()));
		m_pkSk->SetPointVar("dex", m_pkChr->GetPoint(POINT_DX) - (135-m_pkChr->GetLevel()));
		m_pkSk->SetPointVar("con", m_pkChr->GetPoint(POINT_HT) - (135-m_pkChr->GetLevel()));
		m_pkSk->SetPointVar("def", m_pkChr->GetPoint(POINT_DEF_GRADE) - (135-m_pkChr->GetLevel()));
		m_pkSk->SetPointVar("odef", m_pkChr->GetPoint(POINT_DEF_GRADE) - m_pkChr->GetPoint(POINT_DEF_GRADE_BONUS));
		m_pkSk->SetPointVar("horse_level", m_pkChr->GetHorseLevel());

		bool bIgnoreDefense = false;
		if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_PENETRATE))
		{
			int iPenetratePct = (int) m_pkSk->kPointPoly2.Eval();
			if (number(1, 100) <= iPenetratePct)
				bIgnoreDefense = true;
		}

		bool bIgnoreTargetRating = false;
		if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_IGNORE_TARGET_RATING))
		{
			int iPct = (int) m_pkSk->kPointPoly2.Eval();
			if (number(1, 100) <= iPct)
				bIgnoreTargetRating = true;
		}

		m_pkSk->SetPointVar("ar", CalcAttackRating(m_pkChr, pkChrVictim, bIgnoreTargetRating));
		if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_USE_MELEE_DAMAGE))
			m_pkSk->SetPointVar("atk", CalcMeleeDamage(m_pkChr, pkChrVictim, true, bIgnoreTargetRating));
		else if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_USE_ARROW_DAMAGE))
		{
			LPITEM pkBow, pkArrow;
			if (1 == m_pkChr->GetArrowAndBow(&pkBow, &pkArrow, 1))
				m_pkSk->SetPointVar("atk", CalcArrowDamage(m_pkChr, pkChrVictim, pkBow, pkArrow, true));
			else
				m_pkSk->SetPointVar("atk", 0);
		}

		if (m_pkSk->bPointOn == POINT_MOV_SPEED)
			m_pkSk->kPointPoly.SetVar("maxv", pkChrVictim->GetLimitPoint(POINT_MOV_SPEED));

		m_pkSk->SetPointVar("maxhp", pkChrVictim->GetMaxHP());
		m_pkSk->SetPointVar("maxsp", pkChrVictim->GetMaxSP());

		m_pkSk->SetPointVar("chain", m_pkChr->GetChainLightningIndex());
		m_pkChr->IncChainLightningIndex();

		m_pkSk->SetPointVar("ek", m_pkChr->GetAffectedEunhyung()*1./100);

		int iAmount = 0;
		if (m_pkChr->GetUsedSkillMasterType(m_pkSk->dwVnum) >= SKILL_GRAND_MASTER)
		{
			iAmount = (int) m_pkSk->kMasterBonusPoly.Eval();
		}
		else
		{
			iAmount = (int) m_pkSk->kPointPoly.Eval();
		}

		iAmount = -iAmount;

		int iDam;

		iDam = CalcBattleDamage(iAmount, m_pkChr->GetLevel(), pkChrVictim->GetLevel());

		EDamageType dt = DAMAGE_TYPE_NONE;
		switch (m_pkSk->bSkillAttrType)
		{
			case SKILL_ATTR_TYPE_NORMAL:
				break;

			case SKILL_ATTR_TYPE_MELEE:
				{
					dt = DAMAGE_TYPE_MELEE;

					if (!bIgnoreDefense)
						iDam -= pkChrVictim->GetPoint(POINT_DEF_GRADE);
				}
				break;

			case SKILL_ATTR_TYPE_RANGE:
				dt = DAMAGE_TYPE_RANGE;
				iDam = iDam * (100 - pkChrVictim->GetPoint(POINT_RESIST_BOW)) / 100;
				break;

			case SKILL_ATTR_TYPE_MAGIC:
				dt = DAMAGE_TYPE_MAGIC;
				iDam = CalcAttBonus(m_pkChr, pkChrVictim, iDam);
#ifdef ENABLE_MAGIC_REDUCTION_SYSTEM
				{
					const int resist_magic = MINMAX(0, pkChrVictim->GetPoint(POINT_RESIST_MAGIC), 100);
					const int resist_magic_reduction = MINMAX(0, (m_pkChr->GetJob()==JOB_SURA) ? m_pkChr->GetPoint(POINT_RESIST_MAGIC_REDUCTION)/2 : m_pkChr->GetPoint(POINT_RESIST_MAGIC_REDUCTION), 50);
					const int total_res_magic = MINMAX(0, resist_magic - resist_magic_reduction, 100);
					iDam = iDam * (100 - total_res_magic) / 100;
				}
#else
				iDam = iDam * (100 - pkChrVictim->GetPoint(POINT_RESIST_MAGIC)) / 100;
#endif
				break;

			default:
				sys_err("Unknown skill attr type %u vnum %u", m_pkSk->bSkillAttrType, m_pkSk->dwVnum);
				break;
		}

		if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_COMPUTE_MAGIC_DAMAGE))
			dt = DAMAGE_TYPE_MAGIC;

		if (pkChrVictim->CanBeginFight())
			pkChrVictim->BeginFight(m_pkChr);

		if (!pkChrVictim->Damage(m_pkChr, iDam, dt) && !pkChrVictim->IsStun())
		{
			if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_REMOVE_GOOD_AFFECT))
			{
				int iAmount2 = (int) m_pkSk->kPointPoly2.Eval();
				int iDur2 = (int) m_pkSk->kDurationPoly2.Eval();
				iDur2 += m_pkChr->GetPoint(POINT_PARTY_BUFFER_BONUS);

				if (number(1, 100) <= iAmount2)
				{
					pkChrVictim->RemoveGoodAffect();
					pkChrVictim->AddAffect(m_pkSk->dwVnum, POINT_NONE, 0, AFF_SKILL_DISPEL, iDur2, 0, true);
				}
			}

#ifdef ENABLE_WOLFMAN_CHARACTER
			if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_SLOW | SKILL_FLAG_STUN | SKILL_FLAG_FIRE_CONT | SKILL_FLAG_POISON | SKILL_FLAG_BLEEDING))
#else
			if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_SLOW | SKILL_FLAG_STUN | SKILL_FLAG_FIRE_CONT | SKILL_FLAG_POISON))
#endif
			{
				int iPct = (int) m_pkSk->kPointPoly2.Eval();
				int iDur = (int) m_pkSk->kDurationPoly2.Eval();

				iDur += m_pkChr->GetPoint(POINT_PARTY_BUFFER_BONUS);

				if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_STUN))
				{
					SkillAttackAffect(m_pkChr, pkChrVictim, iPct, IMMUNE_STUN, AFFECT_STUN, POINT_NONE, 0, AFF_STUN, iDur, m_pkSk->szName);
				}
				else if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_SLOW))
				{
					SkillAttackAffect(m_pkChr, pkChrVictim, iPct, IMMUNE_SLOW, AFFECT_SLOW, POINT_MOV_SPEED, -30, AFF_SLOW, iDur, m_pkSk->szName);
				}
				else if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_FIRE_CONT))
				{
					m_pkSk->SetDurationVar("k", 1.0 * m_bUseSkillPower * m_pkSk->bMaxLevel / 100);
					m_pkSk->SetDurationVar("iq", m_pkChr->GetPoint(POINT_IQ));

					iDur = (int)m_pkSk->kDurationPoly2.Eval();
					int bonus = m_pkChr->GetPoint(POINT_PARTY_BUFFER_BONUS);

					if (bonus != 0)
					{
						iDur += bonus / 2;
					}

					if (number(1, 100) <= iDur)
					{
						pkChrVictim->AttackedByFire(m_pkChr, iPct, 5);
					}
				}
				else if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_POISON))
				{
					if (number(1, 100) <= iPct)
						pkChrVictim->AttackedByPoison(m_pkChr);
				}
#ifdef ENABLE_WOLFMAN_CHARACTER
				else if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_BLEEDING))
				{
					if (number(1, 100) <= iPct)
						pkChrVictim->AttackedByBleeding(m_pkChr);
				}
#endif
			}

			if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_CRUSH | SKILL_FLAG_CRUSH_LONG) &&
				!IS_SET(pkChrVictim->GetAIFlag(), AIFLAG_NOMOVE))
			{
				float fCrushSlidingLength = 200;

				if (m_pkChr->IsNPC())
					fCrushSlidingLength = 400;

				if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_CRUSH_LONG))
					fCrushSlidingLength *= 2;

				float fx, fy;
				float degree = GetDegreeFromPositionXY(m_pkChr->GetX(), m_pkChr->GetY(), pkChrVictim->GetX(), pkChrVictim->GetY());

				if (m_pkSk->dwVnum == SKILL_HORSE_WILDATTACK)
				{
					degree -= m_pkChr->GetRotation();
					degree = fmod(degree, 360.0f) - 180.0f;

					if (degree > 0)
						degree = m_pkChr->GetRotation() + 90.0f;
					else
						degree = m_pkChr->GetRotation() - 90.0f;
				}

				GetDeltaByDegree(degree, fCrushSlidingLength, &fx, &fy);
				sys_log(0, "CRUSH! %s -> %s (%d %d) -> (%d %d)", m_pkChr->GetName(), pkChrVictim->GetName(), pkChrVictim->GetX(), pkChrVictim->GetY(), (long)(pkChrVictim->GetX()+fx), (long)(pkChrVictim->GetY()+fy));
				long tx = (long)(pkChrVictim->GetX()+fx);
				long ty = (long)(pkChrVictim->GetY()+fy);

				pkChrVictim->Sync(tx, ty);
				pkChrVictim->Goto(tx, ty);
				pkChrVictim->CalculateMoveDuration();
			}
		}

		if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_HP_ABSORB))
		{
			int iPct = (int) m_pkSk->kPointPoly2.Eval();
			m_pkChr->PointChange(POINT_HP, iDam * iPct / 100);
		}

		if (IS_SET(m_pkSk->dwFlag, SKILL_FLAG_SP_ABSORB))
		{
			int iPct = (int) m_pkSk->kPointPoly2.Eval();
			m_pkChr->PointChange(POINT_SP, iDam * iPct / 100);
		}
	}

	CSkillProto * m_pkSk;
	LPCHARACTER	m_pkChr;
	BYTE m_bUseSkillPower;
};

int CHARACTER::ZodiacSkillAttack(LPCHARACTER Victim, DWORD dwVnum, BYTE bSkillLevel)
{
	if (!dwVnum || dwVnum == 0)
		return BATTLE_NONE;

	if (!bSkillLevel || bSkillLevel == 0)
		return BATTLE_NONE;

	if (!IsMonster() || !IsZodiacBoss())
		return BATTLE_NONE;

	if (!Victim)
		return BATTLE_NONE;

	if (GetMountVnum())
		return BATTLE_NONE;

	if (IsPolymorphed())
		return BATTLE_NONE;

	if (g_bSkillDisable)
		return BATTLE_NONE;

	CSkillProto * pkSk = CSkillManager::instance().Get(dwVnum);

	if (!pkSk)
		return BATTLE_NONE;

	if (!IS_SET(pkSk->dwFlag, SKILL_FLAG_SPLASH))
		return BATTLE_NONE;

	const float k = 1.0 * GetSkillPower(pkSk->dwVnum, bSkillLevel) * pkSk->bMaxLevel / 100;

	pkSk->SetPointVar("k", k);
	pkSk->kSplashAroundDamageAdjustPoly.SetVar("k", k);

	if (IS_SET(pkSk->dwFlag, SKILL_FLAG_USE_MELEE_DAMAGE))
	{
		pkSk->SetPointVar("atk", CalcMeleeDamage(this, this, true, false));
	}
	else if (IS_SET(pkSk->dwFlag, SKILL_FLAG_USE_MAGIC_DAMAGE))
	{
		pkSk->SetPointVar("atk", CalcMagicDamage(this, this));
	}
	else if (IS_SET(pkSk->dwFlag, SKILL_FLAG_USE_ARROW_DAMAGE))
	{
		LPITEM pkBow, pkArrow;
		if (1 == GetArrowAndBow(&pkBow, &pkArrow, 1))
		{
			pkSk->SetPointVar("atk", CalcArrowDamage(this, this, pkBow, pkArrow, true));
		}
		else
		{
			pkSk->SetPointVar("atk", 0);
		}
	}

	if (pkSk->bPointOn == POINT_MOV_SPEED)
	{
		pkSk->SetPointVar("maxv", this->GetLimitPoint(POINT_MOV_SPEED));
	}

	pkSk->SetPointVar("lv", GetLevel());
	pkSk->SetPointVar("iq", GetPoint(POINT_IQ));
	pkSk->SetPointVar("str", GetPoint(POINT_ST));
	pkSk->SetPointVar("dex", GetPoint(POINT_DX));
	pkSk->SetPointVar("con", GetPoint(POINT_HT));
	pkSk->SetPointVar("maxhp", this->GetMaxHP());
	pkSk->SetPointVar("maxsp", this->GetMaxSP());
	pkSk->SetPointVar("chain", 0);
	pkSk->SetPointVar("ar", CalcAttackRating(this, this));
	pkSk->SetPointVar("def", GetPoint(POINT_DEF_GRADE));
	pkSk->SetPointVar("odef", GetPoint(POINT_DEF_GRADE) - GetPoint(POINT_DEF_GRADE_BONUS));
	pkSk->SetPointVar("horse_level", GetHorseLevel());

	if (pkSk->bSkillAttrType != SKILL_ATTR_TYPE_NORMAL)
		OnMove(true);

	pkSk->SetDurationVar("k", k/*bSkillLevel*/);

	int iAmount = (int) pkSk->kPointPoly.Eval();
	int iAmount2 = (int) pkSk->kPointPoly2.Eval();

	if (GetUsedSkillMasterType(pkSk->dwVnum) >= SKILL_GRAND_MASTER)
	{
		iAmount = (int) pkSk->kMasterBonusPoly.Eval();
	}

	if (IS_SET(pkSk->dwFlag, SKILL_FLAG_REMOVE_BAD_AFFECT))
	{
		if (number(1, 100) <= iAmount2)
		{
			RemoveBadAffect();
		}
	}

	if (IS_SET(pkSk->dwFlag, SKILL_FLAG_ATTACK | SKILL_FLAG_USE_MELEE_DAMAGE | SKILL_FLAG_USE_MAGIC_DAMAGE))
	{
		if (pkSk->bPointOn == POINT_HP && iAmount < 0)
		{
			FuncZodiacSplashDamage(pkSk, this, GetSkillPower(dwVnum, bSkillLevel)) (Victim);
		}

		return BATTLE_DAMAGE;
	}

	return BATTLE_NONE;
}


struct FuncCanonAttack
{
	LPCHARACTER m_pkCanon;
	FuncCanonAttack(LPCHARACTER ch) : m_pkCanon(ch) {};

	void operator () (LPENTITY ent)
	{
		if (!ent->IsType(ENTITY_CHARACTER))
			return;

		LPCHARACTER pkChr = (LPCHARACTER) ent;

		if (!pkChr || !m_pkCanon)
			return;

		if (DISTANCE_APPROX(pkChr->GetX() - m_pkCanon->GetX(), pkChr->GetY() - m_pkCanon->GetY()) <= 2000)
		{
			if (pkChr->IsZodiacBoss())
			{
				if (number(0, 100) <= 5)
				{
					int iDam = pkChr->GetMaxHP() / 10;
					pkChr->Damage(m_pkCanon, iDam, DAMAGE_TYPE_NORMAL);
				}
			}
		}
	}
};

void CHARACTER::CanonDamage()
{
	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(GetMapIndex());
	if (pkMap)
	{
		FuncCanonAttack f(this);
		pkMap->for_each(f);
	}
}


DWORD OfficerVnum(BYTE Vnum)
{
	switch(Vnum)
	{
		case 1:
			return 2750; // Zi
			break;

		case 2:
			return 2760; // Chou
			break;

		case 3:
			return 2770; // Yin
			break;

		case 4:
			return 2780; // Mao
			break;

		case 5:
			return 2790; // Chen
			break;

		case 6:
			return 2800; // Si
			break;

		case 7:
			return 2810; // Wu
			break;

		case 8:
			return 2820; // Wei
			break;

		case 9:
			return 2830; // Shen
			break;

		case 10:
			return 2840; // Yu
			break;

		case 11:
			return 2850; // Xu
			break;

		case 12:
			return 2860; // Hai
			break;

		default:
			return 0;
			break;
	}
}

BYTE MobLevel(BYTE Floor)
{
	if (Floor == 1)
		return number(10, 20);
	else if (Floor == 2)
		return number(15, 25);
	else if (Floor == 3)
		return number(25, 30);
	else if (Floor == 4)
		return number(35, 49);
	else if (Floor == 5 || Floor == 6)
		return number(40, 50);
	else if ((Floor == 7) || (Floor == 21) || (Floor >= 35 && Floor <= 39))
		return 59;
	else if (Floor == 8)
		return number(50, 59);
	else if (Floor == 9)
		return number(50, 69);
	else if (Floor == 10)
		return number(60, 70);
	else if (Floor == 11 || Floor == 12)
		return number(70, 80);
	else if (Floor == 13)
		return number(70, 90);
	else if (Floor == 14)
		return 50;
	else if (Floor == 15 || Floor == 16)
		return number(80, 90);
	else if (Floor == 17)
		return number(80, 93);
	else if (Floor == 18)
		return number(81, 90);
	else if (Floor == 19 || Floor == 20)
		return number(90, 100);
	else if (Floor == 22)
		return number(95, 102);
	else if (Floor == 23)
		return number(100, 107);
	else if (Floor == 24)
		return number(100, 110);
	else if (Floor == 25)
		return number(100, 112);
	else if (Floor == 26)
		return number(109, 119);
	else if (Floor == 27)
		return number(110, 120);
	else if (Floor == 28)
		return 50;
	else if (Floor == 29)
		return number(117, 122);
	else if (Floor == 30)
		return number(118, 124);
	else if (Floor == 31)
		return number(120, 130);
	else if (Floor == 32)
		return number(125, 130);
	else if (Floor == 33)
		return number(121, 130);
	else if (Floor == 34)
		return number(130, 136);
	else
		return 0;
}

BYTE OfficerLevel(BYTE Floor)
{
	BYTE Level = 50;
	BYTE Dongu = 11;

	for (BYTE b = 8; b < 40; ++b)
	{
		if (Level > 135)
			return 135;

		if (b == Floor)
			return Level;

		if ((Dongu - b) == 0)
		{
			Dongu += 3;
			Level += 10;
		}
	}

	return 0;
}

DWORD GroupVnum(BYTE Portal)
{
	if (Portal == 1) //Portal del Zi
		return number(MIN(2900, 2902), MAX(2900, 2902));
	else if (Portal == 2) //Portal del Chou
		return number(MIN(2903, 2905), MAX(2903, 2905));
	else if (Portal == 3) //Portal del Yin
		return number(MIN(2906, 2908), MAX(2906, 2908));
	else if (Portal == 4) //Portal del Mao
		return number(MIN(2909, 2911), MAX(2909, 2911));
	else if (Portal == 5) //Portal del Chen
		return number(MIN(2912, 2914), MAX(2912, 2914));
	else if (Portal == 6) //Portal del Si
		return number(MIN(2915, 2917), MAX(2915, 2917));
	else if (Portal == 7) //Portal del Wu
		return number(MIN(2918, 2920), MAX(2918, 2920));
	else if (Portal == 8) //Portal del Wei
		return number(MIN(2921, 2923), MAX(2921, 2923));
	else if (Portal == 9) //Portal del Shen
		return number(MIN(2924, 2926), MAX(2924, 2926));
	else if (Portal == 10) //Portal del Yu
		return number(MIN(2927, 2929), MAX(2927, 2929));
	else if (Portal == 11) //Portal del Xu
		return number(MIN(2930, 2932), MAX(2930, 2932));
	else if (Portal == 12) //Portal del Hai
		return number(MIN(2933, 2935), MAX(2933, 2935));
	else
		return 0;
}

void CHARACTER::SpawnZodiacGroup(LPZODIAC pZodiac)
{
	if (!pZodiac)
	{
		sys_err("char_battle_zodiac.cpp : SpawnZodiacGroup : No existe pZodiac!");
		return;
	}

	BYTE Floor = pZodiac->GetFloor();

	if (Floor == 7 || Floor == 21) //Bonus
		return;

	BYTE Portal = pZodiac->GetPortal();
	BYTE Level = MobLevel(Floor);

	m_dwStateDuration = PASSES_PER_SEC(1);

	DWORD dwVnum = GroupVnum(Portal);
	if (dwVnum == 0)
	{
		sys_err("Portal falso");
		return;
	}

	SendMovePacket(FUNC_ATTACK, 0, GetX(), GetY(), 0);

	CHARACTER_MANAGER::instance().SelectStone(this);
	CHARACTER_MANAGER::instance().SpawnGroupZodiac(dwVnum, GetMapIndex(), GetX() - 1000, GetY() - 1000, GetX() + 1000, GetY() + 1000, NULL, true, pZodiac, Level);
	CHARACTER_MANAGER::instance().SpawnGroupZodiac(dwVnum, GetMapIndex(), GetX() - 1000, GetY() - 1000, GetX() + 1000, GetY() + 1000, NULL, true, pZodiac, Level);

	if (number(0, 7) == 3)
		CHARACTER_MANAGER::instance().SpawnGroupZodiac(OfficerVnum(Portal), GetMapIndex(), GetX() - 1000, GetY() - 1000, GetX() + 1000, GetY() + 1000, NULL, true, pZodiac, OfficerLevel(Floor));

	CHARACTER_MANAGER::instance().SelectStone(NULL);

	UpdatePacket();
	return;
}

void CHARACTER::SpawnZodiacStone(LPZODIAC pZodiac)
{
	if (!pZodiac)
	{
		sys_err("char_battle_zodiac.cpp : SpawnZodiacStone : No existe pZodiac!");
		return;
	}

	BYTE Floor = pZodiac->GetFloor();

	const CMob* pkMob = NULL;
	DWORD vnum = 0;

	vnum = 2900+number(0, 8);

	if (vnum == 2904 || vnum == 2905 || vnum == 2906) //ZodiacMetin2_group2, ZodiacMetin2_group3, ZodiacMetin3_group1
	{
		if (number(0,2) == 1)
			vnum = 2900+number(0, 3);
		else
			vnum = 2900+number(7, 8);
	}

	if ((pkMob = CMobManager::instance().Get(vnum)) == NULL)
		vnum = 0;

	if (vnum != 0 && pkMob != NULL)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().SpawnMobRange(vnum, 
			GetMapIndex(), 
			GetX() - number(1500, 3000), 
			GetY() - number(1500, 3000), 
			GetX() + number(1500, 3000), 
			GetY() + number(1500, 3000), 
			true, 
			pkMob->m_table.bType == CHAR_TYPE_STONE,
			false,
			(Floor == 6 || Floor == 7) ? 40 : OfficerLevel(Floor));

		if (ch)
		{
			int newHP = ch->GetMaxHP()+(ch->GetLevel()*5000);
			ch->SetMaxHP(newHP);
			ch->SetHP(newHP);
			ch->UpdatePacket();
		}
	}
}
#endif // ENABLE_12ZI
