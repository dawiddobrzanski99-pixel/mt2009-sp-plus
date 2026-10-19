# MT2009_PLUS9_ORIGIN_V1: per-instance metadata, requested only for a real +9.
import binascii
import weakref
import item
import net

_pending = {}
_serial = 0

def Cancel(tooltip):
    global _pending
    for token, entry in list(_pending.items()):
        if entry[0]() is tooltip or entry[0]() is None:
            _pending.pop(token, None)

def Request(tooltip, mode, a, b, vnum):
    global _pending, _serial
    Cancel(tooltip)
    item.SelectItem(vnum)
    if not item.GetItemName().rstrip().endswith('+9'):
        return
    _serial = (_serial + 1) % 1000000000
    if len(_pending) >= 64:
        _pending.pop(min(_pending), None)
    _pending[_serial] = (weakref.ref(tooltip), int(vnum))
    net.SendChatPacket('/plus9info %d %d %d %d %d' % (_serial, mode, a, b, vnum))

def OnCommand(token, vnum, ordinal, namehex):
    global _pending
    try:
        token, vnum, ordinal = int(token), int(vnum), int(ordinal)
        entry = _pending.pop(token, None)
        if entry is None or vnum != entry[1]:
            return
        tooltip = entry[0]()
        if tooltip is None or not tooltip.IsShow() or ordinal <= 0 or namehex == '-':
            return
        name = binascii.unhexlify(namehex)
        if not isinstance(name, str):
            name = name.decode('cp1250')
        name = name.replace('|', '')
        tooltip.AppendSpace(5)
        tooltip.AppendTextLine('Ulepszyl: |cffff3333%s|r' % name)
        tooltip.AppendTextLine('%d. osoba na serwerze z tym +9' % ordinal)
    except (ValueError, TypeError, binascii.Error):
        return

# MT2009_PLUS9_LINK_V2: link the real server item ID, not its attributes.
_pendingLinks = {}

def _AddOrigin(link, originID):
    if '|h' not in link:
        return link
    return link.replace('|h', ':p9:%x|h' % int(originID), 1)

def PasteItemLink(slotIndex):
    global _serial
    import player
    import ime
    link = player.GetItemLink(slotIndex)
    vnum = player.GetItemIndex(slotIndex)
    item.SelectItem(vnum)
    if not item.GetItemName().rstrip().endswith('+9'):
        ime.PasteString(link)
        return
    _serial = (_serial + 1) % 1000000000
    if len(_pendingLinks) >= 32:
        _pendingLinks.pop(min(_pendingLinks), None)
    _pendingLinks[_serial] = (link, int(vnum))
    net.SendChatPacket('/plus9info %d 2 %d %d %d' % (_serial, player.INVENTORY, slotIndex, vnum))

def OnLinkCommand(token, vnum, originID):
    import ime
    try:
        entry = _pendingLinks.pop(int(token), None)
        if entry is None or entry[1] != int(vnum) or int(originID) <= 0:
            return
        ime.PasteString(_AddOrigin(entry[0], int(originID)))
    except (ValueError, TypeError):
        return

def SplitOrigin(tokens):
    if len(tokens) >= 2 and tokens[-2] == 'p9':
        try:
            originID = int(tokens[-1], 16)
            if originID > 0 and originID <= 4294967295:
                return tokens[:-2], originID
        except (ValueError, TypeError):
            pass
        return tokens[:-2], 0
    return tokens, 0

def LinkFromHyperlink(hyperlink):
    import chat
    tokens, originID = SplitOrigin(hyperlink.split(':'))
    link = chat.GetLinkFromHyperlink(':'.join(tokens))
    return _AddOrigin(link, originID) if originID else link
