#ifndef SEBAN_BONUS_EXTRA_V1_H
#define SEBAN_BONUS_EXTRA_V1_H
// MT2009_NASZE_BONUSY_WSZYSTKIE_V1: dowolne bonusy z gry (POINT_*) dopisywane do systemow z panelu Seban
// (Systemy -> Kon / Polimorfia / ...). Wiersze w tresci zadania: "B <poziom> <punkt> <wartosc>".
// Starsze tresci (bez wierszy B) dzialaja jak dotad.
#include "../../common/length.h"
#include <sstream>
#include <string>
#include <vector>
#include <utility>
namespace SebanExtra {
static const int MaxLines = 4000;
static const long MaxValue = 1000000;
// Punkty techniczne (poziom, PZ/PM biezace, yang, doswiadczenie, punkty statystyk, stany) - nie jako bonus.
inline bool Allowed(int point) {
 if (point <= 0 || point >= POINT_MAX_NUM) return false;
 switch (point) {
  case 1: case 2: case 3: case 4: case 5: case 7: case 9: case 11: case 20: case 24: case 25: case 26: case 27:
  case 29: case 30: case 31: case 35: case 36: case 102: case 108: case 109: case 112: case 113:
  case 125: case 126: case 127: case 128: case 129: return false;
 }
 return true;
}
struct Levels {
 std::vector< std::vector< std::pair<int, long> > > rows;
 void Reset(int maxLevel) { rows.assign(maxLevel + 1, std::vector< std::pair<int, long> >()); }
 const std::vector< std::pair<int, long> >& At(int level) const {
  static const std::vector< std::pair<int, long> > none;
  return level >= 0 && level < static_cast<int>(rows.size()) ? rows[level] : none;
 }
 long Sum(int level, int point) const { long v = 0; const std::vector< std::pair<int, long> >& r = At(level); for (size_t i = 0; i < r.size(); ++i) if (r[i].first == point) v += r[i].second; return v; }
};
// Czyta reszte tresci: puste linie albo "B poziom punkt wartosc"; ten sam punkt na poziomie tylko raz.
inline bool Parse(std::istream& input, int maxLevel, Levels& out) {
 Levels candidate; candidate.Reset(maxLevel); std::string line, tag, extra; int count = 0;
 while (std::getline(input, line)) {
  if (line.find_first_not_of(" \t\r") == std::string::npos) continue;
  std::istringstream row(line); int level, point; long value;
  if (!(row >> tag >> level >> point >> value) || row >> extra || tag != "B") return false;
  if (level < 1 || level > maxLevel || !Allowed(point) || value < -MaxValue || value > MaxValue || ++count > MaxLines) return false;
  std::vector< std::pair<int, long> >& r = candidate.rows[level];
  for (size_t i = 0; i < r.size(); ++i) if (r[i].first == point) return false;
  if (value) r.push_back(std::make_pair(point, value));
 }
 out = candidate; return true;
}
}
#endif
