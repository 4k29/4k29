"""Existing own numerical stack, dynamic padding, fixed immutable batch schedule.
No cross-document concatenation: each row is an independent original unit/window.
"""
import pathlib,sys,json,gzip,math,random
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation';RUN=N/'private/next-run';ROOT=N.parents[3];OLD=N.parent/'diverse-foundation'
sys.path.insert(0,str(OLD))
import common as legacy
import copy
from common import torch,restore_isolated,trajectory,digest,save,record,causal_ce,clip_grad_accurate

def read(path):return json.loads(pathlib.Path(path).read_text())
def sha(path):return legacy.sha(path)
def write(path,value):
 import os
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.pending')
 with tmp.open('w')as f:f.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path);fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
def load_data():
 corpus=[json.loads(line)for line in gzip.open(D/'corpus.jsonl.gz','rt')];schedule=json.load(gzip.open(D/'schedule.json.gz','rt'));return corpus,schedule

def batch_windows(corpus,refs):
 return [dict(tokens=corpus[r['record']]['tokens'][r['start']:r['start']+r['length']],source=corpus[r['record']]['source'])for r in refs]
def pack(rows):
 assert rows;T=max(len(r['tokens'])-1 for r in rows);assert 1<=T<=256
 x=torch.zeros((len(rows),T),dtype=torch.long);y=torch.full_like(x,-100)
 for i,row in enumerate(rows):
  tokens=row['tokens'];assert 2<=len(tokens)<=257 and 0 not in tokens and 5 not in tokens and 1 not in tokens[1:]
  n=len(tokens)-1;x[i,:n]=torch.tensor(tokens[:-1]);y[i,:n]=torch.tensor(tokens[1:])
 return x,y

def rate(step,plan):
 p=plan['lr'];n=plan['full_pass_updates'];w=p['warmup'];assert 1<=step<=n
 return p['peak']*step/w if step<=w else p['end']+(p['peak']-p['end'])*.5*(1+math.cos(math.pi*(step-w)/(n-w)))
def extra_rng():
 import numpy as np
 a=np.random.get_state();return dict(globalPython=random.getstate(),numpy=dict(kind=a[0],keys=a[1].tolist(),position=a[2],has_gauss=a[3],cached_gaussian=a[4]))
def restore_extra_rng(saved):
 import numpy as np
 def tuples(v):return tuple(tuples(x)for x in v)if isinstance(v,(list,tuple))else v
 random.setstate(tuples(saved['globalPython']));a=saved['numpy'];np.random.set_state((a['kind'],np.array(a['keys'],dtype='uint32'),a['position'],a['has_gauss'],a['cached_gaussian']))

def state_integrity(obj):
 return digest({k:obj[k]for k in ['trajectory','extra_rng','sampler','arm','active_cursor','trace','plan_sha256']})
def seal(obj):
 obj['state_integrity_sha256']=state_integrity(obj);return obj

def load_study_model(name):
 arm,step=name.split('-');step=int(step);assert arm in {'A','B'}
 if step==0:return starting(arm)[0],0
 path=RUN/arm/f'checkpoint-{step:05d}.pt'
 if path.exists():
  expected=read(RUN/arm/f'receipt-{step:05d}.json')['checkpoint_sha256'];assert sha(path)==expected;obj=torch.load(path,weights_only=False)
 else:
  manifest=D/'artifacts'/name/'checkpoint.json';obj=legacy.loader.load_checkpoint(manifest,read(manifest)['sha256'])
 assert obj['plan_sha256']==sha(D/'PLAN.json')and obj['state_integrity_sha256']==state_integrity(obj)
 return restore_isolated(obj['trajectory'])[0],obj['active_cursor']


def starting(arm):
 refs=read(D/'INITIAL_REFERENCES.json');reference=refs['sources'][arm];manifest=ROOT/reference['manifest'];obj=legacy.loader.load_checkpoint(manifest,reference['checkpoint_sha256']);base=obj['trajectory'];model=legacy.decoder(copy.deepcopy(base['config']));model.load_state_dict(base['model']);opt=torch.optim.AdamW(model.parameters(),lr=3e-5,betas=(.9,.999),eps=1e-8,weight_decay=.05)
 def tuples(v):return tuple(tuples(x)for x in v)if isinstance(v,list)else v
 rng=random.Random();rng.setstate(tuples(refs['private_python_rng_state']));torch.set_rng_state(torch.tensor(refs['torch_rng_bytes'],dtype=torch.uint8));model.train();return model,opt,rng,base
