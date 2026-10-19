#ifndef __INC_METIN2_PLAYERBOT_GUILD_LFG_H__
#define __INC_METIN2_PLAYERBOT_GUILD_LFG_H__

// MT2009_PLUS_GUILD_LFG_V1 - "Szukam ludzi do gildii" (experimental).
//
// The owner, 5 October: "Dodaj opcje: Szukam ludzi do gildii - gracz pisze na
// czacie ze szuka do gildii, zglaszaja sie do niego boty na podobnej zasadzie
// co do dungeonow. Tylko boty ktore nie maja gildii, albo tylko boty ktore
// maja bardzo slaba gildie. [...] Odpisuje TAK i wtedy bot mowi ze czeka np.
// przy kowalu w M1 [...] Bot czeka tam 5 minut i jak nie dostanie zaproszenia
// do gildii to pisze, ze czekal i juz idzie bo nie ma wiecej czasu."
//
// Modelled on the dungeon finder (playerbot_dungeon_lfg.h), whose refusals,
// words of the bot's own hand (greeting, level, class and path), yes/no
// reading and line queue it borrows:
//
//   - the call (HandlePlayerBotGuildLfgCall): a person's line on the normal
//     chat, the shout or the '@' trade chat - "szukam ludzi do gildii",
//     "rekrutacja do gildii", "kto do gildii?", "nabor do gildii", "gildia
//     szuka", "zapraszam do gildii" (playerbot_guild_lfg::ParseCall). Only a
//     guild's master or a member whose grade may add members is answered; a
//     guild that is full, or a person blocking whispers, is not. A person with
//     no guild is now and then told "przeciez nie masz gildii xd" by one bot.
//     A person's calls are answered once in ten minutes.
//   - which bots: one to three of the person's kingdom, within fifteen levels
//     of the person, with no guild or a very weak one (GetPlayerBotGuildLfgFreedom:
//     a bot guild below the elite with at most three members, or level 2 or
//     less with at most eight; a person's guild of level 2 or less with at
//     most three members), never a guild's master, a Legend or a Legend's
//     guild, a guild at war; and in no business that matters (the dungeon
//     finder's GetPlayerBotLfgRefusal: a party with a person, a companion, a
//     dungeon run, a raid, the cohorts, a stall...). A bot that offered once
//     is not offered again for thirty minutes.
//   - the offer: "Siema, mam 55 lvl, woj body, dodasz mnie do gildii?" by
//     whisper, through the conversation's queue (the bot's hand and pace; the
//     whisper block, MT2009_PLUS_BOT_WHISPER_BLOCK_V1, holds there).
//   - the yes ("tak", "ok", "jasne", "dawaj", "dodam", "zapraszam"): the bot
//     names the meeting - an NPC of the person's kingdom's first village (the
//     blacksmith, the armour or weapon merchant, the general store, the
//     storekeeper, the old woman; the channel when the person is on another)
//     - and goes there: on foot when it is near, by the map change every move
//     of the AI is otherwise. A bot of a weak guild leaves it then, since the
//     engine's invitation is refused to anybody in a guild. It waits five
//     minutes; the invitation is accepted as any is (AcceptPlayerBotGuildInvite)
//     and it thanks the person. No invitation in five minutes: "czekalem, ale
//     musze juz isc" and back to its life. A no gets a short okay; an offer
//     not answered lapses in three minutes without another word.
//
// MT2009_PLUS_GUILD_LFG_V2 (the owner, 6 October: "nikt im sie nie zglasza
// ... minimum 1 bot, a jak jest wiecej dostepnych to max 10"): three to ten
// bots are wanted; when the rules above find fewer, a looser pass adds any of
// the kingdom from level 10 in a guild below the elite (a person's guild: of
// level 5 or less with at most ten members), without the offer gap. A
// person's calls are answered every three minutes, a bot offers every
// fifteen. With M1 on another core the bot meets the person where the person
// stands. "Piszcie do mnie na pw" and "wbijajcie do gildii" are calls too.
//
// The FILE playerbot_guild_lfg_off in the game core's directory switches it
// off (checked every 30 s, as the dungeon finder's playerbot_lfg_off).
//
// An implementation fragment: include it once, after playerbot_dungeon_lfg.h
// and playerbot_legends.h.

namespace playerbot_guild_lfg
{
	typedef unsigned int u32;
	using playerbot_conv::TTokens;
	using playerbot_conv::TRng;
	using playerbot_lfg::TFacts;
	using playerbot_lfg::StartsWith;
	using playerbot_lfg::ReplaceAll;
	using playerbot_lfg::Any;

	const u32 OFFER_TTL_MS = 3 * 60 * 1000;
	const u32 WAIT_MS = 5 * 60 * 1000;
	const size_t MAX_CALL_WORDS = 24;

	inline bool In(const std::string& w, const char* const* list, size_t n)
	{
		for (size_t i = 0; i < n; ++i)
			if (w == list[i])
				return true;
		return false;
	}

	inline bool StartsIn(const std::string& w, const char* const* list, size_t n)
	{
		for (size_t i = 0; i < n; ++i)
			if (StartsWith(w, list[i]))
				return true;
		return false;
	}

#define GLFG_IN(w, arr) In((w), (arr), sizeof(arr) / sizeof((arr)[0]))
#define GLFG_STARTS_IN(w, arr) StartsIn((w), (arr), sizeof(arr) / sizeof((arr)[0]))

	inline bool IsGuildWord(const std::string& w)
	{
		return StartsWith(w, "gild") || StartsWith(w, "guild") || w == "gildia";
	}

	// Is the public line a guild's call for members? A person looking for a
	// guild ("szukam gildii", "kto mnie przyjmie do gildii", "chce dolaczyc do
	// gildii"), a trade or a war is not.
	inline bool ParseCall(const char* raw)
	{
		if (!raw || !*raw || playerbot_lfg::RawTradeMark(raw))
			return false;
		TTokens t;
		playerbot_conv::Normalize(raw, t);
		const std::vector<std::string>& w = t.words;
		if (w.empty() || w.size() > MAX_CALL_WORDS)
			return false;
		static const char* const trade[] = { "kupie", "kupuje", "sprzedam", "sprzedaje", "oddam", "wymienie", "zamienie",
			"yang", "kk", "won", "wony", "cena", "cene", "tanio", "drogo" };
		static const char* const self[] = { "mnie", "przyjmie", "przyjmiecie", "przyjmiesz", "wezmie", "wezmiecie",
			"wezmiesz", "dodacie", "doda", "dodasz", "zaprosi", "zaprosicie", "zaprosisz" };
		static const char* const war[] = { "wojna", "wojne", "wojny", "war", "wara", "gw" };
		static const char* const people[] = { "ludzi", "ludzie", "osob", "osoby", "osobe", "graczy", "gracza", "chetnych",
			"czlonkow", "czlonka", "memberow", "membersow", "nowych", "kogos", "rekrutow", "aktywnych", "ekipy", "ekipe",
			"skladu", "graczow", "typa", "typow" };
		static const char* const recruit[] = { "rekrut", "nabor", "werbu", "zapraszam", "zapraszamy", "przyjme", "przyjmuje",
			"przyjmujemy", "przyjmiemy", "zbieram", "zbieramy", "lfm", "dodam", "dodaje", "dodajemy", "szukamy", "wolne",
			"zaprosze", "zaprosimy" };
		static const char* const joinStems[] = { "dolacz", "wstap", "wbij" };
		// MT2009_PLUS_GUILD_LFG_V2: "piszcie do mnie", "zglaszajcie sie do mnie" -
		// the way to reach the caller, not a person asking to be taken.
		static const char* const contact[] = { "pisz", "piszcie", "pisac", "napisz", "napiszcie", "zglaszac", "zglaszajcie",
			"zglos", "zgloscie", "priv", "pw", "msg", "pv" };
		bool contactWord = false;
		for (size_t i = 0; i < w.size(); ++i)
			if (GLFG_IN(w[i], contact))
				contactWord = true;
		static const char* const who[] = { "kto", "ktos", "ktokolwiek", "chetny", "chetni", "chetna" };
		static const char* const want[] = { "chce", "chcialbym", "chcialabym", "chcem", "szukalbym" };

		size_t guildAt = w.size();
		for (size_t i = 0; i < w.size(); ++i)
			if (IsGuildWord(w[i]))
			{
				guildAt = i;
				break;
			}
		if (guildAt == w.size())
			return false;
		bool peopleWord = false, recruitWord = false, joinWord = false, whoWord = false, wantWord = false;
		size_t seekAt = w.size();
		for (size_t i = 0; i < w.size(); ++i)
		{
			const std::string& x = w[i];
			if (GLFG_IN(x, trade) || GLFG_IN(x, war))
				return false;
			if (GLFG_IN(x, self) && !(contactWord && x == "mnie"))
				return false;
			if (GLFG_IN(x, people))
				peopleWord = true;
			if (GLFG_STARTS_IN(x, recruit))
				recruitWord = true;
			if (GLFG_STARTS_IN(x, joinStems))
				joinWord = true;
			if (GLFG_IN(x, who))
				whoWord = true;
			if (GLFG_IN(x, want))
				wantWord = true;
			if (seekAt == w.size() && (StartsWith(x, "szuk") || StartsWith(x, "potrzeb") || StartsWith(x, "brak")))
				seekAt = i;
		}
		// "do gildii", "do mojej gildii", "do naszej gildii".
		bool doGuild = false;
		for (size_t back = 1; back <= 2 && back <= guildAt; ++back)
			if (w[guildAt - back] == "do")
				doGuild = true;
		const bool seek = seekAt != w.size();
		// "szukam gildii", "szukam jakiejs dobrej gildii": a person after one.
		if (seek && seekAt < guildAt && !doGuild && !peopleWord)
			return false;
		// "chce dolaczyc do gildii": the same.
		if (wantWord && (joinWord || doGuild) && !peopleWord && !whoWord)
			return false;
		const bool guildSubject = seek && guildAt < seekAt;
		// "wbijajcie do gildii": the call's plural imperative.
		for (size_t i = 0; i < w.size(); ++i)
			if (StartsWith(w[i], "wbijaj") || StartsWith(w[i], "dolaczaj") || StartsWith(w[i], "wstepuj"))
				joinWord = whoWord = true;
		return recruitWord || (joinWord && (whoWord || t.question || peopleWord)) ||
				(seek && (peopleWord || guildSubject || doGuild)) || (whoWord && doGuild);
	}

	// The person's whispered answer: 1 yes, -1 no, 0 neither. The dungeon
	// finder's reading, and the guild's own yes ("dodam", "zapraszam").
	inline int ParseYesNo(const TTokens& t)
	{
		const int yn = playerbot_lfg::ParseYesNo(t);
		if (yn != 0)
			return yn;
		static const char* const yes[] = { "dodam", "dodaje", "dodamy", "zaprosze", "zapraszam", "przyjme", "przyjmuje",
			"biore", "wezme", "dawaj", "jasne", "wpadaj", "przyjdz", "chodz", "zgoda", "spoko", "okk", "oki", "okej" };
		bool y = false;
		for (size_t i = 0; i < t.words.size(); ++i)
		{
			if (t.words[i] == "nie")
				return 0;
			if (GLFG_IN(t.words[i], yes))
				y = true;
		}
		return y && t.words.size() <= 12 ? 1 : 0;
	}

	inline bool AsksWhere(const TTokens& t)
	{
		for (size_t i = 0; i < t.words.size(); ++i)
			if (t.words[i] == "gdzie" || t.words[i] == "gdzie?" || t.words[i] == "jestes" || t.words[i] == "stoisz")
				return true;
		return false;
	}

	// ----------------------------------------------------------- the lines

	// The NPCs a meeting is named at, in the town services' table
	// (playerbot_empire_rules::TTownServices): "przy $NPC".
	enum ENpc
	{
		NPC_SMITH = 0,
		NPC_ARMOUR,
		NPC_MISC,
		NPC_STORE,
		NPC_WEAPON,
		NPC_OLD_WOMAN,
		NPC_COUNT
	};

	inline const char* NpcWords(TRng& rng, int npc)
	{
		static const char* const smith[] = { "kowalu", "kowalu", "Kowalu" };
		static const char* const armour[] = { "handlarzu zbrojami", "handlarzu zbroj`a", "sklepie ze zbrojami" };
		static const char* const misc[] = { "handlarce r`o`zno`sci", "handlarce", "sklepie z r`o`zno`sciami" };
		static const char* const store[] = { "magazynierze", "magazynie", "magazynierze" };
		static const char* const weapon[] = { "handlarzu broni`a", "sklepie z broni`a", "handlarzu broni`a" };
		static const char* const old[] = { "starszej pani", "starej kobiecie", "babci od reset`ow" };
		switch (npc)
		{
			case NPC_SMITH: return Any(rng, smith);
			case NPC_ARMOUR: return Any(rng, armour);
			case NPC_MISC: return Any(rng, misc);
			case NPC_STORE: return Any(rng, store);
			case NPC_WEAPON: return Any(rng, weapon);
			default: return Any(rng, old);
		}
	}

	// Where: "w M1 przy kowalu", "w Yongan przy handlarzu zbrojami (CH2)".
	struct TPlace
	{
		int npc;
		std::string village;   // the first village's name
		int channel;           // named when the person is on another
		bool nearPerson;       // MT2009_PLUS_GUILD_LFG_V2: at the person's side, M1 not on this core
		TPlace() : npc(NPC_SMITH), channel(0), nearPerson(false) {}
	};

	inline std::string PlaceWords(TRng& rng, const TPlace& p)
	{
		if (p.nearPerson)
		{
			static const char* const near[] = { "przy tobie", "obok ciebie", "ko`lo ciebie", "tam gdzie stoisz" };
			return Any(rng, near);
		}
		static const char* const forms[] = { "w M1 przy $NPC", "przy $NPC w M1", "w $VIL przy $NPC", "w M1 ($VIL) przy $NPC",
			"przy $NPC w $VIL", "w M1 przy $NPC" };
		std::string out = Any(rng, forms);
		ReplaceAll(out, "$NPC", NpcWords(rng, p.npc));
		ReplaceAll(out, "$VIL", p.village);
		if (p.channel > 0)
		{
			char ch[24];
			snprintf(ch, sizeof(ch), rng.Chance(50) ? " na CH%d" : " (CH%d)", p.channel);
			out += ch;
		}
		return out;
	}

	inline std::string Lower(std::string s)
	{
		if (!s.empty() && s[0] >= 'A' && s[0] <= 'Z')
			s[0] = (char)(s[0] - 'A' + 'a');
		return s;
	}

	// "Siema, mam 55 lvl, woj body, dodasz mnie do gildii?"
	inline std::string OfferLine(TRng& rng, const TFacts& f, bool guildless)
	{
		static const char* const ask[] = { "dodasz mnie do gildii?", "przyjmiesz mnie do gildii?", "we`xmiesz mnie do gildii?",
			"dodasz mnie?", "przyjmiesz mnie?", "jest jeszcze miejsce? ch`etnie do`l`acz`e", "mog`e do ciebie do gildii?",
			"szukasz jeszcze? ch`etnie wbij`e do gildii", "we`xmiesz mnie?", "dodasz do gildii?", "mog`e do`l`aczy`c?",
			"przyjmiecie mnie do gildii?", "ch`etnie do`l`acz`e do gildii, dodasz?", "jak co to ja si`e pisz`e, dodasz?" };
		static const char* const none[] = { "nie mam gildii", "szukam gildii", "jestem bez gildii", "akurat nie mam gildii",
			"szukam jakiej`s gildii" };
		static const char* const weak[] = { "moja gildia jest martwa", "w mojej gildii nikogo nie ma", "moja gildia nie gra",
			"mam s`lab`a gildi`e, chc`e zmieni`c", "u mnie w gildii pusto" };
		const std::string g = playerbot_lfg::Greeting(rng);
		const std::string s = playerbot_lfg::SelfWords(rng);
		const std::string a = Any(rng, ask);
		const std::string st = rng.Chance(45) ? std::string(guildless ? Any(rng, none) : Any(rng, weak)) : std::string();
		std::string out;
		switch (rng.Range(5))
		{
			case 0: out = (g.empty() ? "" : g + ", ") + s + ", " + a; break;
			case 1: out = (g.empty() ? "" : g + "! ") + s + (st.empty() ? "" : ", " + st) + ". " + a; break;
			case 2: out = (g.empty() ? "" : g + ", ") + (st.empty() ? "" : st + ", ") + s + " - " + a; break;
			case 3: out = s + (st.empty() ? "" : ", " + st) + ", " + a; break;
			default: out = (g.empty() ? "" : g + ", ") + a + " " + s; break;
		}
		return playerbot_lfg::Finish(rng, f, out);
	}

	// A person with no guild calling for members: one bot says so, rarely.
	inline std::string NoGuildLine(TRng& rng, const TFacts& f)
	{
		static const char* const k[] = { "przecie`z nie masz gildii xd", "a ty masz w og`ole gildi`e? :D",
			"najpierw za`l`o`z gildi`e xd", "do jakiej gildii, przecie`z nie masz :D", "ale ty nie masz gildii xd" };
		return playerbot_lfg::Finish(rng, f, Any(rng, k));
	}

	// The yes: the meeting named.
	inline std::string MeetLine(TRng& rng, const TFacts& f, const TPlace& p, bool walking)
	{
		static const char* const lead[] = { "ok, ", "super, ", "dzi`eki, ", "git, ", "jasne, ", "dobra, ", "spoko, ", "" };
		static const char* const there[] = { "czekam $WHERE, b`ed`e tam 5 minut", "jestem ju`z $WHERE, zapro`s mnie jak b`edziesz",
			"stoj`e $WHERE, czekam 5 min", "czekam na ciebie $WHERE, mam jakie`s 5 minut",
			"jestem $WHERE, daj zaproszenie do gildii", "b`ed`e $WHERE przez 5 minut, wpadnij i zapro`s",
			"czekam $WHERE. 5 minut, potem musz`e lecie`c" };
		static const char* const coming[] = { "ju`z id`e, poczekam $WHERE 5 minut", "ju`z biegn`e, b`ed`e czeka`l $WHERE",
			"zaraz b`ed`e $WHERE, zapro`s mnie tam", "lec`e, czekam $WHERE 5 min" };
		std::string out = std::string(Any(rng, lead));
		std::string body = walking ? Any(rng, coming) : Any(rng, there);
		ReplaceAll(body, "$WHERE", PlaceWords(rng, p));
		out += out.empty() ? body : Lower(body);
		return playerbot_lfg::Finish(rng, f, out);
	}

	inline std::string WhereLine(TRng& rng, const TFacts& f, const TPlace& p)
	{
		static const char* const k[] = { "$WHERE", "czekam $WHERE", "stoj`e $WHERE :)", "jestem $WHERE, zapro`s mnie" };
		std::string out = Any(rng, k);
		ReplaceAll(out, "$WHERE", PlaceWords(rng, p));
		return playerbot_lfg::Finish(rng, f, out);
	}

	inline std::string AlreadyLine(TRng& rng, const TFacts& f, const TPlace& p)
	{
		static const char* const k[] = { "przecie`z ju`z czekam $WHERE :)", "ju`z tu stoj`e, $WHERE", "czekam czekam, $WHERE",
			"jestem $WHERE, daj zaproszenie" };
		std::string out = Any(rng, k);
		ReplaceAll(out, "$WHERE", PlaceWords(rng, p));
		return playerbot_lfg::Finish(rng, f, out);
	}

	inline std::string DeclineLine(TRng& rng, const TFacts& f)
	{
		static const char* const k[] = { "ok, spoko", "jasne, powodzenia z rekrutacj`a", "dobra, nara", "luz, mo`ze innym razem",
			"ok, szkoda", "spoko, powodzenia", "ok :)", "rozumiem, nara" };
		return playerbot_lfg::Finish(rng, f, Any(rng, k));
	}

	inline std::string JoinedLine(TRng& rng, const TFacts& f)
	{
		static const char* const k[] = { "dzi`eki za zaproszenie!", "dzi`eki, jestem :)", "super, dzi`eki!", "dzi`eki za gildi`e",
			"jestem w gildii, dzi`eki :)", "dzi`ex, to do zobaczenia", "dzi`eki! jakby co pisz" };
		return playerbot_lfg::Finish(rng, f, Any(rng, k));
	}

	// Five minutes and no invitation.
	inline std::string TimeoutLine(TRng& rng, const TFacts& f, const TPlace& p)
	{
		static const char* const k[] = { "czeka`lem 5 minut $WHERE, ale musz`e ju`z i`s`c", "nie doczeka`lem si`e zaproszenia, lec`e dalej, nie mam wi`ecej czasu",
			"czeka`lem, ale nikt nie przyszed`l. musz`e ju`z lecie`c", "dobra, czeka`lem, ale ju`z nie mam czasu. nara",
			"sorki, czeka`lem $WHERE, ale musz`e ju`z i`s`c", "no nic, czeka`lem 5 minut. musz`e lecie`c, jakby co pisz",
			"czeka`lem i czeka`lem, ale musz`e ju`z i`s`c. mo`ze innym razem", "nie mam ju`z czasu czeka`c, lec`e. jakby co pisz" };
		std::string out = Any(rng, k);
		ReplaceAll(out, "$WHERE", PlaceWords(rng, p));
		return playerbot_lfg::Finish(rng, f, out);
	}

	inline std::string OtherGuildLine(TRng& rng, const TFacts& f)
	{
		static const char* const k[] = { "sorki, kto`s mnie ju`z wzi`a`l do gildii", "sorry, ju`z mam gildi`e, nieaktualne",
			"ju`z jestem w innej gildii, sorki" };
		return playerbot_lfg::Finish(rng, f, Any(rng, k));
	}
}

#undef GLFG_IN
#undef GLFG_STARTS_IN

namespace
{
	const DWORD PLAYERBOT_GLFG_FIRST_DELAY_MIN_MS = 5000;
	const DWORD PLAYERBOT_GLFG_FIRST_DELAY_SPREAD_MS = 6000;
	const DWORD PLAYERBOT_GLFG_NEXT_DELAY_MIN_MS = 5000;
	const DWORD PLAYERBOT_GLFG_NEXT_DELAY_SPREAD_MS = 9000;
	// A person's calls are answered this often; a bot offers this often.
	// MT2009_PLUS_GUILD_LFG_V2 (the owner, 6 October: "nikt im sie nie zglasza
	// ... zawsze, przy kazdym zgloszeniu napisal do niego minimum 1 bot, a jak
	// jest wiecej dostepnych to max 10"): shorter gaps, up to ten bots, and a
	// looser second pass (PLAYERBOT_GLFG_RELAXED) when the strict one finds none.
	const DWORD PLAYERBOT_GLFG_PERSON_GAP_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_GLFG_BOT_GAP_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_GLFG_OFFER_SLACK_MS = 20 * 1000;
	const DWORD PLAYERBOT_GLFG_WALK_EXTRA_MS = 90 * 1000;
	const DWORD PLAYERBOT_GLFG_SWITCH_CHECK_MS = 30 * 1000;
	const DWORD PLAYERBOT_GLFG_PRUNE_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_GLFG_NOTE_MS = 60 * 1000;
	const int PLAYERBOT_GLFG_LEVEL_SPAN = 15;
	const int PLAYERBOT_GLFG_MIN_LEVEL = 10;
	const int PLAYERBOT_GLFG_MIN_BOTS = 3;
	const int PLAYERBOT_GLFG_MAX_BOTS = 10;
	const int PLAYERBOT_GLFG_NO_GUILD_PERCENT = 15;
	const int PLAYERBOT_GLFG_WALK_RANGE = 4000;
	const int PLAYERBOT_GLFG_SPOT_RADIUS = 180;
	const int PLAYERBOT_GLFG_STAY_DISTANCE = 300;

	enum EPlayerBotGuildLfgPhase
	{
		GLFG_PHASE_DUE = 1,
		GLFG_PHASE_OFFERED,
		GLFG_PHASE_WAITING
	};

	enum EPlayerBotGuildLfgLine
	{
		GLFG_LINE_NONE = 0,
		GLFG_LINE_DECLINE,
		GLFG_LINE_TIMEOUT,
		GLFG_LINE_JOINED,
		GLFG_LINE_OTHER_GUILD,
		GLFG_LINE_CALLED_AWAY,
		GLFG_LINE_CANT_COME
	};

	struct TPlayerBotGuildLfg
	{
		DWORD personPID;
		std::string personName;
		BYTE personEmpire;
		DWORD guildID;
		BYTE phase;
		bool noGuild;      // "przeciez nie masz gildii" and nothing more
		bool walking;
		bool relaxed;      // MT2009_PLUS_GUILD_LFG_V2: found by the looser pass
		DWORD dueAt;
		DWORD offeredAt;
		DWORD acceptedAt;
		DWORD waitUntil;
		DWORD notedAt;
		long map;
		long spotX;
		long spotY;
		playerbot_guild_lfg::TPlace place;
		TPlayerBotGuildLfg() : personPID(0), personEmpire(0), guildID(0), phase(GLFG_PHASE_DUE), noGuild(false),
			walking(false), relaxed(false), dueAt(0), offeredAt(0), acceptedAt(0), waitUntil(0), notedAt(0), map(0), spotX(0), spotY(0) {}
	};

	std::map<DWORD, TPlayerBotGuildLfg> s_mapPlayerBotGuildLfg;     // by bot pid
	std::map<DWORD, DWORD> s_mapPlayerBotGuildLfgCalls;             // person pid -> the last call answered
	std::map<DWORD, DWORD> s_mapPlayerBotGuildLfgBotAt;             // bot pid -> its last offer
	bool s_bPlayerBotGuildLfgOff = false;
	DWORD s_dwPlayerBotGuildLfgSwitchAt = 0;
	DWORD s_dwPlayerBotGuildLfgPruneAt = 0;
	unsigned int s_uPlayerBotGuildLfgCalls = 0;
	unsigned int s_uPlayerBotGuildLfgOffers = 0;
	unsigned int s_uPlayerBotGuildLfgAccepted = 0;
	unsigned int s_uPlayerBotGuildLfgJoined = 0;

	bool IsPlayerBotGuildLfgOn(DWORD dwNow)
	{
		if (s_dwPlayerBotGuildLfgSwitchAt == 0 || dwNow - s_dwPlayerBotGuildLfgSwitchAt >= PLAYERBOT_GLFG_SWITCH_CHECK_MS)
		{
			s_dwPlayerBotGuildLfgSwitchAt = dwNow ? dwNow : 1;
			const bool off = PlayerBotConvFlagFile("playerbot_guild_lfg_off");
			if (off != s_bPlayerBotGuildLfgOff)
				sys_log(0, "PLAYERBOT_GUILD_LFG: %s", off ? "off (playerbot_guild_lfg_off)" : "on (experimental)");
			s_bPlayerBotGuildLfgOff = off;
		}
		return !s_bPlayerBotGuildLfgOff;
	}

	// Waiting at the village NPC: the passes that would take a bot away ask
	// this through IsPlayerBotHeldForCompany (playerbot_companions.h), and
	// the party rotation directly.
	bool IsPlayerBotGuildLfgHeld(DWORD botPID)
	{
		std::map<DWORD, TPlayerBotGuildLfg>::const_iterator it = s_mapPlayerBotGuildLfg.find(botPID);
		return it != s_mapPlayerBotGuildLfg.end() && it->second.phase == GLFG_PHASE_WAITING;
	}

	// Whether the person may take members into their guild.
	bool CanPlayerBotGuildLfgPersonInvite(LPCHARACTER person, CGuild* guild)
	{
		if (!person || !guild)
			return false;
		const DWORD pid = person->GetPlayerID();
		if (guild->GetMasterPID() == pid)
			return true;
		TGuildMember* m = guild->GetMember(pid);
		return m && guild->HasGradeAuth(m->grade, GUILD_AUTH_ADD_MEMBER);
	}

	// 0: the bot stays where it is; 1: it has no guild; 2: its guild is
	// so weak it leaves it for the person's.
	// MT2009_PLUS_GUILD_LFG_V2: `relaxed` - any guild below the elite will do
	// (the second pass, when no bot of a weak guild or none is free).
	int GetPlayerBotGuildLfgFreedom(LPCHARACTER bot, CGuild* theirs, bool relaxed = false)
	{
		if (!bot)
			return 0;
		CGuild* mine = bot->GetGuild();
		if (!mine)
			return 1;
		if (mine == theirs || mine->GetMasterPID() == bot->GetPlayerID() || IsPlayerBotLegendGuild(mine) ||
				mine->UnderAnyWar() != 0 || IsPlayerBotGuildRaidingTower(mine->GetID()))
			return 0;
		const int members = mine->GetMemberCount();
		const int level = mine->GetLevel();
		const TPlayerBotGuildInfo* info = GetPlayerBotGuildInfo(mine);
		if (info)
		{
			if (info->bTier == GUILD_TIER_ELITE)
				return 0;
			if (relaxed)
				return 2;
			return members <= 3 || (level <= 2 && members <= 8) ? 2 : 0;
		}
		// A person's guild the bot was invited into: only one that is barely one.
		if (relaxed)
			return level <= 5 && members <= 10 ? 2 : 0;
		return level <= 2 && members <= 3 ? 2 : 0;
	}

	playerbot_lfg::TFacts MakePlayerBotGuildLfgFacts(LPCHARACTER bot, const TPlayerBotGuildLfg& e)
	{
		playerbot_lfg::TFacts f;
		f.level = bot ? bot->GetLevel() : 0;
		f.job = bot ? bot->GetJob() : 0;
		f.group = bot ? bot->GetSkillGroup() : 0;
		f.botName = bot ? bot->GetName() : "";
		f.playerName = e.personName;
		return f;
	}

	void EndPlayerBotGuildLfg(DWORD botPID, const char* reason, int line)
	{
		std::map<DWORD, TPlayerBotGuildLfg>::iterator it = s_mapPlayerBotGuildLfg.find(botPID);
		if (it == s_mapPlayerBotGuildLfg.end())
			return;
		const TPlayerBotGuildLfg e = it->second;
		s_mapPlayerBotGuildLfg.erase(it);
		const DWORD dwNow = get_dword_time();
		LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(botPID);
		if (e.phase == GLFG_PHASE_WAITING)
		{
			// No longer waiting for this person's invitation: the bot masters
			// may ask it again, and it may found its own.
			if (line != GLFG_LINE_JOINED)
				s_mapPlayerBotGuildRecruit.erase(botPID);
			TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(botPID);
			if (bot && st != s_mapPlayerBotAIStates.end())
			{
				ClearPlayerBotRoute(st->second, true);
				st->second.dwLastMeaningfulActivityTime = dwNow;
				SetPlayerBotAction(st->second, BOT_ACTION_IDLE, dwNow);
			}
		}
		sys_log(0, "PLAYERBOT_GUILD_LFG: over pid=%u name=%s person=%s phase=%u reason=%s waited_s=%u",
				botPID, bot ? bot->GetName() : "?", e.personName.c_str(), (unsigned int)e.phase, reason ? reason : "?",
				e.acceptedAt ? (dwNow - e.acceptedAt) / 1000 : 0);
		if (!bot || line == GLFG_LINE_NONE)
			return;
		playerbot_conv::TRng rng = MakePlayerBotLfgRng();
		const playerbot_lfg::TFacts f = MakePlayerBotGuildLfgFacts(bot, e);
		std::string text;
		switch (line)
		{
			case GLFG_LINE_DECLINE: text = playerbot_guild_lfg::DeclineLine(rng, f); break;
			case GLFG_LINE_TIMEOUT: text = playerbot_guild_lfg::TimeoutLine(rng, f, e.place); break;
			case GLFG_LINE_JOINED: text = playerbot_guild_lfg::JoinedLine(rng, f); break;
			case GLFG_LINE_OTHER_GUILD: text = playerbot_guild_lfg::OtherGuildLine(rng, f); break;
			case GLFG_LINE_CALLED_AWAY: text = playerbot_lfg::CalledAwayLine(rng, f); break;
			case GLFG_LINE_CANT_COME: text = playerbot_lfg::CantComeLine(rng, f); break;
			default: break;
		}
		SayPlayerBotLfgLine(bot, e.personPID, text, 400 + number(0, 900));
	}

	// ------------------------------------------------------------ the call

	struct TPlayerBotGuildLfgCandidate
	{
		DWORD pid;
		int weight;
		bool relaxed;
	};

	// A person's line on the normal chat, the shout or the '@' trade chat.
	// True when it was a guild's call (answered or not): the dungeon finder,
	// the trade and the shout's questions leave it alone.
	bool HandlePlayerBotGuildLfgCall(LPCHARACTER person, const char* text, const char* source)
	{
		if (!IsPlayerBotPersonCharacter(person) || !text || !*text)
			return false;
		const DWORD dwNow = get_dword_time();
		if (!IsPlayerBotGuildLfgOn(dwNow))
			return false;
		if (!playerbot_guild_lfg::ParseCall(text))
			return false;
		const DWORD personPID = person->GetPlayerID();
		if (person->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
			return true;
		{
			std::map<DWORD, DWORD>::const_iterator last = s_mapPlayerBotGuildLfgCalls.find(personPID);
			if (last != s_mapPlayerBotGuildLfgCalls.end() && dwNow - last->second < PLAYERBOT_GLFG_PERSON_GAP_MS)
				return true;
		}
		const BYTE empire = person->GetEmpire();
		const int personLevel = person->GetLevel();
		CGuild* guild = person->GetGuild();
		const char* skip = NULL;
		if (person->IsBlockMode(BLOCK_WHISPER))
			skip = "block_whisper";
		else if (guild && !CanPlayerBotGuildLfgPersonInvite(person, guild))
			skip = "no_invite_right";
		else if (guild && guild->GetMemberCount() >= guild->GetMaxMemberCount())
			skip = "guild_full";
		else if (!guild && number(1, 100) > PLAYERBOT_GLFG_NO_GUILD_PERCENT)
			skip = "no_guild";
		// MT2009_PLUS_GUILD_LFG_V2: M1 on another core is no reason for silence -
		// the bot then meets the person where the person stands
		// (PlacePlayerBotGuildLfgSpot).
		if (skip)
		{
			s_mapPlayerBotGuildLfgCalls[personPID] = dwNow;
			sys_log(0, "PLAYERBOT_GUILD_LFG: call from=%s source=%s - %s text=\"%s\"", person->GetName(), source, skip, text);
			return true;
		}

		std::vector<TPlayerBotGuildLfgCandidate> candidates;
		// MT2009_PLUS_GUILD_LFG_V2: at least one bot whenever one is free, up to ten.
		int wanted = 1;
		if (guild)
			wanted = number(PLAYERBOT_GLFG_MIN_BOTS, PLAYERBOT_GLFG_MAX_BOTS);
		// The strict pass first; when it finds fewer than wanted, a looser one -
		// any level from PLAYERBOT_GLFG_MIN_LEVEL, a guild of any tier below the
		// elite, no 15-minute gap between a bot's offers - adds more.
		for (int pass = 0; pass < (guild ? 2 : 1) && (int)candidates.size() < wanted; ++pass)
		{
			const bool relaxed = pass == 1;
			const size_t strictFound = candidates.size();
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				const DWORD pid = it->first;
				bool already = false;
				for (size_t i = 0; i < strictFound; ++i)
					if (candidates[i].pid == pid)
						already = true;
				if (already)
					continue;
				if (s_mapPlayerBotGuildLfg.find(pid) != s_mapPlayerBotGuildLfg.end() ||
						s_mapPlayerBotLfg.find(pid) != s_mapPlayerBotLfg.end())
					continue;
				std::map<DWORD, DWORD>::const_iterator cool = s_mapPlayerBotGuildLfgBotAt.find(pid);
				if (!relaxed && cool != s_mapPlayerBotGuildLfgBotAt.end() && dwNow - cool->second < PLAYERBOT_GLFG_BOT_GAP_MS)
					continue;
				LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(pid);
				if (!c || c == person || c->GetEmpire() != empire)
					continue;
				const TPlayerBotAIState& state = it->second;
				if (!guild)
				{
					// "przeciez nie masz gildii": a bot that heard it, of any level.
					if (c->GetMapIndex() != person->GetMapIndex() ||
							DISTANCE_APPROX(c->GetX() - person->GetX(), c->GetY() - person->GetY()) > 5000 ||
							GetPlayerBotLfgRefusal(c, state, dwNow))
						continue;
					TPlayerBotGuildLfgCandidate cand = { pid, 10, false };
					candidates.push_back(cand);
					continue;
				}
				const int level = c->GetLevel();
				if (level < (relaxed ? PLAYERBOT_GLFG_MIN_LEVEL : std::max(PLAYERBOT_GLFG_MIN_LEVEL, personLevel - PLAYERBOT_GLFG_LEVEL_SPAN)) ||
						(!relaxed && level > personLevel + PLAYERBOT_GLFG_LEVEL_SPAN))
					continue;
				if (IsPlayerBotAwaitingGuildInvite(pid) || IsPlayerBotLegendTier(GetPlayerBotLegendTier(pid)))
					continue;
				const int freedom = GetPlayerBotGuildLfgFreedom(c, guild, relaxed);
				if (freedom == 0)
					continue;
				// The engine's own refusal of a fresh leaver (CGuild::Invite).
				if (get_global_time() - c->GetQuestFlag("guild_manage.new_withdraw_time") <
						CGuildManager::instance().GetWithdrawDelay() ||
						get_global_time() - c->GetQuestFlag("guild_manage.new_disband_time") <
						CGuildManager::instance().GetDisbandDelay())
					continue;
				if (GetPlayerBotLfgRefusal(c, state, dwNow))
					continue;
				TPlayerBotGuildLfgCandidate cand;
				cand.pid = pid;
				cand.weight = relaxed ? 4 : 10;
				cand.relaxed = relaxed;
				if (freedom == 1)
					cand.weight += 10;
				if (c->GetMapIndex() == person->GetMapIndex())
					cand.weight += 20;
				if (state.bCurrentAction == BOT_ACTION_IDLE || state.bCurrentAction == BOT_ACTION_TRAVEL ||
						state.bCurrentAction == BOT_ACTION_TOWN_REST)
					cand.weight += 6;
				if (GetPlayerBotAffinity(state, personPID) > 0)
					cand.weight += 8;
				candidates.push_back(cand);
			}
		}

		const size_t found = candidates.size();
		DWORD due = dwNow + PLAYERBOT_GLFG_FIRST_DELAY_MIN_MS + number(0, (int)PLAYERBOT_GLFG_FIRST_DELAY_SPREAD_MS);
		int picked = 0;
		std::string names;
		while (picked < wanted && !candidates.empty())
		{
			int total = 0;
			for (size_t i = 0; i < candidates.size(); ++i)
				total += candidates[i].weight;
			int roll = number(1, std::max(1, total));
			size_t chosen = 0;
			for (size_t i = 0; i < candidates.size(); ++i)
			{
				roll -= candidates[i].weight;
				if (roll <= 0)
				{
					chosen = i;
					break;
				}
			}
			const DWORD pid = candidates[chosen].pid;
			const bool relaxedPick = candidates[chosen].relaxed;
			candidates.erase(candidates.begin() + chosen);
			LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!c)
				continue;
			TPlayerBotGuildLfg& e = s_mapPlayerBotGuildLfg[pid];
			e = TPlayerBotGuildLfg();
			e.personPID = personPID;
			e.personName = person->GetName();
			e.personEmpire = empire;
			e.guildID = guild ? guild->GetID() : 0;
			e.noGuild = guild == NULL;
			e.relaxed = relaxedPick;
			e.phase = GLFG_PHASE_DUE;
			e.dueAt = due;
			due += PLAYERBOT_GLFG_NEXT_DELAY_MIN_MS + number(0, (int)PLAYERBOT_GLFG_NEXT_DELAY_SPREAD_MS);
			++picked;
			if (!names.empty())
				names += ",";
			names += c->GetName();
		}
		s_mapPlayerBotGuildLfgCalls[personPID] = dwNow;
		++s_uPlayerBotGuildLfgCalls;
		sys_log(0, "PLAYERBOT_GUILD_LFG: call from=%s level=%d source=%s guild=%s candidates=%u picked=%d bots=%s text=\"%s\"",
				person->GetName(), personLevel, source, guild ? guild->GetName() : "-", (unsigned int)found, picked,
				names.c_str(), text);
		return true;
	}

	// ---------------------------------------------------------- the answers

	// The meeting's NPC and the bot's own spot beside it.
	// MT2009_PLUS_GUILD_LFG_V2: with the person's M1 on another core, beside
	// the person instead ("czekam przy tobie").
	bool PlacePlayerBotGuildLfgSpot(LPCHARACTER bot, TPlayerBotGuildLfg& e, LPCHARACTER personLocal)
	{
		static const int kSide[8][2] = {
			{ 200, 0 }, { 141, 141 }, { 0, 200 }, { -141, 141 }, { -200, 0 }, { -141, -141 }, { 0, -200 }, { 141, -141 } };
		const long m1 = playerbot_empire_rules::GetHomeMap(e.personEmpire, playerbot_empire_rules::MAP_ROLE_M1);
		playerbot_empire_rules::TTownServices services;
		if (!m1 || !IsPlayerBotMapHostedHere(m1) || !playerbot_empire_rules::GetTownServices(m1, services))
		{
			if (!personLocal || personLocal->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ||
					!IsPlayerBotMapHostedHere(personLocal->GetMapIndex()))
				return false;
			const int* side = kSide[bot->GetPlayerID() % 8];
			e.map = personLocal->GetMapIndex();
			e.spotX = personLocal->GetX() + side[0] * PLAYERBOT_GLFG_SPOT_RADIUS / 200;
			e.spotY = personLocal->GetY() + side[1] * PLAYERBOT_GLFG_SPOT_RADIUS / 200;
			CPlayerBotNavigation& near = CPlayerBotNavigation::instance(e.map);
			PIXEL_POSITION safe;
			if (near.Init(e.map) && near.FindNearestWalkableWorld(e.spotX, e.spotY, 12, safe, bot->GetPlayerID()))
			{
				e.spotX = safe.x;
				e.spotY = safe.y;
			}
			e.place.nearPerson = true;
			return true;
		}
		const int npc = number(0, playerbot_guild_lfg::NPC_COUNT - 1);
		playerbot_empire_rules::TPoint p;
		switch (npc)
		{
			case playerbot_guild_lfg::NPC_SMITH: p = services.blacksmith; break;
			case playerbot_guild_lfg::NPC_ARMOUR: p = services.armourMerchant; break;
			case playerbot_guild_lfg::NPC_MISC: p = services.miscMerchant; break;
			case playerbot_guild_lfg::NPC_STORE: p = services.storekeeper; break;
			case playerbot_guild_lfg::NPC_WEAPON: p = services.weaponMerchant; break;
			default: p = services.skillReset; break;
		}
		const int* side = kSide[bot->GetPlayerID() % 8];
		e.map = m1;
		e.spotX = p.x + side[0] * PLAYERBOT_GLFG_SPOT_RADIUS / 200;
		e.spotY = p.y + side[1] * PLAYERBOT_GLFG_SPOT_RADIUS / 200;
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(m1);
		PIXEL_POSITION safe;
		if (navigation.Init(m1) && navigation.FindNearestWalkableWorld(e.spotX, e.spotY, 12, safe, bot->GetPlayerID()))
		{
			e.spotX = safe.x;
			e.spotY = safe.y;
		}
		e.place.npc = npc;
		e.place.village = GetPlayerBotTownName(m1);
		return true;
	}

	// The yes: to the NPC in the first village, out of a weak guild, and the
	// wait begins. False when the bot cannot come after all (it has said so).
	bool AcceptPlayerBotGuildLfg(LPCHARACTER bot, TPlayerBotGuildLfg& e, const TPlayerBotConvPerson& person)
	{
		const DWORD botPID = bot->GetPlayerID();
		const DWORD dwNow = get_dword_time();
		TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(botPID);
		CGuild* theirs = CGuildManager::instance().FindGuild(e.guildID);
		if (st == s_mapPlayerBotAIStates.end() || !theirs)
		{
			EndPlayerBotGuildLfg(botPID, "gone", GLFG_LINE_NONE);
			return false;
		}
		TPlayerBotAIState& state = st->second;
		const char* refusal = GetPlayerBotLfgRefusal(bot, state, dwNow);
		if (!refusal && person.local && (person.local->GetGuild() != theirs || !CanPlayerBotGuildLfgPersonInvite(person.local, theirs)))
			refusal = "person_left_guild";
		const int freedom = refusal ? 0 : GetPlayerBotGuildLfgFreedom(bot, theirs, e.relaxed);
		if (!refusal && freedom == 0)
			refusal = bot->GetGuild() == theirs ? "already_member" : "own_guild";
		if (!refusal && !PlacePlayerBotGuildLfgSpot(bot, e, person.local))
			refusal = "no_m1";
		if (refusal)
		{
			sys_log(0, "PLAYERBOT_GUILD_LFG: yes refused pid=%u name=%s person=%s reason=%s", botPID, bot->GetName(),
					e.personName.c_str(), refusal);
			EndPlayerBotGuildLfg(botPID, refusal, GLFG_LINE_CANT_COME);
			return false;
		}
		const bool sameMap = bot->GetMapIndex() == e.map;
		const int distance = sameMap ? DISTANCE_APPROX(bot->GetX() - e.spotX, bot->GetY() - e.spotY) : INT_MAX;
		state.dwTargetVID = 0;
		bot->SetVictim(NULL);
		ClearPlayerBotRoute(state, true);
		if (distance > PLAYERBOT_GLFG_WALK_RANGE)
		{
			if (!TransitionPlayerBotMap(bot, state, e.map, e.spotX, e.spotY, dwNow, "guild_lfg") || bot->GetMapIndex() != e.map)
			{
				sys_log(0, "PLAYERBOT_GUILD_LFG: move refused pid=%u name=%s to_map=%ld", botPID, bot->GetName(), e.map);
				EndPlayerBotGuildLfg(botPID, "move_refused", GLFG_LINE_CANT_COME);
				return false;
			}
			e.walking = false;
		}
		else
			e.walking = true;
		// The engine's invitation is refused to anybody in a guild: a weak
		// one is left now, as the whispered recruit does
		// (HandlePlayerBotGuildRecruitWhisper).
		if (freedom == 2 && bot->GetGuild())
		{
			sys_log(0, "PLAYERBOT_GUILD_LFG: leaves a weak guild pid=%u name=%s from=%s level=%u members=%d to=%s",
					botPID, bot->GetName(), bot->GetGuild()->GetName(), (unsigned int)bot->GetGuild()->GetLevel(),
					bot->GetGuild()->GetMemberCount(), theirs->GetName());
			bot->GetGuild()->RequestRemoveMember(botPID);
		}
		NotePlayerBotAwaitingGuildInvite(botPID, e.personPID);
		const int personChannel = person.Channel();
		e.place.channel = personChannel > 0 && personChannel != (int)g_bChannel ? (int)g_bChannel : 0;
		e.phase = GLFG_PHASE_WAITING;
		e.acceptedAt = dwNow;
		e.notedAt = dwNow;
		e.waitUntil = dwNow + playerbot_guild_lfg::WAIT_MS + (e.walking ? PLAYERBOT_GLFG_WALK_EXTRA_MS : 0);
		state.dwLastMeaningfulActivityTime = dwNow;
		SetPlayerBotAction(state, e.walking ? BOT_ACTION_TRAVEL : BOT_ACTION_IDLE, dwNow);
		++s_uPlayerBotGuildLfgAccepted;
		playerbot_conv::TRng rng = MakePlayerBotLfgRng();
		const std::string line = playerbot_guild_lfg::MeetLine(rng, MakePlayerBotGuildLfgFacts(bot, e), e.place, e.walking);
		SayPlayerBotLfgLine(bot, e.personPID, line, 300 + number(0, 700));
		sys_log(0, "PLAYERBOT_GUILD_LFG: yes pid=%u name=%s level=%u person=%s guild=%s map=%ld npc=%d spot=(%ld,%ld) by=%s text=\"%s\"",
				botPID, bot->GetName(), bot->GetLevel(), e.personName.c_str(), theirs->GetName(), e.map, e.place.npc,
				e.spotX, e.spotY, e.walking ? "walk" : "teleport", line.c_str());
		return true;
	}

	// A whisper from the person to a bot that offered or waits: the yes, the
	// no, "gdzie jestes?". Anything else is the conversation's.
	bool HandlePlayerBotGuildLfgWhisper(DWORD personPID, const char* personName, LPCHARACTER bot, const char* text)
	{
		(void)personName;
		if (!personPID || !bot || !text || !*text)
			return false;
		std::map<DWORD, TPlayerBotGuildLfg>::iterator it = s_mapPlayerBotGuildLfg.find(bot->GetPlayerID());
		if (it == s_mapPlayerBotGuildLfg.end() || it->second.personPID != personPID || it->second.noGuild ||
				it->second.phase == GLFG_PHASE_DUE)
			return false;
		TPlayerBotGuildLfg& e = it->second;
		playerbot_conv::TTokens t;
		playerbot_conv::Normalize(text, t);
		const int yn = playerbot_guild_lfg::ParseYesNo(t);
		playerbot_conv::TRng rng = MakePlayerBotLfgRng();
		if (e.phase == GLFG_PHASE_OFFERED)
		{
			if (yn > 0)
			{
				TPlayerBotConvPerson person;
				FindPlayerBotConvPerson(personPID, person);
				AcceptPlayerBotGuildLfg(bot, e, person);
				return true;
			}
			if (yn < 0)
			{
				EndPlayerBotGuildLfg(bot->GetPlayerID(), "declined", number(1, 100) <= 70 ? GLFG_LINE_DECLINE : GLFG_LINE_NONE);
				return true;
			}
			return false;
		}
		// Waiting.
		if (yn < 0)
		{
			EndPlayerBotGuildLfg(bot->GetPlayerID(), "declined_waiting", GLFG_LINE_DECLINE);
			return true;
		}
		if (yn > 0 || playerbot_guild_lfg::AsksWhere(t))
		{
			const playerbot_lfg::TFacts f = MakePlayerBotGuildLfgFacts(bot, e);
			SayPlayerBotLfgLine(bot, personPID, yn > 0 ? playerbot_guild_lfg::AlreadyLine(rng, f, e.place)
					: playerbot_guild_lfg::WhereLine(rng, f, e.place), 300 + number(0, 600));
			return true;
		}
		return false;
	}

	// ------------------------------------------------------------- the wait

	// The bot's part of the tick while it waits by the NPC: to its spot, and
	// it stands there. Moved off the village by something with the better
	// claim, it says so and goes.
	bool ManagePlayerBotGuildLfgWait(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return false;
		std::map<DWORD, TPlayerBotGuildLfg>::iterator it = s_mapPlayerBotGuildLfg.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotGuildLfg.end() || it->second.phase != GLFG_PHASE_WAITING || ch->IsDead())
			return false;
		TPlayerBotGuildLfg& e = it->second;
		if (ch->GetMapIndex() != e.map)
		{
			EndPlayerBotGuildLfg(ch->GetPlayerID(), "moved_away", GLFG_LINE_CALLED_AWAY);
			return false;
		}
		if (HandlePostDeathRecovery(ch, state, dwNow))
			return true;
		UseHealthPotion(ch, state, dwNow);
		UseManaPotion(ch, state, dwNow);
		state.dwLastMeaningfulActivityTime = dwNow;
		state.lLastX = ch->GetX();
		state.lLastY = ch->GetY();
		state.dwTargetVID = 0;
		const int distance = DISTANCE_APPROX(ch->GetX() - e.spotX, ch->GetY() - e.spotY);
		if (distance > PLAYERBOT_GLFG_STAY_DISTANCE)
		{
			MovePlayerBot(ch, e.spotX, e.spotY, dwNow, 6, true, true, false, false);
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			return true;
		}
		if (e.walking)
		{
			e.walking = false;
			sys_log(0, "PLAYERBOT_GUILD_LFG: arrived pid=%u name=%s walk_s=%u", ch->GetPlayerID(), ch->GetName(),
					(dwNow - e.acceptedAt) / 1000);
		}
		if (!state.vecRoute.empty())
			ClearPlayerBotRoute(state, true);
		if (ch->IsStateMove())
			ch->Stop();
		if (ch->IsRiding())
			SetPlayerBotRidingForTravel(ch, state, false, dwNow, "guild_lfg_wait");
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// ------------------------------------------------------- the world tick

	void ManagePlayerBotGuildLfg(DWORD dwNow)
	{
		if (dwNow - s_dwPlayerBotGuildLfgPruneAt >= PLAYERBOT_GLFG_PRUNE_MS)
		{
			s_dwPlayerBotGuildLfgPruneAt = dwNow;
			for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotGuildLfgCalls.begin(); it != s_mapPlayerBotGuildLfgCalls.end(); )
			{
				if (dwNow - it->second > PLAYERBOT_GLFG_PERSON_GAP_MS)
					s_mapPlayerBotGuildLfgCalls.erase(it++);
				else
					++it;
			}
			for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotGuildLfgBotAt.begin(); it != s_mapPlayerBotGuildLfgBotAt.end(); )
			{
				if (dwNow - it->second > PLAYERBOT_GLFG_BOT_GAP_MS)
					s_mapPlayerBotGuildLfgBotAt.erase(it++);
				else
					++it;
			}
			if (s_uPlayerBotGuildLfgCalls)
				sys_log(0, "PLAYERBOT_GUILD_LFG: stats calls=%u offers=%u accepted=%u joined=%u open=%u", s_uPlayerBotGuildLfgCalls,
						s_uPlayerBotGuildLfgOffers, s_uPlayerBotGuildLfgAccepted, s_uPlayerBotGuildLfgJoined,
						(unsigned int)s_mapPlayerBotGuildLfg.size());
		}
		if (s_mapPlayerBotGuildLfg.empty())
			return;
		std::vector<std::pair<DWORD, int> > ends;
		std::vector<const char*> reasons;
		for (std::map<DWORD, TPlayerBotGuildLfg>::iterator it = s_mapPlayerBotGuildLfg.begin(); it != s_mapPlayerBotGuildLfg.end(); ++it)
		{
			const DWORD botPID = it->first;
			TPlayerBotGuildLfg& e = it->second;
			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(botPID);
			TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(botPID);
			TPlayerBotConvPerson person;
			const bool personHere = FindPlayerBotConvPerson(e.personPID, person);
			if (!bot || st == s_mapPlayerBotAIStates.end())
			{
				ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_NONE));
				reasons.push_back("bot_gone");
				continue;
			}
			if (!personHere)
			{
				ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_NONE));
				reasons.push_back("person_gone");
				continue;
			}
			// In the person's guild: invited (AcceptPlayerBotGuildInvite took it).
			if (!e.noGuild && e.phase != GLFG_PHASE_DUE && bot->GetGuild() && bot->GetGuild()->GetID() == e.guildID)
			{
				++s_uPlayerBotGuildLfgJoined;
				ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_JOINED));
				reasons.push_back("joined_guild");
				continue;
			}
			switch (e.phase)
			{
				case GLFG_PHASE_DUE:
				{
					if ((int)(dwNow - e.dueAt) < 0)
						break;
					const char* refusal = GetPlayerBotLfgRefusal(bot, st->second, dwNow);
					if (!refusal && !person.local)
						refusal = "person_away";
					if (!refusal && person.local->IsBlockMode(BLOCK_WHISPER))
						refusal = "block_whisper";
					if (!refusal && !e.noGuild)
					{
						CGuild* theirs = CGuildManager::instance().FindGuild(e.guildID);
						if (!theirs || GetPlayerBotGuildLfgFreedom(bot, theirs, e.relaxed) == 0)
							refusal = "guild_changed";
					}
					if (refusal)
					{
						ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_NONE));
						reasons.push_back(refusal);
						break;
					}
					playerbot_conv::TRng rng = MakePlayerBotLfgRng();
					const playerbot_lfg::TFacts f = MakePlayerBotGuildLfgFacts(bot, e);
					const std::string text = e.noGuild ? playerbot_guild_lfg::NoGuildLine(rng, f)
							: playerbot_guild_lfg::OfferLine(rng, f, bot->GetGuild() == NULL);
					s_mapPlayerBotGuildLfgBotAt[botPID] = dwNow;
					if (!SayPlayerBotLfgLine(bot, e.personPID, text, 0))
					{
						ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_NONE));
						reasons.push_back("unsaid");
						break;
					}
					sys_log(0, "PLAYERBOT_GUILD_LFG: %s pid=%u name=%s level=%u guild=%s person=%s text=\"%s\"",
							e.noGuild ? "no_guild_told" : "offered", botPID, bot->GetName(), bot->GetLevel(),
							bot->GetGuild() ? bot->GetGuild()->GetName() : "-", e.personName.c_str(), text.c_str());
					if (e.noGuild)
					{
						ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_NONE));
						reasons.push_back("no_guild_told");
						break;
					}
					++s_uPlayerBotGuildLfgOffers;
					e.phase = GLFG_PHASE_OFFERED;
					e.offeredAt = dwNow;
					break;
				}
				case GLFG_PHASE_OFFERED:
					if (dwNow - e.offeredAt > playerbot_guild_lfg::OFFER_TTL_MS + PLAYERBOT_GLFG_OFFER_SLACK_MS)
					{
						ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_NONE));
						reasons.push_back("lapsed");
					}
					break;
				case GLFG_PHASE_WAITING:
					if (bot->GetGuild())
					{
						// Somebody else's invitation came first.
						ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_OTHER_GUILD));
						reasons.push_back("other_guild");
						break;
					}
					if ((int)(dwNow - e.waitUntil) >= 0)
					{
						ends.push_back(std::make_pair(botPID, (int)GLFG_LINE_TIMEOUT));
						reasons.push_back("timeout");
						break;
					}
					// The bot masters keep off it while it waits (the note
					// lapses in five minutes on its own).
					if (dwNow - e.notedAt >= PLAYERBOT_GLFG_NOTE_MS)
					{
						e.notedAt = dwNow;
						NotePlayerBotAwaitingGuildInvite(botPID, e.personPID);
					}
					break;
				default:
					break;
			}
		}
		for (size_t i = 0; i < ends.size(); ++i)
			EndPlayerBotGuildLfg(ends[i].first, reasons[i], ends[i].second);
	}

	// The line over the bot's head while it waits (playerbot_status.h).
	inline bool BuildPlayerBotGuildLfgStatus(LPCHARACTER ch, const char* prefix, char* status, size_t statusSize, bool en)
	{
		if (!ch || !status || statusSize == 0)
			return false;
		std::map<DWORD, TPlayerBotGuildLfg>::const_iterator it = s_mapPlayerBotGuildLfg.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotGuildLfg.end() || it->second.phase != GLFG_PHASE_WAITING)
			return false;
		snprintf(status, statusSize, PBT(en, "%sCzekam na zaproszenie do gildii od %s", "%sWaiting for %s's guild invitation"),
				prefix ? prefix : "", it->second.personName.c_str());
		return true;
	}
}

#endif
