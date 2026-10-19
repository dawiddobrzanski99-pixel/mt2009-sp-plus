#pragma once
#include "char.h"
#include "desc.h"
#include <map>
namespace combat_bonus_diag {
struct State { int remaining=0; long expiry=0; int minimum=0,maximum=0,roll=0;DWORD target=0; };
inline std::map<DWORD,State>& States(){static std::map<DWORD,State> states;return states;}
inline State* Active(LPCHARACTER ch){if(!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())return nullptr;auto it=States().find(ch->GetPlayerID());if(it==States().end())return nullptr;if(it->second.remaining<=0 || it->second.expiry<get_global_time()){States().erase(it);return nullptr;}return &it->second;}
inline void Start(LPCHARACTER ch){if(!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())return;State state;state.remaining=20;state.expiry=get_global_time()+60;States()[ch->GetPlayerID()]=state;ch->ChatPacket(CHAT_TYPE_INFO,"DMGDBG: nastepne20 trafien, max60 sekund. Bij ten sam cel.");}
inline void Roll(LPCHARACTER ch,LPCHARACTER target,int minimum,int maximum,int roll){State* s=Active(ch);if(!s)return;s->minimum=minimum;s->maximum=maximum;s->roll=roll;s->target=target->GetVID();}
inline void Hit(LPCHARACTER ch,LPCHARACTER target,int damage,bool crit,bool penetrate,int type,DWORD skill){State* s=Active(ch);if(!s)return;ch->ChatPacket(CHAT_TYPE_INFO,"DMGDBG cel=%u dmg=%d kryt=%d przeb=%d typ=%d skill=%u los=%d zakres=%d-%d atk=%d def=%d mob=%d boss=%d metin=%d guild=%d kon=%d mount=%u poly=%u zdrowie_konia=%d mapa=%ld",(unsigned)target->GetVID(),damage,(int)crit,(int)penetrate,type,(unsigned)skill,s->target==(DWORD)target->GetVID()?s->roll:-1,s->minimum,s->maximum,ch->GetPoint(POINT_ATT_GRADE),target->GetDefence(),ch->GetPoint(POINT_ATTBONUS_MONSTER),ch->GetPoint(POINT_ATTBONUS_BOSS),ch->GetPoint(POINT_ATTBONUS_STONE),ch->GetGuildCombatBonus(POINT_ATTBONUS_MONSTER),ch->GetHorseLevel(),(unsigned)ch->GetMountVnum(),(unsigned)ch->GetPolymorphVnum(),ch->GetHorseHealthGrade(),ch->GetMapIndex());s->target=0;if(--s->remaining<=0)States().erase(ch->GetPlayerID());}
}
