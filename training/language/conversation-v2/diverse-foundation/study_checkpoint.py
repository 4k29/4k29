"""Uniquely named loader to avoid collision with the parent conversation-v2/evaluate.py."""
from common import *
from state import starting

def model_history(name):
 if name=='initialA':return 3470
 if name=='initialB':return 0
 arm,step=name.split('-');return int(step)+(3470 if arm=='A'else 0)

def load(name):
 if name in ['initialA','initialB']:return starting(name[-1])[0],0
 arm,step=name.split('-');p=D/'run'/arm/f'checkpoint-{int(step):05d}.pt'
 if p.exists():obj=torch.load(p,weights_only=False)
 else:
  p=D/'run'/arm/f'archive-{int(step):05d}'/'checkpoint.json';obj=loader.load_checkpoint(p,read(p)['sha256'])
 assert obj['trajectory']['uniqueUpdates']==model_history(name)
 return restore_isolated(obj['trajectory'])[0],obj['active_cursor']
