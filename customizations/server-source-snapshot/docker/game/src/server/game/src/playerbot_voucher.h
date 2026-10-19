#pragma once
// MT2009_PLUS_VOUCHER_CODES_V1: kody promocyjne (the owner, 6 October). Universal
// codes "MT2009-PLUS-XXXX" built into the server package, so they work offline:
//
//   /kod <kod>          (alias /voucher; case, spaces and dashes do not matter)
//
// and the same in the ItemShop's "Wykorzystaj voucher" tab (VoucherItemShopCode below): one
// of our codes is answered there with the window's USE_VOUCHER_* reply, any other code goes
// on to the db core's cash vouchers as before.
//
// - The codes are not in the package in plain text: common.mt2009_voucher keeps
//   SHA2(CONCAT(salt, normalized code), 256) and the reward rows (apply.sh; the
//   salt and the normalization are playerbot_voucher_rules.h). The command
//   normalizes what was typed and lets MariaDB hash it - nothing but [A-Z0-9]
//   reaches the query.
// - Once per ACCOUNT: player.mt2009_voucher_used (account_id, code_hash). The
//   row is written first (INSERT IGNORE, its primary key), so two characters of
//   one account on two cores can never both take a reward; the items follow.
// - The items: to the inventory; one that does not fit goes to the ItemShop
//   storage (player.item_award, mall=1 - the same delivery as an ItemShop
//   purchase, "Magazyn ItemShop"), and only if even that write fails, at the
//   character's feet with its ownership (AutoGiveItem).
// - 5 tries a minute per character (each try, right or wrong); bots never.
// - The Seban panel's "Kody bonusowe (vouchery)" (Gra i serwer, #kody-bonusowe) switches
//   them off: event flag m2_vouchers_off, read live (SwitchedOff); one of our codes is
//   then refused with "Kody bonusowe sa wylaczone na tym serwerze." (the cash vouchers
//   of the ItemShop tab are not ours and go on as before).
// - Every redemption is logged (syslog "VOUCHER:"); the used rows are the
//   history (account, character, time).
// Engine side: server-patches/playerqol (cmd.cpp table "kod" / "voucher", itemshop_manager.cpp).

#include "playerbot_voucher_rules.h"

namespace mt2009_voucher
{
	const int TRIES_PER_MINUTE = 5;

	struct TTries
	{
		DWORD windowStart;	// get_dword_time() of the window's first try
		int count;
	};
	std::map<DWORD, TTries> s_mapTries;

	// true: this try is over the limit (not counted again).
	bool OverLimit(DWORD pid)
	{
		const DWORD now = get_dword_time();
		if (s_mapTries.size() > 4096)
			s_mapTries.clear();
		TTries& t = s_mapTries[pid];
		if (!t.count || now - t.windowStart >= 60000)
		{
			t.windowStart = now;
			t.count = 0;
		}
		if (t.count >= TRIES_PER_MINUTE)
			return true;
		++t.count;
		return false;
	}

	bool QueryOk(const std::unique_ptr<SQLMsg>& msg)
	{
		return msg.get() && msg->uiSQLErrno == 0 && msg->Get();
	}

	struct TReward
	{
		DWORD vnum;
		DWORD count;
	};

	const char* ItemName(DWORD vnum)
	{
		const TItemTable* t = ITEM_MANAGER::instance().GetTable(vnum);
		return t ? t->szLocaleName : "?";
	}

	// One reward item: the inventory, else the ItemShop storage, else the floor.
	// `where` gets " (Magazyn ItemShop)" for the storage.
	void GiveOne(LPCHARACTER ch, const TReward& r, const char*& where)
	{
		where = "";
		LPITEM item = ITEM_MANAGER::instance().CreateItem(r.vnum, (ITEM_COUNT) r.count, 0, true);
		if (item)
		{
			const int cell = ch->GetEmptyInventoryEx(item);
			if (cell != -1)
			{
				item->AddToCharacter(ch, TItemPos(item->GetWindowInventoryEx(), cell));
				LogManager::instance().ItemLog(ch, item, "VOUCHER", item->GetName());
				return;
			}
			M2_DESTROY_ITEM(item);
		}
		else
		{
			sys_err("VOUCHER: cannot create item %u x%u for %s", r.vnum, r.count, ch->GetName());
		}

		const char* login = ch->GetDesc()->GetAccountTable().login;
		char escLogin[LOGIN_MAX_LEN * 2 + 1];
		DBManager::instance().EscapeString(escLogin, sizeof(escLogin), login, strlen(login));
		char query[512];
		snprintf(query, sizeof(query),
				"INSERT INTO player.item_award (pid, login, vnum, count, given_time, why, socket0, socket1, socket2, mall) "
				"VALUES (%u, '%s', %u, %u, NOW(), 'Kod promocyjny', 0, 0, 0, 1)",
				ch->GetDesc()->GetAccountTable().id, escLogin, r.vnum, r.count);
		std::unique_ptr<SQLMsg> award(AccountDB::instance().DirectQuery(query));
		if (QueryOk(award) && award->Get()->uiAffectedRows == 1)
		{
			where = " (Magazyn ItemShop)";
			return;
		}
		sys_err("VOUCHER: item_award of %u x%u for %s failed - given at the feet", r.vnum, r.count, ch->GetName());
		ch->AutoGiveItem(r.vnum, (ITEM_COUNT) r.count);
	}

	enum ERedeem
	{
		REDEEM_OK,		// given
		REDEEM_NOT_OURS,	// not a code of common.mt2009_voucher (or not a code at all)
		REDEEM_USED,		// this account has had it
		REDEEM_LIMIT,		// over 5 tries a minute
		REDEEM_ERROR,		// the database did not answer
		REDEEM_OFF,		// switched off in the Seban panel (m2_vouchers_off)
	};

	const char* const MSG_INVALID = "Nieprawid\xb3owy kod.";
	const char* const MSG_USED = "Ten kod zosta\xb3 ju\xbf wykorzystany na tym koncie.";
	const char* const MSG_LIMIT = "Za du\xbfo pr\xf3" "b - spr\xf3" "buj ponownie za minut\xea.";
	const char* const MSG_OFF = "Kody bonusowe s\xb9 wy\xb3\xb9" "czone na tym serwerze.";
	const char* const MSG_ERROR = "Kody s\xb9 chwilowo niedost\xeapne - spr\xf3" "buj p\xf3\x9fniej.";

	// The Seban panel's switch "Kody bonusowe (vouchery)": the event flag
	// m2_vouchers_off (dwPID 0) read from the table itself at each try, so the
	// panel's write works at once on every core, no restart and no db-core cache.
	bool SwitchedOff()
	{
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
				"SELECT lValue FROM player.quest WHERE dwPID=0 AND szName='m2_vouchers_off' AND szState='' LIMIT 1"));
		if (!QueryOk(msg) || !msg->Get()->pSQLResult)
			return false;
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		long v = 0;
		if (row && row[0])
			str_to_number(v, row[0]);
		return v != 0;
	}

	// The whole redemption, for "/kod" and the ItemShop's voucher tab. Tells the
	// character only "Kod zrealizowany: ..." (the callers tell the rest); `hash12`
	// gets the code's hash prefix for a log.
	ERedeem Redeem(LPCHARACTER ch, const char* typed, std::string& hash12)
	{
		hash12.clear();
		if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot() || !ch->IsPC())
			return REDEEM_NOT_OURS;
		const DWORD account = ch->GetDesc()->GetAccountTable().id;
		if (!account)
			return REDEEM_NOT_OURS;
		if (OverLimit(ch->GetPlayerID()))
			return REDEEM_LIMIT;
		std::string code;
		if (!mt2009_voucher_rules::Normalize(typed, code))
			return REDEEM_NOT_OURS;
		const bool off = SwitchedOff();

		// The code's hash and reward. `code` is [A-Z0-9] only (Normalize).
		char query[512];
		snprintf(query, sizeof(query),
				"SELECT code_hash, vnum, count FROM common.mt2009_voucher "
				"WHERE code_hash = SHA2(CONCAT('%s', '%s'), 256) ORDER BY reward_no",
				mt2009_voucher_rules::VOUCHER_SALT, code.c_str());
		std::unique_ptr<SQLMsg> found(AccountDB::instance().DirectQuery(query));
		if (!QueryOk(found))
		{
			sys_err("VOUCHER: common.mt2009_voucher not readable (%s)", ch->GetName());
			return REDEEM_ERROR;
		}
		std::string hash;
		std::vector<TReward> rewards;
		if (found->Get()->pSQLResult)
		{
			MYSQL_ROW row;
			while (NULL != (row = mysql_fetch_row(found->Get()->pSQLResult)))
			{
				TReward r = { 0, 1 };
				if (!row[0] || !row[1] || !str_to_number(r.vnum, row[1]) || !r.vnum)
					continue;
				if (row[2])
					str_to_number(r.count, row[2]);
				if (!r.count)
					r.count = 1;
				hash = row[0];
				rewards.push_back(r);
			}
		}
		if (rewards.empty() || hash.size() != 64 || hash.find_first_not_of("0123456789abcdef") != std::string::npos)
			return REDEEM_NOT_OURS;
		hash12 = hash.substr(0, 12);
		if (off)
			return REDEEM_OFF;

		// Taken: the row first, so the account gets it once even across cores.
		snprintf(query, sizeof(query),
				"INSERT IGNORE INTO player.mt2009_voucher_used (account_id, code_hash, pid, used_at) VALUES (%u, '%s', %u, NOW())",
				account, hash.c_str(), ch->GetPlayerID());
		std::unique_ptr<SQLMsg> taken(AccountDB::instance().DirectQuery(query));
		if (!QueryOk(taken))
		{
			sys_err("VOUCHER: player.mt2009_voucher_used not writable (%s)", ch->GetName());
			return REDEEM_ERROR;
		}
		if (taken->Get()->uiAffectedRows != 1)
			return REDEEM_USED;

		std::string what;
		for (size_t i = 0; i < rewards.size(); ++i)
		{
			const char* where = "";
			GiveOne(ch, rewards[i], where);
			char part[160];
			if (rewards[i].count > 1)
				snprintf(part, sizeof(part), "%s x%u%s", ItemName(rewards[i].vnum), rewards[i].count, where);
			else
				snprintf(part, sizeof(part), "%s%s", ItemName(rewards[i].vnum), where);
			if (!what.empty())
				what += ", ";
			what += part;
			sys_log(0, "VOUCHER: %s (pid %u, account %u) code %s: %u x%u%s", ch->GetName(), ch->GetPlayerID(), account,
					hash12.c_str(), rewards[i].vnum, rewards[i].count, where);
		}
		ch->ChatPacket(CHAT_TYPE_INFO, "Kod zrealizowany: %s.", what.c_str());
		return REDEEM_OK;
	}

	// "/kod <kod>".
	void Command(LPCHARACTER ch, const char* argument)
	{
		if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot() || !ch->IsPC())
			return;
		const char* arg = argument ? argument : "";
		while (*arg == ' ')
			++arg;
		if (!*arg)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "U\xbfycie: /kod MT2009-PLUS-XXXX");
			return;
		}
		std::string hash12;
		switch (Redeem(ch, arg, hash12))
		{
			case REDEEM_OK: break;
			case REDEEM_NOT_OURS: ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_INVALID); break;
			case REDEEM_USED: ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_USED); break;
			case REDEEM_LIMIT: ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_LIMIT); break;
			case REDEEM_ERROR: ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_ERROR); break;
			case REDEEM_OFF: ch->ChatPacket(CHAT_TYPE_INFO, "%s", MSG_OFF); break;
		}
	}
}

// "/kod" and "/voucher" (cmd.cpp, server-patches/playerqol MT2009_PLUS_VOUCHER_CODES_V1).
ACMD(do_voucher)
{
	mt2009_voucher::Command(ch, argument);
}

// The ItemShop's "Wykorzystaj voucher" tab (CItemShopManager::SendUseCodeVoucher,
// server-patches/playerqol MT2009_PLUS_VOUCHER_CODES_V1 (itemshop)): one of our codes
// -> the USE_VOUCHER_* answer for the window (`logCode` gets "kod:<hash prefix>" for
// the engine's voucher log, never the code); -1 -> not ours, the db core's cash
// vouchers take it.
int VoucherItemShopCode(LPCHARACTER ch, const char* code, std::string& logCode)
{
	std::string hash12;
	logCode.clear();
	switch (mt2009_voucher::Redeem(ch, code, hash12))
	{
		case mt2009_voucher::REDEEM_OK:
			logCode = "kod:" + hash12;
			return USE_VOUCHER_SUCCESS;
		case mt2009_voucher::REDEEM_USED:
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", mt2009_voucher::MSG_USED);
			return USE_VOUCHER_ALREADY_USED;
		case mt2009_voucher::REDEEM_LIMIT:
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", mt2009_voucher::MSG_LIMIT);
			return USE_VOUCHER_TRY_AGAIN_LATER;
		case mt2009_voucher::REDEEM_OFF:
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", mt2009_voucher::MSG_OFF);
			return USE_VOUCHER_NO_CODE;
		case mt2009_voucher::REDEEM_ERROR:
			ch->ChatPacket(CHAT_TYPE_INFO, "%s", mt2009_voucher::MSG_ERROR);
			return USE_VOUCHER_TRY_AGAIN_LATER;
		default:
			return -1;
	}
}
