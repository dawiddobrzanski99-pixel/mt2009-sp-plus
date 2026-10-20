#ifndef __INC_METIN2_PLAYERBOT_MARKET_FAIR_EXPORT_H__
#define __INC_METIN2_PLAYERBOT_MARKET_FAIR_EXPORT_H__

// MT2009_PLUS_MARKET_FAIR_EXPORT_V1 - the bots' usual price of every line on
// the market, for the panel's Podglad rynku.
//
// The owner, 10 October: "Podglad rynku pokazuje prawdziwe okazje - ceny
// zwykle maja byc liczone tak samo jak boty licza ceny". The panel kept a copy
// of the bots' price sheet (market_preview/gen_sheet.py) and multiplied it by
// its own reading of the yang rate and the bonus lines; everything the bots
// add on top of the sheet - the inflation of the world's yang, the Cor
// Draconis by the stones it opens into, the level-30 weapons by their
// average, the rare goods, the talismans, the belts, the sale memory and the
// market index - it could not know, and a Cor or a weapon of weak averages
// came out a "bargain" the bots would never call one.
//
// So the panel reads the bots' own number: one core (the events' leader, so
// one file for the world) prices every line of every offline shop the way a
// bot judges a line it looks at - GetPlayerBotShopAskingPrice of the line's
// piece (BotOfflinePreview), the yardstick of every bargain and slip rule in
// playerbot_market.h - and writes it a piece, by the line's item id, to
// PLAYERBOT_MARKET_FAIR_PATH. A pass every PLAYERBOT_MARKET_FAIR_INTERVAL_MS,
// sliced over the manager's ticks; a line without bonus lines is priced once
// a kind (vnum, sockets, count) and a pass. The step limiter is only read
// while it runs (s_bPlayerBotAskStepReadOnly): a look at the market moves no
// price. Written beside the file and renamed over it, so the panel never
// reads half a pass.
//
// An implementation fragment: include it once, after playerbot_offline_market.h
// and playerbot_events.h; the manager calls ExportPlayerBotMarketFairPrices
// after the market ledger.

namespace
{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
	const char* const PLAYERBOT_MARKET_FAIR_PATH = "/opt/m2spool/playerbot_market_fair.tsv";
	const DWORD PLAYERBOT_MARKET_FAIR_INTERVAL_MS = 2 * 60 * 1000;
	// A tick's share: the pieces made and priced, and the lines read.
	const unsigned int PLAYERBOT_MARKET_FAIR_PREVIEWS_PER_TICK = 300;
	const unsigned int PLAYERBOT_MARKET_FAIR_LINES_PER_TICK = 6000;

	struct TPlayerBotMarketFairKey
	{
		DWORD vnum;
		DWORD count;
		long sockets[3];
		bool operator<(const TPlayerBotMarketFairKey& o) const
		{
			if (vnum != o.vnum) return vnum < o.vnum;
			if (count != o.count) return count < o.count;
			for (int i = 0; i < 3; ++i)
				if (sockets[i] != o.sockets[i])
					return sockets[i] < o.sockets[i];
			return false;
		}
	};

	struct TPlayerBotMarketFairPass
	{
		bool running;
		DWORD nextAt;
		std::vector<DWORD> owners;
		size_t ownerIndex;
		FILE* fp;
		unsigned int lines;
		unsigned int previews;
		std::map<TPlayerBotMarketFairKey, DWORD> plain;
		TPlayerBotMarketFairPass() : running(false), nextAt(0), ownerIndex(0), fp(NULL), lines(0), previews(0) {}
	};
	TPlayerBotMarketFairPass s_kPlayerBotMarketFair;

	std::string GetPlayerBotMarketFairTempPath()
	{
		return std::string(PLAYERBOT_MARKET_FAIR_PATH) + ".tmp";
	}

	// The unit price of one line as a bot judges it; 0 for a line it cannot read.
	DWORD GetPlayerBotMarketFairUnit(const ikashop::CShopItem& line, unsigned int& previews)
	{
		const auto& info = line.GetInfo();
		const DWORD count = std::max<DWORD>(1, (DWORD)info.count);
		bool attrs = false;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (info.aAttr[i].bType != 0 && info.aAttr[i].sValue != 0)
				attrs = true;
		TPlayerBotMarketFairKey key;
		key.vnum = info.vnum;
		key.count = count;
		for (int i = 0; i < 3; ++i)
			key.sockets[i] = i < ITEM_SOCKET_MAX_NUM ? (long)info.alSockets[i] : 0;
		if (!attrs)
		{
			std::map<TPlayerBotMarketFairKey, DWORD>::const_iterator it = s_kPlayerBotMarketFair.plain.find(key);
			if (it != s_kPlayerBotMarketFair.plain.end())
				return it->second;
		}
		LPITEM preview = BotOfflinePreview(line);
		if (!preview)
			return 0;
		++previews;
		s_bPlayerBotAskStepReadOnly = true;
		const DWORD total = GetPlayerBotShopAskingPrice(preview);
		s_bPlayerBotAskStepReadOnly = false;
		M2_DELETE(preview);
		const DWORD unit = std::max<DWORD>(1, total / count);
		if (!attrs)
			s_kPlayerBotMarketFair.plain[key] = unit;
		return unit;
	}

	void FinishPlayerBotMarketFairPass(bool ok)
	{
		TPlayerBotMarketFairPass& p = s_kPlayerBotMarketFair;
		const std::string tmp = GetPlayerBotMarketFairTempPath();
		if (p.fp)
		{
			ok = fflush(p.fp) == 0 && ok;
			ok = fclose(p.fp) == 0 && ok;
			p.fp = NULL;
		}
		if (ok && rename(tmp.c_str(), PLAYERBOT_MARKET_FAIR_PATH) == 0)
			sys_log(0, "PLAYERBOT_MARKET: fair prices exported lines=%u priced=%u kinds=%u",
					p.lines, p.previews, (unsigned int)p.plain.size());
		else
			unlink(tmp.c_str());
		p.running = false;
		p.owners.clear();
		p.plain.clear();
	}

	void ExportPlayerBotMarketFairPrices(DWORD dwNow)
	{
		TPlayerBotMarketFairPass& p = s_kPlayerBotMarketFair;
		if (!p.running)
		{
			if (p.nextAt != 0 && (int)(dwNow - p.nextAt) < 0)
				return;
			p.nextAt = dwNow + PLAYERBOT_MARKET_FAIR_INTERVAL_MS;
			if (!IsPlayerBotEventLeader())
				return;
			p.fp = fopen(GetPlayerBotMarketFairTempPath().c_str(), "w");
			if (!p.fp)
				return;
			fprintf(p.fp, "# MT2009_PLUS_MARKET_FAIR_EXPORT_V1 item_id<TAB>unit price as the bots judge it; generated %ld\n",
					(long)get_global_time());
			p.owners.clear();
			for (const auto& [owner, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
				if (shop)
					p.owners.push_back(shop->GetOwnerPID());
			p.ownerIndex = 0;
			p.lines = p.previews = 0;
			p.plain.clear();
			p.running = true;
		}
		unsigned int lines = 0, previews = 0;
		while (p.ownerIndex < p.owners.size() && lines < PLAYERBOT_MARKET_FAIR_LINES_PER_TICK &&
				previews < PLAYERBOT_MARKET_FAIR_PREVIEWS_PER_TICK)
		{
			auto shop = ikashop::GetManager().GetShopByOwnerID(p.owners[p.ownerIndex++]);
			if (!shop)
				continue;
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line || !line->GetTable())
					continue;
				++lines;
				const DWORD unit = GetPlayerBotMarketFairUnit(*line, previews);
				if (unit == 0)
					continue;
				if (fprintf(p.fp, "%llu\t%u\n", (unsigned long long)line->GetID(), unit) < 0)
				{
					FinishPlayerBotMarketFairPass(false);
					return;
				}
				++p.lines;
			}
		}
		p.previews += previews;
		if (p.ownerIndex >= p.owners.size())
			FinishPlayerBotMarketFairPass(true);
	}
#else
	void ExportPlayerBotMarketFairPrices(DWORD) {}
#endif
}

#endif
