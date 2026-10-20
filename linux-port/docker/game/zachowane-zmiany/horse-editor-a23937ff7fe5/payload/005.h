#ifndef SEBAN_HORSE_REWARDS_V2_H
#define SEBAN_HORSE_REWARDS_V2_H
#include "seban_sha256.h"
#include <sstream>
#include <string>
#include <cstring>
namespace SebanHorse {
enum Key { ATTACK,HP,MONSTER,BOSS,STONE,MOVE,CLASSES,HUMAN,ELEMENTS,RESIST_MONSTER,RESIST_BOSS,DEFENSE,SPEED,STRENGTH,VITALITY,DEXTERITY,INTELLIGENCE,CRIT,PENETRATE,DROP,EXP,YANG,COUNT };
static const int Limits[COUNT]={1000,50000,100,100,100,100,90,100,100,900,900,1000,100,100,100,100,100,100,100,100,100,100};
struct Table {
 bool installed,master,enabled;int cells[31][COUNT];std::string revision;
 Table():installed(false),master(true),enabled(true){std::memset(cells,0,sizeof(cells));}
};
inline bool Hex(const std::string& s,size_t n){return s.size()==n && s.find_first_not_of("0123456789abcdef")==std::string::npos;}
inline bool Parse(std::istream& in,Table& out){
 std::string line,magic,digest,extra;if(!std::getline(in,line))return false;
 std::istringstream header(line);if(!(header>>magic>>digest)||header>>extra||magic!="SEBAN_HORSE_V2"||!Hex(digest,64))return false;
 std::string body((std::istreambuf_iterator<char>(in)),std::istreambuf_iterator<char>());
 if(body.size()>32768||Sha256(body)!=digest)return false;
 std::istringstream input(body);Table candidate;int master,enabled;
 if(!std::getline(input,line))return false;
 std::istringstream switches(line);if(!(switches>>master>>enabled)||switches>>extra||(master!=0&&master!=1)||(enabled!=0&&enabled!=1))return false;
 for(int level=1;level<=30;++level){
  if(!std::getline(input,line))return false;
  std::istringstream row(line);int actual;if(!(row>>actual)||actual!=level)return false;
  for(int k=0;k<COUNT;++k)if(!(row>>candidate.cells[level][k])||candidate.cells[level][k]<0||candidate.cells[level][k]>Limits[k])return false;
  if(row>>extra)return false;
 }
 while(std::getline(input,line))if(line.find_first_not_of(" \t\r")!=std::string::npos)return false;
 candidate.installed=true;candidate.master=master;candidate.enabled=enabled;candidate.revision=digest;out=candidate;return true;
}
inline bool ParseCommand(const std::string& raw,std::string& operation,Table& out){
 if(raw.size()>65536)return false;
 std::istringstream input(raw);std::string line,magic,extra;
 if(!std::getline(input,line))return false;
 std::istringstream first(line);if(!(first>>magic>>operation)||first>>extra||magic!="SEBAN_HORSE_REQUEST_V2"||!Hex(operation,32))return false;
 return Parse(input,out);
}
inline int Default(int level,Key key){
 int n=level<0?0:(level>30?30:level),basic=n<10?n:10,growth=n<=10?0:(n-10)*5/20;
 switch(key){case ATTACK:return basic*2;case HP:return basic*100;case MONSTER:return growth;
 case MOVE:return n<=10?0:((n<21?n:21)-10)*20/11;case CLASSES:return n<=11?0:((n<20?n:20)-11)*15/9;
 case HUMAN:return n>=21?10:0;case ELEMENTS:return n>=23?5:(n==22?2:0);case RESIST_MONSTER:case RESIST_BOSS:return growth*10;default:return 0;}
}
inline Table& Storage(){static Table table;return table;}
inline void Commit(const Table& table){Storage()=table;}
inline int Value(int level,Key key){const Table& t=Storage();if(!t.installed)return Default(level,key);if(!t.master||!t.enabled)return 0;return t.cells[level<0?0:(level>30?30:level)][key];}
}
#endif
