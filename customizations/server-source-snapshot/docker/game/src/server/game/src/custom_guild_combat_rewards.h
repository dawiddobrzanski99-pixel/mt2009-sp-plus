#ifndef CUSTOM_GUILD_COMBAT_REWARDS_H
#define CUSTOM_GUILD_COMBAT_REWARDS_H
// GUILD_RATES_V3: membership-derived, never stored or stacked.
inline int CustomGuildCombatBonus(int type,int level){
 if(level<1)return 0;level=level>GUILD_MAX_LEVEL?GUILD_MAX_LEVEL:level;
 switch(type){
 case POINT_ATTBONUS_MONSTER:
 case POINT_ATTBONUS_BOSS:
 case POINT_ATTBONUS_STONE:
 case POINT_ENCHANT_ELECT:
 case POINT_ENCHANT_FIRE:
 case POINT_ENCHANT_ICE:
 case POINT_ENCHANT_WIND:
 case POINT_ENCHANT_EARTH:
 case POINT_ENCHANT_DARK:
 return level/2;
 case POINT_GOLD_DOUBLE_BONUS:return level/4;
 case POINT_ST:
 case POINT_HT:
 case POINT_DX:
 case POINT_IQ:
 case POINT_ATTBONUS_WARRIOR:
 case POINT_ATTBONUS_ASSASSIN:
 case POINT_ATTBONUS_SURA:
 case POINT_ATTBONUS_SHAMAN:
 case POINT_RESIST_WARRIOR:
 case POINT_RESIST_ASSASSIN:
 case POINT_RESIST_SURA:
 case POINT_RESIST_SHAMAN:
 return level;
 default:return 0;
 }
}
#endif
