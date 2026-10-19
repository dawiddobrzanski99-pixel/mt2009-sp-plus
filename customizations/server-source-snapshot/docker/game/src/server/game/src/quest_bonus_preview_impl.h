#include "mission_panel.h"
// Compiled through playerbot_quest_rewards.cpp so existing panel rules are authoritative.
#include "quest_bonus_preview.h"
#include "desc.h"
#include <set>
namespace quest_bonus_preview {
struct Native { const char* quest; const char* terminal; int point; long value; };
static const Native natives[] = {
 {"collect_quest_lv30","__complete",POINT_MOV_SPEED,10},
 {"collect_quest_lv40","__complete",POINT_ATT_SPEED,5},
 {"collect_quest_lv50","__complete",POINT_DEF_GRADE_BONUS,60},
 {"collect_quest_lv60","__complete",POINT_ATT_GRADE_BONUS,50},
 {"collect_quest_lv70","__complete",POINT_MOV_SPEED,11},
 {"collect_quest_lv70","__complete",POINT_DEF_BONUS,10},
 {"collect_quest_lv80","__complete",POINT_ATT_SPEED,6},
 {"collect_quest_lv80","__complete",POINT_ATT_BONUS,10},
 {"collect_quest_lv85","__complete",POINT_RESIST_HUMAN,10},
 {"collect_quest_lv90","__complete",POINT_ATTBONUS_HUMAN,8}
};
static const char* PointName(int point) {
 switch(point) {
 case POINT_NONE:return "POINT_NONE";
 case POINT_LEVEL:return "POINT_LEVEL";
 case POINT_VOICE:return "POINT_VOICE";
 case POINT_EXP:return "POINT_EXP";
 case POINT_NEXT_EXP:return "POINT_NEXT_EXP";
 case POINT_HP:return "POINT_HP";
 case POINT_MAX_HP:return "POINT_MAX_HP";
 case POINT_SP:return "POINT_SP";
 case POINT_MAX_SP:return "POINT_MAX_SP";
 case POINT_STAMINA:return "POINT_STAMINA";
 case POINT_MAX_STAMINA:return "POINT_MAX_STAMINA";
 case POINT_GOLD:return "POINT_GOLD";
 case POINT_ST:return "POINT_ST";
 case POINT_HT:return "POINT_HT";
 case POINT_DX:return "POINT_DX";
 case POINT_IQ:return "POINT_IQ";
 case POINT_DEF_GRADE:return "POINT_DEF_GRADE";
 case POINT_ATT_SPEED:return "POINT_ATT_SPEED";
 case POINT_ATT_GRADE:return "POINT_ATT_GRADE";
 case POINT_MOV_SPEED:return "POINT_MOV_SPEED";
 case POINT_CLIENT_DEF_GRADE:return "POINT_CLIENT_DEF_GRADE";
 case POINT_CASTING_SPEED:return "POINT_CASTING_SPEED";
 case POINT_MAGIC_ATT_GRADE:return "POINT_MAGIC_ATT_GRADE";
 case POINT_MAGIC_DEF_GRADE:return "POINT_MAGIC_DEF_GRADE";
 case POINT_EMPIRE_POINT:return "POINT_EMPIRE_POINT";
 case POINT_LEVEL_STEP:return "POINT_LEVEL_STEP";
 case POINT_STAT:return "POINT_STAT";
 case POINT_SUB_SKILL:return "POINT_SUB_SKILL";
 case POINT_SKILL:return "POINT_SKILL";
 case POINT_WEAPON_MIN:return "POINT_WEAPON_MIN";
 case POINT_WEAPON_MAX:return "POINT_WEAPON_MAX";
 case POINT_PLAYTIME:return "POINT_PLAYTIME";
 case POINT_HP_REGEN:return "POINT_HP_REGEN";
 case POINT_SP_REGEN:return "POINT_SP_REGEN";
 case POINT_BOW_DISTANCE:return "POINT_BOW_DISTANCE";
 case POINT_HP_RECOVERY:return "POINT_HP_RECOVERY";
 case POINT_SP_RECOVERY:return "POINT_SP_RECOVERY";
 case POINT_POISON_PCT:return "POINT_POISON_PCT";
 case POINT_STUN_PCT:return "POINT_STUN_PCT";
 case POINT_SLOW_PCT:return "POINT_SLOW_PCT";
 case POINT_CRITICAL_PCT:return "POINT_CRITICAL_PCT";
 case POINT_PENETRATE_PCT:return "POINT_PENETRATE_PCT";
 case POINT_CURSE_PCT:return "POINT_CURSE_PCT";
 case POINT_ATTBONUS_HUMAN:return "POINT_ATTBONUS_HUMAN";
 case POINT_ATTBONUS_ANIMAL:return "POINT_ATTBONUS_ANIMAL";
 case POINT_ATTBONUS_ORC:return "POINT_ATTBONUS_ORC";
 case POINT_ATTBONUS_MILGYO:return "POINT_ATTBONUS_MILGYO";
 case POINT_ATTBONUS_UNDEAD:return "POINT_ATTBONUS_UNDEAD";
 case POINT_ATTBONUS_DEVIL:return "POINT_ATTBONUS_DEVIL";
 case POINT_ATTBONUS_INSECT:return "POINT_ATTBONUS_INSECT";
 case POINT_ATTBONUS_FIRE:return "POINT_ATTBONUS_FIRE";
 case POINT_ATTBONUS_ICE:return "POINT_ATTBONUS_ICE";
 case POINT_ATTBONUS_DESERT:return "POINT_ATTBONUS_DESERT";
 case POINT_ATTBONUS_MONSTER:return "POINT_ATTBONUS_MONSTER";
 case POINT_ATTBONUS_WARRIOR:return "POINT_ATTBONUS_WARRIOR";
 case POINT_ATTBONUS_ASSASSIN:return "POINT_ATTBONUS_ASSASSIN";
 case POINT_ATTBONUS_SURA:return "POINT_ATTBONUS_SURA";
 case POINT_ATTBONUS_SHAMAN:return "POINT_ATTBONUS_SHAMAN";
 case POINT_ATTBONUS_TREE:return "POINT_ATTBONUS_TREE";
 case POINT_RESIST_WARRIOR:return "POINT_RESIST_WARRIOR";
 case POINT_RESIST_ASSASSIN:return "POINT_RESIST_ASSASSIN";
 case POINT_RESIST_SURA:return "POINT_RESIST_SURA";
 case POINT_RESIST_SHAMAN:return "POINT_RESIST_SHAMAN";
 case POINT_STEAL_HP:return "POINT_STEAL_HP";
 case POINT_STEAL_SP:return "POINT_STEAL_SP";
 case POINT_MANA_BURN_PCT:return "POINT_MANA_BURN_PCT";
 case POINT_DAMAGE_SP_RECOVER:return "POINT_DAMAGE_SP_RECOVER";
 case POINT_BLOCK:return "POINT_BLOCK";
 case POINT_DODGE:return "POINT_DODGE";
 case POINT_RESIST_SWORD:return "POINT_RESIST_SWORD";
 case POINT_RESIST_TWOHAND:return "POINT_RESIST_TWOHAND";
 case POINT_RESIST_DAGGER:return "POINT_RESIST_DAGGER";
 case POINT_RESIST_BELL:return "POINT_RESIST_BELL";
 case POINT_RESIST_FAN:return "POINT_RESIST_FAN";
 case POINT_RESIST_BOW:return "POINT_RESIST_BOW";
 case POINT_RESIST_FIRE:return "POINT_RESIST_FIRE";
 case POINT_RESIST_ELEC:return "POINT_RESIST_ELEC";
 case POINT_RESIST_MAGIC:return "POINT_RESIST_MAGIC";
 case POINT_RESIST_WIND:return "POINT_RESIST_WIND";
 case POINT_REFLECT_MELEE:return "POINT_REFLECT_MELEE";
 case POINT_REFLECT_ARROW:return "POINT_REFLECT_ARROW";
 case POINT_POISON_REDUCE:return "POINT_POISON_REDUCE";
 case POINT_KILL_SP_RECOVER:return "POINT_KILL_SP_RECOVER";
 case POINT_EXP_DOUBLE_BONUS:return "POINT_EXP_DOUBLE_BONUS";
 case POINT_GOLD_DOUBLE_BONUS:return "POINT_GOLD_DOUBLE_BONUS";
 case POINT_ITEM_DROP_BONUS:return "POINT_ITEM_DROP_BONUS";
 case POINT_POTION_BONUS:return "POINT_POTION_BONUS";
 case POINT_KILL_HP_RECOVERY:return "POINT_KILL_HP_RECOVERY";
 case POINT_IMMUNE_STUN:return "POINT_IMMUNE_STUN";
 case POINT_IMMUNE_SLOW:return "POINT_IMMUNE_SLOW";
 case POINT_IMMUNE_FALL:return "POINT_IMMUNE_FALL";
 case POINT_PARTY_ATTACKER_BONUS:return "POINT_PARTY_ATTACKER_BONUS";
 case POINT_PARTY_TANKER_BONUS:return "POINT_PARTY_TANKER_BONUS";
 case POINT_ATT_BONUS:return "POINT_ATT_BONUS";
 case POINT_DEF_BONUS:return "POINT_DEF_BONUS";
 case POINT_ATT_GRADE_BONUS:return "POINT_ATT_GRADE_BONUS";
 case POINT_DEF_GRADE_BONUS:return "POINT_DEF_GRADE_BONUS";
 case POINT_MAGIC_ATT_GRADE_BONUS:return "POINT_MAGIC_ATT_GRADE_BONUS";
 case POINT_MAGIC_DEF_GRADE_BONUS:return "POINT_MAGIC_DEF_GRADE_BONUS";
 case POINT_RESIST_NORMAL_DAMAGE:return "POINT_RESIST_NORMAL_DAMAGE";
 case POINT_HIT_HP_RECOVERY:return "POINT_HIT_HP_RECOVERY";
 case POINT_HIT_SP_RECOVERY:return "POINT_HIT_SP_RECOVERY";
 case POINT_MANASHIELD:return "POINT_MANASHIELD";
 case POINT_PARTY_BUFFER_BONUS:return "POINT_PARTY_BUFFER_BONUS";
 case POINT_PARTY_SKILL_MASTER_BONUS:return "POINT_PARTY_SKILL_MASTER_BONUS";
 case POINT_HP_RECOVER_CONTINUE:return "POINT_HP_RECOVER_CONTINUE";
 case POINT_SP_RECOVER_CONTINUE:return "POINT_SP_RECOVER_CONTINUE";
 case POINT_STEAL_GOLD:return "POINT_STEAL_GOLD";
 case POINT_POLYMORPH:return "POINT_POLYMORPH";
 case POINT_MOUNT:return "POINT_MOUNT";
 case POINT_PARTY_HASTE_BONUS:return "POINT_PARTY_HASTE_BONUS";
 case POINT_PARTY_DEFENDER_BONUS:return "POINT_PARTY_DEFENDER_BONUS";
 case POINT_STAT_RESET_COUNT:return "POINT_STAT_RESET_COUNT";
 case POINT_HORSE_SKILL:return "POINT_HORSE_SKILL";
 case POINT_MALL_ATTBONUS:return "POINT_MALL_ATTBONUS";
 case POINT_MALL_DEFBONUS:return "POINT_MALL_DEFBONUS";
 case POINT_MALL_EXPBONUS:return "POINT_MALL_EXPBONUS";
 case POINT_MALL_ITEMBONUS:return "POINT_MALL_ITEMBONUS";
 case POINT_MALL_GOLDBONUS:return "POINT_MALL_GOLDBONUS";
 case POINT_MAX_HP_PCT:return "POINT_MAX_HP_PCT";
 case POINT_MAX_SP_PCT:return "POINT_MAX_SP_PCT";
 case POINT_SKILL_DAMAGE_BONUS:return "POINT_SKILL_DAMAGE_BONUS";
 case POINT_NORMAL_HIT_DAMAGE_BONUS:return "POINT_NORMAL_HIT_DAMAGE_BONUS";
 case POINT_SKILL_DEFEND_BONUS:return "POINT_SKILL_DEFEND_BONUS";
 case POINT_NORMAL_HIT_DEFEND_BONUS:return "POINT_NORMAL_HIT_DEFEND_BONUS";
 case POINT_PC_BANG_EXP_BONUS:return "POINT_PC_BANG_EXP_BONUS";
 case POINT_PC_BANG_DROP_BONUS:return "POINT_PC_BANG_DROP_BONUS";
 case POINT_RAMADAN_CANDY_BONUS_EXP:return "POINT_RAMADAN_CANDY_BONUS_EXP";
 case POINT_ENERGY:return "POINT_ENERGY";
 case POINT_ENERGY_END_TIME:return "POINT_ENERGY_END_TIME";
 case POINT_COSTUME_ATTR_BONUS:return "POINT_COSTUME_ATTR_BONUS";
 case POINT_MAGIC_ATT_BONUS_PER:return "POINT_MAGIC_ATT_BONUS_PER";
 case POINT_MELEE_MAGIC_ATT_BONUS_PER:return "POINT_MELEE_MAGIC_ATT_BONUS_PER";
 case POINT_RESIST_ICE:return "POINT_RESIST_ICE";
 case POINT_RESIST_EARTH:return "POINT_RESIST_EARTH";
 case POINT_RESIST_DARK:return "POINT_RESIST_DARK";
 case POINT_RESIST_CRITICAL:return "POINT_RESIST_CRITICAL";
 case POINT_RESIST_PENETRATE:return "POINT_RESIST_PENETRATE";
 case POINT_TERROR:return "POINT_TERROR";
 case POINT_ST_REGEN:return "POINT_ST_REGEN";
 case POINT_DAGGER_ATT_GRADE_MONSTER:return "POINT_DAGGER_ATT_GRADE_MONSTER";
 case POINT_ATT_GRADE_MONSTER:return "POINT_ATT_GRADE_MONSTER";
 case POINT_RESIST_MONSTER_1000PCT:return "POINT_RESIST_MONSTER_1000PCT";
 case POINT_ABSORB_DAMAGE:return "POINT_ABSORB_DAMAGE";
 case POINT_ABSORB_DAMAGE_MONSTER:return "POINT_ABSORB_DAMAGE_MONSTER";
 case POINT_IMMUNE_STUN_BREAK:return "POINT_IMMUNE_STUN_BREAK";
 case POINT_BREAK_TEMPLE_CURSE:return "POINT_BREAK_TEMPLE_CURSE";
 case POINT_SKILL_DURATION:return "POINT_SKILL_DURATION";
 case POINT_ATTBONUS_ORC_VALLEY:return "POINT_ATTBONUS_ORC_VALLEY";
 case POINT_ATTBONUS_STONE:return "POINT_ATTBONUS_STONE";
 case POINT_ATTBONUS_BOSS:return "POINT_ATTBONUS_BOSS";
 case POINT_MAGIC_ATT_MONSTER:return "POINT_MAGIC_ATT_MONSTER";
 case POINT_BREAK_RESIST_SWORD:return "POINT_BREAK_RESIST_SWORD";
 case POINT_BREAK_RESIST_TWOHAND:return "POINT_BREAK_RESIST_TWOHAND";
 case POINT_BREAK_RESIST_DAGGER:return "POINT_BREAK_RESIST_DAGGER";
 case POINT_BREAK_RESIST_BELL:return "POINT_BREAK_RESIST_BELL";
 case POINT_BREAK_RESIST_FAN:return "POINT_BREAK_RESIST_FAN";
 case POINT_BREAK_RESIST_BOW:return "POINT_BREAK_RESIST_BOW";
 case POINT_COLLECT_CHANCE:return "POINT_COLLECT_CHANCE";
 case POINT_LEARN_CHANCE:return "POINT_LEARN_CHANCE";
 case POINT_RESIST_HUMAN:return "POINT_RESIST_HUMAN";
 case POINT_MAGIC_ATT:return "POINT_MAGIC_ATT";
 case POINT_FIRE_PCT:return "POINT_FIRE_PCT";
 case POINT_CONVERT_DAMAGE_TO_SP:return "POINT_CONVERT_DAMAGE_TO_SP";
 case POINT_DROP_RARE:return "POINT_DROP_RARE";
 case POINT_MAGIC_ATT_GRADE_BONUS_MONSTER:return "POINT_MAGIC_ATT_GRADE_BONUS_MONSTER";
 case POINT_ROOT_PCT:return "POINT_ROOT_PCT";
 case POINT_ATT_SPECIAL:return "POINT_ATT_SPECIAL";
 case POINT_DEATH_PENALTY:return "POINT_DEATH_PENALTY";
 case POINT_MIN_WEP:return "POINT_MIN_WEP";
 case POINT_MAX_WEP:return "POINT_MAX_WEP";
 case POINT_MIN_MAGIC_WEP:return "POINT_MIN_MAGIC_WEP";
 case POINT_MAX_MAGIC_WEP:return "POINT_MAX_MAGIC_WEP";
 case POINT_MIN_ATK:return "POINT_MIN_ATK";
 case POINT_MAX_ATK:return "POINT_MAX_ATK";
 case POINT_HIT_RATE:return "POINT_HIT_RATE";
 case POINT_EVADE_RATE:return "POINT_EVADE_RATE";
 case POINT_ENCHANT_ELECT:return "POINT_ENCHANT_ELECT";
 case POINT_ENCHANT_FIRE:return "POINT_ENCHANT_FIRE";
 case POINT_ENCHANT_ICE:return "POINT_ENCHANT_ICE";
 case POINT_ENCHANT_WIND:return "POINT_ENCHANT_WIND";
 case POINT_ENCHANT_EARTH:return "POINT_ENCHANT_EARTH";
 case POINT_ENCHANT_DARK:return "POINT_ENCHANT_DARK";
 default:return "UNKNOWN";
 }
}
static bool Finished(quest::PC* pc,const char* q,const std::string& state) {
 auto& manager=quest::CQuestManager::instance();
 if(!manager.GetQuestIndexByName(q))return false;
 const int terminal=manager.GetQuestStateIndex(q,state);
 return terminal!=0 && pc->GetFlag(std::string(q)+".__status")==terminal;
}
static bool ActiveQuest(const char* q) {return quest::CQuestManager::instance().GetQuestIndexByName(q)!=0;}
static void Remaining(LPCHARACTER ch,quest::PC* pc,std::map<int,long>& left) {
 using namespace mt2009_quest_rewards;
 Load();
 for(const auto& native:natives) {
  if(!ActiveQuest(native.quest) || Finished(pc,native.quest,native.terminal))continue;
  int point=native.point;long value=native.value;
  QuestRules* rule=Find(native.quest);
  if(rule){const BonusRule* bonus=nullptr;auto exact=rule->bonus.find(std::make_pair(point,value));
   if(exact!=rule->bonus.end())bonus=&exact->second;
   else {auto any=rule->bonusAny.find(point);if(any!=rule->bonusAny.end())bonus=&any->second;}
   if(bonus){point=bonus->point;value=bonus->value;}}
  if(point>0 && value>0)left[point]+=value;
 }
 // Finite state rewards, including all current bonus extras in the panel.
 for(const auto& row:g_rules) {
  if(!ActiveQuest(row.first.c_str()))continue;
  for(const auto& anchor:row.second.extras) {
   bool canEarn=false;
   if(anchor.first.compare(0,6,"state:")==0) {
    const std::string state=anchor.first.substr(6);
    if(state=="__complete" || state=="__COMPLETE__" || state=="complete" || state=="COMPLETE" || state=="THEEND" || state=="__THEEND__")canEarn=!Finished(pc,row.first.c_str(),state);
   } else if(row.first=="horse_upgrade" && anchor.first=="item:50052")canEarn=ch->GetHorseLevel()<11;
   if(canEarn)for(const auto& extra:anchor.second)if(extra.kind=="bonus" && extra.a>0 && extra.a<POINT_MAX_NUM && extra.b>0)left[(int)extra.a]+=(long)extra.b;
  }
 }
 // The old training quest tops out at five collect points per kind. Levels themselves are not quest rewards.
 if(ActiveQuest("konie"))for(const auto& entry: {std::make_pair(POINT_ATTBONUS_MONSTER,"nm")}) {
  int have=pc->GetFlag(std::string("konie.")+entry.second);have=std::max(0,std::min(5,have));
  long missing=5-have;
  QuestRules* rule=Find("konie");
  if(rule) {auto any=rule->bonusAny.find((int)entry.first);
   if(any!=rule->bonusAny.end()) {if(any->second.point<=0)missing=0;else {left[any->second.point]+=missing*std::max(0L,any->second.value);continue;}}}
  if(missing)left[entry.first]+=missing;
 }
}
void Send(LPCHARACTER ch) {
 if(!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())return;
 quest::PC* pc=quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID());
 if(!pc || !pc->IsLoaded() || !ch->IsLoadedAffect())return;
 static std::map<unsigned,DWORD> requests;const DWORD now=get_dword_time();
 auto last=requests.find(ch->GetPlayerID());if(last!=requests.end() && (DWORD)(now-last->second)<2000)return;
 for(auto it=requests.begin();it!=requests.end();)if((DWORD)(now-it->second)>60000)it=requests.erase(it);else ++it;
 requests[ch->GetPlayerID()]=now;
 std::map<int,long> earned,left;
 // Rank, weekly ranking, guild, equipment and temporary buffs deliberately do not enter this total.
 for(const CAffect* affect:ch->GetAffectContainer())if(affect && affect->dwType==AFFECT_COLLECT && affect->lDuration>0 && affect->lApplyValue)earned[affect->bApplyOn]+=affect->lApplyValue;
 Remaining(ch,pc,left);
 mission_panel::AddPreview(ch,earned,left);
 std::set<int> points;
 for(const auto& row:earned)if(row.second)points.insert(row.first);
 for(const auto& row:left)if(row.second)points.insert(row.first);
 ch->ChatPacket(CHAT_TYPE_COMMAND,"QPBeg");
 for(int point:points)ch->ChatPacket(CHAT_TYPE_COMMAND,"QPRow %d %ld %ld %s",point,earned[point],left[point],PointName(point));
 ch->ChatPacket(CHAT_TYPE_COMMAND,"QPEnd");
}
}

// QUEST_PERMANENT_STYLE_V1: identity comes from server quest indices, never translated titles.
namespace quest_bonus_preview {
void SendStyles(LPCHARACTER ch) {
 if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot()) return;
 static std::map<unsigned,DWORD> times;const DWORD now=get_dword_time();
 auto last=times.find(ch->GetPlayerID());if(last!=times.end() && (DWORD)(now-last->second)<3000)return;
 for(auto it=times.begin();it!=times.end();)if((DWORD)(now-it->second)>60000)it=times.erase(it);else ++it;
 times[ch->GetPlayerID()]=now;
 std::set<unsigned> indices;auto& manager=quest::CQuestManager::instance();
 auto include=[&](const char* name){const unsigned index=manager.GetQuestIndexByName(name);if(index)indices.insert(index);};
 for(const auto& native:natives)include(native.quest);
 include("konie");
 using namespace mt2009_quest_rewards;Load();
 for(const auto& row:g_rules) {
  bool permanent=false;
  for(const auto& bonus:row.second.bonus)if(bonus.second.point>0 && bonus.second.value>0)permanent=true;
  for(const auto& bonus:row.second.bonusAny)if(bonus.second.point>0 && bonus.second.value>0)permanent=true;
  for(const auto& anchor:row.second.extras)for(const auto& extra:anchor.second)if(extra.kind=="bonus" && extra.a>0 && extra.a<POINT_MAX_NUM && extra.b>0)permanent=true;
  if(permanent)include(row.first.c_str());
 }
 ch->ChatPacket(CHAT_TYPE_COMMAND,"QSBegin");
 for(unsigned index:indices)ch->ChatPacket(CHAT_TYPE_COMMAND,"QSIndex %u",index);
 ch->ChatPacket(CHAT_TYPE_COMMAND,"QSEnd");
}
}
