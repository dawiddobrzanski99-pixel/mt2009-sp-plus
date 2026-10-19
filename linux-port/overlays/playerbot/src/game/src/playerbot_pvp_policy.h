#ifndef PLAYERBOT_PVP_POLICY_H
#define PLAYERBOT_PVP_POLICY_H

#include <cstdint>
#include <map>
#include "playerbot_duel_rules.h"

// A challenge to a duel. Human challenges remain pending through preparation
// and ready chat; autonomous bot challenges retain their existing acceptance.
//
// CPVPManager::Insert is a two-sided agreement: the first call makes the CPVP
// and tells the victim "%s challenged you to a battle", the second call from
// the other side reaches Agree() and the fight begins. A player types /pvp
// <vid>; a bot has no client to type it back, so a challenge to a bot simply
// sat there unanswered for ever.
//
// The engine's side only records that a bot was challenged (playerbotify.py
// puts the call at the end of Insert, which is reached exactly once per new
// duel - the branch above it returns early when the pair already exists). The
// bot's own tick calls Insert back, which is what the player's second /pvp
// would have been.
//
// The timestamp is taken by the AI, not here: the wait before a bot agrees is
// a matter of how a bot behaves, and the engine has no business knowing about
// it. Zero means "seen for the first time on the next tick".
//
// Included from an engine translation unit as well as from the overlay, so
// everything is inline and nothing of the engine is dragged in. Same shape as
// playerbot_offline_policy.h and playerbot_party_policy.h.
namespace playerbot_pvp {

struct Challenge
{
	uint32_t challengerPid;
	uint32_t seenAt;
	playerbot_duel::Phase phase = playerbot_duel::Phase::React;
	uint32_t reactAt = 0, readyAt = 0, nextMove = 0, nextItem = 0;
	bool playerReady = false, reminded = false, alchemyStarted = false, reserveLogged = false;
	int desiredRange = 0, threat = 0, budget = 0;
	long originX = 0, originY = 0, map = 0;
	playerbot_duel::StealthPlan stealthPlan = playerbot_duel::StealthPlan::None;
	bool setupMoveDone = false;
	uint32_t setupMoveUntil = 0;
	// MT2009_PLUS_BOT_DUEL_AI_V1: a bot challenged by another bot through the
	// prepared path; the challenger answers the ready chat itself (answerAt).
	bool botChallenger = false;
	uint32_t answerAt = 0;
};

inline std::map<uint32_t, Challenge> challenges;
// MT2009_PLUS_BOT_DUEL_AI_V1: the challenging bot's own preparation, keyed by
// the challenger; challengerPid holds the bot it challenged.
inline std::map<uint32_t, Challenge> botSides;

// Called from the engine for a bot that was just challenged. Keep one pending
// preparation per bot: another person must not steal its ready handshake.
inline void NoteChallenge(uint32_t challengerPid, uint32_t botPid)
{
	if (!challengerPid || !botPid || challengerPid == botPid)
		return;
	// One pending pair per bot. A new person cannot steal an ongoing preparation.
	if (challenges.count(botPid)) return;
	Challenge& challenge = challenges[botPid];
	challenge.challengerPid = challengerPid;
	challenge.seenAt = 0;
}

// Called from the bot's tick. Returns the challenger and stamps the moment the
// bot first saw it, so the caller can let the agreed pause run before agreeing.
inline bool PeekChallenge(uint32_t botPid, uint32_t& challengerPid, uint32_t& seenAt, uint32_t now)
{
	std::map<uint32_t, Challenge>::iterator it = challenges.find(botPid);
	if (it == challenges.end())
		return false;
	if (it->second.seenAt == 0)
		it->second.seenAt = now;
	challengerPid = it->second.challengerPid;
	seenAt = it->second.seenAt;
	return true;
}

inline void Forget(uint32_t botPid)
{
	challenges.erase(botPid);
}
inline bool NoteReady(uint32_t botPid,uint32_t senderPid) {
	auto it=challenges.find(botPid);
	if(it==challenges.end() || it->second.challengerPid!=senderPid) return false;
	it->second.playerReady=true;
	return true;
}
inline bool PreparationExpired(const Challenge& c,uint32_t now) {
	return c.readyAt ? now-c.readyAt>playerbot_duel::readyTimeout :
		c.seenAt && now-c.seenAt>playerbot_duel::prepareTimeout;
}

// How long this bot believes it is in an agreed duel.
//
// The engine knows the answer (CPVPManager::IsFighting), but on this line that
// method sits behind ENABLE_NEWSTUFF and the overlay is shared with an engine
// that may not define it at all - so asking it would be a compile-time gamble
// for a fact the bot can simply remember. Set when the bot agrees, cleared when
// it dies or the bound runs out; read by the health-potion pass, because the
// operator's rule is that a duel is fought without drinking.
struct Duel
{
	uint32_t opponentPid;
	uint32_t until;
	bool prepared = false, alchemyStarted = false;
	uint32_t nextDecision = 0, nextMove = 0, moveUntil = 0, nextChase = 0;
	uint32_t openingSkill = 0;
	uint32_t chargeUntil = 0, meleeUntil = 0, nextTrace = 0;
	uint32_t lastWeaponAt = 0, nextOpponentCheck = 0, dispelAt = 0, nextBuffCheck = 0;
	unsigned weaponChain = 0;
	bool opponentBuff = false;
	int observedHP = 0;
	uint32_t lastDamagedAt = 0;
	bool stealthOpening = false;
	playerbot_duel::SkillHitSequence skillHits;
	// MT2009_PLUS_BOT_DUEL_AI_V1: a prepared bot-v-bot duel; the challenged
	// side (botOwner) is the one counted in the census.
	bool botPair = false, botOwner = false;
};

inline std::map<uint32_t, Duel> duels;
struct Result { unsigned wins=0, losses=0, draws=0; int streak=0, last=0; };
inline std::map<std::pair<uint32_t,uint32_t>, Result> history;
inline void RecordResult(uint32_t bot,uint32_t foe,int outcome) {
	const auto key=std::make_pair(bot,foe);
	if (!history.count(key) && history.size()>=2048) history.erase(history.begin());
	auto& r=history[key]; r.last=outcome;
	if(outcome>0) {++r.wins;r.streak=0;} else if(outcome<0) {++r.losses;r.streak=std::min(r.streak+1,2);} else ++r.draws;
}

// No duel is assumed to last longer than this (PLAYERBOT_PVP_DUEL_ASSUMED is
// three minutes); a deadline further ahead is none.
inline constexpr uint32_t kDuelMaxMs = 60u * 60u * 1000u;

// Whether a duel's deadline is still ahead of now. It is get_dword_time() plus
// the assumed length, a 32-bit clock that wraps after 49.7 days: `now >= until`
// ended a duel agreed in the last minutes before the wrap at once. The
// difference survives the wrap, and the bound keeps an entry nothing read for
// weeks - a bot gone in the middle of a duel and back a month later - from
// reading as ahead again, which a signed difference alone would do.
inline bool DuelStands(uint32_t until, uint32_t now)
{
	const uint32_t ahead = until - now;
	return ahead != 0 && ahead <= kDuelMaxMs;
}

inline void NoteDuelStarted(uint32_t botPid, uint32_t opponentPid, uint32_t until)
{
	if (!botPid)
		return;
	Duel& duel = duels[botPid];
	duel = Duel{};
	duel.opponentPid = opponentPid;
	duel.until = until;
}

inline bool IsInDuel(uint32_t botPid, uint32_t now)
{
	std::map<uint32_t, Duel>::iterator it = duels.find(botPid);
	if (it == duels.end())
		return false;
	if (!DuelStands(it->second.until, now))
	{
		// The manager must still see a prepared duel to clean its engine pair,
		// temporary alchemy and target after an expiry.
		if (!it->second.prepared) duels.erase(it);
		return false;
	}
	return true;
}

// Who this bot agreed to fight, or zero.
//
// Knowing that a duel is on was enough while the only thing the AI did about
// one was stop drinking. It is not enough to fight: every road to a target -
// the collector, the engaged finder, the party focus, the held target - asks
// for IsMonster() or IsStone(), so a bot that had just agreed to a duel had
// nobody it was allowed to hit and stood there. Measured on our own world:
// twenty agreements, zero blows, and a player reporting that the bot accepted
// and then ignored him. The opponent is therefore remembered with the
// deadline, and the tick makes it the target the way a monster would be.
inline uint32_t GetDuelOpponent(uint32_t botPid, uint32_t now)
{
	std::map<uint32_t, Duel>::iterator it = duels.find(botPid);
	if (it == duels.end())
		return 0;
	if (!DuelStands(it->second.until, now))
	{
		if (!it->second.prepared) duels.erase(it);
		return 0;
	}
	return it->second.opponentPid;
}

inline void EndDuel(uint32_t botPid)
{
	duels.erase(botPid);
}

} // namespace playerbot_pvp

#endif
