# RANK_SIDE_GOTHIC_V1: transparent gothic lettering beside native nicknames.
import ui
import app
import chr
import player
import textTail
import wndMgr

SIZES = {1: (62, 22), 2: (75, 22), 3: (70, 22), 4: (77, 22), 5: (115, 22), 6: (75, 22), 7: (94, 22), 8: (76, 22), 9: (93, 22), 10: (83, 22), 11: (114, 22), 12: (72, 22)}
MAX_DISTANCE = 3000
MAX_VISIBLE = 48
_records = {}
_badges = {}
_nextAttach = 0.0
_spaceWidth = None

def PlaceholderName(tier):
    global _spaceWidth
    if tier not in SIZES:
        return ''
    if _spaceWidth is None:
        measure = ui.TextLine()
        measure.SetText('. .')
        a = measure.GetTextSize()[0]
        measure.SetText('..')
        b = measure.GetTextSize()[0]
        _spaceWidth = max(1, a - b)
    width = SIZES[tier][0] + 4
    return ' ' * int((width + _spaceWidth - 1) // _spaceWidth)

def _Attach(vid, tier):
    import rankpoints
    import chrmgr
    rankpoints._Register()
    if hasattr(chrmgr, 'SetRankTitle'):
        chrmgr.SetRankTitle(vid, tier if tier in SIZES else 0)
    elif tier in SIZES:
        r, g, b = rankpoints.TIERS[tier][3]
        textTail.AttachTitle(vid, PlaceholderName(tier), r / 255.0, g / 255.0, b / 255.0)
    elif hasattr(textTail, 'DetachTitle'):
        textTail.DetachTitle(vid)

class Badge(ui.Window):
    def __init__(self, vid, tier):
        ui.Window.__init__(self, 'UI_BOTTOM')
        self.AddFlag('not_pick')
        self.vid = vid
        self.tier = tier
        self.width, self.height = SIZES[tier]
        self.SetSize(self.width, self.height)
        self.image = ui.ImageBox()
        self.image.SetParent(self)
        self.image.AddFlag('not_pick')
        self.image.LoadImage('ranktitles/rank%02d.tga' % tier)
        self.image.Show()
        self.measure = ui.TextLine()
        self.lastName = None
        self.nameWidth = 0

    def Follow(self):
        try:
            x, y, z = textTail.GetPosition(self.vid)
        except (AttributeError, RuntimeError, TypeError):
            self.Hide()
            return
        if x <= 0 or y <= 0 or x > wndMgr.GetScreenWidth() or y > wndMgr.GetScreenHeight():
            self.Hide()
            return
        name = chr.GetNameByVID(self.vid)
        if name != self.lastName or self.nameWidth <= 0:
            self.measure.SetText(name)
            self.nameWidth = self.measure.GetTextSize()[0]
            self.lastName = name
        # Native title is right-aligned at x - half the nickname width.
        # Spaces reserve its width so the native level stays to its left.
        self.SetPosition(int(x - self.nameWidth / 2.0 - self.width + 4), int(y - self.height + 4))
        self.Show()

    def Destroy(self):
        self.Hide()
        self.image.Hide()
        self.image = None
        self.measure = None

def Set(vid, tier):
    vid, tier = int(vid), int(tier)
    if tier not in SIZES:
        _records.pop(vid, None)
        old = _badges.pop(vid, None)
        if old:
            old.Destroy()
        if chr.HasInstance(vid):
            _Attach(vid, 0)
        return
    old = _badges.get(vid)
    if old and old.tier != tier:
        old.Destroy()
        del _badges[vid]
    _records[vid] = (tier, app.GetTime())
    if chr.HasInstance(vid):
        _Attach(vid, tier)

def Update(showNames=True, picked=0, target=0):
    global _nextAttach
    now = app.GetTime()
    own = player.GetMainCharacterIndex()
    candidates = []
    for vid, (tier, created) in list(_records.items()):
        if not chr.HasInstance(vid):
            if now - created > 2.0:
                _records.pop(vid, None)
            old = _badges.pop(vid, None)
            if old:
                old.Destroy()
            continue
        distance = 0 if vid == own else player.GetCharacterDistance(vid)
        if distance < 0 or distance > MAX_DISTANCE:
            continue
        if not showNames and vid not in (picked, target):
            continue
        candidates.append((0 if vid == own else 1, distance, vid, tier))
    candidates.sort()
    chosen = candidates[:MAX_VISIBLE]
    visible = set(row[2] for row in chosen)
    for vid in list(_badges):
        if vid not in _records:
            _badges.pop(vid).Destroy()
        elif vid not in visible:
            _badges[vid].Hide()
    for priority, distance, vid, tier in chosen:
        if now >= _nextAttach:
            _Attach(vid, tier)
        badge = _badges.get(vid)
        if badge is None:
            badge = Badge(vid, tier)
            _badges[vid] = badge
        badge.Follow()
    if now >= _nextAttach:
        _nextAttach = now + 0.5

def Destroy():
    global _nextAttach
    for badge in list(_badges.values()):
        badge.Destroy()
    _badges.clear()
    _records.clear()
    _nextAttach = 0.0
