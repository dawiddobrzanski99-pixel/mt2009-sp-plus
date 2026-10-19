#ifndef PLAYERBOT_DUEL_H
#define PLAYERBOT_DUEL_H
// Implementation fragment included inside the manager's anonymous namespace,
// after the existing combat, inventory, alchemy and chat helpers.
bool ManagePlayerBotDuelCombat(LPCHARACTER, TPlayerBotAIState&, DWORD);
bool HandlePlayerBotDuelReady(LPCHARACTER from,const char* text);
CPVP* PlayerBotDuelPair(DWORD a,DWORD b);

void LogPlayerBotDuel(LPCHARACTER ch, const char* event) {
    if (playerbot_duel::debug) sys_log(0,"PLAYERBOT_DUEL: pid=%u %s",ch->GetPlayerID(),event);
}
void CleanupPlayerBotDuelOnLeave(LPCHARACTER ch,TPlayerBotAIState& state);

// MT2009_PLUS_BOT_DUEL_AI_V1: bot-v-bot duels through the prepared path.
// On unless a GM sets "/eventflag bot_duel_ai_off 1" (an unset event flag reads
// 0, so the switch is the "off" one); then bot challenges use the old instant
// agreement again. Duels already being prepared or fought finish as they are.
const int PLAYERBOT_DUEL_AI_MAX_BOT_PAIRS = 6;     // per core, prepared + fighting
const DWORD PLAYERBOT_DUEL_AI_CENSUS_MS = 10 * 60 * 1000;
const DWORD PLAYERBOT_DUEL_AI_SIDE_TIMEOUT = playerbot_duel::prepareTimeout + playerbot_duel::readyTimeout + 5000;
struct TPlayerBotDuelAiCensus {
    unsigned started=0, ready=0, aborted=0, capped=0, ended=0, ko=0, timeout=0, distance=0, safeZone=0, despawn=0, other=0;
};
TPlayerBotDuelAiCensus s_playerBotDuelAiCensus;
DWORD s_dwPlayerBotDuelAiCensusAt=0;
bool IsPlayerBotDuelAiOn() {
    return quest::CQuestManager::instance().GetEventFlag("bot_duel_ai_off")==0;
}
// Prepared or fighting bot-v-bot pairs on this core, each counted once.
int CountPlayerBotDuelAiPairs() {
    int n=0;
    for(const auto& c:playerbot_pvp::challenges) if(c.second.botChallenger) ++n;
    for(const auto& d:playerbot_pvp::duels) if(d.second.botOwner) ++n;
    return n;
}
// A bot already being prepared for a duel, on either side, takes no new one.
bool IsPlayerBotDuelAiBusy(DWORD pid) {
    return playerbot_pvp::challenges.count(pid) || playerbot_pvp::botSides.count(pid);
}
void ManagePlayerBotDuelAiCensus(DWORD now) {
    if(s_dwPlayerBotDuelAiCensusAt==0) {s_dwPlayerBotDuelAiCensusAt=now;return;}
    if(now-s_dwPlayerBotDuelAiCensusAt<PLAYERBOT_DUEL_AI_CENSUS_MS) return;
    s_dwPlayerBotDuelAiCensusAt=now;
    const auto& c=s_playerBotDuelAiCensus;
    sys_log(0,"PLAYERBOT_DUEL_BB: census on=%d active=%d cap=%d started=%u ready=%u aborted_prep=%u capped=%u ended=%u ko=%u timeout=%u distance=%u safe_zone=%u despawn=%u other=%u",
        IsPlayerBotDuelAiOn()?1:0,CountPlayerBotDuelAiPairs(),PLAYERBOT_DUEL_AI_MAX_BOT_PAIRS,
        c.started,c.ready,c.aborted,c.capped,c.ended,c.ko,c.timeout,c.distance,c.safeZone,c.despawn,c.other);
    s_playerBotDuelAiCensus=TPlayerBotDuelAiCensus();
}
// The challenger's side ends: its preparation forgotten, a pending pair removed.
void DropPlayerBotDuelAiSide(LPCHARACTER ch,const char* why) {
    auto side=playerbot_pvp::botSides.find(ch->GetPlayerID());
    if(side==playerbot_pvp::botSides.end()) return;
    const DWORD foePid=side->second.challengerPid;
    if(side->second.alchemyStarted && !playerbot_pvp::duels.count(ch->GetPlayerID())) ch->DragonSoul_DeactivateAll();
    playerbot_pvp::botSides.erase(side);
    if(CPVP* pair=PlayerBotDuelPair(ch->GetPlayerID(),foePid)) {
        if(!pair->IsFight()) {pair->Packet(true);CPVPManager::instance().Delete(pair);}
    }
    sys_log(0,"PLAYERBOT_DUEL_BB: challenger stop pid=%u foe=%u reason=%s",ch->GetPlayerID(),foePid,why);
}
bool PlayerBotDuelWar(LPCHARACTER ch,const TPlayerBotAIState& state) {
    return ch->GetWarMap()!=NULL || state.dwGuildWarEnemyGID!=0 || (ch->GetGuild() && GetPlayerBotWarEnemy(ch->GetGuild()));
}
CPVP* PlayerBotDuelPair(DWORD a,DWORD b) {
    CPVP key(a,b); return CPVPManager::instance().Find(key.GetCRC());
}
void CancelPlayerBotPreparation(LPCHARACTER ch,TPlayerBotAIState& state,const char* why) {
    auto it=playerbot_pvp::challenges.find(ch->GetPlayerID());
    if(it==playerbot_pvp::challenges.end()) return;
    if(it->second.alchemyStarted) ch->DragonSoul_DeactivateAll();
    // MT2009_PLUS_BOT_DUEL_AI_V1: a bot-v-bot preparation counted once, here.
    if(it->second.botChallenger) {
        ++s_playerBotDuelAiCensus.aborted;
        sys_log(0,"PLAYERBOT_DUEL_BB: prep aborted pid=%u challenger=%u reason=%s",ch->GetPlayerID(),it->second.challengerPid,why);
        if(LPCHARACTER challenger=CHARACTER_MANAGER::instance().FindByPID(it->second.challengerPid))
            DropPlayerBotDuelAiSide(challenger,"challenged side gave up");
        else playerbot_pvp::botSides.erase(it->second.challengerPid);
    }
    if(CPVP* pair=PlayerBotDuelPair(ch->GetPlayerID(),it->second.challengerPid)) {
        if(!pair->IsFight()) {pair->Packet(true);CPVPManager::instance().Delete(pair);}
    }
    playerbot_pvp::Forget(ch->GetPlayerID());
    state.dwTargetVID=0;
    if(playerbot_duel::CanClearEngineVictim(ch->IsDead(),ch->GetHP())) ch->SetVictim(NULL);
    ClearPlayerBotRoute(state,true);
    ch->SetTarget(NULL);
    if(ch->IsAffectFlag(AFF_MUYEONG)) ch->StartMuyeongEvent();
    if(!ch->IsDead()) ch->Stop();
    LogPlayerBotDuel(ch,why);
}
void FinishPlayerBotPreparedDuel(LPCHARACTER ch,TPlayerBotAIState& state,DWORD now,const char* why,int result=0) {
    auto it=playerbot_pvp::duels.find(ch->GetPlayerID());
    if(it==playerbot_pvp::duels.end()) return;
    const auto duel=it->second;
    if(duel.chargeUntil) ch->RemoveAffect(SKILL_CHARGE);
    if(duel.prepared) {
        LPCHARACTER foe=CHARACTER_MANAGER::instance().FindByPID(duel.opponentPid);
        if(foe && foe->GetDesc() && !foe->GetDesc()->IsBot()) foe->SetSyncOwner(NULL);
        playerbot_pvp::RecordResult(ch->GetPlayerID(),duel.opponentPid,result);
        // MT2009_PLUS_BOT_DUEL_AI_V1: each side logs its own result; the
        // challenged side alone feeds the census, so a duel counts once.
        if(duel.botPair) {
            sys_log(0,"PLAYERBOT_DUEL_BB: end pid=%u foe=%u side=%s reason=%s result=%s",ch->GetPlayerID(),duel.opponentPid,
                duel.botOwner?"challenged":"challenger",why,result>0?"win":result<0?"loss":"draw");
            if(duel.botOwner) {
                auto& c=s_playerBotDuelAiCensus;++c.ended;
                if(!strcmp(why,"end ko")) ++c.ko; else if(!strcmp(why,"end timeout")) ++c.timeout;
                else if(!strcmp(why,"end distance")) ++c.distance; else if(!strcmp(why,"safe zone")) ++c.safeZone;
                else if(!strcmp(why,"despawn duel")) ++c.despawn; else ++c.other;
            }
        }
        if(duel.alchemyStarted) {ch->DragonSoul_DeactivateAll();state.dwLastCombatActionTime=0;}
    }
    // EndPlayerBotDuel needs the opponent even when the deadline just expired.
    it->second.until=now+1000;
    EndPlayerBotDuel(ch,state,now,why);
    playerbot_pvp::Forget(ch->GetPlayerID());
    state.dwTargetVID=0;
    if(playerbot_duel::CanClearEngineVictim(ch->IsDead(),ch->GetHP())) ch->SetVictim(NULL);
    ClearPlayerBotRoute(state,true);
    ch->SetTarget(NULL);
    if(!ch->IsDead()) ch->Stop();
    state.dwNextPotionTime=now; state.dwNextManaPotionTime=now;
    state.bComboMotion=MOTION_COMBO_ATTACK_1;
    SetPlayerBotAction(state,BOT_ACTION_IDLE,now);
    LogPlayerBotDuel(ch,why);
}
void CleanupPlayerBotDuelOnLeave(LPCHARACTER ch,TPlayerBotAIState& state) {
    if(!ch) return;
    CancelPlayerBotPreparation(ch,state,"despawn preparation");
    DropPlayerBotDuelAiSide(ch,"despawn"); // MT2009_PLUS_BOT_DUEL_AI_V1
    if(playerbot_pvp::duels.count(ch->GetPlayerID()))
        FinishPlayerBotPreparedDuel(ch,state,get_dword_time(),"despawn duel");
}
// Spatial gates use the engine's pathfinder, never Show/Warp/teleport.
bool MovePlayerBotDuelRange(LPCHARACTER ch,LPCHARACTER foe,DWORD now,int range,int angleOffset=0) {
    const double dx=ch->GetX()-foe->GetX(),dy=ch->GetY()-foe->GetY();
    const double angle=atan2(dy,dx)+angleOffset*3.141592653589793/180.0;
    return MovePlayerBot(ch,foe->GetX()+(long)(cos(angle)*range),foe->GetY()+(long)(sin(angle)*range),now,4,false,false);
}
bool PlayerBotDuelValuableBuff(LPCHARACTER foe) {
    const auto build=GetPlayerBotSkillBuild(foe->GetJob(),foe->GetSkillGroup(),foe->GetPlayerID());
    for(DWORD skill:build.dwBuffSkills) if(skill && skill!=SKILL_CURE && FindPlayerBotBuffMainAffect(foe,skill)) return true;
    return false;
}
int PlayerBotDuelSkillRange(DWORD skill) {
    CSkillProto* proto=CSkillManager::instance().Get(skill);
    if(!proto) return 0;
    const int reach=playerbot_duel::EffectiveSkillRange(proto->dwTargetRange,proto->iSplashRange,
        IS_SET(proto->dwFlag,SKILL_FLAG_SELFONLY),proto->bSkillAttrType==SKILL_ATTR_TYPE_MAGIC,
        IS_SET(proto->dwFlag,SKILL_FLAG_USE_ARROW_DAMAGE),skill==SKILL_DRAGON_ROAR);
    return skill==SKILL_FAST_ATTACK?playerbot_duel::FastAttackRange(reach):reach;
}
bool PlayerBotDuelSkillReaches(DWORD skill,int distance) {
    const int reach=PlayerBotDuelSkillRange(skill);
    return reach>0 && playerbot_duel::SkillInRange(distance,reach,0,false,false,PLAYERBOT_MELEE_SPLASH_RANGE);
}
bool PlayerBotDuelClearLine(LPCHARACTER ch,LPCHARACTER foe) {
    auto& nav=CPlayerBotNavigation::instance(ch->GetMapIndex());
    return nav.Init(ch->GetMapIndex()) && nav.SegmentClearWorld(ch->GetX(),ch->GetY(),foe->GetX(),foe->GetY());
}
int PlayerBotDuelHealingReserve(LPCHARACTER ch,const TPlayerBotAIState& state,DWORD now) {
    if(ch->GetJob()!=JOB_SHAMAN || ch->GetSkillGroup()!=2 || ch->GetMaxHP()<=0 ||
        ch->GetHP()*100/ch->GetMaxHP()>=65 || !ch->GetSkillLevel(SKILL_CURE) || !IsPlayerBotSkillReady(state,SKILL_CURE,now)) return 0;
    return GetPlayerBotSkillSPCost(ch,SKILL_CURE);
}
DWORD SelectPlayerBotDuelSkill(LPCHARACTER ch,LPCHARACTER foe,TPlayerBotAIState& state,DWORD now,bool opening=false,bool approachCandidate=false) {
    auto build=GetPlayerBotSkillBuild(ch->GetJob(),ch->GetSkillGroup(),ch->GetPlayerID());
    // The shared WP PvE build leaves its last slots empty. Include a learned
    // Dispel for duels without changing that build's PvE/Guild War rotation.
    if(ch->GetJob()==JOB_SURA && ch->GetSkillGroup()==1 && ch->GetSkillLevel(SKILL_DISPEL)>0) {
        bool listed=false;for(DWORD skill:build.dwOffensiveSkills) if(skill==SKILL_DISPEL) listed=true;
        if(!listed) for(DWORD& skill:build.dwOffensiveSkills) if(!skill) {skill=SKILL_DISPEL;break;}
    }
    const int distance=DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY());
    const auto profile=playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup());
    if(!PlayerBotDuelClearLine(ch,foe)) return 0;
    const bool valuableBuff=PlayerBotDuelValuableBuff(foe);
    auto active=playerbot_pvp::duels.find(ch->GetPlayerID());
    const bool dispelObserved=active==playerbot_pvp::duels.end() ||
        (active->second.opponentBuff && (int32_t)(now-active->second.dispelAt)>=0);
    const int healCost=PlayerBotDuelHealingReserve(ch,state,now);
    int best=-10000;DWORD selected=0;
    for(DWORD skill:build.dwOffensiveSkills) {
        // Charge's UseSkill(target) already computes its hit. Handle its
        // dash/impact separately instead of the generic damage executor.
        if(!skill || skill==SKILL_CHARGE || !ch->GetSkillLevel(skill) || !IsPlayerBotSkillReady(state,skill,now) ||
            (!approachCandidate && !PlayerBotDuelSkillReaches(skill,distance))) continue;
        CSkillProto* proto=CSkillManager::instance().Get(skill);
        if(!proto || (skill==SKILL_DISPEL && (!valuableBuff || !dispelObserved))) continue;
        playerbot_duel::SkillSituation situation;
        situation.level=ch->GetSkillLevel(skill);
        situation.affordable=playerbot_duel::HasSkillResources(ch->GetSP(),GetPlayerBotSkillSPCost(ch,skill),healCost);
        situation.control=(IS_SET(proto->dwFlag,SKILL_FLAG_STUN) && !IS_SET(proto->dwFlag,SKILL_FLAG_STUN_MOB)) ||
            (IS_SET(proto->dwFlag,SKILL_FLAG_CRUSH | SKILL_FLAG_CRUSH_LONG) && !IS_SET(proto->dwFlag,SKILL_FLAG_CRUSH_MOB));
        situation.slow=IS_SET(proto->dwFlag,SKILL_FLAG_SLOW);
        situation.poison=IS_SET(proto->dwFlag,SKILL_FLAG_POISON);
        situation.dispel=skill==SKILL_DISPEL;
        situation.backstab=skill==SKILL_AMBUSH;
        situation.burst=skill==SKILL_DARK_ORB || (ch->GetJob()==JOB_WARRIOR && ch->GetSkillGroup()==2) || skill==SKILL_AMBUSH;
        situation.foeStunned=foe->IsStun();situation.foePoisoned=foe->IsAffectFlag(AFF_POISON);
        situation.foeSlowed=foe->IsAffectFlag(AFF_SLOW);situation.valuableBuff=valuableBuff;
        // Use the direction we would face for this cast, not the previous tick's rotation.
        const float castFacing=GetDegreeFromPositionXY(ch->GetX(),ch->GetY(),foe->GetX(),foe->GetY());
        situation.behind=GetDegreeDelta(castFacing,foe->GetRotation())<number(25,45);
        situation.opening=opening;situation.close=distance<500;
        situation.finisher=foe->GetMaxHP()>0 && foe->GetHP()*100/foe->GetMaxHP()<playerbot_duel::finisherHP;
        const int score=playerbot_duel::SkillScore(profile.style,situation)+number(0,8);
        if(score>best) {best=score;selected=skill;}
    }
    return selected;
}
bool CastPlayerBotDuelSelfBuff(LPCHARACTER ch,TPlayerBotAIState& state,DWORD now,bool healingOnly=false) {
    const auto build=GetPlayerBotSkillBuild(ch->GetJob(),ch->GetSkillGroup(),ch->GetPlayerID());
    for(DWORD skill:build.dwBuffSkills) {
        if(!skill || !ch->GetSkillLevel(skill) || (healingOnly && skill!=SKILL_CURE)) continue;
        if(skill==SKILL_CURE) {
            if(ch->GetMaxHP()<=0 || ch->GetHP()*100/ch->GetMaxHP()>playerbot_duel::healHP) continue;
        } else if(IsPlayerBotBuffAffectOn(ch,skill) && !IsPlayerBotBuffRunningOut(ch,skill)) continue;
        else state.mapBuffActiveUntil.erase(skill); // Engine affect is authoritative after Dispel.
        if(!IsPlayerBotSkillReady(state,skill,now)) continue;
        if(ch->GetSP()<GetPlayerBotSkillSPCost(ch,skill)) {UseManaPotion(ch,state,now,100);return !healingOnly;}
        // Never toggle an active skill off; a nearly spent toggle stays on.
        if(skill!=SKILL_CURE && ch->FindAffect(skill)) continue;
        ch->Stop();ClearPlayerBotRoute(state,true);
        if(!PlayerBotUseSkill(ch,state,skill,ch,now)) continue;
        SendPlayerBotSkillPacket(ch,skill);state.dwLastBotSkillTime=now;
        if(skill==SKILL_FLAME_SPIRIT && playerbot_pvp::challenges.count(ch->GetPlayerID())) ch->StopMuyeongEvent();
        if(healingOnly) {
            auto duel=playerbot_pvp::duels.find(ch->GetPlayerID());
            if(duel!=playerbot_pvp::duels.end()) {duel->second.weaponChain=0;duel->second.lastWeaponAt=0;}
            state.bComboMotion=MOTION_COMBO_ATTACK_1;
        }
        state.dwNextAttackTime=now+PLAYERBOT_SKILL_ANIMATION_LOCK;
        state.mapBuffActiveUntil[skill]=now+(skill==SKILL_CURE?10000:PLAYERBOT_BUFF_FALLBACK_DURATION);
        LogPlayerBotDuel(ch,healingOnly?"heal":"buff");return true;
    }
    return false;
}

// Recognise only the existing proto-supported families. Unknown/event items
// are never spent. Affect type/point/value follow char_item.cpp, including dew sockets.
struct DuelBooster {WORD cell;DWORD vnum;int stock,tier,point,value;DWORD affect;};
bool DescribePlayerBotDuelBooster(LPITEM item,DuelBooster& out) {
    if(!item || item->isLocked() || item->IsExchanging()) return false;
    out.vnum=item->GetVnum();out.cell=item->GetCell();out.stock=0;
    if(item->GetType()==ITEM_BLEND && out.vnum>=50821 && out.vnum<=50826) {
        out.tier=1;out.affect=AFFECT_BLEND;out.point=item->GetSocket(0);out.value=item->GetSocket(1);
        if(item->GetSocket(2)<30) return false;
    } else if(IsPlayerBotBoosterItem(item)) {
        if(item->GetSubType()==USE_ABILITY_UP) {
            out.point=item->GetValue(0);out.value=item->GetValue(2);
            out.affect=out.point==POINT_MOV_SPEED?AFFECT_MOV_SPEED:out.point==POINT_ATT_SPEED?AFFECT_ATT_SPEED:AFFECT_STR;
            const bool water=out.vnum>=50801 && out.vnum<=50820;
            bool known=water || (out.vnum>=27100 && out.vnum<=27105) || out.vnum==27053 || out.vnum==27054;
            for(DWORD v:PLAYERBOT_BOOSTER_VNUMS) if(v==out.vnum) known=true;
            if(!known) return false;
            out.tier=water?1:0;
            if(water) out.affect=AFFECT_EXP_BONUS_EURO_FREE;
        } else {
            // Existing itemshop booster list is the premium family, no new item table.
            const bool water=out.vnum>=50801 && out.vnum<=50820;
            bool known=water;for(DWORD v:PLAYERBOT_ISHOP_BOOSTER_VNUMS) if(v==out.vnum) known=true;
            if(!known) return false;
            out.tier=water?1:2;out.affect=item->GetValue(0);out.point=item->GetValue(1);out.value=item->GetValue(2);
        }
    } else return false;
    switch(out.point) {
        case POINT_ATT_SPEED:case POINT_MOV_SPEED:case POINT_CASTING_SPEED:
        case POINT_ATT_GRADE_BONUS:case POINT_DEF_GRADE_BONUS:case POINT_CRITICAL_PCT:
        case POINT_PENETRATE_PCT:case POINT_RESIST_MAGIC:case POINT_MAX_HP_PCT:
        case POINT_MALL_ATTBONUS:case POINT_MALL_DEFBONUS:
        case POINT_ST:case POINT_DX:case POINT_HT:case POINT_IQ:return out.value>0;
        default:return false;
    }
}
bool PreparePlayerBotDuelItem(LPCHARACTER ch,playerbot_pvp::Challenge& prep,DWORD now) {
    if(prep.playerReady || prep.budget<=0) return false;
    if(prep.nextItem && (int32_t)(now-prep.nextItem)<0) return true;
    prep.nextItem=now+playerbot_duel::itemInterval;
    std::map<DWORD,DuelBooster> stock;
    for(WORD cell=0;cell<PLAYERBOT_BAG_CELLS;++cell) {
        LPITEM item=ch->GetInventoryItem(cell);DuelBooster b;
        if(!item || item->GetCell()!=cell || IsPlayerBotSidekickHeld(ch,item) || !DescribePlayerBotDuelBooster(item,b)) continue;
        auto it=stock.find(b.vnum);
        if(it==stock.end()) it=stock.emplace(b.vnum,b).first;
        it->second.stock+=item->GetCount();
        if(b.value>it->second.value) {const int n=it->second.stock;it->second=b;it->second.stock=n;}
    }
    const DuelBooster* best=NULL;
    for(const auto& entry:stock) {
        const auto& b=entry.second;
        if(!playerbot_duel::Spend(b.stock,b.tier,prep.threat,prep.budget)) {
            if(!prep.reserveLogged && b.stock<=playerbot_duel::Reserve(b.tier)) {
                prep.reserveLogged=true;LogPlayerBotDuel(ch,"consumable skipped: PvE reserve");
            }
            continue;
        }
        if(ch->FindAffect(b.affect,b.point) || ch->FindAffect(AFFECT_POTION_BOOST,b.point)) continue;
        if(b.affect==AFFECT_BLEND && ch->FindAffect(AFFECT_EXP_BONUS_EURO_FREE,POINT_RESIST_MAGIC)) continue;
        bool covered=false;
        for(const CAffect* a:ch->GetAffectContainer())
            if(a->bApplyOn==b.point && a->lApplyValue>=b.value && a->lDuration>=playerbot_duel::minBuffSeconds) covered=true;
        if(covered) continue;
        if(!best || b.value>best->value) best=&b;
    }
    if(!best) {prep.budget=0;return false;}
    LPITEM item=ch->GetInventoryItem(best->cell);if(!item || item->GetVnum()!=best->vnum) return false;
    const int before=item->GetCount(); const DWORD id=item->GetID();
    ch->UseItem(TItemPos(INVENTORY,best->cell));
    item=ch->GetInventoryItem(best->cell);
    if(!item || item->GetID()!=id || (int)item->GetCount()<before) {
        prep.budget-=playerbot_duel::Cost(best->tier);LogPlayerBotDuel(ch,"consumable used above PvE reserve");return true;
    }
    prep.budget=0;return false;
}

bool ManagePlayerBotDuelCharge(LPCHARACTER ch,LPCHARACTER foe,TPlayerBotAIState& state,
                              playerbot_pvp::Duel& duel,DWORD now,int distance) {
    if(duel.chargeUntil) {
        if((int32_t)(now-duel.chargeUntil)>=0 || !ch->IsAffectFlag(AFF_CHARGE_DASH)) {
            ch->RemoveAffect(SKILL_CHARGE);duel.chargeUntil=0;
            LogPlayerBotDuel(ch,"charge cancelled before impact");return false;
        }
        if(ch->IsStun()) return true;
        if(distance<=playerbot_duel::chargeImpactRange) {
            ch->Stop();ClearPlayerBotRoute(state,true);ch->SetRotationToXY(foe->GetX(),foe->GetY());
            // Charge's target phase performs ComputeSkill internally and
            // consumes AFF_CHARGE_DASH. Do not compute damage a second time.
            if(ch->UseSkill(SKILL_CHARGE,foe)) {
                duel.chargeUntil=0;state.dwLastEngineSkillTime=now;
                duel.weaponChain=0;duel.lastWeaponAt=0;state.bComboMotion=MOTION_COMBO_ATTACK_1;
                SendPlayerBotSkillPacket(ch,SKILL_CHARGE);
                state.dwNextAttackTime=now+PLAYERBOT_SKILL_ANIMATION_LOCK;
                LogPlayerBotDuel(ch,"charge impact");return true;
            }
        }
        if(!duel.nextChase || (int32_t)(now-duel.nextChase)>=0) {
            duel.nextChase=now+playerbot_duel::moveRetry;
            MovePlayerBotDuelRange(ch,foe,now,0);
        }
        return true;
    }
    if(ch->GetJob()!=JOB_WARRIOR || ch->GetSkillGroup()!=1 || !ch->GetSkillLevel(SKILL_CHARGE) ||
        distance>PLAYERBOT_DUEL_CHARGE_RANGE || ch->IsRiding() || ch->IsStun() ||
        (int32_t)(now-state.dwNextSkillCastTime)<0 || (int32_t)(now-state.dwNextAttackTime)<0 ||
        !IsPlayerBotSkillReady(state,SKILL_CHARGE,now) || !CanPlayerBotStrikeCharacter(ch,foe)) return false;
    if(!CanPlayerBotAffordSkill(ch,state,SKILL_CHARGE,now)) {UseManaPotion(ch,state,now,100);return false;}
    if(distance<=GetPlayerBotBasicAttackRange(ch) && !playerbot_duel::CanBreakCombo(playerbot_duel::Style::Body,
        duel.weaponChain,true,false,foe->GetMaxHP()>0 && foe->GetHP()*100/foe->GetMaxHP()<playerbot_duel::finisherHP)) return false;
    if(!PlayerBotDuelClearLine(ch,foe)) return false;
    ch->Stop();ClearPlayerBotRoute(state,true);ch->SetRotationToXY(foe->GetX(),foe->GetY());
    const bool contact=distance<=playerbot_duel::chargeImpactRange;
    if(!PlayerBotUseSkill(ch,state,SKILL_CHARGE,contact?foe:ch,now)) return false;
    state.dwLastBotSkillTime=now;
    duel.weaponChain=0;duel.lastWeaponAt=0;state.bComboMotion=MOTION_COMBO_ATTACK_1;
    state.dwNextSkillCastTime=now+playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup()).skillGap;
    if(contact) {
        SendPlayerBotSkillPacket(ch,SKILL_CHARGE);
        state.dwNextAttackTime=now+PLAYERBOT_SKILL_ANIMATION_LOCK;
        LogPlayerBotDuel(ch,"charge contact impact");
    } else {
        duel.chargeUntil=now+playerbot_duel::chargeTimeout;duel.nextChase=now+playerbot_duel::moveRetry;
        MovePlayerBotDuelRange(ch,foe,now,0);
        LogPlayerBotDuel(ch,"charge dash started");
    }
    return true;
}

bool ManagePlayerBotDuelSkillHits(LPCHARACTER ch,LPCHARACTER foe,playerbot_pvp::Duel& duel,DWORD now) {
    auto& sequence=duel.skillHits;
    if(!sequence.remaining) return false;
    if(ch->IsStun() || ch->IsAffectFlag(AFF_STUN) || ch->IsPolymorphed() || ch->IsStateMove() ||
        DISTANCE_APPROX(ch->GetX()-sequence.originX,ch->GetY()-sequence.originY)>playerbot_duel::skillHitDisplacement) {
        sequence={};LogPlayerBotDuel(ch,"skill contacts interrupted");return false;
    }
    if(!playerbot_duel::ClaimSkillHit(sequence,now)) return sequence.remaining>0;
    const DWORD skill=sequence.skill;
    const int distance=DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY());
    const bool inArc=IsPlayerBotSkillAroundCaster(skill) ||
        cosf(GetDegreeDelta(ch->GetRotation(),GetDegreeFromPositionXY(ch->GetX(),ch->GetY(),foe->GetX(),foe->GetY()))*3.141592653589793f/180.0f)>=PLAYERBOT_MELEE_SPLASH_FACING_DOT;
    // A claimed hit can miss. The next one is a new collision check, not a
    // guarantee of three hits on an opponent who escaped the animation.
    if(!inArc || !PlayerBotDuelSkillReaches(skill,distance) || !PlayerBotDuelClearLine(ch,foe) ||
        !CanPlayerBotStrikeCharacter(ch,foe) || !ch->CheckSkillHitCount((BYTE)skill,foe->GetVID())) {
        LogPlayerBotDuel(ch,"skill contact missed/refused");return true;
    }
    const int before=foe->GetHP();const DWORD foeVID=foe->GetVID();
    ch->ComputeSkill(skill,foe);
    LPCHARACTER after=CHARACTER_MANAGER::instance().Find(foeVID);
    if(playerbot_duel::debug) sys_log(0,"PLAYERBOT_DUEL: skill contact pid=%u skill=%u hit=%u dist=%d hp_delta=%d",ch->GetPlayerID(),skill,sequence.attempted,distance,after?std::max(0,before-after->GetHP()):0);
    return true;
}
bool ManagePlayerBotPreparedCombat(LPCHARACTER ch,LPCHARACTER foe,TPlayerBotAIState& state,DWORD now) {
    auto& duel=playerbot_pvp::duels.at(ch->GetPlayerID());
    // Contacts follow the ongoing skill motion even between decision ticks.
    // The flow above already validated the opponent and canonical CPVP pair.
    if(ManagePlayerBotDuelSkillHits(ch,foe,duel,now)) return true;
    if(duel.nextDecision && (int32_t)(now-duel.nextDecision)<0) return true;
    duel.nextDecision=now+number(playerbot_duel::decisionMin,playerbot_duel::decisionMax);
    const int distance=DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY());
    if(duel.chargeUntil && ManagePlayerBotDuelCharge(ch,foe,state,duel,now,distance)) return true;
    if(ch->IsStun() || ch->IsAffectFlag(AFF_STUN) || ch->IsPolymorphed() || (int32_t)(now-state.dwNextAttackTime)<0) return true;
    if(duel.stealthOpening) {
        duel.stealthOpening=false;
        if(ch->GetJob()==JOB_ASSASSIN && ch->GetSkillGroup()==1 && ch->GetSkillLevel(SKILL_STEALTH)>0 &&
            !IsPlayerBotBuffAffectOn(ch,SKILL_STEALTH) && CanPlayerBotAffordSkill(ch,state,SKILL_STEALTH,now) &&
            PlayerBotUseSkill(ch,state,SKILL_STEALTH,ch,now)) {
            ch->Stop();ClearPlayerBotRoute(state,true);SendPlayerBotSkillPacket(ch,SKILL_STEALTH);
            state.dwNextAttackTime=now+PLAYERBOT_SKILL_ANIMATION_LOCK;duel.openingSkill=0;
            LogPlayerBotDuel(ch,"stealth after accept");return true;
        }
    }
    state.dwTargetVID=foe->GetVID();ch->SetVictim(foe);SetPlayerBotAction(state,BOT_ACTION_FIGHT,now);
    const auto profile=playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup());
    if(duel.lastWeaponAt && playerbot_duel::ComboTimedOut(now,state.dwNextAttackTime)) {
        duel.weaponChain=0;duel.lastWeaponAt=0;state.bComboMotion=MOTION_COMBO_ATTACK_1;
    }
    if(!duel.nextOpponentCheck || (int32_t)(now-duel.nextOpponentCheck)>=0) {
        duel.nextOpponentCheck=now+playerbot_duel::opponentObservation;
        if(duel.observedHP>0 && ch->GetHP()<duel.observedHP) duel.lastDamagedAt=now;
        duel.observedHP=ch->GetHP();
        const bool buff=PlayerBotDuelValuableBuff(foe);
        if(buff && !duel.opponentBuff) duel.dispelAt=now+number(playerbot_duel::buffReactionMin,playerbot_duel::buffReactionMax);
        duel.opponentBuff=buff;
    }
    // Finish the sword sequence, let its real animation complete, then pursue
    // the victim's client-reported landing position before choosing a spell.
    // Do not pull the victim back, invent a landing point or teleport the bot.
    if(profile.style==playerbot_duel::Style::Body && duel.weaponChain>=4 &&
        state.bComboMotion==MOTION_COMBO_ATTACK_1 && distance>GetPlayerBotBasicAttackRange(ch)) {
        if(!duel.nextChase || (int32_t)(now-duel.nextChase)>=0) {
            duel.nextChase=now+playerbot_duel::moveRetry;
            MovePlayerBotDuelRange(ch,foe,now,std::max(0,GetPlayerBotBasicAttackRange(ch)-PLAYERBOT_NAV_ARRIVAL_DISTANCE-100));
        }
        return true;
    }
    if(ManagePlayerBotDuelCharge(ch,foe,state,duel,now,distance)) return true;
    const bool finisher=foe->GetMaxHP()>0 && foe->GetHP()*100/foe->GetMaxHP()<playerbot_duel::finisherHP;
    const int ownHP=ch->GetMaxHP()>0?ch->GetHP()*100/ch->GetMaxHP():0;
    if(profile.style==playerbot_duel::Style::Heal && ownHP<=30 && CastPlayerBotDuelSelfBuff(ch,state,now,true)) return true;
    if(duel.moveUntil && (int32_t)(now-duel.moveUntil)<0) return true;
    duel.moveUntil=0;
    DWORD skill=duel.openingSkill;
    // Revalidate the opener after the reaction delay, before deciding whether
    // there is an actual cast available or ordinary weapon pressure is needed.
    if (!skill || !IsPlayerBotSkillReady(state,skill,now) || !PlayerBotDuelSkillReaches(skill,distance) ||
        (skill==SKILL_DISPEL && !PlayerBotDuelValuableBuff(foe)))
        skill=SelectPlayerBotDuelSkill(ch,foe,state,now);
    duel.openingSkill=0;
    const int reserveSP=PlayerBotDuelHealingReserve(ch,state,now);
    UseManaPotion(ch,state,now,skill && ch->GetSP()<GetPlayerBotSkillSPCost(ch,skill)+reserveSP?100:PLAYERBOT_POTION_SP_PERCENT);
    const bool clearLine=PlayerBotDuelClearLine(ch,foe);
    const bool castReady=skill && CanPlayerBotAffordSkill(ch,state,skill,now) &&
        playerbot_duel::HasSkillResources(ch->GetSP(),GetPlayerBotSkillSPCost(ch,skill),reserveSP) && clearLine &&
        PlayerBotDuelSkillReaches(skill,distance) && (int32_t)(now-state.dwNextSkillCastTime)>=0;
    const auto weapon=playerbot_duel::BetweenSkills(profile,distance,GetPlayerBotBowRange(ch->GetMapIndex()),
        GetPlayerBotBasicAttackRange(ch),castReady,PLAYERBOT_NAV_ARRIVAL_DISTANCE+100);
    const bool meleeCommitted=duel.meleeUntil && (int32_t)(now-duel.meleeUntil)<0;
    const bool casterRetreat=playerbot_duel::CasterRetreat(ownHP,meleeCommitted);
    if((!duel.nextBuffCheck || (int32_t)(now-duel.nextBuffCheck)>=0) &&
        playerbot_duel::SafeBuffCast(ownHP,distance,foe->IsStun(),duel.lastDamagedAt && now-duel.lastDamagedAt<2000)) {
        duel.nextBuffCheck=now+playerbot_duel::buffReview;
        if(CastPlayerBotDuelSelfBuff(ch,state,now)) {
            duel.weaponChain=0;duel.lastWeaponAt=0;state.bComboMotion=MOTION_COMBO_ATTACK_1;return true;
        }
    }
    if(profile.style==playerbot_duel::Style::Heal) {
        const int hp=ch->GetMaxHP()>0?ch->GetHP()*100/ch->GetMaxHP():0;
        if(ch->GetSkillLevel(SKILL_CURE)>0 && hp>30 && hp<=playerbot_duel::healHP && distance<profile.minimum &&
            (!duel.nextMove || (int32_t)(now-duel.nextMove)>=0) && CanPlayerBotAffordSkill(ch,state,SKILL_CURE,now)) {
            duel.nextMove=now+profile.repositionMs;
            if(MovePlayerBotDuelRange(ch,foe,now,profile.range,number(-25,25))) {duel.moveUntil=now+500;return true;}
        }
        if(CastPlayerBotDuelSelfBuff(ch,state,now,true)) return true;
    }
    if((int32_t)(now-duel.nextMove)>=0) {
        duel.nextMove=now+profile.repositionMs+number(0,700);
        const float facing=GetDegreeFromPositionXY(ch->GetX(),ch->GetY(),foe->GetX(),foe->GetY());
        const bool flank=profile.style==playerbot_duel::Style::Dagger && distance<350 &&
            ch->GetSkillLevel(SKILL_AMBUSH)>0 && CanPlayerBotAffordSkill(ch,state,SKILL_AMBUSH,now) &&
            GetDegreeDelta(facing,foe->GetRotation())>45 &&
            playerbot_duel::CanBreakCombo(profile.style,duel.weaponChain,weapon.attack,false,finisher);
        const bool canRetreat=profile.style==playerbot_duel::Style::Archer || casterRetreat;
        if(weapon.reposition && !finisher && (flank || (canRetreat && distance<profile.minimum)) && number(1,100)<=profile.repositionChance) {
            const int retreatRange=profile.style==playerbot_duel::Style::Archer?std::min(profile.range,GetPlayerBotBowRange(ch->GetMapIndex())-100):profile.range;
            if(MovePlayerBotDuelRange(ch,foe,now,flank?180:retreatRange,flank?number(65,120):number(-25,25))) {
                duel.moveUntil=now+number(400,700);return true;
            }
        }
    }
    ch->SetRotationToXY(foe->GetX(),foe->GetY());
    const bool utility=skill==SKILL_DISPEL || (profile.style==playerbot_duel::Style::Mental && skill==SKILL_SWORD_STRIKE && foe->IsStateMove() && !foe->IsStun());
    if(castReady && playerbot_duel::CanBreakCombo(profile.style,duel.weaponChain,weapon.attack,utility,finisher)) {
        ch->Stop();ClearPlayerBotRoute(state,true);
        if(ExecutePlayerBotAttackSkill(ch,foe,state,now,skill)) {
            duel.weaponChain=0;duel.lastWeaponAt=0;state.bComboMotion=MOTION_COMBO_ATTACK_1;
            // Leave room for ordinary hits between skills; never shorten the engine cooldown.
            state.dwNextSkillCastTime=now+profile.skillGap+number(0,250);return true;
        }
    }
    // A weapon can reach a few units farther than a contact skill's safe
    // cast limit. Do not stay at that boundary and permanently starve Finger Strike.
    const DWORD approachSkill=!castReady?SelectPlayerBotDuelSkill(ch,foe,state,now,false,true):0;
    if(approachSkill && !PlayerBotDuelSkillReaches(approachSkill,distance) &&
        (profile.style!=playerbot_duel::Style::Archer || PlayerBotDuelSkillRange(approachSkill)>=weapon.reach) &&
        CanPlayerBotAffordSkill(ch,state,approachSkill,now) &&
        playerbot_duel::CanBreakCombo(profile.style,duel.weaponChain,weapon.attack,false,finisher) &&
        (!duel.nextChase || (int32_t)(now-duel.nextChase)>=0)) {
        const int skillStandOff=playerbot_duel::SkillStandOff(PlayerBotDuelSkillRange(approachSkill),PLAYERBOT_NAV_ARRIVAL_DISTANCE+100);
        duel.nextChase=now+playerbot_duel::moveRetry;
        if(MovePlayerBotDuelRange(ch,foe,now,weapon.attack?std::min(weapon.approachRange,skillStandOff):skillStandOff)) return true;
    }
    if(weapon.attack && clearLine) {
        ch->Stop();ClearPlayerBotRoute(state,true);ch->SetPosition(POS_FIGHTING);
        const int foeHP=foe->GetHP();const DWORD foeVID=foe->GetVID();
        const bool swung=ExecutePlayerBotBasicAttack(ch,foe,state,now);
        if(swung) {++duel.weaponChain;duel.lastWeaponAt=now;}
        if(swung && !meleeCommitted) duel.meleeUntil=now+playerbot_duel::meleeCommitTime;
        if(playerbot_duel::debug && (!duel.nextTrace || (int32_t)(now-duel.nextTrace)>=0)) {
            duel.nextTrace=now+5000;
            LPCHARACTER after=CHARACTER_MANAGER::instance().Find(foeVID);
            sys_log(0,"PLAYERBOT_DUEL: weapon pid=%u foe=%u profile=%s dist=%d accepted=%d hp_delta=%d chain=%u moving=%d recovery=%d",ch->GetPlayerID(),duel.opponentPid,profile.name,distance,swung,after?std::max(0,foeHP-after->GetHP()):0,duel.weaponChain,ch->IsStateMove(),state.bRecoveringAfterDeath);
        }
        return true;
    }
    if(!duel.nextChase || (int32_t)(now-duel.nextChase)>=0) {
        duel.nextChase=now+playerbot_duel::moveRetry;
        MovePlayerBotDuelRange(ch,foe,now,weapon.approachRange);
    }
    return true;
}

// MT2009_PLUS_BOT_DUEL_AI_V1: the challenging bot's preparation. It drops PvE,
// sends its horse away, recovers, buffs, wakes its alchemy and spends within
// the same budget as the challenged bot, stands at its class distance and,
// once the other bot has asked "r?", answers "g"/"go" on the local chat after
// a human pause - through HandlePlayerBotDuelReady, as a player's line would.
bool ManagePlayerBotDuelAiChallenger(LPCHARACTER ch,TPlayerBotAIState& state,DWORD now) {
    const DWORD pid=ch->GetPlayerID();
    auto& side=playerbot_pvp::botSides[pid];
    LPCHARACTER foe=CHARACTER_MANAGER::instance().FindByPID(side.challengerPid);
    auto theirs=playerbot_pvp::challenges.find(side.challengerPid);
    if(ch->IsDead() || ch->GetHP()<=0 || !foe || foe->GetMapIndex()!=ch->GetMapIndex() ||
        theirs==playerbot_pvp::challenges.end() || theirs->second.challengerPid!=pid || !theirs->second.botChallenger ||
        PlayerBotDuelWar(ch,state) || ch->GetExchange() || ch->GetMyShop() || ch->IsPolymorphed()) {
        DropPlayerBotDuelAiSide(ch,"invalid");return false;
    }
    auto& their=theirs->second;
    if(!side.seenAt) {
        side.seenAt=now;side.reactAt=now+number(playerbot_duel::reactionMin,playerbot_duel::reactionMax);
        side.desiredRange=playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup()).startRange+number(-40,40);
        auto result=playerbot_pvp::history.find(std::make_pair(pid,side.challengerPid));
        side.threat=playerbot_duel::Threat(ch->GetLevel(),foe->GetLevel(),result==playerbot_pvp::history.end()?0:result->second.streak);
        side.budget=playerbot_duel::Budget(side.threat);
        state.dwTargetVID=0;ch->SetVictim(NULL);ch->SetTarget(NULL);ch->Stop();ClearPlayerBotRoute(state,true);
        state.bVisitingShop=false;state.bTacticalRetreat=false;state.bMultiPullActive=false;
        sys_log(0,"PLAYERBOT_DUEL_BB: challenger prep pid=%u foe=%u threat=%d profile=%s",pid,side.challengerPid,side.threat,
            playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup()).name);
    }
    if(now-side.seenAt>PLAYERBOT_DUEL_AI_SIDE_TIMEOUT) {DropPlayerBotDuelAiSide(ch,"timeout");return false;}
    state.dwTargetVID=0;ch->SetVictim(NULL);state.dwLastMeaningfulActivityTime=now;state.dwLastCombatActionTime=now;
    if(ch->IsAffectFlag(AFF_MUYEONG)) ch->StopMuyeongEvent();
    if((int32_t)(now-side.reactAt)<0 || ch->IsStun()) return true;
    SendPlayerBotHorseAwayForFight(ch,state,now,"duel_prepare");
    if(side.playerReady) return true; // Answered; the challenged bot accepts.
    const int distance=DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY());
    if(ch->GetHP()<ch->GetMaxHP()) UseHealthPotion(ch,state,now,100);
    if(ch->GetSP()<ch->GetMaxSP()) UseManaPotion(ch,state,now,100);
    const bool recovered=ch->GetMaxHP()>0 && ch->GetMaxSP()>0 && ch->GetHP()*100/ch->GetMaxHP()>=playerbot_duel::readyHP &&
        ch->GetSP()*100/ch->GetMaxSP()>=playerbot_duel::readySP;
    if(recovered && state.bRecoveringAfterDeath) EndPlayerBotRecovery(ch,state);
    const bool botSafe=IsPlayerBotSafeZone(ch->GetMapIndex(),ch->GetX(),ch->GetY());
    if(botSafe || playerbot_duel::NeedsPreparationApproach(distance)) {
        if(!side.nextMove || (int32_t)(now-side.nextMove)>=0) {side.nextMove=now+playerbot_duel::moveRetry;MovePlayerBotDuelRange(ch,foe,now,botSafe?0:side.desiredRange);}
        return true;
    }
    if((int32_t)(now-state.dwNextAttackTime)<0) return true;
    ch->Stop();ClearPlayerBotRoute(state,true);ch->SetRotationToXY(foe->GetX(),foe->GetY());
    if(!recovered) return true;
    if(side.phase!=playerbot_duel::Phase::WaitReady) {
        side.phase=playerbot_duel::Phase::Prepare;
        if(CastPlayerBotDuelSelfBuff(ch,state,now)) return true;
        if(!side.alchemyStarted && ch->DragonSoul_GetActiveDeck()<0 && IsPlayerBotAlchemyUser(ch) && ch->DragonSoul_IsQualified() && CountPlayerBotWornDs(ch,true)>0)
            side.alchemyStarted=ch->DragonSoul_ActivateDeck(DRAGON_SOUL_DECK_0);
        if(PreparePlayerBotDuelItem(ch,side,now)) return true;
        side.phase=playerbot_duel::Phase::WaitReady;
    }
    SwitchOffPlayerBotAutoPotionsForDuel(ch,now);
    // The other bot has not asked yet, or a queued red potion is still running.
    if(!their.readyAt || ch->FindAffect(AFFECT_AUTO_HP_RECOVERY) ||
        (ch->GetPoint(POINT_HP_RECOVERY)>0 && ch->GetHP()<ch->GetMaxHP())) return true;
    if(!side.answerAt) side.answerAt=std::max(now,their.readyAt+number(1000,4000));
    if((int32_t)(now-side.answerAt)<0) return true;
    if(ch->GetPoint(POINT_HP_RECOVERY)>0) ch->PointChange(POINT_HP_RECOVERY,-ch->GetPoint(POINT_HP_RECOVERY));
    const char* line=number(0,1)?"g":"go";
    SendPlayerBotLocalChat(ch,line);
    const bool heard=HandlePlayerBotDuelReady(ch,line);
    side.playerReady=true;
    if(heard) ++s_playerBotDuelAiCensus.ready;
    sys_log(0,"PLAYERBOT_DUEL_BB: ready answered pid=%u foe=%u line=%s heard=%d after_ms=%u",pid,side.challengerPid,line,heard?1:0,now-their.readyAt);
    return true;
}
// The challenged bot has just accepted: the challenger fights the same
// prepared duel from its own side, with its own profile.
void StartPlayerBotDuelAiChallengerFight(LPCHARACTER ch,LPCHARACTER foe,DWORD now,playerbot_pvp::Duel& mine) {
    const DWORD foePid=foe->GetPlayerID();
    auto side=playerbot_pvp::botSides.find(foePid);
    const bool alchemy=side!=playerbot_pvp::botSides.end() && side->second.alchemyStarted;
    if(side!=playerbot_pvp::botSides.end()) playerbot_pvp::botSides.erase(side);
    mine.botPair=true;mine.botOwner=true;
    ++s_playerBotDuelAiCensus.started;
    TPlayerBotAIStateMap::iterator fs=s_mapPlayerBotAIStates.find(foePid);
    if(fs==s_mapPlayerBotAIStates.end()) {
        sys_log(0,"PLAYERBOT_DUEL_BB: start pid=%u foe=%u challenger_state=missing",ch->GetPlayerID(),foePid);return;
    }
    TPlayerBotAIState& fstate=fs->second;
    playerbot_pvp::NoteDuelStarted(foePid,ch->GetPlayerID(),now+PLAYERBOT_PVP_DUEL_ASSUMED);
    auto& theirs=playerbot_pvp::duels[foePid];
    theirs.prepared=true;theirs.botPair=true;theirs.alchemyStarted=alchemy;
    theirs.openingSkill=SelectPlayerBotDuelSkill(foe,ch,fstate,now,true);
    theirs.opponentBuff=PlayerBotDuelValuableBuff(ch);theirs.dispelAt=now;
    theirs.observedHP=foe->GetHP();theirs.nextOpponentCheck=now+playerbot_duel::opponentObservation;
    theirs.nextDecision=now+number(playerbot_duel::openingReactionMin,playerbot_duel::openingReactionMax);
    theirs.nextMove=now+1500;fstate.dwNextSkillCastTime=now;
    fstate.dwTargetVID=ch->GetVID();foe->SetVictim(ch);foe->SetTarget(ch);
    fstate.bComboMotion=MOTION_COMBO_ATTACK_1;
    sys_log(0,"PLAYERBOT_DUEL_BB: start pid=%u foe=%u profile=%s foe_profile=%s level=%u foe_level=%u map=%ld",
        ch->GetPlayerID(),foePid,playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup()).name,
        playerbot_duel::GetProfile(foe->GetJob(),foe->GetSkillGroup()).name,(unsigned)ch->GetLevel(),(unsigned)foe->GetLevel(),ch->GetMapIndex());
}

// Called from both scheduled and light ticks. Inactive bots pay only map lookups.
bool ManagePlayerBotDuelFlow(LPCHARACTER ch,TPlayerBotAIState& state,DWORD now) {
    if(!ch) return false;
    const DWORD pid=ch->GetPlayerID();
    auto duel=playerbot_pvp::duels.find(pid);
    if(duel!=playerbot_pvp::duels.end() && duel->second.prepared) {
        LPCHARACTER foe=CHARACTER_MANAGER::instance().FindByPID(duel->second.opponentPid);
        CPVP* pair=PlayerBotDuelPair(pid,duel->second.opponentPid);
        const bool ended=ch->IsDead() || ch->GetHP()<=0 || ch->IsPolymorphed() || !foe || foe->IsDead() || foe->GetHP()<=0 || !foe->GetDesc() || foe->GetMapIndex()!=ch->GetMapIndex() ||
            !pair || !pair->IsFight() || !playerbot_pvp::DuelStands(duel->second.until,now) || PlayerBotDuelWar(ch,state) ||
            ch->GetExchange() || ch->GetMyShop() || ch->GetShop() || foe->GetExchange() || foe->GetMyShop() || DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY())>playerbot_duel::maxDistance;
        if(ended) {
            const int result=ch->IsDead() || ch->GetHP()<=0?-1:foe && (foe->IsDead() || foe->GetHP()<=0)?1:0;
            // MT2009_PLUS_BOT_DUEL_AI_V1: the reason, for the logs and the census.
            const char* why=result?"end ko":!playerbot_pvp::DuelStands(duel->second.until,now)?"end timeout":
                foe && foe->GetMapIndex()==ch->GetMapIndex() && DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY())>playerbot_duel::maxDistance?"end distance":
                PlayerBotDuelWar(ch,state)?"end war":!foe?"end foe gone":"end";
            FinishPlayerBotPreparedDuel(ch,state,now,why,result);return false;
        }
        if(IsPlayerBotSafeZone(ch->GetMapIndex(),ch->GetX(),ch->GetY()) || IsPlayerBotSafeZone(foe->GetMapIndex(),foe->GetX(),foe->GetY())) {
            FinishPlayerBotPreparedDuel(ch,state,now,"safe zone");return false;
        }
        if(ch->GetTarget()!=foe) ch->SetTarget(foe); // Native targeted skill events use GetTarget.
        SwitchOffPlayerBotAutoPotionsForDuel(ch,now);
        state.dwLastCombatActionTime=now;
        ManagePlayerBotDsDeckTick(ch,state,now);
        // Invisible players are not tracked with perfect knowledge.
        if(foe->IsAffectFlag(AFF_SKILL_STEALTH) || foe->IsAffectFlag(AFF_INVISIBILITY)) {duel->second.skillHits={};ch->Stop();return true;}
        return ManagePlayerBotPreparedCombat(ch,foe,state,now);
    }
    // MT2009_PLUS_BOT_DUEL_AI_V1: the challenging bot gets ready as well.
    if(playerbot_pvp::botSides.count(pid)) return ManagePlayerBotDuelAiChallenger(ch,state,now);
    auto it=playerbot_pvp::challenges.find(pid);
    if(it==playerbot_pvp::challenges.end()) return false;
    auto& prep=it->second;
    LPCHARACTER foe=CHARACTER_MANAGER::instance().FindByPID(prep.challengerPid);
    // An unmarked bot challenge (the switch off, a kingdom quarrel) keeps the
    // established autonomous bot-v-bot flow; it has no ready chat.
    if(!prep.botChallenger && foe && foe->GetDesc() && foe->GetDesc()->IsBot()) return false;
    const int distance=foe?DISTANCE_APPROX(ch->GetX()-foe->GetX(),ch->GetY()-foe->GetY()):0;
    CPVP* pair=PlayerBotDuelPair(pid,prep.challengerPid);
    const char* refusal=GetPlayerBotDuelRefusal(ch,now);
    // A travelling bot may have its weapon temporarily unequipped. Prepare it
    // instead of deleting the pending CPVP and forcing a second challenge.
    const bool needsWeapon=refusal && !strcmp(refusal,"no_weapon");
    if(ch->IsDead() || ch->GetHP()<=0 || !foe || !foe->GetDesc() || foe->IsDead() || foe->GetHP()<=0 || foe->GetMapIndex()!=ch->GetMapIndex() || playerbot_pvp::duels.count(pid) ||
        ch->GetLevel()<PK_PROTECT_LEVEL || foe->GetLevel()<PK_PROTECT_LEVEL || ch->GetSkillGroup()==0 || !pair || pair->IsFight() ||
        PlayerBotDuelWar(ch,state) || ch->GetExchange() || ch->GetMyShop() || ch->GetShop() || ch->IsPolymorphed() ||
        (refusal && !needsWeapon) || distance>playerbot_duel::challengeDistance) {
        if(playerbot_duel::debug) sys_log(0,"PLAYERBOT_DUEL: rejected pid=%u reason=%s distance=%d recovering=%d war=%d",pid,refusal?refusal:"invalid pair/character/context",distance,state.bRecoveringAfterDeath,PlayerBotDuelWar(ch,state));
        CancelPlayerBotPreparation(ch,state,"cancel invalid challenge");return false;
    }
    if(!prep.seenAt) {
        prep.seenAt=now;prep.reactAt=now+number(playerbot_duel::reactionMin,playerbot_duel::reactionMax);
        prep.originX=ch->GetX();prep.originY=ch->GetY();prep.map=ch->GetMapIndex();
        prep.desiredRange=playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup()).startRange+number(-40,40);
        if(ch->GetJob()==JOB_ASSASSIN && ch->GetSkillGroup()==1 && ch->GetSkillLevel(SKILL_STEALTH)>0) {
            prep.stealthPlan=playerbot_duel::DaggerStealthPlan(number(0,99));
            if(prep.stealthPlan==playerbot_duel::StealthPlan::Opening) prep.desiredRange=playerbot_duel::daggerOpeningRange+number(-75,75);
        }
        auto result=playerbot_pvp::history.find(std::make_pair(pid,prep.challengerPid));
        prep.threat=playerbot_duel::Threat(ch->GetLevel(),foe->GetLevel(),result==playerbot_pvp::history.end()?0:result->second.streak);
        prep.budget=playerbot_duel::Budget(prep.threat);
        state.dwTargetVID=0;ch->SetVictim(NULL);ch->SetTarget(NULL);ch->Stop();ClearPlayerBotRoute(state,true);
        if(ch->IsAffectFlag(AFF_MUYEONG)) ch->StopMuyeongEvent();
        state.bVisitingShop=false;state.bTacticalRetreat=false;state.bMultiPullActive=false;
        if(playerbot_duel::debug) sys_log(0,"PLAYERBOT_DUEL: challenge pid=%u foe=%u threat=%d profile=%s",pid,prep.challengerPid,prep.threat,playerbot_duel::GetProfile(ch->GetJob(),ch->GetSkillGroup()).name);
    }
    if(playerbot_pvp::PreparationExpired(prep,now) || prep.map!=ch->GetMapIndex() ||
        DISTANCE_APPROX(ch->GetX()-prep.originX,ch->GetY()-prep.originY)>playerbot_duel::maxTravel) {
        SendPlayerBotLocalChat(ch,"nvm");CancelPlayerBotPreparation(ch,state,"preparation timeout");return false;
    }
    state.dwTargetVID=0;ch->SetVictim(NULL);state.dwLastMeaningfulActivityTime=now;
    if(ch->IsAffectFlag(AFF_MUYEONG)) ch->StopMuyeongEvent();
    if((int32_t)(now-prep.reactAt)<0 || ch->IsStun()) return true;
    SendPlayerBotHorseAwayForFight(ch,state,now,"duel_prepare");
    if (needsWeapon) {
        if(!prep.nextItem || (int32_t)(now-prep.nextItem)>=0) {
            prep.nextItem=now+playerbot_duel::itemInterval;
            ReadyPlayerBotHandForFight(ch,state,now,"duel_prepare");
        }
        return true;
    }
    // Keep the handshake while the player steps out of town protection. Never
    // accept or fight in a safe zone, and retain the preparation timeout.
    if(IsPlayerBotSafeZone(foe->GetMapIndex(),foe->GetX(),foe->GetY())) {
        ch->Stop();ClearPlayerBotRoute(state,true);return true;
    }
    if(IsPlayerBotArcherBuild(ch)) {
        LPITEM held=ch->GetWear(WEAR_WEAPON);
        if(!held || held->GetSubType()!=WEAPON_BOW) {
            if(!prep.nextItem || (int32_t)(now-prep.nextItem)>=0) {
                prep.nextItem=now+playerbot_duel::itemInterval;
                state.dwNextEquipmentCheckTime=now;ManagePlayerBotEquipment(ch,state,now);
            }
            return true;
        }
        if(!EnsurePlayerBotArrowsEquipped(ch)) return true;
    }
    // A 100% threshold in the existing potion helper also matches full HP.
    // Do not spend a mixed restoration item while already fully recovered.
    if(ch->GetHP()<ch->GetMaxHP()) UseHealthPotion(ch,state,now,100);
    if(ch->GetSP()<ch->GetMaxSP()) UseManaPotion(ch,state,now,100);
    if(ch->GetMaxHP()<=0 || ch->GetMaxSP()<=0 || ch->GetHP()*100/ch->GetMaxHP()<playerbot_duel::readyHP ||
        ch->GetSP()*100/ch->GetMaxSP()<playerbot_duel::readySP) {prep.phase=playerbot_duel::Phase::Recover;return true;}
    // Preparation has already recovered above the normal post-death threshold.
    // End that existing state before accepting; the basic attack executor
    // correctly refuses swings while bRecoveringAfterDeath remains set.
    if(state.bRecoveringAfterDeath) EndPlayerBotRecovery(ch,state);
    if(prep.stealthPlan==playerbot_duel::StealthPlan::Opening && !prep.setupMoveDone && !prep.playerReady) {
        prep.setupMoveDone=true;
        if(distance<500 && MovePlayerBotDuelRange(ch,foe,now,prep.desiredRange,number(-15,15))) {
            prep.setupMoveUntil=now+playerbot_duel::daggerSetupMove;return true;
        }
    }
    if(prep.setupMoveUntil && (int32_t)(now-prep.setupMoveUntil)<0 && !prep.playerReady) return true;
    const bool botSafe=IsPlayerBotSafeZone(ch->GetMapIndex(),ch->GetX(),ch->GetY());
    // Class spacing is tactical preference, never a prerequisite for accepting.
    // Inside the shared start area let the player choose their own distance.
    if(botSafe || playerbot_duel::NeedsPreparationApproach(distance)) {
        prep.phase=playerbot_duel::Phase::Approach;
        if(!prep.nextMove || (int32_t)(now-prep.nextMove)>=0) {prep.nextMove=now+playerbot_duel::moveRetry;MovePlayerBotDuelRange(ch,foe,now,botSafe?0:prep.desiredRange);}
        return true;
    }
    ch->Stop();ClearPlayerBotRoute(state,true);ch->SetRotationToXY(foe->GetX(),foe->GetY());
    if(IsPlayerBotSafeZone(ch->GetMapIndex(),ch->GetX(),ch->GetY())) return true;
    if((int32_t)(now-state.dwNextAttackTime)<0) return true;
    if(prep.phase!=playerbot_duel::Phase::WaitReady) {
        prep.phase=playerbot_duel::Phase::Prepare;
        if(CastPlayerBotDuelSelfBuff(ch,state,now)) return true;
        if(prep.stealthPlan==playerbot_duel::StealthPlan::Before && !prep.playerReady && ch->GetJob()==JOB_ASSASSIN && ch->GetSkillGroup()==1 &&
            ch->GetSkillLevel(SKILL_STEALTH)>0 && !IsPlayerBotBuffAffectOn(ch,SKILL_STEALTH) &&
            CanPlayerBotAffordSkill(ch,state,SKILL_STEALTH,now) && PlayerBotUseSkill(ch,state,SKILL_STEALTH,ch,now)) {
            SendPlayerBotSkillPacket(ch,SKILL_STEALTH);
            state.dwNextAttackTime=now+PLAYERBOT_SKILL_ANIMATION_LOCK;
            state.mapBuffActiveUntil[SKILL_STEALTH]=now+PLAYERBOT_BUFF_FALLBACK_DURATION;
            LogPlayerBotDuel(ch,"stealth preparation");return true;
        }
        if(!prep.playerReady && ch->DragonSoul_GetActiveDeck()<0 && IsPlayerBotAlchemyUser(ch) && ch->DragonSoul_IsQualified() && CountPlayerBotWornDs(ch,true)>0) {
            prep.alchemyStarted=ch->DragonSoul_ActivateDeck(DRAGON_SOUL_DECK_0);
        }
        if(PreparePlayerBotDuelItem(ch,prep,now)) return true;
        prep.phase=playerbot_duel::Phase::WaitReady;
        if(!prep.readyAt) {prep.readyAt=now;SendPlayerBotLocalChat(ch,playerbot_duel::ReadyPrompt(number(0,99)));LogPlayerBotDuel(ch,"ready message");}
    }
    if(prep.botChallenger && !prep.reminded && prep.readyAt==now)
        sys_log(0,"PLAYERBOT_DUEL_BB: ready asked pid=%u challenger=%u",pid,prep.challengerPid);
    if(!prep.playerReady) {
        if(now-prep.readyAt>playerbot_duel::readyTimeout) {SendPlayerBotLocalChat(ch,"nvm");CancelPlayerBotPreparation(ch,state,"ready timeout");return false;}
        if(!prep.reminded && now-prep.readyAt>playerbot_duel::readyReminder) {prep.reminded=true;SendPlayerBotLocalChat(ch,"?");}
        return true;
    }
    SwitchOffPlayerBotAutoPotionsForDuel(ch,now);
    if(ch->FindAffect(AFFECT_AUTO_HP_RECOVERY)) return true;
    if(CastPlayerBotDuelSelfBuff(ch,state,now)) return true;
    // Do not carry a queued red potion's healing into the fight. Let it finish.
    if(ch->GetPoint(POINT_HP_RECOVERY)>0 && ch->GetHP()<ch->GetMaxHP()) return true;
    if(ch->GetPoint(POINT_HP_RECOVERY)>0) ch->PointChange(POINT_HP_RECOVERY,-ch->GetPoint(POINT_HP_RECOVERY));
    const DWORD first=SelectPlayerBotDuelSkill(ch,foe,state,now,true);
    const auto saved=prep;
    state.dwTargetVID=foe->GetVID();ch->SetVictim(foe);ch->SetTarget(foe);
    CPVPManager::instance().Insert(ch,foe);
    pair=PlayerBotDuelPair(pid,foe->GetPlayerID());
    if(!pair || !pair->IsFight()) {CancelPlayerBotPreparation(ch,state,"accept refused");return false;}
    playerbot_pvp::NoteDuelStarted(pid,foe->GetPlayerID(),now+PLAYERBOT_PVP_DUEL_ASSUMED);
    auto& active=playerbot_pvp::duels[pid];active.prepared=true;active.alchemyStarted=saved.alchemyStarted;active.openingSkill=first;
    active.stealthOpening=saved.stealthPlan==playerbot_duel::StealthPlan::Opening ||
        (saved.stealthPlan==playerbot_duel::StealthPlan::Before && !IsPlayerBotBuffAffectOn(ch,SKILL_STEALTH));
    foe->SetSyncOwner(NULL); // Release a previous client-less ownership before ordinary hits.
    active.opponentBuff=PlayerBotDuelValuableBuff(foe);active.dispelAt=now;
    active.observedHP=ch->GetHP();active.nextOpponentCheck=now+playerbot_duel::opponentObservation;
    if(ch->IsAffectFlag(AFF_MUYEONG)) ch->StartMuyeongEvent();
    state.bComboMotion=MOTION_COMBO_ATTACK_1;
    if(saved.botChallenger) StartPlayerBotDuelAiChallengerFight(ch,foe,now,active);
    // Accept promptly, but give the first combat action a human reaction delay.
    active.nextDecision=now+number(playerbot_duel::openingReactionMin,playerbot_duel::openingReactionMax);
    active.nextMove=now+1500;state.dwNextSkillCastTime=now;
    playerbot_pvp::Forget(pid);
    LogPlayerBotDuel(ch,"accept; HP potion blocked; SP allowed");
    return ManagePlayerBotPreparedCombat(ch,foe,state,now);
}

bool HandlePlayerBotDuelReady(LPCHARACTER from,const char* text) {
    if(!from || from->IsDead() || !playerbot_duel::ReadyText(text)) return false;
    bool accepted=false;
    for(auto& entry:playerbot_pvp::challenges) {
        auto& prep=entry.second;
        if(prep.challengerPid!=from->GetPlayerID()) continue;
        LPCHARACTER bot=CHARACTER_MANAGER::instance().FindByPID(entry.first);
        if(!bot || bot->IsDead() || bot->GetMapIndex()!=from->GetMapIndex() ||
            DISTANCE_APPROX(bot->GetX()-from->GetX(),bot->GetY()-from->GetY())>playerbot_duel::maxDistance) continue;
        accepted=playerbot_pvp::NoteReady(entry.first,from->GetPlayerID()) || accepted;
        LogPlayerBotDuel(bot,"player ready");
    }
    return accepted;
}
#endif
