#pragma once
#include <map>
namespace mission_panel {
void Command(LPCHARACTER ch,const char* argument);
void OnKill(LPCHARACTER ch,LPCHARACTER victim);
void OnLogin(LPCHARACTER ch);
void AddPreview(LPCHARACTER ch,std::map<int,long>& earned,std::map<int,long>& left);
int ItemDropBonus(LPCHARACTER ch);
}
