// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
#ifndef __INC_METIN_II_GAME_ZODIAC_H
#define __INC_METIN_II_GAME_ZODIAC_H

#include "dungeon.h"
#include <boost/unordered_map.hpp>
#include "sectree_manager.h"
#include "../../common/CommonDefines.h"

#ifdef ENABLE_12ZI
// #include "../../common/service.h"

enum eConfig
{
	MAP_INDEX = 358,
};

#ifdef ENABLE_SERVERTIME_PORTAL_SPAWN
enum EPortalSpawn
{
	ZC_MONDAY = 1,
	ZC_TUESDAY = 2,
	ZC_WEDNESDAY = 3,
	ZC_THURSDAY = 4,
	ZC_FRIDAY = 5,
	ZC_SATURDAY = 6,
	ZC_SUNDAY = 0,
};

enum EZodiacZonePadders
{
	TIME_DAY,
	TIME_HOUR,
	TIME_MIN,
	TIME_SEC
};

class CZodiac : public singleton<CZodiac>
#else
class CZodiac
#endif
{
	typedef TR1_NS::unordered_map<LPPARTY, int> TPartyMap;
	typedef std::map<std::string, LPCHARACTER> TUniqueMobMap;

	public:
		typedef uint32_t IdType;

		~CZodiac();

		IdType GetId() const { return m_id; }

		void	SetFloor(BYTE completedFloor);
		void	SetFlag(std::string name, int value);
		int		GetFlag(std::string name);

		void	Jump(LPCHARACTER ch, long lFromMapIndex, int x, int y);
		void	JumpAll(long lFromMapIndex, int x, int y);
		void	JumpParty(LPPARTY pParty, long lFromMapIndex, int x, int y);

		void	SpawnRegen(const char* filename, bool bOnce = true);
#ifdef ENABLE_SERVERTIME_PORTAL_SPAWN
		static void	SpawnRegenZodiac(const char* filename, bool bOnce = true);
#endif
		void	AddRegen(LPREGEN regen);
		void	ClearRegen();
		bool	IsValidRegen(LPREGEN regen, size_t regen_id);

		void	ZodiacMessage(const char* msg);
		void	ZodiacMessageClear();

		void	ZodiacMessageMission(BYTE Floor);
		void	ZodiacFloorMessage(BYTE Floor, BYTE Count = 0);
		void	ZodiacFloorSubMessage(const char * msg);

		void	ZodiacTime(BYTE currentfloor, BYTE nextfloor, int time, int time2 = 0);
		void	ZodiacTimeClear();

		long	GetMapIndex() { return m_lMapIndex; }
		BYTE	GetPortal() { return m_bPortal; }
		BYTE	GetFloor() { return m_bFloor; }
		BYTE	GetNextFloor() { return m_bNextFloor; }
		bool	IsNextFloor() { return m_bNextFloorControl; }
		// MT2009_PLUS_ZODIAC_RUNS_V3: the temple's own way out (time up, an expulsion) under way.
		bool	IsExiting() const { return zodiac_exit_temple_event_data != NULL; }
		DWORD	GetTime() { return m_dwGetGlobalTime; }

		void	ControlMob();
		int		CountMonster();
		int		CountIsBoss();
		int		CountIsStone();
		bool	ControlCharacter();

		void	ExitTemple();
		void	TimeIsUp();

		void	Purge();
		void	KillAll();

		void	NewFloor(BYTE Floor);

		void	JoinParty(LPPARTY pParty);
		void	QuitParty(LPPARTY pParty);

		void	Join(LPCHARACTER ch);

		void	IncMember(LPCHARACTER ch);
		void	DecMember(LPCHARACTER ch);

		void	IncPartyMember(LPPARTY pParty, LPCHARACTER ch);
		void	DecPartyMember(LPPARTY pParty, LPCHARACTER ch);

		void	IncMonster() { m_iMonsterCount++; sys_log(0, "MonsterCount %d", m_iMonsterCount); }
		void	DecMonster() { m_iMonsterCount--; }

		void	PolyCharacter(LPCHARACTER Mob);
		void	ProcessZodiacItems(bool enable);

		void	NextFloorButton();
		void	SpawnMob();
		void	SpawnStone(bool Statue = false);
		void	SpawnBoss(BYTE Flag = 0);

		void	GiveGiftBox();

		void	GiveGiftZodiacSmall();
		void	GiveGiftZodiacMiddle();
		void	GiveGiftZodiacBig();

		void	GiveGiftZi();
		void	GiveGiftChou();
		void	GiveGiftYin();
		void	GiveGiftMao();
		void	GiveGiftChen();
		void	GiveGiftSi();
		void	GiveGiftWu();
		void	GiveGiftWei();
		void	GiveGiftShen();
		void	GiveGiftYu();
		void	GiveGiftXu();
		void	GiveGiftHai();

		void	StartLogin();

	protected:
		CZodiac(IdType id, long lMapIndex, BYTE bPortal);
		void	Initialize();

	private:
		IdType		m_id;
		long		m_lMapIndex;
		BYTE		m_bPortal;
		BYTE		m_bFloor;
		BYTE		m_bNextFloor;
		bool		m_bNextFloorControl;
		BYTE		m_bPosition;
		DWORD		m_dwGetGlobalTime;
		bool		m_bTimeDown;

		CHARACTER_SET	m_set_pkCharacter;
		std::map<std::string, int>  m_map_Flag;

		TPartyMap	m_map_pkParty;
		TUniqueMobMap	m_map_UniqueMob;

		int		m_iMonsterCount;

		int		m_iMobKill;
		int		m_iStoneKill;
		int		m_iBossKill;
		int		m_iTotalMonster;

		std::vector<LPREGEN> m_regen;

		size_t regen_id_;

		LPEVENT zodiac_floor_event_data;
		LPEVENT zodiac_remaining_time_temple_floor;
		LPEVENT zodiac_exit_temple_event_data;
		LPEVENT deadEvent;

		friend class CZodiacManager;
		friend EVENTFUNC(Floor_event_data_start);
		friend EVENTFUNC(Floor_remaining_time_event_data_start);
		friend EVENTFUNC(Exit_temple_event_data_start);
		friend EVENTFUNC(zodiac_dead_event);

		LPPARTY m_pParty;

	public :
		void SetPartyNull();
};

extern bool regen_zodiac(const char* filename, long lMapIndex, int base_x, int base_y, LPZODIAC pZodiac, bool bOnce = true);

class CZodiacManager : public singleton<CZodiacManager>
{
	typedef std::map<CZodiac::IdType, LPZODIAC> TZodiacMap;
	typedef std::map<long, LPZODIAC> TMapZodiac;

	public:
		CZodiacManager();
		virtual ~CZodiacManager();

#ifdef ENABLE_SERVERTIME_PORTAL_SPAWN
		bool		Initialize();
		LPEVENT		zodiac_spawn_timer;

		int			GetCurrentDay();
		bool		GetIsDaily();
		bool		Spawn();
#endif

		LPZODIAC	Create(BYTE bPortal);
		void		Destroy(CZodiac::IdType zodiac_id);
		LPZODIAC	Find(CZodiac::IdType zodiac_id);
		LPZODIAC	FindByMapIndex(long lMapIndex);

		void		StartTemple(LPCHARACTER pkChar, BYTE portal);

		void		DeadMob(LPCHARACTER Mob, DWORD mapIndex);
		void		DeadPC(DWORD mapIndex);

#ifndef ENABLE_SERVERTIME_PORTAL_SPAWN
	private:
#endif
		TZodiacMap	m_map_pkZodiac;
		TMapZodiac	m_map_pkMapZodiac;
		CZodiac::IdType next_id_;
};

#endif // ENABLE_12ZI

#endif
