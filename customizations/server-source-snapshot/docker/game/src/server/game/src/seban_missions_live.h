// MT2009_NASZE_MISJE_V1: zegar misji (systems/misje/request.txt -> status/<port>.json, schema SEBAN_MISSIONS_V1).
// Wklejany w mission_panel_impl.h po Send(); po zmianie przelicza bonusy misji graczy online (Sync).
namespace seban_live {
LPEVENT clockEvent = NULL; std::vector<DWORD> pending; size_t cursor = 0; std::string operation, instance, error; bool applying = false;
const std::string& Root() {
 static const std::string root = std::string(std::getenv("M2_RATES_SPOOL") && *std::getenv("M2_RATES_SPOOL") ? std::getenv("M2_RATES_SPOOL") : "/opt/m2spool") + "/systems/misje";
 return root;
}
void WriteFile(const std::string& path, const std::string& text) {
 std::string temp = path + ".tmp." + std::to_string(getpid());
 { std::ofstream f(temp.c_str(), std::ios::binary); if (!f) return; f << text; f.flush(); if (!f) { std::remove(temp.c_str()); return; } }
 chmod(temp.c_str(), 0660); if (std::rename(temp.c_str(), path.c_str())) std::remove(temp.c_str());
}
void Status() {
 mkdir(Root().c_str(), 02770); mkdir((Root() + "/status").c_str(), 02770);
 SebanMissionTable* t = SebanMissionCurrent();
 std::ostringstream out; out << "{\"schema\":\"SEBAN_MISSIONS_V1\",\"port\":" << mother_port << ",\"instance\":\"" << instance << "\",\"operation\":\"" << operation
  << "\",\"revision\":\"" << (t ? t->revision : "defaults") << "\",\"state\":\""
  << (!error.empty() ? "error" : applying ? "applying" : operation.empty() ? "ready" : "applied") << "\",\"updated\":" << time(NULL)
  << ",\"processed\":" << cursor << ",\"total\":" << pending.size() << ",\"error\":\"" << error << "\"}\n";
 WriteFile(Root() + "/status/" + std::to_string(mother_port) + ".json", out.str());
}
bool Hex64(const std::string& s) { return s.size() == 64 && s.find_first_not_of("0123456789abcdef") == std::string::npos; }
bool ParseCommand(const std::string& raw, std::string& op, SebanMissionTable& t) {
 if (raw.size() > 524288) return false;
 std::istringstream in(raw); std::string line, magic, digest, extra;
 if (!std::getline(in, line)) return false;
 { std::istringstream a(line); if (!(a >> magic >> op) || a >> extra || magic != "SEBAN_MISSIONS_REQUEST_V1" || op.size() != 32 || op.find_first_not_of("0123456789abcdef") != std::string::npos) return false; }
 if (!std::getline(in, line)) return false;
 { std::istringstream b(line); if (!(b >> magic >> digest) || b >> extra || magic != "SEBAN_MISSIONS_V1" || !Hex64(digest)) return false; }
 std::string body((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
 if (SebanHorse::Sha256(body) != digest || !SebanParseMissions(body, t)) return false;
 t.revision = digest; return true;
}
struct Collect { void operator()(LPCHARACTER ch) { if (ch && ch->IsPC()) pending.push_back(ch->GetPlayerID()); } };
void Tick() {
 std::ifstream f((Root() + "/request.txt").c_str(), std::ios::binary);
 if (f) {
  std::string raw; char buf[4096]; while (f && raw.size() <= 524288) { f.read(buf, sizeof(buf)); raw.append(buf, static_cast<size_t>(f.gcount())); }
  std::string next; SebanMissionTable* t = new SebanMissionTable();
  SebanMissionTable* cur = SebanMissionCurrent();
  if (!ParseCommand(raw, next, *t)) { error = "invalid_request"; delete t; }
  else if (next == operation && (!cur || cur->revision != t->revision)) { error = "operation_reused"; delete t; }
  else if (next != operation) {
   SebanMissionCurrent() = t; operation = next; error.clear(); pending.clear(); cursor = 0;
   CHARACTER_MANAGER::instance().for_each_pc(Collect()); applying = true;
  } else { error.clear(); delete t; }
 } else if (!operation.empty()) error = "request_missing";
 if (applying && error.empty()) {
  size_t stop = std::min(pending.size(), cursor + 100);
  for (; cursor < stop; ++cursor) { LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pending[cursor]); if (quest::PC* pc = Ready(ch)) Sync(ch, pc); }
  if (cursor == pending.size()) applying = false;
 }
 Status();
}
EVENTINFO(ClockInfo) {};
EVENTFUNC(Clock) { (void)event; (void)processing_time; Tick(); return PASSES_PER_SEC(1); }
}
