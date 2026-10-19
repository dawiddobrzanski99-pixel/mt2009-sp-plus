# ASCII: permanent reward quest styling, no gameplay mutations.
import app
import net
GOLD = 0xffffd36a
NORMAL = 0xffc3c3c3
_indices = set()
_pending = None
_next = 0.0
_handle = 0

def Reset():
 global _indices, _pending, _next
 _indices = set()
 _pending = None
 _next = 0.0

def Request():
 global _next
 now = app.GetTime()
 if now >= _next:
  _next = now + 5.0
  net.SendChatPacket('/quest_bonus_styles')

def Begin():
 global _pending
 _pending = set()

def Index(value):
 if _pending is None: return
 try: value = int(value)
 except (ValueError, TypeError): return
 if value > 0: _pending.add(value)

def End():
 global _indices, _pending
 if _pending is not None: _indices = _pending
 _pending = None

def IsPermanent(index):
 return index in _indices

def Icon(original):
 global _handle
 if not _handle:
  try:
   import player
   path = 'playerbot_ui/quest_permanent.tga'
   if app.IsExistFile(path):
    player.RegisterEmotionIcon(920001, path)
    _handle = player.GetEmotionIconImage(920001)
  except Exception: return original
 return _handle or original
