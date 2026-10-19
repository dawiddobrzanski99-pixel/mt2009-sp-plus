#pragma once
// CHEST50122_ALL_METINS_BOSSES_V1: one independent roll, no table duplicates.
namespace chest50122 {
inline int Chance(bool stone,bool monster,int level,int rank) {
 if(stone)return level>=50 ? 200 : 0;
 return monster && rank>=MOB_RANK_BOSS ? 500 : 0;
}
inline int Chance(LPCHARACTER victim) {
 return victim ? Chance(victim->IsStone(),victim->IsMonster(),victim->GetLevel(),victim->GetMobRank()) : 0;
}
inline int Chance(const TMobTable& table) {
 return Chance(table.bType==CHAR_TYPE_STONE,table.bType==CHAR_TYPE_MONSTER,table.bLevel,table.bRank);
}
inline void Drop(ITEM_MANAGER& manager,LPCHARACTER victim,LPCHARACTER killer,std::vector<LPITEM>& loot) {
 const int chance=Chance(victim);
 if(!chance || !killer || !killer->IsPC())return;
 // Replace only this item's old rolls; all other loot stays intact.
 for(auto it=loot.begin();it!=loot.end();) {
  if(*it && (*it)->GetVnum()==50122){M2_DESTROY_ITEM(*it);it=loot.erase(it);}else ++it;
 }
 if(number(1,10000)<=chance){LPITEM item=manager.CreateItem(50122,1);if(item)loot.push_back(item);}
}
inline void Preview(ITEM_MANAGER& manager,LPCHARACTER victim,std::vector<std::pair<DWORD,int> >& lines) {
 if(!Chance(victim))return;
 lines.erase(std::remove_if(lines.begin(),lines.end(),[](const std::pair<DWORD,int>& r){return r.first==50122;}),lines.end());
 if(manager.GetTable(50122))lines.insert(lines.begin(),std::make_pair((DWORD)50122,1));
}
inline void Wiki(ITEM_MANAGER& manager,const TMobTable& table,std::vector<TDropWikiRow>& rows) {
 const int chance=Chance(table);if(!chance)return;
 rows.erase(std::remove_if(rows.begin(),rows.end(),[](const TDropWikiRow& r){return r.dwVnum==50122;}),rows.end());
 if(manager.GetTable(50122)){TDropWikiRow row;row.dwVnum=50122;row.iCountMin=1;row.iCountMax=1;row.dChance=chance/10000.0;rows.push_back(row);}
}
}
