#ifndef SEBAN_CLIENT_SYNC_V1_H
#define SEBAN_CLIENT_SYNC_V1_H
// MT2009_NASZE_KLIENT_Z_SERWERA_V1: serwer wysyla tabele systemow (kon, polimorfia) do wtyczki ROOT
// (sebansystems.py). Klient pokazuje te wartosci w opisach - po zmianie w panelu nie trzeba nowego ROOT.
// Polecenia: "SebanSys B" (poczatek), "SebanSys L <sys> <poziom> p:v,p:v" (punkty POINT_*, 1000 = odp. na bossy
// w promilach, 1001 = czas przemiany w s), "SebanSys E" (koniec). Wysylane przy wejsciu do gry i po "Zastosuj".
#include "seban_horse_rewards.h"
#include "seban_poly_rewards.h"
#include "seban_guild_rewards.h"
#include "seban_rank_rewards.h"
#include "seban_weekly_rewards.h"
#include "char.h"
#include <map>
#include <string>
#include <cstdio>
namespace SebanClientSync {
static const int RESIST_BOSS_PSEUDO = 1000, DURATION_PSEUDO = 1001;
typedef std::map<int, long> Row;
inline void Add(Row& r, int point, long value) { if (value) r[point] += value; }
inline void AddExtra(Row& r, const SebanExtra::Levels* ex, int level) {
 if (!ex) return; const std::vector< std::pair<int, long> >& v = ex->At(level);
 for (size_t i = 0; i < v.size(); ++i) Add(r, v[i].first, v[i].second);
}
inline void SendRow(LPCHARACTER ch, const char* sys, int level, const Row& r) {
 std::string chunk; char pair[48];
 for (Row::const_iterator it = r.begin(); it != r.end(); ++it) {
  snprintf(pair, sizeof(pair), "%s%d:%ld", chunk.empty() ? "" : ",", it->first, it->second);
  if (chunk.size() + strlen(pair) > 380) { ch->ChatPacket(CHAT_TYPE_COMMAND, "SebanSys L %s %d %s", sys, level, chunk.c_str()); chunk.clear(); snprintf(pair, sizeof(pair), "%d:%ld", it->first, it->second); }
  chunk += pair;
 }
 ch->ChatPacket(CHAT_TYPE_COMMAND, "SebanSys L %s %d %s", sys, level, chunk.empty() ? "-" : chunk.c_str());
}
inline void Send(LPCHARACTER ch) {
 if (!ch || !ch->IsPC() || !ch->GetDesc()) return;
 ch->ChatPacket(CHAT_TYPE_COMMAND, "SebanSys B");
 const SebanExtra::Levels* hx = SebanHorse::Extra();
 for (int level = 1; level <= 30; ++level) {
  Row r;
  Add(r, POINT_ATT_GRADE_BONUS, SebanHorse::Value(level, SebanHorse::ATTACK)); Add(r, POINT_MAX_HP, SebanHorse::Value(level, SebanHorse::HP));
  Add(r, POINT_ATTBONUS_MONSTER, SebanHorse::Value(level, SebanHorse::MONSTER)); Add(r, POINT_ATTBONUS_BOSS, SebanHorse::Value(level, SebanHorse::BOSS));
  Add(r, POINT_ATTBONUS_STONE, SebanHorse::Value(level, SebanHorse::STONE)); Add(r, POINT_MOV_SPEED, SebanHorse::Value(level, SebanHorse::MOVE));
  Add(r, POINT_RESIST_MONSTER_1000PCT, SebanHorse::Value(level, SebanHorse::RESIST_MONSTER)); Add(r, POINT_DEF_GRADE_BONUS, SebanHorse::Value(level, SebanHorse::DEFENSE));
  Add(r, POINT_ATT_SPEED, SebanHorse::Value(level, SebanHorse::SPEED)); Add(r, POINT_ATTBONUS_HUMAN, SebanHorse::Value(level, SebanHorse::HUMAN));
  Add(r, POINT_ST, SebanHorse::Value(level, SebanHorse::STRENGTH)); Add(r, POINT_HT, SebanHorse::Value(level, SebanHorse::VITALITY));
  Add(r, POINT_DX, SebanHorse::Value(level, SebanHorse::DEXTERITY)); Add(r, POINT_IQ, SebanHorse::Value(level, SebanHorse::INTELLIGENCE));
  Add(r, POINT_CRITICAL_PCT, SebanHorse::Value(level, SebanHorse::CRIT)); Add(r, POINT_PENETRATE_PCT, SebanHorse::Value(level, SebanHorse::PENETRATE));
  Add(r, POINT_ITEM_DROP_BONUS, SebanHorse::Value(level, SebanHorse::DROP)); Add(r, POINT_EXP_DOUBLE_BONUS, SebanHorse::Value(level, SebanHorse::EXP));
  Add(r, POINT_GOLD_DOUBLE_BONUS, SebanHorse::Value(level, SebanHorse::YANG));
  Add(r, POINT_RESIST_WARRIOR, SebanHorse::Value(level, SebanHorse::CLASSES)); Add(r, POINT_RESIST_ASSASSIN, SebanHorse::Value(level, SebanHorse::CLASSES));
  Add(r, POINT_RESIST_SURA, SebanHorse::Value(level, SebanHorse::CLASSES)); Add(r, POINT_RESIST_SHAMAN, SebanHorse::Value(level, SebanHorse::CLASSES));
  Add(r, POINT_ENCHANT_ELECT, SebanHorse::Value(level, SebanHorse::ELEMENTS)); Add(r, POINT_ENCHANT_FIRE, SebanHorse::Value(level, SebanHorse::ELEMENTS));
  Add(r, POINT_ENCHANT_ICE, SebanHorse::Value(level, SebanHorse::ELEMENTS)); Add(r, POINT_ENCHANT_WIND, SebanHorse::Value(level, SebanHorse::ELEMENTS));
  Add(r, POINT_ENCHANT_EARTH, SebanHorse::Value(level, SebanHorse::ELEMENTS)); Add(r, POINT_ENCHANT_DARK, SebanHorse::Value(level, SebanHorse::ELEMENTS));
  Add(r, RESIST_BOSS_PSEUDO, SebanHorse::Value(level, SebanHorse::RESIST_BOSS));
  AddExtra(r, hx, level);
  SendRow(ch, "kon", level, r);
 }
 const SebanExtra::Levels* px = SebanPoly::Extra();
 for (int level = 1; level <= 40; ++level) {
  const CustomPolyRewards p = SebanPoly::For(level); Row r;
  Add(r, POINT_ATT_GRADE_BONUS, p.attack); Add(r, POINT_DEF_GRADE_BONUS, p.defense);
  Add(r, POINT_ATTBONUS_MONSTER, p.monster); Add(r, POINT_RESIST_MONSTER_1000PCT, p.resistMonster * 10);
  Add(r, POINT_ATTBONUS_BOSS, p.boss); Add(r, POINT_ATTBONUS_STONE, p.stone);
  Add(r, POINT_ATT_SPEED, p.speed); Add(r, POINT_MOV_SPEED, p.moveSpeed);
  Add(r, DURATION_PSEUDO, SebanPoly::Duration(level, 0));
  AddExtra(r, px, level);
  SendRow(ch, "poli", level, r);
 }
 for (int level = 1; level <= GUILD_MAX_LEVEL; ++level) { // MT2009_NASZE_GILDIA_V1
  Row r; for (int p = 1; p < POINT_MAX_NUM; ++p) Add(r, p, SebanGuild::Bonus(p, level));
  SendRow(ch, "gildia", level, r);
 }
 const int rankTiers = SebanRank::Count(SebanRank::TIERS + 1) - 1;
 for (int tier = 1; tier <= rankTiers; ++tier) { // MT2009_NASZE_RANGI_V1 (1002 = prog rangi w punktach)
  Row r; std::vector< std::pair<int, long> > def;
  const std::vector< std::pair<int, long> >* src = &def;
  if (SebanRank::Installed()) src = &SebanRank::Row(tier); else SebanRank::DefaultRow(tier, def);
  for (size_t i = 0; i < src->size(); ++i) Add(r, (*src)[i].first, (*src)[i].second);
  r[1002] = SebanRank::From(tier, tier <= SebanRank::TIERS ? SebanRank::DEFAULT_FROM[tier] : 0);
  SendRow(ch, "rangi", tier, r);
 }
 for (int cat = 1; cat <= 8; ++cat) for (int place = 1; place <= 3; ++place) { // MT2009_NASZE_RANKING_V1 (slot = (kategoria-1)*3+miejsce)
  Row r;
  if (SebanWeekly::Installed()) { const std::vector< std::pair<int, long> >& v = SebanWeekly::Row(cat, place); for (size_t i = 0; i < v.size(); ++i) Add(r, v[i].first, v[i].second); }
  else {
   static const int pve[4] = {0, 10, 5, 3}, pct[4] = {0, 15, 8, 4}, hp[4] = {0, 2500, 2000, 1500};
   if (cat == 1 || cat == 2 || cat == 5) Add(r, POINT_ATTBONUS_MONSTER, pve[place]);
   if (cat == 3) Add(r, POINT_ATTBONUS_BOSS, pve[place]);
   if (cat == 4 || cat == 8) Add(r, POINT_ATTBONUS_HUMAN, pct[place]);
   if (cat == 8) Add(r, POINT_ATTBONUS_MONSTER, pct[place]);
   if (cat == 6) Add(r, POINT_MAX_HP, hp[place]);
   if (cat == 7) Add(r, POINT_ATT_GRADE_BONUS, 50);
  }
  SendRow(ch, "tydzien", (cat - 1) * 3 + place, r);
 }
 ch->ChatPacket(CHAT_TYPE_COMMAND, "SebanSys E");
}
}
#endif
