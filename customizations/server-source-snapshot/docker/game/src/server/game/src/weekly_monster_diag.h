#pragma once
// WEEKLY_MONSTER_DIAG_V1: player's own live values, throttled, read-only.
#include "item.h"
#include "PetSystem.h"
#include "custom_horse_polymorph_rewards.h"
#include <map>
void WeeklyRankDebugMonster(LPCHARACTER ch);
long NewPetDebugMonster(LPCHARACTER ch);
namespace weekly_monster_diag {
inline void Send(LPCHARACTER ch) {
 if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())return;
 static std::map<unsigned,DWORD> requests;const DWORD now=get_dword_time();
 auto last=requests.find(ch->GetPlayerID());if(last!=requests.end() && (DWORD)(now-last->second)<3000)return;
 for(auto it=requests.begin();it!=requests.end();)if((DWORD)(now-it->second)>60000)it=requests.erase(it);else ++it;
 requests[ch->GetPlayerID()]=now;
 auto print=[&](const char* text){ch->ChatPacket(CHAT_TYPE_INFO,"[WRDBG] %s",text);sys_log(0,"WRDBG pid=%u name=%s %s",ch->GetPlayerID(),ch->GetName(),text);};
 char text[240];long poly=0;
 if (ch->IsPolymorphed() && !ch->IsPolyMaintainStat() && ch->GetPolymorphVnum()!=30000)poly=CustomPolyForLevel(ch->GetSkillLevel(SKILL_POLYMORPH)).monster;
 const long pet=NewPetDebugMonster(ch);const long guild=ch->GetGuildCombatBonus(POINT_ATTBONUS_MONSTER);
 snprintf(text,sizeof(text),"BEGIN monster=%d limited=%d real=%d guild=%ld horse_level=%d horse_bonus=%d poly=%ld newpet=%ld",ch->GetPoint(POINT_ATTBONUS_MONSTER),ch->GetLimitPoint(POINT_ATTBONUS_MONSTER),ch->GetRealPoint(POINT_ATTBONUS_MONSTER),guild,ch->GetHorseLevel(),CustomHorseMonsterBoss(ch->GetHorseLevel()),poly,pet);print(text);
 unsigned worn=0;
 for (int slot=0;slot<WEAR_MAX_NUM;++slot)if (LPITEM item=ch->GetWear(slot)) {
  ++worn;long proto=0,attrs=0;
  for(int i=0;i<ITEM_APPLY_MAX_NUM;++i)if(item->GetProto()->aApplies[i].bType==POINT_ATTBONUS_MONSTER)proto+=item->GetProto()->aApplies[i].lValue;
  for(int i=0;i<ITEM_ATTRIBUTE_MAX_NUM;++i)if(item->GetAttributeType(i)==POINT_ATTBONUS_MONSTER)attrs+=item->GetAttributeValue(i);
  snprintf(text,sizeof(text),"wear slot=%d vnum=%u proto53=%ld attrs53=%ld sig=%u",slot,item->GetVnum(),proto,attrs,item->GetSIGVnum());print(text);
 }
 long legacyPets=0;
#ifdef __PET_SYSTEM__
 if(ch->GetPetSystem())legacyPets=(long)ch->GetPetSystem()->CountSummoned();
#endif
 snprintf(text,sizeof(text),"worn_count=%u alchemy_active=%d mount=%u oldpets=%ld",worn,ch->DragonSoul_IsDeckActivated()?1:0,ch->GetMountVnum(),legacyPets);print(text);
 WeeklyRankDebugMonster(ch);print("END");
}
}
