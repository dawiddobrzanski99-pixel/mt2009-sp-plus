// COLLECTOR_REFINE_MATERIALS_V1: only called by equipment-refine paths.
namespace {
TSession* RefineSession(LPCHARACTER ch) {
 if(!RealPlayer(ch) || ch->GetDesc()->IsBot())return NULL;
 auto it=s_sessions.find(ch->GetPlayerID());
 if(it==s_sessions.end() || it->second.account!=ch->GetDesc()->GetAccountTable().id || it->second.handle!=ch->GetDesc()->GetHandle())return NULL;
 return &it->second;
}
bool RefineBagItem(LPCHARACTER ch,LPITEM item,LPITEM refined,LPITEM scroll) {
 return item && item!=refined && item!=scroll && !item->IsEquipped() && !item->isLocked() && !item->IsExchanging() && (!ch->GetMyShop() || !ch->GetMyShop()->IsSellingItem(item->GetID()));
}
}
void WarmRefine(LPCHARACTER ch) {
 if(!RealPlayer(ch) || ch->GetDesc()->IsBot() || RefineSession(ch))return;
 PurgeOffline();TSession s;s.account=ch->GetDesc()->GetAccountTable().id;s.handle=ch->GetDesc()->GetHandle();s.nonce=++s_nonce;s.visible=false;s.mapIndex=ch->GetMapIndex();s.x=ch->GetX();s.y=ch->GetY();
 const DWORD pid=ch->GetPlayerID(),handle=s.handle,nonce=s.nonce,account=s.account;s_sessions[pid]=s;
 DBManager::instance().FuncQuery([pid,handle,nonce,account](SQLMsg* msg){TSession* s=NULL;LPCHARACTER ch=Back(pid,handle,nonce,s);if(!ch)return;s->tier=0;s->tierWritable=msg && msg->uiSQLErrno==0;if(s->tierWritable && msg->Get() && msg->Get()->pSQLResult){MYSQL_ROW row=mysql_fetch_row(msg->Get()->pSQLResult);if(row && row[0])str_to_number(s->tier,row[0]);}s->tier=MINMAX(0,s->tier,TIER_COUNT-1);LoadItems(pid,handle,nonce,account);},"SELECT tier FROM player.collector_storage WHERE account_id=%u",account);
}
static bool PayMaterials(LPCHARACTER ch,LPITEM refined,LPITEM scroll,const TRefineTable* recipe) {
 if(!ch || !recipe)return false;
 std::map<DWORD,unsigned long long> needs;
 for(int i=0;i<recipe->material_count;++i)if(recipe->materials[i].count)needs[recipe->materials[i].vnum]+=recipe->materials[i].count;
 struct BagPart {LPITEM item;ITEM_COUNT count;};struct StorePart{DWORD id;ITEM_COUNT count;};
 std::vector<BagPart> bag;std::vector<StorePart> store;TSession* session=RefineSession(ch);
 for(const auto& need:needs){unsigned long long left=need.second;
  for(int cell=0;cell<ch->GetInventoryMaxCount() && left;++cell){LPITEM item=ch->GetInventoryItem(cell);if(!RefineBagItem(ch,item,refined,scroll) || item->GetCell()!=cell || item->GetVnum()!=need.first)continue;ITEM_COUNT count=(ITEM_COUNT)MIN(left,(unsigned long long)item->GetCount());bag.push_back({item,count});left-=count;}
  if(left && (!session || !session->loaded)){WarmRefine(ch);ch->ChatPacket(CHAT_TYPE_INFO,"Wczytywanie Kolekcjonera. Poczekaj chwile i ponow probe ulepszenia.");return false;}
  if(left){for(const auto& entry:session->entries){const TPlayerItem& row=entry.second;if(row.vnum!=need.first || !NoAttrs(row) || ITEM_MANAGER::instance().Find(row.id))continue;ITEM_COUNT count=(ITEM_COUNT)MIN(left,(unsigned long long)row.count);store.push_back({row.id,count});left-=count;if(!left)break;}}
  if(left){ch->ChatPacket(CHAT_TYPE_INFO,LC_TEXT("Not the right material for an upgrade."));return false;}
 }
 // No mutations before the complete recipe has been reserved in this game-thread snapshot.
 if(!store.empty() && !db_clientdesc){ch->ChatPacket(CHAT_TYPE_INFO,"Kolekcjoner chwilowo niedostepny. Materialy nie zostaly zuzyte.");return false;}
 for(const auto& part:store){auto it=session->entries.find(part.id);TPlayerItem& row=it->second;if(part.count>=row.count){DeleteRecord(row.id);session->entries.erase(it);if(session->visible)SendDel(ch,part.id);}else{row.count-=part.count;SaveRecord(row);if(session->visible)SendSet(ch,row);}sys_log(0,"COLLECTOR_REFINE pid=%u account=%u row=%u consumed=%u",ch->GetPlayerID(),session->account,part.id,(unsigned)part.count);}
 for(const auto& part:bag){LPITEM item=part.item;const ITEM_COUNT rest=item->GetCount()-part.count;item->SetCount(rest);if(rest)FlushRow(item);}
 return true;
}

// Read-only recipe counts; actual PayRefine payment is unchanged.
void WarmRefineForRecipe(LPCHARACTER ch,const TRefineTable* recipe) {
 if(!RealPlayer(ch) || ch->GetDesc()->IsBot() || !recipe)return;
 WarmRefine(ch);TSession* session=RefineSession(ch);if(!session)return;
 session->refineVnums.clear();
 for(int i=0;i<recipe->material_count;++i){DWORD vnum=recipe->materials[i].vnum;if(vnum && std::find(session->refineVnums.begin(),session->refineVnums.end(),vnum)==session->refineVnums.end())session->refineVnums.push_back(vnum);}
 if(session->loaded)SendRefineCounts(ch,*session);else ch->ChatPacket(CHAT_TYPE_COMMAND,"COLLREF begin");
}

bool PayRefine(LPCHARACTER ch,LPITEM refined,LPITEM scroll,const TRefineTable* recipe){return refined && PayMaterials(ch,refined,scroll,recipe);}

// BIO_COLLECTOR_V1: same eligibility and payment as refining; bag first.
unsigned long long CountBiologMaterial(LPCHARACTER ch,DWORD vnum){
 if(!RealPlayer(ch) || ch->GetDesc()->IsBot())return ch?ch->CountSpecifyItem(vnum):0;
 unsigned long long count=0;
 for(int cell=0;cell<ch->GetInventoryMaxCount();++cell){LPITEM item=ch->GetInventoryItem(cell);if(RefineBagItem(ch,item,NULL,NULL) && item->GetCell()==cell && item->GetVnum()==vnum)count+=item->GetCount();}
 WarmRefine(ch);TSession* session=RefineSession(ch);
 if(session && session->loaded)for(const auto& entry:session->entries){const TPlayerItem& row=entry.second;if(row.vnum==vnum && NoAttrs(row) && !ITEM_MANAGER::instance().Find(row.id))count+=row.count;}
 return count;
}
bool ConsumeBiologMaterial(LPCHARACTER ch,DWORD vnum,ITEM_COUNT count){
 if(!ch || !count || !ch->CanHandleItem())return false;
 TRefineTable recipe{};recipe.material_count=1;recipe.materials[0].vnum=vnum;recipe.materials[0].count=count;
 return PayMaterials(ch,NULL,NULL,&recipe);
}
