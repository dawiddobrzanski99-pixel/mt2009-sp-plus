
# -*- coding: ascii -*-
import ui

TEXT=0xff3d2918
BORDER=0xff9f7439
PAPER=0xfff1dfbb

class ParchmentBox(ui.Window):
    def __init__(self,parent,x,y,w,h):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x,y)
        self._fill=ui.Bar()
        self._fill.SetParent(self)
        self._fill.AddFlag('not_pick')
        self._fill.SetColor(PAPER)
        self._fill.Show()
        self._edges=[]
        for i in xrange(4):
            edge=ui.Bar()
            edge.SetParent(self)
            edge.AddFlag('not_pick')
            edge.SetColor(BORDER)
            edge.Show()
            self._edges.append(edge)
        self.SetSize(w,h)
        self.Show()

    def SetSize(self,w,h):
        ui.Window.SetSize(self,w,h)
        if not hasattr(self,'_fill'):
            return
        self._fill.SetSize(w,h)
        positions=((0,0,w,1),(0,h-1,w,1),(0,0,1,h),(w-1,0,1,h))
        for edge,pos in zip(self._edges,positions):
            edge.SetPosition(pos[0],pos[1])
            edge.SetSize(pos[2],pos[3])

def ApplyTextTheme(window):
    seen=set()
    def visit(obj):
        if obj is None or id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj,ui.Button):
            return
        if isinstance(obj,ui.TextLine):
            obj.SetPackedFontColor(TEXT)
            obj.SetOutline(False)
        children=getattr(obj,'Children',None)
        if isinstance(children,(list,tuple)):
            for child in children:
                visit(child)
        elements=getattr(obj,'ElementDictionary',None)
        if isinstance(elements,dict):
            for child in elements.values():
                visit(child)
    visit(window)
