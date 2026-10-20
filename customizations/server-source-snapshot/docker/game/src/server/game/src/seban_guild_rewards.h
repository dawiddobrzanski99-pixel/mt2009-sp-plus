#ifndef SEBAN_GUILD_REWARDS_V1_H
#define SEBAN_GUILD_REWARDS_V1_H
// MT2009_NASZE_GILDIA_V1: bonusy czlonkow gildii wg poziomu gildii z panelu Seban (Systemy -> Gildia).
// Tresc: "master enabled", potem wiersze "B <poziom 1-20> <punkt POINT_*> <wartosc>".
// Bez konfiguracji z panelu dziala dotychczasowa tabela (CustomGuildCombatBonus).
#include "custom_guild_combat_rewards.h"
#include "seban_bonus_extra.h"
#include "seban_sha256.h"
#include <sstream>
#include <string>
#include <cstring>
#include <iterator>
namespace SebanGuild {
struct Table {
 bool installed, master, enabled; std::string revision; SebanExtra::Levels rows; int cells[GUILD_MAX_LEVEL + 1][POINT_MAX_NUM];
 Table() : installed(false), master(true), enabled(true) { rows.Reset(GUILD_MAX_LEVEL); std::memset(cells, 0, sizeof(cells)); }
};
inline bool Hex(const std::string& s, size_t n) { return s.size() == n && s.find_first_not_of("0123456789abcdef") == std::string::npos; }
inline bool Parse(std::istream& in, Table& out) {
 std::string line, magic, digest, extra; if (!std::getline(in, line)) return false;
 std::istringstream header(line); if (!(header >> magic >> digest) || header >> extra || magic != "SEBAN_GUILD_V1" || !Hex(digest, 64)) return false;
 std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
 if (body.size() > 131072 || SebanHorse::Sha256(body) != digest) return false;
 std::istringstream input(body); int master, enabled;
 if (!std::getline(input, line)) return false;
 std::istringstream switches(line); if (!(switches >> master >> enabled) || switches >> extra || (master != 0 && master != 1) || (enabled != 0 && enabled != 1)) return false;
 Table* candidate = new Table();
 if (!SebanExtra::Parse(input, GUILD_MAX_LEVEL, candidate->rows)) { delete candidate; return false; }
 for (int level = 1; level <= GUILD_MAX_LEVEL; ++level) {
  const std::vector< std::pair<int, long> >& r = candidate->rows.At(level);
  for (size_t i = 0; i < r.size(); ++i) candidate->cells[level][r[i].first] = static_cast<int>(r[i].second);
 }
 candidate->installed = true; candidate->master = master; candidate->enabled = enabled; candidate->revision = digest;
 out = *candidate; delete candidate; return true;
}
inline bool ParseCommand(const std::string& raw, std::string& operation, Table& out) {
 if (raw.size() > 262144) return false;
 std::istringstream input(raw); std::string line, magic, extra;
 if (!std::getline(input, line)) return false;
 std::istringstream first(line); if (!(first >> magic >> operation) || first >> extra || magic != "SEBAN_GUILD_REQUEST_V1" || !Hex(operation, 32)) return false;
 return Parse(input, out);
}
inline Table& Storage() { static Table* table = new Table(); return *table; }
inline void Commit(const Table& table) { Storage() = table; }
inline int Clamp(int level) { return level < 0 ? 0 : (level > GUILD_MAX_LEVEL ? GUILD_MAX_LEVEL : level); }
inline int Bonus(int type, int level) {
 const Table& t = Storage();
 if (!t.installed) return CustomGuildCombatBonus(type, level);
 if (!t.master || !t.enabled || level < 1 || type < 0 || type >= POINT_MAX_NUM) return 0;
 return t.cells[Clamp(level)][type];
}
}
#endif
