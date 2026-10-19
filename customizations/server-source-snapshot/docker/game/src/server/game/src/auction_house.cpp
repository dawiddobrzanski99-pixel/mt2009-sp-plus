// DOM AUKCYJNY (AH_V1)
// Autor: Vekirion
//
// Wyszukiwarka i zakupy ofert ze sklepow offline (Ikarus). Nie wystawia
// niczego sama: oferty to linie sklepow z CShopManager, a kazdy zakup idzie
// zwykla sciezka kupna Ikarusa (blokada linii w db core, kontrola ceny, Yang,
// logi), tak jak /flea_buy Domu Towarowego.
//
// Klient nie ma nowych pakietow (brak zrodel binarki). Kanal:
//   klient -> serwer : komendy czatu /ah_*
//   serwer -> klient : ChatPacket(CHAT_TYPE_COMMAND, "AH...") oraz istniejacy
//                      pakiet wynikow wyszukiwania Ikarusa (jedna strona ofert,
//                      odbiera go SetSearchResultItems okna ustawionego przez
//                      ikashop.SetSearchShopBoard).
//
// KOMENDY KLIENTA
//   /ah_search <req> <strona> <naStrone> <FILTR>
//   /ah_names <req> <FILTR>                      (podpowiedzi nazw; bonusy pomijane)
//   /ah_bonus
//   /ah_buy <wlasciciel> <idOferty> <ilosc|0=cala> <widzianaCenaCalejOferty>
//   /ah_cart_add <reset 0|1> <wlasciciel:idOferty:cena,...>
//   /ah_cart_buy
//   /ah_bulk_quote <req> <ileSztuk> <FILTR>      (FILTR musi miec vnum)
//   /ah_bulk_buy <token>
//   /ah_cancel
//
//   FILTR = <kategoria> <kolumnaSort> <malejaco 0|1> <plusOd|-1> <plusDo|-1>
//           <cenaOd> <cenaDo> <vnum> <socket0|-1> <trybBonusow> <liczbaBonusow>
//           <klasa> <bonusy|-> [nazwa[|skill,skill,...]]
//     klasa       : 0 dowolna, 1 wojownik, 2 ninja, 3 sura, 4 szaman - tylko
//                   przedmioty, ktore ta klasa moze zalozyc
//                   MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: albo
//                   klasa:poziomOd:poziomDo:sztukiOd:sztukiDo:plec - poziom postaci
//                   (LIMIT_LEVEL), liczba sztuk w ofercie (-1 = bez granicy), plec
//                   0 dowolna, 1 kobieta, 2 mezczyzna (tylko bron, zbroje, kostiumy)
//     cenaOd/Do   : cena calej oferty w Yang; 0 = bez granicy
//     plusOd/Do   : poziom ulepszenia z nazwy przedmiotu ("+7"); -1 = bez granicy
//     kolumnaSort : 0 cena oferty, 1 cena za sztuke, 2 ilosc
//     trybBonusow : 0 rowno, 1 przynajmniej, 2 maksymalnie
//     bonusy      : typ:wartosc,typ:wartosc (do 7); przedmiot musi miec wszystkie
//
// ODPOWIEDZI SERWERA
//   AHSearch <req> <strona> <liczbaStron> <liczbaOfert> <vnum> <socket0>   + pakiet ze strona
//       vnum    : wszystkie znalezione oferty to ten jeden przedmiot (0: rozne)
//       socket0 : dla ksiag ta jedna umiejetnosc, inaczej -1
//   AHBusy <req>                                          (za szybko, ponow)
//   AHNames <req> <vnum,vnum,...|->                       (podpowiedzi: przedmioty z ofert)
//   AHBonusBegin / AHBonus <rzadki> <typ> <lv1..lv5> <max dla 8 zestawow> / AHBonusEnd
//   AHBuyResult <wlasciciel> <idOferty> <ok> <powod> <sztuki> <zaplacono>
//   AHJobDone <rodzaj> <udane> <wszystkie> <sztuki> <wydano> <powod>
//   AHJobRefused <rodzaj> <powod>
//   AHBulkQuote <req> <token> <sztuki> <oferty> <koszt> <dostepneSztuki>
//   FleaMarketStackUpdate <wlasciciel> <idOferty> <ilosc> <cena> 0   (stan linii)
//
// Kategorie (indeks = pozycja w s_categories) musza zgadzac sie z lista w
// skrypcie okna po stronie klienta.
//
// Ograniczenia silnika (cmd.cpp, interpret_command): cala komenda to najwyzej
// 256 znakow, a gracz ma 10 komend na pol sekundy - klient musi sie w tym miescic.

#include <deque>
#include <cstdlib>
#include <cstring>

#include "stdafx.h"
#include "../../common/tables.h"
#include "../../common/utils.h"
#include "packet.h"
#include "item.h"
#include "char.h"
#include "item_manager.h"
#include "desc.h"
#include "char_manager.h"
#include "buffer_manager.h"
#include "config.h"
#include "constants.h"
#include "event.h"
#include "questmanager.h"
#include "utils.h"
#include "cmd.h"
#include "mob_manager.h"	// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1 (nazwy potworow marmurow)

#include <algorithm>
#include <map>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#ifdef ENABLE_IKASHOP_RENEWAL

#include "ikarus_shop.h"
#include "ikarus_shop_manager.h"

// z ikarus_shop_manager.cpp
bool IsFleaMarketOn();
bool IsFleaMarketMap(LPCHARACTER ch);
std::string StringToLower(const char* name, size_t len);
namespace ikashop
{
	extern bool g_fleaRemoteBuy;
	extern DWORD g_fleaBuyQuantity;
}

// wywolywane z ikarus_shop_manager.cpp
void AuctionHouse_OnBuyLockSent(DWORD buyerid, DWORD itemid);
void AuctionHouse_OnBuyResult(DWORD buyerid, DWORD itemid, bool success);

namespace
{
	// ---------------------------------------------------------------- stale
	constexpr int AH_PAGE_SIZE_MAX = 20;
	// Ofert w jednym wyniku. Lista w trakcie zbierania nigdy nie ma wiecej niz dwa
	// razy tyle pozycji (CollectOffers przycina ja do najlepszych wg sortowania),
	// wiec szukanie samymi filtrami w swiecie z setkami tysiecy ofert nie zabiera
	// pamieci 32-bitowemu core (por. MT2009_PLUS_FLEA_MARKET_BOUND_V1 w 2.0.61).
	constexpr size_t AH_RESULT_MAX = 20000;
	constexpr DWORD AH_CACHE_TTL_MS = 15000;		// tyle zyje wynik dla kolejnych stron
	constexpr DWORD AH_SEARCH_GAP_MS = 150;			// odstep miedzy zapytaniami gracza
	constexpr DWORD AH_BUY_TIMEOUT_MS = 6000;		// czekanie na odpowiedz db core
	constexpr DWORD AH_QUOTE_TTL_MS = 60000;		// waznosc wyceny "Kup wiele"
	constexpr size_t AH_JOB_ENTRIES_MAX = 300;		// ofert w jednym zleceniu
	constexpr size_t AH_JOB_WINDOW = 10;			// tyle zakupow zlecenia czeka naraz na db core
	constexpr int AH_JOB_STEPS_PER_TICK = 12;		// ofert zlecenia przegladanych w jednym takcie
	// Sklep liczy graczowi akcje (IkarusShopFloodCheck): kupno wazy 5, limit to 2500
	// na minute, czyli 500 zakupow. Zlecenia biora z tego najwyzej tyle.
	constexpr size_t AH_BUYS_PER_MINUTE = 400;
	constexpr DWORD AH_BULK_PIECES_MAX = 100000;
	constexpr DWORD AH_PURGE_GAP_MS = 60000;
	constexpr DWORD AH_STATE_IDLE_MS = 600000;
	constexpr DWORD AH_VNUM_CACHE_TTL_MS = 600000;
	constexpr size_t AH_BONUS_MAX = 7;
	constexpr int AH_BONUS_SETS = 8;				// ATTRIBUTE_SET_WEAPON .. ATTRIBUTE_SET_EAR

	enum EAhSortColumn { AH_SORT_PRICE, AH_SORT_UNIT_PRICE, AH_SORT_COUNT };
	enum EAhBonusMode { AH_BONUS_EQUAL, AH_BONUS_AT_LEAST, AH_BONUS_AT_MOST };
	enum EAhJobKind { AH_JOB_SINGLE, AH_JOB_CART, AH_JOB_BULK };

	// AHBuyResult <powod>
	enum EAhBuyReason
	{
		AH_BUY_OK,
		AH_BUY_GONE,			// oferty juz nie ma
		AH_BUY_CHANGED,			// zmienila sie cena albo ilosc
		AH_BUY_REFUSED,			// sklep odmowil (edycja sklepu, blokada postaci, podzial stosu)
		AH_BUY_DB_REFUSED,		// db core odmowil (ktos byl szybszy)
		AH_BUY_TIMEOUT,
	};

	// AHJobDone / AHJobRefused <powod>
	enum EAhStopReason
	{
		AH_STOP_DONE,
		AH_STOP_CANCELLED,
		AH_STOP_GOLD,
		AH_STOP_INVENTORY,
		AH_STOP_TIMEOUT,
		AH_STOP_MAP,
		AH_STOP_BUSY,			// inne zlecenie w toku
		AH_STOP_EMPTY,			// nic do kupienia
		AH_STOP_QUOTE_EXPIRED,
		AH_STOP_OFF,
		AH_STOP_LIMIT,			// limit akcji sklepu na minute
	};

	// ------------------------------------------------------------ kategorie
	constexpr int AH_TYPE_ANY = -1;
	constexpr int AH_TYPE_OTHER = -2;

	struct TAhCategory
	{
		int parent;				// -1: kategoria glowna
		int type;				// ITEM_*, AH_TYPE_ANY albo AH_TYPE_OTHER
		int sub;				// podtyp albo -1
		DWORD classAntiFlag;	// podkategoria klasy: przedmiot NIE moze miec tej antyflagi
	};

	const TAhCategory s_categories[] =
	{
		/*  0 Wszystko            */ { -1, AH_TYPE_ANY, -1, 0 },
		/*  1 Bron                */ { -1, ITEM_WEAPON, -1, 0 },
		/*  2 Miecze jednoreczne  */ {  1, ITEM_WEAPON, WEAPON_SWORD, 0 },
		/*  3 Miecze dwureczne    */ {  1, ITEM_WEAPON, WEAPON_TWO_HANDED, 0 },
		/*  4 Luki                */ {  1, ITEM_WEAPON, WEAPON_BOW, 0 },
		/*  5 Sztylety            */ {  1, ITEM_WEAPON, WEAPON_DAGGER, 0 },
		/*  6 Dzwony              */ {  1, ITEM_WEAPON, WEAPON_BELL, 0 },
		/*  7 Wachlarze           */ {  1, ITEM_WEAPON, WEAPON_FAN, 0 },
		/*  8 Zbroje              */ { -1, ITEM_ARMOR, ARMOR_BODY, 0 },
		/*  9 Zbroje - Wojownik   */ {  8, ITEM_ARMOR, ARMOR_BODY, ITEM_ANTIFLAG_WARRIOR },
		/* 10 Zbroje - Ninja      */ {  8, ITEM_ARMOR, ARMOR_BODY, ITEM_ANTIFLAG_ASSASSIN },
		/* 11 Zbroje - Sura       */ {  8, ITEM_ARMOR, ARMOR_BODY, ITEM_ANTIFLAG_SURA },
		/* 12 Zbroje - Szaman     */ {  8, ITEM_ARMOR, ARMOR_BODY, ITEM_ANTIFLAG_SHAMAN },
		/* 13 Helmy               */ { -1, ITEM_ARMOR, ARMOR_HEAD, 0 },
		/* 14 Helmy - Wojownik    */ { 13, ITEM_ARMOR, ARMOR_HEAD, ITEM_ANTIFLAG_WARRIOR },
		/* 15 Helmy - Ninja       */ { 13, ITEM_ARMOR, ARMOR_HEAD, ITEM_ANTIFLAG_ASSASSIN },
		/* 16 Helmy - Sura        */ { 13, ITEM_ARMOR, ARMOR_HEAD, ITEM_ANTIFLAG_SURA },
		/* 17 Helmy - Szaman      */ { 13, ITEM_ARMOR, ARMOR_HEAD, ITEM_ANTIFLAG_SHAMAN },
		/* 18 Tarcze              */ { -1, ITEM_ARMOR, ARMOR_SHIELD, 0 },
		/* 19 Buty                */ { -1, ITEM_ARMOR, ARMOR_FOOTS, 0 },
		/* 20 Bransolety          */ { -1, ITEM_ARMOR, ARMOR_WRIST, 0 },
		/* 21 Naszyjniki          */ { -1, ITEM_ARMOR, ARMOR_NECK, 0 },
		/* 22 Kolczyki            */ { -1, ITEM_ARMOR, ARMOR_EAR, 0 },
		/* 23 Ksiegi              */ { -1, ITEM_SKILLBOOK, -1, 0 },
		/* 24 Ksiegi zapomnienia  */ { -1, ITEM_SKILLFORGET, -1, 0 },
		/* 25 Kamienie duszy      */ { -1, ITEM_METIN, -1, 0 },
		/* 26 Rudy i przetopy     */ { -1, ITEM_RESOURCE, -1, 0 },
		/* 27 Dopalacze           */ { -1, ITEM_POTION, -1, 0 },
		/* 28 Uzywalne            */ { -1, ITEM_USE, -1, 0 },
		/* 29 Ulepszacze          */ { -1, ITEM_MATERIAL, -1, 0 },
		/* 30 Inne                */ { -1, AH_TYPE_OTHER, -1, 0 },
		// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: kategorie z Domu Towarowego, dopisane
		// na koncu, zeby indeksy starszych kategorii (i starego klienta) sie nie zmienily.
		// Klient pokazuje je w panelu tam, gdzie staly w Domu Towarowym (CATEGORY_VISIBLE).
		/* 31 Smocza Alchemia     */ { -1, ITEM_DS, -1, 0 },		// + ITEM_SPECIAL_DS i Cory Draconis (GetCategoryOverride)
		/* 32 Polimorfia          */ { -1, ITEM_POLYMORPH, -1, 0 },
	};
	constexpr int AH_CATEGORY_COUNT = sizeof(s_categories) / sizeof(s_categories[0]);
	constexpr int AH_CAT_ALL = 0;
	constexpr int AH_CAT_ORES = 26;
	constexpr int AH_CAT_UPGRADES = 29;
	constexpr int AH_CAT_OTHER = 30;
	constexpr int AH_CAT_DRAGON_ALCHEMY = 31;	// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1

	// Przedmioty, ktorych typ w item_proto jest wspolny z mnostwem niezwiazanych
	// rzeczy: tu wpis wygrywa z dopasowaniem typu (jak w Domu Towarowym).
	int GetCategoryOverride(DWORD vnum)
	{
		switch (vnum)
		{
			case 27987:		// Malz
			case 27798:		// Skamieniala Krewetka
			case 27799:		// Rybia Osc
			case 71026:
				return AH_CAT_UPGRADES;

			case 30379:		// Przetopiony Kruszec
			case 39005:		// Magiczna Ruda Miedzi (warianty)
			case 70035:
			case 72308:
				return AH_CAT_ORES;
		}

		if (vnum >= 50601 && vnum <= 50638)		// rudy i przetopy pod ITEM_SPECIAL
			return AH_CAT_ORES;

		// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: Cory Draconis (kazdy stopien i rodzaj) to
		// w silniku zwykle przedmioty - ida do "Smocza Alchemia" jak w Domu Towarowym.
		switch (vnum)
		{
			case 50252: case 50255: case 50256: case 50257: case 50258: case 50259: case 50260:
			case 51501: case 51502: case 51503: case 51504: case 51505: case 51506: case 51507:
			case 51508: case 51509: case 51510: case 51541: case 51548: case 51549: case 51562:
			case 51569: case 51576: case 51583: case 51590: case 51597: case 51604: case 51611:
			case 51618: case 51625: case 51632:
				return AH_CAT_DRAGON_ALCHEMY;
		}

		return -1;
	}

	// ------------------------------------------------- dane przedmiotu (cache)
	struct TAhVnumInfo
	{
		bool valid = false;
		BYTE type = 0;
		BYTE sub = 0;
		DWORD antiFlags = 0;
		int refine = -1;		// poziom ulepszenia z konca nazwy ("Miecz+7" -> 7); -1: brak
		int baseCategory = AH_CAT_OTHER;
		int level = 0;			// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: LIMIT_LEVEL, 0 bez wymagania
		std::string lowerName;
	};

	std::unordered_map<DWORD, TAhVnumInfo> s_vnumInfo;
	DWORD s_vnumInfoTime = 0;
	std::unordered_map<DWORD, std::string> s_mobLowerNames;	// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1

	const TAhVnumInfo& GetVnumInfo(DWORD vnum)
	{
		// item_proto mozna przeladowac w locie, wiec cache nie zyje wiecznie
		const DWORD now = get_dword_time();
		if (now - s_vnumInfoTime > AH_VNUM_CACHE_TTL_MS)
		{
			s_vnumInfo.clear();
			s_mobLowerNames.clear();	// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1
			s_vnumInfoTime = now;
		}

		auto it = s_vnumInfo.find(vnum);
		if (it != s_vnumInfo.end())
			return it->second;

		TAhVnumInfo& info = s_vnumInfo[vnum];
		const TItemTable* table = ITEM_MANAGER::instance().GetTable(vnum);
		if (!table)
			return info;

		info.valid = true;
		info.type = table->bType;
		info.sub = table->bSubType;
		info.antiFlags = table->dwAntiFlags;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)	// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1
			if (table->aLimits[i].bType == LIMIT_LEVEL)
				info.level = std::max<int>(info.level, static_cast<int>(table->aLimits[i].lValue));
		info.lowerName = StringToLower(table->szLocaleName, strnlen(table->szLocaleName, ITEM_NAME_MAX_LEN));

		// poziom ulepszenia: cyfry po ostatnim plusie, do konca nazwy
		const size_t plus = info.lowerName.rfind('+');
		if (plus != std::string::npos && plus + 1 < info.lowerName.size() && info.lowerName.size() - plus <= 4)
		{
			bool digits = true;
			for (size_t i = plus + 1; i < info.lowerName.size(); ++i)
				digits = digits && info.lowerName[i] >= '0' && info.lowerName[i] <= '9';
			if (digits)
				info.refine = atoi(info.lowerName.c_str() + plus + 1);
		}

		const int overrideCategory = GetCategoryOverride(vnum);
		if (overrideCategory >= 0)
		{
			info.baseCategory = overrideCategory;
		}
		else if (info.type == ITEM_SPECIAL_DS)		// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1
		{
			info.baseCategory = AH_CAT_DRAGON_ALCHEMY;
		}
		else
		{
			for (int i = 1; i < AH_CATEGORY_COUNT; ++i)
			{
				const TAhCategory& category = s_categories[i];
				if (category.parent != -1 || category.type < 0)
					continue;
				if (category.type != info.type)
					continue;
				if (category.sub != -1 && category.sub != info.sub)
					continue;
				info.baseCategory = i;
				break;
			}
		}

		return info;
	}

	// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: marmur polimorfii nosi potwora w sockecie 0 -
	// "<marmur> - <potwor>" (jak w oknie i podpowiedziach) pasuje do wpisanej nazwy.
	// Cache zyje tyle co cache przedmiotow (s_mobLowerNames czysci GetVnumInfo).
	const std::string& GetMobLowerName(DWORD mobVnum)
	{
		auto it = s_mobLowerNames.find(mobVnum);
		if (it != s_mobLowerNames.end())
			return it->second;
		std::string& name = s_mobLowerNames[mobVnum];
		if (const CMob* mob = CMobManager::instance().Get(mobVnum))
		{
			const char* localeName = mob->m_table.szLocaleName;
			name = StringToLower(localeName, strnlen(localeName, CHARACTER_NAME_MAX_LEN));
		}
		return name;
	}

	bool MatchCategory(int categoryIndex, const TAhVnumInfo& info)
	{
		if (categoryIndex == AH_CAT_ALL)
			return true;

		const TAhCategory& category = s_categories[categoryIndex];
		if (category.parent == -1)
			return info.baseCategory == categoryIndex;

		if (info.baseCategory != category.parent)
			return false;

		if (category.classAntiFlag != 0)
			return (info.antiFlags & category.classAntiFlag) == 0;

		return info.sub == category.sub;
	}

	bool IsSkillBook(DWORD vnum)
	{
		return vnum == 50300 || vnum == 70037 || vnum == 70055;
	}

	// ----------------------------------------------------------------- filtr
	struct TAhBonus
	{
		int type = 0;
		int value = 0;
	};

	struct TAhFilter
	{
		int category = AH_CAT_ALL;
		int sortColumn = AH_SORT_PRICE;
		bool sortDescending = false;
		int refineMin = -1;
		int refineMax = -1;
		long long priceMin = 0;
		long long priceMax = 0;
		DWORD vnum = 0;
		long socket0 = -1;
		int bonusMode = AH_BONUS_AT_LEAST;
		int minBonusCount = 0;
		DWORD classAntiFlag = 0;		// przedmiot nie moze miec tej antyflagi (0: dowolna klasa)
		// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: poziom postaci (LIMIT_LEVEL), sztuki, plec;
		// -1 / 0: bez granicy
		int levelMin = -1;
		int levelMax = -1;
		int countMin = -1;
		int countMax = -1;
		DWORD sexAntiFlag = 0;
		std::vector<TAhBonus> bonuses;
		std::string query;				// male litery
		std::vector<long> skills;		// ksiegi: umiejetnosci pasujace do nazwy (zna je tylko klient)
		std::string key;				// caly filtr jako tekst, do porownania z cache
	};

	// Czyta FILTR z reszty komendy. Zwraca false, gdy brakuje pol.
	bool ParseFilter(const char* argument, TAhFilter& filter)
	{
		while (*argument == ' ')
			++argument;
		filter.key = argument;
		while (!filter.key.empty() && (filter.key.back() == ' ' || filter.key.back() == '\r' || filter.key.back() == '\n'))
			filter.key.pop_back();

		char fields[12][32];
		for (auto& field : fields)
		{
			argument = one_argument(argument, field, sizeof(field));
			if (!*field)
				return false;
		}

		char bonusArg[160];
		argument = one_argument(argument, bonusArg, sizeof(bonusArg));
		if (!*bonusArg)
			return false;

		filter.category = std::clamp(atoi(fields[0]), 0, AH_CATEGORY_COUNT - 1);
		filter.sortColumn = std::clamp(atoi(fields[1]), 0, static_cast<int>(AH_SORT_COUNT));
		filter.sortDescending = atoi(fields[2]) != 0;
		filter.refineMin = std::clamp(atoi(fields[3]), -1, 999);
		filter.refineMax = std::clamp(atoi(fields[4]), -1, 999);
		filter.priceMin = std::max<long long>(0, atoll(fields[5]));
		filter.priceMax = std::max<long long>(0, atoll(fields[6]));
		filter.vnum = static_cast<DWORD>(strtoul(fields[7], nullptr, 10));
		filter.socket0 = atol(fields[8]);
		filter.bonusMode = std::clamp(atoi(fields[9]), 0, static_cast<int>(AH_BONUS_AT_MOST));
		filter.minBonusCount = std::clamp(atoi(fields[10]), 0, static_cast<int>(ITEM_ATTRIBUTE_MAX_NUM));
		switch (atoi(fields[11]))
		{
			case 1: filter.classAntiFlag = ITEM_ANTIFLAG_WARRIOR; break;
			case 2: filter.classAntiFlag = ITEM_ANTIFLAG_ASSASSIN; break;
			case 3: filter.classAntiFlag = ITEM_ANTIFLAG_SURA; break;
			case 4: filter.classAntiFlag = ITEM_ANTIFLAG_SHAMAN; break;
			default: filter.classAntiFlag = 0; break;
		}

		// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: pole klasy moze niesc dalsze filtry
		// "klasa:poziomOd:poziomDo:sztukiOd:sztukiDo:plec" (-1: bez granicy, plec 1 kobieta,
		// 2 mezczyzna). Stary klient wysyla sama klase - atoi wyzej czyta ja tak samo.
		{
			long extra[5] = { -1, -1, -1, -1, 0 };
			const char* cursor = strchr(fields[11], ':');
			for (int i = 0; i < 5 && cursor; ++i)
			{
				extra[i] = strtol(cursor + 1, nullptr, 10);
				cursor = strchr(cursor + 1, ':');
			}
			filter.levelMin = static_cast<int>(std::clamp<long>(extra[0], -1, 999));
			filter.levelMax = static_cast<int>(std::clamp<long>(extra[1], -1, 999));
			filter.countMin = static_cast<int>(std::clamp<long>(extra[2], -1, 1000000));
			filter.countMax = static_cast<int>(std::clamp<long>(extra[3], -1, 1000000));
			switch (extra[4])
			{
				case 1: filter.sexAntiFlag = ITEM_ANTIFLAG_FEMALE; break;
				case 2: filter.sexAntiFlag = ITEM_ANTIFLAG_MALE; break;
				default: filter.sexAntiFlag = 0; break;
			}
		}

		// bonusy: typ:wartosc,typ:wartosc
		if (strcmp(bonusArg, "-") != 0)
		{
			const std::string bonusText = bonusArg;
			size_t pos = 0;
			while (pos < bonusText.size() && filter.bonuses.size() < AH_BONUS_MAX)
			{
				const size_t comma = bonusText.find(',', pos);
				const std::string token = bonusText.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
				const size_t colon = token.find(':');
				if (colon != std::string::npos)
				{
					TAhBonus bonus;
					bonus.type = atoi(token.substr(0, colon).c_str());
					bonus.value = atoi(token.substr(colon + 1).c_str());
					if (bonus.type > 0)
						filter.bonuses.push_back(bonus);
				}
				if (comma == std::string::npos)
					break;
				pos = comma + 1;
			}
		}

		// nazwa[|skill,skill,...]
		std::string query = argument ? argument : "";
		const size_t bar = query.find('|');
		if (bar != std::string::npos)
		{
			const std::string skillPart = query.substr(bar + 1);
			query.erase(bar);
			size_t pos = 0;
			while (pos < skillPart.size() && filter.skills.size() < 64)
			{
				const size_t comma = skillPart.find(',', pos);
				const std::string token = skillPart.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
				const long skillVnum = strtol(token.c_str(), nullptr, 10);
				if (skillVnum > 0)
					filter.skills.push_back(skillVnum);
				if (comma == std::string::npos)
					break;
				pos = comma + 1;
			}
		}
		while (!query.empty() && (query.back() == ' ' || query.back() == '\r' || query.back() == '\n'))
			query.pop_back();
		if (query.size() > 60)
			query.resize(60);
		filter.query = StringToLower(query.c_str(), query.size());
		return true;
	}

	bool MatchBonuses(const TAhFilter& filter, const ikashop::TShopItem& item)
	{
		if (filter.minBonusCount > 0)
		{
			int count = 0;
			for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
				if (item.aAttr[i].bType != 0)
					++count;
			if (count != filter.minBonusCount)		// rowno tyle bonusow
				return false;
		}

		for (const TAhBonus& bonus : filter.bonuses)
		{
			bool hit = false;
			for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM && !hit; ++i)
			{
				if (static_cast<int>(item.aAttr[i].bType) != bonus.type)
					continue;

				const int value = static_cast<int>(item.aAttr[i].sValue);
				switch (filter.bonusMode)
				{
					case AH_BONUS_EQUAL:	hit = value == bonus.value; break;
					case AH_BONUS_AT_MOST:	hit = value <= bonus.value; break;
					default:				hit = value >= bonus.value; break;
				}
			}
			if (!hit)
				return false;
		}
		return true;
	}

	bool MatchItem(const TAhFilter& filter, const ikashop::TShopItem& item)
	{
		if (filter.vnum != 0)
		{
			if (item.vnum != filter.vnum)
				return false;
			if (filter.socket0 >= 0 && item.alSockets[0] != filter.socket0)
				return false;
		}

		const TAhVnumInfo& info = GetVnumInfo(item.vnum);
		if (!info.valid)
			return false;

		if (!MatchCategory(filter.category, info))
			return false;

		if (filter.classAntiFlag != 0 && (info.antiFlags & filter.classAntiFlag) != 0)
			return false;

		// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: plec mowi cos tylko o tym, co sie zaklada
		if (filter.sexAntiFlag != 0)
		{
			if (info.type != ITEM_WEAPON && info.type != ITEM_ARMOR && info.type != ITEM_COSTUME)
				return false;
			if ((info.antiFlags & filter.sexAntiFlag) != 0)
				return false;
		}
		if (filter.levelMin >= 0 && info.level < filter.levelMin)
			return false;
		if (filter.levelMax >= 0 && info.level > filter.levelMax)
			return false;
		if (filter.countMin >= 0 && static_cast<long long>(item.count) < filter.countMin)
			return false;
		if (filter.countMax >= 0 && static_cast<long long>(item.count) > filter.countMax)
			return false;

		if (filter.refineMin >= 0 || filter.refineMax >= 0)
		{
			// filtr ulepszenia pokazuje tylko przedmioty, ktore maja "+N" w nazwie
			if (info.refine < 0)
				return false;
			if (filter.refineMin >= 0 && info.refine < filter.refineMin)
				return false;
			if (filter.refineMax >= 0 && info.refine > filter.refineMax)
				return false;
		}

		if (filter.priceMin > 0 || filter.priceMax > 0)
		{
			const long long total = item.price.GetTotalYangAmount();
			if (filter.priceMin > 0 && total < filter.priceMin)
				return false;
			if (filter.priceMax > 0 && total > filter.priceMax)
				return false;
		}

		if (!filter.query.empty() && info.lowerName.find(filter.query) == std::string::npos)
		{
			// MT2009_PLUS_AUCTION_HOUSE_FILTERS_V1: marmur polimorfii po nazwie potwora
			if (info.type == ITEM_POLYMORPH && item.alSockets[0] > 0)
			{
				const std::string& mobName = GetMobLowerName(static_cast<DWORD>(item.alSockets[0]));
				if (mobName.empty() || (info.lowerName + " - " + mobName).find(filter.query) == std::string::npos)
					return false;
			}
			// ksiega umiejetnosci: po umiejetnosci z socketu 0
			else if (!IsSkillBook(item.vnum))
				return false;
			else if (std::find(filter.skills.begin(), filter.skills.end(), static_cast<long>(item.alSockets[0])) == filter.skills.end())
				return false;
		}

		return MatchBonuses(filter, item);
	}

	// --------------------------------------------------------- zbieranie ofert
	struct TAhOffer
	{
		DWORD owner = 0;
		DWORD item = 0;
		DWORD count = 0;
		long long total = 0;
		DWORD vnum = 0;
		long socket0 = 0;
	};

	// cena za sztuke a < b, bez dzielenia
	bool UnitPriceLess(const TAhOffer& a, const TAhOffer& b)
	{
		const long double left = static_cast<long double>(a.total) * static_cast<long double>(std::max<DWORD>(1, b.count));
		const long double right = static_cast<long double>(b.total) * static_cast<long double>(std::max<DWORD>(1, a.count));
		return left < right;
	}

	bool OfferBefore(const TAhOffer& a, const TAhOffer& b, int column, bool descending);

	// trim: po przekroczeniu 2 x AH_RESULT_MAX lista jest przycinana do AH_RESULT_MAX
	// najlepszych ofert wg sortowania z filtra (wyszukiwanie i wycena "Kup wiele").
	// uniqueVnum (podpowiedzi nazw): jedna oferta na przedmiot - podpowiedzi potrzebuja
	// tylko vnumow, a dwie litery nazwy pasuja do dziesiatek tysiecy ofert.
	// MT2009_PLUS_AUCTION_HOUSE_BOUND_V1: zadne wywolanie nie bierze wszystkich ofert swiata.
	void CollectOffers(LPCHARACTER ch, const TAhFilter& filter, std::vector<TAhOffer>& offers, bool trim = false, bool uniqueVnum = false)
	{
		const DWORD pid = ch->GetPlayerID();
		std::unordered_set<DWORD> seenVnums;	// MT2009_PLUS_AUCTION_HOUSE_BOUND_V1 (names)
		for (const auto& [ownerId, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || ownerId == pid)
				continue;

#ifdef EXTEND_IKASHOP_PRO
			if (shop->GetDuration() == 0)
				continue;
#endif

			for (const auto& [itemId, shopItem] : shop->GetItems())
			{
				if (!shopItem)
					continue;

				const auto& info = shopItem->GetInfo();
				if (!MatchItem(filter, info))
					continue;
				if (uniqueVnum && !seenVnums.insert(info.vnum).second)
					continue;	// MT2009_PLUS_AUCTION_HOUSE_BOUND_V1 (names)

				TAhOffer& offer = offers.emplace_back();
				offer.owner = ownerId;
				offer.item = itemId;
				offer.count = static_cast<DWORD>(info.count);
				offer.total = info.price.GetTotalYangAmount();
				offer.vnum = info.vnum;
				offer.socket0 = info.alSockets[0];

				if (trim && offers.size() >= AH_RESULT_MAX * 2)
				{
					std::nth_element(offers.begin(), offers.begin() + AH_RESULT_MAX, offers.end(),
						[&](const TAhOffer& a, const TAhOffer& b) {
							return OfferBefore(a, b, filter.sortColumn, filter.sortDescending);
						});
					offers.resize(AH_RESULT_MAX);
				}
			}
		}
	}

	// Wpisana nazwa, ktora jest dokladnie nazwa ktoregos ze znalezionych przedmiotow
	// ("zolc niedzwiedzia"), pokazuje tylko ten przedmiot - bez odmian z dopiskiem
	// ("Zolc Niedzwiedzia+"). Gdy zaden nie nazywa sie dokladnie tak, zostaje zwykle
	// dopasowanie fragmentu nazwy.
	void ApplyExactName(const TAhFilter& filter, std::vector<TAhOffer>& offers)
	{
		if (filter.query.empty() || filter.vnum != 0)
			return;

		auto isExact = [&](const TAhOffer& offer) {
			return GetVnumInfo(offer.vnum).lowerName == filter.query;
		};

		if (std::none_of(offers.begin(), offers.end(), isExact))
			return;

		std::erase_if(offers, [&](const TAhOffer& offer) { return !isExact(offer); });
	}

	// porzadek wyniku: true, gdy a stoi przed b
	bool OfferBefore(const TAhOffer& a, const TAhOffer& b, int column, bool descending)
	{
		// porzadek staly: przy remisie tansza oferta, potem starsza
		auto tieLess = [](const TAhOffer& a, const TAhOffer& b) {
			return a.total == b.total ? a.item < b.item : a.total < b.total;
		};

		{
			switch (column)
			{
				case AH_SORT_UNIT_PRICE:
					if (UnitPriceLess(a, b))
						return !descending;
					if (UnitPriceLess(b, a))
						return descending;
					return tieLess(a, b);

				case AH_SORT_COUNT:
					if (a.count != b.count)
						return descending ? a.count > b.count : a.count < b.count;
					return tieLess(a, b);

				default:
					if (a.total != b.total)
						return descending ? a.total > b.total : a.total < b.total;
					return a.item < b.item;
			}
		}
	}

	void SortOffers(std::vector<TAhOffer>& offers, int column, bool descending)
	{
		std::sort(offers.begin(), offers.end(), [&](const TAhOffer& a, const TAhOffer& b) {
			return OfferBefore(a, b, column, descending);
		});
	}

	// ------------------------------------------------------- stan na gracza
	struct TAhRef
	{
		DWORD owner = 0;
		DWORD item = 0;
	};

	struct TAhEntry
	{
		DWORD owner = 0;
		DWORD item = 0;
		DWORD quantity = 0;			// 0: cala oferta
		long long seenTotal = 0;	// cena calej oferty, ktora widzial gracz
		long long cost = 0;			// ile za to zaplaci (liczone tuz przed kupnem)
		DWORD pieces = 0;			// ile sztuk dostanie
	};

	struct TAhState
	{
		DWORD lastUse = 0;

		// wynik ostatniego wyszukiwania (kolejne strony bez ponownego przegladania sklepow)
		std::string cacheKey;
		std::vector<TAhRef> cacheRefs;
		DWORD cacheTime = 0;
		DWORD cacheVnum = 0;		// wszystkie oferty wyniku to ten jeden przedmiot (0: rozne)
		long cacheSocket0 = -1;		// ...i, dla ksiag, ta jedna umiejetnosc (-1: rozne albo nie ksiega)
		DWORD lastSearch = 0;
		DWORD lastNames = 0;
		std::deque<DWORD> buyTimes;	// zakupy zlecen z ostatniej minuty (limit akcji sklepu)

		// "Kup wybrane"
		std::vector<TAhEntry> cart;

		// "Kup wiele"
		DWORD quoteToken = 0;
		DWORD quoteTime = 0;
		long long quoteTotal = 0;
		std::vector<TAhEntry> quoteEntries;
	};

	struct TAhFlight
	{
		size_t index = 0;		// pozycja w TAhJob::entries
		DWORD item = 0;
		DWORD deadline = 0;
	};

	struct TAhJob
	{
		DWORD serial = 0;
		int kind = AH_JOB_SINGLE;
		std::vector<TAhEntry> entries;
		size_t next = 0;				// nastepna oferta do wyslania
		std::vector<TAhFlight> flights;	// zakupy wyslane, czekaja na db core
		bool exclusive = false;			// w drodze jest czesc stosu: nic wiecej nie idzie
		DWORD dispatchItem = 0;			// oferta wlasnie przekazywana sklepowi
		bool lockSent = false;
		int stopReason = -1;			// zlecenie konczy sie, gdy wroca zakupy w drodze
		bool cancel = false;
		int okCount = 0;
		long long spent = 0;
		DWORD pieces = 0;
	};

	std::map<DWORD, TAhState> s_states;
	std::map<DWORD, TAhJob> s_jobs;
	DWORD s_jobSerial = 0;
	DWORD s_quoteToken = 0;
	DWORD s_lastPurge = 0;

	TAhState& GetState(DWORD pid)
	{
		const DWORD now = get_dword_time();
		if (now - s_lastPurge > AH_PURGE_GAP_MS)
		{
			s_lastPurge = now;
			std::erase_if(s_states, [&](const auto& pair) {
				return pair.first != pid && now - pair.second.lastUse > AH_STATE_IDLE_MS;
			});
		}

		TAhState& state = s_states[pid];
		state.lastUse = now;
		return state;
	}

	bool CheckAvailable(LPCHARACTER ch, bool notify)
	{
		if (!IsFleaMarketOn())
		{
			if (notify)
				ch->ChatPacket(CHAT_TYPE_INFO, "Dom Aukcyjny jest wylaczony na tym swiecie.");
			return false;
		}

		if (!IsFleaMarketMap(ch))
		{
			if (notify)
				ch->ChatPacket(CHAT_TYPE_INFO, "Dom Aukcyjny jest dostepny tylko w M1.");
			return false;
		}

		return true;
	}

	// ------------------------------------------------------------ wyszukiwanie
	void SendPage(LPCHARACTER ch, DWORD requestId, const TAhState& state, int page, int pageSize)
	{
		const std::vector<TAhRef>& refs = state.cacheRefs;
		const int total = static_cast<int>(refs.size());
		const int pageCount = std::max(1, (total + pageSize - 1) / pageSize);
		page = std::clamp(page, 0, pageCount - 1);

		std::vector<ikashop::TSearchResultInfo> rows;
		rows.reserve(pageSize);

		const int begin = page * pageSize;
		const int end = std::min(total, begin + pageSize);
		for (int i = begin; i < end; ++i)
		{
			auto shop = ikashop::GetManager().GetShopByOwnerID(refs[i].owner);
			if (!shop)
				continue;
#ifdef EXTEND_IKASHOP_PRO
			if (shop->GetDuration() == 0)
				continue;
#endif
			auto shopItem = shop->GetItem(refs[i].item);
			if (!shopItem)
				continue;		// sprzedane od czasu wyszukania

			ikashop::TSearchResultInfo& row = rows.emplace_back();
			static_cast<ikashop::TShopItem&>(row) = shopItem->GetInfo();
			row.auction = false;
			row.duration = shop->GetDuration();
			str_to_cstring(row.seller_name, shop->GetOwnerName());
		}

		// najpierw naglowek strony, potem same oferty - ida tym samym polaczeniem, w tej kolejnosci
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHSearch %u %d %d %d %u %ld",
			requestId, page, pageCount, total, state.cacheVnum, state.cacheSocket0);
		ikashop::GetManager().SendShopFilterResultClientPacket(ch, rows);
	}

	// ----------------------------------------------------------------- zakupy
	void SendBuyResult(LPCHARACTER ch, const TAhEntry& entry, bool ok, int reason)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBuyResult %u %u %d %d %u %lld",
			entry.owner, entry.item, ok ? 1 : 0, reason, ok ? entry.pieces : 0, ok ? entry.cost : 0LL);
	}

	void SendOfferState(LPCHARACTER ch, const TAhEntry& entry, DWORD count, long long price)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "FleaMarketStackUpdate %u %u %u %lld 0", entry.owner, entry.item, count, price);
	}

	void FinishJob(LPCHARACTER ch, DWORD pid, int reason)
	{
		auto it = s_jobs.find(pid);
		if (it == s_jobs.end())
			return;

		const TAhJob& job = it->second;
		sys_log(0, "AUCTION_HOUSE: job done pid=%u kind=%d ok=%d/%u pieces=%u spent=%lld reason=%d",
			pid, job.kind, job.okCount, static_cast<unsigned int>(job.entries.size()), job.pieces, job.spent, reason);

		if (ch && ch->GetDesc())
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobDone %d %d %u %u %lld %d",
				job.kind, job.okCount, static_cast<unsigned int>(job.entries.size()), job.pieces, job.spent, reason);

		s_jobs.erase(it);

		// po zakupach lista ofert gracza jest nieaktualna
		auto stateIt = s_states.find(pid);
		if (stateIt != s_states.end())
			stateIt->second.cacheKey.clear();
	}

	// cena czesci stosu: tak samo liczy ja sklep (RecvShopBuyItemClientPacket)
	bool GetPartPrice(long long lineYang, DWORD lineCount, DWORD quantity, long long& partYang)
	{
		if (lineCount == 0 || quantity == 0 || quantity >= lineCount)
			return false;

		partYang = (lineYang * static_cast<long long>(quantity) + static_cast<long long>(lineCount) - 1) / static_cast<long long>(lineCount);
		return partYang > 0 && lineYang - partYang >= 1;
	}

	// czy zlecenie moze teraz wyslac kolejny zakup (limit akcji sklepu na minute)
	bool TakeBuyBudget(TAhState& state, DWORD now)
	{
		while (!state.buyTimes.empty() && now - state.buyTimes.front() > 60000)
			state.buyTimes.pop_front();
		if (state.buyTimes.size() >= AH_BUYS_PER_MINUTE)
			return false;
		state.buyTimes.push_back(now);
		return true;
	}

	EVENTINFO(TAhJobEventInfo)
	{
		DWORD pid = 0;
		DWORD serial = 0;
	};

	// Zlecenie zakupu. Kazdy zakup to zwykly zakup Ikarusa (blokada oferty w db
	// core, zaplata, wydanie przedmiotu), wiec trwa kilka taktow. Zeby zlecenie
	// nie czekalo na kazdy z osobna, naraz w drodze jest do AH_JOB_WINDOW zakupow
	// roznych ofert - tak samo, jakby gracz szybko klikal w sklepie. Yang na
	// zakupy w drodze jest odliczany przy sprawdzaniu kolejnego. Czesc stosu
	// idzie zawsze sama: przy pelnym ekwipunku wyladowalaby na ziemi, a cale
	// oferty trafiaja wtedy do magazynu sklepu.
	EVENTFUNC(ah_job_tick)
	{
		auto* eventInfo = dynamic_cast<TAhJobEventInfo*>(event->info);
		if (!eventInfo)
			return 0;

		const DWORD pid = eventInfo->pid;
		auto it = s_jobs.find(pid);
		if (it == s_jobs.end() || it->second.serial != eventInfo->serial)
			return 0;

		TAhJob& job = it->second;
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (!ch || !ch->GetDesc())
		{
			FinishJob(nullptr, pid, AH_STOP_CANCELLED);
			return 0;
		}

		const DWORD now = get_dword_time();
		for (const TAhFlight& flight : job.flights)
		{
			if (now < flight.deadline)
				continue;

			// db core nie odpowiedzial: stan zakupu nieznany, dalej nie kupujemy
			SendBuyResult(ch, job.entries[flight.index], false, AH_BUY_TIMEOUT);
			FinishJob(ch, pid, AH_STOP_TIMEOUT);
			return 0;
		}

		auto stop = [&](int reason) {
			if (job.stopReason < 0)
				job.stopReason = reason;
		};

		if (job.cancel)
			stop(AH_STOP_CANCELLED);
		else if (!IsFleaMarketOn() || !IsFleaMarketMap(ch))
			stop(AH_STOP_MAP);

		int steps = 0;
		while (job.stopReason < 0 && job.next < job.entries.size() && !job.exclusive
			&& job.flights.size() < AH_JOB_WINDOW && steps++ < AH_JOB_STEPS_PER_TICK)
		{
			TAhEntry& entry = job.entries[job.next];

			// stan oferty teraz
			auto shop = ikashop::GetManager().GetShopByOwnerID(entry.owner);
			auto shopItem = shop ? shop->GetItem(entry.item) : nullptr;
			bool gone = !shop || !shopItem;
#ifdef EXTEND_IKASHOP_PRO
			gone = gone || shop->GetDuration() == 0;
#endif
			if (gone)
			{
				SendBuyResult(ch, entry, false, AH_BUY_GONE);
				ikashop::GetManager().SendSearchResultDeleteClientPacket(ch, entry.item);
				++job.next;
				continue;
			}

			const auto& info = shopItem->GetInfo();
			const DWORD lineCount = static_cast<DWORD>(info.count);
			const long long lineTotal = info.price.GetTotalYangAmount();
			if (lineTotal != entry.seenTotal || entry.quantity > lineCount)
			{
				SendBuyResult(ch, entry, false, AH_BUY_CHANGED);
				SendOfferState(ch, entry, lineCount, lineTotal);
				++job.next;
				continue;
			}

			const bool part = entry.quantity != 0 && entry.quantity != lineCount;
			if (part)
			{
				if (!GetPartPrice(lineTotal, lineCount, entry.quantity, entry.cost))
				{
					SendBuyResult(ch, entry, false, AH_BUY_REFUSED);
					++job.next;
					continue;
				}
				entry.pieces = entry.quantity;

				if (!job.flights.empty())
					break;		// czesc stosu dopiero, gdy wroci reszta
			}
			else
			{
				entry.cost = lineTotal;
				entry.pieces = lineCount;
			}

			// Yang: bez tego, co pojdzie na zakupy w drodze
			long long pending = 0;
			for (const TAhFlight& flight : job.flights)
				pending += job.entries[flight.index].cost;
			if (static_cast<long long>(ch->GetGold()) < entry.cost + pending)
			{
				if (job.flights.empty())
					stop(AH_STOP_GOLD);
				break;		// zakup w drodze moze sie nie udac i zwolnic Yang
			}

			if (!ch->HasSlotForItem(info.vnum))
			{
				stop(AH_STOP_INVENTORY);
				break;
			}

			if (!TakeBuyBudget(GetState(pid), now))
			{
				stop(AH_STOP_LIMIT);
				break;
			}

			// zwykly zakup Ikarusa, zdalnie jak /flea_buy; wszystkie kontrole sa jego
			job.dispatchItem = entry.item;
			job.lockSent = false;

			ikashop::g_fleaRemoteBuy = true;
			ikashop::g_fleaBuyQuantity = part ? entry.quantity : 0;
			ikashop::GetManager().RecvShopBuyItemClientPacket(ch, entry.owner, entry.item, true, entry.seenTotal);
			ikashop::g_fleaRemoteBuy = false;
			ikashop::g_fleaBuyQuantity = 0;

			job.dispatchItem = 0;
			if (!job.lockSent)
			{
				// sklep odmowil od razu (powod wypisal graczowi na czacie)
				SendBuyResult(ch, entry, false, AH_BUY_REFUSED);
				++job.next;
				continue;
			}

			TAhFlight& flight = job.flights.emplace_back();
			flight.index = job.next;
			flight.item = entry.item;
			flight.deadline = now + AH_BUY_TIMEOUT_MS;
			job.exclusive = part;
			++job.next;
		}

		if (job.flights.empty())
		{
			if (job.stopReason >= 0)
			{
				FinishJob(ch, pid, job.stopReason);
				return 0;
			}
			if (job.next >= job.entries.size())
			{
				FinishJob(ch, pid, AH_STOP_DONE);
				return 0;
			}
		}

		return 1;		// co takt: wynik zakupu od razu zwalnia miejsce na nastepny
	}

	void StartJob(LPCHARACTER ch, int kind, std::vector<TAhEntry>&& entries)
	{
		const DWORD pid = ch->GetPlayerID();
		if (s_jobs.contains(pid))
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", kind, AH_STOP_BUSY);
			return;
		}

		if (entries.empty())
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", kind, AH_STOP_EMPTY);
			return;
		}

		if (entries.size() > AH_JOB_ENTRIES_MAX)
			entries.resize(AH_JOB_ENTRIES_MAX);

		TAhJob& job = s_jobs[pid];
		job.serial = ++s_jobSerial;
		job.kind = kind;
		job.entries = std::move(entries);

		auto* info = AllocEventInfo<TAhJobEventInfo>();
		info->pid = pid;
		info->serial = job.serial;
		event_create(ah_job_tick, info, 1);
	}

	// wlasciciel:idOferty:cena,wlasciciel:idOferty:cena
	void ParseCartEntries(const char* text, std::vector<TAhEntry>& cart)
	{
		const std::string list = text;
		size_t pos = 0;
		while (pos < list.size() && cart.size() < AH_JOB_ENTRIES_MAX)
		{
			const size_t comma = list.find(',', pos);
			const std::string token = list.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
			const size_t first = token.find(':');
			const size_t second = first == std::string::npos ? std::string::npos : token.find(':', first + 1);
			if (second != std::string::npos)
			{
				TAhEntry entry;
				entry.owner = static_cast<DWORD>(strtoul(token.substr(0, first).c_str(), nullptr, 10));
				entry.item = static_cast<DWORD>(strtoul(token.substr(first + 1, second - first - 1).c_str(), nullptr, 10));
				entry.seenTotal = atoll(token.substr(second + 1).c_str());

				const bool known = std::any_of(cart.begin(), cart.end(), [&](const TAhEntry& other) {
					return other.owner == entry.owner && other.item == entry.item;
				});
				if (entry.owner != 0 && entry.item != 0 && entry.seenTotal >= 0 && !known)
					cart.push_back(entry);
			}
			if (comma == std::string::npos)
				break;
			pos = comma + 1;
		}
	}
}

// ------------------------------------------------------- wejscia ze sklepu
void AuctionHouse_OnBuyLockSent(DWORD buyerid, DWORD itemid)
{
	auto it = s_jobs.find(buyerid);
	if (it != s_jobs.end() && it->second.dispatchItem != 0 && it->second.dispatchItem == itemid)
		it->second.lockSent = true;
}

void AuctionHouse_OnBuyResult(DWORD buyerid, DWORD itemid, bool success)
{
	auto it = s_jobs.find(buyerid);
	if (it == s_jobs.end())
		return;

	TAhJob& job = it->second;
	auto flightIt = std::find_if(job.flights.begin(), job.flights.end(), [&](const TAhFlight& flight) {
		return flight.item == itemid;
	});
	if (flightIt == job.flights.end() || flightIt->index >= job.entries.size())
		return;

	const TAhEntry& entry = job.entries[flightIt->index];
	job.flights.erase(flightIt);
	job.exclusive = false;
	if (success)
	{
		++job.okCount;
		job.spent += entry.cost;
		job.pieces += entry.pieces;
	}

	if (LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(buyerid))
		if (ch->GetDesc())
			SendBuyResult(ch, entry, success, success ? AH_BUY_OK : AH_BUY_DB_REFUSED);
}

// ----------------------------------------------------------------- komendy
// /ah_search <req> <strona> <naStrone> <FILTR>
ACMD(do_ah_search)
{
	if (!ch || !ch->GetDesc())
		return;

	char requestArg[32], pageArg[32], sizeArg[32];
	argument = one_argument(argument, requestArg, sizeof(requestArg));
	argument = one_argument(argument, pageArg, sizeof(pageArg));
	argument = one_argument(argument, sizeArg, sizeof(sizeArg));
	if (!*requestArg || !*pageArg || !*sizeArg)
		return;

	const DWORD requestId = static_cast<DWORD>(strtoul(requestArg, nullptr, 10));
	const int page = std::max(0, atoi(pageArg));
	const int pageSize = std::clamp(atoi(sizeArg), 1, AH_PAGE_SIZE_MAX);

	if (!CheckAvailable(ch, true))
		return;

	TAhFilter filter;
	if (!ParseFilter(argument, filter))
		return;

	const DWORD pid = ch->GetPlayerID();
	const DWORD now = get_dword_time();
	TAhState& state = GetState(pid);
	if (state.lastSearch != 0 && now - state.lastSearch < AH_SEARCH_GAP_MS)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBusy %u", requestId);
		return;
	}
	state.lastSearch = now;
	ch->SetIkarusShopUseTime();

	// ta sama lista dla kolejnych stron; nowe zapytanie albo stary wynik = od nowa
	const bool cached = !state.cacheKey.empty() && state.cacheKey == filter.key && now - state.cacheTime < AH_CACHE_TTL_MS;
	if (!cached)
	{
		std::vector<TAhOffer> offers;
		CollectOffers(ch, filter, offers, true);
		ApplyExactName(filter, offers);
		SortOffers(offers, filter.sortColumn, filter.sortDescending);
		if (offers.size() > AH_RESULT_MAX)
			offers.resize(AH_RESULT_MAX);

		// czy caly wynik to jeden przedmiot (wtedy klient moze zaproponowac "Kup wiele")
		state.cacheVnum = offers.empty() ? 0 : offers.front().vnum;
		state.cacheSocket0 = offers.empty() || !IsSkillBook(offers.front().vnum) ? -1 : offers.front().socket0;

		state.cacheRefs.clear();
		state.cacheRefs.reserve(offers.size());
		for (const TAhOffer& offer : offers)
		{
			TAhRef& ref = state.cacheRefs.emplace_back();
			ref.owner = offer.owner;
			ref.item = offer.item;

			if (offer.vnum != state.cacheVnum)
				state.cacheVnum = 0;
			else if (state.cacheSocket0 != -1 && offer.socket0 != state.cacheSocket0)
				state.cacheSocket0 = -1;
		}
		if (state.cacheVnum == 0)
			state.cacheSocket0 = -1;
		state.cacheKey = filter.key;
		state.cacheTime = now;

		sys_log(0, "AUCTION_HOUSE: search pid=%u name=%s offers=%u filter=%s",
			pid, ch->GetName(), static_cast<unsigned int>(offers.size()), filter.key.c_str());
	}

	SendPage(ch, requestId, state, page, pageSize);
}

// /ah_names <req> <FILTR> - podpowiedzi do pola nazwy: przedmioty, ktore sa teraz
// wystawione, pasuja do wpisanego tekstu oraz do kategorii, klasy i poziomu
// ulepszenia z filtra. Bonusy z filtra nie maja tu znaczenia. Odpowiedz to lista
// vnumow (nazwy zna klient): najpierw nazwy zaczynajace sie od tekstu, potem reszta.
ACMD(do_ah_names)
{
	if (!ch || !ch->GetDesc())
		return;

	char requestArg[32];
	argument = one_argument(argument, requestArg, sizeof(requestArg));
	if (!*requestArg)
		return;

	const DWORD requestId = static_cast<DWORD>(strtoul(requestArg, nullptr, 10));
	if (!CheckAvailable(ch, false))
		return;

	TAhFilter filter;
	if (!ParseFilter(argument, filter) || filter.query.size() < 2)
		return;

	filter.bonuses.clear();
	filter.minBonusCount = 0;
	filter.vnum = 0;
	filter.socket0 = -1;
	filter.skills.clear();		// ksiegi po nazwie umiejetnosci nie maja wlasnej nazwy do podpowiedzi

	const DWORD now = get_dword_time();
	TAhState& state = GetState(ch->GetPlayerID());
	if (state.lastNames != 0 && now - state.lastNames < AH_SEARCH_GAP_MS)
		return;		// klient i tak zapyta ponownie po nastepnej literze
	state.lastNames = now;

	std::vector<TAhOffer> offers;
	CollectOffers(ch, filter, offers, false, true);	// MT2009_PLUS_AUCTION_HOUSE_BOUND_V1 (names)

	std::vector<DWORD> vnums;
	vnums.reserve(offers.size());
	for (const TAhOffer& offer : offers)
		vnums.push_back(offer.vnum);
	std::sort(vnums.begin(), vnums.end());
	vnums.erase(std::unique(vnums.begin(), vnums.end()), vnums.end());

	std::sort(vnums.begin(), vnums.end(), [&](DWORD left, DWORD right) {
		const std::string& leftName = GetVnumInfo(left).lowerName;
		const std::string& rightName = GetVnumInfo(right).lowerName;
		const bool leftStarts = leftName.compare(0, filter.query.size(), filter.query) == 0;
		const bool rightStarts = rightName.compare(0, filter.query.size(), filter.query) == 0;
		if (leftStarts != rightStarts)
			return leftStarts;
		return leftName == rightName ? left < right : leftName < rightName;
	});

	// jedna komenda czatu to najwyzej 512 znakow
	std::string list;
	for (DWORD vnum : vnums)
	{
		const std::string token = std::to_string(vnum);
		if (list.size() + token.size() + 1 > 440)
			break;
		if (!list.empty())
			list += ',';
		list += token;
	}

	ch->ChatPacket(CHAT_TYPE_COMMAND, "AHNames %u %s", requestId, list.empty() ? "-" : list.c_str());
}

// /ah_bonus - tabele bonusow z bazy (item_attr, item_attr_rare)
ACMD(do_ah_bonus)
{
	if (!ch || !ch->GetDesc() || !IsFleaMarketOn())
		return;

	auto sendTable = [&](const TItemAttrMap& table, int rare) {
		for (const auto& [applyIndex, row] : table)
		{
			if (applyIndex == 0)
				continue;

			bool used = false;
			for (int i = 0; i < AH_BONUS_SETS; ++i)
				used = used || row.bMaxLevelBySet[i] != 0;
			if (!used)
				continue;

			// zestawy: bron, zbroja, bransoleta, buty, naszyjnik, helm, tarcza, kolczyki
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBonus %d %u %ld %ld %ld %ld %ld %d %d %d %d %d %d %d %d",
				rare, applyIndex,
				row.lValues[0], row.lValues[1], row.lValues[2], row.lValues[3], row.lValues[4],
				row.bMaxLevelBySet[0], row.bMaxLevelBySet[1], row.bMaxLevelBySet[2], row.bMaxLevelBySet[3],
				row.bMaxLevelBySet[4], row.bMaxLevelBySet[5], row.bMaxLevelBySet[6], row.bMaxLevelBySet[7]);
		}
	};

	ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBonusBegin");
	sendTable(g_map_itemAttr, 0);
	sendTable(g_map_itemRare, 1);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBonusEnd");
}

// /ah_buy <wlasciciel> <idOferty> <ilosc|0=cala> <widzianaCena>
ACMD(do_ah_buy)
{
	if (!ch || !ch->GetDesc())
		return;

	char ownerArg[32], itemArg[32], quantityArg[32], priceArg[64];
	argument = one_argument(argument, ownerArg, sizeof(ownerArg));
	argument = one_argument(argument, itemArg, sizeof(itemArg));
	argument = one_argument(argument, quantityArg, sizeof(quantityArg));
	one_argument(argument, priceArg, sizeof(priceArg));
	if (!*ownerArg || !*itemArg || !*quantityArg || !*priceArg)
		return;

	if (!CheckAvailable(ch, true))
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", AH_JOB_SINGLE, IsFleaMarketOn() ? AH_STOP_MAP : AH_STOP_OFF);
		return;
	}

	TAhEntry entry;
	entry.owner = static_cast<DWORD>(strtoul(ownerArg, nullptr, 10));
	entry.item = static_cast<DWORD>(strtoul(itemArg, nullptr, 10));
	entry.quantity = static_cast<DWORD>(strtoul(quantityArg, nullptr, 10));
	entry.seenTotal = atoll(priceArg);
	if (entry.owner == 0 || entry.item == 0 || entry.seenTotal < 0)
		return;

	std::vector<TAhEntry> entries;
	entries.push_back(entry);
	StartJob(ch, AH_JOB_SINGLE, std::move(entries));
}

// /ah_cart_add <reset 0|1> <wlasciciel:idOferty:cena,...> - lista "Kup wybrane", w kilku
// komendach (jedna komenda to najwyzej 256 znakow, a gracz ma 10 komend na pol sekundy)
ACMD(do_ah_cart_add)
{
	if (!ch || !ch->GetDesc() || !IsFleaMarketOn())
		return;

	char resetArg[32];
	argument = one_argument(argument, resetArg, sizeof(resetArg));
	if (!*resetArg)
		return;

	TAhState& state = GetState(ch->GetPlayerID());
	if (atoi(resetArg) != 0)
		state.cart.clear();

	char listArg[CHAT_MAX_LEN + 1];
	one_argument(argument, listArg, sizeof(listArg));
	if (*listArg)
		ParseCartEntries(listArg, state.cart);
}

// /ah_cart_buy - kupuje cala liste, oferta po ofercie
ACMD(do_ah_cart_buy)
{
	if (!ch || !ch->GetDesc())
		return;

	if (!CheckAvailable(ch, true))
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", AH_JOB_CART, IsFleaMarketOn() ? AH_STOP_MAP : AH_STOP_OFF);
		return;
	}

	TAhState& state = GetState(ch->GetPlayerID());
	std::vector<TAhEntry> entries;
	entries.swap(state.cart);
	StartJob(ch, AH_JOB_CART, std::move(entries));
}

// /ah_bulk_quote <req> <ileSztuk> <FILTR> - wycena "Kup wiele": najtansze za sztuke,
// razem dokladnie tyle sztuk (albo mniej, gdy tylu nie ma), nigdy wiecej.
ACMD(do_ah_bulk_quote)
{
	if (!ch || !ch->GetDesc())
		return;

	char requestArg[32], piecesArg[32];
	argument = one_argument(argument, requestArg, sizeof(requestArg));
	argument = one_argument(argument, piecesArg, sizeof(piecesArg));
	if (!*requestArg || !*piecesArg)
		return;

	const DWORD requestId = static_cast<DWORD>(strtoul(requestArg, nullptr, 10));
	const DWORD wanted = std::min<DWORD>(static_cast<DWORD>(strtoul(piecesArg, nullptr, 10)), AH_BULK_PIECES_MAX);

	if (!CheckAvailable(ch, true))
		return;

	TAhFilter filter;
	if (!ParseFilter(argument, filter) || filter.vnum == 0 || wanted == 0)
		return;

	const DWORD now = get_dword_time();
	TAhState& state = GetState(ch->GetPlayerID());
	if (state.lastSearch != 0 && now - state.lastSearch < AH_SEARCH_GAP_MS)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBusy %u", requestId);
		return;
	}
	state.lastSearch = now;

	// MT2009_PLUS_AUCTION_HOUSE_BOUND_V1 (bulk): najtansze za sztuke, przyciete jak wyszukiwanie -
	// popularny przedmiot ma w swiecie botow dziesiatki tysiecy ofert, a wycena bierze najwyzej
	// AH_JOB_ENTRIES_MAX. "Dostepne sztuki" licza sie wtedy z AH_RESULT_MAX najtanszych ofert.
	filter.sortColumn = AH_SORT_UNIT_PRICE;
	filter.sortDescending = false;
	std::vector<TAhOffer> offers;
	CollectOffers(ch, filter, offers, true);
	ApplyExactName(filter, offers);
	SortOffers(offers, AH_SORT_UNIT_PRICE, false);

	state.quoteEntries.clear();
	state.quoteTotal = 0;

	DWORD available = 0;
	DWORD remaining = wanted;
	for (const TAhOffer& offer : offers)
	{
		available += offer.count;
		if (remaining == 0 || state.quoteEntries.size() >= AH_JOB_ENTRIES_MAX || offer.count == 0)
			continue;

		TAhEntry entry;
		entry.owner = offer.owner;
		entry.item = offer.item;
		entry.seenTotal = offer.total;

		if (offer.count <= remaining)
		{
			entry.quantity = 0;
			entry.cost = offer.total;
			entry.pieces = offer.count;
		}
		else
		{
			// czesc stosu: tyle, ile brakuje. Stosu, ktorego nie da sie podzielic, nie bierzemy.
			if (!GetPartPrice(offer.total, offer.count, remaining, entry.cost))
				continue;
			entry.quantity = remaining;
			entry.pieces = remaining;
		}

		remaining -= entry.pieces;
		state.quoteTotal += entry.cost;
		state.quoteEntries.push_back(entry);
	}

	state.quoteToken = ++s_quoteToken;
	state.quoteTime = now;

	ch->ChatPacket(CHAT_TYPE_COMMAND, "AHBulkQuote %u %u %u %u %lld %u",
		requestId, state.quoteToken, wanted - remaining, static_cast<unsigned int>(state.quoteEntries.size()),
		state.quoteTotal, available);
}

// /ah_bulk_buy <token> - kupuje dokladnie to, co bylo w wycenie, po cenach z wyceny
ACMD(do_ah_bulk_buy)
{
	if (!ch || !ch->GetDesc())
		return;

	char tokenArg[32];
	one_argument(argument, tokenArg, sizeof(tokenArg));
	if (!*tokenArg)
		return;

	if (!CheckAvailable(ch, true))
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", AH_JOB_BULK, IsFleaMarketOn() ? AH_STOP_MAP : AH_STOP_OFF);
		return;
	}

	const DWORD token = static_cast<DWORD>(strtoul(tokenArg, nullptr, 10));
	TAhState& state = GetState(ch->GetPlayerID());
	if (token == 0 || token != state.quoteToken || get_dword_time() - state.quoteTime > AH_QUOTE_TTL_MS)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", AH_JOB_BULK, AH_STOP_QUOTE_EXPIRED);
		return;
	}

	if (ch->GetGold() < state.quoteTotal)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "AHJobRefused %d %d", AH_JOB_BULK, AH_STOP_GOLD);
		return;
	}

	std::vector<TAhEntry> entries;
	entries.swap(state.quoteEntries);
	state.quoteToken = 0;
	StartJob(ch, AH_JOB_BULK, std::move(entries));
}

// /ah_cancel - przerywa zlecenie po zakupie, ktory jest w toku
ACMD(do_ah_cancel)
{
	if (!ch)
		return;

	auto it = s_jobs.find(ch->GetPlayerID());
	if (it != s_jobs.end())
		it->second.cancel = true;
}

#endif // ENABLE_IKASHOP_RENEWAL
