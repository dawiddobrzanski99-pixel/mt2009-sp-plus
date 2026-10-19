#ifndef CUSTOM_HORSE_POLYMORPH_REWARDS_V1_H
#define CUSTOM_HORSE_POLYMORPH_REWARDS_V1_H
// CUSTOM_POLY_P_MOVE65_BOSS30_STONE30_V1
struct CustomPolyRewards { int attack, defense, monster, resistMonster, boss, stone, speed, moveSpeed; };
static CustomPolyRewards CustomPolyForLevel(int level)
{
    CustomPolyRewards r = {0,0,0,0,0,0,0,0};
    if (level <= 0) return r;
    if (level >= 40) { r.attack=150; r.defense=150; r.monster=15; r.resistMonster=15; r.boss=30; r.stone=30; r.speed=15; r.moveSpeed=65; return r; }
    if (level <= 29) { r.attack=level*50/29; r.defense=level*50/29; if(level>=20) r.speed=5; return r; }
    const int g=level-29;
    r.attack=50+g*3; r.defense=50+g*2; r.monster=g; r.resistMonster=g; r.speed=5+g/2;
    return r;
}
static int CustomHorseGrowth(int level, int maximum, int last)
{
    if (level<=10) return 0;
    const int steps=level<last ? level-10 : last-10;
    return steps*maximum/(last-10);
}
static int CustomHorseMonsterBoss(int level)
{ return level>=23 ? 10 : level==22 ? 7 : CustomHorseGrowth(level,5,21); }
static int CustomHorseElements(int level)
{ return level>=23 ? 5 : level==22 ? 2 : 0; }
static long CustomPolyDuration(int level, long original)
{ return level>=40 ? 3600 : level>=30 ? 1800 : original; }
#endif
