#pragma once
// MT2009_PLUS_QUEST_REWARD_OVERRIDES_V1: the quests' rewards as the Seban
// panel's "Questy" part (dbeditor/quests.py) changed them - without touching a
// compiled quest.
//
// The quests give their rewards through a handful of Lua functions
// (questlua_pc.cpp, questlua_affect.cpp); server-patches/questrewards puts one
// call of this file at the top of each, after the function has read its
// arguments:
//
//   pc.give_item2 / pc.give_item       OnItem   (vnum, count)
//   pc.change_money / changemoney /
//   change_gold / pc.give_gold         OnGold   (amount > 0 only: a cost stays a cost)
//   pc.give_exp2 / pc.give_exp /
//   pc.give_exp_perc                   OnExp    (the amount the call gives)
//   affect.add_collect                 OnBonus  (POINT_* type, value) - the
//                                      Biologist's permanent bonuses
//   set_state / setstate               OnState  (only extras)
//
// Which quest is calling: CQuestManager's current PC (the quest whose script
// runs). Which reward: the call's ORIGINAL arguments - "item 50109 of
// collect_quest_lv30", "bonus POINT_MOV_SPEED 10 of collect_quest_lv30" - so
// the same reward is the same rule wherever the quest gives it, and the rule
// does not depend on a state name the script may have changed a line earlier
// (the Biologist does set_state(__complete) before its rewards).
//
// The rules: <quest dir>/reward_overrides.txt, written by the game's
// m2-quests before the cores boot from the panel's spool file
// (quests/quests.custom.txt), read once by each core at its first reward.
// One rule a line, tab separated, "#" a comment:
//
//   item   <quest> <vnum>        <new vnum|0 = nothing> <count|0 = the call's>
//   gold   <quest> <amount|*>    mul|set <value>
//   exp    <quest> <amount|*>    mul|set <value>
//   bonus  <quest> <point> <value|*>  <new point|0 = no bonus> <new value>
//   extra  <quest> <anchor> item|gold|exp|bonus <a> <b>
//
// An extra is given each time its anchor happens in that quest, right where
// it happens: item:<vnum>, bonus:<point>:<value>, gold:*, exp:* (the call with
// those original arguments) or state:<name> (set_state to that state). a/b:
// item vnum/count, gold amount/0, exp amount/0, bonus point/value. Every
// change is logged (syslog, "QUEST_REWARD_OVERRIDE").
//
// Only rewards given after the restart change - a bonus the Biologist already
// gave stays as it was (affect.add_collect sums every call into one affect per
// POINT type, so there is nothing to recompute it from).
// Included after the engine's own headers (DWORD, BYTE, YANG, LPCHARACTER).
#include <string>

namespace mt2009_quest_rewards
{
	enum EItemAction
	{
		ITEM_SKIP = 0,     // give nothing: the caller returns as if nothing was given
		ITEM_PROCEED = 1,  // the caller goes on with vnum/count (maybe changed)
		ITEM_GIVEN = 2,    // given here (more than one stack); given_id = the first item's id
	};

	int OnItem(LPCHARACTER ch, DWORD& vnum, int& count, DWORD& given_id);
	// false: give nothing (the caller returns)
	bool OnGold(LPCHARACTER ch, YANG& amount);
	bool OnExp(LPCHARACTER ch, DWORD& amount);
	bool OnBonus(LPCHARACTER ch, BYTE& point, long& value);
	void OnState(LPCHARACTER ch, const std::string& quest, const std::string& state);
	unsigned int RuleCount();
}
