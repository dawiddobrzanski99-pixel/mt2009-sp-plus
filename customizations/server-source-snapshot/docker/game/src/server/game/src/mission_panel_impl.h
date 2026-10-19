// MISSION_PANEL_HUNTING_V1 - compiled once after quest_bonus_preview_impl.h.
#include "mission_panel.h"
#include "utils.h"
#include "playerbot_collector.h"
#include "char_manager.h"
#include "mob_manager.h"
#include "event.h"
#include <algorithm>
namespace mission_panel {
namespace {
const DWORD HUNT_AFFECT=64000; // dedicated aggregate; explicitly retained on death.
struct Bonus{int point;long value;};
struct Hunt{int id,level;DWORD race;long map;int kills;const char* name;const char* location;const char* label;Bonus bonus[8];};
#include "hunt-data.inc"
// MASTERIES_V2
struct Master{const char* kind;int id,level;DWORD race;int targetLevel,kills;const char* name;const char* location;Bonus bonus[8];};
#include "master-data.inc"
struct MissionExtra{const char* kind;int id;long yang;int bless,change,add,coupons;};
#include "boss-extra-data.inc"
#include "legacy-boss-data-v15.inc"
const Bonus (&FinalRewards(const char* kind))[8]{if(std::string(kind)=="metin")return metinFinal;return bossFinal;}
std::string MasterFlag(const Master& m,const char* what){return std::string("custom_masteries_v1.")+m.kind+"_"+what+"_"+std::to_string(m.id);}
bool MasterDone(quest::PC* pc,const Master& m){return pc->GetFlag(MasterFlag(m,"done"))!=0;}
// SEQUENTIAL_MASTERIES_V8: only the first unfinished stage can start or count kills.
const Master* NextMaster(quest::PC* pc,const char* kind){for(const auto& m:masters)if(std::string(m.kind)==kind && !MasterDone(pc,m))return &m;return nullptr;}
bool AllDone(quest::PC* pc,const char* kind){for(const auto& m:masters)if(std::string(m.kind)==kind && !MasterDone(pc,m))return false;return true;}
// BOSS_TRACK_30_V15: historical bonuses are a floor, never a second award.
std::string BossMigrationFlag(const char* what){return std::string("custom_boss30_v15.")+what;}
std::string LegacyBonusFlag(int point){return BossMigrationFlag("earned_")+std::to_string(point);}
void MasterTotals(quest::PC* pc,std::map<int,long>& earned,std::map<int,long>& left){
 std::map<int,long> bossEarned,bossMax;
 for(const auto& m:masters)for(const auto& b:m.bonus)if(b.point>0 && b.value>0){
  if(std::string(m.kind)=="boss"){bossMax[b.point]+=b.value;if(MasterDone(pc,m))bossEarned[b.point]+=b.value;}
  else (MasterDone(pc,m)?earned:left)[b.point]+=b.value;
 }
 for(const char* kind:{"metin","boss"})for(const auto& b:FinalRewards(kind))if(b.point>0){
  if(std::string(kind)=="boss"){bossMax[b.point]+=b.value;if(AllDone(pc,kind))bossEarned[b.point]+=b.value;}
  else (AllDone(pc,kind)?earned:left)[b.point]+=b.value;
 }
 for(const auto& b:bossMax){long value=std::min(b.second,std::max(bossEarned[b.first],(long)pc->GetFlag(LegacyBonusFlag(b.first))));if(value>0)earned[b.first]+=value;if(b.second>value)left[b.first]+=b.second-value;}
}
void MigrateBoss30(LPCHARACTER ch,quest::PC* pc){
 if(pc->GetFlag(BossMigrationFlag("done")))return;
 std::map<int,long> legacyEarned;bool all=true;long coupons=0;
 for(const auto& m:legacyBossMastersV15){
  bool done=MasterDone(pc,m);all=all && done;
  if(done)for(const auto& b:m.bonus)if(b.point>0 && b.value>0)legacyEarned[b.point]+=b.value;
  std::string claim="custom_mission_loot_v1.boss_"+std::to_string(m.id)+"_item_80017";
  coupons+=std::max(0,pc->GetFlag(claim));
 }
 if(all)for(const auto& b:bossFinal)if(b.point>0)legacyEarned[b.point]+=b.value;
 for(const auto& b:legacyEarned)ch->SetQuestFlag(LegacyBonusFlag(b.first),b.second);
 ch->SetQuestFlag(BossMigrationFlag("coupons"),std::min(40L,coupons));
 for(const auto& m:masters)if(std::string(m.kind)=="boss"){
  // Same VNUM retains count and completion. Fully completed old track stays completed.
  if(all){ch->SetQuestFlag(MasterFlag(m,"done"),1);ch->SetQuestFlag(MasterFlag(m,"count"),std::max(m.kills,pc->GetFlag(MasterFlag(m,"count"))));}
  if(!MasterDone(pc,m))continue;
  const MissionExtra* e=nullptr;for(const auto& candidate:missionExtras)if(std::string(candidate.kind)=="boss" && candidate.id==m.id){e=&candidate;break;}
  if(!e)continue;
  std::string base="custom_mission_loot_v1.boss_"+std::to_string(m.id)+"_";
  // Completed historical stages keep paid values; suppress a second payout from rebalancing.
  bool historical=false;for(const auto& prior:legacyBossMastersV15)if(prior.id==m.id && MasterDone(pc,prior)){historical=true;break;}
  if(!historical && !all)continue;
  if(!historical || pc->GetFlag(base+"yang")>0)ch->SetQuestFlag(base+"yang",std::max(e->yang,(long)pc->GetFlag(base+"yang")));
  for(const auto& gift:std::vector<std::pair<DWORD,int>>{{25040,e->bless},{71284,e->change},{71285,e->add},{80017,e->coupons}}){std::string flag=base+"item_"+std::to_string(gift.first);if(!historical || pc->GetFlag(flag)>0)ch->SetQuestFlag(flag,std::max(gift.second,pc->GetFlag(flag)));}
 }
 ch->SetQuestFlag(BossMigrationFlag("done"),1);pc->Save();
}

struct Bio{const char* quest;int level;DWORD item;int required;};
const Bio bios[]={{"collect_quest_lv30",30,30006,10},{"collect_quest_lv40",40,30047,15},{"collect_quest_lv50",50,30015,15},{"collect_quest_lv60",60,30050,20},{"collect_quest_lv70",70,30165,25},{"collect_quest_lv80",80,30166,30},{"collect_quest_lv85",85,30167,40},{"collect_quest_lv90",90,30168,50}};
quest::PC* Ready(LPCHARACTER ch){
 if(!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot() || !ch->IsLoadedAffect())return nullptr;
 quest::PC* pc=quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());return pc && pc->IsLoaded()?pc:nullptr;
}
std::string Flag(const char* kind,int id){return std::string("custom_hunting_v1.")+kind+std::to_string(id);}
bool Done(quest::PC* pc,const Hunt& h){return pc->GetFlag(Flag("done_",h.id))!=0;}
int Progress(quest::PC* pc,const Hunt& h){return std::max(0,std::min(h.kills,pc->GetFlag(Flag("count_",h.id))));}
long BaseMap(long m){return m>=10000?m/10000:m;}
bool MapMatch(long map,long want){map=BaseMap(map);return map==want || (want==1 && (map==21 || map==41)) || (want==3 && (map==23 || map==43));}
const Hunt* ByID(int id){for(const auto& h:hunts)if(h.id==id)return &h;return nullptr;}
// SEQUENTIAL_HUNTING_V1: browsing allowed, starting/kills only for first unfinished stage.
const Hunt* NextHunt(quest::PC* pc){for(const auto& h:hunts)if(!Done(pc,h))return &h;return nullptr;}
const char* BossGiftName(DWORD vnum){switch(vnum){case 25040:return "Zwoj Blogoslawienstwa";case 71284:return "Zaczarowanie Przedmiotu";case 71285:return "Wzmocnienie Przedmiotu";case 80017:return "Kupon 50 SM";default:return "Przedmiot";}}
const MissionExtra* ExtraFor(const char* kind,int id){for(const auto& e:missionExtras)if(std::string(e.kind)==kind && e.id==id)return &e;return nullptr;}
std::vector<std::pair<DWORD,int>> ExtraItems(const MissionExtra& e){return {{25040,e.bless},{71284,e.change},{71285,e.add},{80017,e.coupons}};}
void GrantMissionExtras(LPCHARACTER ch,quest::PC* pc){
 if(!ch || !pc || !ch->CanHandleItem())return;
 for(const auto& m:masters){if(!MasterDone(pc,m))continue;const MissionExtra* e=ExtraFor(m.kind,m.id);if(!e)continue;
  std::string base="custom_mission_loot_v1."+std::string(m.kind)+"_"+std::to_string(m.id)+"_";
  long gold=std::max(0L,e->yang-(long)pc->GetFlag(base+"yang"));
  if(gold && ch->GetGold()<=GOLD_MAX-gold){ch->PointChange(POINT_GOLD,gold);ch->SetQuestFlag(base+"yang",e->yang);pc->Save();ch->Save();}
  for(const auto& item:ExtraItems(*e)){
   if(item.second<=0)continue;std::string flag=base+"item_"+std::to_string(item.first);int count=std::max(0,item.second-pc->GetFlag(flag));
   bool bossCoupon=std::string(m.kind)=="boss" && item.first==80017;
   if(bossCoupon)count=std::min(count,std::max(0,40-pc->GetFlag(BossMigrationFlag("coupons"))));
   if(count && ch->AutoGiveItem(item.first,count)){ch->SetQuestFlag(flag,pc->GetFlag(flag)+count);if(bossCoupon)ch->SetQuestFlag(BossMigrationFlag("coupons"),pc->GetFlag(BossMigrationFlag("coupons"))+count);pc->Save();ch->Save();}
  }
 }
}
void Totals(quest::PC* pc,std::map<int,long>& earned,std::map<int,long>& left){
 for(const auto& h:hunts)for(const auto& b:h.bonus)if(b.point>0 && b.value>0)(Done(pc,h)?earned:left)[b.point]+=b.value;
 MasterTotals(pc,earned,left);
}

// RECONCILE_LOWER_REQUIREMENTS_V11: retain historical counts and claim IDs.
// Only the next unfinished stage can be completed, after its level gate.
void ReconcileProgress(LPCHARACTER ch,quest::PC* pc){
 if(!ch || !pc)return;
 bool changed=false;
 while(const Hunt* h=NextHunt(pc)){
  if(pc->GetFlag(Flag("count_",h->id))<h->kills)break;
  ch->SetQuestFlag(Flag("done_",h->id),1);changed=true;
 }
 for(const char* kind:{"metin","boss"})while(const Master* m=NextMaster(pc,kind)){
  if(ch->GetLevel()<m->level || pc->GetFlag(MasterFlag(*m,"count"))<m->kills)break;
  ch->SetQuestFlag(MasterFlag(*m,"done"),1);changed=true;
 }
 if(changed)pc->Save();
}

void Sync(LPCHARACTER ch,quest::PC* pc){
 MigrateBoss30(ch,pc);
 ReconcileProgress(ch,pc);
 GrantMissionExtras(ch,pc);
 std::map<int,long> wanted,unused;Totals(pc,wanted,unused);
 const Master* metinNext=NextMaster(pc,"metin");int metinActive=pc->GetFlag("custom_masteries_v1.metin_active");if(metinActive && (!metinNext || metinNext->id!=metinActive)){ch->SetQuestFlag("custom_masteries_v1.metin_active",0);pc->Save();}
 const Hunt* next=NextHunt(pc);int active=pc->GetFlag("custom_hunting_v1.active");if(active && (!next || next->id!=active)){ch->SetQuestFlag("custom_hunting_v1.active",0);pc->Save();}
 if(!pc->GetFlag("custom_missions.mission_rewards_20261013_v1")){ch->SetQuestFlag("custom_missions.mission_rewards_20261013_v1",1);pc->Save();}
 std::vector<int> stale;
 for(const CAffect* a:ch->GetAffectContainer())if(a && a->dwType==HUNT_AFFECT && !wanted.count(a->bApplyOn))stale.push_back(a->bApplyOn);
 for(int point:stale)ch->RemoveAffect(ch->FindAffect(HUNT_AFFECT,point));
 for(const auto& b:wanted){CAffect* have=ch->FindAffect(HUNT_AFFECT,b.first);if(!have || have->lApplyValue!=b.second)ch->AddAffect(HUNT_AFFECT,(BYTE)b.first,b.second,0,INFINITE_AFFECT_DURATION,0,true,true);}
}
std::string Hex(const std::string& text){const char* digits="0123456789abcdef";std::string out;for(unsigned char c:text){out+=digits[c>>4];out+=digits[c&15];}return out.empty()?"-":out;}
std::string BonusList(const std::map<int,long>& values){std::ostringstream out;bool first=true;for(const auto& b:values){if(!first)out<<',';first=false;out<<b.first<<':'<<b.second<<':'<<quest_bonus_preview::PointName(b.first);}return first?"-":out.str();}
void Row(LPCHARACTER ch,const char* kind,int id,int level,DWORD race,DWORD item,int count,int required,int status,const std::string& name,const std::string& place,const std::map<int,long>& bonus){
 ch->ChatPacket(CHAT_TYPE_COMMAND,"MP row %s %d %d %u %u %d %d %d %s %s %s",kind,id,level,race,item,count,required,status,Hex(name).c_str(),Hex(place).c_str(),BonusList(bonus).c_str());
}
std::map<int,long> BioBonuses(const Bio& b){
 using namespace mt2009_quest_rewards;
 std::map<int,long> result;QuestRules* rules=Find(b.quest);
 for(const auto& n:quest_bonus_preview::natives)if(std::string(n.quest)==b.quest){int point=n.point;long value=n.value;
  if(rules){const BonusRule* rule=nullptr;auto exact=rules->bonus.find({point,value});if(exact!=rules->bonus.end())rule=&exact->second;else{auto any=rules->bonusAny.find(point);if(any!=rules->bonusAny.end())rule=&any->second;}if(rule){point=rule->point;value=rule->value;}}
  if(point>0 && value>0)result[point]+=value;
 }
 if(rules){auto extra=rules->extras.find("state:__complete");if(extra!=rules->extras.end())for(const auto& e:extra->second)if(e.kind=="bonus" && e.a>0 && e.a<POINT_MAX_NUM && e.b>0)result[(int)e.a]+=(long)e.b;}
 return result;
}
void Send(LPCHARACTER ch,quest::PC* pc){
 Sync(ch,pc);ch->ChatPacket(CHAT_TYPE_COMMAND,"MP begin");bool prior=true;
 long wait=ch->FindAffect(AFFECT_COLLECT_NO_TIME)?0:std::max(0L,(long)pc->GetFlag("collect_quest.wait")-(long)get_global_time());
 ch->ChatPacket(CHAT_TYPE_COMMAND,"MP biotimer %ld",wait);
 for(const auto& b:bios){if(!quest_bonus_preview::ActiveQuest(b.quest))continue;
  bool done=quest_bonus_preview::Finished(pc,b.quest,"__complete");int status=done?3:((ch->GetLevel()>=b.level && prior)?1:0);
  int count=std::max(0,std::min(b.required,pc->GetFlag(std::string(b.quest)+".collect_count")));
  int keyState=quest::CQuestManager::instance().GetQuestStateIndex(b.quest,"key_item");
  if(done || (keyState && pc->GetFlag(std::string(b.quest)+".__status")==keyState))count=b.required;
  Row(ch,"biolog",b.level,b.level,20084,b.item,count,b.required,status,"Biolog - poziom "+std::to_string(b.level),"M1",BioBonuses(b));prior=done;
 }
 int active=pc->GetFlag("custom_hunting_v1.active");
 for(const auto& h:hunts){std::map<int,long> bonus;for(const auto& b:h.bonus)if(b.point)bonus[b.point]+=b.value;
  int status=Done(pc,h)?3:((NextHunt(pc)!=&h)?0:(active==h.id?2:1));
  Row(ch,"hunting",h.id,h.level,h.race,0,Done(pc,h)?h.kills:Progress(pc,h),h.kills,status,h.name,h.location,bonus);
 }
 
 for(const auto& m:masters){std::map<int,long> bonus;for(const auto& b:m.bonus)if(b.point)bonus[b.point]+=b.value;
  int active=pc->GetFlag(std::string("custom_masteries_v1.")+m.kind+"_active");
  int status=MasterDone(pc,m)?3:((NextMaster(pc,m.kind)!=&m || ch->GetLevel()<m.level)?0:(std::string(m.kind)=="boss" || active==m.id?2:1));
  int count=MasterDone(pc,m)?m.kills:std::max(0,std::min(m.kills,pc->GetFlag(MasterFlag(m,"count"))));
  Row(ch,m.kind,m.id,m.level,m.race,0,count,m.kills,status,m.name,m.location,bonus);
  {const MissionExtra* e=ExtraFor(m.kind,m.id);if(e){std::ostringstream items;bool first=true;
   for(const auto& item:ExtraItems(*e)){if(item.second<=0)continue;if(!first)items<<",";first=false;items<<item.first<<":"<<item.second<<":"<<Hex(BossGiftName(item.first));}
   ch->ChatPacket(CHAT_TYPE_COMMAND,"MP extra %s %d %ld %s",m.kind,m.id,e->yang,items.str().c_str());}}

 }
 for(const char* kind:{"metin","boss"}){std::map<int,long> bonus;for(const auto& b:FinalRewards(kind))if(b.point)bonus[b.point]+=b.value;
  Row(ch,kind,99999,1,0,0,AllDone(pc,kind)?1:0,1,AllDone(pc,kind)?3:0,"Nagroda za cala sciezke","Wszystkie etapy",bonus);
 }
 ch->ChatPacket(CHAT_TYPE_COMMAND,"MP end");
}
struct LoginInfo:public event_info_data{DWORD pid,handle;int attempts;};
EVENTFUNC(LoginEvent){
 auto* info=dynamic_cast<LoginInfo*>(event->info);if(!info)return 0;
 LPCHARACTER ch=CHARACTER_MANAGER::instance().FindByPID(info->pid);if(!ch || !ch->GetDesc() || ch->GetDesc()->GetHandle()!=info->handle)return 0;
 if(auto* pc=Ready(ch)){Sync(ch,pc);return 0;}
 return ++info->attempts<60?PASSES_PER_SEC(1):0;
}
}
void OnLogin(LPCHARACTER ch){
 if(!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())return;
 playerbot_collector::WarmRefine(ch);
 if(auto* pc=Ready(ch)){Sync(ch,pc);return;}
 auto* info=AllocEventInfo<LoginInfo>();info->pid=ch->GetPlayerID();info->handle=ch->GetDesc()->GetHandle();info->attempts=0;event_create(LoginEvent,info,PASSES_PER_SEC(1));
}
void AddPreview(LPCHARACTER ch,std::map<int,long>& earned,std::map<int,long>& left){if(auto* pc=Ready(ch)){Sync(ch,pc);Totals(pc,earned,left);}}
int ItemDropBonus(LPCHARACTER ch){if(!ch)return 0;CAffect* a=ch->FindAffect(HUNT_AFFECT,POINT_ITEM_DROP_BONUS);return a?std::max(0L,a->lApplyValue):0;}

void MasterKill(LPCHARACTER ch,LPCHARACTER victim){
 auto* pc=Ready(ch);if(!pc || !victim || victim->IsPC())return;
 for(const auto& m:masters){
  bool stone=std::string(m.kind)=="metin";
  if(NextMaster(pc,m.kind)!=&m || MasterDone(pc,m) || ch->GetLevel()<m.level)continue;
  if(stone){if(!victim->IsStone() || victim->GetLevel()!=m.targetLevel || pc->GetFlag("custom_masteries_v1.metin_active")!=m.id)continue;}
  else if(!victim->IsMonster() || victim->IsStone() || victim->GetRaceNum()!=m.race)continue;
  int n=std::min(m.kills,std::max(0,pc->GetFlag(MasterFlag(m,"count")))+1);
  ch->SetQuestFlag(MasterFlag(m,"count"),n);
  if(n==m.kills){ch->SetQuestFlag(MasterFlag(m,"done"),1);pc->Save();Sync(ch,pc);ch->ChatPacket(CHAT_TYPE_INFO,"%s: %s - ukonczone!",stone?"Metinologia":"Bossologia",m.name);}
  ch->ChatPacket(CHAT_TYPE_COMMAND,"MP masterprogress %s %d %d %d",m.kind,m.id,n,n==m.kills?3:2);
  if(n==m.kills)Send(ch,pc);
  return;
 }
}
void OnKill(LPCHARACTER ch,LPCHARACTER victim){
 MasterKill(ch,victim);
 quest::PC* pc=Ready(ch);if(!pc || !victim || !victim->IsMonster() || victim->IsStone())return;
 const Hunt* h=ByID(pc->GetFlag("custom_hunting_v1.active"));
 if(!h || NextHunt(pc)!=h || Done(pc,*h) || victim->GetRaceNum()!=h->race || !MapMatch(victim->GetMapIndex(),h->map))return;
 int count=std::min(h->kills,Progress(pc,*h)+1);ch->SetQuestFlag(Flag("count_",h->id),count);
 if(count==h->kills){ch->SetQuestFlag(Flag("done_",h->id),1);pc->Save();Sync(ch,pc);ch->ChatPacket(CHAT_TYPE_INFO,"Polowanie ukonczone! %s",h->label);}
 ch->ChatPacket(CHAT_TYPE_COMMAND,"MP progress %d %d %d",h->id,count,count==h->kills?3:2);
 if(count==h->kills)Send(ch,pc);
}
void Command(LPCHARACTER ch,const char* argument){
 quest::PC* pc=Ready(ch);if(!pc){if(ch && ch->GetDesc())ch->ChatPacket(CHAT_TYPE_INFO,"Misje jeszcze sie wczytuja. Sprobuj za chwile.");return;}
 std::istringstream args(argument?argument:"");std::string op;args>>op;
 if(op=="biolog"){
  if(!ch->CanWarp() || !ch->CanHandleItem() || ch->GetDungeon()) {ch->ChatPacket(CHAT_TYPE_INFO,"Nie mozesz teraz teleportowac sie do Biologa.");return;}
  static const long destinations[3][2]={{499400,957000},{90000,182100},{950300,233300}};
  int empire=ch->GetEmpire();if(empire<1 || empire>3)return;
  ch->WarpSet(destinations[empire-1][0],destinations[empire-1][1]);return;
 }
 
 if(op=="metin"){int id=0;if(!(args>>id))return;for(const auto& m:masters)if(std::string(m.kind)=="metin" && m.id==id && NextMaster(pc,"metin")==&m && !MasterDone(pc,m) && ch->GetLevel()>=m.level){ch->SetQuestFlag("custom_masteries_v1.metin_active",id);pc->Save();Send(ch,pc);return;}return;}
 if(op=="start"){int id=0;std::string extra;if(!(args>>id) || (args>>extra))return;const Hunt* h=ByID(id);
  if(!h || NextHunt(pc)!=h || Done(pc,*h)){ch->ChatPacket(CHAT_TYPE_INFO,"Najpierw ukoncz poprzednie Polowanie.");return;}
  ch->SetQuestFlag("custom_hunting_v1.active",id);pc->Save();Send(ch,pc);return;
 }
 if(op=="wersja"){ch->ChatPacket(CHAT_TYPE_INFO,"MISSION_BALANCE_V8 / MISSION_REQUIREMENTS_V13: Metinologia/Bossologia25+10, Polowanie25+25 bez poziomu");return;}
 if(!op.empty() && op!="show")return;
 // Requests per live session; no gameplay changes from refreshing the panel.
 static std::map<std::pair<DWORD,DWORD>,DWORD> times;DWORD now=get_dword_time();auto key=std::make_pair(ch->GetPlayerID(),ch->GetDesc()->GetHandle());
 auto it=times.find(key);if(it!=times.end() && (DWORD)(now-it->second)<800)return;
 for(auto p=times.begin();p!=times.end();)if((DWORD)(now-p->second)>60000)p=times.erase(p);else ++p;
 times[key]=now;Send(ch,pc);
}
}
