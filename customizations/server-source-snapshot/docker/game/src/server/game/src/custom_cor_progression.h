#pragma once
// CUSTOM_COR_PROGRESSION_V2: approved order and fixed rare-Cor chance.
namespace custom_cor {
struct Rule{DWORD vnum;double chance;int min,max;};
inline long BaseMap(long map){return map>=10000?map/10000:map;}
inline bool Match(DWORD race,long map,DWORD boss,long expected){return race==boss && (!map || BaseMap(map)==expected);}
inline bool Zodiac(DWORD race,long map){return race>=2752 && race<=2862 && (race-2752)%10==0 && (!map || BaseMap(map)==358);}
inline int WorldStage(DWORD race,long map,bool boss){
 const DWORD known[][5]={{691,692,693,0,0},{1901,1902,1903,0,0},{2191,2192,0,0,0},{2091,2092,2094,0,0},{2381,0,0,0,0},{2382,2306,2307,0,0},{1192,2491,2492,2495,0}};
 int stage=-1;long base=BaseMap(map);
 if(base==64)stage=0;else if(base==61)stage=1;else if(base==63)stage=2;else if(base==104 || base==71)stage=3;else if(base==67)stage=4;else if(base==68)stage=5;else if(base==72 || base==73)stage=6;
 if(stage>=0){if(boss)return stage;for(DWORD v:known[stage])if(v && v==race)return stage;return -1;}
 if(!map)for(int i=0;i<7;++i)for(DWORD v:known[i])if(v && v==race)return i;
 return -1;
}
inline std::vector<Rule> CustomOriginalRules(bool stone,int level,DWORD race,long map=0,bool worldBoss=false){
 std::vector<Rule> result;
 if(stone && level>=60){int step=(level-60)/10;result.push_back({50256,static_cast<double>(std::min(100,5+step*5)),std::min(5,1+step),5});}
 if(stone)return result;
 const DWORD bosses[]={1093,2598,6191,4559,2493,9714};const long maps[]={66,216,352,158,208,366};
 for(int i=0;i<6;++i)if(Match(race,map,bosses[i],maps[i]))result.push_back({50259,5.0+i*5,1+i,4+i});
 if(Zodiac(race,map))result.push_back({50259,35,7,10});
 const DWORD ancientBosses[]={9682,6091,9694,1093,2598,6191,4559,2493,9714};const long ancientMaps[]={364,351,365,66,216,352,158,208,366};
 for(int i=0;i<9;++i)if(Match(race,map,ancientBosses[i],ancientMaps[i]))result.push_back({50258,8.0+i*5,1+i,4+i});
 if(Zodiac(race,map))result.push_back({50258,53,10,13});
 const DWORD rareBosses[]={6091,9694,2598,6191,4559,2493,9714};const long rareMaps[]={351,365,216,352,158,208,366};
 for(int i=0;i<7;++i)if(Match(race,map,rareBosses[i],rareMaps[i]))result.push_back({50257,25,2+i,10});
 if(Zodiac(race,map))result.push_back({50257,25,9,10});
 int world=WorldStage(race,map,worldBoss);
 if(world>=0){result.push_back({50257,2.5+world,1+world,4+world});if(world>=1)result.push_back({50258,2.5+(world-1),world,3+world});if(world>=5)result.push_back({50259,2.5+(world-5),world-4,world-2});}
 return result;
}
inline bool CustomOriginalTargeted(DWORD v,const std::vector<Rule>& rules){for(const auto& r:rules)if(r.vnum==v)return true;return false;}
}


// CUSTOM_SUPPLEMENT_AND_BLESSING_DROP_V2
namespace custom_supplement_policy
{
    inline bool DungeonMap(long map)
    {
        switch (map) {
            case 363: case 66: case 364: case 351: case 365:
            case 216: case 352: case 158: case 208: case 366: case 358:
                return true;
            default: return false;
        }
    }

    inline bool Match(unsigned race,long map,unsigned wanted,long dungeon)
    {
        return race==wanted && (map==dungeon || map==0);
    }

    inline bool FinalBoss(unsigned race,long map)
    {
        if (Match(race,map,9706,363)) return true;
        if (Match(race,map,1093,66)) return true;
        if (Match(race,map,9682,364)) return true;
        if (Match(race,map,6091,351)) return true;
        if (Match(race,map,9694,365)) return true;
        if (Match(race,map,2598,216)) return true;
        if (Match(race,map,6191,352)) return true;
        if (Match(race,map,4559,158)) return true;
        if (Match(race,map,2493,208)) return true;
        if (Match(race,map,9714,366)) return true;
        return (map==358 || map==0) &&
            race>=2752 && race<=2862 && (race-2752)%10==0;
    }

    inline double BlessingChance(unsigned race,long map)
    {
        if (Match(race,map,6091,351)) return 1.0;
        if (Match(race,map,9694,365)) return 3.0;
        if (Match(race,map,2598,216)) return 5.0;
        if (Match(race,map,6191,352)) return 7.0;
        if (Match(race,map,4559,158)) return 9.0;
        if (Match(race,map,2493,208)) return 11.0;
        if (Match(race,map,9714,366)) return 13.0;
        return 0.0;
    }
}

namespace custom_cor
{
    template<typename A,typename B,typename C,typename D,typename E>
    inline auto Rules(A stone,B level,C raceArg,D mapArg,E boss)
        -> decltype(CustomOriginalRules(stone,level,raceArg,mapArg,boss))
    {
        auto result=CustomOriginalRules(stone,level,raceArg,mapArg,boss);
        if (stone) return result;

        const unsigned race=static_cast<unsigned>(raceArg);
        const long rawMap=static_cast<long>(mapArg);
        const long map=rawMap>=10000 ? rawMap/10000 : rawMap;
        const bool finalBoss=custom_supplement_policy::FinalBoss(race,map);

        if (!finalBoss &&
            (!boss || custom_supplement_policy::DungeonMap(map) || rawMap>=10000))
            return result;

        const unsigned ids[]={72064,72065,72066,72067};
        const double worldChance[]={2.5,2.0,1.5,1.0};
        const double dungeonChance[]={10.0,7.0,5.0,1.2};

        for (int i=0;i<4;++i) {
            typename decltype(result)::value_type rule={};
            rule.vnum=ids[i];
            rule.min=1;
            rule.max=finalBoss ? 3 : 1;
            rule.chance=finalBoss ? dungeonChance[i] : worldChance[i];
            result.push_back(rule);
        }

        const double blessing=custom_supplement_policy::BlessingChance(race,map);
        if (finalBoss && blessing>0.0) {
            typename decltype(result)::value_type rule={};
            rule.vnum=71052;
            rule.min=1;
            rule.max=1;
            rule.chance=blessing;
            result.push_back(rule);
        }
        return result;
    }

    template<typename V,typename R>
    inline bool Targeted(V vnum,const R& rules)
    {
        if (CustomOriginalTargeted(vnum,rules)) return true;
        const unsigned v=static_cast<unsigned>(vnum);
        if (v!=71052 && (v<72064 || v>72067)) return false;
        for (const auto& rule:rules)
            if (static_cast<unsigned>(rule.vnum)==v) return true;
        return false;
    }
}
