#ifndef CUSTOM_MAP_COUNTERS_H
#define CUSTOM_MAP_COUNTERS_H
// CUSTOM_MAP_COUNTERS_V1: live entities on the exact map/channel, cached per core.
#include "char.h"
#include "desc.h"
#include "guild.h"
#include "sectree_manager.h"
#include "utils.h"
#include <map>

namespace custom_map_counters
{
struct Totals
{
    unsigned bosses = 0, stones = 0;
    std::map<DWORD, unsigned> guildMembers;
    void operator()(LPENTITY entity)
    {
        if (!entity || !entity->IsType(ENTITY_CHARACTER)) return;
        LPCHARACTER member = static_cast<LPCHARACTER>(entity);
        if (member->IsPC())
        {
            // Present online members, including the viewer and guild bots; dead PCs remain members.
            if (member->GetDesc() && member->GetGuild())
                ++guildMembers[member->GetGuild()->GetID()];
            return;
        }
        if (member->IsDead() || member->GetHP() <= 0) return;
        if (member->IsStone()) ++stones;
        else if (member->IsMonster() && member->GetMobRank() >= MOB_RANK_BOSS) ++bosses;
    }
};
struct Cache
{
    Totals totals;
    DWORD refreshed = 0, accessed = 0;
    bool valid = false;
};
inline void Send(LPCHARACTER viewer)
{
    if (!viewer || !viewer->IsPC() || !viewer->GetDesc() || viewer->GetDesc()->IsBot()) return;
    static std::map<long, Cache> caches;
    static DWORD lastCleanup = 0;
    const DWORD now = get_dword_time();
    if ((DWORD)(now - lastCleanup) >= 60000)
    {
        for (std::map<long, Cache>::iterator it = caches.begin(); it != caches.end();)
            if ((DWORD)(now - it->second.accessed) >= 60000) it = caches.erase(it);
            else ++it;
        lastCleanup = now;
    }
    const long mapIndex = viewer->GetMapIndex();
    LPSECTREE_MAP map = SECTREE_MANAGER::instance().GetMap(mapIndex);
    if (!map)
    {
        caches.erase(mapIndex);
        viewer->ChatPacket(CHAT_TYPE_COMMAND, "MapCounters %ld 0 0 0", mapIndex);
        return;
    }
    Cache& cache = caches[mapIndex];
    cache.accessed = now;
    if (!cache.valid || (DWORD)(now - cache.refreshed) >= 5000)
    {
        cache.totals = Totals();
        map->for_each(cache.totals);
        cache.refreshed = now;
        cache.valid = true;
    }
    unsigned members = 0;
    if (viewer->GetGuild())
    {
        const DWORD gid = viewer->GetGuild()->GetID();
        std::map<DWORD, unsigned>::const_iterator found = cache.totals.guildMembers.find(gid);
        if (found != cache.totals.guildMembers.end()) members = found->second;
    }
    viewer->ChatPacket(CHAT_TYPE_COMMAND, "MapCounters %ld %u %u %u", mapIndex,
                       cache.totals.bosses, cache.totals.stones, members);
}
}
#endif
