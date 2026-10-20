#ifndef CUSTOM_MARMUR_CZARNY_ORK_V1_H
#define CUSTOM_MARMUR_CZARNY_ORK_V1_H
// MT2009_NASZE_MARMUR_CZARNY_ORK_V1: Marmur Czarnego Orka (70108) z metinow 40+.
// Dolina Orkow (mapa 64): 1%, pozostale mapy: 0.5%. Wielkanocne metiny bez dropu.
// Stala szansa, bez skalowania bonusami dropu i roznica poziomow.
namespace custom_marmur_czarny_ork
{
	static const DWORD ItemVnum = 70108;
	static const DWORD RaceVnum = 636; // Czarny Ork
	static const long ValleyMap = 64;  // map_n_threeway, Dolina Orkow

	// Szansa w 1/10000; 0 = brak dropu.
	static int ChancePer10000(LPCHARACTER victim, long baseMap)
	{
		if (!victim || !victim->IsStone() || victim->GetLevel() < 40)
			return 0;
		const DWORD race = victim->GetRaceNum();
		if (race >= 8041 && race <= 8050) // Wielkanocne Metiny
			return 0;
		return baseMap == ValleyMap ? 100 : 50;
	}
}
#endif
