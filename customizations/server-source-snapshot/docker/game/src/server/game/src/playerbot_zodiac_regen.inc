// MT2009_PLUS_ZODIAC_V1: Swiatynia Zodiaku (mapa 358) - Autor: Digi Rasta (nowy-system 0.35.0, na podstawie
// paczki WLsj24 "ZodiacTemple" 2.1-3.0, metin2.dev). Plik nowy, poza plikami silnika; wpiecie: server-patches/zodiak
// (edits.json), README tamze. Wszystko w #ifdef ENABLE_12ZI (definiuje je ostatnia zmiana edits.json).
// ZODIAK: dolaczane z regen.cpp (hak zodiak_haki.py); korzysta ze statycznych funkcji regen.cpp
#include "playerbot_zodiac_temple.h"

EVENTINFO(zodiac_regen_event_info)
{
	LPREGEN 	regen;
	CZodiac::IdType zodiac_id;

	zodiac_regen_event_info()
	: regen( 0 )
	, zodiac_id( 0 )
	{
	}
};

static bool read_line_zodiac(FILE *fp, LPREGEN regen)
{
	char szTmp[256];

	int mode = MODE_TYPE;
	int tmpTime;
	DWORD i;

	while (get_word(fp, szTmp))
	{
		if (!strncmp(szTmp, "//", 2))
		{
			next_line(fp);
			continue;
		}

		switch (mode)
		{
			case MODE_TYPE:
				if (szTmp[0] == 'm')
					regen->type = REGEN_TYPE_MOB;
				else if (szTmp[0] == 'g')
				{
					regen->type = REGEN_TYPE_GROUP;

					if (szTmp[1] == 'a')
						regen->is_aggressive = true;
				}
				else if (szTmp[0] == 'e')
					regen->type = REGEN_TYPE_EXCEPTION;
				else if (szTmp[0] == 'r')
					regen->type = REGEN_TYPE_GROUP_GROUP;
				else if (szTmp[0] == 's')
					regen->type = REGEN_TYPE_ANYWHERE;
				else
				{
					sys_err("read_line_zodiac: unknown regen type %c", szTmp[0]);
					exit(1);
				}

				++mode;
				break;

			case MODE_SX:
				str_to_number(regen->sx, szTmp);
				++mode;
				break;

			case MODE_SY:
				str_to_number(regen->sy, szTmp);
				++mode;
				break;

			case MODE_EX:
				{
					int iX = 0;
					str_to_number(iX, szTmp);

					regen->sx -= iX;
					regen->ex = regen->sx + iX * 2;

					regen->sx *= 100;
					regen->ex *= 100;

					++mode;
				}
				break;

			case MODE_EY:
				{
					int iY = 0;
					str_to_number(iY, szTmp);

					regen->sy -= iY;
					regen->ey = regen->sy + iY * 2;

					regen->sy *= 100;
					regen->ey *= 100;

					++mode;
				}
				break;

			case MODE_Z_SECTION:
				str_to_number(regen->z_section, szTmp);

				// 익셉션 이면 나가주자.
				if (regen->type == REGEN_TYPE_EXCEPTION)
					return true;

				++mode;
				break;

			case MODE_DIRECTION:
				str_to_number(regen->direction, szTmp);
				++mode;
				break;

			case MODE_REGEN_TIME:
				regen->time = 0;
				tmpTime = 0;

				for (i = 0; i < strlen(szTmp); ++i)
				{
					switch (szTmp[i])
					{
						case 'h':
							regen->time += tmpTime * 3600;
							tmpTime = 0;
							break;

						case 'm':
							regen->time += tmpTime * 60;
							tmpTime = 0;
							break;

						case 's':
							regen->time += tmpTime;
							tmpTime = 0;
							break;

						default:
							if (szTmp[i] >= '0' && szTmp[i] <= '9')
							{
								tmpTime *= 10;
								tmpTime += (szTmp[i] - '0');
							}
					}
				}

				++mode;
				break;

			case MODE_REGEN_PERCENT:
				++mode;
				break;

			case MODE_MAX_COUNT:
				regen->count = 0;
				str_to_number(regen->max_count, szTmp);
				++mode;
				break;

			case MODE_VNUM:
				str_to_number(regen->vnum, szTmp);
				++mode;
				break;

			case MODE_LEVEL:
				str_to_number(regen->level, szTmp);
				++mode;
				return true;
		}
	}

	return false;
}

static void regen_spawn_zodiac(LPREGEN regen, LPZODIAC pZodiac, bool bOnce)
{
	DWORD	num;
	DWORD	i;

	num = (regen->max_count - regen->count);

	if (!num)
		return;

	for (i = 0; i < num; ++i)
	{
		LPCHARACTER ch = NULL;

		if (regen->type == REGEN_TYPE_MOB)
		{
			ch = CHARACTER_MANAGER::Instance().SpawnMobRange(regen->vnum, regen->lMapIndex, regen->sx, regen->sy, regen->ex, regen->ey, true, false, false, regen->level);

			if (ch)
			{
				++regen->count;
				ch->SetZodiac(pZodiac);
			}
		}
		else if (regen->type == REGEN_TYPE_GROUP)
		{
			if (CHARACTER_MANAGER::Instance().SpawnGroupZodiac(regen->vnum, regen->lMapIndex, regen->sx, regen->sy, regen->ex, regen->ey, bOnce ? NULL : regen, regen->is_aggressive, pZodiac, regen->level))
				++regen->count;
		}
		else if (regen->type == REGEN_TYPE_GROUP_GROUP)
		{
			if (CHARACTER_MANAGER::Instance().SpawnGroupGroupZodiac(regen->vnum, regen->lMapIndex, regen->sx, regen->sy, regen->ex, regen->ey, bOnce ? NULL : regen, regen->is_aggressive, pZodiac, regen->level))
				++regen->count;
		}

		if (ch && !bOnce)
			ch->SetRegen(regen);
	}
}

EVENTFUNC(zodiac_regen_event)
{
	zodiac_regen_event_info* info = dynamic_cast<zodiac_regen_event_info*>( event->info );

	if ( info == NULL )
	{
		sys_err( "zodiac_regen_event> <Factor> Null pointer" );
		return 0;
	}

	LPZODIAC pZodiac = CZodiacManager::instance().Find(info->zodiac_id);
	if (pZodiac == NULL) {
		return 0;
	}

	LPREGEN	regen = info->regen;
	if (regen->time == 0)
	{
		regen->event = NULL;
	}

	regen_spawn_zodiac(regen, pZodiac, false);
	return PASSES_PER_SEC(regen->time);
}

bool regen_zodiac(const char* filename, long lMapIndex, int base_x, int base_y, LPZODIAC pZodiac, bool bOnce)
{
	if (g_bNoRegen)
		return true;

	if (lMapIndex >= 114 && lMapIndex <= 117)
		return true;

	LPREGEN regen = NULL;
	FILE* fp = fopen(filename, "rt");

	if (NULL == fp)
	{
		sys_err("SYSTEM: regen_zodiac: %s: file not found", filename);
		return false;
	}

	while (true)
	{
		REGEN tmp;

		memset(&tmp, 0, sizeof(tmp));

		if (!read_line_zodiac(fp, &tmp))
			break;

		if (tmp.type == REGEN_TYPE_MOB ||
			tmp.type == REGEN_TYPE_GROUP ||
			tmp.type == REGEN_TYPE_GROUP_GROUP ||
			tmp.type == REGEN_TYPE_ANYWHERE)
		{
			if (!bOnce)
			{
				regen = M2_NEW REGEN;
				memcpy(regen, &tmp, sizeof(REGEN));
			}
			else
				regen = &tmp;

			if (pZodiac)
				regen->is_aggressive = true;

			regen->lMapIndex = lMapIndex;
			regen->count = 0;

			regen->sx += base_x;
			regen->ex += base_x;

			regen->sy += base_y;
			regen->ey += base_y;

			if (regen->sx > regen->ex)
			{
				regen->sx ^= regen->ex;
				regen->ex ^= regen->sx;
				regen->sx ^= regen->ex;
			}

			if (regen->sy > regen->ey)
			{
				regen->sy ^= regen->ey;
				regen->ey ^= regen->sy;
				regen->sy ^= regen->ey;
			}

			if (regen->type == REGEN_TYPE_MOB)
			{
				const CMob * p = CMobManager::instance().Get(regen->vnum);

				if (!p)
				{
					sys_err("In %s, No mob data by vnum %u", filename, regen->vnum);
					if (!bOnce) {
						M2_DELETE(regen);
					}
					continue;
				}
			}

			if (!bOnce && pZodiac != NULL)
			{
				zodiac_regen_event_info* info = AllocEventInfo<zodiac_regen_event_info>();

				info->regen = regen;
				info->zodiac_id = pZodiac->GetId();

				regen->event = event_create(zodiac_regen_event, info, PASSES_PER_SEC(number(0, 16)) + PASSES_PER_SEC(regen->time));

				pZodiac->AddRegen(regen);
				// regen_id should be determined at this point,
				// before the call to CHARACTER::SetRegen()
			}

			// 처음엔 무조건 리젠 해준다.
			regen_spawn_zodiac(regen, pZodiac, bOnce);

		}
	}

	fclose(fp);
	return true;
}

