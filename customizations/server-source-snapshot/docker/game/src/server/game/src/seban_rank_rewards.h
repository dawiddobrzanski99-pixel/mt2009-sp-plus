#ifndef SEBAN_RANK_REWARDS_V1_H
#define SEBAN_RANK_REWARDS_V1_H
// MT2009_NASZE_RANGI_V1 (+V2: wlasne rangi): progi, nazwy i bonusy rang (Punkty Rangi) z panelu Seban (Systemy -> Rangi).
// Tresc: "master enabled", "F <prog1> ... <progN>" (N = 1..40 rang), opcjonalnie "N <ranga> <nazwa hex CP1250>",
// wiersze "B <ranga> <punkt POINT_*> <wartosc>".
// Bez konfiguracji z panelu dziala dotychczasowa tabela (12 rang, RANK_CUMULATIVE_REWARDS_V4).
#include "seban_bonus_extra.h"
#include "seban_sha256.h"
#include <sstream>
#include <string>
#include <vector>
#include <utility>
#include <iterator>
#include <cstdlib>
namespace SebanRank {
static const int TIERS = 12;		// wkompilowane rangi
static const int MAX_TIERS = 40;	// limit wlasnych rang z panelu
static const int DEFAULT_FROM[TIERS + 1] = {0, 0, 1000, 3000, 6000, 10000, 16000, 30000, 50000, 80000, 110000, 150000, 200000};
struct Table {
 bool installed, master, enabled; std::string revision; int count; int from[MAX_TIERS + 1]; std::string names[MAX_TIERS + 1]; SebanExtra::Levels rows;
 Table() : installed(false), master(true), enabled(true), count(TIERS) { for (int i = 0; i <= MAX_TIERS; ++i) from[i] = i <= TIERS ? DEFAULT_FROM[i] : 200000; rows.Reset(MAX_TIERS); }
};
inline bool Hex(const std::string& s, size_t n) { return s.size() == n && s.find_first_not_of("0123456789abcdef") == std::string::npos; }
inline bool Unhex(const std::string& in, std::string& out) {
 out.clear(); if (in.size() % 2 || in.size() > 96) return false;
 for (size_t i = 0; i < in.size(); i += 2) { char b[3] = {in[i], in[i + 1], 0}; char* e; long v = strtol(b, &e, 16); if (*e || v < 32 || v == '%') return false; out += static_cast<char>(v); }
 return true;
}
inline bool Parse(std::istream& in, Table& out) {
 std::string line, magic, digest, extra, tag; if (!std::getline(in, line)) return false;
 std::istringstream header(line); if (!(header >> magic >> digest) || header >> extra || magic != "SEBAN_RANK_V1" || !Hex(digest, 64)) return false;
 std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
 if (body.size() > 65536 || SebanHorse::Sha256(body) != digest) return false;
 std::istringstream input(body); Table candidate; int master, enabled;
 if (!std::getline(input, line)) return false;
 std::istringstream switches(line); if (!(switches >> master >> enabled) || switches >> extra || (master != 0 && master != 1) || (enabled != 0 && enabled != 1)) return false;
 if (!std::getline(input, line)) return false;
 std::istringstream f(line); if (!(f >> tag) || tag != "F") return false;
 candidate.from[0] = 0; candidate.count = 0; int v;
 while (f >> v) {
  if (candidate.count >= MAX_TIERS || v < 0 || v > 200000 || (candidate.count > 0 && v < candidate.from[candidate.count])) return false;
  candidate.from[++candidate.count] = v;
 }
 if (!f.eof() || candidate.count < 1) return false;
 // "N" (nazwy) przed wierszami "B"
 std::string rest, pending;
 while (std::getline(input, line)) {
  std::istringstream row(line); std::string t;
  if (!(row >> t)) continue;
  if (t == "N") { int tier; std::string hex, name; if (!(row >> tier >> hex) || row >> extra || tier < 1 || tier > candidate.count || !Unhex(hex, name)) return false; candidate.names[tier] = name; }
  else rest += line + "\n";
 }
 std::istringstream bonuses(rest);
 if (!SebanExtra::Parse(bonuses, candidate.count, candidate.rows)) return false;
 candidate.installed = true; candidate.master = master; candidate.enabled = enabled; candidate.revision = digest; out = candidate; return true;
}
inline bool ParseCommand(const std::string& raw, std::string& operation, Table& out) {
 if (raw.size() > 131072) return false;
 std::istringstream input(raw); std::string line, magic, extra;
 if (!std::getline(input, line)) return false;
 std::istringstream first(line); if (!(first >> magic >> operation) || first >> extra || magic != "SEBAN_RANK_REQUEST_V1" || !Hex(operation, 32)) return false;
 return Parse(input, out);
}
inline Table& Storage() { static Table table; return table; }
inline void Commit(const Table& table) { Storage() = table; }
inline bool Installed() { return Storage().installed; }
// Liczba rang + 1 (jak TIER_COUNT w playerbot_rank_points.h).
inline int Count(int original) { const Table& t = Storage(); return t.installed ? t.count + 1 : original; }
inline int From(int tier, int original) { const Table& t = Storage(); return t.installed ? (tier >= 0 && tier <= t.count ? t.from[tier] : 2000000000) : original; }
inline const char* Name(int tier, const char* original) { const Table& t = Storage(); if (!t.installed || tier < 1 || tier > t.count || t.names[tier].empty()) return original ? original : ""; return t.names[tier].c_str(); }
// Dotychczasowe bonusy (RewardValue w playerbot_rank_points.h) - dla klienta, gdy panel nic nie ustawil.
inline void DefaultRow(int stage, std::vector< std::pair<int, long> >& out) {
 static const int points[] = {POINT_DEF_GRADE_BONUS, POINT_RESIST_FIRE, POINT_RESIST_ICE, POINT_RESIST_WIND, POINT_RESIST_EARTH, POINT_RESIST_ELEC, POINT_RESIST_DARK,
  POINT_ENCHANT_FIRE, POINT_ENCHANT_ICE, POINT_ENCHANT_WIND, POINT_ENCHANT_EARTH, POINT_ENCHANT_ELECT, POINT_ENCHANT_DARK, POINT_ATT_SPEED, POINT_MOV_SPEED, POINT_ATTBONUS_STONE};
 out.clear();
 for (int i = 0; i < 16; ++i) {
  long v = i == 0 ? stage * 30 / 12 : i <= 12 ? stage * 20 / 12 : i <= 14 ? (stage / 2) * 10 / 6 : stage / 2;
  if (v > 0) out.push_back(std::make_pair(points[i], v));
 }
}
// Bonusy rangi `stage` wg panelu (pusty, gdy modul wylaczony).
inline const std::vector< std::pair<int, long> >& Row(int stage) {
 static const std::vector< std::pair<int, long> > none; const Table& t = Storage();
 if (!t.installed || !t.master || !t.enabled) return none;
 return t.rows.At(stage < 0 ? 0 : (stage > t.count ? t.count : stage));
}
}
#endif
