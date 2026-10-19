#ifndef PLAYERBOT_DUEL_RULES_H
#define PLAYERBOT_DUEL_RULES_H
#include <cstdint>
#include <string>
#include <algorithm>
// Pure rules; world units are centimetres. Engine ranges still cap every cast.
namespace playerbot_duel {
inline constexpr uint32_t reactionMin = 350, reactionMax = 800;
inline constexpr uint32_t openingReactionMin = 350, openingReactionMax = 650;
inline constexpr int castSafetyMargin = 40, challengeDistance = 4000;
inline constexpr uint32_t chargeTimeout = 3000, meleeCommitTime = 3500;
inline constexpr int chargeImpactRange = 200, defensiveRetreatHP = 35;
inline constexpr int magicFallbackRange = 800;
inline constexpr int daggerOpeningRange = 750;
inline constexpr uint32_t daggerSetupMove = 800;
enum class StealthPlan { None, Before, Opening };
inline StealthPlan DaggerStealthPlan(int roll) {
    return roll<35?StealthPlan::Before:roll<75?StealthPlan::Opening:StealthPlan::None;
}
inline const char* ReadyPrompt(int roll) { return roll<85?"r?":roll<95?"ready?":"gotowy?"; }
inline bool AssignClientSyncOwner(bool preparedDuel,bool humanVictim) { return !(preparedDuel && humanVictim); }
// Native melee impacts need ownership to animate their slide. Account for that
// involuntary travel in the engine's next movement check; never accumulate it.
inline constexpr int hitSlideAllowance = 600;
inline bool NeedsHitSlideAllowance(bool preparedDuel,bool humanVictim,bool melee) {
    return preparedDuel && humanVictim && melee;
}
inline int HitSlideMovementBonus(int existing) { return std::max(existing,hitSlideAllowance); }
// A client's Fast Attack normally moves it to the victim. The bot executor
// does not perform that relocation: select/cast it only after normal approach.
inline constexpr int fastAttackContactRange = 280;
inline int FastAttackRange(int protoRange) { return std::min(std::max(0,protoRange),fastAttackContactRange); }
// At zero HP the engine runs StunEvent for three seconds before POS_DEAD.
// SetVictim(NULL) during that window calls battle_end -> POS_STANDING and
// cancels that event. Clear the AI target now, the engine victim after death.
inline bool CanClearEngineVictim(bool dead,int hp) { return dead || hp>0; }
inline constexpr uint32_t skillHitInterval = 250;
inline constexpr int skillHitDisplacement = 120;
inline int DuelSkillHitCount(int perTarget,int engineLimit,int totalBudget) {
    return std::max(0,std::min(std::min(perTarget,engineLimit),totalBudget>0?totalBudget:perTarget));
}
struct SkillHitSequence {
    uint32_t skill=0,nextAt=0,until=0;
    unsigned remaining=0,attempted=0;
    long originX=0,originY=0;
};
inline void StartSkillHits(SkillHitSequence& hits,uint32_t skill,unsigned count,uint32_t now,uint32_t duration) {
    hits={};hits.skill=skill;hits.remaining=count;
    hits.nextAt=now+skillHitInterval;hits.until=now+duration;
}
// Claim a motion hit once, including misses. Never dump overdue hits in a
// single tick or retry a missed collision when the victim returns later.
inline bool ClaimSkillHit(SkillHitSequence& hits,uint32_t now) {
    if(!hits.remaining) return false;
    if((int32_t)(now-hits.until)>=0) {hits={};return false;}
    if((int32_t)(now-hits.nextAt)<0) return false;
    --hits.remaining;++hits.attempted;hits.nextAt=now+skillHitInterval;
    return true;
}
inline constexpr uint32_t comboReset = 2200, opponentObservation = 500, buffReview = 2000;
inline constexpr uint32_t buffReactionMin = 350, buffReactionMax = 700;
// A shared start area, not an exact class-specific stand-off distance.
inline constexpr int startArea = 1800;
inline bool NeedsPreparationApproach(int distance) { return distance > startArea; }
// Zero target range is not unlimited reach. Caster-centred skills use their
// actual splash radius; targeted exceptions are resolved by the engine adapter.
inline bool SkillInRange(int distance, int targetRange, int splashRange,
                         bool selfOnly, bool /*melee*/, int contactRange) {
    int reach = targetRange > 0 ? targetRange : contactRange;
    if (selfOnly) {
        if (splashRange <= 0) return false;
        reach = splashRange;
    }
    return distance >= 0 && distance <= std::max(0, reach - castSafetyMargin);
}
inline int EffectiveSkillRange(int targetRange, int splashRange, bool selfOnly,
                               bool magic, bool arrow, bool /*targetedRoar*/) {
    if(selfOnly) return std::max(0,splashRange);
    if(targetRange>0) return targetRange;
    if(magic) return magicFallbackRange;
    if(arrow && splashRange>0) return std::max(300,splashRange);
    return 300;
}
inline constexpr uint32_t prepareTimeout = 45000, readyReminder = 14000, readyTimeout = 26000;
inline constexpr int maxDistance = 2400, maxTravel = 3000, readyHP = 95, readySP = 85;
inline constexpr int healHP = 55, finisherHP = 20, minBuffSeconds = 15;
inline constexpr bool debug = true;
inline constexpr uint32_t decisionMin = 120, decisionMax = 300, moveRetry = 650, itemInterval = 1500;
enum class Phase { React, Recover, Approach, Prepare, WaitReady };
enum class Style { Body, Mental, Dagger, Archer, Weapon, Magic, Dragon, Heal };
struct Profile { Style style; const char* name; int startRange, range, minimum; uint32_t repositionMs; int repositionChance; uint32_t skillGap; };
inline Profile GetProfile(int job, int group) {
    static constexpr Profile profiles[8] = {
        {Style::Body,"BODY",350,130,0,1800,0,2300}, {Style::Mental,"MENTAL",400,140,0,2400,0,2600},
        {Style::Dagger,"DAGGER",350,130,0,2800,65,2100}, {Style::Archer,"ARCHER",900,900,500,1800,85,2200},
        {Style::Weapon,"WEAPON",400,140,0,2400,0,2400}, {Style::Magic,"MAGIC",650,650,300,2800,60,2200},
        {Style::Dragon,"DRAGON",550,550,250,3000,45,2500}, {Style::Heal,"HEAL",700,700,350,2300,75,2500}
    };
    return profiles[std::clamp(job,0,3)*2 + (group == 2 ? 1 : 0)];
}
struct WeaponPlan { int reach, approachRange; bool attack, reposition; };
inline int SkillStandOff(int range,int navigationMargin) {
    return std::max(0,range-castSafetyMargin-navigationMargin);
}
inline WeaponPlan BetweenSkills(const Profile& profile, int distance, int bowRange,
                                int meleeRange, bool offensiveCastReady, int navigationMargin = 200) {
    const bool archer = profile.style == Style::Archer;
    const int reach = archer ? std::min(profile.range, bowRange) : meleeRange;
    // A caster lacking a usable spell closes to weapon range instead of
    // repeatedly backing away from the ordinary attack it needs to perform.
    return {reach, std::max(0, reach - navigationMargin), distance <= reach,
            profile.minimum == 0 || archer || offensiveCastReady};
}
inline bool CasterRetreat(int hpPercent, bool meleeCommitted) {
    return hpPercent<=15 || (hpPercent <= defensiveRetreatHP && !meleeCommitted);
}
inline bool EngineComputesSkill(bool selfOnly, bool nonAttack, bool charge,
                                bool summonLightning, bool flameSpirit) {
    return selfOnly || nonAttack || charge || summonLightning || flameSpirit;
}
inline bool HasSkillResources(int sp,int cost,int reserve) {
    return sp>=0 && cost>=0 && reserve>=0 && sp>=cost && sp-cost>=reserve;
}
inline int ComboBeforeSkill(Style style) {
    switch(style) {
        case Style::Body:case Style::Weapon:return 3;
        case Style::Archer:return 1;
        default:return 2;
    }
}
inline bool CanBreakCombo(Style style, unsigned hits, bool inWeaponRange,
                          bool utility, bool finisher) {
    return !inWeaponRange || hits==0 || hits>=(unsigned)ComboBeforeSkill(style) || utility || finisher;
}
inline bool ComboTimedOut(uint32_t now,uint32_t swingFinishedAt) {
    return (int32_t)(now-swingFinishedAt)>(int32_t)comboReset;
}
inline bool SafeBuffCast(int ownHP, int distance, bool foeStunned, bool recentlyHit=false) {
    return ownHP>=65 && (foeStunned || (distance>=700 && !recentlyHit));
}
struct SkillSituation {
    int level = 0;
    bool affordable = true, control = false, poison = false, backstab = false;
    bool dispel = false, burst = false, slow = false;
    bool foeStunned = false, foePoisoned = false, foeSlowed = false;
    bool valuableBuff = false, behind = false, opening = false, finisher = false, close = false;
};
inline int SkillScore(Style style, const SkillSituation& s) {
    int score=s.level;
    if(!s.affordable) score-=400;
    if(s.dispel) {
        if(!s.valuableBuff) return -10000;
        score+=120;
    }
    if(s.control) score+=s.foeStunned?-30:(style==Style::Mental?45:style==Style::Archer && s.close?40:18);
    if(s.slow) score+=s.foeSlowed?-20:(s.close?35:15);
    if(s.poison) score+=s.foePoisoned?-45:(s.opening?45:20);
    if(s.backstab) score+=s.behind?60:-12;
    if(s.burst && s.finisher) score+=50;
    if(style==Style::Dagger && s.poison && !s.foePoisoned) score+=12;
    if(style==Style::Magic && s.slow && s.close) score+=15;
    return score;
}
inline bool ReadyText(const char* text) {
    if (!text) return false;
    std::string s(text);
    const auto first=s.find_first_not_of(" \t\r\n"), last=s.find_last_not_of(" \t\r\n");
    if(first==std::string::npos) return false;
    s=s.substr(first,last-first+1);
    for(char& c:s) if(c>='A' && c<='Z') c+= 'a'-'A';
    return s=="g" || s=="go" || s=="ready";
}
inline int Threat(int botLevel,int playerLevel,int losses) {
    return std::clamp((playerLevel-botLevel >= 15 ? 3 : playerLevel-botLevel >= 5 ? 2 : playerLevel+10 < botLevel ? 0 : 1) + std::min(losses,2),0,3);
}
inline int Budget(int threat) { const int b[]={0,2,6,10}; return b[std::clamp(threat,0,3)]; }
inline int Reserve(int tier) { const int r[]={3,8,15,30}; return r[std::clamp(tier,0,3)]; }
inline int Cost(int tier) { const int c[]={1,3,6,100}; return c[std::clamp(tier,0,3)]; }
inline bool Spend(int stock,int tier,int threat,int budget) {
    return tier<3 && stock>Reserve(tier) && threat>=tier+1 && budget>=Cost(tier);
}
inline bool BlockHP(bool duel,bool guildWar) { return duel && !guildWar; }
}
#endif
