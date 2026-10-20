#ifndef SEBAN_RANK_LIVE_V1_H
#define SEBAN_RANK_LIVE_V1_H
// MT2009_NASZE_RANGI_V1: zegar odczytujacy /opt/m2spool/systems/rangi/request.txt,
// zatwierdza tabele i potwierdza status/<port>.json (schema SEBAN_RANK_V1). Bez restartu.
#include "seban_rank_rewards.h"
#include "seban_client_sync.h"
#include "char.h"
#include "char_manager.h"
#include "event.h"
#include "config.h"
#include "utils.h"
#include <fstream>
#include <vector>
#include <algorithm>
#include <ctime>
#include <cstdlib>
#include <cstdio>
#include <unistd.h>
#include <sys/time.h>
#include <sys/stat.h>
namespace SebanRankLive {
static LPEVENT clockEvent = NULL;
static std::vector<DWORD> pending;
static size_t cursor = 0;
static std::string operation, instance, error;
static bool applying = false;
inline const std::string& Root() {
 static const std::string root = std::string(std::getenv("M2_RATES_SPOOL") && *std::getenv("M2_RATES_SPOOL") ? std::getenv("M2_RATES_SPOOL") : "/opt/m2spool") + "/systems/rangi";
 return root;
}
inline void Status() {
 mkdir(Root().c_str(), 02770); mkdir((Root() + "/status").c_str(), 02770);
 std::ostringstream out; out << "{\"schema\":\"SEBAN_RANK_V1\",\"port\":" << mother_port << ",\"instance\":\"" << instance << "\",\"operation\":\"" << operation
  << "\",\"revision\":\"" << (SebanRank::Storage().installed ? SebanRank::Storage().revision : "defaults") << "\",\"state\":\""
  << (!error.empty() ? "error" : applying ? "applying" : operation.empty() ? "ready" : "applied") << "\",\"updated\":" << time(NULL)
  << ",\"processed\":" << cursor << ",\"total\":" << pending.size() << ",\"error\":\"" << error << "\"}\n";
 std::string path = Root() + "/status/" + std::to_string(mother_port) + ".json", temp = path + ".tmp." + std::to_string(getpid());
 { std::ofstream f(temp.c_str(), std::ios::binary); if (!f) return; f << out.str(); f.flush(); if (!f) { std::remove(temp.c_str()); return; } }
 chmod(temp.c_str(), 0660); if (std::rename(temp.c_str(), path.c_str())) std::remove(temp.c_str());
}
struct Collect { void operator()(LPCHARACTER ch) { if (ch && ch->IsPC()) pending.push_back(ch->GetPlayerID()); } };
inline void Tick() {
 std::string path = Root() + "/request.txt"; std::ifstream f(path.c_str(), std::ios::binary);
 if (f) {
  std::string raw; char buf[4096]; while (f && raw.size() <= 262144) { f.read(buf, sizeof(buf)); raw.append(buf, static_cast<size_t>(f.gcount())); }
  std::string nextOperation; SebanRank::Table* table = new SebanRank::Table();
  if (!SebanRank::ParseCommand(raw, nextOperation, *table)) error = "invalid_request";
  else if (nextOperation == operation && SebanRank::Storage().revision != table->revision) error = "operation_reused";
  else if (nextOperation != operation) {
   SebanRank::Commit(*table); operation = nextOperation; error.clear(); pending.clear(); cursor = 0;
   CHARACTER_MANAGER::instance().for_each_pc(Collect()); applying = true;
  } else error.clear();
  delete table;
 } else if (!operation.empty()) error = "request_missing";
 if (applying && error.empty()) {
  // Bonusy rangi to ukryte efekty (AFFECT_RANK_POINTS) - SyncBonuses je zdejmuje i naklada od nowa.
  size_t stop = std::min(pending.size(), cursor + 200);
  for (; cursor < stop; ++cursor) { LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pending[cursor]); if (ch && ch->IsPC()) { if (mt2009_rankp::Enabled() && mt2009_rankp::Counts(ch) && mt2009_rankp::Known(ch)) mt2009_rankp::Refresh(ch, -1, false); SebanClientSync::Send(ch); } }
  if (cursor == pending.size()) applying = false;
 }
 Status();
}
EVENTINFO(ClockInfo) {};
EVENTFUNC(Clock) { (void)event; (void)processing_time; Tick(); return PASSES_PER_SEC(1); }
inline void Start() {
 if (g_bAuthServer || clockEvent) return;
 struct timeval tv; gettimeofday(&tv, NULL); instance = SebanHorse::Sha256(std::to_string(getpid()) + ":rank:" + std::to_string(tv.tv_sec) + ":" + std::to_string(tv.tv_usec));
 // MT2009_NASZE_RANGI_EKSPORT_V1: wkompilowane rangi -> status/defaults.txt ("F progi", "N ranga nazwa_hex", "B ranga punkt wartosc").
 {
  std::ostringstream o; o << "F";
  for (int i = 1; i < mt2009_rankp::TIER_COUNT; ++i) o << ' ' << mt2009_rankp::TIERS[i].from;
  o << '\n';
  static const char digits[] = "0123456789abcdef";
  for (int i = 1; i < mt2009_rankp::TIER_COUNT; ++i) {
   std::string hex; for (const unsigned char* p = (const unsigned char*)mt2009_rankp::TIERS[i].name; *p; ++p) { hex += digits[*p >> 4]; hex += digits[*p & 15]; }
   o << "N " << i << ' ' << (hex.empty() ? "-" : hex) << '\n';
   std::vector< std::pair<int, long> > row; SebanRank::DefaultRow(i, row);
   for (size_t k = 0; k < row.size(); ++k) o << "B " << i << ' ' << row[k].first << ' ' << row[k].second << '\n';
  }
  mkdir(Root().c_str(), 02770); mkdir((Root() + "/status").c_str(), 02770);
  std::string path = Root() + "/status/defaults.txt", temp = path + ".tmp." + std::to_string(getpid());
  { std::ofstream f(temp.c_str(), std::ios::binary); if (f) { f << o.str(); f.flush(); } }
  chmod(temp.c_str(), 0660); if (std::rename(temp.c_str(), path.c_str())) std::remove(temp.c_str());
 }
 ClockInfo* info = AllocEventInfo<ClockInfo>(); clockEvent = event_create(Clock, info, PASSES_PER_SEC(1));
 Tick();
}
}
#endif
