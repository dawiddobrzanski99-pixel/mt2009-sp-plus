// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "item.h"
#include "item_manager.h"
#include "locale_service.h"
#include "questmanager.h"

#include "../../common/CommonDefines.h"

#ifdef ENABLE_12ZI

void CHARACTER::ZTT_CHECK_BOX(int color, int index){
	int result_hex[] = {
		0x1,		0x2,		0x4,		0x8,		0x10,		0x20,
		0x40, 		0x80,		0x100,		0x200,		0x400,		0x800,
		0x1000,		0x2000,		0x4000,		0x8000,		0x10000,	0x20000,
		0x40000,	0x80000,	0x100000,	0x200000,	0x400000,	0x800000,
		0x1000000, 	0x2000000,	0x4000000,	0x8000000,	0x10000000,	0x20000000
	};//DO NOT CHANGE.


	int row_count_item 		= 50;
	int row_id_item 		= ZTT_CHECK_ITEM_ROW(color,index);

	int column_count_item 	= 50;
	int column_id_item 		= ZTT_CHECK_ITEM_COLUMN(color,index);

	LPITEM  lp_item_row 	= ITEM_MANAGER::instance().CreateItem(row_id_item, row_count_item, 0, true);
	LPITEM  lp_item_column 	= ITEM_MANAGER::instance().CreateItem(column_id_item, column_count_item, 0, true);

	if ((CountSpecifyItem(column_id_item) < column_count_item) || (CountSpecifyItem(row_id_item) < row_count_item) )
	{
		ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You don't have enough insignia.")); //208
		return;
	}

	RemoveSpecifyItem(column_id_item, column_count_item);
	RemoveSpecifyItem(row_id_item, row_count_item);

	char zodiac_temple_char[1024];
	snprintf(zodiac_temple_char, sizeof(zodiac_temple_char), "12zi_temple.zt_color_%d",color);

	int zodiac_temple_box = GetQuestFlag(zodiac_temple_char);

	SetQuestFlag(zodiac_temple_char,zodiac_temple_box+result_hex[index]);

	ZTT_CHECK_REWARD();

}

void CHARACTER::ZTT_REWARD(int type)
{
	int iEmptyPos;
	int give_reward[] = {33026,33027,33028};

	int check_color_yellow = GetQuestFlag("12zi_temple.zt_color_0");
	int check_color_green = GetQuestFlag("12zi_temple.zt_color_1");

	int yellow_reward_count = GetQuestFlag("12zi_temple.zt_yellowreward_count");
	int green_reward_count = GetQuestFlag("12zi_temple.zt_greenreward_count");

	// ChatPacket(CHAT_TYPE_INFO,"%d %d", check_color_yellow, GetQuestFlag("12zi_temple.zt_can_get_yellowreward")); //debug only

	if ((type == 1) && (GetQuestFlag("12zi_temple.zt_can_get_yellowreward") == 0))
		return;

	if ((type == 2) && (GetQuestFlag("12zi_temple.zt_can_get_greenreward") == 0))
		return;

	if ((type == 3) && ((yellow_reward_count == 0) && (green_reward_count == 0)))
		return;

	LPITEM item = ITEM_MANAGER::instance().CreateItem(give_reward[type-1]);
	iEmptyPos = item->IsDragonSoul() ? GetEmptyDragonSoulInventory(item) : GetEmptyInventory(item->GetSize());
	if (iEmptyPos < 0)
	{
		ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Unfortunately you don't have enough space in your inventory."));
		return;
	}

	if(type == 1)
	{
		SetQuestFlag("12zi_temple.zt_can_get_yellowreward", 0);
		SetQuestFlag("12zi_temple.zt_color_0", 0);
		SetQuestFlag("12zi_temple.zt_yellowreward_count", yellow_reward_count+1);
		AutoGiveItem(give_reward[type-1], 1);
	}
	if(type == 2)
	{
		SetQuestFlag("12zi_temple.zt_can_get_greenreward", 0);
		SetQuestFlag("12zi_temple.zt_color_1", 0);
		SetQuestFlag("12zi_temple.zt_greenreward_count", green_reward_count+1);
		AutoGiveItem(give_reward[type-1], 1);
	}

	if (yellow_reward_count>green_reward_count)
		SetQuestFlag("12zi_temple.zt_goldreward_give", green_reward_count);
	else if (green_reward_count>yellow_reward_count)
		SetQuestFlag("12zi_temple.zt_goldreward_give", yellow_reward_count);
	else if (green_reward_count==yellow_reward_count)
		SetQuestFlag("12zi_temple.zt_goldreward_give", green_reward_count);

	int gold_box_count_give = GetQuestFlag("12zi_temple.zt_goldreward_give");

	if(type == 3)
	{
		SetQuestFlag("12zi_temple.zt_can_get_goldreward", 0);
		SetQuestFlag("12zi_temple.zt_yellowreward_count", yellow_reward_count-gold_box_count_give);
		SetQuestFlag("12zi_temple.zt_greenreward_count", green_reward_count-gold_box_count_give);
		SetQuestFlag("12zi_temple.zt_goldreward_give", 0);
		AutoGiveItem(give_reward[type-1], gold_box_count_give);
	}

	ZTT_LOAD_INFO();
}

void CHARACTER::ZTT_CHECK_REWARD()
{
	int check_color_yellow = GetQuestFlag("12zi_temple.zt_color_0");
	int check_color_green = GetQuestFlag("12zi_temple.zt_color_1");

	int yellow_reward_count = GetQuestFlag("12zi_temple.zt_yellowreward_count");
	int green_reward_count = GetQuestFlag("12zi_temple.zt_greenreward_count");

	if(check_color_yellow == 1073741823)
	{
		SetQuestFlag("12zi_temple.zt_can_get_yellowreward", 1);
	}
	else
	{
		SetQuestFlag("12zi_temple.zt_can_get_yellowreward", 0);
	}

	if(check_color_green == 1073741823)
	{
		SetQuestFlag("12zi_temple.zt_can_get_greenreward", 1);
	}
	else
	{
		SetQuestFlag("12zi_temple.zt_can_get_greenreward", 0);
	}

	if ((yellow_reward_count>=1) && (green_reward_count>=1))
	{
		SetQuestFlag("12zi_temple.zt_can_get_goldreward", 1);
	}
	else
	{
		SetQuestFlag("12zi_temple.zt_can_get_goldreward", 0);
	}
}

void CHARACTER::ZTT_LOAD_INFO(){
	ChatPacket(CHAT_TYPE_COMMAND, "OpenUI12zi 0x%08x 0x%08x %d %d %d", GetQuestFlag("12zi_temple.zt_color_0"), GetQuestFlag("12zi_temple.zt_color_1"), GetQuestFlag("12zi_temple.zt_yellowreward_count"), GetQuestFlag("12zi_temple.zt_greenreward_count"), GetQuestFlag("12zi_temple.zt_can_get_goldreward"));
}

int CHARACTER::ZTT_CHECK_ITEM_ROW(int color, int index){
	int r_item_list[] = {33013, 33014, 33015, 33016, 33017, 33018, 33019, 33020, 33021, 33022};

	if (index >= 0 && index <=5){return r_item_list[0+color];}
	if (index >= 6 && index <=11){return r_item_list[2+color];}
	if (index >= 12 && index <=17){return r_item_list[4+color];}
	if (index >= 18 && index <=23){return r_item_list[6+color];}
	if (index >= 24 && index <=29){return r_item_list[8+color];}
}

int CHARACTER::ZTT_CHECK_ITEM_COLUMN(int color, int index){
	int c_item_list[] = {33001, 33002, 33003, 33004, 33005, 33006, 33007, 33008, 33009, 33010, 33011, 33012};
	
	if (index == 0 || index == 6 || index == 12 || index == 18 || index == 24){return c_item_list[0+color];}
	if (index == 1 || index == 7 || index == 13 || index == 19 || index == 25){return c_item_list[2+color];}
	if (index == 2 || index == 8 || index == 14 || index == 20 || index == 26){return c_item_list[4+color];}
	if (index == 3 || index == 9 || index == 15 || index == 21 || index == 27){return c_item_list[6+color];}
	if (index == 4 || index == 10 || index == 16 || index == 22 || index == 28){return c_item_list[8+color];}
	if (index == 5 || index == 11 || index == 17 || index == 23 || index == 29){return c_item_list[10+color];}
}
#endif // ENABLE_12ZI
