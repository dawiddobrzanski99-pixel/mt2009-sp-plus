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
    def Disable(self):self.enabled=False;self.label.SetPackedFontColor(0xff777777)
    def OnMouseOverIn(self):
        if self.enabled:self.label.SetPackedFontColor(0xffffffff)
    def OnMouseOverOut(self):self.label.SetPackedFontColor(self.color if self.enabled else 0xff777777)
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
        self.interior=ui.Bar();self.interior.SetParent(self);self.interior.AddFlag('not_pick');self.interior.SetPosition(14,41);self.interior.SetSize(452,194);self.interior.SetColor(0xff1b1713);self.interior.Show();self.parts.append(self.interior)
        self.skin=ui.ExpandedImageBox();self.skin.SetParent(self);self.skin.LoadImage('d:/ymir work/ui/game/mission_panel/background.tga');self.textureWidth=self.skin.GetWidth();self.textureHeight=self.skin.GetHeight();self.skin.SetScale(float(self.width)/self.skin.GetWidth(),float(self.height)/self.skin.GetHeight());self.skin.Show();self.parts.append(self.skin)
        self.title=self.Text(self,'ALE ZAJEBISTY PANEL',240,23);SetMissionFont(self.title,14)
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
        SetMissionFont(self.Text(self.bonuses,'STALA NAGRODA',68,6),11)
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
        scale=1.15
        for part in self.parts:
            x,y=part.GetLocalPosition();part.SetPosition(int(x*scale+0.5),int(y*scale+0.5))
            if part is not self.skin and not isinstance(part,ui.TextLine):part.SetSize(max(1,int(part.GetWidth()*scale+0.5)),max(1,int(part.GetHeight()*scale+0.5)))
        self.skin.SetScale(float(self.width)*scale/self.textureWidth,float(self.height)*scale/self.textureHeight)
        self.rewardScroll.SetScrollBarSize(int(141*scale+0.5))
        self.width=int(self.width*scale+0.5);self.height=int(self.height*scale+0.5);self.SetSize(self.width,self.height);self.SetCenterPosition()
    def Board(self,x,y,w,h):
        board=ui.Window();board.SetParent(self);board.SetPosition(x,y);board.SetSize(w,h);board.Show();self.parts.append(board);return board
    def Text(self,parent,value,x,y):
        line=ui.TextLine();line.SetParent(parent);line.SetPosition(x,y);line.SetHorizontalAlignCenter();SetMissionFont(line,12);line.SetPackedFontColor(0xffecd494);line.SetOutline();line.SetText(value);line.Show();self.parts.append(line);return line
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
        self.title.SetText('ALE ZAJEBISTY PANEL')
        rows=self.data[self.category]
        # AUTO_CURRENT_STAGE_V14: follow server state; browsing temporarily opts out.
        if rows and self.followCurrent:
            self.position=next((i for i,r in enumerate(rows) if r.get('state')==2),next((i for i,r in enumerate(rows) if r.get('state')!=3),len(rows)-1))
        self.position=min(self.position,max(0,len(rows)-1))
        for key,b in self.buttons.items():b.SetTextColor(0xffe6c56d if key==self.category else 0xffdddddd)
        self.number.SetText('%d / %d'%(self.position+1,len(rows)) if rows else '-')
        self.previous.Disable() if self.position==0 else self.previous.Enable()
        self.next.Disable() if self.position>=len(rows)-1 else self.next.Enable()
        for line in self.rewardLines:line.SetText('')
        self.startButton.Hide();self.rewardScroll.Hide();self.bioTeleport.Hide();self.bioTimer.SetText('')
        if not rows:
            self.name.SetText({'biolog':'Badania Biologa','hunting':'Polowanie','metin':'Metinologia','boss':'Bossologia'}[self.category]);self.progress.SetText('Oczekiwanie na dane misji');self.level.SetText('');self.targetName.SetText('');self.location.SetText('');self.status.SetText('')
            if self.model:self.model.Hide()
            return
        m=rows[self.position];self.name.SetText(m.get('name','Misja'));self.progress.SetPackedFontColor(0xff70e8ed)
        count=max(0,int(m.get('progress',0)));required=max(0,int(m.get('required',0)));remaining=max(0,required-count)
        label='Do zniszczenia' if self.category=='metin' else ('Do oddania' if self.category=='biolog' else 'Do zabicia')
        # REMAINING_COUNT_ONLY_V11: progress is text only, without a bar or percentage.
        self.progress.SetText('%s: %d'%(label,remaining))
        level=m.get('level',0);self.level.SetText('' if self.category in ('hunting','metin') else 'Wymagany poziom: %d'%level)
        self.level.SetPackedFontColor(0xff80d080 if player.GetStatus(player.LEVEL)>=level else 0xffff7777)
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
