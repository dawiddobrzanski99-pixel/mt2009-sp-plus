# MISSION_PANEL_DRAFT_V1: presentation only; no rewards or quest mutations.
import ui
import wndMgr
import player
import nonplayer
import gamefont
import app
import net
import binascii
import uiquestbonuspreview

_bioReadyAt=0.0
_window=None
_pending=None
_data={"biolog":[],"hunting":[],"metin":[],"boss":[]}
def MissionFont(size=12):
    return gamefont.GetCurrentFontLarge().split(':')[0]+':'+str(int(size*1.15+0.5))

def SetMissionFont(line,size):
    # Client SetTextPointer does not invalidate cached glyphs: force a text rebuild.
    text=line.GetText();line.SetText('');line.SetFontName(MissionFont(size));line.SetText(text)

class MissionButton(ui.Window):
    def __init__(self,parent,title,x,y,callback,width=172,height=38):
        ui.Window.__init__(self);self.SetParent(parent);self.SetPosition(x,y);self.SetSize(width,height)
        self.callback=callback;self.enabled=True;self.color=0xffe5c875
        self.label=ui.TextLine();self.label.SetParent(self);self.label.AddFlag('not_pick');self.label.SetPosition(width//2,max(1,(height-14)//2));self.label.SetHorizontalAlignCenter();SetMissionFont(self.label,12);self.label.SetOutline();self.label.SetText(title);self.label.SetPackedFontColor(self.color);self.label.Show();self.Show()
    def SetSize(self,width,height):
        ui.Window.SetSize(self,width,height)
        if 'label' in self.__dict__:self.label.SetPosition(width//2,max(1,(height-14)//2))
    def SetTextColor(self,color):self.color=color;self.label.SetPackedFontColor(color)
    def Enable(self):self.enabled=True;self.label.SetPackedFontColor(self.color)
    def Disable(self):self.enabled=False;self.label.SetPackedFontColor(0xff796a54)
    def OnMouseOverIn(self):
        if self.enabled:self.label.SetPackedFontColor(0xff4b3018)
    def OnMouseOverOut(self):self.label.SetPackedFontColor(self.color if self.enabled else 0xff796a54)
    def OnMouseLeftButtonDown(self):return self.enabled
    def OnMouseLeftButtonUp(self):
        if self.enabled:self.callback()
        return True

class MissionModel(ui.Window):
    def RegisterWindow(self,layer):self.hWnd=wndMgr.RegisterRenderTarget(self,layer)

class MissionPanel(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('movable');self.AddFlag('float')
        self.width=480;self.height=270
        self.SetSize(self.width,self.height);self.SetCenterPosition()
        self.parts=[];self.data=dict((k,[]) for k in ('biolog','hunting','metin','boss'));self.category='biolog';self.position=0;self.rewardOffset=0;self.nextRequest=0.0;self.renderedRace=0;self.followCurrent=True;self.modelReady=False
        # COMPACT_FIXED_LAYOUT_V9: real coordinates; never resize text bounding boxes.
        self.interior=ui.Bar();self.interior.SetParent(self);self.interior.AddFlag('not_pick');self.interior.SetPosition(14,41);self.interior.SetSize(452,194);self.interior.SetColor(0xffead8b6);self.interior.Show();self.parts.append(self.interior)
        self.skin=ui.ExpandedImageBox();self.skin.SetParent(self);self.skin.LoadImage('d:/ymir work/ui/game/custom_windows/mission_background.tga');self.textureWidth=self.skin.GetWidth();self.textureHeight=self.skin.GetHeight();self.skin.SetScale(float(self.width)/self.skin.GetWidth(),float(self.height)/self.skin.GetHeight());self.skin.Show();self.parts.append(self.skin)
        self.title=self.Text(self,'MISJE I BADANIA',240,23);SetMissionFont(self.title,14)
        self.closeButton=ui.Button();self.closeButton.SetParent(self);self.closeButton.SetPosition(450,20);self.closeButton.SetUpVisual('d:/ymir work/ui/public/close_button_01.sub');self.closeButton.SetOverVisual('d:/ymir work/ui/public/close_button_02.sub');self.closeButton.SetDownVisual('d:/ymir work/ui/public/close_button_03.sub');self.closeButton.SetEvent(self.Close);self.closeButton.Show();self.parts.append(self.closeButton)
        self.left=self.Board(25,59,91,141);self.selector=self.Board(25,201,91,22)
        self.target=self.Board(120,43,194,143);self.middle=self.Board(120,186,194,36);self.bonuses=self.Board(320,43,136,179)
        self.buttons={}
        for i,(key,name) in enumerate([('biolog','Badania Biologa'),('hunting','Polowanie'),('metin','Metinologia'),('boss','Bossologia')]):
            b=MissionButton(self.left,name,0,i*37,lambda k=key:self.SelectCategory(k),91,30);SetMissionFont(b.label,11);self.parts.append(b);self.buttons[key]=b
        self.selectorTitle=self.Text(self.selector,'Wybor etapu',45,0);SetMissionFont(self.selectorTitle,10)
        self.previous=MissionButton(self.selector,'<',2,9,self.Previous,16,13);self.next=MissionButton(self.selector,'>',73,9,self.Next,16,13);self.parts.extend([self.previous,self.next])
        self.number=self.Text(self.selector,'-',45,11);SetMissionFont(self.number,10)
        self.name=self.Text(self.middle,'',97,0);SetMissionFont(self.name,10)
        self.progress=self.Text(self.middle,'Oczekiwanie na dane',97,12);SetMissionFont(self.progress,10)
        self.level=self.Text(self.target,'',97,103);SetMissionFont(self.level,10)
        self.startButton=MissionButton(self,'Rozpocznij',280,232,self.StartSelected,150,20);self.parts.append(self.startButton);self.startButton.Hide()
        SetMissionFont(self.Text(self.bonuses,'',68,6),11)
        self.rewardLines=[self.Text(self.bonuses,'',65,32+i*23) for i in xrange(6)]
        for line in self.rewardLines:SetMissionFont(line,11)
        self.rewardScroll=ui.ScrollBar();self.rewardScroll.SetParent(self.bonuses);self.rewardScroll.SetPosition(122,29);self.rewardScroll.SetScrollBarSize(141);self.rewardScroll.SetScrollEvent(ui.__mem_func__(self.OnRewardScroll));self.rewardScroll.Hide();self.parts.append(self.rewardScroll)
        self.targetName=self.Text(self.target,'',97,6);SetMissionFont(self.targetName,12)
        self.location=self.Text(self.target,'',97,116);SetMissionFont(self.location,11)
        self.status=self.Text(self.target,'',97,129);SetMissionFont(self.status,11)
        self.model=None
        if hasattr(wndMgr,'RegisterRenderTarget') and hasattr(player,'Mt2009ModelSelect'):
            self.model=MissionModel();self.model.SetParent(self.target);self.model.AddFlag('not_pick');self.model.SetPosition(67,22);self.model.SetSize(60,76);wndMgr.SetRenderTarget(self.model.hWnd,getattr(app,'RENDER_TARGET_INDEX_ILLUSTRATED',1));self.parts.append(self.model)
        self.bioTimer=self.Text(self,'',126,236);SetMissionFont(self.bioTimer,11)
        self.bioTeleport=MissionButton(self,'Teleportuj do Biologa',270,232,self.TeleportBiolog,160,20);SetMissionFont(self.bioTeleport.label,11);self.parts.append(self.bioTeleport);self.bioTeleport.Hide()
        self.ApplyLargerLayout();self.Refresh();self.Hide()
    def ApplyLargerLayout(self):
        # MISSION_PANEL_SCALE115_V10: preserve text glyph bounds; only resize shape windows.
        scale=1.5
        for part in self.parts:
            x,y=part.GetLocalPosition();part.SetPosition(int(x*scale+0.5),int(y*scale+0.5))
            if part is not self.skin and not isinstance(part,ui.TextLine):part.SetSize(max(1,int(part.GetWidth()*scale+0.5)),max(1,int(part.GetHeight()*scale+0.5)))
        self.skin.SetScale(float(self.width)*scale/self.textureWidth,float(self.height)*scale/self.textureHeight)
        self.rewardScroll.SetScrollBarSize(int(141*scale+0.5))
        self.width=int(self.width*scale+0.5);self.height=int(self.height*scale+0.5);self.SetSize(self.width,self.height);self.SetCenterPosition()
    def Board(self,x,y,w,h):
        board=ui.Window();board.SetParent(self);board.SetPosition(x,y);board.SetSize(w,h);board.Show();self.parts.append(board);return board
    def Text(self,parent,value,x,y):
        line=ui.TextLine();line.SetParent(parent);line.SetPosition(x,y);line.SetHorizontalAlignCenter();SetMissionFont(line,12);line.SetPackedFontColor(0xff3d2918);line.SetOutline();line.SetText(value);line.Show();self.parts.append(line);return line
    def Button(self,parent,title,x,y,callback):
        b=MissionButton(parent,title,x,y,callback,200 if title=='Teleportuj do Biologa' else 172,38);self.parts.append(b);return b
    def SelectCategory(self,key):
        self.category=key;self.position=0;self.rewardOffset=0;self.followCurrent=True;self.Refresh()
    def SetMissions(self,data):
        self.data=dict((k,list(data.get(k,[]))) for k in ('biolog','hunting','metin','boss'))
        self.Refresh()
    def Previous(self):
        self.followCurrent=False;self.position=max(0,self.position-1);self.rewardOffset=0;self.Refresh()
    def Next(self):
        self.followCurrent=False;self.position=min(max(0,len(self.data[self.category])-1),self.position+1);self.rewardOffset=0;self.Refresh()
    def Refresh(self):
        self.title.SetText('MISJE I BADANIA')
        rows=self.data[self.category]
        # AUTO_CURRENT_STAGE_V14: follow server state; browsing temporarily opts out.
        if rows and self.followCurrent:
            self.position=next((i for i,r in enumerate(rows) if r.get('state')==2),next((i for i,r in enumerate(rows) if r.get('state')!=3),len(rows)-1))
        self.position=min(self.position,max(0,len(rows)-1))
        for key,b in self.buttons.items():b.SetTextColor(0xff352416 if key==self.category else 0xff352416)
        self.number.SetText('%d / %d'%(self.position+1,len(rows)) if rows else '-')
        self.previous.Disable() if self.position==0 else self.previous.Enable()
        self.next.Disable() if self.position>=len(rows)-1 else self.next.Enable()
        for line in self.rewardLines:line.SetText('')
        self.startButton.Hide();self.rewardScroll.Hide();self.bioTeleport.Hide();self.bioTimer.SetText('')
        if not rows:
            self.name.SetText({'biolog':'Badania Biologa','hunting':'Polowanie','metin':'Metinologia','boss':'Bossologia'}[self.category]);self.progress.SetText('Oczekiwanie na dane misji');self.level.SetText('');self.targetName.SetText('');self.location.SetText('');self.status.SetText('')
            if self.model:self.model.Hide()
            return
        m=rows[self.position];self.name.SetText(m.get('name','Misja'));self.progress.SetPackedFontColor(0xff23536a)
        count=max(0,int(m.get('progress',0)));required=max(0,int(m.get('required',0)));remaining=max(0,required-count)
        label='Do zniszczenia' if self.category=='metin' else ('Do oddania' if self.category=='biolog' else 'Do zabicia')
        # REMAINING_COUNT_ONLY_V11: progress is text only, without a bar or percentage.
        self.progress.SetText('%s: %d'%(label,remaining))
        level=m.get('level',0);self.level.SetText('' if self.category in ('hunting','metin') else 'Wymagany poziom: %d'%level)
        self.level.SetPackedFontColor(0xff286137 if player.GetStatus(player.LEVEL)>=level else 0xffac3528)
        self.DrawRewards(m.get('rewards',[]))
        if self.category in ('hunting','metin') and m.get('state')==1:self.startButton.Show()
        if self.category=='biolog':self.bioTeleport.Show();self.UpdateBioTimer()
        race=m.get('target',0);self.targetName.SetText(m.get('target_name',''))
        self.location.SetText('Lokacja: '+m.get('location',''))
        self.status.SetPackedFontColor(0xff91e1bc if m.get('state')==3 else 0xfff7d77b);self.status.SetText(m.get('status',''))
        if self.model:
            if race:
                if race!=self.renderedRace:self.modelReady=bool(player.Mt2009ModelSelect(race));self.renderedRace=race
                if self.IsShow() and self.modelReady:player.Mt2009ModelShow(1);self.model.Show()
                else:player.Mt2009ModelShow(0);self.model.Hide()
            else:self.model.Hide();player.Mt2009ModelShow(0)
    def RewardLines(self,rewards):
        lines=[]
        for reward in rewards:
            line=''
            for word in reward.split():
                if line and len(line)+len(word)+1>22:lines.append(line);line=word
                else:line=(line+' '+word).strip()
            if line:lines.append(line)
        return lines
    def DrawRewards(self,rewards):
        rewards=self.RewardLines(rewards)
        self.rewardOffset=min(self.rewardOffset,max(0,len(rewards)-6))
        for line in self.rewardLines:line.SetText('')
        for line,text in zip(self.rewardLines,rewards[self.rewardOffset:self.rewardOffset+6]):line.SetPackedFontColor(0xff87ee9e);line.SetText(text)
        if len(rewards)>6:self.rewardScroll.Show()
        else:self.rewardScroll.Hide()
    def OnRewardScroll(self):
        rows=self.data[self.category]
        if not rows:return
        rewards=self.RewardLines(rows[self.position].get('rewards',[]))
        self.rewardOffset=int(self.rewardScroll.GetPos()*max(0,len(rewards)-6))
        self.DrawRewards(rows[self.position].get('rewards',[]))
    def TeleportBiolog(self):
        net.SendChatPacket('/mission_panel biolog')
    def UpdateBioTimer(self):
        seconds=max(0,int(_bioReadyAt-app.GetTime()+0.999))
        rows=self.data.get('biolog',[]);current=rows[self.position] if rows else {}
        self.bioTimer.SetPackedFontColor(0xfff6b46c if seconds else 0xff87ee9e)
        if current.get('state')==3:self.bioTimer.SetText('Badanie ukonczone');return
        if current.get('progress',0)>=current.get('required',1):self.bioTimer.SetText('Oddaj kamien misji');return
        self.bioTimer.SetText('Gotowy do oddania' if seconds==0 else 'Czekaj: %02d:%02d:%02d'%(seconds//3600,(seconds//60)%60,seconds%60))
    def StartSelected(self):
        rows=self.data[self.category]
        if self.category in ('hunting','metin') and rows and rows[self.position].get('state')==1:net.SendChatPacket('/mission_panel %s %d'%('start' if self.category=='hunting' else 'metin',rows[self.position]['id']))
    def Open(self):
        self.followCurrent=True;self.rewardOffset=0;self.SetTop();self.Show();self.Refresh();self.nextRequest=app.GetTime()+5.0;net.SendChatPacket('/mission_panel show')
    def OnUpdate(self):
        if self.IsShow() and self.category=='biolog':self.UpdateBioTimer()
        if self.IsShow() and app.GetTime()>=self.nextRequest:
            self.nextRequest=app.GetTime()+5.0;net.SendChatPacket('/mission_panel show')
    def Close(self):
        self.Hide()
        if self.model:player.Mt2009ModelShow(0)
    def OnPressEscapeKey(self):self.Close();return True

def GetWindow():
    global _window
    if _window is None:_window=MissionPanel();_window.SetMissions(_data)
    return _window

def ToggleWindow():
    w=GetWindow()
    if w.IsShow():w.Close()
    else:w.Open()

def Destroy():
    global _window,_data,_pending
    if _window:_window.Close()
    _window=None;_data={"biolog":[],"hunting":[],"metin":[],"boss":[]};_pending=None

# ASCII wire format, CP1250 bytes decoded from hex without relying on codec availability.
def _Unhex(value):
    if value=='-':return ''
    return binascii.unhexlify(value)

def OnCommand(word='',*args):
    global _pending,_data,_bioReadyAt
    if word=='masterprogress' and len(args)==4:
        try:_MasterProgress(args[0],int(args[1]),int(args[2]),int(args[3]))
        except (ValueError,TypeError):return
    elif word=='biotimer' and len(args)==1:
        try:_bioReadyAt=app.GetTime()+max(0,int(args[0]))
        except (ValueError,TypeError):return
        if _window and _window.category=='biolog':_window.UpdateBioTimer()
    elif word=='begin':_pending={'biolog':[],'hunting':[],'metin':[],'boss':[]}
    elif word=='row' and _pending is not None and len(args)==11:
        try:
            kind=args[0]
            if kind not in _pending:return
            ident,level,target,itemv,progress,required,state=[int(v) for v in args[1:8]]
            name=_Unhex(args[8]);location=_Unhex(args[9]);rewards=[]
            if args[10]!='-':
                for token in args[10].split(','):
                    point,value,key=token.split(':',2);rewards.append(uiquestbonuspreview.FormatRow(int(point),key,int(value)))
            if kind=='biolog':title=name;targetName='Biolog'
            else:title={'hunting':'Polowanie','metin':'Metinologia','boss':'Bossologia'}[kind];targetName=name
            status={0:'Zablokowana',1:'Dostepna',2:'W trakcie',3:'Ukonczona'}.get(state,'')
            _pending[kind].append(dict(id=ident,level=level,target=target,item=itemv,progress=progress,required=required,state=state,name=title,target_name=targetName,location=location,status=status,rewards=rewards))
        except (ValueError,TypeError,binascii.Error):return
    elif word=='extra' and _pending is not None and len(args)==4:
        try:
            kind=args[0];ident=int(args[1]);gold=int(args[2])
            row=next((r for r in _pending.get(kind,[]) if r['id']==ident),None)
            if row is not None:
                row['rewards'].append(str(gold)+' Yang')
                for token in args[3].split(','):
                    vnum,count,name=token.split(':',2);row['rewards'].append(_Unhex(name)+' x'+str(int(count)))
        except (ValueError,TypeError,binascii.Error):return
    elif word=='end' and _pending is not None:
        _data=_pending;_pending=None
        if _window:_window.SetMissions(_data)
    elif word=='progress' and len(args)==3:
        try:ident,count,state=[int(v) for v in args]
        except (ValueError,TypeError):return
        for row in _data['hunting']:
            if row['id']==ident:row['progress']=count;row['state']=state;row['status']='Ukonczona' if state==3 else 'W trakcie'
        if _window:_window.SetMissions(_data)
        if state==3:uiquestbonuspreview.Reset()

def DestroyWindow():
    Destroy()


def _MasterProgress(kind,ident,count,state):
    for row in _data.get(kind,[]):
        if row['id']==ident:
            row['progress']=count;row['state']=state;row['status']='Ukonczona' if state==3 else 'W trakcie'
    if _window:_window.SetMissions(_data)
    if state==3:
        uiquestbonuspreview.Reset()
        net.SendChatPacket('/mission_panel show')


# CUSTOM_PARCHMENT_MISSION_V1
from custom_window_theme import ParchmentBox as _MissionPaperBox
_mission_previous_font=SetMissionFont
def SetMissionFont(line,size):
    _mission_previous_font(line,size)
    line.SetPackedFontColor(0xff3d2918)
    line.SetOutline(False)

def _MissionPaperBoard(self,x,y,w,h):
    board=_MissionPaperBox(self,x,y,w,h)
    self.parts.append(board)
    return board
MissionPanel.Board=_MissionPaperBoard

_mission_previous_button_init=MissionButton.__init__
def _MissionPaperButtonInit(self,*args,**kwargs):
    _mission_previous_button_init(self,*args,**kwargs)
    self.color=0xff4b3018
    self.label.SetPackedFontColor(self.color)
    self.label.SetOutline(False)
    for child in self.__dict__.values():
        if isinstance(child,ui.Bar):
            child.SetColor(0xffdfc18b)
MissionButton.__init__=_MissionPaperButtonInit



# CUSTOM_MISSION_READABLE_TEXT_V2
import re as _contrast_re
import app as _contrast_app

def _MissionReadableText(window):
    seen=set()
    def visit(obj):
        if obj is None or id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj,ui.TextLine):
            obj.SetPackedFontColor(0xff302215)
            obj.SetOutline(False)
            value=obj.GetText()
            if value and ('|c' in value or '|r' in value):
                obj.SetText(_contrast_re.sub(
                    r'\|c[0-9a-fA-F]{8}|\|r','',value
                ))
            return
        if isinstance(obj,ui.Button):
            return
        if isinstance(obj,dict):
            values=list(obj.values())
        elif isinstance(obj,(list,tuple)):
            values=list(obj)
        elif isinstance(obj,ui.Window):
            values=list(getattr(obj,'__dict__',{}).values())
        else:
            return
        for child in values:
            if isinstance(child,(ui.Window,list,tuple,dict)):
                visit(child)
    visit(window)

def _MissionReadableWrapper(previous):
    def wrapped(self,*args,**kwargs):
        result=previous(self,*args,**kwargs)
        _MissionReadableText(self)
        return result
    return wrapped

for _method in (
    '__init__','Refresh','DrawRewards','UpdateBioTimer',
    'SelectCategory','Open'
):
    _previous=getattr(MissionPanel,_method,None)
    if _previous is not None:
        setattr(MissionPanel,_method,_MissionReadableWrapper(_previous))

for _method in (
    'SetTextColor','Enable','Disable',
    'OnMouseOverIn','OnMouseOverOut'
):
    _previous=getattr(MissionButton,_method,None)
    if _previous is not None:
        setattr(MissionButton,_method,_MissionReadableWrapper(_previous))

_contrast_previous_update=MissionPanel.OnUpdate
def _MissionReadableUpdate(self,*args,**kwargs):
    result=_contrast_previous_update(self,*args,**kwargs)
    now=_contrast_app.GetTime()
    if now>=getattr(self,'_nextContrastUpdate',0):
        self._nextContrastUpdate=now+0.25
        _MissionReadableText(self)
    return result
MissionPanel.OnUpdate=_MissionReadableUpdate


# CUSTOM_MISSION_LAYOUT_V3

class _MissionPaperPanel(ui.Window):
    def __init__(self,parent,x,y,w,h):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(x,y)
        self._paper=ui.Bar()
        self._paper.SetParent(self)
        self._paper.AddFlag('not_pick')
        self._paper.SetColor(0x99f3e5c8)
        self._paper.Show()
        self._edges=[]
        for unused in xrange(4):
            edge=ui.Bar()
            edge.SetParent(self)
            edge.AddFlag('not_pick')
            edge.SetColor(0x887e5528)
            edge.Show()
            self._edges.append(edge)
        self.SetSize(w,h)
        self.Show()

    def SetSize(self,w,h):
        ui.Window.SetSize(self,w,h)
        if not hasattr(self,'_paper'):
            return
        self._paper.SetSize(w,h)
        for edge,rect in zip(self._edges,(
            (0,0,w,1),(0,h-1,w,1),
            (0,0,1,h),(w-1,0,1,h)
        )):
            edge.SetPosition(rect[0],rect[1])
            edge.SetSize(rect[2],rect[3])

def _MissionCleanBoard(self,x,y,w,h):
    board=_MissionPaperPanel(self,x,y,w,h)
    self.parts.append(board)
    return board

MissionPanel.Board=_MissionCleanBoard

def _MissionPlace(obj,x,y,w=None,h=None):
    if obj is None:
        return
    obj.SetPosition(x,y)
    if w is not None and h is not None:
        obj.SetSize(w,h)

def _MissionInk(obj,size=12):
    if obj is None:
        return
    obj.SetPackedFontColor(0xff352416)
    obj.SetOutline(False)
    SetMissionFont(obj,size)

def _MissionArrange(self):
    self.SetSize(720,405)
    self.width=720
    self.height=405

    _MissionPlace(self.title,360,28)
    _MissionInk(self.title,16)
    _MissionPlace(self.closeButton,681,24)

    _MissionPlace(self.left,29,75,147,224)
    _MissionPlace(self.selector,29,307,147,39)
    _MissionPlace(self.target,187,75,300,217)
    _MissionPlace(self.middle,187,301,300,45)
    _MissionPlace(self.bonuses,498,75,193,271)

    categories=[
        ('biolog','Badania Biologa'),
        ('hunting','Polowanie'),
        ('metin','Metinologia'),
        ('boss','Bossologia')
    ]
    for i,(key,label) in enumerate(categories):
        button=self.buttons[key]
        _MissionPlace(button,8,10+i*53,131,44)
        _MissionPlace(button.label,65,14)
        _MissionInk(button.label,12)
        button.label.SetText(label)
        button.color=0xff352416

        if not hasattr(button,'_layoutBack'):
            button._layoutBack=ui.Bar()
            button._layoutBack.SetParent(button)
            button._layoutBack.AddFlag('not_pick')
            button._layoutBack.Show()
            button._layoutLine=ui.Bar()
            button._layoutLine.SetParent(button)
            button._layoutLine.AddFlag('not_pick')
            button._layoutLine.Show()

        button._layoutBack.SetSize(131,44)
        button._layoutBack.SetColor(
            0xddcda969 if key==self.category else 0x55e6cf9e
        )
        button._layoutLine.SetPosition(0,43)
        button._layoutLine.SetSize(131,1)
        button._layoutLine.SetColor(0x887e5528)
        button.label.SetTop()

    _MissionPlace(self.selectorTitle,73,5)
    _MissionInk(self.selectorTitle,11)
    _MissionPlace(self.number,73,22)
    _MissionInk(self.number,12)
    _MissionPlace(self.previous,8,15,25,20)
    _MissionPlace(self.next,114,15,25,20)
    for button in (self.previous,self.next):
        _MissionPlace(button.label,12,3)
        _MissionInk(button.label,12)

    _MissionPlace(self.targetName,150,12)
    _MissionInk(self.targetName,16)
    _MissionPlace(self.level,150,158)
    _MissionPlace(self.location,150,176)
    _MissionPlace(self.status,150,194)
    for obj in (self.level,self.location,self.status):
        _MissionInk(obj,12)

    _MissionPlace(self.name,150,5)
    _MissionInk(self.name,12)
    _MissionPlace(self.progress,150,24)
    _MissionInk(self.progress,14)

    # Model ma wlasny obszar renderowania; zachowujemy jego obsluge.
    model=getattr(self,'model',None)
    if model is not None:
        parent=getattr(model,'GetParent',lambda:None)()
        if parent is self.target:
            model.SetPosition(65,35)
        elif parent is self:
            model.SetPosition(252,110)

    for i,line in enumerate(self.rewardLines):
        _MissionPlace(line,91,43+i*34)
        _MissionInk(line,12)
    _MissionPlace(self.rewardScroll,176,39)
    self.rewardScroll.SetScrollBarSize(218)

    # Naglowek nagrod nie ma osobnego pola w starszej wersji.
    if not hasattr(self,'_layoutRewardTitle'):
        self._layoutRewardTitle=ui.TextLine()
        self._layoutRewardTitle.SetParent(self.bonuses)
        self._layoutRewardTitle.AddFlag('not_pick')
        self._layoutRewardTitle.SetHorizontalAlignCenter()
        self._layoutRewardTitle.SetText('STALE BONUSY')
        self._layoutRewardTitle.Show()
        for obj in getattr(self.bonuses,'__dict__',{}).values():
            if isinstance(obj,ui.TextLine) and obj is not self._layoutRewardTitle:
                try:
                    if obj.GetText() in ('STALA NAGRODA','STA\u0141A NAGRODA'):
                        obj.Hide()
                except Exception:
                    pass
    _MissionPlace(self._layoutRewardTitle,96,13)
    _MissionInk(self._layoutRewardTitle,13)

    _MissionPlace(self.startButton,240,359,230,26)
    _MissionPlace(self.startButton.label,115,5)
    _MissionInk(self.startButton.label,13)

    teleport=getattr(self,'bioTeleport',None)
    if teleport is not None:
        _MissionPlace(teleport,475,359,216,26)
        label=getattr(teleport,'label',None)
        if label is not None:
            _MissionPlace(label,108,5)
            _MissionInk(label,12)

    timer=getattr(self,'bioTimer',None)
    if timer is not None:
        _MissionPlace(timer,205,366)
        _MissionInk(timer,12)

def _MissionLayoutWrap(previous):
    def wrapped(self,*args,**kwargs):
        result=previous(self,*args,**kwargs)
        _MissionArrange(self)
        return result
    return wrapped

for _layoutMethod in ('__init__','Refresh','Open'):
    _layoutPrevious=getattr(MissionPanel,_layoutMethod,None)
    if _layoutPrevious is not None:
        setattr(
            MissionPanel,_layoutMethod,
            _MissionLayoutWrap(_layoutPrevious)
        )



# CUSTOM_FINAL_MISSION_LAYOUT_V1
_FINAL_ART = "d:/ymir work/ui/game/custom_windows/final/"
_FinalModelOwner = None

def _FinalFont(line, size, color=0xff302215, serif=False):
    text=line.GetText()
    line.SetText("")
    line.SetFontName(("Times New Roman:" if serif else "Tahoma:")+str(size))
    line.SetText(text)
    line.SetPackedFontColor(color)
    line.SetOutline(False)

def _FinalText(parent,text,x,y,size=14,center=True):
    line=ui.TextLine()
    line.SetParent(parent)
    line.AddFlag("not_pick")
    line.SetPosition(x,y)
    if center:
        line.SetHorizontalAlignCenter()
    line.SetText(text)
    _FinalFont(line,size)
    line.Show()
    return line

def _FinalClaimModel(window):
    global _FinalModelOwner
    previous=_FinalModelOwner
    if previous is not None and previous is not window:
        model=getattr(previous,"_uiSharedModel",None)
        if model is not None:
            model.Hide()
    _FinalModelOwner=window

def _FinalButtonStyle(button):
    dark=getattr(button,"_finalDark",False)
    color=0xfff6e5bd if dark else 0xff302215
    if not button.enabled:
        color=0xff826f55
    button.color=color
    _FinalFont(button.label,getattr(button,"_finalFont",16),color)
    if hasattr(button,"_finalLabelX"):
        button.label.SetPosition(
            button._finalLabelX,
            max(1,(button.GetHeight()-18)//2)
        )

def _FinalButtonColor(self,color):
    self.color=color
    _FinalButtonStyle(self)

def _FinalButtonEnable(self):
    self.enabled=True
    _FinalButtonStyle(self)

def _FinalButtonDisable(self):
    self.enabled=False
    _FinalButtonStyle(self)

def _FinalButtonHover(self):
    _FinalButtonStyle(self)

MissionButton.SetTextColor=_FinalButtonColor
MissionButton.Enable=_FinalButtonEnable
MissionButton.Disable=_FinalButtonDisable
MissionButton.OnMouseOverIn=_FinalButtonHover
MissionButton.OnMouseOverOut=_FinalButtonHover

def _FinalButtonArt(button,name,w,h,dark=False,font=16,labelx=None):
    button.SetSize(w,h)
    art=getattr(button,"_finalArt",None)
    if art is None:
        art=ui.ExpandedImageBox()
        art.SetParent(button)
        art.AddFlag("not_pick")
        button._finalArt=art
    if getattr(button,"_finalArtName",None)!=name:
        art.LoadImage(_FINAL_ART+name+".tga")
        button._finalArtName=name
    art.SetPosition(0,0)
    art.SetScale(float(w)/art.GetWidth(),float(h)/art.GetHeight())
    art.Show()
    button._finalDark=dark
    button._finalFont=font
    button._finalLabelX=w//2 if labelx is None else labelx
    button.label.SetTop()
    _FinalButtonStyle(button)

def _FinalMissionStyle(self):
    self.title.SetText("PANEL MISJI")
    _FinalFont(self.title,26,serif=True)
    for line in self.rewardLines:
        _FinalFont(line,14)
    for line in (self.level,self.location,self.status,self.bioTimer):
        _FinalFont(line,14)
    _FinalFont(self.name,20,serif=True)
    _FinalFont(self.targetName,18,serif=True)
    _FinalFont(self.progress,16)
    _FinalFont(self.number,18)
    for i,key in enumerate(("biolog","hunting","metin","boss")):
        selected=key==self.category
        _FinalButtonArt(
            self.buttons[key],
            "mission_tab_%d_%s"%(i,"selected" if selected else "normal"),
            190,66,selected,16,120
        )
    for button in (self.startButton,self.bioTeleport):
        _FinalButtonStyle(button)

def _FinalMissionLayout(self):
    if not getattr(self,"_finalLayoutReady",False):
        self.interior.Hide()
        self.skin.LoadImage(_FINAL_ART+"mission_frame.tga")
        self.skin.SetScale(1.0,1.0)
        self._finalRewardTitle=_FinalText(
            self.bonuses,"NAGRODY",109,0,20
        )
        # Usuwamy dodatkowe naglowki i stare plaskie dekoracje.
        keep=set(id(v) for v in (
            self.title,self.selectorTitle,self.number,self.name,
            self.progress,self.level,self.targetName,self.location,
            self.status,self.bioTimer,self._finalRewardTitle
        ))
        keep.update(id(v) for v in self.rewardLines)
        seen=set()
        def clean(obj):
            if obj is None or id(obj) in seen:
                return
            seen.add(id(obj))
            if isinstance(obj,ui.TextLine):
                if id(obj) not in keep:
                    # Etykiety przyciskow sa zachowywane osobno.
                    if not any(obj is b.label for b in
                        list(self.buttons.values())+
                        [self.previous,self.next,self.startButton,self.bioTeleport]):
                        obj.Hide()
                return
            if isinstance(obj,ui.Bar):
                obj.Hide()
                return
            if isinstance(obj,dict):
                values=list(obj.values())
            elif isinstance(obj,(list,tuple)):
                values=list(obj)
            elif isinstance(obj,ui.Window):
                values=list(getattr(obj,"__dict__",{}).values())
            else:
                return
            for value in values:
                if isinstance(value,(ui.Window,list,tuple,dict)):
                    clean(value)
        clean(self)
        self._finalLayoutReady=True

    self.width=860
    self.height=660
    self.SetSize(860,660)
    self.title.SetPosition(430,49)
    self.closeButton.SetPosition(805,62)
    self.closeButton.SetTop()

    self.left.SetPosition(38,105)
    self.left.SetSize(190,290)
    for i,key in enumerate(("biolog","hunting","metin","boss")):
        self.buttons[key].SetPosition(0,i*72)

    self.selector.SetPosition(39,552)
    self.selector.SetSize(190,58)
    self.selectorTitle.Hide()
    self.previous.SetPosition(4,8)
    self.next.SetPosition(148,8)
    self.previous.label.SetText("")
    self.next.label.SetText("")
    _FinalButtonArt(self.previous,"previous",38,38)
    _FinalButtonArt(self.next,"next",38,38)
    self.number.SetPosition(95,15)

    self.middle.SetPosition(245,105)
    self.middle.SetSize(330,450)
    self.name.SetPosition(165,0)
    self.progress.SetPosition(165,420)

    self.target.SetPosition(245,155)
    self.target.SetSize(330,365)
    self.targetName.SetPosition(165,270)
    self.location.SetPosition(165,302)
    self.level.SetPosition(165,326)
    self.status.SetPosition(165,348)
    if self.model:
        self.model.SetPosition(25,15)
        self.model.SetSize(280,250)
        self._uiSharedModel=self.model

    self.bonuses.SetPosition(595,180)
    self.bonuses.SetSize(218,340)
    for i,line in enumerate(self.rewardLines):
        line.SetPosition(104,50+i*45)
    self.rewardScroll.SetPosition(205,45)
    self.rewardScroll.SetScrollBarSize(280)

    for button in (self.startButton,self.bioTeleport):
        button.SetPosition(350,558)
        _FinalButtonArt(button,"mission_action",320,48,True,18)
    self.bioTimer.SetPosition(510,618)
    self.SetCenterPosition()
    _FinalMissionStyle(self)

_FinalMissionInit=MissionPanel.__init__
def _FinalMissionInitWrapper(self,*args,**kwargs):
    _FinalMissionInit(self,*args,**kwargs)
    _FinalMissionLayout(self)
MissionPanel.__init__=_FinalMissionInitWrapper

_FinalMissionRefresh=MissionPanel.Refresh
def _FinalMissionRefreshWrapper(self,*args,**kwargs):
    model=self.model
    foreign=_FinalModelOwner is not None and _FinalModelOwner is not self
    if foreign:
        self.model=None
    try:
        result=_FinalMissionRefresh(self,*args,**kwargs)
    finally:
        self.model=model
    _FinalMissionStyle(self)
    return result
MissionPanel.Refresh=_FinalMissionRefreshWrapper

_FinalMissionDraw=MissionPanel.DrawRewards
def _FinalMissionDrawWrapper(self,*args,**kwargs):
    result=_FinalMissionDraw(self,*args,**kwargs)
    for line in self.rewardLines:
        _FinalFont(line,14)
    return result
MissionPanel.DrawRewards=_FinalMissionDrawWrapper

_FinalMissionOpen=MissionPanel.Open
def _FinalMissionOpenWrapper(self,*args,**kwargs):
    _FinalClaimModel(self)
    self.renderedRace=0
    result=_FinalMissionOpen(self,*args,**kwargs)
    _FinalMissionLayout(self)
    self.Refresh()
    return result
MissionPanel.Open=_FinalMissionOpenWrapper

_FinalMissionClose=MissionPanel.Close
def _FinalMissionCloseWrapper(self,*args,**kwargs):
    global _FinalModelOwner
    model=self.model
    if _FinalModelOwner is not self:
        self.model=None
    try:
        return _FinalMissionClose(self,*args,**kwargs)
    finally:
        self.model=model
        if _FinalModelOwner is self:
            _FinalModelOwner=None
MissionPanel.Close=_FinalMissionCloseWrapper

_FinalMissionUpdate=MissionPanel.OnUpdate
def _FinalMissionUpdateWrapper(self,*args,**kwargs):
    result=_FinalMissionUpdate(self,*args,**kwargs)
    if self.IsShow() and app.GetTime()>=getattr(self,"_finalTextUpdate",0):
        self._finalTextUpdate=app.GetTime()+0.25
        _FinalMissionStyle(self)
    return result
MissionPanel.OnUpdate=_FinalMissionUpdateWrapper
