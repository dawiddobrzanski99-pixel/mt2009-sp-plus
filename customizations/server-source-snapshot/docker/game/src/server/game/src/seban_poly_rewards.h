#ifndef SEBAN_POLY_REWARDS_V1_H
#define SEBAN_POLY_REWARDS_V1_H
// MT2009_NASZE_POLIMORFIA_V1: tabela bonusow polimorfii z panelu Seban (Systemy -> Polimorfia).
// Bez konfiguracji z panelu dziala dotychczasowa tabela (CustomPolyForLevel / CustomPolyDuration).
#include "custom_horse_polymorph_rewards.h"
#include "seban_sha256.h"
#include "seban_bonus_extra.h" // MT2009_NASZE_BONUSY_WSZYSTKIE_V1
#include <sstream>
#include <string>
#include <cstring>
#include <iterator>
namespace SebanPoly {
enum Key { ATTACK, DEFENSE, MONSTER, RESIST_MONSTER, BOSS, STONE, SPEED, MOVE, DURATION, COUNT };
static const int Limits[COUNT] = {1000, 1000, 100, 100, 100, 100, 100, 200, 86400};
struct Table {
 bool installed, master, enabled; int cells[41][COUNT]; std::string revision; SebanExtra::Levels extra;
 Table() : installed(false), master(true), enabled(true) { std::memset(cells, 0, sizeof(cells)); }
};
inline bool Hex(const std::string& s, size_t n) { return s.size() == n && s.find_first_not_of("0123456789abcdef") == std::string::npos; }
inline bool Parse(std::istream& in, Table& out) {
 std::string line, magic, digest, extra; if (!std::getline(in, line)) return false;
 std::istringstream header(line); if (!(header >> magic >> digest) || header >> extra || magic != "SEBAN_POLY_V1" || !Hex(digest, 64)) return false;
 std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
 if (body.size() > 32768 || SebanHorse::Sha256(body) != digest) return false;
 std::istringstream input(body); Table candidate; int master, enabled;
 if (!std::getline(input, line)) return false;
 std::istringstream switches(line); if (!(switches >> master >> enabled) || switches >> extra || (master != 0 && master != 1) || (enabled != 0 && enabled != 1)) return false;
 for (int level = 1; level <= 40; ++level) {
  if (!std::getline(input, line)) return false;
  std::istringstream row(line); int actual; if (!(row >> actual) || actual != level) return false;
  for (int k = 0; k < COUNT; ++k) if (!(row >> candidate.cells[level][k]) || candidate.cells[level][k] < 0 || candidate.cells[level][k] > Limits[k]) return false;
  if (row >> extra) return false;
 }
 if (!SebanExtra::Parse(input, 40, candidate.extra)) return false;
 candidate.installed = true; candidate.master = master; candidate.enabled = enabled; candidate.revision = digest; out = candidate; return true;
}
inline bool ParseCommand(const std::string& raw, std::string& operation, Table& out) {
 if (raw.size() > 65536) return false;
 std::istringstream input(raw); std::string line, magic, extra;
 if (!std::getline(input, line)) return false;
 std::istringstream first(line); if (!(first >> magic >> operation) || first >> extra || magic != "SEBAN_POLY_REQUEST_V1" || !Hex(operation, 32)) return false;
 return Parse(input, out);
}
inline Table& Storage() { static Table table; return table; }
inline void Commit(const Table& table) { Storage() = table; }
inline int Clamp(int level) { return level < 0 ? 0 : (level > 40 ? 40 : level); }
inline const SebanExtra::Levels* Extra() { const Table& t = Storage(); return t.installed && t.master && t.enabled ? &t.extra : NULL; }
inline CustomPolyRewards For(int level) {
 const Table& t = Storage();
 if (!t.installed) return CustomPolyForLevel(level);
 CustomPolyRewards r = {0, 0, 0, 0, 0, 0, 0, 0};
 if (!t.master || !t.enabled || level <= 0) return r;
 const int* c = t.cells[Clamp(level)];
 r.attack = c[ATTACK]; r.defense = c[DEFENSE]; r.monster = c[MONSTER]; r.resistMonster = c[RESIST_MONSTER];
 r.boss = c[BOSS]; r.stone = c[STONE]; r.speed = c[SPEED]; r.moveSpeed = c[MOVE];
 return r;
}
// 0 w tabeli = czas z gry (marmur / ksiega).
inline long Duration(int level, long original) {
 const Table& t = Storage();
 if (!t.installed) return CustomPolyDuration(level, original);
 if (!t.master || level <= 0) return original;
 const int d = t.cells[Clamp(level)][DURATION];
 return d > 0 ? d : original;
}
}
#endif
