"""Same numerical routines; accept verified original human roles in the mixed data."""
from runtime import *
def pack(windows):
 x=torch.zeros((len(windows),256),dtype=torch.long);y=torch.full_like(x,-100)
 for i,w in enumerate(windows):
  s=w['tokens'];assert 2<=len(s)<=257 and not(set(s)&{0,5})
  if w.get('source_kind')!='original_human_A_B':assert not(set(s)&{3,4})
  n=len(s)-1;x[i,:n]=torch.tensor(s[:-1]);y[i,:n]=torch.tensor(s[1:])
 return x,y
