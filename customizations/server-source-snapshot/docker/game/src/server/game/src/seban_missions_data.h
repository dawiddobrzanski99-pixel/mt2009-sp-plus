// MT2009_NASZE_MISJE_V1: tabele misji Ctrl+N (Polowania, Metinologia, Bossologia) z panelu Seban
// (Systemy -> Misje). Wklejane w mission_panel_impl.h (anonimowa przestrzen nazw) po plikach *-data.inc.
// Bez konfiguracji z panelu dzialaja wkompilowane tabele (hunts, masters, missionExtras, metinFinal, bossFinal).
// Tresc: "master enabled", potem wiersze:
//   H id poziom rasa mapa ilosc nazwa(hex) miejsce(hex) opis(hex) bonusy
//   M rodzaj(metin|boss) id poziom rasa poziom_metina ilosc nazwa(hex) miejsce(hex) bonusy
//   X rodzaj id yang zwoj_blog zaczarowanie wzmocnienie kupony
//   F rodzaj bonusy                    (nagroda za cala sciezke)
// bonusy = "p:v,p:v" (punkty POINT_*, do 8) albo "-". Postep graczy jest liczony po id etapu.
// MT2009_NASZE_MISJE_V2: "R <hunting|metin|boss> <id> <yang> <vnum:ilosc,...|->" - dowolne nagrody jednorazowe etapu.
struct SebanReward { std::string kind; int id; long yang; std::vector< std::pair<DWORD, int> > items; };
struct SebanMissionTable {
 std::vector<Hunt> hunts; std::vector<Master> masters; std::vector<MissionExtra> extras; std::vector<SebanReward> rewards;
 Bonus metinF[8], bossF[8]; std::list<std::string> strings; std::string revision; bool enabled, bots;
 SebanMissionTable() : enabled(true), bots(true) { std::memset(metinF, 0, sizeof(metinF)); std::memset(bossF, 0, sizeof(bossF)); }
 const char* Keep(const std::string& s) { strings.push_back(s); return strings.back().c_str(); }
};
// Zatwierdzone tabele nie sa zwalniane (wskazniki na nazwy zostaja wazne); zmiana z panelu to kilka KB.
SebanMissionTable*& SebanMissionCurrent() { static SebanMissionTable* t = NULL; return t; }
// MT2009_NASZE_MISJE_BOTY_V1: boty robia Polowania/Metinologie/Bossologie (stale bonusy, bez nagrod jednorazowych).
bool SebanBotsAllowed() { SebanMissionTable* t = SebanMissionCurrent(); return !t || t->bots; }
const std::vector<Hunt>& Hunts() { static const std::vector<Hunt> def(std::begin(hunts), std::end(hunts)); SebanMissionTable* t = SebanMissionCurrent(); return t ? t->hunts : def; }
const std::vector<Master>& Masters() { static const std::vector<Master> def(std::begin(masters), std::end(masters)); SebanMissionTable* t = SebanMissionCurrent(); return t ? t->masters : def; }
const std::vector<MissionExtra>& Extras() { static const std::vector<MissionExtra> def(std::begin(missionExtras), std::end(missionExtras)); SebanMissionTable* t = SebanMissionCurrent(); return t ? t->extras : def; }
bool SebanUnhex(const std::string& in, std::string& out) {
 out.clear(); if (in == "-") return true; if (in.size() % 2 || in.size() > 256) return false;
 for (size_t i = 0; i < in.size(); i += 2) { char b[3] = {in[i], in[i + 1], 0}; char* e; long v = strtol(b, &e, 16); if (*e) return false; out += static_cast<char>(v); }
 return true;
}
bool SebanBonuses(const std::string& in, Bonus out[8]) {
 std::memset(out, 0, sizeof(Bonus) * 8); if (in == "-") return true;
 std::istringstream s(in); std::string part; int n = 0;
 while (std::getline(s, part, ',')) {
  int p; long v; char colon;
  std::istringstream x(part); if (!(x >> p >> colon >> v) || colon != ':' || n >= 8 || !SebanExtra::Allowed(p) || v < 0 || v > 1000000) return false;
  out[n].point = p; out[n].value = v; ++n;
 }
 return true;
}
bool SebanParseMissions(const std::string& body, SebanMissionTable& t) {
 std::istringstream in(body); std::string line; int master, enabled;
 if (!std::getline(in, line)) return false;
 { std::istringstream sw(line); if (!(sw >> master >> enabled)) return false; int bots = 1; if (sw >> bots) t.bots = bots != 0; }
 t.enabled = master && enabled;
 while (std::getline(in, line)) {
  if (line.find_first_not_of(" \t\r") == std::string::npos) continue;
  std::istringstream row(line); std::string tag; row >> tag;
  if (tag == "H") {
   Hunt h; std::string name, loc, label, bonus, a, b, c;
   if (!(row >> h.id >> h.level >> h.race >> h.map >> h.kills >> a >> b >> c >> bonus) || h.kills < 1 || h.kills > 1000000) return false;
   if (!SebanUnhex(a, name) || !SebanUnhex(b, loc) || !SebanUnhex(c, label) || !SebanBonuses(bonus, h.bonus)) return false;
   for (const auto& o : t.hunts) if (o.id == h.id) return false;
   h.name = t.Keep(name); h.location = t.Keep(loc); h.label = t.Keep(label); t.hunts.push_back(h);
  } else if (tag == "M") {
   Master m; std::string kind, name, loc, bonus, a, b;
   if (!(row >> kind >> m.id >> m.level >> m.race >> m.targetLevel >> m.kills >> a >> b >> bonus) || (kind != "metin" && kind != "boss") || m.kills < 1 || m.kills > 1000000 || m.id == 99999) return false;
   if (!SebanUnhex(a, name) || !SebanUnhex(b, loc) || !SebanBonuses(bonus, m.bonus)) return false;
   for (const auto& o : t.masters) if (o.id == m.id && kind == o.kind) return false;
   m.kind = t.Keep(kind); m.name = t.Keep(name); m.location = t.Keep(loc); t.masters.push_back(m);
  } else if (tag == "X") {
   MissionExtra e; std::string kind;
   if (!(row >> kind >> e.id >> e.yang >> e.bless >> e.change >> e.add >> e.coupons) || (kind != "metin" && kind != "boss")) return false;
   if (e.yang < 0 || e.yang > 2000000000L || e.bless < 0 || e.change < 0 || e.add < 0 || e.coupons < 0 || e.bless > 200 || e.change > 200 || e.add > 200 || e.coupons > 200) return false;
   e.kind = t.Keep(kind); t.extras.push_back(e);
  } else if (tag == "R") {
   SebanReward r; std::string items;
   if (!(row >> r.kind >> r.id >> r.yang >> items) || (r.kind != "hunting" && r.kind != "metin" && r.kind != "boss") || r.yang < 0 || r.yang > 2000000000L) return false;
   if (items != "-") {
    std::istringstream s(items); std::string part;
    while (std::getline(s, part, ',')) {
     unsigned long v; int c; char colon; std::istringstream x(part);
     if (!(x >> v >> colon >> c) || colon != ':' || !v || c < 1 || c > 200 || r.items.size() >= 10) return false;
     r.items.push_back(std::make_pair((DWORD)v, c));
    }
   }
   for (const auto& o : t.rewards) if (o.kind == r.kind && o.id == r.id) return false;
   t.rewards.push_back(r);
  } else if (tag == "F") {
   std::string kind, bonus; if (!(row >> kind >> bonus) || (kind != "metin" && kind != "boss")) return false;
   if (!SebanBonuses(bonus, kind == "metin" ? t.metinF : t.bossF)) return false;
  } else return false;
  std::string extra; if (row >> extra) return false;
 }
 if (!t.enabled) { t.hunts.clear(); t.masters.clear(); t.extras.clear(); t.rewards.clear(); std::memset(t.metinF, 0, sizeof(t.metinF)); std::memset(t.bossF, 0, sizeof(t.bossF)); }
 return true;
}
// Eksport wkompilowanych tabel dla panelu (wartosci domyslne edytora): systems/misje/status/defaults.txt.
std::string SebanHexText(const char* s) { const char* d = "0123456789abcdef"; std::string out; for (const unsigned char* p = (const unsigned char*)s; *p; ++p) { out += d[*p >> 4]; out += d[*p & 15]; } return out.empty() ? "-" : out; }
std::string SebanBonusText(const Bonus b[8]) { std::ostringstream o; bool first = true; for (int i = 0; i < 8; ++i) if (b[i].point > 0 && b[i].value > 0) { o << (first ? "" : ",") << b[i].point << ':' << b[i].value; first = false; } return first ? "-" : o.str(); }
std::string SebanDefaultsText() {
 std::ostringstream o; o << "1 1\n";
 for (const auto& h : hunts) o << "H " << h.id << ' ' << h.level << ' ' << h.race << ' ' << h.map << ' ' << h.kills << ' ' << SebanHexText(h.name) << ' ' << SebanHexText(h.location) << ' ' << SebanHexText(h.label) << ' ' << SebanBonusText(h.bonus) << '\n';
 for (const auto& m : masters) o << "M " << m.kind << ' ' << m.id << ' ' << m.level << ' ' << m.race << ' ' << m.targetLevel << ' ' << m.kills << ' ' << SebanHexText(m.name) << ' ' << SebanHexText(m.location) << ' ' << SebanBonusText(m.bonus) << '\n';
 for (const auto& e : missionExtras) o << "X " << e.kind << ' ' << e.id << ' ' << e.yang << ' ' << e.bless << ' ' << e.change << ' ' << e.add << ' ' << e.coupons << '\n';
 o << "F metin " << SebanBonusText(metinFinal) << '\n' << "F boss " << SebanBonusText(bossFinal) << '\n';
 return o.str();
}
