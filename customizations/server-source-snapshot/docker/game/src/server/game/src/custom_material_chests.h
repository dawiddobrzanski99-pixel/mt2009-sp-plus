#pragma once
// CUSTOM_MAP_MATERIAL_CHESTS_V1: map scoped replacement, exact independent chances.
#include "char.h"
#include "item.h"
#include "item_manager.h"
#include "mob_manager.h"
#include <vector>
namespace custom_material_chests {
struct Row { DWORD item; int count; int chance; };
struct Box { DWORD item; const Row* rows; unsigned size; };
static const Row rows0[] = {{30003,1,3750},{30004,1,5000},{30010,1,4700},{30011,1,5400},{30017,1,11250},{30018,1,4500},{30023,1,3750},{30027,1,5000},{30028,1,5000},{30031,1,2250},{30034,1,3150},{30035,1,9000},{30037,1,2500},{30038,1,6250},{30053,1,4700},{30069,1,5000},{30070,1,5000},{30071,1,3750},{30072,1,3750},{30073,1,4500},{30346,1,2500},{30347,1,950},{30353,1,2500},{30356,1,1000}};
static const Row rows1[] = {{30005,1,2775},{30011,1,5400},{30021,1,4250},{30030,1,5525},{30031,1,2250},{30032,1,2550},{30033,1,2125},{30034,1,3150},{30041,1,1275},{30052,1,4250},{30073,1,4500},{30074,1,1700},{30075,1,2125},{30092,1,5325},{30357,1,5000},{30358,1,3500}};
static const Row rows2[] = {{30006,1,2925},{30007,1,2925},{30008,1,3750},{30022,1,6075},{30045,1,5400},{30046,1,5400},{30047,1,6750},{30051,1,5625},{30055,1,2700},{30067,1,3500},{30075,1,2125},{30076,1,4500},{30077,1,4500},{30078,1,7425},{30079,1,5625},{30081,1,2500},{30082,1,4000},{30352,1,1800},{30357,1,5000},{30359,1,3125}};
static const Row rows3[] = {{30006,1,2925},{30007,1,2925},{30009,1,9000},{30022,1,6075},{30025,1,6750},{30039,1,7875},{30045,1,5400},{30046,1,5400},{30055,1,2700},{30056,1,4050},{30057,1,6750},{30058,1,5400},{30059,1,9450},{30067,1,3500},{30076,1,4500},{30081,1,2500},{30082,1,4000},{30083,1,4500},{30085,1,6750},{30352,1,1800},{30355,1,7200},{30359,1,3125}};
static const Row rows4[] = {{30350,1,3250},{30351,1,500}};
static const Row rows5[] = {{30009,1,9000},{30014,1,9000},{30039,1,7875},{30048,1,6750},{30049,1,6750},{30050,1,6750},{30079,1,5625},{30080,1,6750},{30083,1,4500},{30085,1,6750},{30088,1,4500},{30089,1,4500},{30090,1,5400},{30348,1,1500},{30355,1,7200}};
static const Row rows6[] = {{30349,1,3250}};
static const Row rows7[] = {{30019,1,3375},{30042,1,3375},{30091,1,6750},{30367,1,2250}};
static const Row rows8[] = {{50721,1,2500},{50722,1,2500},{50723,1,2500},{50724,1,2500},{50725,1,2500},{50726,1,2500},{50727,1,2000},{50728,1,2000},{50729,1,500},{50732,1,1250},{50733,1,500},{50734,1,1000},{50735,1,1250},{50736,4,12500}};
static const Box boxes[] = {{59001,rows0,sizeof(rows0)/sizeof(Row)},{59002,rows1,sizeof(rows1)/sizeof(Row)},{59003,rows2,sizeof(rows2)/sizeof(Row)},{59004,rows3,sizeof(rows3)/sizeof(Row)},{59005,rows4,sizeof(rows4)/sizeof(Row)},{59006,rows5,sizeof(rows5)/sizeof(Row)},{59007,rows6,sizeof(rows6)/sizeof(Row)},{59008,rows7,sizeof(rows7)/sizeof(Row)},{59009,rows8,sizeof(rows8)/sizeof(Row)}};

inline long BaseMap(long map) { return map>=10000 ? map/10000 : map; }
inline int BoxForMap(long map) {
 switch(BaseMap(map)) {
 case 1:case 21:case 41:return 0;
 case 3:case 23:case 43:return 1;
 case 64:return 2;case 63:return 3;case 109:return 4;
 case 61:return 5;case 67:return 6;case 62:return 7;
 default:return -1;
 }
}
// BIOLOGIST_DIRECT_DROP_KEEP_V1: exemptions only; existing tables retain their odds/counts.
inline bool BiologistMaterial(DWORD item) {switch(item){case 30006:case 30077:case 30047:case 30080:case 30015:case 30086:case 30050:case 30090:case 30165:case 30166:case 30167:case 30168:case 30220:case 30221:case 30222:case 30223:case 30224:case 30225:case 30226:case 30227:case 30251:case 30252:case 30253:return true;default:return false;}}
inline bool IsBox(DWORD item) { return item>=59001 && item<=59009; }
inline bool Contains(int index,DWORD item) {for(unsigned i=0;i<boxes[index].size;++i)if(boxes[index].rows[i].item==item)return true;return false;}
inline bool PotionIngredient(DWORD item) {
 switch(item) {case 50721:case 50722:case 50723:case 50724:case 50725:case 50726:case 50727:case 50728:case 50729:case 50730:case 50731:case 50732:case 50733:case 50734:case 50735:case 50736:case 50801:case 50802:case 50803:case 50804:case 50813:case 50814:case 50815:case 50816:case 50817:case 50818:case 50819:case 50820:case 50901:return true;default:return false;}
}

// CUSTOM_DUNGEON_CHEST_COUNTS_V1
inline void Roll(ITEM_MANAGER& manager,std::vector<LPITEM>& loot,int index,int chance,int count=1) {
 if(number(1,1000000)<=chance) { LPITEM item=manager.CreateItem(boxes[index].item,count);if(item)loot.push_back(item); }
}
inline std::vector<std::pair<int,int> > Sources(DWORD race,long map,bool monster,bool stone,int rank) {
 std::vector<std::pair<int,int> > result;map=BaseMap(map);int index=BoxForMap(map);
 // CUSTOM_SHADOW_STONE_TWO_BOXES_V2
 if(race==8009 && stone){result.emplace_back(2,300000);result.emplace_back(3,300000);return result;}
 // CUSTOM_STONE_LEVEL_BOXES_V3
 if(stone && (index>=0 || map==360 || map==65)) {
  // CUSTOM_FOREST_LEVEL_POLICY_V5
  const CMob* levelMob = CMobManager::instance().Get(race);
  if(levelMob && (levelMob->m_table.bLevel==50 || levelMob->m_table.bLevel==55)) {result.emplace_back(5,300000);return result;}
  if(levelMob && levelMob->m_table.bLevel==65) {result.emplace_back(5,300000);result.emplace_back(6,300000);return result;}

  if(race==2903 || race==2904 || race==8010 || race==8011 || race==8015 || race==8016 || race==8045 || race==8110 || race==8111 || race==9677){result.emplace_back(5,300000);result.emplace_back(6,300000);return result;}
  if(race==8012 || race==8017 || race==8035 || race==8037 || race==8039 || race==8040 || race==8046 || race==8057 || race==8112){result.emplace_back(5,300000);result.emplace_back(7,300000);return result;}
 }
 if(index>=0 && (monster || stone)) {
  if(stone)result.emplace_back(index,300000);
  else if(rank>=MOB_RANK_BOSS)result.emplace_back(index,500000);
  else if(monster){result.emplace_back(index,5000);result.emplace_back(8,10000);}
 }
 if(race==9706 && map==363){result.emplace_back(0,750000);result.emplace_back(1,750000);}
 if(race==9682 && map==364){result.emplace_back(2,750000);result.emplace_back(4,750000);result.emplace_back(3,750000);}
 if(race==6091 && map==351){result.emplace_back(5,750000);result.emplace_back(6,750000);result.emplace_back(7,750000);}
 return result;
}
// CUSTOM_TEMPLE_MOB_CHESTS_V4
inline std::vector<std::pair<int,int> > LiveSources(LPCHARACTER mob) {
 auto result=Sources(mob->GetRaceNum(),mob->GetMapIndex(),mob->IsMonster(),mob->IsStone(),mob->GetMobRank());
 if(BaseMap(mob->GetMapIndex())!=65 || !mob->IsMonster() || mob->IsStone() || mob->GetMobRank()>=MOB_RANK_BOSS)return result;
 // CUSTOM_TEMPLE_VALLEY_V5
 result.clear();
 result.emplace_back(2,5000);
 result.emplace_back(8,10000);
 return result;
}
inline bool TempleMaterial(LPCHARACTER mob,DWORD item) {
 if(BaseMap(mob->GetMapIndex())!=65 || !mob->IsMonster() || mob->IsStone() || mob->GetMobRank()>=MOB_RANK_BOSS)return false;
 if(PotionIngredient(item))return true;
 for(int i=0;i<8;++i)if(Contains(i,item))return true;
 return false;
}
inline void Filter(LPCHARACTER victim,LPCHARACTER killer,std::vector<LPITEM>& loot) {
 if(!victim || !killer || !killer->IsPC() || !killer->GetDesc())return;
 const long map=BaseMap(victim->GetMapIndex());const int index=BoxForMap(map);
 // Never delete a shared monster's drops globally: only the requested map scope.
 if((index>=0 || victim->GetRaceNum()==8009 || map==65) && (victim->IsMonster() || victim->IsStone())) {
  for(auto it=loot.begin();it!=loot.end();) {
   LPITEM item=*it;
   if(item && !BiologistMaterial(item->GetVnum()) && (TempleMaterial(victim,item->GetVnum()) || (index>=0 && Contains(index,item->GetVnum())) || (victim->GetRaceNum()==8009 && (Contains(2,item->GetVnum()) || Contains(3,item->GetVnum()))) || PotionIngredient(item->GetVnum()))) {M2_DESTROY_ITEM(item);it=loot.erase(it);}else ++it;
  }
 }
}
inline void Drop(ITEM_MANAGER& manager,LPCHARACTER victim,LPCHARACTER killer,std::vector<LPITEM>& loot) {
 if(!victim || !killer || !killer->IsPC() || !killer->GetDesc())return;
 Filter(victim,killer,loot);
 for(const auto& source:LiveSources(victim))Roll(manager,loot,source.first,source.second,source.first<8 && ((victim->GetRaceNum()==9706 && BaseMap(victim->GetMapIndex())==363) || (victim->GetRaceNum()==9682 && BaseMap(victim->GetMapIndex())==364) || (victim->GetRaceNum()==6091 && BaseMap(victim->GetMapIndex())==351)) ? number(victim->GetRaceNum()==6091 ? 3 : (victim->GetRaceNum()==9682 ? 2 : 1),5) : 1);
}
inline bool Open(LPCHARACTER ch,LPITEM item) {
 if(!ch || !item || !IsBox(item->GetVnum()))return false;
 if(item->IsExchanging() || item->IsEquipped() || item->GetCount()<1)return false;
 if(ch->GetEmptyInventory(3)<0) {ch->ChatPacket(CHAT_TYPE_INFO,"Potrzebujesz wolnego miejsca na nagrody ze skrzynki.");return false;}
 const Box& box=boxes[item->GetVnum()-59001];
 // CUSTOM_MAP_MATERIAL_CHESTS_V2: exactly one guaranteed reward; original odds are weights.
 int total=0;for(unsigned i=0;i<box.size;++i)total+=box.rows[i].chance;
 if(total<=0)return false;
 int ticket=number(1,total);const Row* selected=nullptr;
 for(unsigned i=0;i<box.size;++i) {ticket-=box.rows[i].chance;if(ticket<=0){selected=&box.rows[i];break;}}
 if(!selected)return false;
 if(!ch->AutoGiveItem(selected->item,selected->count))return false;
 item->SetCount(item->GetCount()-1);
 return true;
}
inline bool Preview(LPCHARACTER ch,DWORD vnum) {
 if(!IsBox(vnum))return false;
 const Box& box=boxes[vnum-59001];
 ch->ChatPacket(CHAT_TYPE_COMMAND,"ChestPreviewBegin %u",vnum);
 for(unsigned i=0;i<box.size;++i)ch->ChatPacket(CHAT_TYPE_COMMAND,"ChestPreviewItem %u|%d",box.rows[i].item,box.rows[i].count);
 ch->ChatPacket(CHAT_TYPE_COMMAND,"ChestPreviewEnd %u",vnum);
 return true;
}

struct WikiSource { DWORD race; int box; int chance; };
static const WikiSource wikiSources[] = {{101,0,5000},{101,8,10000},{102,0,5000},{102,8,10000},{103,0,5000},{103,8,10000},{104,0,5000},{104,8,10000},{105,0,5000},{105,8,10000},{106,0,5000},{106,8,10000},{107,0,5000},{107,8,10000},{108,0,5000},{108,8,10000},{109,0,5000},{109,8,10000},{110,0,5000},{110,8,10000},{111,0,5000},{111,8,10000},{112,0,5000},{112,8,10000},{113,0,5000},{113,8,10000},{114,0,5000},{114,8,10000},{115,0,5000},{115,8,10000},{136,0,5000},{136,8,10000},{138,0,5000},{138,8,10000},{142,0,5000},{142,8,10000},{144,0,5000},{144,8,10000},{151,0,5000},{151,8,10000},{152,0,5000},{152,8,10000},{153,0,5000},{153,8,10000},{154,0,5000},{154,8,10000},{155,0,5000},{155,8,10000},{171,0,5000},{171,8,10000},{172,0,5000},{172,8,10000},{173,0,5000},{173,8,10000},{174,0,5000},{174,8,10000},{175,0,5000},{175,8,10000},{176,0,5000},{176,8,10000},{177,0,5000},{177,8,10000},{178,0,5000},{178,8,10000},{179,0,5000},{179,8,10000},{180,0,5000},{180,8,10000},{181,0,5000},{181,8,10000},{182,0,5000},{182,8,10000},{183,0,5000},{183,8,10000},{184,0,5000},{184,8,10000},{185,0,5000},{185,8,10000},{191,0,5000},{191,8,10000},{192,0,5000},{192,8,10000},{193,0,5000},{193,8,10000},{194,0,5000},{194,8,10000},{301,0,5000},{301,1,5000},{301,8,10000},{302,0,5000},{302,1,5000},{302,8,10000},{303,0,5000},{303,8,10000},{304,0,5000},{304,1,5000},{304,8,10000},{331,1,5000},{331,8,10000},{332,1,5000},{332,8,10000},{333,1,5000},{333,8,10000},{334,1,5000},{334,8,10000},{351,0,5000},{351,8,10000},{352,0,5000},{352,8,10000},{354,0,5000},{354,8,10000},{391,0,5000},{391,8,10000},{392,0,5000},{392,8,10000},{393,0,5000},{393,8,10000},{394,0,5000},{394,8,10000},{395,0,5000},{395,8,10000},{396,0,5000},{396,8,10000},{397,0,5000},{397,8,10000},{398,0,5000},{398,8,10000},{401,1,5000},{401,8,10000},{402,1,5000},{402,8,10000},{403,1,5000},{403,8,10000},{404,1,5000},{404,8,10000},{405,1,5000},{405,8,10000},{406,1,5000},{406,8,10000},{431,1,5000},{431,8,10000},{432,1,5000},{432,8,10000},{433,1,5000},{433,8,10000},{434,1,5000},{434,8,10000},{435,1,5000},{435,8,10000},{436,1,5000},{436,8,10000},{451,1,5000},{451,8,10000},{453,1,5000},{453,8,10000},{454,1,5000},{454,8,10000},{455,1,5000},{455,8,10000},{456,1,5000},{456,8,10000},{491,1,5000},{491,8,10000},{492,1,5000},{492,8,10000},{493,1,5000},{493,8,10000},{494,1,5000},{494,8,10000},{501,1,5000},{501,8,10000},{502,1,5000},{502,8,10000},{503,1,5000},{503,8,10000},{504,1,5000},{504,8,10000},{531,1,5000},{531,2,5000},{531,8,10000},{532,1,5000},{532,2,5000},{532,8,10000},{533,1,5000},{533,2,5000},{533,8,10000},{534,1,5000},{534,2,5000},{534,8,10000},{551,1,5000},{551,8,10000},{552,1,5000},{552,8,10000},{553,1,5000},{553,8,10000},{554,1,5000},{554,8,10000},{591,1,500000},{601,2,5000},{601,8,10000},{602,2,5000},{602,8,10000},{603,2,5000},{603,8,10000},{604,2,5000},{604,8,10000},{631,2,5000},{631,3,5000},{631,8,10000},{632,2,5000},{632,3,5000},{632,8,10000},{633,2,5000},{633,3,5000},{633,8,10000},{634,2,5000},{634,3,5000},{634,8,10000},{635,2,5000},{635,3,5000},{635,8,10000},{636,2,5000},{636,3,5000},{636,8,10000},{637,2,5000},{637,8,10000},{651,2,5000},{651,8,10000},{652,2,5000},{652,8,10000},{653,2,5000},{653,8,10000},{654,2,5000},{654,8,10000},{655,2,5000},{655,8,10000},{656,2,5000},{656,8,10000},{657,2,5000},{657,8,10000},{681,2,5000},{681,8,10000},{691,2,500000},{701,2,5000},{701,8,10000},{702,2,5000},{702,8,10000},{703,2,5000},{703,8,10000},{704,2,5000},{704,8,10000},{705,2,5000},{705,8,10000},{706,2,5000},{706,8,10000},{707,2,5000},{707,8,10000},{731,5,5000},{731,8,10000},{732,5,5000},{732,8,10000},{733,5,5000},{733,8,10000},{734,5,5000},{734,8,10000},{735,5,5000},{735,8,10000},{736,5,5000},{736,8,10000},{737,5,5000},{737,8,10000},{751,2,5000},{751,8,10000},{752,2,5000},{752,8,10000},{753,2,5000},{753,8,10000},{754,2,5000},{754,8,10000},{755,2,5000},{755,8,10000},{756,2,5000},{756,8,10000},{757,2,5000},{757,8,10000},{771,5,5000},{771,8,10000},{772,5,5000},{772,8,10000},{773,5,5000},{773,8,10000},{901,3,5000},{901,5,5000},{901,8,10000},{902,3,5000},{902,5,5000},{902,8,10000},{903,3,5000},{903,5,5000},{903,8,10000},{904,3,5000},{904,5,5000},{904,8,10000},{905,3,5000},{905,5,5000},{905,8,10000},{906,3,5000},{906,5,5000},{906,8,10000},{907,3,5000},{907,5,5000},{907,8,10000},{931,3,5000},{931,5,5000},{931,8,10000},{932,3,5000},{932,5,5000},{932,8,10000},{933,3,5000},{933,5,5000},{933,8,10000},{934,3,5000},{934,5,5000},{934,8,10000},{935,3,5000},{935,5,5000},{935,8,10000},{936,5,5000},{936,8,10000},{937,3,5000},{937,5,5000},{937,8,10000},{1101,5,5000},{1101,8,10000},{1102,5,5000},{1102,8,10000},{1103,5,5000},{1103,8,10000},{1104,5,5000},{1104,8,10000},{1105,5,5000},{1105,8,10000},{1106,5,5000},{1106,8,10000},{1107,5,5000},{1107,8,10000},{1171,5,5000},{1171,8,10000},{1181,5,5000},{1181,8,10000},{1182,5,5000},{1182,8,10000},{1901,5,500000},{2001,3,5000},{2001,8,10000},{2002,3,5000},{2002,8,10000},{2003,3,5000},{2003,8,10000},{2004,3,5000},{2004,8,10000},{2005,3,5000},{2005,8,10000},{2051,3,5000},{2051,8,10000},{2052,3,5000},{2052,8,10000},{2053,3,5000},{2053,8,10000},{2054,3,5000},{2054,8,10000},{2102,2,5000},{2102,3,5000},{2102,8,10000},{2103,2,5000},{2103,3,5000},{2103,8,10000},{2104,2,5000},{2104,3,5000},{2104,8,10000},{2105,2,5000},{2105,3,5000},{2105,8,10000},{2106,2,5000},{2106,3,5000},{2106,8,10000},{2107,2,5000},{2107,3,5000},{2107,8,10000},{2108,2,5000},{2108,3,5000},{2108,8,10000},{2131,3,5000},{2131,8,10000},{2158,3,5000},{2158,8,10000},{2181,3,5000},{2181,8,10000},{2182,3,5000},{2182,8,10000},{2191,3,500000},{2201,7,5000},{2201,8,10000},{2202,7,5000},{2202,8,10000},{2203,7,5000},{2203,8,10000},{2204,7,5000},{2204,8,10000},{2205,7,5000},{2205,8,10000},{2281,7,5000},{2281,8,10000},{2282,7,5000},{2282,8,10000},{2301,6,5000},{2301,8,10000},{2302,6,5000},{2302,8,10000},{2303,6,5000},{2303,8,10000},{2304,6,5000},{2304,8,10000},{2305,6,5000},{2305,8,10000},{2381,6,5000},{2381,8,10000},{5121,4,5000},{5121,8,10000},{5122,4,5000},{5122,8,10000},{5123,4,5000},{5123,8,10000},{5124,4,5000},{5124,8,10000},{5125,4,5000},{5125,8,10000},{5126,4,5000},{5126,8,10000},{5151,4,5000},{5151,8,10000},{5152,4,5000},{5152,8,10000},{5153,4,5000},{5153,8,10000},{5154,4,5000},{5154,8,10000},{5155,4,5000},{5155,8,10000},{5156,4,5000},{5156,8,10000},{5163,4,500000},{6091,5,750000},{6091,6,750000},{6091,7,750000},{8001,0,300000},{8002,0,300000},{8003,0,300000},{8004,0,300000},{8005,0,300000},{8005,1,300000},{8006,1,300000},{8007,1,300000},{8008,2,300000},{8008,3,300000},{8009,2,300000},{8009,3,300000},{8014,7,300000},{8024,6,300000},{8025,6,300000},{9682,2,750000},{9682,3,750000},{9682,4,750000},{9706,0,750000},{9706,1,750000},{8012,5,300000},{8012,7,300000},{8017,5,300000},{8017,7,300000},{8035,5,300000},{8035,7,300000},{8037,5,300000},{8037,7,300000},{8039,5,300000},{8039,7,300000},{8040,5,300000},{8040,7,300000},{8046,5,300000},{8046,7,300000},{8057,5,300000},{8057,7,300000},{8112,5,300000},{8112,7,300000},{2903,5,300000},{2904,5,300000},{8010,5,300000},{8011,5,300000},{8013,5,300000},{8013,6,300000},{8015,5,300000},{8016,5,300000},{8018,5,300000},{8018,6,300000},{8045,5,300000},{8110,5,300000},{8111,5,300000},{8113,5,300000},{8113,6,300000},{9677,5,300000}};

}
