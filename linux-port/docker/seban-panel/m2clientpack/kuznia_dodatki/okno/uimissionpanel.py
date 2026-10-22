# MT2009_NASZE_OKNO_CTRLN_V2: okno Ctrl+N Kuzni Mocy - Misje (Biolog, Polowanie, Metinologia, Bossologia) i Kolekcjoner.
# Staly rozmiar 600x430, bez skalowania. Grafiki: d:/ymir work/ui/game/kuznia_okno/*.tga (paczka Kuzni).
# Dane: "MP ..." (misje, serwer mission_panel) i "KC ..." (Kolekcjoner, serwer "/kolekcje").
import ui
import wndMgr
import player
import app
import net
import item
import binascii
import gamefont
import uiquestbonuspreview

ART = 'd:/ymir work/ui/game/kuznia_okno/'
W, H = 600, 430
GOLD = 0xfff3e3bd
LIGHT = 0xffe7e0d2
MUTED = 0xff8d8472
GREEN = 0xff9fe08a
AMBER = 0xffffd98a
RED = 0xffd98a7a
LOCKED = 0xff8c8070
MISSION_KINDS = ('biolog', 'hunting', 'metin', 'boss')
MISSION_NAMES = {'biolog': 'Badania Biologa', 'hunting': 'Polowanie', 'metin': 'Metinologia', 'boss': 'Bossologia'}
FINAL_ID = 99999
# Nazwy bonusow z panelu (Kuznia Mocy, ta sama lista co przy wyborze bonusu) - klient nie zna wszystkich.
POINT_NAMES = {6: ('Maks. P\xaf', ''), 8: ('Maks. PM', ''), 10: ('Maks. wytrzyma\xb3o\x9c\xe6', ''), 12: ('Si\xb3a', ''), 13: ('Witalno\x9c\xe6', ''), 14: ('Zr\xeaczno\x9c\xe6', ''), 15: ('Inteligencja', ''), 16: ('Obrona', ''), 17: ('Szybko\x9c\xe6 ataku', '%'), 18: ('Warto\x9c\xe6 ataku (sta\xb3a)', ''), 19: ('Szybko\x9c\xe6 ruchu', '%'), 21: ('Szybko\x9c\xe6 zakl\xeacia', '%'), 22: ('Warto\x9c\xe6 magicznego ataku', ''), 23: ('Magiczna warto\x9c\xe6 obrony', ''), 28: ('Punkty umiej\xeatno\x9cci', ''), 32: ('Regeneracja P\xaf', '%'), 33: ('Regeneracja PM', '%'), 34: ('Zasi\xeag \xb3uku', 'm'), 37: ('Szansa na otrucie', '%'), 38: ('Szansa na omdlenie', '%'), 39: ('Szansa na spowolnienie', '%'), 40: ('Szansa na cios krytyczny', '%'), 41: ('Szansa na przeszywaj\xb9cy', '%'), 42: ('Szansa na kl\xb9tw\xea', '%'), 43: ('Silny przeciw ludziom', '%'), 44: ('Silny przeciw zwierz\xeatom', '%'), 45: ('Silny przeciw orkom', '%'), 46: ('Silny przeciw mistykom', '%'), 47: ('Silny przeciw nieumar\xb3ym', '%'), 48: ('Silny przeciw diab\xb3om', '%'), 49: ('Silny przeciw owadom', '%'), 50: ('Silny przeciw ogniu', '%'), 51: ('Silny przeciw lodowi', '%'), 52: ('Silny przeciw pustyni', '%'), 53: ('Silny przeciw potworom', '%'), 54: ('Silny przeciw wojownikom', '%'), 55: ('Silny przeciw ninja', '%'), 56: ('Silny przeciw surom', '%'), 57: ('Silny przeciw szamanom', '%'), 58: ('Silny przeciw drzewom', '%'), 59: ('Odporno\x9c\xe6 na wojownik\xf3w', '%'), 60: ('Odporno\x9c\xe6 na ninja', '%'), 61: ('Odporno\x9c\xe6 na sury', '%'), 62: ('Odporno\x9c\xe6 na szaman\xf3w', '%'), 63: ('Kradzie\xbf P\xaf', '%'), 64: ('Kradzie\xbf PM', '%'), 65: ('Szansa na kradzie\xbf PM', '%'), 66: ('Odzyskanie PM po obra\xbfeniach', '%'), 67: ('Szansa na blok', '%'), 68: ('Szansa na unik strza\xb3', '%'), 69: ('Odporno\x9c\xe6 na miecze', '%'), 70: ('Odporno\x9c\xe6 na bro\xf1 dwur\xeaczn\xb9', '%'), 71: ('Odporno\x9c\xe6 na sztylety', '%'), 72: ('Odporno\x9c\xe6 na dzwony', '%'), 73: ('Odporno\x9c\xe6 na wachlarze', '%'), 74: ('Odporno\x9c\xe6 na strza\xb3y', '%'), 75: ('Odporno\x9c\xe6 na ogie\xf1', '%'), 76: ('Odporno\x9c\xe6 na b\xb3yskawice', '%'), 77: ('Odporno\x9c\xe6 na magi\xea', '%'), 78: ('Odporno\x9c\xe6 na wiatr', '%'), 79: ('Odbicie obra\xbfe\xf1 fizycznych', '%'), 80: ('Odbicie strza\xb3', '%'), 81: ('Odporno\x9c\xe6 na trucizny', '%'), 82: ('Odzyskanie PM po zabiciu', '%'), 83: ('Bonus do\x9cwiadczenia', '%'), 84: ('Bonus Yang', '%'), 85: ('Bonus dropu przedmiot\xf3w', '%'), 86: ('Bonus mikstur', '%'), 87: ('Odzyskanie P\xaf po zabiciu', '%'), 88: ('Odporno\x9c\xe6 na omdlenie', ''), 89: ('Odporno\x9c\xe6 na spowolnienie', ''), 90: ('Odporno\x9c\xe6 na przewr\xf3cenie', ''), 93: ('Warto\x9c\xe6 ataku', '%'), 94: ('Warto\x9c\xe6 obrony', '%'), 95: ('Warto\x9c\xe6 ataku', ''), 96: ('Warto\x9c\xe6 obrony', ''), 97: ('Warto\x9c\xe6 magicznego ataku (premia)', ''), 98: ('Magiczna warto\x9c\xe6 obrony (premia)', ''), 99: ('Odporno\x9c\xe6 na zwyk\xb3e ataki', '%'), 100: ('Odzysk P\xaf przy trafieniu', '%'), 101: ('Odzysk PM przy trafieniu', '%'), 107: ('Kradzie\xbf Yang', '%'), 114: ('Warto\x9c\xe6 ataku (sklep)', '%'), 115: ('Warto\x9c\xe6 obrony (sklep)', '%'), 116: ('Bonus do\x9cwiadczenia (sklep)', '%'), 117: ('Szansa na zdobycie przedmiot\xf3w (sklep)', '%'), 118: ('Szansa na zdobycie Yang (sklep)', '%'), 119: ('Maks. P\xaf', '%'), 120: ('Maks. PM', '%'), 121: ('Obra\xbfenia umiej\xeatno\x9cci', '%'), 122: ('\x8crednie obra\xbfenia', '%'), 123: ('Odporno\x9c\xe6 na obra\xbfenia umiej\xeatno\x9cci', '%'), 124: ('Odporno\x9c\xe6 na \x9crednie obra\xbfenia', '%'), 130: ('Bonus kostiumu', '%'), 131: ('Magiczny atak', '%'), 132: ('Magiczny/fizyczny atak', '%'), 133: ('Odporno\x9c\xe6 na l\xf3d', '%'), 134: ('Odporno\x9c\xe6 na ziemi\xea', '%'), 135: ('Odporno\x9c\xe6 na mrok', '%'), 136: ('Odporno\x9c\xe6 na cios krytyczny', '%'), 137: ('Odporno\x9c\xe6 na przeszywaj\xb9cy', '%'), 138: ('Terror', '%'), 139: ('Regeneracja wytrzyma\xb3o\x9cci', '%'), 140: ('Atak sztyletem przeciw potworom', ''), 141: ('Warto\x9c\xe6 ataku przeciw potworom', ''), 142: ('Odporno\x9c\xe6 na potwory', '\x89'), 143: ('Poch\xb3anianie obra\xbfe\xf1', '%'), 144: ('Poch\xb3anianie obra\xbfe\xf1 od potwor\xf3w', '%'), 145: ('Prze\xb3amanie odporno\x9cci na og\xb3uszenie', ''), 146: ('Prze\xb3amanie kl\xb9twy \x9cwi\xb9tyni', ''), 147: ('Czas trwania umiej\xeatno\x9cci', '%'), 148: ('Silny przeciw potworom z Doliny Ork\xf3w', '%'), 149: ('Silny przeciw Metinom', '%'), 150: ('Silny przeciw bossom', '%'), 151: ('Magiczny atak przeciw potworom', '%'), 152: ('Prze\xb3amanie odporno\x9cci na miecz', '%'), 153: ('Prze\xb3amanie odporno\x9cci na bro\xf1 dwur\xeaczn\xb9', '%'), 154: ('Prze\xb3amanie odporno\x9cci na sztylet', '%'), 155: ('Prze\xb3amanie odporno\x9cci na dzwonek', '%'), 156: ('Prze\xb3amanie odporno\x9cci na wachlarz', '%'), 157: ('Prze\xb3amanie odporno\x9cci na \xb3uk', '%'), 158: ('Szansa na zbieranie', '%'), 159: ('Szansa na nauk\xea', '%'), 160: ('Odporno\x9c\xe6 na ludzi', '%'), 161: ('Magiczny atak', ''), 162: ('Szansa na podpalenie', '%'), 163: ('Zamiana obra\xbfe\xf1 na PM', '%'), 164: ('Szansa na rzadki \xb3up', '%'), 165: ('Magiczna warto\x9c\xe6 ataku przeciw potworom', ''), 166: ('Szansa na unieruchomienie', '%'), 167: ('Atak specjalny', ''), 168: ('Kara za \x9cmier\xe6', '%'), 178: ('Moc \xbfywio\xb3u: b\xb3yskawica', '%'), 179: ('Moc \xbfywio\xb3u: ogie\xf1', '%'), 180: ('Moc \xbfywio\xb3u: l\xf3d', '%'), 181: ('Moc \xbfywio\xb3u: wiatr', '%'), 182: ('Moc \xbfywio\xb3u: ziemia', '%'), 183: ('Moc \xbfywio\xb3u: mrok', '%')}

_window = None
_missions = dict((k, []) for k in MISSION_KINDS)
_pending = None
_bioReadyAt = 0.0
_cats = []
_catsPending = None
_catsAt = 0.0
_taskButton = None


def Font(size, bold=False):
	name = gamefont.GetCurrentFontLarge().split(':')[0]
	return name + ':' + str(size) + ('b' if bold else '')


def Clock(seconds):
	seconds = max(0, int(seconds))
	return '%02d:%02d:%02d' % (seconds // 3600, (seconds // 60) % 60, seconds % 60)


def Unhex(value):
	if value == '-':
		return ''
	try:
		return binascii.unhexlify(value)
	except (TypeError, binascii.Error):
		return ''


def Bonuses(token):
	rows = []
	if token and token != '-':
		for part in token.split(','):
			try:
				point, value, key = part.split(':', 2)
				point, value = int(point), int(value)
				if point in POINT_NAMES:
					name, unit = POINT_NAMES[point]
					rows.append('%s: %s%d%s' % (name, '+' if value >= 0 else '', value, unit))
				else:
					rows.append(uiquestbonuspreview.FormatRow(point, key, value))
			except (ValueError, TypeError):
				pass
	return rows


# item.SelectItem w tym kliencie nic nie zwraca (None) - wynik nie jest sprawdzany.
def ItemName(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetItemName() or str(vnum)
	except Exception:
		return str(vnum)


def ItemIcon(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetIconImageFileName() or ''
	except Exception:
		return ''


def Duration(seconds):
	seconds = int(seconds)
	if seconds <= 0:
		return 'bez przerwy'
	if seconds % 3600 == 0:
		return '%d godz.' % (seconds // 3600)
	if seconds >= 60:
		return '%d min' % (seconds // 60)
	return '%d s' % seconds


class Area(ui.Window):
	"""Przezroczysty obszar klikany (wiersz listy, karta)."""

	def __init__(self, parent, x, y, w, h, click, wheel=None):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(w, h)
		self.click = click
		self.wheel = wheel
		self.Show()

	def OnMouseLeftButtonUp(self):
		if self.click:
			self.click()
		return True

	def OnMouseWheel(self, delta):
		if self.wheel:
			self.wheel(1 if delta > 0 else -1)
			return True
		return False


class Model(ui.Window):
	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterRenderTarget(self, layer)


class Panel(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag('movable')
		self.AddFlag('float')
		self.SetSize(W, H)
		self.SetCenterPosition()
		self.view = 'mis'
		self.mcat = 'biolog'
		self.ccat = None
		self.sel = {}
		self.follow = True
		self.listTop = 0
		self.gridTop = 0
		self.renderedRace = 0
		self.modelReady = False
		self.nextRequest = 0.0
		self.dyn = []

		self.background = self.Img(self, 'bg', 0, 0)  # odwolanie trzymane - inaczej Python usuwa obrazek i tlo znika
		self.title = self.Text(self, '', W // 2, 9, GOLD, 13, True, True)
		self.close = self.Button(self, 'close', W - 30, 7, self.Close)
		self.tabs = {}
		for i, (key, label) in enumerate((('mis', 'Misje'), ('kol', 'Kolekcjoner'))):
			x = 18 + i * 92
			self.tabs[key] = (self.Text(self, label, x + 40, 42, MUTED, 12, True, True),
							  self.Img(self, 'tab_line', x, 60),
							  Area(self, x, 38, 80, 24, lambda k=key: self.SelectView(k)))
		Area(self, 12, 72, 162, 316, None, self.ScrollList)
		self.listArea = ui.Window()
		self.listArea.SetParent(self)
		self.listArea.SetPosition(0, 0)
		self.listArea.SetSize(W, H)
		self.listArea.AddFlag('not_pick')
		self.listArea.Show()
		self.body = ui.Window()
		self.body.SetParent(self)
		self.body.SetPosition(0, 0)
		self.body.SetSize(W, H)
		self.body.AddFlag('not_pick')
		self.body.Show()
		self.model = None
		if hasattr(wndMgr, 'RegisterRenderTarget') and hasattr(player, 'Mt2009ModelSelect'):
			self.model = Model()
			self.model.SetParent(self)
			self.model.AddFlag('not_pick')
			self.model.SetPosition(207, 100)
			self.model.SetSize(220, 190)
			wndMgr.SetRenderTarget(self.model.hWnd, getattr(app, 'RENDER_TARGET_INDEX_ILLUSTRATED', 1))
			self.model.Hide()
		self.Hide()

	# --- elementy
	def Img(self, parent, name, x, y, keep=True):
		img = ui.ImageBox()
		img.SetParent(parent)
		img.AddFlag('not_pick')
		img.SetPosition(x, y)
		# Pelna sciezka (ikona przedmiotu z klienta: "icon\item\x.tga") albo nazwa grafiki okna (ART + nazwa + .tga).
		path = name if ('/' in name or '\\' in name or name.lower().endswith('.tga')) else ART + name + '.tga'
		try:
			img.LoadImage(path)
		except Exception:
			pass  # brak obrazka nie przerywa rysowania okna
		img.Show()
		if not keep:
			self.dyn.append(img)
		return img

	def Bar(self, parent, name, x, y, cur, top, keep=False):
		bar = ui.ExpandedImageBox()
		bar.SetParent(parent)
		bar.AddFlag('not_pick')
		bar.SetPosition(x, y)
		try:
			bar.LoadImage(ART + name + '.tga')
		except Exception:
			pass
		bar.SetPercentage(max(0, min(cur, top)), max(1, top))
		bar.Show()
		if not keep:
			self.dyn.append(bar)
		return bar

	def Text(self, parent, text, x, y, color=LIGHT, size=12, bold=False, center=False, keep=True):
		line = ui.TextLine()
		line.SetParent(parent)
		line.AddFlag('not_pick')
		line.SetFontName(Font(size, bold))
		line.SetPosition(x, y)
		if center:
			line.SetHorizontalAlignCenter()
		line.SetPackedFontColor(color)
		line.SetText(text)
		line.Show()
		if not keep:
			self.dyn.append(line)
		return line

	def Button(self, parent, art, x, y, event, label='', keep=True, color=0xff2a1606):
		btn = ui.Button()
		btn.SetParent(parent)
		btn.SetPosition(x, y)
		btn.SetUpVisual(ART + art + '_0.tga')
		btn.SetOverVisual(ART + art + '_1.tga')
		btn.SetDownVisual(ART + art + '_2.tga')
		if label:
			btn.SetText(label)
			try:
				# Klient nie przebudowuje liter po zmianie czcionki - najpierw pusty tekst, potem czcionka i tekst.
				btn.ButtonText.SetText('')
				btn.ButtonText.SetFontName(Font(12))
				btn.ButtonText.SetPackedFontColor(color)
				btn.ButtonText.SetText(label)
			except Exception:
				pass
		btn.SetEvent(event)
		btn.Show()
		if not keep:
			self.dyn.append(btn)
		return btn

	def Slot(self, parent, x, y, icon, locked=False):
		self.Img(parent, 'slot', x, y, False)
		if icon:
			img = self.Img(parent, icon, x, y, False)
			if locked:
				img.SetAlpha(0.45)

	def Clear(self):
		for el in self.dyn:
			el.Hide()
		self.dyn = []

	# --- nawigacja
	def SelectView(self, key):
		self.view = key
		self.listTop = 0
		self.gridTop = 0
		self.follow = True
		if key == 'kol':
			net.SendChatPacket('/kolekcje show')
		self.Refresh()

	def SelectList(self, key):
		if self.view == 'mis':
			self.mcat = key
		else:
			self.ccat = key
		self.gridTop = 0
		self.follow = True
		self.Refresh()

	def ScrollList(self, step):
		self.listTop = max(0, min(self.listTop - step, max(0, len(self.ListRows()) - 6)))
		self.Refresh()

	def ScrollGrid(self, step, total, visible):
		self.gridTop = max(0, min(self.gridTop - step, max(0, total - visible)))
		self.Refresh()

	def Pick(self, index):
		self.sel[self.Key()] = index
		self.follow = False
		self.Refresh()

	def Key(self):
		return (self.view, self.mcat if self.view == 'mis' else self.ccat)

	# --- dane
	def MissionRows(self, kind):
		return [r for r in _missions.get(kind, []) if r['id'] != FINAL_ID or kind == 'biolog']

	def ListRows(self):
		if self.view == 'mis':
			out = []
			for kind in MISSION_KINDS:
				rows = self.MissionRows(kind)
				out.append((kind, MISSION_NAMES[kind], ART + 'cat_' + kind + '.tga',
							len([r for r in rows if r['state'] == 3]), len(rows)))
			return out
		out = []
		for c in _cats:
			icon = ItemIcon(c['icon']) if c['icon'] else ART + 'kat_' + c['key'] + '.tga'  # wlasna ikona kategorii z panelu
			out.append((c['key'], c['name'], icon, len([i for i in c['items'] if i['state'] == 3]), len(c['items'])))
		return out

	def Current(self, rows, done):
		key = self.Key()
		if self.follow or key not in self.sel:
			index = next((i for i, r in enumerate(rows) if not done(r)), max(0, len(rows) - 1))
			self.sel[key] = index
		return min(self.sel[key], max(0, len(rows) - 1))

	# --- rysowanie
	def Refresh(self):
		# Blad rysowania nie moze zablokowac okna (Ctrl+N / przycisk dzialaja dalej) - tylko wpis do syserr.
		try:
			self.Draw()
		except Exception:
			import sys
			try:
				import dbg
				dbg.TraceError('uimissionpanel: %s' % (sys.exc_info()[1],))
			except Exception:
				pass

	def Draw(self):
		if not self.IsShow():
			return
		self.Clear()
		self.title.SetText('M I S J E' if self.view == 'mis' else 'K O L E K C J O N E R')
		for key, (label, line, _area) in self.tabs.items():
			label.SetPackedFontColor(AMBER if key == self.view else MUTED)
			if key == self.view:
				line.Show()
			else:
				line.Hide()
		self.DrawList()
		if self.view != 'mis' or self.mcat == 'biolog':
			self.ShowModel(0)
		if self.view == 'mis':
			if self.mcat == 'biolog':
				self.DrawBiolog()
			else:
				self.DrawStage()
		else:
			self.DrawCollector()

	def DrawList(self):
		rows = self.ListRows()
		current = self.mcat if self.view == 'mis' else self.ccat
		if self.view == 'kol' and current is None and rows:
			self.ccat = current = rows[0][0]
		for n, (key, name, icon, done, total) in enumerate(rows[self.listTop:self.listTop + 6]):
			y = 78 + n * 50
			if key == current:
				self.Img(self.listArea, 'row_on', 18, y, False)
			self.Slot(self.listArea, 24, y + 6, icon)
			self.Text(self.listArea, name, 64, y + 4, GOLD if key == current else LIGHT, 12, True, keep=False)
			self.Text(self.listArea, '%d / %d' % (done, total), 64, y + 19, MUTED, 11, keep=False)
			self.Img(self.listArea, 'mini_bg', 64, y + 35, False)
			if total:
				self.Bar(self.listArea, 'mini_green', 64, y + 35, done, total)
			self.dyn.append(Area(self.listArea, 18, y, 146, 44, lambda k=key: self.SelectList(k), self.ScrollList))
		if len(rows) > 6:
			self.Img(self.listArea, 'scroll_track', 166, 78, False)
			span = 304 * 6 // len(rows)
			self.Img(self.listArea, 'scroll_thumb', 166, 78 + (304 - span) * self.listTop // max(1, len(rows) - 6), False)
		if not rows and self.view == 'kol':
			self.Text(self.listArea, 'Brak kategorii', 93, 90, MUTED, 11, center=True, keep=False)

	def Tag(self, x, y, state, text):
		self.Img(self.body, 'tag_' + ('done', 'act', 'lock')[0 if state == 3 else (1 if state in (1, 2) else 2)], x, y, False)
		self.Text(self.body, text, x + 33, y + 1, (GREEN, AMBER, LOCKED)[0 if state == 3 else (1 if state in (1, 2) else 2)], 10, True, True, False)

	def Rewards(self, lines, y, limit):
		for text in lines[:limit]:
			self.Text(self.body, text, 524, y, GREEN, 11, center=True, keep=False)
			y += 14
		if len(lines) > limit:
			self.Text(self.body, '+ %d wi\xeacej' % (len(lines) - limit), 524, y, MUTED, 10, center=True, keep=False)
			y += 14
		return y

	def DrawBiolog(self):
		rows = self.MissionRows('biolog')
		self.Text(self.body, MISSION_NAMES['biolog'], 192, 79, GOLD, 13, True, keep=False)
		self.Text(self.body, 'Oddaj przedmioty do bada\xf1', 192, 96, MUTED, 11, keep=False)
		if not rows:
			self.Text(self.body, 'Oczekiwanie na dane misji...', 317, 200, MUTED, 12, center=True, keep=False)
			return
		cur = self.Current(rows, lambda r: r['state'] == 3)
		top = max(0, min(self.gridTop, len(rows) - 5))
		wheel = lambda s, n=len(rows): self.ScrollGrid(s, n, 5)
		for n, r in enumerate(rows[top:top + 5]):
			i = top + n
			y = 116 + n * 52
			art = ('card_w_done' if r['state'] == 3 else ('card_w_act' if r['state'] in (1, 2) else 'card_w'))
			self.Img(self.body, art, 190, y, False)
			if i == cur:
				self.Img(self.body, 'card_w_sel', 188, y - 2, False)
			self.Slot(self.body, 196, y + 7, ItemIcon(r['item']), r['state'] == 0)
			self.Text(self.body, ItemName(r['item']) if r['item'] else r['name'], 234, y + 4, LOCKED if r['state'] == 0 else LIGHT, 12, True, keep=False)
			self.Text(self.body, 'od %d poziomu' % r['level'], 234, y + 19, MUTED, 11, keep=False)
			self.Img(self.body, 'mini_bg', 234, y + 36, False)
			self.Bar(self.body, 'mini_green' if r['state'] == 3 else 'mini_gold', 234, y + 36, r['progress'], max(1, r['required']))
			self.Tag(376, y + 4, r['state'], 'gotowe' if r['state'] == 3 else ('%d / %d' % (r['progress'], r['required']) if r['state'] else 'zablokowana'))
			self.dyn.append(Area(self.body, 190, y, 254, 46, lambda k=i: self.Pick(k), wheel))
		r = rows[cur]
		self.Big(r['item'])
		self.Text(self.body, ItemName(r['item']), 524, 132, GOLD, 12, True, True, False)
		self.Text(self.body, 'Oddaj %d szt.' % r['required'], 524, 150, LIGHT, 11, center=True, keep=False)
		self.Gauge(r['progress'], r['required'], r['state'] == 3)
		self.Text(self.body, 'Poziom: %d+' % r['level'], 470, 206, MUTED, 11, keep=False)
		self.Img(self.body, 'chip', 466, 225, False)
		self.timer = self.Text(self.body, '', 524, 228, AMBER, 11, True, True, False)
		self.UpdateBioTimer()
		self.Text(self.body, 'NAGRODA', 524, 252, 0xffd9b25f, 10, center=True, keep=False)
		self.Rewards(r['rewards'], 266, 3)
		self.Button(self.body, 'btn_ghost', 466, 326, self.TeleportBiolog, 'Teleport do Biologa', False, 0xfff1d697)
		self.Text(self.body, 'Uko\xf1czone badania: %d / %d' % (len([x for x in rows if x['state'] == 3]), len(rows)), 300, 404, MUTED, 11, center=True, keep=False)

	def DrawStage(self):
		kind = self.mcat
		rows = self.MissionRows(kind)
		self.Img(self.body, 'stage', 182, 72, False)
		self.Text(self.body, MISSION_NAMES[kind], 192, 79, GOLD, 13, True, keep=False)
		if not rows:
			self.Text(self.body, 'Oczekiwanie na dane misji...', 317, 200, MUTED, 12, center=True, keep=False)
			return
		cur = self.Current(rows, lambda r: r['state'] == 3)
		r = rows[cur]
		self.Text(self.body, 'misja %d / %d' % (cur + 1, len(rows)), 444, 81, MUTED, 11, keep=False).SetHorizontalAlignRight()
		self.Button(self.body, 'arrow_l', 192, 186, lambda: self.Step(-1, len(rows)), keep=False)
		self.Button(self.body, 'arrow_r', 416, 186, lambda: self.Step(1, len(rows)), keep=False)
		self.Text(self.body, r['target_name'], 317, 306, GOLD, 14, True, True, False)
		place = r['location'] + ((' \xb7 od %d poz.' % r['level']) if r['level'] > 1 and kind == 'boss' else '')
		self.Text(self.body, place, 317, 325, MUTED, 11, center=True, keep=False)
		self.Img(self.body, 'bar_bg_l', 222, 346, False)
		self.Bar(self.body, 'bar_green_l' if r['state'] == 3 else 'bar_gold_l', 222, 346, r['progress'], max(1, r['required']))
		self.Text(self.body, '%d / %d \xb7 %s' % (r['progress'], r['required'], r['status'].lower()), 317, 358, LIGHT, 11, center=True, keep=False)
		self.ShowModel(r['target'])
		verb = {'hunting': 'Zabij', 'metin': 'Zniszcz', 'boss': 'Pokonaj'}[kind]
		self.Text(self.body, 'CEL', 524, 80, 0xffd9b25f, 10, center=True, keep=False)
		self.Text(self.body, '%s %d\xd7' % (verb, r['required']), 524, 95, LIGHT, 11, True, True, False)
		self.Text(self.body, r['target_name'], 524, 109, LIGHT, 11, center=True, keep=False)
		self.Text(self.body, 'BONUSY NA STA\xa3E', 524, 130, 0xffd9b25f, 10, center=True, keep=False)
		y = self.Rewards(r['bonuses'], 145, 5)
		if r.get('items') or r.get('yang'):
			self.Text(self.body, 'PRZEDMIOTY', 524, y + 4, 0xffd9b25f, 10, center=True, keep=False)
			goods = ([('icon/item/money.tga', self.Yang(r['yang']))] if r.get('yang') else []) + \
					[(ItemIcon(v), 'x%d' % c) for v, c in r.get('items', [])]
			for n, (icon, label) in enumerate(goods[:4]):
				x = 470 + (n % 2) * 58
				yy = y + 20 + (n // 2) * 36
				self.Slot(self.body, x, yy, icon)
				self.Text(self.body, label, x + 36, yy + 9, AMBER, 11, keep=False)
		if kind in ('hunting', 'metin') and r['state'] == 1:
			self.Button(self.body, 'btn_gold', 466, 356, self.StartSelected, 'Rozpocznij', False)
		else:
			self.Text(self.body, r['status'], 524, 362, GREEN if r['state'] == 3 else (AMBER if r['state'] == 2 else LOCKED), 12, True, True, False)
		final = [x for x in _missions.get(kind, []) if x['id'] == FINAL_ID]
		if final and final[0]['bonuses']:
			text = 'Za wszystkie: ' + ', '.join(final[0]['bonuses'][:3]) + (' ...' if len(final[0]['bonuses']) > 3 else '')
			self.Text(self.body, text, 300, 404, GREEN if final[0]['state'] == 3 else MUTED, 11, center=True, keep=False)

	def DrawCollector(self):
		cat = next((c for c in _cats if c['key'] == self.ccat), None)
		if cat is None:
			self.Text(self.body, 'Kolekcjoner nie ma jeszcze kolekcji.', 317, 190, MUTED, 12, center=True, keep=False)
			self.Text(self.body, 'Administrator dodaje je w panelu: Ku\x9fnia Mocy - Kolekcjoner.', 317, 208, MUTED, 11, center=True, keep=False)
			return
		items = cat['items']
		self.Text(self.body, cat['name'], 192, 79, GOLD, 13, True, keep=False)
		self.Text(self.body, 'od %d poziomu' % cat['level'], 444, 81, MUTED, 11, keep=False).SetHorizontalAlignRight()
		if cat['desc']:
			self.Text(self.body, cat['desc'][:58], 192, 96, MUTED, 11, keep=False)
		if not items:
			return
		cur = self.Current(items, lambda r: r['state'] == 3)
		rows = (len(items) + 1) // 2
		top = max(0, min(self.gridTop, rows - 5))
		wheel = lambda s, n=rows: self.ScrollGrid(s, n, 5)
		for n, it in enumerate(items[top * 2:top * 2 + 10]):
			i = top * 2 + n
			x = 190 + (n % 2) * 128
			y = 114 + (n // 2) * 46
			art = 'card_done' if it['state'] == 3 else ('card_act' if it['state'] == 1 else 'card')
			self.Img(self.body, art, x, y, False)
			if i == cur:
				self.Img(self.body, 'card_sel', x - 2, y - 2, False)
			self.Slot(self.body, x + 5, y + 6, ItemIcon(it['vnum']), it['state'] == 0)
			name = ItemName(it['vnum'])
			self.Text(self.body, name if len(name) <= 13 else name[:12] + '...', x + 42, y + 5, LOCKED if it['state'] == 0 else LIGHT, 11, True, keep=False)
			self.Tag(x + 42, y + 23, it['state'], 'gotowe' if it['state'] == 3 else ('%d / %d' % (it['got'], it['need']) if it['state'] else 'zablokowana'))
			self.dyn.append(Area(self.body, x, y, 123, 44, lambda k=i: self.Pick(k), wheel))
		if rows > 5:
			self.Img(self.body, 'scroll_track_g', 446, 114, False)
			span = 228 * 5 // rows
			self.Img(self.body, 'scroll_thumb', 446, 114 + (228 - span) * top // max(1, rows - 5), False)
		it = items[cur]
		self.Big(it['vnum'])
		self.Text(self.body, ItemName(it['vnum']), 524, 132, GOLD, 12, True, True, False)
		self.Gauge(it['got'], it['need'], it['state'] == 3, 150)
		self.Text(self.body, 'Szansa: %d%%' % it['chance'], 470, 186, LIGHT, 11, keep=False)
		self.Text(self.body, 'Co ile: %s' % Duration(it['cooldown']), 470, 200, LIGHT, 11, keep=False)
		if it['state'] == 1:
			self.Text(self.body, 'Masz: %d szt.' % it['have'], 470, 214, LIGHT, 11, keep=False)
		self.Img(self.body, 'chip', 466, 233, False)
		self.timer = self.Text(self.body, '', 524, 236, AMBER, 11, True, True, False)
		self.kcItem = it
		self.UpdateKcTimer()
		self.Text(self.body, 'NAGRODA', 524, 262, 0xffd9b25f, 10, center=True, keep=False)
		self.Rewards(it['bonuses'], 276, 4)
		if it['state'] == 1:
			self.Button(self.body, 'btn_gold', 466, 356, lambda k=cat['key'], v=it['vnum']: self.Give(k, v), 'Oddaj', False)
		else:
			self.Button(self.body, 'btn_off', 466, 356, lambda: None, 'Uko\xf1czona' if it['state'] == 3 else 'Zablokowana', False, 0xff8c8070)
		done = len([x for x in items if x['state'] == 3])
		if cat['fin']:
			text = 'Za ca\xb3\xb9 kategori\xea (%d/%d): %s' % (done, len(items), ', '.join(cat['fin'][:3]) + (' ...' if len(cat['fin']) > 3 else ''))
		else:
			text = 'Uko\xf1czone kolekcje: %d / %d' % (done, len(items))
		self.Text(self.body, text, 300, 404, GREEN if done == len(items) else MUTED, 11, center=True, keep=False)

	def Big(self, vnum):
		self.Img(self.body, 'big', 502, 80, False)
		icon = ItemIcon(vnum)
		if icon:
			self.Img(self.body, icon, 508, 86, False)

	def Gauge(self, cur, top, green, y=168):
		self.Img(self.body, 'bar_bg', 470, y, False)
		self.Bar(self.body, 'bar_green' if green else 'bar_gold', 470, y, cur, max(1, top))
		self.Text(self.body, '%d / %d' % (min(cur, top), top), 524, y + 12, LIGHT, 11, center=True, keep=False)

	def Yang(self, value):
		if value >= 1000000:
			return '%gkk' % (value / 1000000.0)
		if value >= 1000:
			return '%gk' % (value / 1000.0)
		return str(value)

	def Step(self, step, count):
		key = self.Key()
		self.sel[key] = max(0, min(count - 1, self.sel.get(key, 0) + step))
		self.follow = False
		self.Refresh()

	def ShowModel(self, race):
		if not self.model:
			return
		if race and self.IsShow():
			if race != self.renderedRace:
				self.modelReady = bool(player.Mt2009ModelSelect(race))
				self.renderedRace = race
				if self.modelReady and hasattr(player, 'Mt2009ModelRotation'):
					try:
						player.Mt2009ModelRotation(180.0)
					except Exception:
						pass
			if self.modelReady:
				player.Mt2009ModelShow(1)
				self.model.Show()
				self.model.SetTop()
				return
		player.Mt2009ModelShow(0)
		self.model.Hide()

	# --- akcje
	def TeleportBiolog(self):
		net.SendChatPacket('/mission_panel biolog')

	def StartSelected(self):
		rows = self.MissionRows(self.mcat)
		if not rows:
			return
		r = rows[min(self.sel.get(self.Key(), 0), len(rows) - 1)]
		if self.mcat in ('hunting', 'metin') and r['state'] == 1:
			net.SendChatPacket('/mission_panel %s %d' % ('start' if self.mcat == 'hunting' else 'metin', r['id']))

	def Give(self, key, vnum):
		net.SendChatPacket('/kolekcje give %s %d' % (key, vnum))

	# --- liczniki
	def UpdateBioTimer(self):
		if self.view != 'mis' or self.mcat != 'biolog' or not getattr(self, 'timer', None):
			return
		rows = self.MissionRows('biolog')
		if not rows:
			return
		r = rows[min(self.sel.get(self.Key(), 0), len(rows) - 1)]
		seconds = int(_bioReadyAt - app.GetTime() + 0.999)
		if r['state'] == 3:
			self.timer.SetText('Badanie uko\xf1czone')
		elif r['state'] == 0:
			self.timer.SetText('Najpierw poprzednie')
		elif r['progress'] >= r['required']:
			self.timer.SetText('Oddaj kamie\xf1 misji')
		elif seconds > 0:
			self.timer.SetText('Za ' + Clock(seconds))
		else:
			self.timer.SetText('Mo\xbfesz odda\xe6 teraz')

	def UpdateKcTimer(self):
		it = getattr(self, 'kcItem', None)
		if self.view != 'kol' or not it or not getattr(self, 'timer', None):
			return
		if it['state'] == 3:
			self.timer.SetText('Kolekcja uko\xf1czona')
		elif it['state'] == 0:
			self.timer.SetText('Najpierw poprzednia')
		else:
			left = int(it['readyAt'] - app.GetTime() + 0.999)
			self.timer.SetText('Za ' + Clock(left) if left > 0 else 'Mo\xbfesz odda\xe6 teraz')

	def Open(self):
		self.follow = True
		self.SetTop()
		self.Show()
		self.Refresh()
		self.nextRequest = app.GetTime() + 5.0
		net.SendChatPacket('/mission_panel show')
		net.SendChatPacket('/kolekcje show')

	def OnUpdate(self):
		if not self.IsShow():
			return
		self.UpdateBioTimer()
		self.UpdateKcTimer()
		if app.GetTime() >= self.nextRequest:
			self.nextRequest = app.GetTime() + 5.0
			net.SendChatPacket('/mission_panel show' if self.view == 'mis' else '/kolekcje show')

	def Close(self):
		self.Hide()
		if self.model:
			player.Mt2009ModelShow(0)
			self.model.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


def GetWindow():
	global _window
	if _window is None:
		_window = Panel()
	return _window


def ToggleWindow():
	w = GetWindow()
	if w.IsShow():
		w.Close()
	else:
		w.Open()


def AttachTaskbar(taskbar):
	"""Przycisk na dolnym pasku (na lewo od przycisku postaci) - otwiera to okno (jak Ctrl+N)."""
	global _taskButton
	try:
		x, y = taskbar.GetChild('CharacterButton').GetLocalPosition()
	except Exception:
		x, y = wndMgr.GetScreenWidth() - 137, 3
	btn = ui.Button()
	btn.SetParent(taskbar)
	btn.SetPosition(x - 34, y)
	btn.SetUpVisual(ART + 'taskbar_0.tga')
	btn.SetOverVisual(ART + 'taskbar_1.tga')
	btn.SetDownVisual(ART + 'taskbar_2.tga')
	try:
		btn.SetToolTipText('Misje i Kolekcjoner (Ctrl+N)')
	except Exception:
		pass
	btn.SetEvent(ToggleWindow)
	btn.Show()
	_taskButton = btn


def Destroy():
	global _window, _missions, _pending, _cats, _catsPending, _taskButton
	_taskButton = None
	if _window:
		_window.Close()
		_window.Clear()
	_window = None
	_missions = dict((k, []) for k in MISSION_KINDS)
	_pending = None
	_cats = []
	_catsPending = None


def DestroyWindow():
	Destroy()


def _Changed():
	if _window and _window.IsShow():
		_window.Refresh()


def OnCommand(word='', *args):
	"""Misje: "MP begin|row|extra|end|biotimer|progress|masterprogress" (format serwera mission_panel)."""
	global _pending, _missions, _bioReadyAt
	if word == 'biotimer' and len(args) == 1:
		try:
			_bioReadyAt = app.GetTime() + max(0, int(args[0]))
		except (ValueError, TypeError):
			return
	elif word == 'begin':
		_pending = dict((k, []) for k in MISSION_KINDS)
	elif word == 'row' and _pending is not None and len(args) == 11:
		try:
			kind = args[0]
			if kind not in _pending:
				return
			ident, level, target, itemv, progress, required, state = [int(v) for v in args[1:8]]
			name = Unhex(args[8])
			status = {0: 'Zablokowana', 1: 'Dost\xeapna', 2: 'W trakcie', 3: 'Uko\xf1czona'}.get(state, '')
			_pending[kind].append(dict(id=ident, level=level, target=target, item=itemv, progress=progress, required=required,
									   state=state, name=name, target_name=name, location=Unhex(args[9]), status=status,
									   bonuses=Bonuses(args[10]), rewards=Bonuses(args[10]), items=[], yang=0))
		except (ValueError, TypeError):
			return
	elif word == 'extra' and _pending is not None and len(args) == 4:
		try:
			kind = args[0]
			ident = int(args[1])
			row = next((r for r in _pending.get(kind, []) if r['id'] == ident), None)
			if row is not None:
				row['yang'] = int(args[2])
				if args[3] != '-':
					for token in args[3].split(','):
						vnum, count, _name = token.split(':', 2)
						row['items'].append((int(vnum), int(count)))
		except (ValueError, TypeError):
			return
	elif word == 'end' and _pending is not None:
		_missions = _pending
		_pending = None
		_Changed()
	elif word == 'progress' and len(args) == 3:
		try:
			ident, count, state = [int(v) for v in args]
		except (ValueError, TypeError):
			return
		for row in _missions['hunting']:
			if row['id'] == ident:
				row['progress'] = count
				row['state'] = state
				row['status'] = 'Uko\xf1czona' if state == 3 else 'W trakcie'
		_Changed()
		if state == 3:
			uiquestbonuspreview.Reset()
	elif word == 'masterprogress' and len(args) == 4:
		try:
			kind, ident, count, state = args[0], int(args[1]), int(args[2]), int(args[3])
		except (ValueError, TypeError):
			return
		for row in _missions.get(kind, []):
			if row['id'] == ident:
				row['progress'] = count
				row['state'] = state
				row['status'] = 'Uko\xf1czona' if state == 3 else 'W trakcie'
		_Changed()
		if state == 3:
			uiquestbonuspreview.Reset()
			net.SendChatPacket('/mission_panel show')


def OnKolekcje(word='', *args):
	"""Kolekcjoner: "KC begin", "KC cat <klucz> <ikona> <poziom> <nazwa hex> <opis hex> <bonusy>",
	"KC item <klucz> <vnum> <ile> <ma> <szansa> <przerwa> <czekaj> <stan> <posiada> <bonusy>", "KC end"."""
	global _cats, _catsPending
	if word == 'begin':
		_catsPending = []
	elif word == 'cat' and _catsPending is not None and len(args) == 6:
		try:
			_catsPending.append(dict(key=args[0], icon=int(args[1]), level=int(args[2]), name=Unhex(args[3]),
									 desc=Unhex(args[4]), fin=Bonuses(args[5]), items=[]))
		except (ValueError, TypeError):
			return
	elif word == 'item' and _catsPending is not None and len(args) == 10:
		try:
			cat = next((c for c in _catsPending if c['key'] == args[0]), None)
			if cat is None:
				return
			vnum, need, got, chance, cooldown, wait, state, have = [int(v) for v in args[1:9]]
			cat['items'].append(dict(vnum=vnum, need=need, got=got, chance=chance, cooldown=cooldown, state=state, have=have,
									 readyAt=app.GetTime() + max(0, wait), bonuses=Bonuses(args[9])))
		except (ValueError, TypeError):
			return
	elif word == 'end' and _catsPending is not None:
		_cats = _catsPending
		_catsPending = None
		if _window and _window.ccat not in [c['key'] for c in _cats]:
			_window.ccat = _cats[0]['key'] if _cats else None
		_Changed()
