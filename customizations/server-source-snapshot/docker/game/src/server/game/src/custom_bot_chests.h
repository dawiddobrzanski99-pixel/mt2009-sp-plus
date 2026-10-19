#ifndef M2_CUSTOM_BOT_CHESTS_V1_H
#define M2_CUSTOM_BOT_CHESTS_V1_H
// CUSTOM_BOT_CHESTS_V1: only our explicitly added boxes, never Cor Draconis.
namespace custom_bot_chests {
inline bool Material(DWORD vnum) {return vnum>=59001 && vnum<=59009;}
// CUSTOM_RECIPE_CHEST_BOTS_V1
inline bool IsBox(DWORD vnum) {return (vnum==59010 || vnum==59011) || Material(vnum) || vnum==27999 || vnum==50033 || vnum==50035 || vnum==50122 || vnum==50124;}
}
#endif

// CUSTOM_UKRAINKA_BOT_CHEST_V1
