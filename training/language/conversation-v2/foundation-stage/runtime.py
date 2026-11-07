"""Existing own model numerical stack, isolated state and durable writes."""
import copy,hashlib,importlib.util,json,os,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,trajectory,digest,causal_ce,clip_grad_accurate
spec=importlib.util.spec_from_file_location('committed_checkpoint',V/'foundation-data/research/zero_update_preflight.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def initial():
 p=V/'epoch1/medium/archive/checkpoint.pt.chunks.json';return loader.load_checkpoint(p,json.loads(p.read_text())['sha256'])
def snapshot(name='foundation'):
 p=H/'run'/(name+'.pt')
 if p.exists():return torch.load(p,map_location='cpu',weights_only=False)
 p=H/'run'/name/'archive/checkpoint.json';return loader.load_checkpoint(p,json.loads(p.read_text())['sha256'])
def save(p,obj):
 p.parent.mkdir(exist_ok=True,parents=True)
 with p.with_suffix('.pending').open('wb')as f:torch.save(obj,f);f.flush();os.fsync(f.fileno())
 os.replace(p.with_suffix('.pending'),p);fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
def record(p,obj):
 with p.open('a')as f:f.write(json.dumps(obj,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
def pack(windows):
 x=torch.zeros((len(windows),256),dtype=torch.long);y=torch.full_like(x,-100)
 for i,w in enumerate(windows):
  s=w['tokens'];assert 2<=len(s)<=257 and 0 not in s and not(set(s)&{3,4,5});n=len(s)-1;x[i,:n]=torch.tensor(s[:-1]);y[i,:n]=torch.tensor(s[1:])
 return x,y
def restore_isolated(st):return restore(copy.deepcopy(st),json.loads((V/'PLAN.json').read_text())['training'])
