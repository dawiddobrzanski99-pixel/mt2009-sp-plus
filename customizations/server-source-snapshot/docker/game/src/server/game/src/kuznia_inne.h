#pragma once
// MT2009_NASZE_INNE_V1: zakladka "Inne" Kuzni Mocy - dodatki wlaczane w panelu (domyslnie wylaczone).
// Flagi: <spool>/systems/inne/flagi.txt ("klucz=1"), czytane raz przy starcie gry (panel restartuje kanaly).
//  sakiewka_kd=1  - Kamien Duszy z Metina spada jako Sakiewka Kamieni Dusz (27999), z ta sama szansa co KD.
//  skrzynka_ku=1  - Ksiega Umiejetnosci (50300) z Metina/bossa spada jako Skrzynia z KU (50035).
// Podglad dropu i wiki pokazuja to samo co drop (KD/KU znikaja, w ich miejscu sakiewka/skrzynia).
#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <map>
#include <string>
#include <vector>

namespace kuznia_inne {

inline const std::string& Root()
{
	static const std::string root = std::string(std::getenv("M2_RATES_SPOOL") && *std::getenv("M2_RATES_SPOOL")
		? std::getenv("M2_RATES_SPOOL") : "/opt/m2spool") + "/systems/inne";
	return root;
}

// sakiewka_szansa=N - Metin bez KD w dropie: szansa na Sakiewke N/10000 (kazdy Metin ma Sakiewke).
// klepsydra_metin=N / klepsydra_boss=N - szansa Klepsydry z kazdego Metina / bossa (N/10000, domyslnie 200 = 2%);
// klepsydra_mob=<vnum potwora>:N - wybrane potwory z wlasna szansa (wazniejsze niz Metin/boss).
// auto_kolekcjoner=1 - podniesiony przedmiot (nie questowy) od razu trafia do Kolekcjonera gracza.
struct Flags { bool sakiewka = false, skrzynka_ku = false, ulepszacze = false, klepsydra = false, licznik = false, auto_kolekcjoner = false; int sakiewka_szansa = 200;
	int klepsydra_metin = 200, klepsydra_boss = 200; std::map<DWORD, int> klepsydra_mob; };

inline const Flags& Get()
{
	static Flags flags;
	static bool loaded = false;
	if (!loaded)
	{
		loaded = true;
		std::ifstream in((Root() + "/flagi.txt").c_str());
		std::string line;
		while (std::getline(in, line))
		{
			if (!line.empty() && line[line.size() - 1] == '\r') line.erase(line.size() - 1);
			if (line == "sakiewka_kd=1") flags.sakiewka = true;
			else if (line == "skrzynka_ku=1") flags.skrzynka_ku = true;
			else if (line == "ulepszacze=1") flags.ulepszacze = true;
			else if (line == "klepsydra=1") flags.klepsydra = true;
			else if (line == "licznik=1") flags.licznik = true;
			else if (line == "auto_kolekcjoner=1") flags.auto_kolekcjoner = true;
			else if (line.compare(0, 16, "sakiewka_szansa=") == 0)
				flags.sakiewka_szansa = std::max(0, std::min(10000, atoi(line.c_str() + 16)));
			else if (line.compare(0, 16, "klepsydra_metin=") == 0)
				flags.klepsydra_metin = std::max(0, std::min(10000, atoi(line.c_str() + 16)));
			else if (line.compare(0, 15, "klepsydra_boss=") == 0)
				flags.klepsydra_boss = std::max(0, std::min(10000, atoi(line.c_str() + 15)));
			else if (line.compare(0, 14, "klepsydra_mob=") == 0)
			{
				const DWORD race = strtoul(line.c_str() + 14, NULL, 10);
				const size_t colon = line.find(':');
				if (race && colon != std::string::npos)
					flags.klepsydra_mob[race] = std::max(0, std::min(10000, atoi(line.c_str() + colon + 1)));
			}
		}
		sys_log(0, "KUZNIA_INNE: sakiewka_kd=%d skrzynka_ku=%d ulepszacze=%d klepsydra=%d licznik=%d", flags.sakiewka ? 1 : 0,
				flags.skrzynka_ku ? 1 : 0, flags.ulepszacze ? 1 : 0, flags.klepsydra ? 1 : 0, flags.licznik ? 1 : 0);
	}
	return flags;
}

// ulepszacze=1: materialy do ulepszania i przedmioty Biologa brane z plecaka, a brakujace z Kolekcjonera.
inline bool Ulepszacze() { return Get().ulepszacze; }
// licznik=1: pod minimapa liczba Metinow i bossow na mapie (komenda /map_counters; wylaczone = brak odpowiedzi,
// okno w kliencie sie nie pokazuje).
inline bool Licznik() { return Get().licznik; }
// auto_kolekcjoner=1: podnoszony drop od razu do Kolekcjonera (char_item.cpp PickupItem).
inline bool AutoKolekcjoner() { return Get().auto_kolekcjoner; }

// klepsydra=1: Klepsydra Biologa (71102, zeruje czas oczekiwania u Biologa) - 2% z kazdego Metina i bossa.
static const DWORD KLEPSYDRA = 71102;
static const int KLEPSYDRA_PER_10000 = 200;

static const DWORD SAKIEWKA_KD = 27999;
static const DWORD SKRZYNKA_KU = 50035;
static const DWORD KU = 50300;

inline bool IsKD(DWORD vnum) { return vnum >= 28000 && vnum < 29000; }

// Na co zamienic przedmiot z dropu (ten sam, gdy nic).
inline DWORD Map(DWORD vnum, bool stone, bool boss)
{
	const Flags& f = Get();
	if (f.sakiewka && stone && IsKD(vnum)) return SAKIEWKA_KD;
	if (f.skrzynka_ku && vnum == KU && (stone || boss)) return SKRZYNKA_KU;
	return vnum;
}

inline bool IsBoss(LPCHARACTER victim) { return victim->IsMonster() && victim->GetMobRank() >= MOB_RANK_BOSS; }

// Szansa Klepsydry Biologa z tego potwora (N/10000): wybrany potwor z panelu, inaczej Metin / boss.
inline int HourglassChance(DWORD race, bool stone, bool boss)
{
	const Flags& f = Get();
	if (!f.klepsydra) return 0;
	std::map<DWORD, int>::const_iterator it = f.klepsydra_mob.find(race);
	if (it != f.klepsydra_mob.end()) return it->second;
	return stone ? f.klepsydra_metin : (boss ? f.klepsydra_boss : 0);
}

// Drop: koniec CreateDropItem - podmiana przedmiotow na sakiewke/skrzynie (szansa ta sama, co oryginalu).
template <class Manager>
inline void Drop(Manager& manager, LPCHARACTER victim, std::vector<LPITEM>& loot)
{
	if (!victim) return;
	const Flags& f = Get();
	if (!f.sakiewka && !f.skrzynka_ku && !f.klepsydra) return;
	const bool stone = victim->IsStone(), boss = IsBoss(victim);
	const int hourglass = HourglassChance(victim->GetRaceNum(), stone, boss);
	if (hourglass > 0 && number(1, 10000) <= hourglass)
	{
		LPITEM glass = manager.CreateItem(KLEPSYDRA, 1, 0, true);
		if (glass) loot.push_back(glass);
	}
	bool pouch = false;
	for (size_t i = 0; i < loot.size(); ++i)
	{
		LPITEM item = loot[i];
		if (!item) continue;
		const DWORD to = Map(item->GetVnum(), stone, boss);
		if (to == SAKIEWKA_KD) pouch = true;
		if (to == item->GetVnum()) continue;
		LPITEM box = manager.CreateItem(to, to == SAKIEWKA_KD ? 1 : item->GetCount(), 0, true);
		if (!box) continue;
		manager.DestroyItem(item);
		loot[i] = box;
	}
	// Kazdy Metin ma Sakiewke: bez KD w dropie - wlasna szansa (sakiewka_szansa/10000).
	if (f.sakiewka && stone && !pouch && f.sakiewka_szansa > 0 && number(1, 10000) <= f.sakiewka_szansa)
	{
		LPITEM box = manager.CreateItem(SAKIEWKA_KD, 1, 0, true);
		if (box) loot.push_back(box);
	}
}

// Podglad dropu potwora (MobPreviewItem): zamiana i bez powtorzen.
inline void Preview(bool stone, bool boss, DWORD race, std::vector<std::pair<DWORD, int> >& lines)
{
	const Flags& f = Get();
	if (!f.sakiewka && !f.skrzynka_ku && !f.klepsydra) return;
	std::vector<std::pair<DWORD, int> > out;
	if (HourglassChance(race, stone, boss) > 0) lines.push_back(std::make_pair(KLEPSYDRA, 1));
	for (size_t i = 0; i < lines.size(); ++i)
	{
		const DWORD to = Map(lines[i].first, stone, boss);
		bool seen = false;
		for (size_t j = 0; j < out.size(); ++j) if (out[j].first == to) { seen = true; break; }
		if (!seen) out.push_back(std::make_pair(to, to == SAKIEWKA_KD ? 1 : lines[i].second));
	}
	if (f.sakiewka && stone && f.sakiewka_szansa > 0)
	{
		bool seen = false;
		for (size_t j = 0; j < out.size(); ++j) if (out[j].first == SAKIEWKA_KD) { seen = true; break; }
		if (!seen) out.push_back(std::make_pair(SAKIEWKA_KD, 1));
	}
	lines.swap(out);
}

// Wiki dropu: zamiana; szanse KD laczone w jedna szanse sakiewki.
template <class Row>
inline void Wiki(bool stone, bool boss, DWORD race, std::vector<Row>& rows)
{
	const Flags& f = Get();
	if (!f.sakiewka && !f.skrzynka_ku && !f.klepsydra) return;
	std::vector<Row> out;
	if (const int hourglass = HourglassChance(race, stone, boss))
	{
		Row glass = Row();
		glass.dwVnum = KLEPSYDRA; glass.iCountMin = 1; glass.iCountMax = 1; glass.dChance = hourglass / 10000.0;
		rows.push_back(glass);
	}
	for (size_t i = 0; i < rows.size(); ++i)
	{
		Row row = rows[i];
		const DWORD from = row.dwVnum, to = Map(from, stone, boss);
		if (to == SAKIEWKA_KD) { row.iCountMin = 1; row.iCountMax = 1; }
		row.dwVnum = to;
		size_t j = 0;
		for (; j < out.size(); ++j) if (out[j].dwVnum == to) break;
		if (j == out.size()) out.push_back(row);
		else if (to != from) out[j].dChance = std::min(1.0, out[j].dChance + row.dChance);
	}
	if (f.sakiewka && stone && f.sakiewka_szansa > 0)
	{
		size_t j = 0;
		for (; j < out.size(); ++j) if (out[j].dwVnum == SAKIEWKA_KD) break;
		if (j == out.size())
		{
			Row pouch = Row();
			pouch.dwVnum = SAKIEWKA_KD; pouch.iCountMin = 1; pouch.iCountMax = 1; pouch.dChance = f.sakiewka_szansa / 10000.0;
			out.push_back(pouch);
		}
	}
	rows.swap(out);
}

} // namespace kuznia_inne
