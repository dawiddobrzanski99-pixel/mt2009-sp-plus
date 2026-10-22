#pragma once
// MT2009_NASZE_KOLEKCJE_V1: Kolekcjoner Kuzni Mocy - kolekcje przedmiotow ustawiane w panelu (Kuznia Mocy -> Kolekcjoner).
// Wlaczany raz do mission_panel_impl.h (jedna jednostka kompilacji), komenda "/kolekcje" z cmd.cpp.
//
// Ustawienia: <spool>/systems/kolekcje/config.txt (panel), czytane ponownie po zmianie pliku - bez restartu gry.
// Linie rozdzielone tabulatorem, teksty jako hex bajtow CP1250:
//   cat     <klucz> <ikona vnum> <od poziomu> <nazwa hex> <opis hex>
//   catbon  <klucz> <point> <wartosc>                         nagroda za cala kategorie
//   item    <klucz> <vnum> <ile oddac> <szansa %> <przerwa s>
//   itembon <klucz> <vnum> <point> <wartosc>                  bonus za ukonczenie kolekcji
// W kategorii kolekcje ida po kolei: nastepna odblokowuje sie po ukonczeniu poprzedniej.
// Postep gracza: flagi questu "kolekcje.<klucz>_<vnum>_n" (przyjete) i "_t" (najblizsza proba, czas unix).
// Bonusy: affect KOLEKCJE_AFFECT (nie znika po smierci - char_affect.cpp), przeliczany przy logowaniu (Sync misji).
//
// Klient (okno Ctrl+N, zakladka Kolekcjoner): "/kolekcje show", "/kolekcje give <klucz> <vnum>";
// odpowiedz: "KC begin", "KC cat ...", "KC item ...", "KC end".
#include <map>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cstdlib>
#include <sys/stat.h>

namespace kuznia_kolekcje {

const DWORD KOLEKCJE_AFFECT = 64001;

struct Bon { int point; long value; };
struct Item { DWORD vnum; int need, chance; long cooldown; std::vector<Bon> bon; };
struct Cat { std::string key, name, desc; DWORD icon; int level; std::vector<Item> items; std::vector<Bon> fin; };

inline std::string ConfigPath()
{
	const char* spool = std::getenv("M2_RATES_SPOOL");
	return std::string(spool && *spool ? spool : "/opt/m2spool") + "/systems/kolekcje/config.txt";
}

inline bool Hex(const std::string& hex)
{
	if (hex == "-") return true;
	if (hex.size() % 2) return false;
	for (char c : hex) if (!isxdigit((unsigned char) c)) return false;
	return true;
}

inline std::string Unhex(const std::string& hex)
{
	std::string out;
	if (hex == "-") return out;
	for (size_t i = 0; i + 1 < hex.size(); i += 2) out += (char) strtol(hex.substr(i, 2).c_str(), NULL, 16);
	return out;
}

inline bool KeyOk(const std::string& key)
{
	if (key.empty() || key.size() > 8) return false;
	for (char c : key) if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9'))) return false;
	return true;
}

inline Cat* FindCat(std::vector<Cat>& cats, const std::string& key)
{
	for (auto& c : cats) if (c.key == key) return &c;
	return NULL;
}

// Ustawienia z panelu; plik czytany ponownie, gdy zmieni sie jego czas lub rozmiar.
inline const std::vector<Cat>& Cats()
{
	static std::vector<Cat> cats;
	static time_t mtime = -1;
	static off_t size = -1;
	struct stat st;
	if (stat(ConfigPath().c_str(), &st) != 0) { cats.clear(); mtime = -1; size = -1; return cats; }
	if (st.st_mtime == mtime && st.st_size == size) return cats;
	mtime = st.st_mtime; size = st.st_size;
	std::vector<Cat> fresh;
	std::ifstream in(ConfigPath().c_str());
	std::string line;
	while (std::getline(in, line))
	{
		if (!line.empty() && line[line.size() - 1] == '\r') line.erase(line.size() - 1);
		std::vector<std::string> f;
		std::istringstream ss(line);
		std::string part;
		while (std::getline(ss, part, '\t')) f.push_back(part);
		if (f.empty()) continue;
		if (f[0] == "cat" && f.size() >= 6 && KeyOk(f[1]) && !FindCat(fresh, f[1]) && Hex(f[4]) && Hex(f[5]))
		{
			Cat c; c.key = f[1]; c.icon = strtoul(f[2].c_str(), NULL, 10); c.level = atoi(f[3].c_str());
			c.name = f[4]; c.desc = f[5];
			fresh.push_back(c);
		}
		else if (f[0] == "catbon" && f.size() >= 4)
		{
			Cat* c = FindCat(fresh, f[1]); int p = atoi(f[2].c_str()); long v = atol(f[3].c_str());
			if (c && p > 0 && p < POINT_MAX_NUM && p < 256 && v > 0) c->fin.push_back({p, v});
		}
		else if (f[0] == "item" && f.size() >= 6)
		{
			Cat* c = FindCat(fresh, f[1]);
			Item it; it.vnum = strtoul(f[2].c_str(), NULL, 10); it.need = atoi(f[3].c_str());
			it.chance = std::max(1, std::min(100, atoi(f[4].c_str()))); it.cooldown = std::max(0L, atol(f[5].c_str()));
			bool dup = false;
			if (c) for (const auto& o : c->items) if (o.vnum == it.vnum) dup = true;
			if (c && !dup && it.vnum && it.need > 0 && ITEM_MANAGER::instance().GetTable(it.vnum)) c->items.push_back(it);
		}
		else if (f[0] == "itembon" && f.size() >= 5)
		{
			Cat* c = FindCat(fresh, f[1]); DWORD vnum = strtoul(f[2].c_str(), NULL, 10);
			int p = atoi(f[3].c_str()); long v = atol(f[4].c_str());
			if (c && p > 0 && p < POINT_MAX_NUM && p < 256 && v > 0)
				for (auto& it : c->items) if (it.vnum == vnum) it.bon.push_back({p, v});
		}
	}
	cats.swap(fresh);
	sys_log(0, "KUZNIA_KOLEKCJE: wczytano %u kategorii z %s", (unsigned) cats.size(), ConfigPath().c_str());
	return cats;
}

inline std::string Flag(const Cat& c, const Item& it, const char* what)
{
	return "kolekcje." + c.key + "_" + std::to_string(it.vnum) + "_" + what;
}

inline int Got(quest::PC* pc, const Cat& c, const Item& it) { return std::max(0, pc->GetFlag(Flag(c, it, "n"))); }
inline bool Done(quest::PC* pc, const Cat& c, const Item& it) { return Got(pc, c, it) >= it.need; }

// Pierwsza nieukonczona kolekcja kategorii (tylko ta przyjmuje przedmioty).
inline const Item* Next(quest::PC* pc, const Cat& c)
{
	for (const auto& it : c.items) if (!Done(pc, c, it)) return &it;
	return NULL;
}

inline bool AllDone(quest::PC* pc, const Cat& c) { return !c.items.empty() && Next(pc, c) == NULL; }

// Bonusy z ukonczonych kolekcji i kategorii -> jeden affect na kazdy bonus (jak misje).
inline void Apply(LPCHARACTER ch, quest::PC* pc)
{
	if (!ch || !pc) return;
	std::map<int, long> wanted;
	for (const auto& c : Cats())
	{
		for (const auto& it : c.items) if (Done(pc, c, it)) for (const auto& b : it.bon) wanted[b.point] += b.value;
		if (AllDone(pc, c)) for (const auto& b : c.fin) wanted[b.point] += b.value;
	}
	std::vector<int> stale;
	for (const CAffect* a : ch->GetAffectContainer())
		if (a && a->dwType == KOLEKCJE_AFFECT && !wanted.count(a->bApplyOn)) stale.push_back(a->bApplyOn);
	for (int point : stale) ch->RemoveAffect(ch->FindAffect(KOLEKCJE_AFFECT, point));
	for (const auto& b : wanted)
	{
		CAffect* have = ch->FindAffect(KOLEKCJE_AFFECT, b.first);
		if (!have || have->lApplyValue != b.second)
			ch->AddAffect(KOLEKCJE_AFFECT, (BYTE) b.first, b.second, 0, INFINITE_AFFECT_DURATION, 0, true, true);
	}
}

inline std::string Bonuses(const std::vector<Bon>& list)
{
	std::ostringstream out;
	bool first = true;
	for (const auto& b : list)
	{
		if (!first) out << ',';
		first = false;
		out << b.point << ':' << b.value << ':' << quest_bonus_preview::PointName(b.point);
	}
	return first ? "-" : out.str();
}

inline unsigned long long Have(LPCHARACTER ch, DWORD vnum)
{
	return playerbot_collector::CountBiologMaterial(ch, vnum);
}

inline void Send(LPCHARACTER ch, quest::PC* pc)
{
	const long now = get_global_time();
	ch->ChatPacket(CHAT_TYPE_COMMAND, "KC begin");
	for (const auto& c : Cats())
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "KC cat %s %u %d %s %s %s", c.key.c_str(), c.icon, c.level, c.name.c_str(),
				c.desc.substr(0, 240).c_str(), Bonuses(c.fin).c_str());
		const Item* next = Next(pc, c);
		for (const auto& it : c.items)
		{
			const int got = std::min(it.need, Got(pc, c, it));
			const int state = got >= it.need ? 3 : (&it == next && ch->GetLevel() >= c.level ? 1 : 0);
			const long wait = state == 1 ? std::max(0L, (long) pc->GetFlag(Flag(c, it, "t")) - now) : 0;
			ch->ChatPacket(CHAT_TYPE_COMMAND, "KC item %s %u %d %d %d %ld %ld %d %llu %s", c.key.c_str(), it.vnum, it.need, got,
					it.chance, it.cooldown, wait, state, state == 1 ? Have(ch, it.vnum) : 0ULL, Bonuses(it.bon).c_str());
		}
	}
	ch->ChatPacket(CHAT_TYPE_COMMAND, "KC end");
}

inline void Give(LPCHARACTER ch, quest::PC* pc, const std::string& key, DWORD vnum)
{
	const Cat* cat = NULL;
	for (const auto& c : Cats()) if (c.key == key) cat = &c;
	if (!cat) return;
	const Item* it = Next(pc, *cat);
	if (!it || it->vnum != vnum) { ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner: najpierw ukoncz poprzednia kolekcje."); return; }
	if (ch->GetLevel() < cat->level) { ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner: ta kategoria jest od %d poziomu.", cat->level); return; }
	const long now = get_global_time(), next = pc->GetFlag(Flag(*cat, *it, "t"));
	if (next > now) { ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner: nastepna proba za %ld min.", (next - now + 59) / 60); return; }
	if (!ch->CanHandleItem() || ch->IsDead()) return;
	if (Have(ch, vnum) < 1 || !playerbot_collector::ConsumeBiologMaterial(ch, vnum, 1))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner: nie masz tego przedmiotu (ani w plecaku, ani w Kolekcjonerze).");
		return;
	}
	if (number(1, 100) > it->chance)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner odrzucil przedmiot (szansa %d%%). Sprobuj jeszcze raz.", it->chance);
		return;
	}
	const int got = Got(pc, *cat, *it) + 1;
	ch->SetQuestFlag(Flag(*cat, *it, "n"), got);
	if (it->cooldown > 0) ch->SetQuestFlag(Flag(*cat, *it, "t"), (int) (now + it->cooldown));
	pc->Save();
	if (got >= it->need)
	{
		Apply(ch, pc);
		ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner: kolekcja ukonczona! Bonus dodany na stale.");
		if (AllDone(pc, *cat)) ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner: cala kategoria ukonczona! Nagroda dodana na stale.");
	}
	else ch->ChatPacket(CHAT_TYPE_INFO, "Kolekcjoner przyjal przedmiot (%d / %d).", got, it->need);
}

} // namespace kuznia_kolekcje
