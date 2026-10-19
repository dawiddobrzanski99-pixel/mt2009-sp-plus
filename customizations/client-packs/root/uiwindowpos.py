# Where the windows stood - per character (the operator, 28 September:
# "zapis pozycji okien osobno dla kazdej postaci").
#
# Track(window, key) wraps the window's own Show and Hide: the position is
# remembered when the window closes and put back when it opens, clamped to
# the screen, so a window left on a bigger monitor is never lost off it.
# One file per character: autohunt/okna/<nick>.cfg, lines "key=x,y". A nick
# with other than letters and digits is kept as its hex, which every file
# system takes. A setting that is no position goes in the same file as
# "key=value,0" (GetValue/SetValue: the inventory's side bar folded or not).
#
# Python 2.7 as the client has it.

import os
import weakref
import player
import wndMgr

import uiautohunt

CONFIG_DIR = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'okna')

_state = {'name': None, 'pos': {}}


def _FileFor(name):
	if not name.isalnum():
		name = name.encode('hex')
	return os.path.join(CONFIG_DIR, name + '.cfg')


def _Load():
	name = player.GetName()
	if not name:
		return False
	if _state['name'] == name:
		return True
	_state['name'] = name
	_state['pos'] = {}
	try:
		with open(_FileFor(name), 'r') as handle:
			for line in handle:
				if '=' not in line:
					continue
				key, value = line.strip().split('=', 1)
				try:
					x, y = value.split(',', 1)
					_state['pos'][key] = (int(x), int(y))
				except ValueError:
					continue
	except (IOError, OSError):
		pass
	return True


def _Save():
	if not _state['name']:
		return
	try:
		if not os.path.exists(CONFIG_DIR):
			os.makedirs(CONFIG_DIR)
		with open(_FileFor(_state['name']), 'w') as handle:
			for key, (x, y) in sorted(_state['pos'].items()):
				handle.write('%s=%d,%d\n' % (key, x, y))
	except (IOError, OSError):
		pass


def Remember(window, key):
	try:
		if not window.IsShow() or not _Load():
			return
		x, y = window.GetGlobalPosition()
		if _state['pos'].get(key) != (x, y):
			_state['pos'][key] = (x, y)
			_Save()
	except Exception:
		pass


def Restore(window, key):
	try:
		if not _Load() or key not in _state['pos']:
			return
		x, y = _state['pos'][key]
		x = max(0, min(x, wndMgr.GetScreenWidth() - window.GetWidth()))
		y = max(0, min(y, wndMgr.GetScreenHeight() - window.GetHeight()))
		window.SetPosition(x, y)
	except Exception:
		pass


def GetValue(key, default=0):
	"""A setting kept for the character under `key`; `default` when it has
	none, None while there is no character to ask for (before the game)."""
	try:
		if not _Load():
			return None
		if key not in _state['pos']:
			return default
		return _state['pos'][key][0]
	except Exception:
		return None


def SetValue(key, value):
	try:
		if not _Load():
			return False
		value = int(value)
		if _state['pos'].get(key) != (value, 0):
			_state['pos'][key] = (value, 0)
			_Save()
		return True
	except Exception:
		return False


def Track(window, key, after_restore=None):
	"""The window's position kept for the character under `key`;
	after_restore (optional, called with the window) moves what hangs on
	the window along. The wrappers hold the window weakly: ui.Window has a
	__del__, and a cycle through it would never be collected."""
	if window is None or getattr(window, '_mt2009PosKey', None):
		return
	window._mt2009PosKey = key
	ref = weakref.ref(window)

	def TrackedShow(*args, **kwargs):
		w = ref()
		if w is None:
			return None
		result = type(w).Show(w, *args, **kwargs)
		Restore(w, key)
		if after_restore:
			try:
				after_restore(w)
			except Exception:
				pass
		return result

	def TrackedHide(*args, **kwargs):
		w = ref()
		if w is None:
			return None
		Remember(w, key)
		return type(w).Hide(w, *args, **kwargs)

	window.Show = TrackedShow
	window.Hide = TrackedHide
