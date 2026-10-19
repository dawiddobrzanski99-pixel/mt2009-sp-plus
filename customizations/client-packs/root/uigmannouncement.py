# GM_ANNOUNCEMENT_PANEL_V1 - Python2 compatible; ASCII source.
import app
import ui
import wndMgr
import grp
import re
_window = None
class Announcement(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('not_pick')
        self.SetSize(720,240)
        self.parts=[]
        self.background=ui.ExpandedImageBox();self.background.AddFlag('not_pick');self.background.SetParent(self)
        self.background.LoadImage('gm_announcement.tga');self.background.SetScale(720.0/768.0,240.0/256.0);self.background.Show()
        self.title=self.Text('OGLOSZENIE ADMINISTRACJI',424,30,'Arial:14b',0xffe2b766)
        self.line1=self.Text('',424,65,'Arial:24b',0xfffff0d0)
        self.line2=self.Text('',424,103,'Arial:24b',0xfffff0d0)
        self.author=self.Text('Administracja',424,188,'Arial:14b',0xffe2b766)
        self.progress=ui.Bar();self.progress.AddFlag('not_pick');self.progress.SetParent(self);self.progress.SetPosition(78,212);self.progress.SetSize(564,3);self.progress.SetColor(0xffdfb963);self.progress.Show()
        self.until=0.0;self.started=0.0;self.Hide()
    def Text(self,text,x,y,font,color):
        line=ui.TextLine();line.AddFlag('not_pick');line.SetParent(self);line.SetPosition(x,y);line.SetHorizontalAlignCenter();line.SetFontName(font);line.SetOutline();line.SetPackedFontColor(color);line.SetText(text);line.Show();return line
    def SetMessage(self,message):
        message=re.sub(r'\|c[0-9a-fA-F]{8}|\|H[^|]*\|h|\|[rRhH]', '',message).strip()
        author='Administracja'
        if ': ' in message and len(message.split(': ',1)[0])<=24:
            author,message=message.split(': ',1)
        self.author.SetText('Administracja' if author in ('Administracja','GM') else author+' - Administracja')
        if not message:return
        self.line1.SetFontName('Arial:24b');self.line2.SetFontName('Arial:24b')
        lines=[];current=''
        for word in message.split():
            candidate=(current+' '+word).strip();self.line1.SetText(candidate)
            if self.line1.GetTextSize()[0]>510 and current:lines.append(current);current=''
            while word:
                self.line1.SetText(word)
                if self.line1.GetTextSize()[0]<=510:current=(current+' '+word).strip();break
                cut=len(word)
                while cut>1:
                    self.line1.SetText(word[:cut])
                    if self.line1.GetTextSize()[0]<=510:break
                    cut-=1
                lines.append(word[:cut]);word=word[cut:]
        if current:lines.append(current)
        self.pages=[lines[i:i+2] for i in xrange(0,len(lines),2)]
        self.page=-1;self.duration=max(12.0,len(self.pages)*6.0)
        self.started=app.GetTime();self.until=self.started+self.duration;self.OnUpdate();self.Show()
    def OnUpdate(self):
        now=app.GetTime()
        if now>=self.until:self.Hide();return
        self.SetPosition(max(0,(wndMgr.GetScreenWidth()-720)//2),42)
        page=min(len(self.pages)-1,int((now-self.started)//6))
        if page!=self.page:
            self.page=page;lines=self.pages[page];self.line1.SetText(lines[0]);self.line2.SetText(lines[1] if len(lines)>1 else '')
        self.progress.SetSize(max(0,int(564*(self.until-now)/self.duration)),3)
def Show(message):
    global _window
    if _window is None:_window=Announcement()
    _window.SetMessage(message)
def Destroy():
    global _window
    if _window:_window.Hide()
    _window=None
