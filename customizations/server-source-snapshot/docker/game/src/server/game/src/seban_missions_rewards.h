// MT2009_NASZE_MISJE_V2: dowolne nagrody jednorazowe etapow (Polowania, Metinologia, Bossologia) z panelu.
// Wiersz "R <hunting|metin|boss> <id> <yang> <vnum:ilosc,...|->". Wydawane raz po ukonczeniu etapu
// (flagi custom_mission_loot_v2.*, licznik wydanych sztuk - zmiana ilosci w panelu dodaje tylko roznice).
// Wklejane w mission_panel_impl.h przed GrantMissionExtras.
const SebanReward* SebanRewardFor(const char* kind, int id) {
 SebanMissionTable* t = SebanMissionCurrent(); if (!t) return nullptr;
 for (const auto& r : t->rewards) if (r.kind == kind && r.id == id) return &r;
 return nullptr;
}
bool SebanStageDone(quest::PC* pc, const std::string& kind, int id) {
 if (kind == "hunting") { for (const auto& h : Hunts()) if (h.id == id) return Done(pc, h); return false; }
 for (const auto& m : Masters()) if (kind == m.kind && m.id == id) return MasterDone(pc, m);
 return false;
}
void SebanGrantRewards(LPCHARACTER ch, quest::PC* pc) {
 SebanMissionTable* t = SebanMissionCurrent(); if (!t) return;
 for (const auto& r : t->rewards) {
  if (!SebanStageDone(pc, r.kind, r.id)) continue;
  std::string base = "custom_mission_loot_v2." + r.kind + "_" + std::to_string(r.id) + "_";
  long gold = std::max(0L, r.yang - (long)pc->GetFlag(base + "yang"));
  if (gold && ch->GetGold() <= GOLD_MAX - gold) { ch->PointChange(POINT_GOLD, gold); ch->SetQuestFlag(base + "yang", r.yang); pc->Save(); ch->Save(); }
  for (const auto& item : r.items) {
   std::string flag = base + "item_" + std::to_string(item.first);
   int count = std::max(0, item.second - pc->GetFlag(flag));
   if (count && ITEM_MANAGER::instance().GetTable(item.first) && ch->AutoGiveItem(item.first, count)) { ch->SetQuestFlag(flag, pc->GetFlag(flag) + count); pc->Save(); ch->Save(); }
  }
 }
}
// "MP extra <kind> <id> <yang> <vnum:ilosc:nazwa_hex,...>" - klasyczne nagrody (X) + nagrody z panelu (R) w jednym wierszu.
void SebanSendExtra(LPCHARACTER ch, const char* kind, int id, const MissionExtra* e) {
 const SebanReward* r = SebanRewardFor(kind, id);
 long yang = (e ? e->yang : 0) + (r ? r->yang : 0);
 std::ostringstream items; bool first = true;
 if (e) for (const auto& item : ExtraItems(*e)) { if (item.second <= 0) continue; items << (first ? "" : ",") << item.first << ":" << item.second << ":" << Hex(BossGiftName(item.first)); first = false; }
 if (r) for (const auto& item : r->items) {
  const TItemTable* proto = ITEM_MANAGER::instance().GetTable(item.first); if (!proto) continue;
  items << (first ? "" : ",") << item.first << ":" << item.second << ":" << Hex(proto->szLocaleName); first = false;
 }
 if (!yang && first) return;
 ch->ChatPacket(CHAT_TYPE_COMMAND, "MP extra %s %d %ld %s", kind, id, yang, first ? "-" : items.str().c_str());
}
