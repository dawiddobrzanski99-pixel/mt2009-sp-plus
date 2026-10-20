#ifndef SEBAN_HORSE_LIVE_V2_H
#define SEBAN_HORSE_LIVE_V2_H
#include "seban_horse_rewards.h"
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
#include <unistd.h>
#include <sys/time.h>
#include <sys/stat.h>
namespace SebanHorseLive {
static LPEVENT clockEvent=NULL;
static std::vector<DWORD> pending;
static size_t cursor=0;
static std::string operation,instance,error;
static bool applying=false;
#ifdef SEBAN_HORSE_ROOT
inline const char* Root(){return SEBAN_HORSE_ROOT;}
#else
inline const char* Root(){
 static const std::string root=std::string(std::getenv("M2_RATES_SPOOL")&&*std::getenv("M2_RATES_SPOOL")?std::getenv("M2_RATES_SPOOL"):"/opt/m2spool")+"/systems/horse";
 return root.c_str();
}
#endif
inline void Status(){
 std::ostringstream out;out<<"{\"schema\":\"SEBAN_HORSE_V2\",\"port\":"<<mother_port<<",\"instance\":\""<<instance<<"\",\"operation\":\""<<operation<<"\",\"revision\":\""<<(SebanHorse::Storage().installed?SebanHorse::Storage().revision:"defaults")<<"\",\"state\":\""<<(!error.empty()?"error":applying?"applying":operation.empty()?"ready":"applied")<<"\",\"updated\":"<<time(NULL)<<",\"processed\":"<<cursor<<",\"total\":"<<pending.size()<<",\"error\":\""<<error<<"\"}\n";
 std::string path=std::string(Root())+"/status/"+std::to_string(mother_port)+".json",temp=path+".tmp."+std::to_string(getpid());
 {std::ofstream f(temp.c_str(),std::ios::binary);if(!f)return;f<<out.str();f.flush();if(!f){std::remove(temp.c_str());return;}}
 chmod(temp.c_str(),0660);if(std::rename(temp.c_str(),path.c_str()))std::remove(temp.c_str());
}
struct Collect {void operator()(LPCHARACTER ch){if(ch&&ch->IsPC())pending.push_back(ch->GetPlayerID());}};
inline void Tick(){
 std::string path=std::string(Root())+"/request.txt";std::ifstream f(path.c_str(),std::ios::binary);
 if(f){
  std::string raw;char buf[4096];while(f&&raw.size()<=65536){f.read(buf,sizeof(buf));raw.append(buf,static_cast<size_t>(f.gcount()));}
  std::string nextOperation;SebanHorse::Table table;
  if(!SebanHorse::ParseCommand(raw,nextOperation,table))error="invalid_request";
  else if(nextOperation==operation&&SebanHorse::Storage().revision!=table.revision)error="operation_reused";
  else if(nextOperation!=operation){
   SebanHorse::Commit(table);operation=nextOperation;error.clear();pending.clear();cursor=0;
   CHARACTER_MANAGER::instance().for_each_pc(Collect());applying=true;
  }else error.clear();
 }else if(!operation.empty())error="request_missing";
 if(applying&&error.empty()){
  size_t stop=std::min(pending.size(),cursor+200);
  for(;cursor<stop;++cursor){LPCHARACTER ch=CHARACTER_MANAGER::instance().FindByPID(pending[cursor]);if(ch&&ch->IsPC()){ch->ComputePoints();ch->PointsPacket();}}
  if(cursor==pending.size())applying=false;
 }
 Status();
}
EVENTINFO(ClockInfo) {};
EVENTFUNC(Clock){(void)event;(void)processing_time;Tick();return PASSES_PER_SEC(1);}
inline void Start(){
 if(g_bAuthServer||clockEvent)return;
 struct timeval tv;gettimeofday(&tv,NULL);instance=SebanHorse::Sha256(std::to_string(getpid())+":"+std::to_string(tv.tv_sec)+":"+std::to_string(tv.tv_usec));
 ClockInfo* info=AllocEventInfo<ClockInfo>();clockEvent=event_create(Clock,info,PASSES_PER_SEC(1));
 // This clock is independent from playerbot_world_event and never ends when bots start.
 Tick();
}
}
#endif
