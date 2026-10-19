# Panel GM (F9) by Kiciamol.
#
# Klasyczne okno (Board + pasek tytulu), menu sekcji z lewej, tresc po prawej
# ukladana wierszami (naglowek, siatka przyciskow, wiersz pol), przewijana
# kolkiem i paskiem. Rozmiar okna: - / + na dole (cztery rozmiary), okno
# zawsze miesci sie na ekranie.
#
# MT2009_PLUS_GM_PANEL_V2: the new F9 panel, fitted to this client:
# - talks only with the commands our server has: the same /gmpanel_* as the
#   old panel (interfacemodule.GMPanelWindow, same answer formats, same
#   Set*Result names called by game.py) and plain GM commands of cmd.cpp
#   (/warp, /transfer, /stun, /advance, /purge, /priv_empire, ...);
# - the buttons are this client's own middle_button, stretched to the cell
#   (StretchButton), not a texture set the client does not have;
# - the texts are here (GMP_TEXTS) - localeinfo.py of this client has none
#   of them; a key localeinfo does have wins (T);
# - the lists it shares with the old panel (item categories, bonuses, AI
#   switches, the commands' list) are read from interfacemodule.py.
# interfacemodule.py builds it inside a try: a widget or a text this client
# lacks costs the new panel (the old one is built instead), never the game.
# Every deadline is clientclock.Now(): app.GetTime() starts again at every
# warp.

import clientclock
import net
import chat
import ui
import wndMgr
import localeInfo
import constInfo
import player

# The client's own button (61 x 21), stretched: both ends at their size, the
# middle column scaled to the width (ExpandedImageBox rendering rect).
CLASSIC_BUTTON = "d:/ymir work/ui/public/middle_button_0%d.sub"
CLASSIC_STATES = {"n": 1, "h": 2, "d": 3}

COLOR_TEXT = 0xffe6e6e6
COLOR_GOLD = 0xffffe08a
COLOR_LABEL = 0xffc9bfa7
COLOR_DIM = 0xff8f887a
COLOR_RED = 0xffff9f8a
COLOR_GREEN = 0xffa8e889

SIZES = [(600, 420), (680, 470), (820, 560), (980, 620)]
DEFAULT_SIZE = 1

MENU_WIDTH = 116
ROW_GAP = 4
BTN_H = 21
EDIT_H = 18
LINE_H = 16

REQUEST_TIMEOUT = 8.0


GMP_TEXTS = {
	'GMP_TITLE': 'Panel GM',
	'GMP_WINDOW_SIZE': 'Rozmiar okna:',
	'GMP_READY': 'Gotowe',
	'GMP_WAITING': 'Czekam na serwer...',
	'GMP_NO_ANSWER': 'Brak odpowiedzi serwera',
	'GMP_SENT': 'Wyslano: %s',
	'GMP_SAVED': 'Zapisano',
	'GMP_SAVED_OFFLINE': 'Zapisano (gracz offline)',
	'GMP_ERR': 'Blad: %s',
	'GMP_ON': 'WL',
	'GMP_OFF': 'WYL',
	'GMP_MENU_PLAYER': 'Gracz',
	'GMP_MENU_SELF': 'Ja (GM)',
	'GMP_MENU_WORLD': 'Swiat i eventy',
	'GMP_MENU_ITEMS': 'Przedmioty',
	'GMP_MENU_ACCOUNTS': 'Konta',
	'GMP_MENU_SPAWN': 'Spawn',
	'GMP_MENU_TELEPORT': 'Teleport',
	'GMP_MENU_SERVER': 'Serwer',
	'GMP_MENU_CMDS': 'Komendy GM',
	'GMP_NICK': 'Nick:',
	'GMP_SEARCH': 'Szukaj',
	'GMP_SEARCH_LABEL': 'Szukaj:',
	'GMP_SEARCH_BONUS': 'Szukaj bonusu:',
	'GMP_SEARCH_STONE': 'Szukaj kamienia:',
	'GMP_BACK': 'Wroc',
	'GMP_MY_TARGET': 'Moj cel',
	'GMP_SEARCHING': 'Szukam...',
	'GMP_FOUND': 'Znaleziono: %s',
	'GMP_NOT_FOUND': 'Nie ma takiej postaci',
	'GMP_ERR_BAD_NICK': 'Nieprawidlowy nick',
	'GMP_ERR_NO_NICK': 'Wpisz nick gracza',
	'GMP_ERR_NO_TARGET': 'Najpierw zaznacz gracza w grze',
	'GMP_ERR_NUMBER': 'Wpisz poprawna liczbe',
	'GMP_ERR_OFFLINE': 'Gracz jest offline',
	'GMP_ERR_NOT_ONLINE': 'Gracz nie jest online',
	'GMP_ERR_EQ_TARGET': 'Ekwipunek: kliknij gracza w grze i wybierz EQ',
	'GMP_ONLINE': 'Online',
	'GMP_OFFLINE_SINCE': 'Offline od %s',
	'GMP_INFO_MAP': 'Mapa: %s',
	'GMP_INFO_HPMP': 'PZ/PE: %s / %s',
	'GMP_INFO_YANG': 'Yang: %s',
	'GMP_INFO_ACCOUNT': 'Konto: %s',
	'GMP_INFO_STATS': 'SIL %s  WIT %s  ZR %s  INT %s',
	'GMP_INFO_POINTS': 'Pkt statusu %s, umiej. %s',
	'GMP_INFO_IP': 'IP: %s',
	'GMP_INFO_HORSE': 'Kon: poziom %s',
	'GMP_INFO_RANK': 'Ranga: %s',
	'GMP_INFO_EXP': 'Exp: %s',
	'GMP_JOB_WARRIOR': 'Wojownik',
	'GMP_JOB_NINJA': 'Ninja',
	'GMP_JOB_SURA': 'Sura',
	'GMP_JOB_SHAMAN': 'Szaman',
	'GMP_HDR_MOVE': 'Ruch',
	'GMP_GOTO_PLAYER': 'Teleport do',
	'GMP_SUMMON': 'Przyzwij',
	'GMP_STATE': 'Stan (czat)',
	'GMP_AFFECTS': 'Efekty (czat)',
	'GMP_HDR_CHAR': 'Postac',
	'GMP_VIEW_EQ': 'Podglad EQ',
	'GMP_GIVE_ITEM': 'Daj przedmiot',
	'GMP_SKILLS_M': 'Wszystkie na M1',
	'GMP_SKILLS_G': 'Wszystkie na G1',
	'GMP_SKILLS_P': 'Wszystkie na P',
	'GMP_VAL_YANG': 'Yang',
	'GMP_VAL_CASH': 'Smocze Monety',
	'GMP_VAL_LEVEL': 'Poziom',
	'GMP_VAL_RANK': 'Ranga',
	'GMP_VAL_HORSE': 'Poziom konia',
	'GMP_VAL_SKILLPT': '+ Pkt umiejetn.',
	'GMP_STAT_STR': 'Sila',
	'GMP_STAT_VIT': 'Witalnosc',
	'GMP_STAT_DEX': 'Zrecznosc',
	'GMP_STAT_INT': 'Inteligencja',
	'GMP_GIVE': 'Daj',
	'GMP_SET': 'Ustaw',
	'GMP_HDR_SKILLS': 'Umiejetnosci',
	'GMP_SKILLS_HINT': 'Wyszukaj gracza online, zeby zobaczyc umiejetnosci',
	'GMP_SKILLS_EDIT': 'Poziom: liczba 1-19, M1-M10, G1-G10 albo P',
	'GMP_SKILLS_NONE': 'Brak wyuczonych umiejetnosci',
	'GMP_SKILLS_OFFLINE': 'Umiejetnosci widac tylko u gracza online',
	'GMP_ERR_SKILL_LEVEL': 'Poziom: 1-19, M1-M10, G1-G10 albo P',
	'GMP_HDR_PUNISH': 'Kary',
	'GMP_MUTE_FOR': 'Wycisz na:',
	'GMP_MUTE': 'Wycisz',
	'GMP_UNMUTE': 'Odcisz',
	'GMP_STUN': 'Oglusz',
	'GMP_SLOW': 'Spowolnij',
	'GMP_KILL': 'Zabij...',
	'GMP_KICK': 'Wyrzuc...',
	'GMP_BAN_DOTS': 'Ban...',
	'GMP_Q_KILL': 'Zabic postac %s?',
	'GMP_Q_KICK': 'Wyrzucic %s z gry?',
	'GMP_HDR_ME': 'Moja postac',
	'GMP_INVISIBLE': 'Niewidzialnosc',
	'GMP_SPY': 'Tryb szpiega',
	'GMP_NO_COOLDOWN': 'Bez odnowienia',
	'GMP_IMMORTAL_ON': 'Niesmiertelnosc WL',
	'GMP_IMMORTAL_OFF': 'Niesmiertelnosc WYL',
	'GMP_FULL_HPMP': 'Pelne PZ/PE',
	'GMP_FULL_SET': 'Pelny set',
	'GMP_MAX_BONUS': 'Bonusy na max',
	'GMP_ALL_SKILLS': 'Wszystkie umiej. P',
	'GMP_CLEAR_MY_AFFECT': 'Zdejmij efekty',
	'GMP_HORSE_MAX': 'Kon na max',
	'GMP_REWARP': 'Przeladuj miejsce',
	'GMP_POLY': 'Polimorfia (vnum):',
	'GMP_POLY_ON': 'Zmien',
	'GMP_POLY_OFF': 'Wroc',
	'GMP_POLY_MARBLE': 'Daj marmur',
	'GMP_HDR_AROUND': 'Wokol mnie',
	'GMP_PURGE': 'Usun potwory',
	'GMP_PURGE_ALL': 'Usun wszystkie',
	'GMP_WEAKEN': 'Oslab potwory',
	'GMP_PULL': 'Przyciagnij',
	'GMP_MOB_COUNT': 'Policz potwory',
	'GMP_RESPAWN': 'Odrodz spawny',
	'GMP_HDR_NOTICE': 'Ogloszenie',
	'GMP_NOTICE_CHAT': 'Na czacie',
	'GMP_NOTICE_GM': 'Jako GM',
	'GMP_NOTICE_BIG': 'Duze',
	'GMP_NOTICE_MAP': 'Tylko ta mapa',
	'GMP_ERR_NO_TEXT': 'Wpisz tresc ogloszenia',
	'GMP_HDR_EVENTS': 'Eventy (bonus imperium)',
	'GMP_EV_EXP': 'Exp %',
	'GMP_EV_DROP': 'Drop %',
	'GMP_EV_YANG': 'Yang %',
	'GMP_EV_HOURS': 'Godz.',
	'GMP_EMPIRE_ALL': 'Wszystkie',
	'GMP_EMPIRE_SHINSOO': 'Shinsoo',
	'GMP_EMPIRE_CHUNJO': 'Chunjo',
	'GMP_EMPIRE_JINNO': 'Jinno',
	'GMP_EV_START': 'Wlacz event',
	'GMP_EV_STOP': 'Wylacz eventy',
	'GMP_EV_HINT': 'Procent dodatkowy, np. 100 = podwojnie. Puste/0 = bez zmian.',
	'GMP_EV_STARTED': 'Event wlaczony',
	'GMP_EV_STOPPED': 'Eventy wylaczone',
	'GMP_ERR_EVENT_EMPTY': 'Wpisz procent Exp, Drop albo Yang',
	'GMP_HDR_WORLD': 'Swiat',
	'GMP_NIGHT': 'Noc',
	'GMP_DAY': 'Dzien',
	'GMP_SNOW_ON': 'Snieg',
	'GMP_SNOW_OFF': 'Bez sniegu',
	'GMP_USERS': 'Gracze na kanale',
	'GMP_WHO': 'Liczba online',
	'GMP_END_DUELS': 'Koniec pojedynkow',
	'GMP_EVENT_FLAGS': 'Flagi eventow',
	'GMP_MAINT_ON': 'Przerwa techn...',
	'GMP_MAINT_OFF': 'Koniec przerwy',
	'GMP_Q_MAINT': 'Zablokowac nowe logowania (przerwa techniczna)?',
	'GMP_RESTART': 'Restart serwera...',
	'GMP_Q_RESTART': 'Zrestartowac serwer? Wszyscy zostana rozlaczeni.',
	'GMP_RESTART_OK': 'Restart zlecony',
	'GMP_CLEAR': 'Wyczysc',
	'GMP_CAT_STONES': 'Kamienie',
	'GMP_PICK_ITEM': 'Wybierz przedmiot',
	'GMP_PICK_BONUS': 'Wybierz bonus %d',
	'GMP_PICK_STONE': 'Wybierz kamien %d',
	'GMP_LOADING': 'Wczytuje...',
	'GMP_NO_RESULTS': 'Brak wynikow',
	'GMP_HDR_NEW_ITEM': 'Nowy przedmiot',
	'GMP_ITEM': 'Przedmiot:',
	'GMP_NO_ITEM': 'nie wybrano',
	'GMP_COUNT': 'Ilosc:',
	'GMP_FOR': 'Dla:',
	'GMP_PLACE_INV': 'Ekwipunek',
	'GMP_PLACE_SAFE': 'Magazyn',
	'GMP_PLACE_MALL': 'Magazyn IS',
	'GMP_HDR_BONUS': 'Bonusy (kliknij, zeby wybrac)',
	'GMP_BONUS_NONE': 'brak bonusu',
	'GMP_HDR_STONES': 'Kamienie',
	'GMP_EMPTY': 'pusty',
	'GMP_CREATE': 'Utworz przedmiot',
	'GMP_RESET_FORM': 'Wyczysc formularz',
	'GMP_ERR_NO_ITEM': 'Wybierz przedmiot z listy',
	'GMP_ITEM_CREATED': 'Przedmiot utworzony',
	'GMP_ERR_OWNER_OFFLINE': 'Odbiorca nie jest online',
	'GMP_ERR_BADVNUM': 'Nie ma takiego przedmiotu',
	'GMP_ERR_SAFEBOX': 'Odbiorca musi najpierw otworzyc magazyn',
	'GMP_ERR_MALL': 'Odbiorca musi najpierw otworzyc magazyn IS',
	'GMP_ERR_NOSPACE': 'Brak miejsca',
	'GMP_ACC_CHECK': 'Sprawdz konto',
	'GMP_ACC_STATUS': 'Konto: %s, blokada: %s',
	'GMP_HDR_BAN': 'Blokada konta',
	'GMP_DAYS': '%d dni',
	'GMP_BAN_DAYS': 'Dni:',
	'GMP_BAN_TEMP': 'Zablokuj na dni...',
	'GMP_BAN_PERM': 'Na zawsze...',
	'GMP_UNBAN': 'Odblokuj',
	'GMP_Q_BAN_TEMP': 'Zablokowac konto %s na %s dni?',
	'GMP_Q_BAN_PERM': 'Zablokowac konto %s NA ZAWSZE?',
	'GMP_KICK_ACC': 'Wyrzuc z gry...',
	'GMP_MUTE_LIST': 'Lista wyciszonych',
	'GMP_HDR_MUTE': 'Czat',
	'GMP_MUTE_10M': 'Wycisz 10 min',
	'GMP_MUTE_1H': 'Wycisz 1 h',
	'GMP_MUTE_1D': 'Wycisz 1 dzien',
	'GMP_HDR_GM': 'Ranga GM',
	'GMP_RANK_LOW': 'Low Wizard',
	'GMP_RANK_HIGH': 'High Wizard',
	'GMP_RANK_GOD': 'God',
	'GMP_RANK_IMPL': 'Implementor',
	'GMP_GM_ADD': 'Nadaj range',
	'GMP_GM_REMOVE': 'Odbierz GM...',
	'GMP_Q_GM_REMOVE': 'Odebrac range GM postaci %s?',
	'GMP_GM_HINT': 'Range innych zmienia tylko Implementor. Dziala od razu.',
	'GMP_GM_SAVED': 'Ranga zapisana',
	'GMP_HDR_BOTS': 'Boty',
	'GMP_BOT_PID': 'PID bota:',
	'GMP_PICK_DOTS': 'Wybierz...',
	'GMP_BOT_SPAWN': 'Przyzwij boty',
	'GMP_BOT_DESPAWN': 'Odeslij boty',
	'GMP_BOT_ACTIVE': 'Aktywne boty',
	'GMP_BOTS_DONE': 'Boty: %s z %s (razem %s)',
	'GMP_ERR_EMPIRE': 'Wybierz imperium',
	'GMP_HDR_MOBS': 'Potwory i metiny',
	'GMP_MOB': 'Potwor:',
	'GMP_METIN': 'Metin:',
	'GMP_SPAWN': 'Przyzwij',
	'GMP_SPAWNED': 'Przyzwano %s z %s',
	'GMP_ERR_NO_MOB': 'Nie ma takiego potwora',
	'GMP_LIST_AVAILBOTS': 'Wolne boty (kliknij, zeby wpisac PID)',
	'GMP_LIST_BOTS': 'Aktywne boty',
	'GMP_LIST_MOBS': 'Potwory',
	'GMP_LIST_METINS': 'Metiny',
	'GMP_CLOSE_LIST': 'Zamknij liste',
	'GMP_PICKED': 'Wybrano: %s',
	'GMP_HDR_QUICK': 'Szybki spawn (zwykle metiny, wszystkie bossy)',
	'GMP_QUICK_HINT': 'Pula... pokazuje bossow danego przedzialu',
	'GMP_BOSS_1': '1 boss',
	'GMP_BOSS_5': '5 bossow',
	'GMP_METIN_1': '1 metin',
	'GMP_METIN_3': '3 metiny',
	'GMP_POOL': 'Pula...',
	'GMP_TP_CITIES': 'Miasta',
	'GMP_TP_MAPS': 'Mapy',
	'GMP_TP_DUNGEONS': 'Lochy',
	'GMP_TP_SPECIAL': 'Specjalne',
	'GMP_TP_SHINSOO_1': 'Shinsoo M1',
	'GMP_TP_SHINSOO_2': 'Shinsoo M2',
	'GMP_TP_CHUNJO_1': 'Chunjo M1',
	'GMP_TP_CHUNJO_2': 'Chunjo M2',
	'GMP_TP_JINNO_1': 'Jinno M1',
	'GMP_TP_JINNO_2': 'Jinno M2',
	'GMP_TP_GVILLAGE_1': 'Wioska gildii 1',
	'GMP_TP_GVILLAGE_2': 'Wioska gildii 2',
	'GMP_TP_GVILLAGE_3': 'Wioska gildii 3',
	'GMP_TP_SEUNGRYONG': 'Dolina Seungryong',
	'GMP_TP_YONGBI': 'Pustynia Yongbi',
	'GMP_TP_SOHAN': 'Gora Sohan',
	'GMP_TP_FIRELAND': 'Kraina Ognia',
	'GMP_TP_GHOSTWOOD': 'Las Duchow',
	'GMP_TP_REDWOOD': 'Czerwony Las',
	'GMP_TP_GIANTS': 'Kraina Gigantow',
	'GMP_TP_WLPASS': 'Przelecz (wl_pass)',
	'GMP_TP_CAPE': 'Przyladek Smoczego Ognia',
	'GMP_TP_DAWNMIST': 'Las Porannej Mgly',
	'GMP_TP_BLACKSAND': 'Zatoka Czarnego Piasku',
	'GMP_TP_THUNDER': 'Gora Grzmotow',
	'GMP_TP_HWANG': 'Swiatynia Hwang',
	'GMP_TP_DEVILTOWER': 'Wieza Demonow',
	'GMP_TP_SPIDER1': 'Loch Pajakow 1',
	'GMP_TP_SPIDER2': 'Loch Pajakow 2',
	'GMP_TP_MONKEY_E': 'Loch Malp (latwy)',
	'GMP_TP_MONKEY_N': 'Loch Malp (normalny)',
	'GMP_TP_MONKEY_H': 'Loch Malp (trudny)',
	'GMP_TP_EXILE1': 'Grota Wygnania 1',
	'GMP_TP_EXILE2': 'Grota Wygnania 2',
	'GMP_TP_BERAN': 'Leze Beran-Setaou',
	'GMP_TP_CATACOMB': 'Katakumby Diabla',
	'GMP_TP_RAZADOR': 'Twierdza Razadora',
	'GMP_TP_PLUS': 'Nasze mapy',
	'GMP_TP_OCHAO': 'Swiatynia Ochao',
	'GMP_TP_ENCHANTED': 'Zaczarowany Las',
	'GMP_TP_CYCLOPS': 'Dolina Cyklopow',
	'GMP_TP_PHARAOH': 'Pustkowie Faraona',
	'GMP_TP_ATLANTIS': 'Ruiny Atlantydy',
	'GMP_TP_NEMERE': 'Leze Nemere',
	'GMP_TP_ZODIAC': 'Swiatynia Zodiaku',
	'GMP_TP_ICE': 'Lodowy loch',
	'GMP_TP_LABYRINTH': 'Labirynt',
	'GMP_TP_OX': 'Arena OX',
	'GMP_TP_WEDDING': 'Sala slubna',
	'GMP_TP_DUEL': 'Arena pojedynkow',
	'GMP_TP_WAR1': 'Wojna Imperiow 1',
	'GMP_TP_WAR2': 'Wojna Imperiow 2',
	'GMP_TP_WAR3': 'Wojna Imperiow 3',
	'GMP_TP_GMROOM': 'Pokoj GM',
	'GMP_GO': 'Idz',
	'GMP_TP_HINT': 'X/Y w metrach globalnych. Ctrl + klik na mapie = teleport.',
	'GMP_HDR_WAYPOINTS': 'Moje miejsca',
	'GMP_WP_EMPTY': '%d. pusty',
	'GMP_WP_SAVE': 'Zapisz tu',
	'GMP_HDR_RATES': 'Rate serwera (%)',
	'GMP_SAVE': 'Zapisz',
	'GMP_FETCH': 'Pobierz',
	'GMP_RATES_HINT': '1-10000, 100 = normalnie. Dziala od razu.',
	'GMP_ERR_RATE': 'Rate: liczba 1-10000',
	'GMP_HDR_AI': 'Zachowanie botow',
	'GMP_AI_WAIT': 'Pobieram ustawienia botow...',
	'GMP_AI_HINT': 'Zmiany dzialaja po kilku sekundach',
	'GMP_HDR_RESTART': 'Restart',
	'GMP_CMDS_HINT': 'Kliknij komende, zeby wypisac ja na czacie',
	'GM_PANEL_GM_SAVED': 'Zapisano. Odswiezanie rang GM...',
	'GM_PANEL_GM_PERMISSION': 'Tylko IMPLEMENTOR zmienia GM innych postaci.',
	'GM_PANEL_GM_SELF_NOTE': 'GM moze zabrac range sobie.',
	'GM_PANEL_GM_EMPTY': 'GM zabrany. Uwaga na nastepny start!',
	'GM_PANEL_GM_EMPTY_NOTE1': 'Lista GM jest pusta: nastepny start moze nadac',
	'GM_PANEL_GM_EMPTY_NOTE2': 'IMPLEMENTOR najstarszej postaci konta admin.',
	'GM_PANEL_GM_RESTART_UNKNOWN': 'GM zabrany. Nie sprawdzono przywrocenia po starcie.',
	'GM_PANEL_GM_NO_ANSWER': 'Brak odpowiedzi. Sprawdz range w panelu WWW.',
	'GM_PANEL_GM_TESTSERVER': 'Tryb test_server nadaje GM wszystkim.',
}


def T(key):
	text = getattr(localeInfo, key, None)
	if text is None:
		text = GMP_TEXTS.get(key, key)
	return text


def TF(key, *args):
	text = T(key)
	try:
		return text % args
	except Exception:
		return text


_textWidths = {}


def TextWidth(text):
	width = _textWidths.get(text)
	if width is None:
		try:
			line = ui.TextLine()
			line.SetText(text)
			width = line.GetTextSize()[0]
		except Exception:
			width = len(text) * 6
		_textWidths[text] = width
	return width


def SafeToken(text):
	return text.strip().replace(" ", "").replace("|", "")










SPAWN_TIERS = [
	("Lv 1-40",
		[5161, 591, 531, 532, 533, 534],
		[8001, 8002, 8003, 8004, 8028, 8005, 8006, 8007, 8008]),
	("Lv 41-70",
		[5162, 692, 691, 5163, 793, 2091, 791, 5002, 993, 794, 2191, 792],
		[8009, 8010, 8015, 8011, 8016, 8012, 8017, 8031, 8032, 8033, 8034, 8035, 8037, 8039, 8040, 8013, 8018, 8014, 8019]),
	("Lv 71-90",
		[2094, 2092, 1901, 1902, 2206, 2207, 1191, 2291, 1091, 1092, 1304, 1306, 1334, 1093, 2306, 1192, 2591, 2592, 2593, 2594, 2595, 2596, 2495],
		[8024, 8025, 8036, 8026, 8038, 8027]),
	("Lv 91-110",
		[2597, 2598, 2492, 1491, 2307, 2493, 1095, 1094, 1307, 693, 2093, 2192, 1903, 795, 796,
		 3090, 3190, 3290, 3390, 3490, 3590, 3690, 3790, 3890, 3910, 3911, 3912, 3913,
		 3091, 3191, 3291, 3391, 3491, 3591, 3595, 3596, 3691, 3791, 3891,
		 6151, 6191, 6091, 3901, 3902, 3903, 3905, 3906],
		[8051, 8052, 8053, 8054, 8055, 8056]),
]


# MT2009_PLUS_GM_PANEL_TP_MAPS_V1: only places this client can draw (Kiciamol,
# 9 October). The three guild villages, Cape Dragon Fire, Dawnmist Wood, Bay
# Black Sand, Mount Thunder and the ice dungeon have no map in our packs (the
# base packs, maps, gf_*, az_*, at_maps, zodiak_maps...): a warp there crashed
# the client or left the character stuck. Beran-Setaou's lair (maps), the
# Devil's Catacomb (catacomb_map) and Razador's (gf_razador) are in our packs
# and stay; the Catacomb's warp is its first floor's entry (the quest's base
# 3072 12032 + floor1_entry 73 63), not the map's corner (20, 20). Their names
# stay for the lookup's map names.
TELEPORT_GROUPS = [
	("GMP_TP_CITIES", [
		("GMP_TP_SHINSOO_1", 4743, 9548), ("GMP_TP_SHINSOO_2", 3584, 8704),
		("GMP_TP_CHUNJO_1", 659, 1556), ("GMP_TP_CHUNJO_2", 1455, 2400),
		("GMP_TP_JINNO_1", 9635, 2797), ("GMP_TP_JINNO_2", 8704, 2560),
	]),
	("GMP_TP_MAPS", [
		("GMP_TP_SEUNGRYONG", 2704, 7399), ("GMP_TP_YONGBI", 2219, 5027),
		("GMP_TP_SOHAN", 3752, 1749), ("GMP_TP_FIRELAND", 5978, 6222),
		("GMP_TP_GHOSTWOOD", 2901, 57), ("GMP_TP_REDWOOD", 11196, 700),
		("GMP_TP_GIANTS", 8277, 7634), ("GMP_TP_WLPASS", 6201, 11875),
	]),
	("GMP_TP_DUNGEONS", [
		("GMP_TP_HWANG", 5537, 1450), ("GMP_TP_DEVILTOWER", 1393, 8547),
		("GMP_TP_SPIDER1", 600, 4966), ("GMP_TP_SPIDER2", 7040, 4625),
		("GMP_TP_MONKEY_E", 7752, 4477), ("GMP_TP_MONKEY_N", 1352, 6525),
		("GMP_TP_MONKEY_H", 1352, 7293), ("GMP_TP_EXILE1", 100, 12078),
		("GMP_TP_EXILE2", 2413, 12754), ("GMP_TP_BERAN", 8453, 10742),
		("GMP_TP_CATACOMB", 3145, 12095), ("GMP_TP_RAZADOR", 7808, 6528),
		("GMP_TP_LABYRINTH", 6156, 12810),
	]),
	# MT2009_PLUS_GM_PANEL_TP_PLUS_V1 (the owner, 10 October): our own maps - the
	# server's /goto places (ochao, las, cyklopy, pustkowie, atlantyda, zodiac)
	# and Nemere's lair (map 352: its base 5120 1536 + Town.txt 171 270).
	("GMP_TP_PLUS", [
		("GMP_TP_OCHAO", 8537, 14164), ("GMP_TP_ENCHANTED", 3787, 3946),
		("GMP_TP_CYCLOPS", 2650, 3051), ("GMP_TP_PHARAOH", 2409, 3940),
		("GMP_TP_ATLANTIS", 38343, 22769), ("GMP_TP_NEMERE", 5291, 1806),
		("GMP_TP_ZODIAC", 3332, 14325),
	]),
	("GMP_TP_SPECIAL", [
		("GMP_TP_OX", 8965, 246), ("GMP_TP_WEDDING", 8223, 220),
		("GMP_TP_DUEL", 8574, 24), ("GMP_TP_WAR1", 9800, 1144),
		("GMP_TP_WAR2", 9344, 1664), ("GMP_TP_WAR3", 9856, 1664),
		("GMP_TP_GMROOM", 1052, 100),
	]),
]


STAT_ROWS = [("st", "GMP_STAT_STR"), ("ht", "GMP_STAT_VIT"), ("dx", "GMP_STAT_DEX"), ("iq", "GMP_STAT_INT")]

GM_RANKS = [("LOW_WIZARD", "GMP_RANK_LOW"), ("HIGH_WIZARD", "GMP_RANK_HIGH"), ("GOD", "GMP_RANK_GOD"), ("IMPLEMENTOR", "GMP_RANK_IMPL")]

BAN_DAYS = [1, 3, 7, 30]
MUTE_TIMES = [("10m", "GMP_MUTE_10M"), ("1h", "GMP_MUTE_1H"), ("24h", "GMP_MUTE_1D")]

EMPIRES = [("1", "GMP_EMPIRE_SHINSOO"), ("2", "GMP_EMPIRE_CHUNJO"), ("3", "GMP_EMPIRE_JINNO")]

SECTIONS = [
	("player", "GMP_MENU_PLAYER"),
	("self", "GMP_MENU_SELF"),
	("world", "GMP_MENU_WORLD"),
	("items", "GMP_MENU_ITEMS"),
	("accounts", "GMP_MENU_ACCOUNTS"),
	("spawn", "GMP_MENU_SPAWN"),
	("teleport", "GMP_MENU_TELEPORT"),
	("server", "GMP_MENU_SERVER"),
	("cmds", "GMP_MENU_CMDS"),
]







JOB_NAMES = ["GMP_JOB_WARRIOR", "GMP_JOB_NINJA", "GMP_JOB_SURA", "GMP_JOB_SHAMAN"]


def JobKeyOf(value):
	try:
		number = int(value)
	except Exception:
		return None
	if number < 0 or number >= 2 * len(JOB_NAMES):
		return None
	return JOB_NAMES[number % len(JOB_NAMES)]


MAP_NAMES = {
	1: "GMP_TP_SHINSOO_1", 3: "GMP_TP_SHINSOO_2", 21: "GMP_TP_CHUNJO_1", 23: "GMP_TP_CHUNJO_2",
	41: "GMP_TP_JINNO_1", 43: "GMP_TP_JINNO_2", 61: "GMP_TP_SOHAN", 62: "GMP_TP_FIRELAND",
	63: "GMP_TP_YONGBI", 64: "GMP_TP_SEUNGRYONG", 65: "GMP_TP_HWANG", 67: "GMP_TP_GHOSTWOOD",
	68: "GMP_TP_REDWOOD", 71: "GMP_TP_SPIDER2", 104: "GMP_TP_SPIDER1", 66: "GMP_TP_DEVILTOWER",
	69: "GMP_TP_WLPASS", 70: "GMP_TP_GIANTS", 72: "GMP_TP_EXILE1", 73: "GMP_TP_EXILE2",
	79: "GMP_TP_LABYRINTH", 81: "GMP_TP_WEDDING", 90: "GMP_TP_ICE", 112: "GMP_TP_DUEL",
	113: "GMP_TP_OX", 208: "GMP_TP_BERAN", 216: "GMP_TP_CATACOMB", 301: "GMP_TP_CAPE",
	302: "GMP_TP_DAWNMIST", 303: "GMP_TP_BLACKSAND", 304: "GMP_TP_THUNDER", 351: "GMP_TP_RAZADOR",
}
# MT2009_PLUS_GM_PANEL_V2: the maps this server has besides those above
# (T() returns a text that is not a key as it is).
MAP_NAMES.update({
	4: "Jungrang (M3)", 24: "Waryong (M3)", 44: "Imha (M3)", 209: "\x8cwi\xb9tynia Ochao",
	360: "Dolina Cyklop\xf3w", 361: "Pustkowie Faraona", 362: "Zaczarowany Las",
	363: "Biblioteka Wiedzy",
})





class StretchButton(ui.Window):
	CAP = 5

	def __init__(self):
		ui.Window.__init__(self)
		self.event = None
		self.args = ()
		self.on = False
		self.enabled = True
		self.fullText = ""
		self.color = COLOR_TEXT
		self.pressed = False
		self.state = None

		self.left = ui.ExpandedImageBox()
		self.mid = ui.ExpandedImageBox()
		self.right = ui.ExpandedImageBox()
		for part in (self.left, self.mid, self.right):
			part.SetParent(self)
			part.AddFlag("not_pick")
			part.Show()

		self.text = ui.TextLine()
		self.text.SetParent(self)
		self.text.AddFlag("not_pick")
		self.text.SetHorizontalAlignCenter()
		self.text.SetVerticalAlignCenter()
		self.text.Show()

		self.__SetState("n")
		self.SetSize(60, BTN_H)

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.event = None
		self.args = ()

	def __SetState(self, state):
		if self.on and state == "n":
			state = "d"
		if state == self.state:
			return
		self.state = state
		image = CLASSIC_BUTTON % CLASSIC_STATES.get(state, 1)
		for part in (self.left, self.mid, self.right):
			part.LoadImage(image)
		self.__Place()

	def __Place(self):
		(w, h) = (self.GetWidth(), self.GetHeight())
		imageW = max(1, self.left.GetWidth())
		imageH = max(1, self.left.GetHeight())
		cap = min(self.CAP, imageW // 2)
		scaleY = float(h) / imageH
		cut = float(imageW - cap) / imageW
		# left end: the picture's first CAP columns
		self.left.SetScale(1.0, scaleY)
		self.left.SetRenderingRect(0.0, 0.0, -cut, 0.0)
		self.left.SetPosition(0, 0)
		# right end: its last CAP columns, at the button's right edge
		self.right.SetScale(1.0, scaleY)
		self.right.SetRenderingRect(-cut, 0.0, 0.0, 0.0)
		self.right.SetPosition(w - imageW, 0)
		# the middle: the picture without its ends, scaled to w - 2 * CAP
		edge = float(cap) / imageW
		self.mid.SetScale(float(w) / imageW, scaleY)
		self.mid.SetRenderingRect(-edge, 0.0, -edge, 0.0)
		self.mid.SetPosition(0, 0)
		self.text.SetPosition(w // 2, h // 2)
		self.__FitText()

	def __FitText(self):
		limit = self.GetWidth() - 8
		text = self.fullText
		self.text.SetText(text)
		if limit <= 0 or not text:
			return
		if self.text.GetTextSize()[0] <= limit:
			return
		while len(text) > 1:
			text = text[:-1]
			self.text.SetText(text + "..")
			if self.text.GetTextSize()[0] <= limit:
				return

	def SetSize(self, width, height=BTN_H):
		ui.Window.SetSize(self, max(self.CAP * 2 + 2, width), height)
		if self.state:
			self.__Place()

	def SetText(self, text):
		self.fullText = text
		self.__FitText()

	def GetText(self):
		return self.fullText

	def SetTextColor(self, color):
		self.color = color
		self.__ApplyColor()

	def __ApplyColor(self):
		if not self.enabled:
			self.text.SetPackedFontColor(COLOR_DIM)
		elif self.on:
			self.text.SetPackedFontColor(COLOR_GOLD)
		else:
			self.text.SetPackedFontColor(self.color)

	def SetOn(self, on):
		if self.on == bool(on) and self.state is not None:
			return
		self.on = bool(on)
		self.state = None
		self.__SetState("d" if self.on else "n")
		self.__ApplyColor()

	def IsOn(self):
		return self.on

	def Enable(self):
		self.enabled = True
		self.__ApplyColor()

	def Disable(self):
		self.enabled = False
		self.__ApplyColor()

	def SetEvent(self, event, *args):
		self.event = event
		self.args = args

	def OnMouseOverIn(self):
		if self.enabled:
			self.__SetState("h")

	def OnMouseOverOut(self):
		self.pressed = False
		self.__SetState("n")

	def OnMouseLeftButtonDown(self):
		if self.enabled:
			self.pressed = True
			self.__SetState("d")
		return True

	def OnMouseLeftButtonUp(self):
		fire = self.pressed and self.enabled and self.IsIn()
		self.pressed = False
		self.__SetState("h" if self.IsIn() else "n")
		if fire and self.event:
			try:
				import snd
				snd.PlaySound("sound/ui/click.wav")
			except Exception:
				pass
			apply(self.event, self.args)
		return True


class Field(ui.Window):
	def __init__(self, maxLen=16, number=False):
		ui.Window.__init__(self)
		self.slot = ui.SlotBar()
		self.slot.SetParent(self)
		self.slot.AddFlag("not_pick")
		self.slot.Show()
		self.edit = ui.EditLine()
		self.edit.SetParent(self)
		self.edit.SetPosition(4, 3)
		self.edit.SetMax(maxLen)
		if number:
			try:
				self.edit.SetNumberMode()
			except Exception:
				pass
		self.edit.Show()
		self.SetSize(60, EDIT_H)

	def __del__(self):
		ui.Window.__del__(self)

	def SetSize(self, width, height=EDIT_H):
		ui.Window.SetSize(self, width, height)
		self.slot.SetSize(width, height)
		self.edit.SetSize(max(4, width - 8), height - 3)

	def GetText(self):
		return self.edit.GetText()

	def SetText(self, text):
		self.edit.SetText(str(text))

	def SetReturnEvent(self, event):
		self.edit.SetReturnEvent(event)

	def KillFocus(self):
		try:
			self.edit.KillFocus()
		except Exception:
			pass

	def IsFocus(self):
		try:
			return self.edit.IsFocus()
		except Exception:
			return False

	def OnMouseLeftButtonDown(self):
		self.edit.SetFocus()
		return True


class Label(ui.TextLine):
	def __init__(self, text="", color=COLOR_LABEL):
		ui.TextLine.__init__(self)
		self.SetText(text)
		self.SetPackedFontColor(color)





class Row(object):
	def __init__(self):
		self.widgets = []
		self.active = True
		self.height = BTN_H

	def Layout(self, panel, x, y, width):
		pass

	def SetVisible(self, visible):
		for widget in self.widgets:
			if visible:
				widget.Show()
			else:
				if isinstance(widget, Field) and widget.IsFocus():
					widget.KillFocus()
				widget.Hide()


class HeaderRow(Row):
	def __init__(self, panel, parent, text):
		Row.__init__(self)
		self.height = 17
		self.bar = ui.HorizontalBar()
		self.bar.SetParent(parent)
		self.bar.Create(200)
		self.title = ui.TextLine()
		self.title.SetParent(self.bar)
		self.title.SetPosition(0, 1)
		self.title.SetWindowHorizontalAlignCenter()
		self.title.SetHorizontalAlignCenter()
		self.title.SetPackedFontColor(0xffe3cca1)
		self.title.SetText(text)
		self.title.Show()
		self.widgets = [self.bar]

	def SetText(self, text):
		self.title.SetText(text)

	def Layout(self, panel, x, y, width):
		self.bar.SetWidth(max(64, width), 32, 17)
		self.bar.SetPosition(x, y)
		self.title.UpdateRect()


class GridRow(Row):
	def __init__(self, panel, parent, cols, specs):
		Row.__init__(self)
		self.cols = cols
		self.buttons = []
		for spec in specs:
			(text, event) = spec[0], spec[1]
			args = spec[2] if len(spec) > 2 else ()
			color = spec[3] if len(spec) > 3 else COLOR_TEXT
			button = StretchButton()
			button.SetParent(parent)
			button.SetText(text)
			button.SetTextColor(color)
			if event:
				button.SetEvent(event, *args)
			self.buttons.append(button)
		self.widgets = list(self.buttons)
		rows = (len(self.buttons) + cols - 1) // cols
		self.height = rows * BTN_H + max(0, rows - 1) * 3

	def Layout(self, panel, x, y, width):
		cellW = (width - (self.cols - 1) * 3) // self.cols
		for i, button in enumerate(self.buttons):
			col = i % self.cols
			row = i // self.cols
			button.SetSize(cellW, BTN_H)
			button.SetPosition(x + col * (cellW + 3), y + row * (BTN_H + 3))


class FormRow(Row):
	
	
	def __init__(self, panel, parent, items):
		Row.__init__(self)
		self.items = items
		for item in items:
			widget = item[1]
			widget.SetParent(parent)
			self.widgets.append(widget)

	def Layout(self, panel, x, y, width):
		fixed = 0
		weights = 0
		for item in self.items:
			kind = item[0]
			if kind == "label":
				fixed += TextWidth(item[1].GetText()) + 6
			elif kind == "button":
				fixed += item[2] + 4
			else:
				fixed += item[2] + 4
				weights += item[3]
		spare = max(0, width - fixed)
		cx = x
		for item in self.items:
			kind = item[0]
			widget = item[1]
			if kind == "label":
				widget.SetPosition(cx, y + 3)
				cx += TextWidth(widget.GetText()) + 6
			elif kind == "button":
				widget.SetSize(item[2], BTN_H)
				widget.SetPosition(cx, y)
				cx += item[2] + 4
			elif kind == "edit":
				extra = (spare * item[3] // weights) if weights else 0
				w = item[2] + extra
				widget.SetSize(w, EDIT_H)
				widget.SetPosition(cx, y + 1)
				cx += w + 4
			elif kind == "value":
				extra = (spare * item[3] // weights) if weights else 0
				widget.SetPosition(cx, y + 3)
				cx += item[2] + extra + 4


class InfoRow(Row):
	def __init__(self, panel, parent, cols, lines):
		Row.__init__(self)
		self.cols = cols
		self.lines = lines
		self.board = ui.ThinBoard()
		self.board.SetParent(parent)
		self.cells = []
		for i in xrange(cols * lines):
			text = ui.TextLine()
			text.SetParent(self.board)
			text.SetPackedFontColor(COLOR_TEXT)
			text.Show()
			self.cells.append(text)
		self.height = lines * LINE_H + 10
		self.widgets = [self.board]

	def SetCell(self, index, text, color=COLOR_TEXT):
		if 0 <= index < len(self.cells):
			self.cells[index].SetText(text)
			self.cells[index].SetPackedFontColor(color)

	def Layout(self, panel, x, y, width):
		self.board.SetSize(width, self.height)
		self.board.SetPosition(x, y)
		cellW = (width - 12) // self.cols
		for i, cell in enumerate(self.cells):
			cell.SetPosition(6 + (i % self.cols) * cellW, 5 + (i // self.cols) * LINE_H)


class TextRow(Row):
	def __init__(self, panel, parent, text, color=COLOR_DIM):
		Row.__init__(self)
		self.height = LINE_H
		self.line = ui.TextLine()
		self.line.SetParent(parent)
		self.line.SetPackedFontColor(color)
		self.line.SetText(text)
		self.widgets = [self.line]

	def SetText(self, text, color=None):
		self.line.SetText(text)
		if color is not None:
			self.line.SetPackedFontColor(color)

	def Layout(self, panel, x, y, width):
		self.line.SetPosition(x, y + 1)


class ListRow(Row):
	
	
	def __init__(self, panel, parent, visible, onPick):
		Row.__init__(self)
		self.visible = visible
		self.onPick = onPick
		self.entries = []
		self.offset = 0
		self.selected = None
		self.board = ui.ThinBoard()
		self.board.SetParent(parent)
		self.rows = []
		for i in xrange(visible):
			button = StretchButton()
			button.SetParent(self.board)
			button.SetEvent(ui.__mem_func__(self.__OnClick), i)
			self.rows.append(button)
		self.prevButton = StretchButton()
		self.prevButton.SetParent(parent)
		self.prevButton.SetText("<")
		self.prevButton.SetEvent(ui.__mem_func__(self.__Page), -1)
		self.nextButton = StretchButton()
		self.nextButton.SetParent(parent)
		self.nextButton.SetText(">")
		self.nextButton.SetEvent(ui.__mem_func__(self.__Page), 1)
		self.info = ui.TextLine()
		self.info.SetParent(parent)
		self.info.SetPackedFontColor(COLOR_DIM)
		self.height = visible * (BTN_H + 1) + 8 + BTN_H + 3
		self.widgets = [self.board, self.prevButton, self.nextButton, self.info]
		self.emptyText = ""

	def SetEntries(self, entries, emptyText=""):
		
		self.entries = entries
		self.offset = 0
		self.emptyText = emptyText
		self.Refresh()

	def SetSelected(self, value):
		self.selected = value
		self.Refresh()

	def __Page(self, direction):
		count = len(self.entries)
		if count <= self.visible:
			return
		self.offset = max(0, min(count - 1, self.offset + direction * self.visible))
		self.offset -= self.offset % self.visible
		self.Refresh()

	def __OnClick(self, index):
		pos = self.offset + index
		if 0 <= pos < len(self.entries) and self.onPick:
			(value, label) = self.entries[pos][0], self.entries[pos][1]
			self.selected = value
			self.Refresh()
			self.onPick(value, label)

	def Refresh(self):
		count = len(self.entries)
		for i, button in enumerate(self.rows):
			pos = self.offset + i
			if pos < count:
				(value, label) = self.entries[pos][0], self.entries[pos][1]
				button.SetText(label)
				button.SetOn(value == self.selected)
				button.Enable()
			else:
				button.SetText(self.emptyText if (i == 0 and count == 0) else "")
				button.SetOn(False)
				button.Disable()
		if count:
			last = min(count, self.offset + self.visible)
			self.info.SetText("%d-%d / %d" % (self.offset + 1, last, count))
		else:
			self.info.SetText("0 / 0")

	def Layout(self, panel, x, y, width):
		boardH = self.visible * (BTN_H + 1) + 8
		self.board.SetSize(width, boardH)
		self.board.SetPosition(x, y)
		for i, button in enumerate(self.rows):
			button.SetSize(width - 8, BTN_H)
			button.SetPosition(4, 4 + i * (BTN_H + 1))
			button.Show()
		by = y + boardH + 3
		self.prevButton.SetSize(40, BTN_H)
		self.prevButton.SetPosition(x, by)
		self.nextButton.SetSize(40, BTN_H)
		self.nextButton.SetPosition(x + 44, by)
		self.info.SetPosition(x + 92, by + 3)





class GMPanelWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetTitleName(T("GMP_TITLE"))
		self.SetCloseEvent(ui.__mem_func__(self.Close))

		self.sizeIndex = DEFAULT_SIZE
		self.section = "player"
		self.sections = {}
		self.sectionParents = {}
		self.scroll = {}
		self.menuButtons = {}
		self.fields = {}
		self.values = {}
		self.dialog = None
		self.pending = {}
		self.targetVid = 0

		self.lookupNick = ""
		self.lookupData = {}
		self.skillBuffer = ""
		self.skills = []

		self.listQueue = []
		self.listBusy = None
		self.listBuffer = ""
		self.listDeadline = 0.0
		self.lists = {}

		self.itemsMode = "item"
		self.itemsCategory = "weapon"
		self.itemVnum = "0"
		self.itemLabel = ""
		self.bonusTypes = ["0"] * 7
		self.stones = ["0"] * 3
		# MT2009_PLUS_GM_PANEL_ITEMS_SEARCH_V1: the search's text of each mode,
		# and where the item list stood when a bonus or a stone was picked:
		# "Back" returns to both (Kiciamol).
		self.itemsSearchSaved = {}
		self.itemsReturnScroll = 0
		self.itemsReturnCategory = None
		self.itemPlace = "inv"
		self.itemsFilter = ""

		self.spawnMode = None
		self.spawnEmpire = "1"
		self.teleportGroup = 0
		self.banDays = 1
		self.gmRank = "HIGH_WIZARD"
		self.eventEmpire = 0
		self.waypointLabels = {}
		self.waypointsLoaded = False
		self.serverLoaded = False
		self.aiValues = {}
		self.cmdFilter = ""

		self.__BuildChrome()
		self.__BuildSections()
		self.__ApplySize()
		self.__SetSection("player")

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.Hide()
		self.confirmCall = None
		self.equipEvent = None
		if self.dialog:
			self.dialog.Close()
			self.dialog = None
		for rows in self.sections.values():
			for row in rows:
				for widget in row.widgets:
					if isinstance(widget, StretchButton):
						widget.Destroy()
				if isinstance(row, GridRow):
					for button in row.buttons:
						button.Destroy()
				if isinstance(row, ListRow):
					row.onPick = None
					for button in row.rows:
						button.Destroy()
		for button in self.menuButtons.values():
			button.Destroy()
		self.equipEvent = None
		self.sections = {}
		self.sectionParents = {}
		self.menuButtons = {}
		self.fields = {}
		self.values = {}
		self.lists = {}

	

	def __BuildChrome(self):
		self.sizeLabel = ui.TextLine()
		self.sizeLabel.SetParent(self)
		self.sizeLabel.SetPackedFontColor(COLOR_DIM)
		self.sizeLabel.SetText(T("GMP_WINDOW_SIZE"))
		self.sizeLabel.Show()
		self.minusButton = StretchButton()
		self.minusButton.SetParent(self)
		self.minusButton.SetText("-")
		self.minusButton.SetSize(26, BTN_H)
		self.minusButton.SetEvent(ui.__mem_func__(self.__ChangeSize), -1)
		self.minusButton.Show()
		self.plusButton = StretchButton()
		self.plusButton.SetParent(self)
		self.plusButton.SetText("+")
		self.plusButton.SetSize(26, BTN_H)
		self.plusButton.SetEvent(ui.__mem_func__(self.__ChangeSize), 1)
		self.plusButton.Show()

		self.menuBoard = ui.Window()
		self.menuBoard.SetParent(self)
		self.menuBoard.AddFlag("not_pick")
		self.menuBoard.Show()
		y = 0
		for (name, key) in SECTIONS:
			button = StretchButton()
			button.SetParent(self.menuBoard)
			button.SetText(T(key))
			button.SetSize(MENU_WIDTH, BTN_H)
			button.SetPosition(0, y)
			button.SetEvent(ui.__mem_func__(self.__SetSection), name)
			button.Show()
			self.menuButtons[name] = button
			y += BTN_H + 3

		self.content = ui.Window()
		self.content.SetParent(self)
		self.content.AddFlag("not_pick")
		self.content.Show()

		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))

		self.statusLine = ui.TextLine()
		self.statusLine.SetParent(self)
		self.statusLine.SetPackedFontColor(COLOR_GREEN)
		self.statusLine.Show()
		self.SetStatus(T("GMP_READY"))

	def __ChangeSize(self, step):
		index = max(0, min(len(SIZES) - 1, self.sizeIndex + step))
		if index == self.sizeIndex:
			return
		self.sizeIndex = index
		self.__ApplySize()
		if self.section == "spawn" and self.spawnMode:
			self.__ScrollIntoView(self.spawnListHeader, self.spawnList)
		self.__Relayout()

	def __ApplySize(self):
		(w, h) = SIZES[self.sizeIndex]
		screenW = wndMgr.GetScreenWidth()
		screenH = wndMgr.GetScreenHeight()
		while self.sizeIndex > 0 and (w > screenW - 10 or h > screenH - 40):
			self.sizeIndex -= 1
			(w, h) = SIZES[self.sizeIndex]
		w = min(w, screenW)
		h = min(h, screenH)
		self.SetSize(w, h)
		self.plusButton.SetPosition(w - 14 - 26, h - 31)
		self.minusButton.SetPosition(w - 14 - 26 - 3 - 26, h - 31)
		self.sizeLabel.SetPosition(w - 14 - 26 - 3 - 26 - 6 - TextWidth(T("GMP_WINDOW_SIZE")), h - 28)
		if self.sizeIndex == 0:
			self.minusButton.Disable()
		else:
			self.minusButton.Enable()
		if self.sizeIndex == len(SIZES) - 1:
			self.plusButton.Disable()
		else:
			self.plusButton.Enable()

		self.menuBoard.SetPosition(12, 36)
		self.menuBoard.SetSize(MENU_WIDTH, h - 36 - 30)
		self.contentX = 12 + MENU_WIDTH + 10
		self.contentY = 36
		self.contentW = w - self.contentX - 12 - 20
		self.contentH = h - self.contentY - 40
		self.content.SetPosition(self.contentX, self.contentY)
		self.content.SetSize(self.contentW + 20, self.contentH)
		for parent in self.sectionParents.values():
			parent.SetSize(self.contentW, self.contentH)
		self.scrollBar.SetPosition(self.contentX + self.contentW + 3, self.contentY)
		self.scrollBar.SetScrollBarSize(self.contentH)
		self.statusLine.SetPosition(14, h - 28)
		self.__KeepOnScreen()

	def __KeepOnScreen(self):
		(x, y) = self.GetLocalPosition()
		screenW = wndMgr.GetScreenWidth()
		screenH = wndMgr.GetScreenHeight()
		x = max(0, min(x, screenW - self.GetWidth()))
		y = max(0, min(y, screenH - self.GetHeight()))
		self.SetPosition(x, y)

	def Open(self):
		if not self.IsShow():
			screenW = wndMgr.GetScreenWidth()
			screenH = wndMgr.GetScreenHeight()
			if not getattr(self, "placed", False):
				self.SetPosition(max(0, (screenW - self.GetWidth()) // 2), max(0, (screenH - self.GetHeight()) // 2))
				self.placed = True
			self.__ApplySize()
			self.Show()
			self.__Relayout()
		self.SetTop()

	def Close(self):
		for field in self.fields.values():
			if field.IsFocus():
				field.KillFocus()
		self.confirmCall = None
		if self.dialog:
			self.dialog.Close()
			self.dialog = None
		self.Hide()

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def OnPressEscapeKey(self):
		if self.section == "items" and self.itemsMode != "item":
			self.__SetItemsMode("item")
			return True
		if self.section == "spawn" and self.spawnMode:
			self.__SetSpawnMode(None)
			return True
		self.Close()
		return True

	def SetStatus(self, text, color=COLOR_GREEN):
		self.statusLine.SetText(text)
		self.statusLine.SetPackedFontColor(color)

	def SetError(self, text):
		self.SetStatus(text, COLOR_RED)

	

	def __SetSection(self, name):
		for field in self.fields.values():
			if field.IsFocus():
				field.KillFocus()
		self.section = name
		for key, button in self.menuButtons.items():
			button.SetOn(key == name)
		for key, parent in self.sectionParents.items():
			if key == name:
				parent.Show()
			else:
				parent.Hide()
		self.scroll[name] = self.scroll.get(name, 0)
		self.__OnEnterSection(name)
		self.__Relayout()

	def __Relayout(self):
		rows = self.sections.get(self.section, [])
		active = [row for row in rows if row.active]
		total = 0
		for row in active:
			total += row.height + ROW_GAP
		overflow = max(0, total - self.contentH)
		if overflow > 0:
			self.scrollBar.SetMiddleBarSize(float(self.contentH) / max(1, total))
			self.scrollBar.Show()
		else:
			self.scrollBar.Hide()
			self.scroll[self.section] = 0
		offset = min(self.scroll.get(self.section, 0), overflow)
		self.scroll[self.section] = offset
		y = -offset
		for row in rows:
			if not row.active:
				row.SetVisible(False)
				continue
			visible = y >= 0 and y + row.height <= self.contentH
			if visible:
				row.Layout(self, 0, y, self.contentW)
			row.SetVisible(visible)
			y += row.height + ROW_GAP
		self.totalHeight = total
		if overflow > 0:
			self.__SyncScrollBar(offset, overflow)

	def __ScrollIntoView(self, first, last):
		
		
		
		
		
		
		y = 0
		top = bottom = None
		for row in self.sections.get(self.section, []):
			if not row.active:
				continue
			if row is first:
				top = y
			if row is last:
				bottom = y + row.height
			y += row.height + ROW_GAP
		if top is None or bottom is None:
			return
		offset = self.scroll.get(self.section, 0)
		if bottom - offset > self.contentH:
			offset = bottom - self.contentH
		if top < offset:
			offset = top
		self.scroll[self.section] = max(0, offset)

	def __OnScroll(self):
		if getattr(self, "syncScroll", False):
			return
		total = getattr(self, "totalHeight", 0)
		overflow = max(0, total - self.contentH)
		pos = self.scrollBar.GetPos()
		offset = overflow if pos >= 0.995 else int(round(pos * overflow))
		if offset != self.scroll.get(self.section, 0):
			self.scroll[self.section] = offset
			self.__Relayout()

	def __SyncScrollBar(self, offset, overflow):
		self.syncScroll = True
		try:
			self.scrollBar.SetPos(float(offset) / overflow if overflow > 0 else 0.0)
		finally:
			self.syncScroll = False

	def OnMouseWheel(self, delta):
		total = getattr(self, "totalHeight", 0)
		overflow = max(0, total - self.contentH)
		if overflow <= 0:
			return True
		step = (BTN_H + ROW_GAP) * 2
		offset = self.scroll.get(self.section, 0) + (-step if delta > 0 else step)
		offset = max(0, min(overflow, offset))
		self.scroll[self.section] = offset
		self.__Relayout()
		return True

	def __Parent(self, section):
		parent = ui.Window()
		parent.SetParent(self.content)
		parent.SetPosition(0, 0)
		parent.SetSize(10, 10)
		parent.AddFlag("not_pick")
		parent.Hide()
		self.sectionParents[section] = parent
		return parent

	def __Button(self, text, event=None, *args):
		button = StretchButton()
		button.SetText(text)
		if event:
			button.SetEvent(event, *args)
		return button

	def __Field(self, key, maxLen=16, number=False, text=""):
		field = Field(maxLen, number)
		if text:
			field.SetText(text)
		self.fields[key] = field
		return field

	def __Mem(self, func):
		return ui.__mem_func__(func)

	def __BuildSections(self):
		self.__BuildPlayer()
		self.__BuildSelf()
		self.__BuildWorld()
		self.__BuildItems()
		self.__BuildAccounts()
		self.__BuildSpawn()
		self.__BuildTeleport()
		self.__BuildServer()
		self.__BuildCommands()

	

	def __BuildPlayer(self):
		p = self.__Parent("player")
		m = self.__Mem
		rows = []
		nick = self.__Field("player_nick", 24)
		nick.SetReturnEvent(m(self.__OnPlayerSearch))
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_NICK"))),
			("edit", nick, 100, 1),
			("button", self.__Button(T("GMP_SEARCH"), m(self.__OnPlayerSearch)), 70),
			("button", self.__Button(T("GMP_MY_TARGET"), m(self.__OnPlayerTarget)), 100),
		]))
		self.playerInfo = InfoRow(self, p, 3, 4)
		rows.append(self.playerInfo)

		rows.append(HeaderRow(self, p, T("GMP_HDR_MOVE")))
		rows.append(GridRow(self, p, 4, [
			(T("GMP_GOTO_PLAYER"), m(self.__PlayerCmd), ("warp",)),
			(T("GMP_SUMMON"), m(self.__PlayerCmd), ("transfer",)),
			(T("GMP_STATE"), m(self.__PlayerCmd), ("state",)),
			(T("GMP_AFFECTS"), m(self.__PlayerCmd), ("affect_remove",)),
		]))

		rows.append(HeaderRow(self, p, T("GMP_HDR_CHAR")))
		rows.append(GridRow(self, p, 4, [
			(T("GMP_VIEW_EQ"), m(self.__OnViewEquip)),
			(T("GMP_GIVE_ITEM"), m(self.__OnGiveItemFor)),
			(T("GMP_SKILLS_M"), m(self.__OnAllSkills), (20,)),
			(T("GMP_SKILLS_G"), m(self.__OnAllSkills), (30,)),
			(T("GMP_SKILLS_P"), m(self.__OnAllSkills), (40,)),
		]))

		values = [
			("gold", "GMP_VAL_YANG", "GMP_GIVE", m(self.__OnValue), True),
			("cash", "GMP_VAL_CASH", "GMP_GIVE", m(self.__OnValue), True),
			("level", "GMP_VAL_LEVEL", "GMP_SET", m(self.__OnValue), True),
			("range", "GMP_VAL_RANK", "GMP_SET", m(self.__OnValue), False),
			("horse", "GMP_VAL_HORSE", "GMP_SET", m(self.__OnValue), True),
			("skillpoint", "GMP_VAL_SKILLPT", "GMP_GIVE", m(self.__OnValue), True),
		]
		for (stat, key) in STAT_ROWS:
			values.append(("stat_" + stat, key, "GMP_SET", m(self.__OnValue), True))
		labelW = max([TextWidth(T(v[1])) for v in values]) + 6
		for i in xrange(0, len(values), 2):
			items = []
			for (name, labelKey, buttonKey, event, number) in values[i:i + 2]:
				if items:
					items.append(("value", Label(""), 4, 0))
				field = self.__Field("val_" + name, 12, number)
				items.append(("value", Label(T(labelKey)), labelW, 0))
				items.append(("edit", field, 50, 1))
				items.append(("button", self.__Button(T(buttonKey), event, name), 56))
			rows.append(FormRow(self, p, items))

		rows.append(HeaderRow(self, p, T("GMP_HDR_SKILLS")))
		self.skillHint = TextRow(self, p, T("GMP_SKILLS_HINT"))
		rows.append(self.skillHint)
		self.skillRows = []
		for i in xrange(24):
			name = Label("", COLOR_TEXT)
			field = self.__Field("skill_%d" % i, 4)
			button = self.__Button(T("GMP_SET"), m(self.__OnSetSkill), i)
			row = FormRow(self, p, [("value", name, 160, 1), ("edit", field, 44, 0), ("button", button, 56)])
			row.active = False
			row.nameLabel = name
			self.skillRows.append(row)
			rows.append(row)

		rows.append(HeaderRow(self, p, T("GMP_HDR_PUNISH")))
		mute = self.__Field("mute_time", 8, False, "10m")
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_MUTE_FOR"))),
			("edit", mute, 50, 1),
			("button", self.__Button(T("GMP_MUTE"), m(self.__OnMute)), 70),
			("button", self.__Button(T("GMP_UNMUTE"), m(self.__OnUnmute)), 80),
		]))
		rows.append(GridRow(self, p, 4, [
			(T("GMP_STUN"), m(self.__PlayerCmd), ("stun",), COLOR_RED),
			(T("GMP_SLOW"), m(self.__PlayerCmd), ("slow",), COLOR_RED),
			(T("GMP_KILL"), m(self.__ConfirmPlayerCmd), ("kill", "GMP_Q_KILL"), COLOR_RED),
			(T("GMP_KICK"), m(self.__ConfirmPlayerCmd), ("dc", "GMP_Q_KICK"), COLOR_RED),
			(T("GMP_BAN_DOTS"), m(self.__OnBanFor), (), COLOR_RED),
		]))
		self.sections["player"] = rows

	def __Nick(self):
		nick = SafeToken(self.fields["player_nick"].GetText())
		if not nick:
			self.SetError(T("GMP_ERR_NO_NICK"))
			return ""
		return nick

	def __OnPlayerTarget(self):
		try:
			import chr
			vid = player.GetTargetVID()
			if vid:
				name = chr.GetNameByVID(vid)
				if name:
					self.targetVid = vid
					self.fields["player_nick"].SetText(name)
					self.__OnPlayerSearch()
					return
		except Exception:
			pass
		self.SetError(T("GMP_ERR_NO_TARGET"))

	def OpenLookupFor(self, name, vid=0):
		self.Open()
		self.targetVid = vid
		self.fields["player_nick"].SetText(name)
		self.__SetSection("player")
		self.__OnPlayerSearch()

	def OpenBanFor(self, name):
		self.Open()
		self.fields["acc_nick"].SetText(name)
		self.__SetSection("accounts")
		self.__OnAccount("check")

	def __OnPlayerSearch(self):
		nick = self.__Nick()
		if not nick:
			return
		self.lookupNick = nick
		self.lookupData = {}
		self.skillBuffer = ""
		self.skills = []
		self.__ShowSkills()
		for i in xrange(12):
			self.playerInfo.SetCell(i, "")
		self.playerInfo.SetCell(0, T("GMP_SEARCHING"), COLOR_DIM)
		net.SendChatPacket("/gmpanel_lookup %s" % nick)
		net.SendChatPacket("/gmpanel_skilllist %s" % nick)
		self.__Pending("lookup")
		self.SetStatus(T("GMP_SEARCHING"))

	def SetLookupResult(self, data):
		self.__Done("lookup")
		if data.startswith("ERR_NOTFOUND"):
			self.playerInfo.SetCell(0, T("GMP_NOT_FOUND"), COLOR_RED)
			self.SetError(T("GMP_NOT_FOUND"))
			return
		if data.startswith("ERR_BADNAME"):
			self.playerInfo.SetCell(0, T("GMP_ERR_BAD_NICK"), COLOR_RED)
			self.SetError(T("GMP_ERR_BAD_NICK"))
			return
		parts = data.split("|")
		keys = ["name", "level", "job", "hp", "mp", "exp", "gold", "st", "ht", "dx", "iq", "statpt",
			"skillpt", "subskillpt", "map", "status", "horse", "horsept", "account", "ip", "playtime", "range"]
		if len(parts) < len(keys):
			self.SetError(TF("GMP_ERR", data))
			return
		d = dict(zip(keys, parts))
		self.lookupData = d
		self.lookupNick = d["name"]
		self.__ShowLookup()
		self.SetStatus(TF("GMP_FOUND", d["name"]))

	def __ShowLookup(self):
		d = self.lookupData
		if not d:
			return
		online = d.get("status") == "ONLINE"
		jobKey = JobKeyOf(d.get("job"))
		if jobKey:
			jobName = T(jobKey)
		else:
			jobName = "-"
		try:
			mapName = T(MAP_NAMES[int(d["map"])])
		except Exception:
			mapName = "#" + d.get("map", "-")
		self.playerInfo.SetCell(0, "%s  Lv %s  %s" % (d["name"], d["level"], jobName), COLOR_GOLD)
		self.playerInfo.SetCell(1, TF("GMP_INFO_MAP", mapName))
		if online:
			self.playerInfo.SetCell(2, T("GMP_ONLINE"), COLOR_GREEN)
		else:
			self.playerInfo.SetCell(2, TF("GMP_OFFLINE_SINCE", d["status"].replace("_", " ")), COLOR_DIM)
		self.playerInfo.SetCell(3, TF("GMP_INFO_HPMP", d["hp"], d["mp"]))
		try:
			gold = localeInfo.NumberToMoneyString(long(d["gold"]))
		except Exception:
			gold = d["gold"]
		self.playerInfo.SetCell(4, TF("GMP_INFO_YANG", gold))
		self.playerInfo.SetCell(5, TF("GMP_INFO_ACCOUNT", d["account"]))
		self.playerInfo.SetCell(6, TF("GMP_INFO_STATS", d["st"], d["ht"], d["dx"], d["iq"]))
		self.playerInfo.SetCell(7, TF("GMP_INFO_POINTS", d["statpt"], d["skillpt"]))
		self.playerInfo.SetCell(8, TF("GMP_INFO_IP", d["ip"]))
		self.playerInfo.SetCell(9, TF("GMP_INFO_HORSE", d["horse"]))
		self.playerInfo.SetCell(10, TF("GMP_INFO_RANK", d["range"]))
		self.playerInfo.SetCell(11, TF("GMP_INFO_EXP", d["exp"]))
		prefill = {"level": d["level"], "range": d["range"].split(".")[0], "horse": d["horse"],
			"statpoint": d["statpt"], "skillpoint": d["skillpt"],
			"stat_st": d["st"], "stat_ht": d["ht"], "stat_dx": d["dx"], "stat_iq": d["iq"]}
		for key, value in prefill.items():
			field = self.fields.get("val_" + key)
			if field:
				field.SetText(value)

	def SetSkillListResult(self, data):
		if data in ("ERR_OFFLINE", "ERR_BADDATA"):
			self.skillBuffer = ""
			self.skills = []
			self.skillHint.SetText(T("GMP_SKILLS_OFFLINE") if data == "ERR_OFFLINE" else T("GMP_SKILLS_HINT"))
			self.__ShowSkills()
			return
		try:
			(isLast, chunk) = data.split("|", 1)
		except ValueError:
			return
		self.skillBuffer += chunk
		if isLast != "1":
			return
		skills = []
		for entry in self.skillBuffer.split(";"):
			parts = entry.split(":")
			if len(parts) != 4 or parts[0] == "0":
				continue
			try:
				skills.append((parts[0], int(parts[2]), int(parts[3])))
			except ValueError:
				pass
		self.skillBuffer = ""
		self.skills = skills
		self.skillHint.SetText(T("GMP_SKILLS_EDIT") if skills else T("GMP_SKILLS_NONE"))
		self.__ShowSkills()

	def __SkillName(self, vnum):
		try:
			import skill
			name = skill.GetSkillName(int(vnum))
			if name:
				return name
		except Exception:
			pass
		return "Skill #%s" % vnum

	def __ShowSkills(self):
		for i, row in enumerate(self.skillRows):
			if i < len(self.skills):
				(vnum, level, maxLevel) = self.skills[i]
				row.nameLabel.SetText(self.__SkillName(vnum))
				self.fields["skill_%d" % i].SetText(self.__GradeText(level))
				row.active = True
			else:
				row.active = False
		if self.section == "player":
			self.__Relayout()

	def __GradeText(self, level):
		if level >= 40:
			return "P"
		if level >= 30:
			return "G%d" % (level - 29)
		if level >= 20:
			return "M%d" % (level - 19)
		return str(level)

	def __GradeValue(self, text):
		text = text.strip().upper()
		try:
			if text == "P":
				return 40
			if text.startswith("G"):
				return 29 + max(1, min(10, int(text[1:] or "1")))
			if text.startswith("M"):
				return 19 + max(1, min(10, int(text[1:] or "1")))
			return max(0, min(40, int(text)))
		except ValueError:
			return -1

	def __OnSetSkill(self, index):
		if index >= len(self.skills) or not self.lookupNick:
			return
		level = self.__GradeValue(self.fields["skill_%d" % index].GetText())
		if level < 0:
			self.SetError(T("GMP_ERR_SKILL_LEVEL"))
			return
		(vnum, old, maxLevel) = self.skills[index]
		net.SendChatPacket("/gmpanel_setskill %s|%s|%d" % (self.lookupNick, vnum, level))
		self.__Pending("setskill")

	def SetSetSkillResult(self, data):
		self.__Done("setskill")
		if data.startswith("OK|"):
			parts = data.split("|")
			try:
				for i, (vnum, level, maxLevel) in enumerate(self.skills):
					if vnum == parts[1]:
						self.skills[i] = (vnum, int(parts[2]), maxLevel)
			except (ValueError, IndexError):
				pass
			self.__ShowSkills()
			self.SetStatus(T("GMP_SAVED"))
		elif data == "ERR_OFFLINE":
			self.SetError(T("GMP_ERR_OFFLINE"))
		else:
			self.SetError(TF("GMP_ERR", data))

	def __TargetNick(self):
		nick = self.lookupNick or SafeToken(self.fields["player_nick"].GetText())
		if not nick:
			self.SetError(T("GMP_ERR_NO_NICK"))
		return nick

	def __PlayerCmd(self, command):
		nick = self.__TargetNick()
		if not nick:
			return
		net.SendChatPacket("/%s %s" % (command, nick))
		self.SetStatus(TF("GMP_SENT", "/%s %s" % (command, nick)))

	def __ConfirmPlayerCmd(self, command, questionKey):
		nick = self.__TargetNick()
		if not nick:
			return
		self.__Confirm(TF(questionKey, nick), self.__PlayerCmd, command)

	def __OnAllSkills(self, level):
		nick = self.__TargetNick()
		if not nick:
			return
		if not self.skills or nick != self.lookupNick:
			self.SetError(T("GMP_SKILLS_HINT"))
			return
		count = 0
		for (vnum, old, maxLevel) in self.skills:
			if int(vnum) >= 121:
				continue
			net.SendChatPacket("/gmpanel_setskill %s|%s|%d" % (nick, vnum, min(level, maxLevel)))
			count += 1
		if count:
			self.__Pending("setskill")
		else:
			self.SetError(T("GMP_SKILLS_NONE"))

	def __OnValue(self, name):
		nick = self.__TargetNick()
		if not nick:
			return
		value = SafeToken(self.fields["val_" + name].GetText())
		if not value or value.lstrip("-") == "" or not value.lstrip("-").isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		if name == "gold":
			net.SendChatPacket("/gmpanel_give_gold %s|%s" % (nick, value))
			self.__Pending("gold")
		elif name == "cash":
			net.SendChatPacket("/gmpanel_give_cash %s|%s" % (nick, value))
			self.__Pending("cash")
		elif name == "horse":
			net.SendChatPacket("/gmpanel_set_horse_points %s|%s" % (nick, value))
			self.__Pending("horse")
		elif name == "range":
			net.SendChatPacket("/gmpanel_set_range %s|%s" % (nick, value))
			self.__Pending("range")
		elif name.startswith("stat_"):
			net.SendChatPacket("/gmpanel_set_stat %s|%s|%s" % (nick, name[5:], value))
			self.__Pending("stat")
		elif name == "level":
			net.SendChatPacket("/advance %s %s" % (nick, value))
			self.SetStatus(TF("GMP_SENT", "/advance %s %s" % (nick, value)))
			self.__RefreshLookupLater()
		elif name == "skillpoint":
			net.SendChatPacket("/set %s skill %s" % (nick, value))
			self.SetStatus(TF("GMP_SENT", "/set %s skill %s" % (nick, value)))
			self.__RefreshLookupLater()

	def __RefreshLookupLater(self):
		self.refreshAt = clientclock.Now() + 1.0

	def __ValueResult(self, key, data, field=None):
		self.__Done(key)
		if data.startswith("OK"):
			self.SetStatus(T("GMP_SAVED_OFFLINE") if data.startswith("OK_OFFLINE") else T("GMP_SAVED"))
			parts = data.split("|")
			if field and len(parts) > 1 and self.lookupData:
				self.lookupData[field] = parts[-1]
				self.__ShowLookup()
		elif data == "ERR_NOTFOUND":
			self.SetError(T("GMP_NOT_FOUND"))
		elif data == "ERR_BADDATA":
			self.SetError(T("GMP_ERR_NUMBER"))
		else:
			self.SetError(TF("GMP_ERR", data))

	def SetGiveGoldResult(self, data):
		self.__ValueResult("gold", data, "gold" if data.startswith("OK|") else None)

	def SetGiveCashResult(self, data):
		self.__ValueResult("cash", data)

	def SetHorsePointsResult(self, data):
		self.__ValueResult("horse", data, "horse")

	def SetRangeResult(self, data):
		self.__ValueResult("range", data, "range")

	def SetStatResult(self, data):
		self.__Done("stat")
		parts = data.split("|")
		if data.startswith("OK") and len(parts) >= 3:
			if self.lookupData:
				self.lookupData[parts[1]] = parts[2]
				self.__ShowLookup()
			self.SetStatus(T("GMP_SAVED"))
		elif data == "ERR_BADSTAT":
			self.SetError(T("GMP_ERR_NUMBER"))
		else:
			self.__ValueResult("stat", data)

	def __OnMute(self):
		nick = self.__TargetNick()
		if not nick:
			return
		duration = self.fields["mute_time"].GetText().strip().replace(" ", "") or "10m"
		net.SendChatPacket("/block_chat %s %s" % (nick, duration))
		self.SetStatus(TF("GMP_SENT", "/block_chat %s %s" % (nick, duration)))

	def __OnUnmute(self):
		nick = self.__TargetNick()
		if not nick:
			return
		net.SendChatPacket("/block_chat %s 0" % nick)
		self.SetStatus(TF("GMP_SENT", "/block_chat %s 0" % nick))

	def __OnBanFor(self):
		nick = self.__TargetNick()
		if nick:
			self.OpenBanFor(nick)

	def SetEquipEvent(self, event):
		self.equipEvent = event

	def __OnViewEquip(self):
		event = getattr(self, "equipEvent", None)
		if self.targetVid and event:
			event(self.targetVid, self.lookupNick)
			return
		self.SetError(T("GMP_ERR_EQ_TARGET"))

	def __OnGiveItemFor(self):
		nick = self.__TargetNick()
		if not nick:
			return
		self.fields["item_owner"].SetText(nick)
		self.__SetSection("items")

	

	def __BuildSelf(self):
		p = self.__Parent("self")
		m = self.__Mem
		rows = []
		rows.append(HeaderRow(self, p, T("GMP_HDR_ME")))
		rows.append(GridRow(self, p, 3, [
			(T("GMP_INVISIBLE"), m(self.__Cmd), ("invisible",)),
			(T("GMP_SPY"), m(self.__Cmd), ("spy",)),
			(T("GMP_NO_COOLDOWN"), m(self.__Cmd), ("cooltime",)),
			(T("GMP_IMMORTAL_ON"), m(self.__Cmd), ("cannot_dead",)),
			(T("GMP_IMMORTAL_OFF"), m(self.__Cmd), ("can_dead",)),
			(T("GMP_FULL_HPMP"), m(self.__Cmd), ("reset",)),
			(T("GMP_FULL_SET"), m(self.__Cmd), ("item_full_set",)),
			(T("GMP_MAX_BONUS"), m(self.__Cmd), ("attr_full_set",)),
			(T("GMP_ALL_SKILLS"), m(self.__Cmd), ("all_skill_master",)),
			(T("GMP_CLEAR_MY_AFFECT"), m(self.__Cmd), ("do_clear_affect",)),
			(T("GMP_HORSE_MAX"), m(self.__OnSelfHorse)),
			(T("GMP_REWARP"), m(self.__Cmd), ("rewarp",)),
		]))
		poly = self.__Field("poly_vnum", 6, True)
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_POLY"))),
			("edit", poly, 50, 1),
			("button", self.__Button(T("GMP_POLY_ON"), m(self.__OnPolymorph), 1), 80),
			("button", self.__Button(T("GMP_POLY_OFF"), m(self.__OnPolymorph), 0), 80),
			("button", self.__Button(T("GMP_POLY_MARBLE"), m(self.__OnPolyMarble)), 100),
		]))
		rows.append(HeaderRow(self, p, T("GMP_HDR_AROUND")))
		rows.append(GridRow(self, p, 3, [
			(T("GMP_PURGE"), m(self.__Cmd), ("purge",)),
			(T("GMP_PURGE_ALL"), m(self.__Cmd), ("purge all",)),
			(T("GMP_WEAKEN"), m(self.__Cmd), ("weaken",)),
			(T("GMP_PULL"), m(self.__Cmd), ("pull_monster",)),
			(T("GMP_MOB_COUNT"), m(self.__Cmd), ("get_mob_count",)),
			(T("GMP_RESPAWN"), m(self.__Cmd), ("respawn",)),
		]))
		self.sections["self"] = rows

	def __Cmd(self, command):
		net.SendChatPacket("/" + command)
		self.SetStatus(TF("GMP_SENT", "/" + command))

	def __OnSelfHorse(self):
		name = player.GetName()
		net.SendChatPacket("/gmpanel_set_horse_points %s|30" % name)
		self.__Pending("horse")

	def __OnPolymorph(self, on):
		if not on:
			self.__Cmd("polymorph 0")
			return
		vnum = SafeToken(self.fields["poly_vnum"].GetText())
		if not vnum.isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		self.__Cmd("polymorph %s" % vnum)

	def __OnPolyMarble(self):
		vnum = SafeToken(self.fields["poly_vnum"].GetText())
		if not vnum.isdigit() or vnum == "0":
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		net.SendChatPacket("/gmpanel_polyitem %s" % vnum)
		self.__Pending("poly")

	def SetPolyItemResult(self, data):
		self.__Done("poly")
		if data == "OK":
			self.SetStatus(T("GMP_ITEM_CREATED"))
		else:
			self.SetError(TF("GMP_ERR", data))

	

	def __BuildWorld(self):
		p = self.__Parent("world")
		m = self.__Mem
		rows = []
		rows.append(HeaderRow(self, p, T("GMP_HDR_NOTICE")))
		notice = self.__Field("notice_text", 120)
		rows.append(FormRow(self, p, [("edit", notice, 100, 1)]))
		rows.append(GridRow(self, p, 4, [
			(T("GMP_NOTICE_CHAT"), m(self.__OnNotice), ("notice",)),
			(T("GMP_NOTICE_GM"), m(self.__OnNotice), ("gm_notice",)),
			(T("GMP_NOTICE_BIG"), m(self.__OnNotice), ("big_notice",)),
			(T("GMP_NOTICE_MAP"), m(self.__OnNotice), ("notice_map",)),
		]))
		rows.append(HeaderRow(self, p, T("GMP_HDR_EVENTS")))
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_EV_EXP"))), ("edit", self.__Field("ev_exp", 4, True, "0"), 36, 1),
			("label", Label(T("GMP_EV_DROP"))), ("edit", self.__Field("ev_drop", 4, True, "0"), 36, 1),
			("label", Label(T("GMP_EV_YANG"))), ("edit", self.__Field("ev_yang", 4, True, "0"), 36, 1),
			("label", Label(T("GMP_EV_HOURS"))), ("edit", self.__Field("ev_hours", 3, True, "1"), 30, 1),
		]))
		self.eventEmpireRow = GridRow(self, p, 4, [
			(T("GMP_EMPIRE_ALL"), m(self.__SetEventEmpire), (0,)),
			(T("GMP_EMPIRE_SHINSOO"), m(self.__SetEventEmpire), (1,)),
			(T("GMP_EMPIRE_CHUNJO"), m(self.__SetEventEmpire), (2,)),
			(T("GMP_EMPIRE_JINNO"), m(self.__SetEventEmpire), (3,)),
		])
		rows.append(self.eventEmpireRow)
		rows.append(GridRow(self, p, 2, [
			(T("GMP_EV_START"), m(self.__OnEvent), (True,), COLOR_GREEN),
			(T("GMP_EV_STOP"), m(self.__OnEvent), (False,), COLOR_RED),
		]))
		rows.append(TextRow(self, p, T("GMP_EV_HINT")))
		rows.append(HeaderRow(self, p, T("GMP_HDR_WORLD")))
		rows.append(GridRow(self, p, 4, [
			(T("GMP_NIGHT"), m(self.__Cmd), ("eclipse 1",)),
			(T("GMP_DAY"), m(self.__Cmd), ("eclipse 0",)),
			(T("GMP_SNOW_ON"), m(self.__Cmd), ("xmas_snow 1",)),
			(T("GMP_SNOW_OFF"), m(self.__Cmd), ("xmas_snow 0",)),
			(T("GMP_USERS"), m(self.__Cmd), ("user",)),
			(T("GMP_WHO"), m(self.__Cmd), ("who",)),
			(T("GMP_END_DUELS"), m(self.__Cmd), ("end_all_duel",)),
			(T("GMP_EVENT_FLAGS"), m(self.__Cmd), ("geteventflag",)),
			(T("GMP_MAINT_ON"), m(self.__ConfirmCmd), ("maintenance 1", "GMP_Q_MAINT"), COLOR_RED),
			(T("GMP_MAINT_OFF"), m(self.__Cmd), ("maintenance 0",)),
			(T("GMP_RESTART"), m(self.__OnRestart), (), COLOR_RED),
		]))
		self.sections["world"] = rows
		self.__SetEventEmpire(0)

	def __OnNotice(self, command):
		text = self.fields["notice_text"].GetText().strip()
		if not text:
			self.SetError(T("GMP_ERR_NO_TEXT"))
			return
		net.SendChatPacket("/%s %s" % (command, text))
		self.SetStatus(TF("GMP_SENT", "/" + command))

	def __SetEventEmpire(self, empire):
		self.eventEmpire = empire
		for i, button in enumerate(self.eventEmpireRow.buttons):
			button.SetOn(i == empire)

	def __OnEvent(self, start):
		hours = SafeToken(self.fields["ev_hours"].GetText()) or "1"
		if not hours.isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		sent = 0
		for (key, privType) in (("ev_exp", 4), ("ev_drop", 1), ("ev_yang", 2)):
			value = SafeToken(self.fields[key].GetText()) or "0"
			if not value.isdigit():
				self.SetError(T("GMP_ERR_NUMBER"))
				return
			value = min(1000, int(value))
			if start and value <= 0:
				continue
			if start:
				net.SendChatPacket("/priv_empire %d %d %d %s" % (self.eventEmpire, privType, value, hours))
			else:
				net.SendChatPacket("/priv_empire %d %d 0 0" % (self.eventEmpire, privType))
			sent += 1
		if start and not sent:
			self.SetError(T("GMP_ERR_EVENT_EMPTY"))
			return
		self.SetStatus(T("GMP_EV_STARTED") if start else T("GMP_EV_STOPPED"))

	def __ConfirmCmd(self, command, questionKey):
		self.__Confirm(T(questionKey), self.__Cmd, command)

	def __OnRestart(self):
		self.__Confirm(T("GMP_Q_RESTART"), self.__DoRestart)

	def __DoRestart(self):
		net.SendChatPacket("/gmpanel_restartserver")
		self.__Pending("restart")

	def SetRestartServerResult(self, data):
		self.__Done("restart")
		if data == "OK":
			self.SetStatus(T("GMP_RESTART_OK"))
		else:
			self.SetError(TF("GMP_ERR", data))

	

	def __BuildItems(self):
		import interfaceModule as interfacemodule
		p = self.__Parent("items")
		m = self.__Mem
		rows = []
		search = self.__Field("item_search", 24)
		# The search has a text of its own for an item, a bonus and a stone,
		# and while a bonus or a stone is picked its button is "Back": the word
		# typed for an item no longer filters the bonuses (Kiciamol, 9 October).
		self.itemsSearchLabel = Label(T("GMP_SEARCH_LABEL"))
		self.itemsClearButton = self.__Button(T("GMP_CLEAR"), m(self.__OnItemsClearSearch))
		rows.append(FormRow(self, p, [
			("label", self.itemsSearchLabel),
			("edit", search, 80, 1),
			("button", self.itemsClearButton, 70),
		]))
		categories = list(interfacemodule.GM_PANEL_CATEGORY_LIST) + [("stone", T("GMP_CAT_STONES"))]
		self.itemCategoryRow = GridRow(self, p, 6, [(label, m(self.__OnItemCategory), (code,)) for (code, label) in categories])
		self.itemCategoryCodes = [code for (code, label) in categories]
		rows.append(self.itemCategoryRow)
		self.itemsHeader = HeaderRow(self, p, T("GMP_PICK_ITEM"))
		rows.append(self.itemsHeader)
		self.itemsList = ListRow(self, p, 8, m(self.__OnItemsPick))
		rows.append(self.itemsList)

		rows.append(HeaderRow(self, p, T("GMP_HDR_NEW_ITEM")))
		self.itemSelected = Label(T("GMP_NO_ITEM"), COLOR_GOLD)
		rows.append(FormRow(self, p, [("label", Label(T("GMP_ITEM"))), ("value", self.itemSelected, 100, 1)]))
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_COUNT"))), ("edit", self.__Field("item_count", 5, True, "1"), 44, 0),
			("label", Label(T("GMP_FOR"))), ("edit", self.__Field("item_owner", 24, False, player.GetName()), 90, 1),
		]))
		self.itemPlaceRow = GridRow(self, p, 3, [
			(T("GMP_PLACE_INV"), m(self.__OnItemPlace), ("inv",)),
			(T("GMP_PLACE_SAFE"), m(self.__OnItemPlace), ("safe",)),
			(T("GMP_PLACE_MALL"), m(self.__OnItemPlace), ("mall",)),
		])
		rows.append(self.itemPlaceRow)
		rows.append(HeaderRow(self, p, T("GMP_HDR_BONUS")))
		self.bonusButtons = []
		for i in xrange(7):
			button = self.__Button(T("GMP_BONUS_NONE"), m(self.__OnPickBonus), i)
			value = self.__Field("bonus_value_%d" % i, 5, True, "0")
			self.bonusButtons.append(button)
			rows.append(FormRow(self, p, [
				("label", Label("%d." % (i + 1))),
				("button", button, 220),
				("edit", value, 50, 1),
			]))
		rows.append(HeaderRow(self, p, T("GMP_HDR_STONES")))
		self.stoneRow = GridRow(self, p, 3, [(T("GMP_EMPTY"), m(self.__OnPickStone), (i,)) for i in xrange(3)])
		rows.append(self.stoneRow)
		rows.append(GridRow(self, p, 2, [
			(T("GMP_CREATE"), m(self.__OnCreateItem), (), COLOR_GREEN),
			(T("GMP_RESET_FORM"), m(self.__OnItemsReset)),
		]))
		self.sections["items"] = rows
		self.__OnItemPlace("inv")
		self.__MarkCategory()

	def __MarkCategory(self):
		for i, button in enumerate(self.itemCategoryRow.buttons):
			button.SetOn(self.itemsMode == "item" and self.itemCategoryCodes[i] == self.itemsCategory)

	def __OnItemCategory(self, code):
		self.itemsCategory = code
		self.__SetItemsMode("item")
		key = "stone" if code == "stone" else "vnum:" + code
		if key not in self.lists:
			self.__FetchList("gmpanel_itemlist", code, key)
		self.__RefreshItemsList()

	def __OnItemsClearSearch(self):
		if self.itemsMode != "item":
			self.__SetItemsMode("item")
			return
		self.fields["item_search"].SetText("")
		self.itemsFilter = ""
		self.__RefreshItemsList()

	def __SetItemsMode(self, mode, index=0):
		oldMode = self.itemsMode
		if "item_search" in self.fields:
			self.itemsSearchSaved[oldMode] = self.fields["item_search"].GetText()
			text = self.itemsSearchSaved.get(mode, "") if mode == "item" else ""
			self.fields["item_search"].SetText(text)
			self.itemsFilter = text
		if oldMode == "item" and mode != "item":
			self.itemsReturnScroll = self.scroll.get("items", 0)
			self.itemsReturnCategory = self.itemsCategory
		self.itemsMode = mode
		self.itemsModeIndex = index
		if mode == "item":
			self.itemsHeader.SetText(T("GMP_PICK_ITEM"))
			self.itemsSearchLabel.SetText(T("GMP_SEARCH_LABEL"))
			self.itemsClearButton.SetText(T("GMP_CLEAR"))
		elif mode == "bonus":
			self.itemsHeader.SetText(TF("GMP_PICK_BONUS", index + 1))
			self.itemsSearchLabel.SetText(T("GMP_SEARCH_BONUS"))
			self.itemsClearButton.SetText(T("GMP_BACK"))
		elif mode == "stone":
			self.itemsHeader.SetText(TF("GMP_PICK_STONE", index + 1))
			self.itemsSearchLabel.SetText(T("GMP_SEARCH_STONE"))
			self.itemsClearButton.SetText(T("GMP_BACK"))
		self.__MarkCategory()
		self.__RefreshItemsList()
		if self.section == "items":
			# Back to the item list: where it stood, if its category is the same.
			if mode == "item" and oldMode != "item" and self.itemsCategory == self.itemsReturnCategory:
				self.scroll["items"] = self.itemsReturnScroll
			else:
				self.scroll["items"] = 0
			self.__Relayout()

	def __ApplyLabel(self, suffix):
		for prefix in ("TOOLTIP_APPLY_", "TOOLTIP_"):
			getter = getattr(localeInfo, prefix + suffix, None)
			if getter is None:
				continue
			try:
				return getter(0).replace(" 0%", "").replace(" +0", "").replace(" 0", "")
			except Exception:
				try:
					return str(getter)
				except Exception:
					pass
		return suffix

	def __RefreshItemsList(self):
		import interfaceModule as interfacemodule
		query = self.itemsFilter.lower()
		if self.itemsMode == "bonus":
			entries = [("0", T("GMP_BONUS_NONE"))] + [(str(n), self.__ApplyLabel(s)) for (n, s) in interfacemodule.GM_PANEL_APPLY_SUFFIXES]
			selected = self.bonusTypes[self.itemsModeIndex]
		elif self.itemsMode == "stone":
			entries = [("0", T("GMP_EMPTY"))] + self.lists.get("stone", [])
			selected = self.stones[self.itemsModeIndex]
		else:
			key = "stone" if self.itemsCategory == "stone" else "vnum:" + self.itemsCategory
			entries = self.lists.get(key, [])
			selected = self.itemVnum
		if query:
			entries = [e for e in entries if query in e[1].lower() or query == e[0]]
		loading = self.listBusy is not None or bool(self.listQueue)
		self.itemsList.selected = selected
		self.itemsList.SetEntries(entries, T("GMP_LOADING") if loading and not entries else T("GMP_NO_RESULTS"))

	def __OnItemsPick(self, value, label):
		if self.itemsMode == "bonus":
			self.bonusTypes[self.itemsModeIndex] = value
			self.bonusButtons[self.itemsModeIndex].SetText(label if value != "0" else T("GMP_BONUS_NONE"))
			self.__SetItemsMode("item")
		elif self.itemsMode == "stone":
			self.stones[self.itemsModeIndex] = value
			self.stoneRow.buttons[self.itemsModeIndex].SetText(label if value != "0" else T("GMP_EMPTY"))
			self.__SetItemsMode("item")
		else:
			self.itemVnum = value
			self.itemLabel = label
			self.itemSelected.SetText("%s (%s)" % (label, value))

	def __OnPickBonus(self, index):
		self.__SetItemsMode("bonus", index)

	def __OnPickStone(self, index):
		if "stone" not in self.lists:
			self.__FetchList("gmpanel_itemlist", "stone", "stone")
		self.__SetItemsMode("stone", index)

	def __OnItemPlace(self, place):
		self.itemPlace = place
		for i, code in enumerate(("inv", "safe", "mall")):
			self.itemPlaceRow.buttons[i].SetOn(code == place)

	def __OnItemsReset(self):
		self.itemVnum = "0"
		self.itemSelected.SetText(T("GMP_NO_ITEM"))
		self.bonusTypes = ["0"] * 7
		self.stones = ["0"] * 3
		for i in xrange(7):
			self.bonusButtons[i].SetText(T("GMP_BONUS_NONE"))
			self.fields["bonus_value_%d" % i].SetText("0")
		for button in self.stoneRow.buttons:
			button.SetText(T("GMP_EMPTY"))
		self.fields["item_count"].SetText("1")
		self.__SetItemsMode("item")

	def __OnCreateItem(self):
		owner = SafeToken(self.fields["item_owner"].GetText()) or player.GetName()
		if self.itemVnum in ("", "0"):
			self.SetError(T("GMP_ERR_NO_ITEM"))
			return
		count = SafeToken(self.fields["item_count"].GetText()) or "1"
		if not count.isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		fields = [owner, self.itemVnum, count, self.itemPlace]
		fields += [self.stones[i] for i in xrange(3)] + ["0", "0", "0"]
		for i in xrange(7):
			value = SafeToken(self.fields["bonus_value_%d" % i].GetText()) or "0"
			if not value.lstrip("-").isdigit():
				value = "0"
			fields += [self.bonusTypes[i], value]
		net.SendChatPacket("/gmpanel_createitem %s" % "|".join(fields))
		self.__Pending("createitem")

	def SetCreateItemResult(self, data):
		self.__Done("createitem")
		messages = {
			"OK": None,
			"ERR_OWNER_OFFLINE": "GMP_ERR_OWNER_OFFLINE",
			"ERR_BADVNUM": "GMP_ERR_BADVNUM",
			"ERR_SAFEBOX_CLOSED": "GMP_ERR_SAFEBOX",
			"ERR_MALL_CLOSED": "GMP_ERR_MALL",
			"ERR_NOSPACE": "GMP_ERR_NOSPACE",
		}
		if data == "OK":
			self.SetStatus(T("GMP_ITEM_CREATED"))
		elif data in messages:
			self.SetError(T(messages[data]))
		else:
			self.SetError(TF("GMP_ERR", data))

	

	def __BuildAccounts(self):
		p = self.__Parent("accounts")
		m = self.__Mem
		rows = []
		nick = self.__Field("acc_nick", 24)
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_NICK"))), ("edit", nick, 100, 1),
			("button", self.__Button(T("GMP_ACC_CHECK"), m(self.__OnAccount), "check"), 110),
		]))
		self.accountInfo = TextRow(self, p, "")
		rows.append(self.accountInfo)
		rows.append(HeaderRow(self, p, T("GMP_HDR_BAN")))
		self.banDaysRow = GridRow(self, p, 4, [(TF("GMP_DAYS", d), m(self.__OnBanDays), (d,)) for d in BAN_DAYS])
		rows.append(self.banDaysRow)
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_BAN_DAYS"))), ("edit", self.__Field("ban_days", 4, True, "1"), 40, 1),
		]))
		rows.append(GridRow(self, p, 3, [
			(T("GMP_BAN_TEMP"), m(self.__OnAccountConfirm), ("temp", "GMP_Q_BAN_TEMP"), COLOR_RED),
			(T("GMP_BAN_PERM"), m(self.__OnAccountConfirm), ("perm", "GMP_Q_BAN_PERM"), COLOR_RED),
			(T("GMP_UNBAN"), m(self.__OnAccount), ("unlock",)),
		]))
		rows.append(GridRow(self, p, 2, [
			(T("GMP_KICK_ACC"), m(self.__OnAccountConfirm), ("kick", "GMP_Q_KICK"), COLOR_RED),
			(T("GMP_MUTE_LIST"), m(self.__Cmd), ("block_chat_list",)),
		]))
		rows.append(HeaderRow(self, p, T("GMP_HDR_MUTE")))
		rows.append(GridRow(self, p, 4, [(T(key), m(self.__OnAccMute), (code,)) for (code, key) in MUTE_TIMES] + [
			(T("GMP_UNMUTE"), m(self.__OnAccMute), ("0",)),
		]))
		rows.append(HeaderRow(self, p, T("GMP_HDR_GM")))
		self.rankRow = GridRow(self, p, 4, [(T(key), m(self.__OnRank), (code,)) for (code, key) in GM_RANKS])
		rows.append(self.rankRow)
		rows.append(GridRow(self, p, 2, [
			(T("GMP_GM_ADD"), m(self.__OnAddGM), ("add",)),
			(T("GMP_GM_REMOVE"), m(self.__OnAddGM), ("remove",), COLOR_RED),
		]))
		self.gmHint = TextRow(self, p, T("GMP_GM_HINT"))
		rows.append(self.gmHint)
		
		
		self.gmHint2 = TextRow(self, p, "")
		self.gmHint2.active = False
		rows.append(self.gmHint2)
		self.sections["accounts"] = rows
		self.__OnBanDays(1)
		self.__OnRank("HIGH_WIZARD")

	def __AccNick(self):
		nick = SafeToken(self.fields["acc_nick"].GetText())
		if not nick:
			self.SetError(T("GMP_ERR_NO_NICK"))
		return nick

	def __OnBanDays(self, days):
		self.banDays = days
		self.fields["ban_days"].SetText(str(days))
		for i, button in enumerate(self.banDaysRow.buttons):
			button.SetOn(BAN_DAYS[i] == days)

	def __OnRank(self, rank):
		self.gmRank = rank
		for i, button in enumerate(self.rankRow.buttons):
			button.SetOn(GM_RANKS[i][0] == rank)

	def __OnAccountConfirm(self, action, questionKey):
		nick = self.__AccNick()
		if not nick:
			return
		days = SafeToken(self.fields["ban_days"].GetText()) or "1"
		self.__Confirm(TF(questionKey, nick, days) if action == "temp" else TF(questionKey, nick), self.__OnAccount, action)

	def __OnAccount(self, action):
		nick = self.__AccNick()
		if not nick:
			return
		days = SafeToken(self.fields["ban_days"].GetText()) or "1"
		if not days.isdigit():
			days = "1"
		net.SendChatPacket("/gmpanel_account %s|%s|%s|-" % (nick, action, days))
		self.lastAccountAction = action
		self.__Pending("account")

	def SetAccountResult(self, data):
		self.__Done("account")
		if data.startswith("STATUS|"):
			parts = data.split("|")
			if len(parts) >= 3:
				locked = parts[1] != "OK" or parts[2] == "LOCKED"
				self.accountInfo.SetText(TF("GMP_ACC_STATUS", parts[1], parts[2]), COLOR_RED if locked else COLOR_GREEN)
				self.SetStatus(T("GMP_READY"))
			return
		codes = {"ERR_NOTFOUND": "GMP_NOT_FOUND", "ERR_BADNAME": "GMP_ERR_BAD_NICK", "ERR_NOTONLINE": "GMP_ERR_NOT_ONLINE"}
		if data == "OK":
			self.SetStatus(T("GMP_SAVED"))
			if getattr(self, "lastAccountAction", "") != "kick":
				self.__OnAccount("check")
		elif data in codes:
			self.SetError(T(codes[data]))
		else:
			self.SetError(TF("GMP_ERR", data))

	def __OnAccMute(self, duration):
		nick = self.__AccNick()
		if not nick:
			return
		net.SendChatPacket("/block_chat %s %s" % (nick, duration))
		self.SetStatus(TF("GMP_SENT", "/block_chat %s %s" % (nick, duration)))

	def __OnAddGM(self, action):
		nick = self.__AccNick()
		if not nick:
			return
		if action == "remove":
			self.__Confirm(TF("GMP_Q_GM_REMOVE", nick), self.__DoAddGM, nick, action)
		else:
			self.__DoAddGM(nick, action)

	def __DoAddGM(self, nick, action):
		if "addgm" in self.pending:
			return
		self.__SetGMHint(T("GMP_GM_HINT"))
		net.SendChatPacket("/gmpanel_addgm %s|%s|%s" % (nick, self.gmRank, action))
		self.__Pending("addgm", 10.0)

	def SetAddGMResult(self, data):
		# Any answer, a late one too, ends the wait; nothing is sent again by
		# itself, because a missing reply does not prove the write failed.
		self.__Done("addgm")
		self.__SetGMHint(T("GMP_GM_HINT"))
		codes = {"ERR_NOTFOUND": "GMP_NOT_FOUND", "ERR_BADNAME": "GMP_ERR_BAD_NICK",
			"ERR_PERMISSION": "GM_PANEL_GM_PERMISSION", "ERR_TESTSERVER": "GM_PANEL_GM_TESTSERVER"}
		if data == "OK_EMPTY":
			
			self.SetError(T("GM_PANEL_GM_EMPTY"))
			self.__SetGMHint(T("GM_PANEL_GM_EMPTY_NOTE1"), T("GM_PANEL_GM_EMPTY_NOTE2"), COLOR_RED)
		elif data == "OK_RESTART_UNKNOWN":
			self.SetError(T("GM_PANEL_GM_RESTART_UNKNOWN"))
		elif data.startswith("OK"):
			self.SetStatus(T("GMP_GM_SAVED"))
		elif data in codes:
			self.SetError(T(codes[data]))
		else:
			self.SetError(TF("GMP_ERR", data))

	def __SetGMHint(self, first, second="", color=COLOR_DIM):
		self.gmHint.SetText(first, color)
		self.gmHint2.SetText(second, color)
		if self.gmHint2.active != bool(second):
			self.gmHint2.active = bool(second)
			if self.section == "accounts":
				self.__Relayout()

	

	def __BuildSpawn(self):
		p = self.__Parent("spawn")
		m = self.__Mem
		rows = []
		rows.append(HeaderRow(self, p, T("GMP_HDR_BOTS")))
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_BOT_PID"))), ("edit", self.__Field("bot_pid", 6, True), 50, 1),
			("label", Label(T("GMP_COUNT"))), ("edit", self.__Field("bot_count", 3, True, "1"), 34, 0),
			("button", self.__Button(T("GMP_PICK_DOTS"), m(self.__SetSpawnMode), "availbots"), 80),
		]))
		self.spawnEmpireRow = GridRow(self, p, 3, [(T(key), m(self.__OnSpawnEmpire), (code,)) for (code, key) in EMPIRES])
		rows.append(self.spawnEmpireRow)
		rows.append(GridRow(self, p, 3, [
			(T("GMP_BOT_SPAWN"), m(self.__OnBotSpawn), ("spawn",), COLOR_GREEN),
			(T("GMP_BOT_DESPAWN"), m(self.__OnBotSpawn), ("despawn",)),
			(T("GMP_BOT_ACTIVE"), m(self.__SetSpawnMode), ("botlist",)),
		]))
		rows.append(HeaderRow(self, p, T("GMP_HDR_MOBS")))
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_MOB"))), ("edit", self.__Field("mob_vnum", 6, True), 50, 1),
			("label", Label(T("GMP_COUNT"))), ("edit", self.__Field("mob_count", 2, True, "1"), 30, 0),
			("button", self.__Button(T("GMP_PICK_DOTS"), m(self.__SetSpawnMode), "moblist"), 70),
			("button", self.__Button(T("GMP_SPAWN"), m(self.__OnSpawnMob), "mob"), 70),
		]))
		rows.append(FormRow(self, p, [
			("label", Label(T("GMP_METIN"))), ("edit", self.__Field("metin_vnum", 6, True), 50, 1),
			("label", Label(T("GMP_COUNT"))), ("edit", self.__Field("metin_count", 2, True, "1"), 30, 0),
			("button", self.__Button(T("GMP_PICK_DOTS"), m(self.__SetSpawnMode), "metinlist"), 70),
			("button", self.__Button(T("GMP_SPAWN"), m(self.__OnSpawnMob), "metin"), 70),
		]))
		self.spawnListHeader = HeaderRow(self, p, "")
		self.spawnListHeader.active = False
		rows.append(self.spawnListHeader)
		self.spawnSearch = self.__Field("spawn_search", 24)
		self.spawnSearchRow = FormRow(self, p, [
			("label", Label(T("GMP_SEARCH_LABEL"))), ("edit", self.spawnSearch, 80, 1),
			("button", self.__Button(T("GMP_CLOSE_LIST"), m(self.__SetSpawnMode), None), 80),
		])
		self.spawnSearchRow.active = False
		rows.append(self.spawnSearchRow)
		self.spawnList = ListRow(self, p, 8, m(self.__OnSpawnPick))
		self.spawnList.active = False
		rows.append(self.spawnList)

		rows.append(HeaderRow(self, p, T("GMP_HDR_QUICK")))
		self.tierPoolText = TextRow(self, p, T("GMP_QUICK_HINT"))
		for index, (label, bosses, metins) in enumerate(SPAWN_TIERS):
			rows.append(FormRow(self, p, [
				("value", Label(label, COLOR_LABEL), 62, 0),
				("button", self.__Button(T("GMP_BOSS_1"), m(self.__OnQuick), index, "boss", 1), 70),
				("button", self.__Button(T("GMP_BOSS_5"), m(self.__OnQuick), index, "boss", 5), 70),
				("button", self.__Button(T("GMP_METIN_1"), m(self.__OnQuick), index, "metin", 1), 70),
				("button", self.__Button(T("GMP_METIN_3"), m(self.__OnQuick), index, "metin", 3), 70),
				("button", self.__Button(T("GMP_POOL"), m(self.__OnShowPool), index), 60),
			]))
		rows.append(self.tierPoolText)
		self.sections["spawn"] = rows
		self.__OnSpawnEmpire("1")

	def __OnSpawnEmpire(self, empire):
		self.spawnEmpire = empire
		for i, button in enumerate(self.spawnEmpireRow.buttons):
			button.SetOn(EMPIRES[i][0] == empire)

	def __SetSpawnMode(self, mode):
		self.spawnMode = mode
		active = mode is not None
		self.spawnListHeader.active = active
		self.spawnSearchRow.active = active
		self.spawnList.active = active
		if active:
			titles = {"availbots": "GMP_LIST_AVAILBOTS", "botlist": "GMP_LIST_BOTS", "moblist": "GMP_LIST_MOBS", "metinlist": "GMP_LIST_METINS"}
			self.spawnListHeader.SetText(T(titles[mode]))
			commands = {"availbots": ("gmpanel_available_bots", "-"), "botlist": ("gmpanel_botlist", "-"),
				"moblist": ("gmpanel_moblist", "0"), "metinlist": ("gmpanel_metinlist", "0")}
			if mode not in self.lists or mode in ("availbots", "botlist"):
				self.lists.pop(mode, None)
				(command, arg) = commands[mode]
				self.__FetchList(command, arg, mode)
			self.__RefreshSpawnList()
		if self.section == "spawn":
			if active:
				self.__ScrollIntoView(self.spawnListHeader, self.spawnList)
			self.__Relayout()

	def __RefreshSpawnList(self):
		if not self.spawnMode:
			return
		entries = self.lists.get(self.spawnMode, [])
		query = self.spawnSearch.GetText().strip().lower()
		if query:
			entries = [e for e in entries if query in e[1].lower() or query == e[0]]
		loading = self.listBusy is not None or bool(self.listQueue)
		self.spawnList.SetEntries(entries, T("GMP_LOADING") if loading and not entries else T("GMP_NO_RESULTS"))

	def __OnSpawnPick(self, value, label):
		if self.spawnMode == "availbots":
			self.fields["bot_pid"].SetText(value)
		elif self.spawnMode == "moblist":
			self.fields["mob_vnum"].SetText(value)
		elif self.spawnMode == "metinlist":
			self.fields["metin_vnum"].SetText(value)
		else:
			return
		self.SetStatus(TF("GMP_PICKED", label))
		# MT2009_PLUS_GM_PANEL_SPAWN_PICK_V1: a pick closes the list, as Close
		# list would (Kiciamol, 9 October).
		self.__SetSpawnMode(None)

	def __OnBotSpawn(self, action):
		pid = SafeToken(self.fields["bot_pid"].GetText())
		count = SafeToken(self.fields["bot_count"].GetText()) or "1"
		if not pid.isdigit() or not count.isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		net.SendChatPacket("/gmpanel_spawn %s|%s|%s|%s" % (pid, count, self.spawnEmpire, action))
		self.__Pending("spawn")

	def SetSpawnResult(self, data):
		self.__Done("spawn")
		parts = data.split("|")
		if parts[0] == "OK" and len(parts) >= 4:
			self.SetStatus(TF("GMP_BOTS_DONE", parts[1], parts[2], parts[3]))
		elif data == "ERR_BADEMPIRE":
			self.SetError(T("GMP_ERR_EMPIRE"))
		else:
			self.SetError(TF("GMP_ERR", data))

	def __OnSpawnMob(self, kind):
		vnum = SafeToken(self.fields[kind + "_vnum"].GetText())
		count = SafeToken(self.fields[kind + "_count"].GetText()) or "1"
		if not vnum.isdigit() or not count.isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		net.SendChatPacket("/gmpanel_spawnmob %s|%s|%s" % (vnum, count, kind))
		self.__Pending("spawnmob")

	def SetSpawnMobResult(self, data):
		self.__Done("spawnmob")
		parts = data.split("|")
		if len(parts) >= 4 and parts[1] == "OK":
			self.SetStatus(TF("GMP_SPAWNED", parts[2], parts[3]))
		elif len(parts) >= 2 and parts[1] == "ERR_NOTFOUND":
			self.SetError(T("GMP_ERR_NO_MOB"))
		else:
			self.SetError(TF("GMP_ERR", data))

	def __OnQuick(self, index, kind, count):
		(label, bosses, metins) = SPAWN_TIERS[index]
		pool = bosses if kind == "boss" else metins
		net.SendChatPacket("/gmpanel_spawnrandommobs %s|%d" % (",".join([str(v) for v in pool]), count))
		self.__Pending("spawnboss")

	def __OnShowPool(self, index):
		(label, bosses, metins) = SPAWN_TIERS[index]
		names = []
		try:
			import nonplayer
			for vnum in bosses[:12]:
				names.append(nonplayer.GetMonsterName(vnum))
		except Exception:
			pass
		text = "%s: %s%s" % (label, ", ".join([n for n in names if n]), "..." if len(bosses) > 12 else "")
		self.tierPoolText.SetText(text, COLOR_TEXT)
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	def SetSpawnBossResult(self, data):
		self.__Done("spawnboss")
		parts = data.split("|")
		if parts[0] == "OK" and len(parts) >= 3:
			self.SetStatus(TF("GMP_SPAWNED", parts[1], parts[2]))
		else:
			self.SetError(TF("GMP_ERR", data))

	def SetSpawnMetinResult(self, data):
		self.SetSpawnBossResult(data)

	

	def __BuildTeleport(self):
		p = self.__Parent("teleport")
		m = self.__Mem
		rows = []
		self.tpGroupRow = GridRow(self, p, len(TELEPORT_GROUPS), [(T(key), m(self.__OnTpGroup), (i,)) for i, (key, places) in enumerate(TELEPORT_GROUPS)])
		rows.append(self.tpGroupRow)
		self.tpPlaceRows = []
		for (key, places) in TELEPORT_GROUPS:
			row = GridRow(self, p, 3, [(T(label), m(self.__OnWarp), (x, y)) for (label, x, y) in places])
			row.active = False
			self.tpPlaceRows.append(row)
			rows.append(row)
		rows.append(FormRow(self, p, [
			("label", Label("X")), ("edit", self.__Field("tp_x", 6, True), 50, 1),
			("label", Label("Y")), ("edit", self.__Field("tp_y", 6, True), 50, 1),
			("button", self.__Button(T("GMP_GO"), m(self.__OnWarpXY)), 60),
		]))
		rows.append(TextRow(self, p, T("GMP_TP_HINT")))
		rows.append(HeaderRow(self, p, T("GMP_HDR_WAYPOINTS")))
		self.wpLabels = {}
		for slot in xrange(1, 6):
			label = Label(TF("GMP_WP_EMPTY", slot), COLOR_DIM)
			self.wpLabels[slot] = label
			rows.append(FormRow(self, p, [
				("value", label, 120, 1),
				("button", self.__Button(T("GMP_GO"), m(self.__OnWaypoint), "load", slot), 60),
				("button", self.__Button(T("GMP_WP_SAVE"), m(self.__OnWaypoint), "save", slot), 90),
			]))
		self.sections["teleport"] = rows
		self.__OnTpGroup(0)

	def __OnTpGroup(self, index):
		self.teleportGroup = index
		for i, button in enumerate(self.tpGroupRow.buttons):
			button.SetOn(i == index)
		for i, row in enumerate(self.tpPlaceRows):
			row.active = (i == index)
		if self.section == "teleport":
			self.__Relayout()

	def __OnWarp(self, x, y):
		net.SendChatPacket("/warp %d %d" % (x, y))
		self.SetStatus(TF("GMP_SENT", "/warp %d %d" % (x, y)))

	def __OnWarpXY(self):
		x = SafeToken(self.fields["tp_x"].GetText())
		y = SafeToken(self.fields["tp_y"].GetText())
		if not x.isdigit() or not y.isdigit():
			self.SetError(T("GMP_ERR_NUMBER"))
			return
		self.__OnWarp(int(x), int(y))

	def __OnWaypoint(self, action, slot):
		if action == "load":
			net.SendChatPacket("/gmpanel_waypoint load %d" % slot)
			return
		label = self.__PlaceName()
		net.SendChatPacket("/gmpanel_waypoint save %d %s" % (slot, label))

	def __PlaceName(self):
		try:
			import background
			mapName = background.GetCurrentMapName()
		except Exception:
			mapName = "mapa"
		try:
			name = localeInfo.MINIMAP_ZONE_NAME_DICT[mapName]
		except Exception:
			name = mapName.replace("metin2_map_", "")
		try:
			(x, y, z) = player.GetMainCharacterPosition()
			name = "%s %d,%d" % (name, x // 100, y // 100)
		except Exception:
			pass
		return name.replace(" ", "_")[:31]

	def SetWaypoint(self, data):
		parts = data.split("|")
		if len(parts) < 2:
			return
		try:
			slot = int(parts[0])
		except ValueError:
			return
		self.waypointLabels[slot] = parts[1].replace("_", " ")
		label = self.wpLabels.get(slot)
		if label:
			label.SetText("%d. %s" % (slot, self.waypointLabels[slot]))
			label.SetPackedFontColor(COLOR_TEXT)

	

	def __BuildServer(self):
		import interfaceModule as interfacemodule
		p = self.__Parent("server")
		m = self.__Mem
		rows = []
		rows.append(HeaderRow(self, p, T("GMP_HDR_RATES")))
		rows.append(FormRow(self, p, [
			("label", Label("Exp")), ("edit", self.__Field("rate_exp", 5, True), 40, 1),
			("label", Label("Drop")), ("edit", self.__Field("rate_drop", 5, True), 40, 1),
			("label", Label("Yang")), ("edit", self.__Field("rate_yang", 5, True), 40, 1),
			("button", self.__Button(T("GMP_SAVE"), m(self.__OnSaveRates)), 64),
			("button", self.__Button(T("GMP_FETCH"), m(self.__OnFetchServer)), 64),
		]))
		rows.append(TextRow(self, p, T("GMP_RATES_HINT")))
		rows.append(HeaderRow(self, p, T("GMP_HDR_AI")))
		self.aiStatus = TextRow(self, p, T("GMP_AI_WAIT"))
		rows.append(self.aiStatus)
		self.aiRows = []
		for (key, title, help, kind, lo, hi) in interfacemodule.GM_PANEL_AI_WEIGHT_ROWS:
			label = Label(title, COLOR_TEXT)
			if kind == "bool":
				button = self.__Button("-", m(self.__OnAIToggle), key)
				row = FormRow(self, p, [("value", label, 150, 1), ("button", button, 70)])
				row.toggle = button
			else:
				field = self.__Field("ai_" + key, 4, True)
				hint = Label("%d-%d%s" % (lo, hi, "%" if kind in ("scrap", "chest") else ""), COLOR_DIM)
				row = FormRow(self, p, [("value", label, 150, 1), ("value", hint, 54, 0), ("edit", field, 44, 0),
					("button", self.__Button(T("GMP_SAVE"), m(self.__OnAISave), key), 64)])
			row.key = key
			row.kind = kind
			row.lo = lo
			row.hi = hi
			row.active = False
			self.aiRows.append(row)
			rows.append(row)
		rows.append(HeaderRow(self, p, T("GMP_HDR_RESTART")))
		rows.append(GridRow(self, p, 2, [(T("GMP_RESTART"), m(self.__OnRestart), (), COLOR_RED)]))
		self.sections["server"] = rows

	def __OnFetchServer(self):
		net.SendChatPacket("/gmpanel_getrates")
		net.SendChatPacket("/gmpanel_getaiweights")
		self.__Pending("rates")
		self.__Pending("ai")
		self.aiStatus.SetText(T("GMP_AI_WAIT"), COLOR_DIM)

	def SetRatesResult(self, data):
		self.__Done("rates")
		parts = data.split("|")
		if len(parts) != 3:
			self.SetError(TF("GMP_ERR", data))
			return
		for name, value in zip(("exp", "drop", "yang"), parts):
			self.fields["rate_" + name].SetText(value)

	def __OnSaveRates(self):
		for name in ("exp", "drop", "yang"):
			value = SafeToken(self.fields["rate_" + name].GetText())
			if not value.isdigit() or not (1 <= int(value) <= 10000):
				self.SetError(T("GMP_ERR_RATE"))
				return
		for name in ("exp", "drop", "yang"):
			net.SendChatPacket("/gmpanel_setrate %s|%s" % (name, SafeToken(self.fields["rate_" + name].GetText())))
		self.__Pending("setrate")

	def SetRateSaveResult(self, data):
		self.__Done("setrate")
		if data.startswith("OK"):
			self.SetStatus(T("GMP_SAVED"))
		elif data == "ERR_RANGE":
			self.SetError(T("GMP_ERR_RATE"))
		else:
			self.SetError(TF("GMP_ERR", data))

	def SetAIWeightsResult(self, data):
		import interfaceModule as interfacemodule
		self.__Done("ai")
		values = {}
		for key, raw in zip(interfacemodule.GM_PANEL_AI_WEIGHT_SERVER_ORDER, data.split("|")):
			try:
				values[key] = int(raw)
			except ValueError:
				pass
		if not values:
			self.aiStatus.SetText(TF("GMP_ERR", data), COLOR_RED)
			return
		self.aiValues = values
		for row in self.aiRows:
			raw = values.get(row.key)
			if raw is None:
				row.active = False
				continue
			row.active = True
			if row.kind == "bool":
				row.toggle.SetText(T("GMP_ON") if raw else T("GMP_OFF"))
				row.toggle.SetOn(bool(raw))
			elif row.kind == "chest":
				self.fields["ai_" + row.key].SetText("-" if raw < 0 else str(max(1, int(round(raw / 10.0)))))
			else:
				self.fields["ai_" + row.key].SetText(str(raw))
		self.aiStatus.SetText(T("GMP_AI_HINT"), COLOR_DIM)
		if self.section == "server":
			self.__Relayout()

	def __OnAIToggle(self, key):
		if key not in self.aiValues:
			return
		value = 0 if self.aiValues[key] else 1
		net.SendChatPacket("/gmpanel_setaiweight %s|%d" % (key, value))
		self.aiValues[key] = value
		for row in self.aiRows:
			if row.key == key:
				row.toggle.SetText(T("GMP_ON") if value else T("GMP_OFF"))
				row.toggle.SetOn(bool(value))
		self.__Pending("setai")

	def __OnAISave(self, key):
		if key not in self.aiValues:
			return
		for row in self.aiRows:
			if row.key != key:
				continue
			text = SafeToken(self.fields["ai_" + key].GetText())
			if not text.isdigit():
				self.SetError(T("GMP_ERR_NUMBER"))
				return
			value = max(row.lo, min(row.hi, int(text)))
			wire = value * 10 if row.kind == "chest" else value
			self.fields["ai_" + key].SetText(str(value))
			net.SendChatPacket("/gmpanel_setaiweight %s|%d" % (key, wire))
			self.aiValues[key] = wire
			self.__Pending("setai")

	def SetAIWeightResult(self, data):
		self.__Done("setai")
		if data.startswith("OK"):
			self.SetStatus(T("GMP_SAVED"))
		else:
			self.SetError(TF("GMP_ERR", data))

	

	def __BuildCommands(self):
		import interfaceModule as interfacemodule
		p = self.__Parent("cmds")
		m = self.__Mem
		rows = []
		self.cmdSearch = self.__Field("cmd_search", 24)
		rows.append(FormRow(self, p, [("label", Label(T("GMP_SEARCH_LABEL"))), ("edit", self.cmdSearch, 80, 1)]))
		self.cmdList = ListRow(self, p, 11, m(self.__OnCmdPick))
		rows.append(self.cmdList)
		rows.append(TextRow(self, p, T("GMP_CMDS_HINT")))
		self.sections["cmds"] = rows
		self.cmdEntries = [(str(i), text) for i, text in enumerate(interfacemodule.GM_COMMANDS_LIST)]
		self.cmdList.SetEntries(self.cmdEntries)

	def __OnCmdPick(self, value, label):
		chat.AppendChat(chat.CHAT_TYPE_INFO, label)

	

	def __OnEnterSection(self, name):
		if name == "items":
			key = "stone" if self.itemsCategory == "stone" else "vnum:" + self.itemsCategory
			if key not in self.lists:
				self.__FetchList("gmpanel_itemlist", self.itemsCategory, key)
			self.__RefreshItemsList()
		elif name == "teleport" and not self.waypointsLoaded:
			self.waypointsLoaded = True
			net.SendChatPacket("/gmpanel_waypoint list")
		elif name == "server" and not self.serverLoaded:
			self.serverLoaded = True
			self.__OnFetchServer()

	

	def __FetchList(self, command, arg, target):
		for (c, a, t) in self.listQueue:
			if t == target:
				return
		if self.listBusy and self.listBusy[2] == target:
			return
		self.listQueue.append((command, arg, target))
		self.__NextList()

	def __NextList(self):
		if self.listBusy or not self.listQueue:
			return
		self.listBusy = self.listQueue.pop(0)
		self.listBuffer = ""
		self.listDeadline = clientclock.Now() + REQUEST_TIMEOUT
		(command, arg, target) = self.listBusy
		net.SendChatPacket("/%s %s" % (command, arg))

	def SetItemListChunk(self, data):
		import interfaceModule as interfacemodule
		if not self.listBusy:
			return
		try:
			(isLast, chunk) = data.split("|", 1)
		except ValueError:
			return
		self.listBuffer += chunk
		self.listDeadline = clientclock.Now() + REQUEST_TIMEOUT
		if isLast != "1":
			return
		(command, arg, target) = self.listBusy
		entries = []
		for entry in self.listBuffer.split(";"):
			if ":" not in entry:
				continue
			(vnum, name) = entry.split(":", 1)
			if target == "botlist" and vnum == "0":
				continue
			listTarget = "vnum" if target.startswith("vnum") else target
			nameIn = getattr(interfacemodule, "GMPanelNameIn", None)
			name = name.replace("_", " ")
			if nameIn:
				name = nameIn(listTarget, vnum, name)
			entries.append((vnum, name))
		if target.startswith("vnum") or target == "stone":
			entries.sort(key=lambda e: e[1])
		self.lists[target] = entries
		self.listBusy = None
		self.listBuffer = ""
		self.__AfterList(target)
		self.__NextList()

	def __AfterList(self, target):
		if self.section == "items":
			self.__RefreshItemsList()
		if self.section == "spawn":
			self.__RefreshSpawnList()

	

	def __Pending(self, key, timeout=REQUEST_TIMEOUT):
		self.pending[key] = clientclock.Now() + timeout
		self.SetStatus(T("GMP_WAITING"), COLOR_DIM)

	def __Done(self, key):
		self.pending.pop(key, None)

	def OnUpdate(self):
		now = clientclock.Now()
		if getattr(self, "refreshAt", 0) and now > self.refreshAt:
			self.refreshAt = 0
			if self.lookupNick:
				net.SendChatPacket("/gmpanel_lookup %s" % self.lookupNick)
		expired = [key for key, deadline in self.pending.items() if now > deadline]
		for key in expired:
			del self.pending[key]
			
			
			self.SetError(T("GM_PANEL_GM_NO_ANSWER") if key == "addgm" else T("GMP_NO_ANSWER"))
		if self.listBusy and now > self.listDeadline:
			self.listBusy = None
			self.listBuffer = ""
			self.__NextList()
			self.__AfterList("")
		if self.section == "items":
			query = self.fields["item_search"].GetText()
			if query != self.itemsFilter:
				self.itemsFilter = query
				self.__RefreshItemsList()
		elif self.section == "spawn" and self.spawnMode:
			query = self.spawnSearch.GetText()
			if query != getattr(self, "spawnFilter", ""):
				self.spawnFilter = query
				self.__RefreshSpawnList()
		elif self.section == "cmds":
			query = self.cmdSearch.GetText().strip().lower()
			if query != self.cmdFilter:
				self.cmdFilter = query
				entries = self.cmdEntries
				if query:
					entries = [e for e in entries if query in e[1].lower()]
				self.cmdList.SetEntries(entries)

	

	def __Confirm(self, text, func, *args):
		import uiCommon
		if self.dialog:
			self.dialog.Close()
		dialog = uiCommon.QuestionDialog()
		dialog.SetText(text)
		dialog.SetWidth(max(280, TextWidth(text) + 40))
		self.confirmCall = (ui.__mem_func__(func), args)
		dialog.SetAcceptEvent(ui.__mem_func__(self.__OnConfirmYes))
		dialog.SetCancelEvent(ui.__mem_func__(self.__OnConfirmNo))
		dialog.Open()
		self.dialog = dialog

	def __OnConfirmYes(self):
		call = getattr(self, "confirmCall", None)
		self.confirmCall = None
		if self.dialog:
			self.dialog.Close()
			self.dialog = None
		if call:
			(func, args) = call
			apply(func, args)

	def __OnConfirmNo(self):
		self.confirmCall = None
		if self.dialog:
			self.dialog.Close()
			self.dialog = None
