# Ukryj kostiumy - the buttons under the costume window (the operator, 28
# September: "ukryj/pokaz kostiumy ... jak sa ukryte, to normalnie widac
# oryginalna zbroje i bron, ale sa zalozone i daja bonusy").
#
# MT2009_PLUS_COSTUME_HIDE_V2 (the owner, 6 October: "nakladka na bron
# wlaczona, a fryzura i kostium wylaczone"): three buttons, each look hidden on
# its own - the costume (1), the hair (2), the weapon skin (4).
#
# The costumes stay worn and keep their bonuses; only what the body, the
# weapon and the hair look like changes, for every player around. The server does the
# looks (item.cpp, Mt2009PlusApplyCostumeParts, server-patches/playerqol):
# "/kostiumy_ukryj m <mask>", sent after every login and warp
# (CostumeHideSync, an updatable of game.py) and on every click; it answers
# "CostumeHiddenAck m <mask>". A hidden hair costume shows the character's own
# default hair; the sash stays as it is.
#
# The setting is the client's, for every character: autohunt/kostiumy.cfg
# ("mask=N"; the old "hidden=1" of V1 reads as everything hidden).
#
# MT2009_PLUS_COSTUME_VIEW_OTHERS_V1 (the owner, 7 October): a fourth button,
# "Ukryj cudze" - the OTHER characters (bots and players) without their looks,
# for this player only: their armour instead of the costume, their weapon
# instead of the weapon skin, their own hair, the sash without its skin. The
# client never knows the others' real parts, so the server sends them to this
# player alone ("/kostiumy_innych <0|1>", answered "CostumeOthersAck <0|1>";
# server-patches/playerqol, item.cpp Mt2009PlusPlainLookParts), at once for
# everyone in view. Sent after every login and warp like the mask; saved as
# "others=1" in the same kostiumy.cfg.
#
# Python 2.7 as the client has it; the texts are CP1250 escapes.

import chat
import net
import os
import player

import uiautohunt

CONFIG_PATH = os.path.join(uiautohunt.CONFIG_BASE_DIR, 'kostiumy.cfg')

BODY = 1
HAIR = 2
WEAPON = 4
ALL = BODY | HAIR | WEAPON
OTHERS = 8  # not in the mask the server gets: its own command (above)

# bit -> (hide text, show text, hidden message, shown message)
TEXTS = {
    BODY: ('Ukryj kostium', 'Poka\xbf kostium', 'Kostium ukryty', 'Kostium znowu widoczny.'),
    HAIR: ('Ukryj fryzur\xea', 'Poka\xbf fryzur\xea', 'Fryzura ukryta', 'Fryzura znowu widoczna.'),
    WEAPON: ('Ukryj bro\xf1', 'Poka\xbf bro\xf1', 'Sk\xf3rka broni ukryta', 'Sk\xf3rka broni znowu widoczna.'),
    OTHERS: ('Ukryj cudze', 'Poka\xbf cudze', 'Kostiumy innych postaci ukryte (widzisz ich zbroje, bronie, fryzury i zwyk\xb3e szarfy)',
             'Kostiumy innych postaci znowu widoczne.'),
}
TOOLTIP_OTHERS = 'Kostiumy innych postaci - ukryte tylko u Ciebie'

_state = {'loaded': False, 'mask': 0, 'announce': 0, 'buttons': []}


def Load():
    if _state['loaded']:
        return
    _state['loaded'] = True
    try:
        with open(CONFIG_PATH, 'r') as handle:
            for line in handle:
                if '=' not in line:
                    continue
                key, value = line.strip().split('=', 1)
                value = value.strip()
                if key == 'mask' and value.isdigit():
                    _state['mask'] = (_state['mask'] & OTHERS) | (int(value) & ALL)
                elif key == 'others' and value == '1':
                    _state['mask'] |= OTHERS
                elif key == 'hidden' and value == '1':
                    _state['mask'] = ALL
    except (IOError, OSError):
        pass


def Save():
    if not os.path.exists(uiautohunt.CONFIG_BASE_DIR):
        try:
            os.makedirs(uiautohunt.CONFIG_BASE_DIR)
        except (IOError, OSError):
            pass
    try:
        with open(CONFIG_PATH, 'w') as handle:
            handle.write('mask=%d\n' % (_state['mask'] & ALL))
            handle.write('others=%d\n' % (1 if _state['mask'] & OTHERS else 0))
    except (IOError, OSError):
        pass


def IsHidden(bit=ALL):
    Load()
    return (_state['mask'] & bit) != 0


def ButtonText(bit):
    if IsHidden(bit):
        return TEXTS[bit][1]
    return TEXTS[bit][0]


def Send():
    Load()
    net.SendChatPacket('/kostiumy_ukryj m %d' % (_state['mask'] & ALL))
    # "Ukryj cudze": only when on, or switched in this session (a server
    # that still remembers it on) - a server without the command never hears it
    if _state['mask'] & OTHERS or _state.get('othersUsed'):
        net.SendChatPacket('/kostiumy_innych %d' % (1 if _state['mask'] & OTHERS else 0))


def Toggle(bit):
    Load()
    _state['mask'] ^= bit
    _state['announce'] = bit
    Save()
    if bit == OTHERS:
        _state['othersUsed'] = True
        net.SendChatPacket('/kostiumy_innych %d' % (1 if _state['mask'] & OTHERS else 0))
    else:
        net.SendChatPacket('/kostiumy_ukryj m %d' % (_state['mask'] & ALL))
    RefreshButtons()


def AddButton(button, bit):
    _state['buttons'].append((button, bit))
    button.SetText(ButtonText(bit))


def RemoveButton(button):
    _state['buttons'] = [entry for entry in _state['buttons'] if entry[0] is not button]


def RefreshButtons():
    for button, bit in _state['buttons']:
        try:
            button.SetText(ButtonText(bit))
        except Exception:
            pass


def OnAck(*rest):
    bit = _state['announce']
    if not bit or bit == OTHERS:
        return  # OTHERS has its own answer (OnOthersAck)
    _state['announce'] = 0
    if rest and rest[0] == 'm' and len(rest) > 1 and rest[1].isdigit():
        mask = int(rest[1])
    elif rest and rest[0] == '1':
        mask = ALL  # a server without V2
    else:
        mask = 0
    if mask & bit:
        chat.AppendChat(chat.CHAT_TYPE_INFO, '%s - bonusy dzia\xb3aj\xb9 dalej.' % TEXTS[bit][2])
    else:
        chat.AppendChat(chat.CHAT_TYPE_INFO, TEXTS[bit][3])


def OnOthersAck(*rest):
    """CostumeOthersAck <0|1> - only after a click (not after the login's sync)."""
    if _state['announce'] != OTHERS:
        return
    _state['announce'] = 0
    if rest and rest[0] == '1':
        chat.AppendChat(chat.CHAT_TYPE_INFO, TEXTS[OTHERS][2] + '.')
    else:
        chat.AppendChat(chat.CHAT_TYPE_INFO, TEXTS[OTHERS][3])


class CostumeHideSync(object):
    """An updatable: the setting to the server once a game phase has a named
    character - after the login and after every warp, when the core may be
    another one."""

    def __init__(self):
        self.sent = False

    def CanUpdate(self):
        return not self.sent

    def OnUpdate(self):
        if player.GetMainCharacterName():
            self.sent = True
            Send()

    def Destroy(self):
        pass
