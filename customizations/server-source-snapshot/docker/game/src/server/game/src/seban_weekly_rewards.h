#ifndef SEBAN_WEEKLY_REWARDS_V1_H
#define SEBAN_WEEKLY_REWARDS_V1_H
// MT2009_NASZE_RANKING_V1: bonusy tytulow rankingu tygodnia z panelu Seban (Systemy -> Ranking tygodnia).
// Tresc: "master enabled", potem "B <slot> <punkt POINT_*> <wartosc>", slot = (kategoria-1)*3 + miejsce (1-24).
// Bez konfiguracji z panelu dziala dotychczasowa tabela (CUSTOM_WEEKLY_REWARDS_V2).
#include "seban_bonus_extra.h"
#include "seban_sha256.h"
#include <sstream>
#include <string>
#include <cstring>
#include <iterator>
namespace SebanWeekly {
static const int SLOTS = 24;
struct Table {
 bool installed, master, enabled; std::string revision; SebanExtra::Levels rows; int cells[SLOTS + 1][POINT_MAX_NUM];
 Table() : installed(false), master(true), enabled(true) { rows.Reset(SLOTS); std::memset(cells, 0, sizeof(cells)); }
};
inline bool Hex(const std::string& s, size_t n) { return s.size() == n && s.find_first_not_of("0123456789abcdef") == std::string::npos; }
inline bool Parse(std::istream& in, Table& out) {
 std::string line, magic, digest, extra; if (!std::getline(in, line)) return false;
 std::istringstream header(line); if (!(header >> magic >> digest) || header >> extra || magic != "SEBAN_WEEKLY_V1" || !Hex(digest, 64)) return false;
 std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
 if (body.size() > 131072 || SebanHorse::Sha256(body) != digest) return false;
 std::istringstream input(body); int master, enabled;
 if (!std::getline(input, line)) return false;
 std::istringstream switches(line); if (!(switches >> master >> enabled) || switches >> extra || (master != 0 && master != 1) || (enabled != 0 && enabled != 1)) return false;
 Table* candidate = new Table();
 if (!SebanExtra::Parse(input, SLOTS, candidate->rows)) { delete candidate; return false; }
 for (int level = 1; level <= SLOTS; ++level) {
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
 std::istringstream first(line); if (!(first >> magic >> operation) || first >> extra || magic != "SEBAN_WEEKLY_REQUEST_V1" || !Hex(operation, 32)) return false;
 return Parse(input, out);
}
inline Table& Storage() { static Table* table = new Table(); return *table; }
inline void Commit(const Table& table) { Storage() = table; }
inline int Clamp(int level) { return level < 0 ? 0 : (level > SLOTS ? SLOTS : level); }
inline bool Installed() { return Storage().installed; }
// Bonusy miejsca place (1-3) w kategorii cat (1-8); pusty, gdy modul wylaczony.
inline const std::vector< std::pair<int, long> >& Row(int cat, int place) {
 static const std::vector< std::pair<int, long> > none; const Table& t = Storage();
 if (!t.installed || !t.master || !t.enabled || cat < 1 || cat > 8 || place < 1 || place > 3) return none;
 return t.rows.At((cat - 1) * 3 + place);
}
inline int Bonus(int type, int level) {
 const Table& t = Storage();
 if (!t.master || !t.enabled || level < 1 || type < 0 || type >= POINT_MAX_NUM) return 0;
 return t.cells[Clamp(level)][type];
}
}
#endif
