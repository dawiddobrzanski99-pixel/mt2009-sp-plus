// MT2009_PLUS_QUEST_REWARD_OVERRIDES_V1: the quests' rewards as the Seban
// panel's "Questy" part changed them (playerbot_quest_rewards.h has the
// whole story and the rule file's format; server-patches/questrewards the
// calls into the quests' Lua functions).
#include "stdafx.h"
#include "config.h"
#include "char.h"
#include "item.h"
#include "item_manager.h"
#include "affect.h"
#include "questmanager.h"
#include "questpc.h"
#include "db.h"
#include "log.h"
#include "../../common/length.h"
#include "playerbot_quest_rewards.h"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace mt2009_quest_rewards
{
	namespace
	{
		const long long GOLD_CAP = 2000000000LL;     // one call's yang
		const long long EXP_CAP = 2000000000LL;      // one call's experience (a DWORD in the engine)
		const long long COUNT_CAP = 10000;           // pieces of one item a rule gives
		const int STACK_ROUNDS_CAP = 200;            // AutoGiveItem calls for one rule
		const long BONUS_CAP = 1000000;
		const char* RULE_FILE = "reward_overrides.txt";

		struct NumRule
		{
			bool mul = true;
			double factor = 1.0;
			long long value = 0;
		};

		struct ItemRule
		{
			DWORD vnum = 0;
			long long count = 0;
		};

		struct BonusRule
		{
			int point = 0;
			long value = 0;
		};

		struct Extra
		{
			std::string kind;
			long long a = 0;
			long long b = 0;
		};

		struct QuestRules
		{
			std::map<DWORD, ItemRule> items;
			std::map<long long, NumRule> gold;
			bool goldAll = false;
			NumRule goldAny;
			std::map<long long, NumRule> exp;
			bool expAll = false;
			NumRule expAny;
			std::map<std::pair<int, long>, BonusRule> bonus;
			std::map<int, BonusRule> bonusAny;
			std::map<std::string, std::vector<Extra>> extras;
		};

		std::unordered_map<std::string, QuestRules> g_rules;
		bool g_loaded = false;
		unsigned int g_count = 0;

		bool ToInt(const std::string& s, long long& out)
		{
			if (s.empty() || s.size() > 19)
				return false;
			char* end = NULL;
			out = std::strtoll(s.c_str(), &end, 10);
			return end && *end == '\0';
		}

		bool ToNum(const std::string& s, double& out)
		{
			if (s.empty() || s.size() > 24)
				return false;
			char* end = NULL;
			out = std::strtod(s.c_str(), &end);
			return end && *end == '\0' && std::isfinite(out);
		}

		bool ParseNumRule(const std::string& mode, const std::string& value, NumRule& rule)
		{
			if (mode == "mul")
			{
				rule.mul = true;
				return ToNum(value, rule.factor) && rule.factor >= 0.0 && rule.factor <= 1000.0;
			}
			if (mode == "set")
			{
				rule.mul = false;
				return ToInt(value, rule.value) && rule.value >= 0 && rule.value <= GOLD_CAP;
			}
			return false;
		}

		bool ParseLine(const std::vector<std::string>& t)
		{
			if (t.size() < 2 || t[1].empty() || t[1].size() > 64)
				return false;
			QuestRules& q = g_rules[t[1]];
			long long a = 0, b = 0, c = 0;
			if (t[0] == "item" && t.size() >= 5)
			{
				if (!ToInt(t[2], a) || !ToInt(t[3], b) || !ToInt(t[4], c) || a <= 0 || b < 0 || c < 0 || c > COUNT_CAP)
					return false;
				ItemRule& r = q.items[(DWORD) a];
				r.vnum = (DWORD) b;
				r.count = c;
				return true;
			}
			if ((t[0] == "gold" || t[0] == "exp") && t.size() >= 5)
			{
				NumRule rule;
				if (!ParseNumRule(t[3], t[4], rule))
					return false;
				const bool gold = t[0] == "gold";
				if (t[2] == "*")
				{
					(gold ? q.goldAll : q.expAll) = true;
					(gold ? q.goldAny : q.expAny) = rule;
					return true;
				}
				if (!ToInt(t[2], a) || a <= 0)
					return false;
				(gold ? q.gold : q.exp)[a] = rule;
				return true;
			}
			if (t[0] == "bonus" && t.size() >= 6)
			{
				if (!ToInt(t[2], a) || a <= 0 || a >= POINT_MAX_NUM || !ToInt(t[4], b) || b < 0 || b >= POINT_MAX_NUM
						|| !ToInt(t[5], c) || c < -BONUS_CAP || c > BONUS_CAP)
					return false;
				BonusRule rule;
				rule.point = (int) b;
				rule.value = (long) c;
				if (t[3] == "*")
				{
					q.bonusAny[(int) a] = rule;
					return true;
				}
				long long v = 0;
				if (!ToInt(t[3], v))
					return false;
				q.bonus[std::make_pair((int) a, (long) v)] = rule;
				return true;
			}
			if (t[0] == "extra" && t.size() >= 6)
			{
				Extra e;
				e.kind = t[3];
				if (t[2].empty() || t[2].size() > 80 || !ToInt(t[4], e.a) || !ToInt(t[5], e.b))
					return false;
				if (e.kind == "item")
				{
					if (e.a <= 0 || e.b <= 0 || e.b > COUNT_CAP)
						return false;
				}
				else if (e.kind == "gold" || e.kind == "exp")
				{
					if (e.a <= 0 || e.a > GOLD_CAP)
						return false;
				}
				else if (e.kind == "bonus")
				{
					if (e.a <= 0 || e.a >= POINT_MAX_NUM || e.b < -BONUS_CAP || e.b > BONUS_CAP)
						return false;
				}
				else
					return false;
				q.extras[t[2]].push_back(e);
				return true;
			}
			return false;
		}

		void Load()
		{
			if (g_loaded)
				return;
			g_loaded = true;
			const std::string path = g_stQuestDir + "/" + RULE_FILE;
			std::ifstream in(path.c_str());
			if (!in.is_open())
			{
				sys_log(0, "QUEST_REWARD_OVERRIDE no %s - every quest gives its own rewards", path.c_str());
				return;
			}
			std::string line;
			int number = 0, bad = 0;
			while (std::getline(in, line) && number < 20000)
			{
				++number;
				if (!line.empty() && line[line.size() - 1] == '\r')
					line.erase(line.size() - 1);
				const size_t hash = line.find('#');
				if (hash != std::string::npos)
					line.erase(hash);
				std::vector<std::string> tokens;
				std::istringstream ss(line);
				std::string token;
				while (ss >> token)
					tokens.push_back(token);
				if (tokens.empty())
					continue;
				if (ParseLine(tokens))
					++g_count;
				else
				{
					++bad;
					sys_err("QUEST_REWARD_OVERRIDE %s:%d not understood - the line is left out", path.c_str(), number);
				}
			}
			// a quest whose every line failed leaves an empty entry: harmless, but drop it
			for (auto it = g_rules.begin(); it != g_rules.end();)
			{
				const QuestRules& q = it->second;
				if (q.items.empty() && q.gold.empty() && !q.goldAll && q.exp.empty() && !q.expAll && q.bonus.empty()
						&& q.bonusAny.empty() && q.extras.empty())
					it = g_rules.erase(it);
				else
					++it;
			}
			sys_log(0, "QUEST_REWARD_OVERRIDE %u rule(s) for %u quest(s) from %s (%d line(s) left out)",
					g_count, (unsigned int) g_rules.size(), path.c_str(), bad);
		}

		const std::string& CurrentQuest()
		{
			static const std::string empty;
			quest::PC* pc = quest::CQuestManager::instance().GetCurrentPC();
			return pc ? pc->GetCurrentQuestName() : empty;
		}

		QuestRules* Find(const std::string& quest)
		{
			Load();
			if (g_rules.empty() || quest.empty())
				return NULL;
			auto it = g_rules.find(quest);
			return it == g_rules.end() ? NULL : &it->second;
		}

		long long Apply(const NumRule& rule, long long amount, long long cap)
		{
			long long v = rule.mul ? (long long) std::llround((double) amount * rule.factor) : rule.value;
			if (v < 0)
				v = 0;
			if (v > cap)
				v = cap;
			return v;
		}

		// count pieces of vnum, a stack at a time; the first item's id in first_id
		void GiveItems(LPCHARACTER ch, DWORD vnum, long long count, DWORD* first_id)
		{
			TItemTable* table = ITEM_MANAGER::instance().GetTable(vnum);
			if (!table)
			{
				sys_err("QUEST_REWARD_OVERRIDE no item %u on this server - nothing given", vnum);
				return;
			}
			long long stack = 1;
			if (table->dwFlags & ITEM_FLAG_STACKABLE)
				stack = table->dwMaxStack > 0 ? (long long) table->dwMaxStack : (long long) ITEM_MAX_COUNT;
			if (count > COUNT_CAP)
				count = COUNT_CAP;
			for (int round = 0; count > 0 && round < STACK_ROUNDS_CAP; ++round)
			{
				const long long n = count < stack ? count : stack;
				LPITEM item = ch->AutoGiveItem(vnum, (ITEM_COUNT) n);
				if (item && first_id && !*first_id)
					*first_id = item->GetID();
				count -= n;
			}
		}

		void AddCollect(LPCHARACTER ch, BYTE point, long value)
		{
			CAffect* aff = ch->FindAffect(AFFECT_COLLECT, point);
			if (aff)
				value += aff->lApplyValue;
			ch->AddAffect(AFFECT_COLLECT, point, value, 0, INFINITE_AFFECT_DURATION, 0, true, true);
		}

		void FireExtras(LPCHARACTER ch, const std::string& quest, QuestRules& q, const std::string& anchor)
		{
			auto it = q.extras.find(anchor);
			if (it == q.extras.end() || !ch)
				return;
			for (const Extra& e : it->second)
			{
				if (e.kind == "item")
				{
					GiveItems(ch, (DWORD) e.a, e.b, NULL);
					LogManager::instance().QuestRewardLog(quest.c_str(), ch->GetPlayerID(), ch->GetLevel(), e.a, (int) e.b, QUEST_LOG_ITEM);
				}
				else if (e.kind == "gold")
				{
					ch->ChangeGold((YANG) e.a);
					DBManager::instance().SendMoneyLog(MONEY_LOG_QUEST, ch->GetPlayerID(), e.a);
					LogManager::instance().QuestRewardLog(quest.c_str(), ch->GetPlayerID(), ch->GetLevel(), e.a, 0, QUEST_LOG_GOLD);
				}
				else if (e.kind == "exp")
				{
					ch->PointChange(POINT_EXP, (int) e.a);
					LogManager::instance().QuestRewardLog(quest.c_str(), ch->GetPlayerID(), ch->GetLevel(), e.a, 0, QUEST_LOG_EXP);
				}
				else if (e.kind == "bonus")
					AddCollect(ch, (BYTE) e.a, (long) e.b);
				sys_log(0, "QUEST_REWARD_OVERRIDE %s: extra %s %lld/%lld (%s) for %s", quest.c_str(), e.kind.c_str(),
						e.a, e.b, anchor.c_str(), ch->GetName());
			}
		}
	}

	int OnItem(LPCHARACTER ch, DWORD& vnum, int& count, DWORD& given_id)
	{
		given_id = 0;
		const std::string& quest = CurrentQuest();
		QuestRules* q = ch ? Find(quest) : NULL;
		if (!q)
			return ITEM_PROCEED;
		const DWORD orig = vnum;
		const int orig_count = count;
		int action = ITEM_PROCEED;
		auto it = q->items.find(orig);
		if (it != q->items.end())
		{
			const ItemRule& rule = it->second;
			if (rule.vnum == 0)
			{
				action = ITEM_SKIP;
				sys_log(0, "QUEST_REWARD_OVERRIDE %s: item %u x%d not given (%s)", quest.c_str(), orig, orig_count, ch->GetName());
			}
			else if (!ITEM_MANAGER::instance().GetTable(rule.vnum))
				sys_err("QUEST_REWARD_OVERRIDE %s: no item %u on this server - the quest's own %u stays", quest.c_str(), rule.vnum, orig);
			else
			{
				const long long want = rule.count > 0 ? rule.count : (long long) orig_count;
				TItemTable* table = ITEM_MANAGER::instance().GetTable(rule.vnum);
				long long stack = 1;
				if (table->dwFlags & ITEM_FLAG_STACKABLE)
					stack = table->dwMaxStack > 0 ? (long long) table->dwMaxStack : (long long) ITEM_MAX_COUNT;
				vnum = rule.vnum;
				if (want > stack)
				{
					GiveItems(ch, vnum, want, &given_id);
					action = ITEM_GIVEN;
				}
				else
					count = (int) want;
				sys_log(0, "QUEST_REWARD_OVERRIDE %s: item %u x%d -> %u x%lld (%s)", quest.c_str(), orig, orig_count, vnum, want,
						ch->GetName());
			}
		}
		FireExtras(ch, quest, *q, "item:" + std::to_string(orig));
		return action;
	}

	bool OnGold(LPCHARACTER ch, YANG& amount)
	{
		if (amount <= 0 || !ch)
			return true;
		const std::string& quest = CurrentQuest();
		QuestRules* q = Find(quest);
		if (!q)
			return true;
		const YANG orig = amount;
		auto it = q->gold.find((long long) orig);
		const NumRule* rule = it != q->gold.end() ? &it->second : (q->goldAll ? &q->goldAny : NULL);
		if (rule)
		{
			amount = (YANG) Apply(*rule, (long long) orig, GOLD_CAP);
			sys_log(0, "QUEST_REWARD_OVERRIDE %s: yang %lld -> %lld (%s)", quest.c_str(), (long long) orig, (long long) amount,
					ch->GetName());
		}
		FireExtras(ch, quest, *q, "gold:*");
		return amount > 0;
	}

	bool OnExp(LPCHARACTER ch, DWORD& amount)
	{
		if (amount == 0 || !ch)
			return true;
		const std::string& quest = CurrentQuest();
		QuestRules* q = Find(quest);
		if (!q)
			return true;
		const DWORD orig = amount;
		auto it = q->exp.find((long long) orig);
		const NumRule* rule = it != q->exp.end() ? &it->second : (q->expAll ? &q->expAny : NULL);
		if (rule)
		{
			amount = (DWORD) Apply(*rule, (long long) orig, EXP_CAP);
			sys_log(0, "QUEST_REWARD_OVERRIDE %s: exp %u -> %u (%s)", quest.c_str(), orig, amount, ch->GetName());
		}
		FireExtras(ch, quest, *q, "exp:*");
		return amount > 0;
	}

	bool OnBonus(LPCHARACTER ch, BYTE& point, long& value)
	{
		if (!ch)
			return true;
		const std::string& quest = CurrentQuest();
		QuestRules* q = Find(quest);
		if (!q)
			return true;
		const BYTE orig_point = point;
		const long orig_value = value;
		bool give = true;
		auto it = q->bonus.find(std::make_pair((int) orig_point, orig_value));
		const BonusRule* rule = it != q->bonus.end() ? &it->second : NULL;
		if (!rule)
		{
			auto any = q->bonusAny.find((int) orig_point);
			if (any != q->bonusAny.end())
				rule = &any->second;
		}
		if (rule)
		{
			if (rule->point <= 0)
				give = false;
			else
			{
				point = (BYTE) rule->point;
				value = rule->value;
			}
			sys_log(0, "QUEST_REWARD_OVERRIDE %s: bonus %d %ld -> %d %ld (%s)", quest.c_str(), (int) orig_point, orig_value,
					give ? (int) point : 0, give ? value : 0L, ch->GetName());
		}
		FireExtras(ch, quest, *q, "bonus:" + std::to_string((int) orig_point) + ":" + std::to_string(orig_value));
		return give;
	}

	void OnState(LPCHARACTER ch, const std::string& quest, const std::string& state)
	{
		if (!ch)
			return;
		QuestRules* q = Find(quest);
		if (q)
			FireExtras(ch, quest, *q, "state:" + state);
	}

	unsigned int RuleCount()
	{
		Load();
		return g_count;
	}
}

#include "quest_bonus_preview_impl.h"
#include "mission_panel_impl.h" // QUEST_BONUS_PREVIEW_V1
