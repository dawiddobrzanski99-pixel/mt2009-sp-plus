// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
#include "stdafx.h"
#include "playerbot_zodiac_temple.h"
#include "dungeon.h"
#include "char.h"
#include "char_manager.h"
#include "party.h"
#include "affect.h"
#include "packet.h"
#include "desc.h"
#include "config.h"
#include "regen.h"
#include "start_position.h"
#include "item.h"
#include "db.h"
#include "log.h"
#include "item_manager.h"
#include "utils.h"
#include "questmanager.h"
#include "entity.h"
#include "sectree_manager.h"
#include "mob_manager.h"
#include "../../common/CommonDefines.h"

#ifdef ENABLE_12ZI
// #include "../../common/service.h"

int GoToPosition[9][2] =
{
	{3332, 14310},//260 - 245
	{3328, 14815},//260 - 750
	{3328, 15331},//260 - 1250
	//---------//
	{3839, 14299},//750 - 245
	{3839, 14812},//750 - 750
	{3839, 15331},//750 - 1250
	//---------//
	{4359, 14294},//1250 - 245
	{4352, 14814},//1250 - 750
	{4357, 15331},//1250 - 1250
};

int SpawnPosition[9][2] =
{
	{3333, 14344},
	{3328, 14848},
	{3328, 15365},
	//---------//
	{3839, 14335},
	{3839, 14848},
	{3839, 15363},
	//---------//
	{4359, 14327},
	{4352, 14840},
	{4357, 15360},
};

const char * c_Portal[13] =
{
	"","Zi","Chou","Yin","Mao","Chen","Si","Wu","Wei","Shen","Yu","Xu","Hai",
};

//--------------------------------------------------------------------------------------------//

EVENTINFO(Floor_event_data)
{
	int seconds;
	BYTE floor;
	long mapIndex;

	Floor_event_data()
	: seconds(0), floor(0), mapIndex(0)
	{}
};

EVENTFUNC(Floor_event_data_start)
{
	Floor_event_data * info = dynamic_cast<Floor_event_data *>(event->info);
	if (info == NULL)
	{
		sys_err( "Floor_event_data_start> <Factor> Null pointer" );
		return 0;
	}

	LPZODIAC pZodiac = CZodiacManager::instance().FindByMapIndex(info->mapIndex);
	if (pZodiac == NULL)
	{
		sys_err("Cannot LPZODIAC");
		return 0;
	}

	int * pSecondMaintenance = &(info->seconds);
	if (*pSecondMaintenance == 0 || *pSecondMaintenance < 1)
	{
		pZodiac->NewFloor(info->floor);

		if (pZodiac->zodiac_floor_event_data)
			pZodiac->zodiac_floor_event_data = NULL;

		return 0;
	}

	--*pSecondMaintenance;
	return passes_per_sec;
}

EVENTINFO(Floor_remaining_time_event_data)
{
	int seconds;
	BYTE seconds2;
	long mapIndex;
	BYTE floor;

	Floor_remaining_time_event_data()
	: seconds(0), seconds2(0), mapIndex(0), floor(0)
	{}
};

EVENTFUNC(Floor_remaining_time_event_data_start)
{
	Floor_remaining_time_event_data * info = dynamic_cast<Floor_remaining_time_event_data *>(event->info);
	if (info == NULL)
	{
		sys_err( "Floor_remaining_time_event_data_start> <Factor> Null pointer" );
		return 0;
	}

	LPZODIAC pZodiac = CZodiacManager::instance().FindByMapIndex(info->mapIndex);
	if (pZodiac == NULL)
	{
		sys_err("Cannot LPZODIAC");
		return 0;
	}

	int * pSecondMaintenance = &(info->seconds);
	if (*pSecondMaintenance == 0 || *pSecondMaintenance < 1)
	{
		if (info->floor == 7 || info->floor == 14 || info->floor == 21 || info->floor == 28) //Bonus floor less than 35
			pZodiac->NewFloor((info->floor)+1);
		else
			pZodiac->TimeIsUp();

		if (pZodiac->zodiac_remaining_time_temple_floor)
			pZodiac->zodiac_remaining_time_temple_floor = NULL;

		return 0;
	}

	BYTE * time = &(info->seconds2);

	BYTE Floor = info->floor;
	if (Floor != 7 && 
		// Floor != 8 && 
		// Floor != 11 && 
		Floor != 13 && 
		Floor != 14 && 
		// Floor != 15 && 
		// Floor != 17 && 
		// Floor != 18 && 
		Floor != 21 && 
		// Floor != 22 && 
		Floor != 27 && 
		Floor != 28 && 
		// Floor != 29 && 
		// Floor != 30 && 
		Floor != 34 && 
		Floor != 35 && 
		Floor != 36 && 
		Floor != 37 && 
		Floor != 38 && 
		Floor != 39 && 
		Floor != 40)
	{
		++*time;
	}

	if (*time == 2)
	{
		pZodiac->ControlMob();
		*time = 0;
	}

	--*pSecondMaintenance;
	return passes_per_sec;
}

EVENTINFO(Exit_temple_event_data)
{
	int seconds;
	long mapIndex;

	Exit_temple_event_data()
	: seconds(0), mapIndex(0)
	{}
};

EVENTFUNC(Exit_temple_event_data_start)
{
	Exit_temple_event_data * info = dynamic_cast<Exit_temple_event_data *>(event->info);
	if (info == NULL)
	{
		sys_err( "Exit_temple_event_data_start> <Factor> Null pointer" );
		return 0;
	}

	LPZODIAC pZodiac = CZodiacManager::instance().FindByMapIndex(info->mapIndex);
	if (pZodiac == NULL)
	{
		sys_err("Cannot LPZODIAC");
		return 0;
	}

	int * pSecondMaintenance = &(info->seconds);
	if (*pSecondMaintenance == 0 || *pSecondMaintenance < 1)
	{
		pZodiac->ExitTemple();

		if (pZodiac->zodiac_exit_temple_event_data)
			pZodiac->zodiac_exit_temple_event_data = NULL;

		return 0;
	}

	--*pSecondMaintenance;
	return passes_per_sec;
}

//--------------------------------------------------------------------------------------------//

CZodiac::CZodiac(IdType id, long lMapIndex, BYTE bPortal)
	: m_id(id), m_lMapIndex(lMapIndex), m_bPortal(bPortal)
{
	Initialize();
}

CZodiac::~CZodiac()
{
	if (m_pParty != NULL)
	{
		m_pParty->SetZodiac_for_Only_party(NULL);
	}

	event_cancel(&zodiac_floor_event_data);
	event_cancel(&zodiac_remaining_time_temple_floor);
	event_cancel(&zodiac_exit_temple_event_data);
	event_cancel(&deadEvent);
}

void CZodiac::Initialize()
{
	regen_id_ = 0;
	m_iMonsterCount = 0;
	m_iMobKill = 0;
	m_iTotalMonster = 0;
	m_iStoneKill = 0;
	m_iBossKill = 0;
	m_bFloor = 0;
	m_bNextFloor = 0;
	m_bNextFloorControl = false;
	m_bPosition = 0;
	m_dwGetGlobalTime = 0;
	m_bTimeDown = false;
	m_pParty = NULL;
	zodiac_floor_event_data = NULL;
	zodiac_remaining_time_temple_floor = NULL;
	zodiac_exit_temple_event_data = NULL;
}

void CZodiac::SetFlag(std::string name, int value)
{
	if (!this)
		return;

	itertype(m_map_Flag) it = m_map_Flag.find(name);
	if (it != m_map_Flag.end())
		it->second = value;
	else
		m_map_Flag.insert(make_pair(name, value));
}

int CZodiac::GetFlag(std::string name)
{
	if (!this)
		return 0;

	itertype(m_map_Flag) it = m_map_Flag.find(name);
	if (it != m_map_Flag.end())
		return it->second;
	else
		return 0;
}

///-------------------------------------------------------------------------------------------///
struct FWarpToPosition
{
	long lMapIndex;
	long x;
	long y;
	FWarpToPosition(long lMapIndex, long x, long y)
		: lMapIndex(lMapIndex), x(x), y(y)
		{}

	void operator()(LPENTITY ent)
	{
		if (!ent->IsType(ENTITY_CHARACTER))
		{
			return;
		}

		LPCHARACTER ch = (LPCHARACTER)ent;
		if (!ch->IsPC())
		{
			return;
		}

		if (ch->GetMapIndex() == lMapIndex)
		{
			ch->Show(lMapIndex, x, y, 0);
			ch->Stop();
		}
		else
		{
			ch->WarpSet(x,y,lMapIndex);
		}
	}
};

void CZodiac::Jump(LPCHARACTER ch, long lFromMapIndex, int x, int y)
{
	if (!this || !ch)
		return;

	if (!ch->IsPC())
	{
		sys_err("cannot by character");
		return;
	}

	x *= 100;
	y *= 100;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(lFromMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", lFromMapIndex);
		return;
	}

	if (ch->GetMapIndex() == (long)m_lMapIndex)
	{
		ch->Show(m_lMapIndex, x, y, 0);
		ch->Stop();
	}
	else
	{
		ch->WarpSet(x, y, m_lMapIndex);
	}
}

void CZodiac::JumpAll(long lFromMapIndex, int x, int y)
{
	if (!this)
		return;

	x *= 100;
	y *= 100;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(lFromMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", lFromMapIndex);
		return;
	}

	FWarpToPosition f(m_lMapIndex, x, y);
	pMap->for_each(f);
}

void CZodiac::JumpParty(LPPARTY pParty, long lFromMapIndex, int x, int y)
{
	if (!this || !pParty)
		return;

	x *= 100;
	y *= 100;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(lFromMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", lFromMapIndex);
		return;
	}

	if (pParty->GetZodiac_for_Only_party() == NULL)
	{
		if (m_pParty == NULL)
		{
			m_pParty = pParty;
		}
		else if (m_pParty != pParty)
		{
			sys_err ("Zodiac already has party. Another party cannot jump in Zodiac : index %d", GetMapIndex());
			return;
		}

		pParty->SetZodiac_for_Only_party(this);
	}

	FWarpToPosition f(m_lMapIndex, x, y);
	pParty->ForEachOnMapMember(f, lFromMapIndex);
}
///-------------------------------------------------------------------------------------------///

void CZodiac::SpawnRegen(const char* filename, bool bOnce)
{
	if (!this)
		return;

	if (!filename)
	{
		sys_err("CZodiac::SpawnRegen(filename=NULL, bOnce=%d) - m_lMapIndex[%d]", bOnce, m_lMapIndex); 
		return;
	}

	LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pkSectreeMap)
	{
		sys_err("CZodiac::SpawnRegen(filename=%s, bOnce=%d) - m_lMapIndex[%d]", filename, bOnce, m_lMapIndex); 
		return;
	}

	regen_zodiac(filename, m_lMapIndex, pkSectreeMap->m_setting.iBaseX, pkSectreeMap->m_setting.iBaseY, this, bOnce);
}

#ifdef ENABLE_SERVERTIME_PORTAL_SPAWN
void CZodiac::SpawnRegenZodiac(const char* filename, bool bOnce)
{
	// ZODIAK: funkcja statyczna (paczka wolala ja na instance() singletona, ktory nie istnieje poza wyprawa; UB)
	if (!filename)
	{
		sys_err("CZodiac::SpawnRegenZodiac(filename=NULL, bOnce=%d)", bOnce);
		return;
	}

	LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(MAP_INDEX);
	if (!pkSectreeMap)
	{
		sys_err("CZodiac::SpawnRegenZodiac(filename=%s, bOnce=%d) - map %d not loaded on this core", filename, bOnce, MAP_INDEX);
		return;
	}

	regen_load_in_file(filename, MAP_INDEX, pkSectreeMap->m_setting.iBaseX, pkSectreeMap->m_setting.iBaseY);
}
#endif

void CZodiac::AddRegen(LPREGEN regen)
{
	if (!this)
		return;

	regen->id = regen_id_++;
	m_regen.push_back(regen);
}

void CZodiac::ClearRegen()
{
	if (!this)
		return;

	for (itertype(m_regen) it = m_regen.begin(); it != m_regen.end(); ++it)
	{
		LPREGEN regen = *it;

		event_cancel(&regen->event);
		M2_DELETE(regen);
	}

	m_regen.clear();
}

bool CZodiac::IsValidRegen(LPREGEN regen, size_t regen_id)
{
	if (!this)
		return false;

	itertype(m_regen) it = std::find(m_regen.begin(), m_regen.end(), regen);
	if (it == m_regen.end())
	{
		return false;
	}

	LPREGEN found = *it;
	return (found->id == regen_id);
}
//-----------------------------------------------------------------------------------------------//

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
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
				ch->ChatPacket(CHAT_TYPE_MISSION, "%s", m_psz);
		}
	}

	const char * m_psz;
};

void CZodiac::ZodiacMessage(const char* msg)
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", MAP_INDEX);
		return;
	}

	FZodiacNotice f(msg);
	pMap->for_each(f);
}

struct FZodiacNoticeFloor
{
	BYTE floor;
	FZodiacNoticeFloor(BYTE f) : floor(f)
	{
	}

	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->ChatPacket(CHAT_TYPE_MISSION, LC_TEXT("[224]Mission complete. As soon as the group leader hits the button, you will be teleported directly to level %u."), floor); //224
			}
		}
	}
};

void CZodiac::ZodiacMessageMission(BYTE Floor)
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacNoticeFloor f(Floor);
	pMap->for_each(f);
}

struct FZodiacMessageFloor
{
	BYTE Floor;
	BYTE Count;
	FZodiacMessageFloor(BYTE f, BYTE c) : Floor(f), Count(c)
	{
	}

	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->ZodiacFloorMessage(Floor);
			}
		}
	}
};

void CZodiac::ZodiacFloorMessage(BYTE Floor, BYTE Count)
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacMessageFloor f(Floor, Count);
	pMap->for_each(f);
}

struct FZodiacSubMessageFloor
{
	const char * m_psz;
	FZodiacSubMessageFloor(const char * psz) : m_psz(psz)
	{
	}

	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->ChatPacket(CHAT_TYPE_SUB_MISSION, "%s", m_psz);
			}
		}
	}
};

void CZodiac::ZodiacFloorSubMessage(const char * msg)
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacSubMessageFloor f(msg);
	pMap->for_each(f);
}

struct FZodiacNoticeClear
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
				ch->ChatPacket(CHAT_TYPE_CLEAR_MISSION, "Zodiac");
		}
	}
};

void CZodiac::ZodiacMessageClear()
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", MAP_INDEX);
		return;
	}

	FZodiacNoticeClear f;
	pMap->for_each(f);
}

struct FZodiacCompletedFloor
{
	BYTE completedFloor;

	FZodiacCompletedFloor(BYTE c)
		: completedFloor(c)
	{}

	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
				ch->SetQuestFlag("12zi_temple.completed_floor", completedFloor);
		}
	}
};

void CZodiac::SetFloor(BYTE completedFloor)
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", MAP_INDEX);
		return;
	}

	FZodiacCompletedFloor f(completedFloor);
	pMap->for_each(f);
}

struct FZodiacTime
{
	BYTE currentfloor, nextfloor;
	int time, time2;

	FZodiacTime(BYTE c, BYTE n, int t, int t2)
		: currentfloor(c), nextfloor(n), time(t), time2(t2)
	{}

	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
				ch->ChatPacket(CHAT_TYPE_COMMAND, "ZodiacTime %d %d %d %d", currentfloor, nextfloor, time, time2);
		}
	}
};

void CZodiac::ZodiacTime(BYTE currentfloor, BYTE nextfloor, int time, int time2)
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", MAP_INDEX);
		return;
	}

	FZodiacTime f(currentfloor, nextfloor, time, time2);
	pMap->for_each(f);
}

struct FZodiacTimeClear
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
				ch->ChatPacket(CHAT_TYPE_COMMAND, "ZodiacTimeClear");
		}
	}
};

void CZodiac::ZodiacTimeClear()
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", MAP_INDEX);
		return;
	}

	FZodiacTimeClear f;
	pMap->for_each(f);
}
//----------------------------------------------------------------------------------------//

void CZodiac::ControlMob()
{
	if (!this)
		return;

	/*if (ControlCharacter() == true)
	{
		sys_err("No se quedo.");
		CZodiacManager::instance().Destroy(m_id);
		return;
	}*/

	if (zodiac_floor_event_data)
	{
		sys_err("Bug Fixed");
		return;
	}

	if (zodiac_exit_temple_event_data)
	{
		sys_err("Bug fixed 2");
		return;
	}

	BYTE Floor = GetFloor();

	if (Floor >= 40)
	{
		sys_err("Now Floor 40");
		return;
	}

	if (Floor == 1)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_1") == 0)
		{
			SetFlag("RemainTime_9min_floor_1", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 4, Time, Time_1); //Jump 4 floors (1F + 4F_Jumps = 5F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_1") == 0)
		{
			SetFlag("RemainTime_8min_floor_1", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (1F + 3F_Jumps = 4F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_1") == 0)
		{
			SetFlag("RemainTime_7min_floor_1", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (1F + 2F_Jumps = 3F)
		}
		else if ((get_global_time() - GetTime()) > 240 && GetFlag("RemainTime_6min_floor_1") == 0)
		{
			SetFlag("RemainTime_6min_floor_1", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (1F + 1F_Jumps = 2F)
		}
	}
	else if (Floor == 2)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_2") == 0)
		{
			SetFlag("RemainTime_9min_floor_2", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (2F + 3F_Jumps = 5F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_2") == 0)
		{
			SetFlag("RemainTime_8min_floor_2", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (2F + 2F_Jumps = 4F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_2") == 0)
		{
			SetFlag("RemainTime_7min_floor_2", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (2F + 1F_Jumps = 3F)
		}
	}
	else if (Floor == 3)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_3") == 0)
		{
			SetFlag("RemainTime_9min_floor_3", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (3F + 2F_Jumps = 5F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_3") == 0)
		{
			SetFlag("RemainTime_8min_floor_3", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (3F + 1F_Jumps = 4F)
		}
	}
	else if (Floor == 4)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_4") == 0)
		{
			SetFlag("RemainTime_9min_floor_4", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (4F + 1F_Jumps = 5F)
		}
	}

	else if (Floor == 8)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_8") == 0)
		{
			SetFlag("RemainTime_9min_floor_8", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 4, Time, Time_1); //Jump 4 floors (8F + 4F_Jumps = 12F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_8") == 0)
		{
			SetFlag("RemainTime_8min_floor_8", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (8F + 3F_Jumps = 11F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_8") == 0)
		{
			SetFlag("RemainTime_7min_floor_8", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (8F + 2F_Jumps = 10F)
		}
		else if ((get_global_time() - GetTime()) > 240 && GetFlag("RemainTime_6min_floor_8") == 0)
		{
			SetFlag("RemainTime_6min_floor_8", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (8F + 1F_Jumps = 9F)
		}
	}
	else if (Floor == 9)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_9") == 0)
		{
			SetFlag("RemainTime_9min_floor_9", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (9F + 3F_Jumps = 12F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_9") == 0)
		{
			SetFlag("RemainTime_8min_floor_9", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (9F + 2F_Jumps = 11F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_9") == 0)
		{
			SetFlag("RemainTime_7min_floor_9", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (9F + 1F_Jumps = 10F)
		}
	}
	else if (Floor == 10)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_10") == 0)
		{
			SetFlag("RemainTime_9min_floor_10", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (10F + 2F_Jumps = 12F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_10") == 0)
		{
			SetFlag("RemainTime_8min_floor_10", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (10F + 1F_Jumps = 11F)
		}
	}
	else if (Floor == 11)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_11") == 0)
		{
			SetFlag("RemainTime_9min_floor_11", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (11F + 1F_Jumps = 12F)
		}
	}

	else if (Floor == 15)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_15") == 0)
		{
			SetFlag("RemainTime_9min_floor_15", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 4, Time, Time_1); //Jump 4 floors (15F + 4F_Jumps = 19F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_15") == 0)
		{
			SetFlag("RemainTime_8min_floor_15", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (15F + 3F_Jumps = 18F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_15") == 0)
		{
			SetFlag("RemainTime_7min_floor_15", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (15F + 2F_Jumps = 17F)
		}
		else if ((get_global_time() - GetTime()) > 240 && GetFlag("RemainTime_6min_floor_15") == 0)
		{
			SetFlag("RemainTime_6min_floor_15", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (15F + 1F_Jumps = 16F)
		}
	}
	else if (Floor == 16)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_16") == 0)
		{
			SetFlag("RemainTime_9min_floor_16", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (16F + 3F_Jumps = 19F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_16") == 0)
		{
			SetFlag("RemainTime_8min_floor_16", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (16F + 2F_Jumps = 18F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_16") == 0)
		{
			SetFlag("RemainTime_7min_floor_16", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (16F + 1F_Jumps = 17F)
		}
	}
	else if (Floor == 17)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_17") == 0)
		{
			SetFlag("RemainTime_9min_floor_17", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (17F + 2F_Jumps = 19F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_17") == 0)
		{
			SetFlag("RemainTime_8min_floor_17", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (17F + 1F_Jumps = 18F)
		}
	}
	else if (Floor == 18)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_18") == 0)
		{
			SetFlag("RemainTime_9min_floor_18", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (18F + 1F_Jumps = 19F)
		}
	}

	else if (Floor == 22)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_22") == 0)
		{
			SetFlag("RemainTime_9min_floor_22", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 4, Time, Time_1); //Jump 4 floors (22F + 4F_Jumps = 26F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_22") == 0)
		{
			SetFlag("RemainTime_8min_floor_22", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (22F + 3F_Jumps = 25F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_22") == 0)
		{
			SetFlag("RemainTime_7min_floor_22", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (22F + 2F_Jumps = 24F)
		}
		else if ((get_global_time() - GetTime()) > 240 && GetFlag("RemainTime_6min_floor_22") == 0)
		{
			SetFlag("RemainTime_6min_floor_22", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (22F + 1F_Jumps = 23F)
		}
	}
	else if (Floor == 23)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_23") == 0)
		{
			SetFlag("RemainTime_9min_floor_23", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (23F + 3F_Jumps = 26F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_23") == 0)
		{
			SetFlag("RemainTime_8min_floor_23", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (23F + 2F_Jumps = 25F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_23") == 0)
		{
			SetFlag("RemainTime_7min_floor_23", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (23F + 1F_Jumps = 24F)
		}
	}
	else if (Floor == 24)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_24") == 0)
		{
			SetFlag("RemainTime_9min_floor_24", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (24F + 2F_Jumps = 26F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_24") == 0)
		{
			SetFlag("RemainTime_8min_floor_24", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (24F + 1F_Jumps = 25F)
		}
	}
	else if (Floor == 25)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_25") == 0)
		{
			SetFlag("RemainTime_9min_floor_25", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (25F + 1F_Jumps = 26F)
		}
	}

	else if (Floor == 29)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_29") == 0)
		{
			SetFlag("RemainTime_9min_floor_29", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 4, Time, Time_1); //Jump 4 floors (29F + 4F_Jumps = 33F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_29") == 0)
		{
			SetFlag("RemainTime_8min_floor_29", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (29F + 3F_Jumps = 32F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_29") == 0)
		{
			SetFlag("RemainTime_7min_floor_29", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (29F + 2F_Jumps = 31F)
		}
		else if ((get_global_time() - GetTime()) > 240 && GetFlag("RemainTime_6min_floor_29") == 0)
		{
			SetFlag("RemainTime_6min_floor_29", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (29F + 1F_Jumps = 30F)
		}
	}
	else if (Floor == 30)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_30") == 0)
		{
			SetFlag("RemainTime_9min_floor_30", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 3, Time, Time_1); //Jump 3 floors (30F + 3F_Jumps = 33F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_30") == 0)
		{
			SetFlag("RemainTime_8min_floor_30", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (30F + 2F_Jumps = 32F)
		}
		else if ((get_global_time() - GetTime()) > 180 && GetFlag("RemainTime_7min_floor_30") == 0)
		{
			SetFlag("RemainTime_7min_floor_30", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (30F + 1F_Jumps = 31F)
		}
	}
	else if (Floor == 31)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_31") == 0)
		{
			SetFlag("RemainTime_9min_floor_31", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 2, Time, Time_1); //Jump 2 floors (31F + 2F_Jumps = 33F)
		}
		else if ((get_global_time() - GetTime()) > 120 && GetFlag("RemainTime_8min_floor_31") == 0)
		{
			SetFlag("RemainTime_8min_floor_31", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (31F + 1F_Jumps = 32F)
		}
	}
	else if (Floor == 32)
	{
		if ((get_global_time() - GetTime()) > 60 && GetFlag("RemainTime_9min_floor_32") == 0)
		{
			SetFlag("RemainTime_9min_floor_32", 1);
			DWORD Time = 10*60;
			DWORD Time_1 = (get_global_time()+1) - GetTime();
			ZodiacTime(Floor, 1, Time, Time_1); //Jump 1 floors (32F + 1F_Jumps = 33F)
		}
	}

	if (CountMonster() == 0)
	{
		SetFloor(Floor);

		if (Floor >= 4 && Floor <=6)
			GiveGiftZodiacSmall();
		else if (Floor == 9 || Floor == 10 || Floor == 12)
		{
			if (number(1, 10) <= 4)
			{
				if (GetPortal() == 1)
					GiveGiftZi();
				else if (GetPortal() == 2)
					GiveGiftChou();
				else if (GetPortal() == 3)
					GiveGiftYin();
				else if (GetPortal() == 4)
					GiveGiftMao();
				else if (GetPortal() == 5)
					GiveGiftChen();
				else if (GetPortal() == 6)
					GiveGiftSi();
				else if (GetPortal() == 7)
					GiveGiftWu();
				else if (GetPortal() == 8)
					GiveGiftWei();
				else if (GetPortal() == 9)
					GiveGiftShen();
				else if (GetPortal() == 10)
					GiveGiftYu();
				else if (GetPortal() == 11)
					GiveGiftXu();
				else if (GetPortal() == 12)
					GiveGiftHai();
			}
			else
				GiveGiftZodiacSmall();
		}
		else if ((Floor == 16 || Floor == 19 || Floor == 20) || (Floor >= 23 && Floor <= 25))
		{
			if (number(1, 10) <= 4)
			{
				if (GetPortal() == 1)
					GiveGiftZi();
				else if (GetPortal() == 2)
					GiveGiftChou();
				else if (GetPortal() == 3)
					GiveGiftYin();
				else if (GetPortal() == 4)
					GiveGiftMao();
				else if (GetPortal() == 5)
					GiveGiftChen();
				else if (GetPortal() == 6)
					GiveGiftSi();
				else if (GetPortal() == 7)
					GiveGiftWu();
				else if (GetPortal() == 8)
					GiveGiftWei();
				else if (GetPortal() == 9)
					GiveGiftShen();
				else if (GetPortal() == 10)
					GiveGiftYu();
				else if (GetPortal() == 11)
					GiveGiftXu();
				else if (GetPortal() == 12)
					GiveGiftHai();
			}
			else
				GiveGiftZodiacMiddle();
		}
		else if (Floor == 26 || Floor == 31 || Floor == 32 || Floor == 33)
		{
			if (number(1, 10) <= 7)
			{
				if (GetPortal() == 1)
					GiveGiftZi();
				else if (GetPortal() == 2)
					GiveGiftChou();
				else if (GetPortal() == 3)
					GiveGiftYin();
				else if (GetPortal() == 4)
					GiveGiftMao();
				else if (GetPortal() == 5)
					GiveGiftChen();
				else if (GetPortal() == 6)
					GiveGiftSi();
				else if (GetPortal() == 7)
					GiveGiftWu();
				else if (GetPortal() == 8)
					GiveGiftWei();
				else if (GetPortal() == 9)
					GiveGiftShen();
				else if (GetPortal() == 10)
					GiveGiftYu();
				else if (GetPortal() == 11)
					GiveGiftXu();
				else if (GetPortal() == 12)
					GiveGiftHai();
			}
			else
				GiveGiftZodiacBig();
		}

		if (Floor == 1)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 6;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(1, 5, 10); //1F + 5F_Jumps = 6F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 5;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(1, 4, 10); //1F + 4F_Jumps = 5F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 4;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(1, 3, 10); //1F + 3F_Jumps = 4F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 240)
			{
				Floor = 3;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(1, 2, 10); //1F + 2F_Jumps = 3F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 300)
			{
				Floor = 2;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(1, 1, 10); //1F + 1F_Jumps = 2F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 2)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 6;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(2, 4, 10); //2F + 4F_Jumps = 6F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 5;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(2, 3, 10); //2F + 3F_Jumps = 5F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 4;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(2, 2, 10); //2F + 2F_Jumps = 4F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 240)
			{
				Floor = 3;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(2, 1, 10); //2F + 1F_Jumps = 3F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 3)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 6;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(3, 3, 10); //3F + 3F_Jumps = 6F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 5;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(3, 2, 10); //3F + 2F_Jumps = 5F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 4;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(3, 1, 10); //3F + 1F_Jumps = 4F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 4)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 6;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(4, 2, 10); //4F + 2F_Jumps = 6F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 5;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(4, 1, 10); //4F + 1F_Jumps = 5F
				NextFloorButton();
				return;
			}
		}

		else if (Floor == 9)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 13;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(9, 4, 10); //9F + 4F_Jumps = 13F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 12;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(9, 3, 10); //9F + 3F_Jumps = 12F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 11;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(9, 2, 10); //9F + 2F_Jumps = 11F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 240)
			{
				Floor = 10;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(9, 1, 10); //9F + 1F_Jumps = 10F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 10)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 13;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(10, 3, 10); //10F + 3F_Jumps = 13F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 12;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(10, 2, 10); //10F + 2F_Jumps = 12F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 11;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(10, 1, 10); //10F + 1F_Jumps = 1F
				NextFloorButton();
				return;
			}
		}

		else if (Floor == 16)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 20;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(16, 4, 10); //16F + 4F_Jumps = 20F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 19;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(16, 3, 10); //16F + 3F_Jumps = 19F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 18;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(16, 2, 10); //16F + 2F_Jumps = 18F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 240)
			{
				Floor = 17;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(16, 1, 10); //16F + 1F_Jumps = 17F
				NextFloorButton();
				return;
			}
		}

		else if (Floor == 23)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 27;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(23, 4, 10); //23F + 4F_Jumps = 27F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 26;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(23, 3, 10); //23F + 3F_Jumps = 26F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 25;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(23, 2, 10); //23F + 2F_Jumps = 25F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 240)
			{
				Floor = 24;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(23, 1, 10); //23F + 1F_Jumps = 24F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 24)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 27;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(24, 3, 10); //24F + 3F_Jumps = 27F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 26;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(24, 2, 10); //24F + 2F_Jumps = 26F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 25;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(24, 1, 10); //24F + 1F_Jumps = 25F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 25)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 27;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(25, 2, 10); //25F + 2F_Jumps = 27F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 26;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(25, 1, 10); //25F + 1F_Jumps = 26F
				NextFloorButton();
				return;
			}
		}


		else if (Floor == 31)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 34;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(31, 3, 10); //31F + 3F_Jumps = 34F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 33;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(31, 2, 10); //31F + 2F_Jumps = 33F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 180)
			{
				Floor = 32;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(31, 1, 10); //31F + 1F_Jumps = 32F
				NextFloorButton();
				return;
			}
		}
		else if (Floor == 32)
		{
			if ((get_global_time() - GetTime()) <= 60)
			{
				Floor = 34;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(32, 2, 10); //32F + 2F_Jumps = 34F
				NextFloorButton();
				return;
			}
			else if ((get_global_time() - GetTime()) <= 120)
			{
				Floor = 33;

				if (zodiac_remaining_time_temple_floor)
				{
					event_cancel(&zodiac_remaining_time_temple_floor);
					zodiac_remaining_time_temple_floor = NULL;
				}

				m_bNextFloor = Floor;
				m_bNextFloorControl = true;

				ZodiacMessageMission(Floor);
				ZodiacTime(32, 1, 10); //32F + 1F_Jumps = 33F
				NextFloorButton();
				return;
			}
		}

		if (zodiac_remaining_time_temple_floor)
		{
			event_cancel(&zodiac_remaining_time_temple_floor);
			zodiac_remaining_time_temple_floor = NULL;
		}

		Floor += 1;

		m_bNextFloor = Floor;
		m_bNextFloorControl = true;

		ZodiacMessageMission(Floor);
		ZodiacTime(Floor-1, 1, 10);
		NextFloorButton();
	}
}

struct FCountMonster
{
	int n;
	FCountMonster() : n(0) {};
	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch->IsPC() && !ch->IsDead() && (ch->IsMonster() || ch->IsStone()))
				n++;
		}
	}
};

int CZodiac::CountMonster()
{
	if (!this)
		return 0;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return -1;
	}

	FCountMonster f;
	pMap->for_each(f);
	return f.n;
}

struct FCountIsBoss
{
	int n;
	FCountIsBoss() : n(0) {};
	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch->IsPC() && !ch->IsDead() && (ch->IsMonster() || ch->IsStone()))
			{
				if (ch->IsZodiacBoss())
				{
					n++;
				}
			}
		}
	}
};

int CZodiac::CountIsBoss()
{
	if (!this)
		return 0;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return 0;
	}

	FCountIsBoss f;
	pMap->for_each(f);
	return f.n;
}

struct FCountIsStone
{
	int n;
	FCountIsStone() : n(0) {};
	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch->IsPC() && !ch->IsDead() && (ch->IsMonster() || ch->IsStone()))
			{
				if (ch->IsStone())
				{
					n++;
				}
			}
		}
	}
};

int CZodiac::CountIsStone()
{
	if (!this)
		return 0;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return 0;
	}

	FCountIsStone f;
	pMap->for_each(f);
	return f.n;
}

struct FCountCharacter
{
	int n;
	FCountCharacter() : n(0) {};
	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (ch->IsPC())
				n++;
		}
	}
};

bool CZodiac::ControlCharacter()
{
	if (!this)
		return false;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return false;
	}

	FCountCharacter f;
	pMap->for_each(f);
	int count = f.n;
	if (count == 0)
		return true;

	return false;
}

struct FZodiacExitAll
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
				ch->WarpSet(333200, 1431000, 0);
		}
	}
};

void CZodiac::ExitTemple()
{
	if (!this)
		return;

	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (!pMap)
	{
		sys_err("cannot find map by index %d", m_lMapIndex);
		return;
	}

	FZodiacExitAll f;
	pMap->for_each(f);
}

void CZodiac::TimeIsUp()
{
	if (!this)
		return;

	if (zodiac_floor_event_data)
		event_cancel(&zodiac_floor_event_data);

	if (zodiac_remaining_time_temple_floor)
		event_cancel(&zodiac_remaining_time_temple_floor);

	if (zodiac_exit_temple_event_data)
		event_cancel(&zodiac_exit_temple_event_data);

	if (deadEvent)
		event_cancel(&deadEvent);

	KillAll();

	ZodiacFloorMessage(43);
	ZodiacTime(GetFloor(), 0, 10);

	Exit_temple_event_data * info = AllocEventInfo<Exit_temple_event_data>();
	info->seconds = 10;
	info->mapIndex = GetMapIndex();
	zodiac_exit_temple_event_data = event_create(Exit_temple_event_data_start, info, 1);
}

struct FPurgeSectree
{
	void operator () (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;

			if (!ch)
				return;

			if (!ch->IsPC()
				&& !ch->IsDead()
				&& !ch->IsPet()
				// && !ch->IsNewPet()
				// && !ch->IsSupport()
				// && !ch->IsNewMount()
				)
			{
				M2_DESTROY_CHARACTER(ch);
			}
		}
		else if (ent->IsType(ENTITY_ITEM))
		{
			LPITEM item = (LPITEM) ent;
			M2_DESTROY_ITEM(item);
		}
		else
			sys_err("unknown entity type %d is in zodiac", ent->GetType());
	}
};

void CZodiac::Purge()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FPurgeSectree f;
	pkMap->for_each(f);
}

struct FKillSectree
{
	void operator () (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;

			if (!ch->IsPC() && !ch->IsDead()
				&& !ch->IsPet()
				// && !ch->IsNewPet()
				// && !ch->IsSupport()
				// && !ch->IsNewMount()
				)
			{
				ch->Dead();

				if (ch->GetSectree())
				{
					ch->GetSectree()->RemoveEntity(ch);
					ch->ViewCleanup();
				}
			}
		}
	}
};

void CZodiac::KillAll()
{
	if (!this)
		return;

	if (CountMonster() == 0)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FKillSectree f;
	pkMap->for_each(f);
}


void CZodiac::NewFloor(BYTE Floor)
{
	if (!this)
		return;

	DWORD Second = 0;
	if (Floor == 7 || Floor == 14 || Floor == 21 || Floor == 28 || Floor == 35 || Floor == 36 || Floor == 37 || Floor == 38 || Floor == 39 || Floor == 40) //Bonus floor
		Second = 5*60;
	else
		Second = 10*60;

	m_dwGetGlobalTime = get_global_time();
	// m_bTimeDown = false;

	if (zodiac_floor_event_data)
	{
		event_cancel(&zodiac_floor_event_data);
		zodiac_floor_event_data = NULL;
	}

	if (zodiac_remaining_time_temple_floor)
	{
		event_cancel(&zodiac_remaining_time_temple_floor);
		zodiac_remaining_time_temple_floor = NULL;
	}

	Floor_remaining_time_event_data * info = AllocEventInfo<Floor_remaining_time_event_data>();
	info->seconds = Second;
	info->mapIndex = m_lMapIndex;
	info->floor = Floor;
	zodiac_remaining_time_temple_floor = event_create(Floor_remaining_time_event_data_start, info, 1);

	m_bFloor = Floor;
	m_bNextFloorControl = false;

	m_iMobKill = 0;
	m_iStoneKill = 0;
	m_iBossKill = 0;
	m_iTotalMonster = 0;

	ZodiacFloorMessage(Floor);
	ZodiacTime(Floor, 1, Second);

	BYTE Portal = 0;
	if ((Portal = GetPortal()) == 0)
	{
		sys_err("cannot find by map::Portal");
		return;
	}

	if (Floor == 1)
	{
		ZodiacTime(Floor, 5, Second);

		m_bPosition = 1;
		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		ProcessZodiacItems(false);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 2)
	{
		ZodiacTime(Floor, 4, Second);

		m_bPosition = 1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 3)
	{
		ZodiacTime(Floor, 3, Second);

		m_bPosition = 1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 4)
	{
		ZodiacTime(Floor, 2, Second);

		m_bPosition = 1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 5)
	{
		m_bPosition = 1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 6)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(1)");

		SpawnBoss(1);
	}
	else if (Floor == 7)
	{
		m_bPosition = 1;

		SetFlag("bonus", 0);
		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	else if (Floor == 8)
	{
		ZodiacTime(Floor, 5, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 8;
		m_iTotalMonster = 8;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(8)");

		for (BYTE b = 0; b < 8; ++b)
			SpawnStone();
	}
	else if (Floor == 9)
	{
		ZodiacTime(Floor, 4, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 10)
	{
		ZodiacTime(Floor, 3, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 11)
	{
		ZodiacTime(Floor, 2, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iBossKill = 3;
		m_iTotalMonster = 3;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/3)");

		for (BYTE b = 0; b < 4; ++b)
			SpawnStone();

		for (BYTE b = 0; b < 3; ++b)
			SpawnBoss(0);
	}
	else if (Floor == 12)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 13)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 8;
		m_iTotalMonster = 8;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/8)");

		for (BYTE b = 0; b < 8; ++b)
			SpawnStone();
	}
	else if (Floor == 14)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 10;
		m_iTotalMonster = 10;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/10)");

		SpawnStone(true);
	}
	else if (Floor == 15)
	{
		ZodiacTime(Floor, 5, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iMobKill = 100;
		m_iTotalMonster = 100;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(100)");

		for (BYTE b = 0; b < 15; ++b)
			SpawnMob();
	}
	else if (Floor == 16)
	{
		ZodiacTime(Floor, 4, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 17)
	{
		ZodiacTime(Floor, 3, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iBossKill = 1;
		m_iTotalMonster = 1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/1)");

		SpawnBoss(0);

		for (BYTE b = 0; b < 4; ++b)
			SpawnStone();
	}
	else if (Floor == 18)
	{
		ZodiacTime(Floor, 2, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 7;
		m_iTotalMonster = 7;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(7)");

		for (BYTE b = 0; b < 7; ++b)
			SpawnStone();
	}
	else if (Floor == 19)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 20)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 21)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		SetFlag("bonus", 0);

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	else if (Floor == 22)
	{
		ZodiacTime(Floor, 5, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iBossKill = 3;
		m_iTotalMonster = 3;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/3)");

		for (BYTE b = 0; b < 3; ++b)
			SpawnMob();

		for (BYTE b = 0; b < 3; ++b)
			SpawnBoss(0);
	}
	else if (Floor == 23)
	{
		ZodiacTime(Floor, 4, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 24)
	{
		ZodiacTime(Floor, 3, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 4;
		m_iTotalMonster = 4;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 25)
	{
		ZodiacTime(Floor, 2, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 26)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 27)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 4;
		m_iTotalMonster = 4;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(4)");

		for (BYTE b = 0; b < 5; ++b)
			SpawnMob();

		for (BYTE b = 0; b < 4; ++b)
			SpawnStone();
	}
	else if (Floor == 28)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 10;
		m_iTotalMonster = 10;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/10)");

		SpawnStone(true);
	}
	else if (Floor == 29)
	{
		ZodiacTime(Floor, 5, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 8;
		m_iTotalMonster = 8;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/8)");

		for (BYTE b = 0; b < 8; ++b)
			SpawnStone();
	}
	else if (Floor == 30)
	{
		ZodiacTime(Floor, 4, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iStoneKill = 8;
		m_iTotalMonster = 8;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(0/8)");

		for (BYTE b = 0; b < 8; ++b)
			SpawnStone();
	}
	else if (Floor == 31)
	{
		ZodiacTime(Floor, 3, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 32)
	{
		ZodiacTime(Floor, 2, Second);

		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 33)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 7; ++b)
			SpawnMob();
	}
	else if (Floor == 34)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		m_iMobKill = 80;
		m_iBossKill = 1;

		m_iTotalMonster = 80;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		ZodiacFloorMessage(Floor);
		ZodiacFloorSubMessage("(80)");

		for (BYTE b = 0; b < 12; ++b)
			SpawnMob();
	}
	//------------------------------------------------------------------------//
	else if (Floor == 35)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	else if (Floor == 36)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	else if (Floor == 37)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	else if (Floor == 38)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	else if (Floor == 39)
	{
		BYTE n = number(1, 8);

		m_bPosition = n+1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[n][0], GoToPosition[n][1]);

		for (BYTE b = 0; b < 2; ++b)
			SpawnStone();
	}
	//------------------------------------------------------------------------//
	else if (Floor == 40)
	{
		m_bPosition = 1;

		KillAll();

		JumpAll(GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

		ZodiacTime(40, 0, Second);
		ZodiacFloorMessage(40);

		SpawnRegen("data/dungeon/zodiac/zodiac_seller.txt");
		SetFloor(Floor);

		ProcessZodiacItems(true);
	}
	//------------------------------------------------------------------------//
}

//--------------------------------------------------------------------------------------------//

void CZodiac::SetPartyNull()
{
	if (!this)
		return;

	m_pParty = NULL;
}

struct FWarpToZodiac
{
	FWarpToZodiac(long lMapIndex, LPZODIAC z) : m_lMapIndex(lMapIndex), m_pkZodiac(z)
	{
		LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(lMapIndex);
		m_x = pkSectreeMap->m_setting.posSpawn.x;
		m_y = pkSectreeMap->m_setting.posSpawn.y; 
	}

	void operator () (LPCHARACTER ch)
	{
		ch->SaveExitLocation();
		ch->WarpSet(m_x, m_y, m_lMapIndex);
	}

	long m_lMapIndex;
	long m_x;
	long m_y;
	LPZODIAC m_pkZodiac;
};

void CZodiac::Join(LPCHARACTER ch)
{
	if (!this || !ch)
		return;

	if (SECTREE_MANAGER::instance().GetMap(m_lMapIndex) == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FWarpToZodiac(m_lMapIndex, this) (ch);
}

void CZodiac::JoinParty(LPPARTY pParty)
{
	if (!this)
		return;

	if (!pParty)
	{
		sys_err("Cannot Party");
		return;
	}

	pParty->SetZodiac(this);
	m_map_pkParty.insert(std::make_pair(pParty, 0));

	if (SECTREE_MANAGER::instance().GetMap(m_lMapIndex) == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FWarpToZodiac f(m_lMapIndex, this);
	pParty->ForEachOnlineMember(f);
}

void CZodiac::QuitParty(LPPARTY pParty)
{
	if (!this)
		return;

	if (!pParty)
	{
		sys_err("Cannot Party");
		return;
	}

	pParty->SetZodiac(NULL);

	TPartyMap::iterator it = m_map_pkParty.find(pParty);
	if (it != m_map_pkParty.end())
		m_map_pkParty.erase(it);
}

void CZodiac::IncPartyMember(LPPARTY pParty, LPCHARACTER ch)
{
	if (!this || !ch)
		return;

	if (!pParty)
	{
		sys_err("Cannot Party");
		return;
	}

	TPartyMap::iterator it = m_map_pkParty.find(pParty);

	if (it != m_map_pkParty.end())
		it->second++;
	else
		m_map_pkParty.insert(std::make_pair(pParty, 1));

	IncMember(ch);
}

void CZodiac::DecPartyMember(LPPARTY pParty, LPCHARACTER ch)
{
	if (!this || !ch)
		return;

	if (!pParty)
	{
		sys_err("Cannot Party");
		return;
	}

	if (quest::CQuestManager::instance().GetEventFlag("zodiac_disconnect_party") == 1)
		return;

	TPartyMap::iterator it = m_map_pkParty.find(pParty);

	if (it == m_map_pkParty.end())
		sys_err("cannot find party");
	else
	{
		it->second--;

		if (it->second == 0)
			QuitParty(pParty);
	}

	DecMember(ch);
}

void CZodiac::IncMember(LPCHARACTER ch)
{
	if (!this || !ch)
		return;

	if (m_set_pkCharacter.find(ch) == m_set_pkCharacter.end())
		m_set_pkCharacter.insert(ch);

	event_cancel(&deadEvent);
}

EVENTINFO(zodiac_id_info)
{
	CZodiac::IdType zodiac_id;

	zodiac_id_info() : zodiac_id(0)
	{}
};

EVENTFUNC(zodiac_dead_event)
{
	zodiac_id_info* info = dynamic_cast<zodiac_id_info*>(event->info);

	if (info == NULL)
	{
		sys_err("zodiac_dead_event> <Factor> Null pointer");
		return 0;
	}

	LPZODIAC pZodiac = CZodiacManager::instance().Find(info->zodiac_id);
	if (pZodiac == NULL)
	{
		return 0;
	}

	pZodiac->deadEvent = NULL;

	CZodiacManager::instance().Destroy(info->zodiac_id);
	return 0;
}

void CZodiac::DecMember(LPCHARACTER ch)
{
	if (!this || !ch)
		return;

	if (quest::CQuestManager::instance().GetEventFlag("zodiac_disconnect_member") == 1)
		return;

	if (m_set_pkCharacter.empty())
	{
		sys_err("DecMember::La lista ya esta vacia!");

		zodiac_id_info* info = AllocEventInfo<zodiac_id_info>();
		info->zodiac_id = m_id;

		event_cancel(&deadEvent);
		deadEvent = event_create(zodiac_dead_event, info, PASSES_PER_SEC(10));
		return;
	}

	if (quest::CQuestManager::instance().GetEventFlag("zodiac_disconnect_member_2") == 0)
	{
		itertype(m_set_pkCharacter) it = m_set_pkCharacter.find(ch);
		if (it == m_set_pkCharacter.end())
		{
			return;
		}

		m_set_pkCharacter.erase(it);
	}
	else
	{
		for (itertype(m_set_pkCharacter) it = m_set_pkCharacter.begin(); it != m_set_pkCharacter.end(); ++it)
		{
			if (ch == *it)
				m_set_pkCharacter.erase(*it);
		}
	}

	if (m_set_pkCharacter.empty())
	{
		zodiac_id_info* info = AllocEventInfo<zodiac_id_info>();
		info->zodiac_id = m_id;

		event_cancel(&deadEvent);
		deadEvent = event_create(zodiac_dead_event, info, PASSES_PER_SEC(10));
	}
}

//----------------------------------------------------------------------------------------------------//

struct FPolyMonster
{
	long Mob_X, Mob_Y;
	FPolyMonster(long x, long y) : Mob_X(x), Mob_Y(y) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (ch->IsPC() && !ch->IsDead() && !ch->IsPolymorphed())
			{
				if (DISTANCE_APPROX(ch->GetX() - Mob_X, ch->GetY() - Mob_Y) > 1000)
				{
					ch->SetPolymorph(101, false);
				}
			}
		}
	}
};

void CZodiac::PolyCharacter(LPCHARACTER Mob)
{
	if (!this)
		return;

	if (!Mob)
	{
		sys_err("Cannot Mob!");
		return;
	}

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FPolyMonster f(Mob->GetX(), Mob->GetY());
	pkMap->for_each(f);
}

void CZodiac::StartLogin()
{
	if (!this)
		return;

	m_bFloor = 0;
	m_bNextFloor = 0;
	m_bNextFloorControl = false;

	if (zodiac_floor_event_data)
	{
		sys_err("Bug Fixed");
		return;
	}

	Floor_event_data * info = AllocEventInfo<Floor_event_data>();
	info->seconds = 14;
	info->floor = 1;
	info->mapIndex = m_lMapIndex;
	zodiac_floor_event_data = event_create(Floor_event_data_start, info, 1);
}

///////////////////////////////

struct FProcessZodiacItem
{
	bool Enable;
	FProcessZodiacItem(bool e) : Enable(e) {};

	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (ch && ch->IsPC())
			{
				if (Enable)
				{
					for (int i = 1; i <= 22; i++)
					{
						ch->SetZodiacItems(33000+i, 50);
					}

					ch->SetZodiacItems(33032, 200); // Prisma del despertar(Q)
					ch->SetZodiacItems(72329, 1); // Pergamino de esferas
				}
				else
				{
					for (int i = 1; i <= 22; i++)
					{
						ch->SetZodiacItems(33000+i, 0);
						ch->SetPurchaseZodiacItems(33000+i, 0);
					}

					ch->SetZodiacItems(33032, 0); // Prisma del despertar
					ch->SetZodiacItems(72329, 0); // Pergamino de esferas

					ch->SetPurchaseZodiacItems(33032, 0); // Prisma del despertar
					ch->SetPurchaseZodiacItems(72329, 0); // Pergamino de esferas
				}
			}
		}
	}
};

void CZodiac::ProcessZodiacItems(bool enable)
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FProcessZodiacItem f(enable);
	pkMap->for_each(f);
}

struct FNextFloorButton
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				if ((ch->GetParty() && ch->GetParty()->GetLeaderPID() == ch->GetPlayerID()) || !ch->GetParty())
				{
					ch->ChatPacket(CHAT_TYPE_COMMAND, "NextFloorButton");
				}
			}
		}
	}
};

void CZodiac::NextFloorButton()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FNextFloorButton f;
	pkMap->for_each(f);
}

BYTE MobLevels(BYTE Floor)
{
	if (Floor >= 1 && Floor <= 3)
	{
		return number(15, 30);
	}
	if (Floor >= 4 && Floor <= 6)
	{
		return number(30, 45);
	}
	else if (Floor >= 7 && Floor <= 9)
	{
		return number(45, 60);
	}
	else if (Floor >= 10 && Floor <= 12)
	{
		return number(60, 75);
	}
	else if (Floor >= 13 && Floor <= 15)
	{
		return number(75, 80);
	}
	else if (Floor >= 16 && Floor <= 21)
	{
		return number(80, 85);
	}
	else if (Floor >= 22 && Floor <= 28)
	{
		return number(85, 100);
	}
	else if (Floor >= 29 && Floor <= 34)
	{
		return number(100, 135);
	}
	else
		return 0;
}

DWORD GroupMobVnum(BYTE Portal, BYTE Floor) //Setea que se hara en cada piso
{
	if (Portal == 1)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2900;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2901, 2902), MAX(2901, 2902));
			else
				return number(MIN(2900, 2902), MAX(2900, 2902));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2900, 2902), MAX(2900, 2902));
			else
				return number(MIN(2901, 2902), MAX(2901, 2902));
		}
		else
			return 0;
	}
	else if (Portal == 2)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2903;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2904, 2905), MAX(2904, 2905));
			else
				return number(MIN(2903, 2905), MAX(2903, 2905));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2903, 2905), MAX(2903, 2905));
			else
				return number(MIN(2904, 2905), MAX(2904, 2905));
		}
		else
			return 0;
	}
	else if (Portal == 3)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2906;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2907, 2908), MAX(2907, 2908));
			else
				return number(MIN(2906, 2908), MAX(2906, 2908));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2906, 2908), MAX(2906, 2908));
			else
				return number(MIN(2907, 2908), MAX(2907, 2908));
		}
		else
			return 0;
	}
	else if (Portal == 4)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2909;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2910, 2911), MAX(2910, 2911));
			else
				return number(MIN(2909, 2911), MAX(2909, 2911));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2909, 2911), MAX(2909, 2911));
			else
				return number(MIN(2910, 2911), MAX(2910, 2911));
		}
		else
			return 0;
	}
	else if (Portal == 5)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2912;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2913, 2914), MAX(2913, 2914));
			else
				return number(MIN(2912, 2914), MAX(2912, 2914));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2912, 2914), MAX(2912, 2914));
			else
				return number(MIN(2913, 2914), MAX(2913, 2914));
		}
		else
			return 0;
	}
	else if (Portal == 6)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2915;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2916, 2917), MAX(2916, 2917));
			else
				return number(MIN(2915, 2917), MAX(2917, 2917));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2915, 2917), MAX(2915, 2917));
			else
				return number(MIN(2916, 2917), MAX(2916, 2917));
		}
		else
			return 0;
	}
	else if (Portal == 7)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2918;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2919, 2920), MAX(2919, 2920));
			else
				return number(MIN(2918, 2920), MAX(2918, 2920));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2918, 2920), MAX(2918, 2920));
			else
				return number(MIN(2919, 2920), MAX(2919, 2920));
		}
		else
			return 0;
	}
	else if (Portal == 8)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2921;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2922, 2923), MAX(2922, 2923));
			else
				return number(MIN(2921, 2923), MAX(2921, 2923));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2921, 2923), MAX(2921, 2923));
			else
				return number(MIN(2922, 2923), MAX(2922, 2923));
		}
		else
			return 0;
	}
	else if (Portal == 9)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2924;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2925, 2926), MAX(2925, 2926));
			else
				return number(MIN(2924, 2926), MAX(2924, 2926));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2924, 2926), MAX(2924, 2926));
			else
				return number(MIN(2925, 2926), MAX(2925, 2926));
		}
		else
			return 0;
	}
	else if (Portal == 10)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2927;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2928, 2929), MAX(2928, 2929));
			else
				return number(MIN(2927, 2929), MAX(2927, 2929));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2927, 2929), MAX(2927, 2929));
			else
				return number(MIN(2928, 2929), MAX(2928, 2929));
		}
		else
			return 0;
	}
	else if (Portal == 11)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2930;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2936, 2937), MAX(2936, 2937));
			else
				return number(MIN(2930, 2932), MAX(2930, 2932));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2930, 2932), MAX(2930, 2932));
			else
				return number(MIN(2936, 2937), MAX(2936, 2937));
		}
		else
			return 0;
	}
	else if (Portal == 12)
	{
		if (Floor >= 1 && Floor <= 8)
		{
			return 2933;
		}
		else if (Floor >= 9 && Floor <= 20)
		{
			if (number(0, 7) == 4)
				return number(MIN(2934, 2935), MAX(2934, 2935));
			else
				return number(MIN(2933, 2935), MAX(2933, 2935));
		}
		else if (Floor > 20 && Floor <= 39)
		{
			if (number(0, 7) == 4)
				return number(MIN(2933, 2935), MAX(2933, 2935));
			else
				return number(MIN(2934, 2935), MAX(2934, 2935));
		}
		else
			return 0;
	}
	else
		return 0;
}

void CZodiac::SpawnMob()
{
	if (!this)
		return;

	BYTE P = GetPortal();
	BYTE F = GetFloor();
	BYTE N = m_bPosition-1;

	long GetX = SpawnPosition[N][0];
	long GetY = SpawnPosition[N][1];

	GetX *= 100;
	GetY *= 100;

	CHARACTER_MANAGER::instance().SpawnGroupZodiac(GroupMobVnum(P,F), GetMapIndex(), GetX - 2500, GetY - 2500, GetX + 2500, GetY + 2500, NULL, true, this, MobLevels(F));
}

BYTE OfficerLevels(BYTE Floor)
{
	BYTE Level = 50;
	BYTE Dongu = 10;

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

DWORD StatueVnum(BYTE Portal)
{
	if (Portal == 1)
		return 20452; // Estatua del Zi
	else if (Portal == 2)
		return 20453; // Estatua del Chou
	else if (Portal == 3)
		return 20454; // Estatua del Yin
	else if (Portal == 4)
		return 20455; // Estatua del Mao
	else if (Portal == 5)
		return 20456; // Estatua del Chen
	else if (Portal == 6)
		return 20457; // Estatua del Si
	else if (Portal == 7)
		return 20458; // Estatua del Wu
	else if (Portal == 8)
		return 20459; // Estatua del Wei
	else if (Portal == 9)
		return 20460; // Estatua del Shen
	else if (Portal == 10)
		return 20461; // Estatua del Yu
	else if (Portal == 11)
		return 20462; // Estatua del Xu
	else if (Portal == 12)
		return 20463; // Estatua del Hai
	else
		return 0;
}

void CZodiac::SpawnStone(bool Statue)
{
	if (!this)
		return;

	BYTE N = m_bPosition-1;

	long GetX1, GetY1, GetX2, GetY2;

	GetX1 = GetX2 = SpawnPosition[N][0]*100;
	GetY1 = GetY2 = SpawnPosition[N][1]*100;

	GetX1 -= 2200;
	GetY1 -= 2200;

	GetX2 += 2200;
	GetY2 += 2200;

	const CMob* pkMob = NULL;
	DWORD vnum = 0;

	if (Statue == true)
	{
		vnum = StatueVnum(GetPortal());
	}
	else
	{
		vnum = 2900+number(0, 8);

		if (vnum == 2904 || vnum == 2905 || vnum == 2906)
		{
			if (number(0,3) == 1)
				vnum = 2900+number(0, 3);
			else
				vnum = 2900+number(7, 8);
		}
	}

	if ((pkMob = CMobManager::instance().Get(vnum)) == NULL)
		vnum = 0;

	if (vnum != 0 && pkMob != NULL)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().SpawnMobRange(vnum, 
			GetMapIndex(), 
			GetX1 - number(300, 500), 
			GetY1 - number(300, 500), 
			GetX2 + number(300, 500), 
			GetY2 + number(300, 500), 
			true, 
			pkMob->m_table.bType == CHAR_TYPE_STONE,
			false,
			(GetFloor() == 6 || GetFloor() == 7) ? 40 : OfficerLevels(GetFloor()));

		if (ch)
		{
			int newHP = ch->GetMaxHP()+(ch->GetLevel()*5000);
			ch->SetMaxHP(newHP);
			ch->SetHP(newHP);
			ch->UpdatePacket();
		}
	}
}

DWORD BossFuckVnum(BYTE Flag, BYTE Portal)
{
	if (Flag == 0)
	{
		if (Portal == 1)
		{
			return 2750;
		}
		else if (Portal == 2)
		{
			return 2760;
		}
		else if (Portal == 3)
		{
			return 2770;
		}
		else if (Portal == 4)
		{
			return 2780;
		}
		else if (Portal == 5)
		{
			return 2790;
		}
		else if (Portal == 6)
		{
			return 2800;
		}
		else if (Portal == 7)
		{
			return 2810;
		}
		else if (Portal == 8)
		{
			return 2820;
		}
		else if (Portal == 9)
		{
			return 2830;
		}
		else if (Portal == 10)
		{
			return 2840;
		}
		else if (Portal == 11)
		{
			return 2850;
		}
		else if (Portal == 12)
		{
			return 2860;
		}
		else
			return 0;
	}
	else if (Flag == 1)
	{
		if (Portal == 1)
		{
			return 2751;
		}
		else if (Portal == 2)
		{
			return 2761;
		}
		else if (Portal == 3)
		{
			return 2771;
		}
		else if (Portal == 4)
		{
			return 2781;
		}
		else if (Portal == 5)
		{
			return 2791;
		}
		else if (Portal == 6)
		{
			return 2801;
		}
		else if (Portal == 7)
		{
			return 2811;
		}
		else if (Portal == 8)
		{
			return 2821;
		}
		else if (Portal == 9)
		{
			return 2831;
		}
		else if (Portal == 10)
		{
			return 2841;
		}
		else if (Portal == 11)
		{
			return 2851;
		}
		else if (Portal == 12)
		{
			return 2861;
		}
		else
			return 0;
	}
	else if (Flag == 2)
	{
		if (Portal == 1)
		{
			return 2752;
		}
		else if (Portal == 2)
		{
			return 2762;
		}
		else if (Portal == 3)
		{
			return 2772;
		}
		else if (Portal == 4)
		{
			return 2782;
		}
		else if (Portal == 5)
		{
			return 2792;
		}
		else if (Portal == 6)
		{
			return 2802;
		}
		else if (Portal == 7)
		{
			return 2812;
		}
		else if (Portal == 8)
		{
			return 2822;
		}
		else if (Portal == 9)
		{
			return 2832;
		}
		else if (Portal == 10)
		{
			return 2842;
		}
		else if (Portal == 11)
		{
			return 2852;
		}
		else if (Portal == 12)
		{
			return 2862;
		}
		else
			return 0;
	}
	else
		return 0;
}

void CZodiac::SpawnBoss(BYTE Flag)
{
	if (!this)
		return;

	BYTE N = m_bPosition-1;

	long GetX1, GetY1, GetX2, GetY2;

	GetX1 = GetX2 = SpawnPosition[N][0]*100;
	GetY1 = GetY2 = SpawnPosition[N][1]*100;

	GetX1 -= 2200;
	GetY1 -= 2200;

	GetX2 += 2200;
	GetY2 += 2200;

	const CMob* pkMob = NULL;

	DWORD vnum = BossFuckVnum(Flag, GetPortal());

	if ((pkMob = CMobManager::instance().Get(vnum)) == NULL)
		vnum = 0;

	if (vnum != 0 && pkMob != NULL)
	{
		CHARACTER_MANAGER::instance().SpawnMobRange(vnum, 
			GetMapIndex(), 
			GetX1 - number(300, 500), 
			GetY1 - number(300, 500), 
			GetX2 + number(300, 500), 
			GetY2 + number(300, 500), 
			true, 
			true,
			true,
			(GetFloor() == 6 || GetFloor() == 7) ? 40 : OfficerLevels(GetFloor()));
	}
}

///-----------------------------------------------------------------------------------------///

struct FGiveGiftBox
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33033, 1); //Cofre dorado del zodíaco
			}
		}
	}
};

void CZodiac::GiveGiftBox()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftBox f;
	pkMap->for_each(f);
}

struct FGiveGiftZodiacSmall
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33000+number(13, 22), number(2, 6));
			}
		}
	}
};

void CZodiac::GiveGiftZodiacSmall()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftZodiacSmall f;
	pkMap->for_each(f);
}

struct FGiveGiftZodiacMiddle
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33000+number(13, 22), number(6, 15));
			}
		}
	}
};

void CZodiac::GiveGiftZodiacMiddle()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftZodiacMiddle f;
	pkMap->for_each(f);
}

struct FGiveGiftZodiacBig
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33000+number(13, 22), number(15, 30));
			}
		}
	}
};

void CZodiac::GiveGiftZodiacBig()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftZodiacBig f;
	pkMap->for_each(f);
}

struct FGiveGiftZi
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33001, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftZi()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftZi f;
	pkMap->for_each(f);
}

struct FGiveGiftChou
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33002, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftChou()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftChou f;
	pkMap->for_each(f);
}

struct FGiveGiftYin
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33003, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftYin()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftYin f;
	pkMap->for_each(f);
}

struct FGiveGiftMao
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33004, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftMao()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftMao f;
	pkMap->for_each(f);
}

struct FGiveGiftChen
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33005, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftChen()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftChen f;
	pkMap->for_each(f);
}

struct FGiveGiftSi
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33006, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftSi()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftSi f;
	pkMap->for_each(f);
}

struct FGiveGiftWu
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33007, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftWu()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftWu f;
	pkMap->for_each(f);
}

struct FGiveGiftWei
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33008, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftWei()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftWei f;
	pkMap->for_each(f);
}

struct FGiveGiftShen
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33009, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftShen()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftShen f;
	pkMap->for_each(f);
}

struct FGiveGiftYu
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33010, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftYu()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftYu f;
	pkMap->for_each(f);
}

struct FGiveGiftXu
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33011, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftXu()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftXu f;
	pkMap->for_each(f);
}

struct FGiveGiftHai
{
	void operator() (LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER))
		{
			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch)
			{
				sys_err("Cannot ch");
				return;
			}

			if (ch->IsPC())
			{
				ch->AutoGiveItem(33012, number(5, 25)); //Insignia del guardian
			}
		}
	}
};

void CZodiac::GiveGiftHai()
{
	if (!this)
		return;

	LPSECTREE_MAP pkMap = SECTREE_MANAGER::instance().GetMap(m_lMapIndex);
	if (pkMap == NULL)
	{
		sys_err("CZodiac: SECTREE_MAP not found for #%ld", m_lMapIndex);
		return;
	}

	FGiveGiftHai f;
	pkMap->for_each(f);
}
///-----------------------------------------------------------------------------------------///
///-----------------------------------------------------------------------------------------///
///-----------------------------------------------------------------------------------------///

CZodiacManager::CZodiacManager()
	: next_id_(0)
{
}

CZodiacManager::~CZodiacManager()
{
}

#ifdef ENABLE_SERVERTIME_PORTAL_SPAWN
EVENTINFO(TZodiacEventInfo)
{
	CZodiacManager* pInstanceManager;

	TZodiacEventInfo()
		: pInstanceManager(0)
	{
	}
};

EVENTFUNC(zodiac_time_event)
{
	if (!event || !event->info)
		return 0;

	TZodiacEventInfo* info = dynamic_cast<TZodiacEventInfo*>(event->info);

	if (!info)
		return 0;

	CZodiacManager* pInstanceManager = info->pInstanceManager;

	if (!pInstanceManager)
		return 0;

	// ZODIAK: portale dnia od razu po starcie rdzenia (serwer nie dziala caly czas, a paczka stawia je tylko o 00:00)
	static bool s_bPierwszy = true;
	if (s_bPierwszy)
	{
		s_bPierwszy = false;
		pInstanceManager->Spawn();
		sys_log(0, "[ZODIAC] Portals spawned at start");
	}

	if (pInstanceManager->GetIsDaily())
	{
		pInstanceManager->Spawn();
		sys_log(0, "[ZODIAC] Spawn function after IsDaily accomplished!");
		return PASSES_PER_SEC(5);
	}

	return PASSES_PER_SEC(1);
}

bool CZodiacManager::Initialize()
{
	// ZODIAK: w paczce kanal 99; u nas timer startuje na rdzeniu, ktory hostuje mape 358 (game1), a funkcja zwraca wartosc
	if (map_allow_find(MAP_INDEX))
	{
		TZodiacEventInfo* info = AllocEventInfo<TZodiacEventInfo>();
		info->pInstanceManager = this;
		zodiac_spawn_timer = event_create(zodiac_time_event, info, PASSES_PER_SEC(40));
		sys_log(0, "[ZODIAC] Initialize worked!");
	}

	return true;
}

int CZodiacManager::GetCurrentDay()
{
	time_t ct = get_global_time();
	struct tm tm = *localtime(&ct);

	switch (tm.tm_wday)
	{
		case 0:
			return ZC_SUNDAY;
		case 1:
			return ZC_MONDAY;
		case 2:
			return ZC_TUESDAY;
		case 3:
			return ZC_WEDNESDAY;
		case 4:
			return ZC_THURSDAY;
		case 5:
			return ZC_FRIDAY;
		case 6:
			return ZC_SATURDAY;
	}

	return ZC_SUNDAY;
}

bool CZodiacManager::GetIsDaily()
{
	time_t ct = get_global_time();
	struct tm tm = *localtime(&ct);

	int dwArray[4] = { GetCurrentDay(), 0, 0, 0 };
	return (tm.tm_wday == dwArray[TIME_DAY] && tm.tm_hour == dwArray[TIME_HOUR] && tm.tm_min == dwArray[TIME_MIN] && (tm.tm_sec == dwArray[TIME_SEC] || tm.tm_sec == 0));
}

bool CZodiacManager::Spawn()
{
	int portal_vnum[] = { 20439, 20440, 20441, 20442, 20443, 20444, 20445, 20446, 20447, 20448, 20449, 20450 };

	CharacterVectorInteractor i;

	//delete if exist
	for (int a = 0; a < _countof(portal_vnum); a++)
	{
		if (CHARACTER_MANAGER::instance().GetCharactersByRaceNum(portal_vnum[a], i))
		{
			CharacterVectorInteractor::iterator it = i.begin();

			while (it != i.end())
			{
				sys_log(0, "[ZODIAC] Portals found and deleted!");
				M2_DESTROY_CHARACTER(*it++);
			}
		}
	}

	//respawn
	if (map_allow_find(MAP_INDEX))
	{
		PIXEL_POSITION posBase;
		if (!SECTREE_MANAGER::instance().GetMapBasePositionByMapIndex(MAP_INDEX, posBase))
		{
			sys_err("cannot get map base position %d", MAP_INDEX);
			return false;
		}

		// MT2009_PLUS_ZODIAC_RUNS_V1: the operator's switch (event flag zodiac_all_portals, the test's
		// "allportals 1" in playerbot_zodiac_test): every portal every day, as on a Sunday.
		if (quest::CQuestManager::instance().GetEventFlag("zodiac_all_portals") != 0)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/7-sunday.txt");
			sys_log(0, "[ZODIAC] ALL PORTALS (zodiac_all_portals) spawned: 20439 - 20450");
		}
		else if (GetCurrentDay() == ZC_MONDAY) //(Zi - Chou)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/1-monday.txt");
			sys_log(0, "[ZODIAC] MONDAY spawned: 20439, 20440");
		}
		else if (GetCurrentDay() == ZC_TUESDAY) //(Yin-Mao)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/2-tuesday.txt");
			sys_log(0, "[ZODIAC] TUESDAY spawned: 20441, 20442");
		}
		else if (GetCurrentDay() == ZC_WEDNESDAY) //(Chen-Si)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/3-wednesday.txt");
			sys_log(0, "[ZODIAC] WEDNESDAY spawned: 20443, 20444");
		}
		else if (GetCurrentDay() == ZC_THURSDAY) //(Wu-Wei)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/4-thursday.txt");
			sys_log(0, "[ZODIAC] THURSDAY spawned: 20445, 20446");
		}
		else if (GetCurrentDay() == ZC_FRIDAY) //(Shen-Yu)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/5-friday.txt");
			sys_log(0, "[ZODIAC] FRIDAY spawned: 20447, 20448");
		}
		else if (GetCurrentDay() == ZC_SATURDAY) //(Xu-Hai)
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/6-saturday.txt");
			sys_log(0, "[ZODIAC] SATURDAY spawned: 20449, 20450");
		}
		else if (GetCurrentDay() == ZC_SUNDAY) //All
		{
			CZodiac::SpawnRegenZodiac("data/dungeon/zodiac/days/7-sunday.txt");
			sys_log(0, "[ZODIAC] SUNDAY spawned: 20439 - 20450");
		}
		else
		{
			sys_log(0, "[ZODIAC] weekday out of range!");
		}

		return true;
	}

	return false;
}
#endif

LPZODIAC CZodiacManager::Create(BYTE bPortal)
{
	DWORD lMapIndex = SECTREE_MANAGER::instance().CreatePrivateMap(MAP_INDEX);

	if (!lMapIndex) 
	{
		sys_log( 0, "Fail to Create Zodiac : OrginalMapindex %d NewMapindex %d", MAP_INDEX, lMapIndex );
		return NULL;
	}

	CZodiac::IdType id = next_id_++;
	while (Find(id) != NULL)
	{
		id = next_id_++;
	}

	sys_err("New Map Index:: %u, Zodiac Id:: %u", lMapIndex, id);

	LPZODIAC pZodiac = M2_NEW CZodiac(id, lMapIndex, bPortal);
	if (!pZodiac)
	{
		sys_err("M2_NEW CZodiac failed");
		return NULL;
	}

	m_map_pkZodiac.insert(std::make_pair(id, pZodiac));
	m_map_pkMapZodiac.insert(std::make_pair(lMapIndex, pZodiac));

	return pZodiac;
}

void CZodiacManager::Destroy(CZodiac::IdType zodiac_id)
{
	LPZODIAC pZodiac = Find(zodiac_id);
	if (pZodiac == NULL)
	{
		return;
	}

	sys_log(0, "ZODIAC destroy : map index %u", zodiac_id);

	if (pZodiac->zodiac_floor_event_data)
		event_cancel(&pZodiac->zodiac_floor_event_data);

	if (pZodiac->zodiac_remaining_time_temple_floor)
		event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);

	if (pZodiac->zodiac_exit_temple_event_data)
		event_cancel(&pZodiac->zodiac_exit_temple_event_data);

	m_map_pkZodiac.erase(zodiac_id);

	long lMapIndex = pZodiac->m_lMapIndex;
	m_map_pkMapZodiac.erase(lMapIndex);

	DWORD server_timer_arg = lMapIndex;
	quest::CQuestManager::instance().CancelServerTimers(server_timer_arg);

	SECTREE_MANAGER::instance().DestroyPrivateMap(lMapIndex);
	M2_DELETE(pZodiac);
}

LPZODIAC CZodiacManager::Find(CZodiac::IdType zodiac_id)
{
	itertype(m_map_pkZodiac) it = m_map_pkZodiac.find(zodiac_id);
	if (it != m_map_pkZodiac.end())
		return it->second;

	return NULL;
}

LPZODIAC CZodiacManager::FindByMapIndex(long lMapIndex)
{
	itertype(m_map_pkMapZodiac) it = m_map_pkMapZodiac.find(lMapIndex);
	if (it != m_map_pkMapZodiac.end())
	{
		return it->second;
	}

	return NULL;
}

void CZodiacManager::StartTemple(LPCHARACTER pkChar, BYTE portal)
{
	if (!pkChar)
	{
		sys_err("Cannot LPCHARACTER");
		return;
	}

	LPZODIAC pZodiac = Create(portal);
	if (!pZodiac)
	{
		sys_err("cannot create zodiac %d", MAP_INDEX);
		return;
	}

	if (pkChar->GetParty() != NULL)
		pZodiac->JumpParty(pkChar->GetParty(), pkChar->GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);
	else
		pZodiac->Jump(pkChar, pkChar->GetMapIndex(), GoToPosition[0][0], GoToPosition[0][1]);

	if (portal > 0)
	{
		pZodiac->m_bPortal = portal;
		pZodiac->StartLogin();
	}
	else
		pZodiac->ExitTemple();
}

void CZodiacManager::DeadMob(LPCHARACTER Mob, DWORD mapIndex)
{
	if (!Mob)
	{
		sys_err("Cannot Monster");
		return;
	}

	if (!Mob->IsZodiacBoss() && !Mob->IsStone() && !Mob->IsMonster())
	{
		sys_err("Cannot mob or boss");
		return;
	}

	if (!mapIndex)
	{
		sys_err("Cannot mapIndex");
		return;
	}

	LPZODIAC pZodiac = FindByMapIndex(mapIndex);
	if (!pZodiac)
	{
		sys_err("cannot create zodiac %d", mapIndex);
		return;
	}

	// MT2009_PLUS_ZODIAC_ITEMS_V1: Zlota Skrzynia Zodiaku from the temple's main boss - its sign's General (27x2,
	// BossFuckVnum flag 2: the last boss, floor 34) - for everybody on the floor, bots too (the owner, 9 October;
	// the package had GiveGiftBox and never called it). The chest's group: special_item_group.zodiak.txt.
	if (Mob->IsZodiacBoss() && Mob->GetRaceNum() == BossFuckVnum(2, pZodiac->GetPortal()))
	{
		pZodiac->GiveGiftBox();
		sys_log(0, "[ZODIAC] boss %u killed map=%ld portal=%u: Zlota Skrzynia given", Mob->GetRaceNum(), (long)mapIndex,
				(unsigned int)pZodiac->GetPortal());
	}

	if (pZodiac->zodiac_floor_event_data || pZodiac->zodiac_exit_temple_event_data)
	{
		sys_err("Bug Fixed");
		return;
	}

	BYTE Floor = pZodiac->GetFloor();

	if (Floor >= 40)
	{
		sys_err("Now Floor 40");
		return;
	}

	if (Floor != 7 && 
		Floor != 8 && 
		Floor != 11 && 
		Floor != 13 && 
		Floor != 14 && 
		Floor != 15 && 
		Floor != 17 && 
		Floor != 18 && 
		Floor != 21 && 
		Floor != 22 && 
		Floor != 27 && 
		Floor != 28 && 
		Floor != 29 && 
		Floor != 30 && 
		Floor != 34 && 
		Floor != 35 && 
		Floor != 36 && 
		Floor != 37 && 
		Floor != 38 && 
		Floor != 39
		)
		return;

	int Boss = pZodiac->CountIsBoss()-1;
	int Stone = pZodiac->CountIsStone()-1;
	int Mobb = 0;

	if (Floor == 11 || Floor == 22)
	{
		if (Mob->IsZodiacBoss())
		{
			Boss = --pZodiac->m_iBossKill;
			if (Boss > 0)
			{
				char szText[32+1];
				snprintf(szText, sizeof(szText), "(%d/%d)", pZodiac->m_iTotalMonster-Boss, pZodiac->m_iTotalMonster);
				pZodiac->ZodiacFloorSubMessage(szText);
				return;
			}
			else
			{
				pZodiac->SetFloor(Floor);
				if (Floor == 11)
				{
					if (number(1, 10) <= 4)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacSmall();

					if ((get_global_time() - pZodiac->GetTime()) <= 60)
					{
						Floor = 13;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(11, 2, 10); //11F + 2F_Jumps = 13F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 120)
					{
						Floor = 12;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(11, 1, 10); //11F + 1F_Jumps = 12F
						pZodiac->NextFloorButton();
						return;
					}
				}
				else if (Floor == 22)
				{
					if (number(1, 10) <= 5)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacMiddle();

					if ((get_global_time() - pZodiac->GetTime()) <= 60)
					{
						Floor = 27;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(22, 5, 10); //22F + 5F_Jumps = 27F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 120)
					{
						Floor = 26;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(22, 4, 10); //22F + 4F_Jumps = 26F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 180)
					{
						Floor = 25;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(22, 3, 10); //22F + 3F_Jumps = 25F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 240)
					{
						Floor = 24;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(22, 2, 10); //22F + 2F_Jumps = 24F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 300)
					{
						Floor = 23;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(22, 1, 10); //22F + 1F_Jumps = 23F
						pZodiac->NextFloorButton();
						return;
					}
				}
			}
		}
		else
			return;
	}
	else if (Floor == 17)
	{
		if (!Mob->IsZodiacBoss())
		{
			return;
		}

		pZodiac->SetFloor(Floor);
		if (number(1, 10) <= 5)
		{
			if (pZodiac->GetPortal() == 1)
				pZodiac->GiveGiftZi();
			else if (pZodiac->GetPortal() == 2)
				pZodiac->GiveGiftChou();
			else if (pZodiac->GetPortal() == 3)
				pZodiac->GiveGiftYin();
			else if (pZodiac->GetPortal() == 4)
				pZodiac->GiveGiftMao();
			else if (pZodiac->GetPortal() == 5)
				pZodiac->GiveGiftChen();
			else if (pZodiac->GetPortal() == 6)
				pZodiac->GiveGiftSi();
			else if (pZodiac->GetPortal() == 7)
				pZodiac->GiveGiftWu();
			else if (pZodiac->GetPortal() == 8)
				pZodiac->GiveGiftWei();
			else if (pZodiac->GetPortal() == 9)
				pZodiac->GiveGiftShen();
			else if (pZodiac->GetPortal() == 10)
				pZodiac->GiveGiftYu();
			else if (pZodiac->GetPortal() == 11)
				pZodiac->GiveGiftXu();
			else if (pZodiac->GetPortal() == 12)
				pZodiac->GiveGiftHai();
		}
		else
			pZodiac->GiveGiftZodiacMiddle();

		if ((get_global_time() - pZodiac->GetTime()) <= 60)
		{
			Floor = 20;

			if (pZodiac->zodiac_remaining_time_temple_floor)
			{
				event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
				pZodiac->zodiac_remaining_time_temple_floor = NULL;
			}

			pZodiac->m_bNextFloor = Floor;
			pZodiac->m_bNextFloorControl = true;

			pZodiac->ZodiacMessageMission(Floor);
			pZodiac->ZodiacTime(17, 3, 10); //17F + 3F_Jumps = 20F
			pZodiac->NextFloorButton();
			return;
		}
		else if ((get_global_time() - pZodiac->GetTime()) <= 120)
		{
			Floor = 19;

			if (pZodiac->zodiac_remaining_time_temple_floor)
			{
				event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
				pZodiac->zodiac_remaining_time_temple_floor = NULL;
			}

			pZodiac->m_bNextFloor = Floor;
			pZodiac->m_bNextFloorControl = true;

			pZodiac->ZodiacMessageMission(Floor);
			pZodiac->ZodiacTime(17, 2, 10); //17F + 2F_Jumps = 19F
			pZodiac->NextFloorButton();
			return;
		}
		else if ((get_global_time() - pZodiac->GetTime()) <= 180)
		{
			Floor = 18;

			if (pZodiac->zodiac_remaining_time_temple_floor)
			{
				event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
				pZodiac->zodiac_remaining_time_temple_floor = NULL;
			}

			pZodiac->m_bNextFloor = Floor;
			pZodiac->m_bNextFloorControl = true;

			pZodiac->ZodiacMessageMission(Floor);
			pZodiac->ZodiacTime(17, 1, 10); //17F + 1F_Jumps = 18F
			pZodiac->NextFloorButton();
			return;
		}
	}
	else if (Floor == 8 || Floor == 13 || Floor == 14 || Floor == 18 || Floor == 27 || Floor == 28 || Floor == 29 || Floor == 30)
	{
		if (Mob->IsStone())
		{
			Stone = --pZodiac->m_iStoneKill;
			if (Stone > 0)
			{
				char szText[32+1];
				if (Floor == 13 || Floor == 14 || Floor == 28 || Floor == 29 || Floor == 30)
				{
					snprintf(szText, sizeof(szText), "(%d/%d)", pZodiac->m_iTotalMonster-Stone, pZodiac->m_iTotalMonster);
					pZodiac->ZodiacFloorSubMessage(szText);
				}
				else
				{
					snprintf(szText, sizeof(szText), "(%d)", Stone);
					pZodiac->ZodiacFloorSubMessage(szText);
				}

				return;
			}
			else
			{
				pZodiac->SetFloor(Floor);
				if (Floor == 14 || Floor == 28)
				{
					if (pZodiac->GetPortal() == 1)
						pZodiac->GiveGiftZi();
					else if (pZodiac->GetPortal() == 2)
						pZodiac->GiveGiftChou();
					else if (pZodiac->GetPortal() == 3)
						pZodiac->GiveGiftYin();
					else if (pZodiac->GetPortal() == 4)
						pZodiac->GiveGiftMao();
					else if (pZodiac->GetPortal() == 5)
						pZodiac->GiveGiftChen();
					else if (pZodiac->GetPortal() == 6)
						pZodiac->GiveGiftSi();
					else if (pZodiac->GetPortal() == 7)
						pZodiac->GiveGiftWu();
					else if (pZodiac->GetPortal() == 8)
						pZodiac->GiveGiftWei();
					else if (pZodiac->GetPortal() == 9)
						pZodiac->GiveGiftShen();
					else if (pZodiac->GetPortal() == 10)
						pZodiac->GiveGiftYu();
					else if (pZodiac->GetPortal() == 11)
						pZodiac->GiveGiftXu();
					else if (pZodiac->GetPortal() == 12)
						pZodiac->GiveGiftHai();
				}
				else if (Floor == 13)
				{
					if (number(1, 10) <= 4)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacSmall();
				}
				else if (Floor == 27)
				{
					if (number(1, 10) <= 7)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacBig();
				}

				if (Floor == 8)
				{
					if (number(1, 10) <= 4)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacSmall();

					if ((get_global_time() - pZodiac->GetTime()) <= 60)
					{
						Floor = 13;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(8, 5, 10); //8F + 5F_Jumps = 13F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 120)
					{
						Floor = 12;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(8, 4, 10); //8F + 4F_Jumps = 12F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 180)
					{
						Floor = 11;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(8, 3, 10); //8F + 3F_Jumps = 11F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 240)
					{
						Floor = 10;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(8, 2, 10); //8F + 2F_Jumps = 10F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 300)
					{
						Floor = 9;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(8, 1, 10); //8F + 1F_Jumps = 9F
						pZodiac->NextFloorButton();
						return;
					}
				}

				else if (Floor == 18)
				{
					if (number(1, 10) <= 5)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacMiddle();

					if ((get_global_time() - pZodiac->GetTime()) <= 60)
					{
						Floor = 20;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(18, 2, 10); //18F + 2F_Jumps = 20F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 120)
					{
						Floor = 19;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(18, 1, 10); //18F + 1F_Jumps = 19F
						pZodiac->NextFloorButton();
						return;
					}
				}

				else if (Floor == 29)
				{
					if (number(1, 10) <= 7)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacBig();

					if ((get_global_time() - pZodiac->GetTime()) <= 60)
					{
						Floor = 34;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(29, 5, 10); //29F + 5F_Jumps = 34F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 120)
					{
						Floor = 33;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(29, 4, 10); //29F + 4F_Jumps = 33F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 180)
					{
						Floor = 32;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(29, 3, 10); //29F + 3F_Jumps = 32F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 240)
					{
						Floor = 31;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(29, 2, 10); //29F + 2F_Jumps = 31F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 300)
					{
						Floor = 30;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(29, 1, 10); //29F + 1F_Jumps = 30F
						pZodiac->NextFloorButton();
						return;
					}
				}
				else if (Floor == 30)
				{
					if (number(1, 10) <= 7)
					{
						if (pZodiac->GetPortal() == 1)
							pZodiac->GiveGiftZi();
						else if (pZodiac->GetPortal() == 2)
							pZodiac->GiveGiftChou();
						else if (pZodiac->GetPortal() == 3)
							pZodiac->GiveGiftYin();
						else if (pZodiac->GetPortal() == 4)
							pZodiac->GiveGiftMao();
						else if (pZodiac->GetPortal() == 5)
							pZodiac->GiveGiftChen();
						else if (pZodiac->GetPortal() == 6)
							pZodiac->GiveGiftSi();
						else if (pZodiac->GetPortal() == 7)
							pZodiac->GiveGiftWu();
						else if (pZodiac->GetPortal() == 8)
							pZodiac->GiveGiftWei();
						else if (pZodiac->GetPortal() == 9)
							pZodiac->GiveGiftShen();
						else if (pZodiac->GetPortal() == 10)
							pZodiac->GiveGiftYu();
						else if (pZodiac->GetPortal() == 11)
							pZodiac->GiveGiftXu();
						else if (pZodiac->GetPortal() == 12)
							pZodiac->GiveGiftHai();
					}
					else
						pZodiac->GiveGiftZodiacBig();

					if ((get_global_time() - pZodiac->GetTime()) <= 60)
					{
						Floor = 34;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(30, 4, 10); //30F + 4F_Jumps = 34F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 120)
					{
						Floor = 33;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(30, 3, 10); //30F + 3F_Jumps = 33F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 180)
					{
						Floor = 32;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(30, 2, 10); //30F + 2F_Jumps = 32F
						pZodiac->NextFloorButton();
						return;
					}
					else if ((get_global_time() - pZodiac->GetTime()) <= 240)
					{
						Floor = 31;

						if (pZodiac->zodiac_remaining_time_temple_floor)
						{
							event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
							pZodiac->zodiac_remaining_time_temple_floor = NULL;
						}

						pZodiac->m_bNextFloor = Floor;
						pZodiac->m_bNextFloorControl = true;

						pZodiac->ZodiacMessageMission(Floor);
						pZodiac->ZodiacTime(30, 1, 10); //30F + 1F_Jumps = 31F
						pZodiac->NextFloorButton();
						return;
					}
				}

			}
		}
		else
			return;
	}
	else if (Floor == 15)
	{
		Mobb = --pZodiac->m_iMobKill;
		if (Mobb > 0)
		{
			char szText[32+1];
			snprintf(szText, sizeof(szText), "(%d)", Mobb);
			pZodiac->ZodiacFloorSubMessage(szText);
			return;
		}
		else
		{
			pZodiac->SetFloor(Floor);
			if (number(1, 10) <= 5)
			{
				if (pZodiac->GetPortal() == 1)
					pZodiac->GiveGiftZi();
				else if (pZodiac->GetPortal() == 2)
					pZodiac->GiveGiftChou();
				else if (pZodiac->GetPortal() == 3)
					pZodiac->GiveGiftYin();
				else if (pZodiac->GetPortal() == 4)
					pZodiac->GiveGiftMao();
				else if (pZodiac->GetPortal() == 5)
					pZodiac->GiveGiftChen();
				else if (pZodiac->GetPortal() == 6)
					pZodiac->GiveGiftSi();
				else if (pZodiac->GetPortal() == 7)
					pZodiac->GiveGiftWu();
				else if (pZodiac->GetPortal() == 8)
					pZodiac->GiveGiftWei();
				else if (pZodiac->GetPortal() == 9)
					pZodiac->GiveGiftShen();
				else if (pZodiac->GetPortal() == 10)
					pZodiac->GiveGiftYu();
				else if (pZodiac->GetPortal() == 11)
					pZodiac->GiveGiftXu();
				else if (pZodiac->GetPortal() == 12)
					pZodiac->GiveGiftHai();
			}
			else
				pZodiac->GiveGiftZodiacMiddle();

			if ((get_global_time() - pZodiac->GetTime()) <= 60)
			{
				Floor = 20;

				pZodiac->KillAll();

				if (pZodiac->zodiac_remaining_time_temple_floor)
				{
					event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
					pZodiac->zodiac_remaining_time_temple_floor = NULL;
				}

				pZodiac->m_bNextFloor = Floor;
				pZodiac->m_bNextFloorControl = true;

				pZodiac->ZodiacMessageMission(Floor);
				pZodiac->ZodiacTime(15, 5, 10); //15F + 5F_Jumps = 20F
				pZodiac->NextFloorButton();
				return;
			}
			else if ((get_global_time() - pZodiac->GetTime()) <= 120)
			{
				Floor = 19;

				pZodiac->KillAll();

				if (pZodiac->zodiac_remaining_time_temple_floor)
				{
					event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
					pZodiac->zodiac_remaining_time_temple_floor = NULL;
				}

				pZodiac->m_bNextFloor = Floor;
				pZodiac->m_bNextFloorControl = true;

				pZodiac->ZodiacMessageMission(Floor);
				pZodiac->ZodiacTime(15, 4, 10); //15F + 4F_Jumps = 19F
				pZodiac->NextFloorButton();
				return;
			}
			else if ((get_global_time() - pZodiac->GetTime()) <= 180)
			{
				Floor = 18;

				pZodiac->KillAll();

				if (pZodiac->zodiac_remaining_time_temple_floor)
				{
					event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
					pZodiac->zodiac_remaining_time_temple_floor = NULL;
				}

				pZodiac->m_bNextFloor = Floor;
				pZodiac->m_bNextFloorControl = true;

				pZodiac->ZodiacMessageMission(Floor);
				pZodiac->ZodiacTime(15, 3, 10); //15F + 3F_Jumps = 18F
				pZodiac->NextFloorButton();
				return;
			}
			else if ((get_global_time() - pZodiac->GetTime()) <= 240)
			{
				Floor = 17;

				pZodiac->KillAll();

				if (pZodiac->zodiac_remaining_time_temple_floor)
				{
					event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
					pZodiac->zodiac_remaining_time_temple_floor = NULL;
				}

				pZodiac->m_bNextFloor = Floor;
				pZodiac->m_bNextFloorControl = true;

				pZodiac->ZodiacMessageMission(Floor);
				pZodiac->ZodiacTime(15, 2, 10); //15F + 2F_Jumps = 17F
				pZodiac->NextFloorButton();
				return;
			}
			else if ((get_global_time() - pZodiac->GetTime()) <= 300)
			{
				Floor = 16;

				pZodiac->KillAll();

				if (pZodiac->zodiac_remaining_time_temple_floor)
				{
					event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
					pZodiac->zodiac_remaining_time_temple_floor = NULL;
				}

				pZodiac->m_bNextFloor = Floor;
				pZodiac->m_bNextFloorControl = true;

				pZodiac->ZodiacMessageMission(Floor);
				pZodiac->ZodiacTime(15, 1, 10); //15F + 1F_Jumps = 16F
				pZodiac->NextFloorButton();
				return;
			}
		}
	}
	else if (Floor == 34)
	{
		if (!Mob->IsStone() && !Mob->IsZodiacBoss())
		{
			Mobb = --pZodiac->m_iMobKill;
			if (Mobb > 0)
			{
				char szText[32+1];
				snprintf(szText, sizeof(szText), "(%d)", Mobb);
				pZodiac->ZodiacFloorSubMessage(szText);
				return;
			}
			else
			{
				if (pZodiac->GetFlag("34boss") == 0)
				{
					pZodiac->SetFlag("34boss", 1);

					pZodiac->KillAll();

					pZodiac->SpawnBoss(2);

					pZodiac->ZodiacFloorMessage(17);
					pZodiac->ZodiacFloorSubMessage("(1)");
				}

				return;
			}
		}
		else if (Mob->IsZodiacBoss())
		{
			Boss = --pZodiac->m_iBossKill;
			if (Boss > 0)
			{
				return;
			}
			else
			{
				pZodiac->SetFloor(Floor);
				pZodiac->GiveGiftBox();
			}
		}
		else
			return;
	}
	else if (Floor == 7 || Floor == 21)
	{
		if (Mob->IsStone() && pZodiac->GetFlag("bonus") == 0)
		{
			pZodiac->SetFlag("bonus", 1);

			pZodiac->KillAll();

			for (BYTE b = 0; b < 2; ++b)
				pZodiac->SpawnStone();

			return;
		}
	}
	else if (Floor >= 35 && Floor < 40)
	{
		pZodiac->SetFloor(Floor);
		if (number(1, 7) == 4)
		{
			pZodiac->KillAll();

			if (pZodiac->zodiac_remaining_time_temple_floor)
			{
				event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
				pZodiac->zodiac_remaining_time_temple_floor = NULL;
			}

			pZodiac->ZodiacMessageMission(40);
			pZodiac->ZodiacTime(Floor-1, 40-(Floor-1), 10);

			pZodiac->m_bNextFloor = 40;
			pZodiac->m_bNextFloorControl = true;
			pZodiac->NextFloorButton();

			if (pZodiac->GetPortal() == 1)
				pZodiac->GiveGiftZi();
			else if (pZodiac->GetPortal() == 2)
				pZodiac->GiveGiftChou();
			else if (pZodiac->GetPortal() == 3)
				pZodiac->GiveGiftYin();
			else if (pZodiac->GetPortal() == 4)
				pZodiac->GiveGiftMao();
			else if (pZodiac->GetPortal() == 5)
				pZodiac->GiveGiftChen();
			else if (pZodiac->GetPortal() == 6)
				pZodiac->GiveGiftSi();
			else if (pZodiac->GetPortal() == 7)
				pZodiac->GiveGiftWu();
			else if (pZodiac->GetPortal() == 8)
				pZodiac->GiveGiftWei();
			else if (pZodiac->GetPortal() == 9)
				pZodiac->GiveGiftShen();
			else if (pZodiac->GetPortal() == 10)
				pZodiac->GiveGiftYu();
			else if (pZodiac->GetPortal() == 11)
				pZodiac->GiveGiftXu();
			else if (pZodiac->GetPortal() == 12)
				pZodiac->GiveGiftHai();

			return;
		}
	}

	pZodiac->KillAll();

	if (pZodiac->zodiac_remaining_time_temple_floor)
	{
		event_cancel(&pZodiac->zodiac_remaining_time_temple_floor);
		pZodiac->zodiac_remaining_time_temple_floor = NULL;
	}

	if (Floor == 7 || Floor == 21)
	{
		pZodiac->SetFloor(Floor);
		if (number(0, 50) == 15)
		{
			pZodiac->ZodiacMessageMission(Floor);
			if (pZodiac->GetPortal() == 1)
				pZodiac->GiveGiftZi();
			else if (pZodiac->GetPortal() == 2)
				pZodiac->GiveGiftChou();
			else if (pZodiac->GetPortal() == 3)
				pZodiac->GiveGiftYin();
			else if (pZodiac->GetPortal() == 4)
				pZodiac->GiveGiftMao();
			else if (pZodiac->GetPortal() == 5)
				pZodiac->GiveGiftChen();
			else if (pZodiac->GetPortal() == 6)
				pZodiac->GiveGiftSi();
			else if (pZodiac->GetPortal() == 7)
				pZodiac->GiveGiftWu();
			else if (pZodiac->GetPortal() == 8)
				pZodiac->GiveGiftWei();
			else if (pZodiac->GetPortal() == 9)
				pZodiac->GiveGiftShen();
			else if (pZodiac->GetPortal() == 10)
				pZodiac->GiveGiftYu();
			else if (pZodiac->GetPortal() == 11)
				pZodiac->GiveGiftXu();
			else if (pZodiac->GetPortal() == 12)
				pZodiac->GiveGiftHai();
		}
		else
		{
			pZodiac->ZodiacFloorMessage(42);
		}
	}

	Floor += 1;

	if (Floor == 40)
	{
		pZodiac->ZodiacFloorMessage(41);
		pZodiac->ZodiacTime(Floor, 0, 10);

		Exit_temple_event_data * info = AllocEventInfo<Exit_temple_event_data>();
		info->seconds = 10;
		info->mapIndex = pZodiac->GetMapIndex();
		pZodiac->zodiac_exit_temple_event_data = event_create(Exit_temple_event_data_start, info, 1);
		return;
	}

	pZodiac->m_bNextFloor = Floor;
	pZodiac->m_bNextFloorControl = true;

	if (Floor != 8 && Floor != 22)
		pZodiac->ZodiacMessageMission(Floor);

	pZodiac->ZodiacTime(Floor-1, 1, 10);
	pZodiac->NextFloorButton();
}

void CZodiacManager::DeadPC(DWORD mapIndex)
{
	if (!mapIndex)
	{
		sys_err("Cannot mapIndex");
		return;
	}

	LPZODIAC pZodiac = FindByMapIndex(mapIndex);
	if (!pZodiac)
	{
		sys_err("cannot create zodiac %d", mapIndex);
		return;
	}

	BYTE Floor = pZodiac->GetFloor();

	if (Floor == 6 || Floor == 12 || Floor == 19 || Floor == 24) //Special Floors, the death of a member of the group supposes the expulsion of the whole group.
	{
		if (pZodiac->zodiac_exit_temple_event_data)
			return;

		pZodiac->KillAll();

		pZodiac->ZodiacFloorMessage(41);
		pZodiac->ZodiacTime(Floor, 1, 10);

		Exit_temple_event_data * info = AllocEventInfo<Exit_temple_event_data>();
		info->seconds = 10;
		info->mapIndex = pZodiac->GetMapIndex();
		pZodiac->zodiac_exit_temple_event_data = event_create(Exit_temple_event_data_start, info, 1);
	}
	// else
		// ChatPacket(CHAT_TYPE_BIG_NOTICE, LC_TEXT("Eliminados! Vuestro tiempo en la mazmorra concluye si nadie revive en el plazo de un minuto."));
}
#endif // ENABLE_12ZI
