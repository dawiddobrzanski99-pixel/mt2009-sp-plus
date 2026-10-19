# COLLECTOR_REFINE_COUNTS_V1 - storage quantities sent for the current recipe.
_counts={}
_ready=False

def OnCommand(word='',*args):
 global _ready,_counts
 if word=='begin':_counts={};_ready=False
 elif word=='item' and len(args)>=2:
  try:vnum=int(args[0]);count=long(args[1])
  except (ValueError,TypeError):return
  if vnum>0 and count>=0:_counts[vnum]=count
 elif word=='end':_ready=True

def Count(vnum):return _counts.get(vnum,0) if _ready else 0

def Destroy():
 global _ready,_counts
 _counts={};_ready=False
