# CUSTOM_EXCHANGE_YANG_SHORTCUTS_V1: integer arithmetic, never float money.
import re
import ui
import wndMgr
import app
import chat
import player
import uiPickMoney

def ParseYang(text):
    text = text.strip().lower()
    if not text: return 0
    match = re.match(r'^([0-9]+)(?:[.,]([0-9]{1,9}))?(k{1,3})?$', text)
    if not match: raise ValueError('format')
    whole, fraction, suffix = match.groups()
    fraction = fraction or ''
    divisor = 10 ** len(fraction)
    numerator = int(whole) * divisor + (int(fraction) if fraction else 0)
    numerator *= 1000 ** len(suffix or '')
    amount, remainder = divmod(numerator, divisor)
    if remainder: raise ValueError('fractional Yang')
    return amount

class ExchangeMoneyDialog(uiPickMoney.PickMoneyDialog):
    def LoadDialog(self):
        uiPickMoney.PickMoneyDialog.LoadDialog(self)
        self.pickValueEditLine.SetNumberMode(False)
        self.pickValueEditLine.SetMax(24)
        self.SetSize(300, 244 if app.ENABLE_CHEQUE_SYSTEM else 178)
        self.board.SetSize(self.GetWidth(), self.GetHeight())
        self.amountLabel = self.MakeText(20, 32, 'Kwota Yang:')
        self.amountSlot = ui.SlotBar()
        self.amountSlot.SetParent(self.board)
        self.amountSlot.SetPosition(20, 50)
        self.amountSlot.SetSize(260, 22)
        self.amountSlot.Show()
        self.pickValueEditLine.SetParent(self.amountSlot)
        self.pickValueEditLine.SetPosition(5, 3)
        self.pickValueEditLine.SetSize(250, 18)
        self.maxValueTextLine.SetParent(self.board)
        self.maxValueTextLine.SetPosition(20, 78)
        self.preview = self.MakeText(20, 96, '')
        self.helpLine = self.MakeText(20, 116, 'Skr\xf3ty: 1k | 1kk | 1kkk | 1,5kk')
        self.helpLine.SetPackedFontColor(0xffaaaaaa)
        self.GetChild('money_slot').Hide()
        if app.ENABLE_CHEQUE_SYSTEM:
            self.chequeLabel = self.MakeText(20, 136, 'Won:')
            self.chequeSlot = ui.SlotBar()
            self.chequeSlot.SetParent(self.board)
            self.chequeSlot.SetPosition(20, 154)
            self.chequeSlot.SetSize(260, 22)
            self.chequeSlot.Show()
            self.pickChequeValueEditLine.SetParent(self.chequeSlot)
            self.pickChequeValueEditLine.SetPosition(5, 3)
            self.pickChequeValueEditLine.SetSize(250, 18)
            self.maxChequeValueTextLine.SetParent(self.board)
            self.maxChequeValueTextLine.SetPosition(20, 180)
            self.GetChild('cheque_slot').Hide()
        self.acceptButton.SetPosition(84, self.GetHeight() - 34)
        self.cancelButton.SetPosition(156, self.GetHeight() - 34)

    def MakeText(self, x, y, text):
        line = ui.TextLine()
        line.SetParent(self.board)
        line.SetPosition(x, y)
        line.SetText(text)
        line.Show()
        return line

    def OnUpdate(self):
        text = self.pickValueEditLine.GetText()
        try:
            amount = ParseYang(text)
            self.preview.SetText('Do handlu: %s Yang' % amount if text else '')
            self.preview.SetPackedFontColor(0xff80d690 if amount <= self.maxValue else 0xffff7777)
        except ValueError:
            self.preview.SetText('Nieprawid\xb3owa kwota.')
            self.preview.SetPackedFontColor(0xffff7777)

    def SetMax(self, unused):
        self.pickValueEditLine.SetMax(24)

    def Open(self, maxValue, *args):
        maxValue = min(maxValue, getattr(player, 'EXCHANGE_GOLD_MAX', 99999999))
        uiPickMoney.PickMoneyDialog.Open(self, maxValue, *args)
        self.maxValueTextLine.SetText('Maksymalnie: %s Yang' % self.maxValue)
        if app.ENABLE_CHEQUE_SYSTEM:
            self.maxChequeValueTextLine.SetText('Maksymalnie: %s Won' % self.chequeMaxValue)
        x, y = self.GetGlobalPosition()
        self.SetPosition(max(0, min(x, wndMgr.GetScreenWidth() - self.GetWidth())),
                         max(0, min(y, wndMgr.GetScreenHeight() - self.GetHeight())))
        self.OnUpdate()

    def OnAccept(self):
        try:
            money = ParseYang(self.pickValueEditLine.GetText())
            cheque = 0
            if app.ENABLE_CHEQUE_SYSTEM:
                text = self.pickChequeValueEditLine.GetText()
                if text and not text.isdigit(): raise ValueError('cheque')
                cheque = int(text) if text else 0
                if cheque > self.chequeMaxValue: raise ValueError('cheque limit')
        except ValueError:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Wpisz kwot\xea Yang, np. 1k, 1,5kk lub 1kkk.')
            return
        if money > self.maxValue:
            chat.AppendChat(chat.CHAT_TYPE_INFO, 'Za du\xbfa kwota. Maksymalnie: %s Yang.' % self.maxValue)
            return
        self.pickValueEditLine.SetText(str(money))
        if self.eventAccept and (money > 0 or cheque > 0):
            if app.ENABLE_CHEQUE_SYSTEM: self.eventAccept(money, cheque)
            else: self.eventAccept(money)
        self.Close()
