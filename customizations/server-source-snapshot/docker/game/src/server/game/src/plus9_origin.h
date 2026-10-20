#ifndef MT2009_PLUS9_ORIGIN_H
#define MT2009_PLUS9_ORIGIN_H
// MT2009_PLUS9_ORIGIN_V1: immutable instance provenance and per-VNUM person order.
#include <memory>
#include <string>
#include <cstdio>
#include <cstdlib>
#include <map>
#include "packet.h"
#include "cmd.h"
#include "utils.h"
#include "db.h"
#include "char.h"
#include "item.h"
#include "desc.h"

#include <fstream>
#include <cstring>
#include <cstdio>
namespace mt2009_plus9 {
std::unique_ptr<SQLMsg> Query(const std::string& text)
{
    return std::unique_ptr<SQLMsg>(DBManager::instance().DirectQuery("%s", text.c_str()));
}
bool Execute(const std::string& text)
{
    std::unique_ptr<SQLMsg> m = Query(text);
    if (!m.get() || m->uiSQLErrno) { sys_err("PLUS9_ORIGIN: database query failed"); return false; }
    return true;
}
std::string Number(unsigned long long value)
{
    char buf[32]; snprintf(buf, sizeof(buf), "%llu", value); return buf;
}
std::string Hex(const char* value)
{
    static const char digits[] = "0123456789abcdef";
    std::string out;
    for (const unsigned char* p = reinterpret_cast<const unsigned char*>(value); *p; ++p)
    { out += digits[*p >> 4]; out += digits[*p & 15]; }
    return out;
}
bool IsNine(LPITEM item) { return item && item->GetRefineLevel() == 9; }
struct Lock {
    bool held;
    Lock(): held(false) {
        std::unique_ptr<SQLMsg> m = Query("SELECT GET_LOCK('mt2009_plus9_write_v1', 2)");
        if (m.get() && !m->uiSQLErrno && m->Get() && m->Get()->uiNumRows) {
            MYSQL_ROW row=mysql_fetch_row(m->Get()->pSQLResult);
            held=row && row[0] && atoi(row[0]) == 1;
        }
    }
    ~Lock() { if (held) Execute("DO RELEASE_LOCK('mt2009_plus9_write_v1')"); }
};
bool SeedReady()
{
    std::unique_ptr<SQLMsg> m=Query("SELECT state_value FROM player.mt2009_plus9_state WHERE state_key='initial_seed_done'");
    if (!m.get() || m->uiSQLErrno || !m->Get() || !m->Get()->uiNumRows) return false;
    MYSQL_ROW row=mysql_fetch_row(m->Get()->pSQLResult);
    return row && row[0] && atoi(row[0])==1;
}
// MT2009_NASZE_PLUS9_USTAWIENIA_V1: ustawienia ogloszenia z panelu (Kuznia Mocy -> Ulepszanie).
void SebanPlus9Announce(LPCHARACTER ch, LPITEM item, unsigned long ordinal)
{
    bool announce=true; unsigned long first=0;
    std::string text="[Ulepszenie +9] {gracz} ulepszyl {przedmiot} jako {nr}. osoba na serwerze!";
    const char* spool=getenv("M2_RATES_SPOOL");
    std::ifstream f((std::string(spool && *spool ? spool : "/opt/m2spool")+"/systems/plus9/config.txt").c_str());
    std::string key, value;
    while (f >> key >> value) {
        if (key=="announce") announce=value=="1";
        else if (key=="first") first=strtoul(value.c_str(),NULL,10);
        else if (key=="text" && value.size()%2==0 && value.size()<=400) {
            std::string out; bool good=true;
            for (size_t i=0;i<value.size();i+=2){ int v=0; if (sscanf(value.substr(i,2).c_str(),"%2x",&v)!=1 || v<32){good=false;break;} out+=static_cast<char>(v); }
            if (good && !out.empty()) text=out;
        }
    }
    if (!announce || (first && ordinal>first)) return;
    const std::pair<const char*,std::string> fields[3]={{"{gracz}",ch->GetName()},{"{przedmiot}",item->GetName()},{"{nr}",std::to_string(ordinal)}};
    for (const auto& field : fields) for (size_t at; (at=text.find(field.first))!=std::string::npos;) text.replace(at,strlen(field.first),field.second);
    if (text.size()>240) text.resize(240);
    BroadcastNotice(text.c_str());
}
// MT2009_NASZE_PLUS9_USTAWIENIA_V2: glowny wylacznik (czytany przy kazdym +9 i kazdym zapytaniu o nick).
bool SebanPlus9Enabled()
{
    const char* spool=getenv("M2_RATES_SPOOL");
    std::ifstream f((std::string(spool && *spool ? spool : "/opt/m2spool")+"/systems/plus9/config.txt").c_str());
    std::string key, value;
    while (f >> key >> value) if (key=="enabled") return value!="0";
    return true;
}
void Register(LPCHARACTER ch, LPITEM item)
{
    if (!SebanPlus9Enabled()) return; // MT2009_NASZE_PLUS9_USTAWIENIA_V2
    if (!ch || !ch->IsPC() || !IsNine(item) || !item->GetID() || !ch->GetPlayerID()) return;
    Lock lock;
    if (!lock.held || !SeedReady()) { sys_err("PLUS9_ORIGIN: seed/lock not ready item=%u",item->GetID()); return; }
    const std::string id=Number(item->GetID()), v=Number(item->GetVnum()), pid=Number(ch->GetPlayerID());
    if (!Execute("START TRANSACTION")) return;
    bool ok=true;
    unsigned long ordinal=0;
    std::unique_ptr<SQLMsg> existing=Query("SELECT ordinal FROM player.mt2009_plus9_items WHERE item_id="+id);
    if (!existing.get() || existing->uiSQLErrno) ok=false;
    else if (existing->Get() && existing->Get()->uiNumRows) { Execute("COMMIT"); return; }
    std::unique_ptr<SQLMsg> person;
    if (ok) person=Query("SELECT ordinal FROM player.mt2009_plus9_people WHERE vnum="+v+" AND author_pid="+pid);
    if (ok && (!person.get() || person->uiSQLErrno)) ok=false;
    if (ok && person->Get() && person->Get()->uiNumRows) {
        MYSQL_ROW row=mysql_fetch_row(person->Get()->pSQLResult);
        if (row && row[0]) ordinal=strtoul(row[0],NULL,10); else ok=false;
    } else if (ok) {
        ok=Execute("INSERT INTO player.mt2009_plus9_counters (vnum,last_ordinal) VALUES ("+v+",1) ON DUPLICATE KEY UPDATE last_ordinal=last_ordinal+1");
        std::unique_ptr<SQLMsg> counter;
        if(ok) counter=Query("SELECT last_ordinal FROM player.mt2009_plus9_counters WHERE vnum="+v);
        if(ok && (!counter.get() || counter->uiSQLErrno || !counter->Get() || !counter->Get()->uiNumRows)) ok=false;
        if(ok) {
            MYSQL_ROW row=mysql_fetch_row(counter->Get()->pSQLResult);
            if(row && row[0]) ordinal=strtoul(row[0],NULL,10); else ok=false;
        }
        if(ok) ok=Execute("INSERT INTO player.mt2009_plus9_people (vnum,author_pid,ordinal,author_name) VALUES ("+v+","+pid+","+Number(ordinal)+",0x"+Hex(ch->GetName())+")");
    }
    if(ok) ok=Execute("INSERT INTO player.mt2009_plus9_items (item_id,vnum,author_pid,ordinal,author_name,historical_seed) VALUES ("+id+","+v+","+pid+","+Number(ordinal)+",0x"+Hex(ch->GetName())+",0)");
    if(ok) ok=Execute("COMMIT");
    if(!ok) Execute("ROLLBACK");
    else {
        sys_log(0,"PLUS9_ORIGIN: refined pid=%u name=%s item=%u vnum=%u person=%lu",ch->GetPlayerID(),ch->GetName(),item->GetID(),item->GetVnum(),ordinal);
        SebanPlus9Announce(ch,item,ordinal); // MT2009_NASZE_PLUS9_USTAWIENIA_V1
    }
}
void Copy(LPITEM oldItem, LPITEM newItem)
{
    if (!IsNine(oldItem) || !IsNine(newItem) || oldItem->GetVnum()!=newItem->GetVnum()) return;
    Execute("INSERT IGNORE INTO player.mt2009_plus9_items (item_id,vnum,author_pid,ordinal,author_name,historical_seed) SELECT "+Number(newItem->GetID())+",vnum,author_pid,ordinal,author_name,historical_seed FROM player.mt2009_plus9_items WHERE item_id="+Number(oldItem->GetID()));
}
void Reply(LPCHARACTER ch, unsigned int token, DWORD id, DWORD vnum, bool publicShop)
{
    if(!SebanPlus9Enabled()){ch->ChatPacket(CHAT_TYPE_COMMAND,"Plus9Origin %u %u 0 -",token,vnum);return;} // MT2009_NASZE_PLUS9_USTAWIENIA_V2
    std::string sql="SELECT HEX(o.author_name),o.ordinal FROM player.mt2009_plus9_items o";
    if(publicShop) sql+=" JOIN player.item i ON i.id=o.item_id AND i.vnum=o.vnum AND i.window='IKASHOP_OFFLINESHOP'";
    sql+=" WHERE o.item_id="+Number(id)+" AND o.vnum="+Number(vnum);
    std::unique_ptr<SQLMsg> m=Query(sql);
    if(!m.get() || m->uiSQLErrno || !m->Get() || !m->Get()->uiNumRows) {
        ch->ChatPacket(CHAT_TYPE_COMMAND,"Plus9Origin %u %u 0 -",token,vnum); return;
    }
    MYSQL_ROW row=mysql_fetch_row(m->Get()->pSQLResult);
    if(row && row[0] && row[1]) ch->ChatPacket(CHAT_TYPE_COMMAND,"Plus9Origin %u %u %s %s",token,vnum,row[1],row[0]);
}
}

ACMD(do_plus9_origin)
{
    (void)cmd; (void)subcmd;
    if(!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot()) return;
    unsigned int token=0, mode=0, a=0, b=0, vnum=0;
    if(sscanf(argument,"%u %u %u %u %u",&token,&mode,&a,&b,&vnum)!=5) return;
    // Modest per-character rate bound. No client-provided author or ordinal is trusted.
    static std::map<DWORD,std::pair<int,int> > requests;
    std::pair<int,int>& count=requests[ch->GetPlayerID()];
    const int now=get_global_time();
    if(count.first!=now) { count.first=now; count.second=0; }
    if(++count.second>12) return;
    if(mode==0 || mode==2) { // MT2009_PLUS9_LINK_V2
        if(a!=INVENTORY && a!=EQUIPMENT) return;
        if(b>65535) return;
        LPITEM item=ch->GetItem(TItemPos(static_cast<BYTE>(a),static_cast<WORD>(b)));
        if(!mt2009_plus9::IsNine(item) || item->GetVnum()!=vnum) return;
        if(mode==2) {
            ch->ChatPacket(CHAT_TYPE_COMMAND,"Plus9Link %u %u %u",token,vnum,item->GetID());
            return;
        }
        mt2009_plus9::Reply(ch,token,item->GetID(),vnum,false);
    } else if(mode==1) {
        if(!a) return;
        mt2009_plus9::Reply(ch,token,a,vnum,true);
    } else if(mode==3) {
        if(!a) return;
        mt2009_plus9::Reply(ch,token,a,vnum,false);
    }
}
#endif
