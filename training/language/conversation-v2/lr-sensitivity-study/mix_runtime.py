"""Isolated LF1 study, existing own numerical stack. No changes to prior study."""
import sys,pathlib,json,gzip,time,copy,hashlib,os,shutil
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2];SCRATCH=ROOT/'scratch'
sys.path.insert(0,str(V/'modern-corpus'))
from next_runtime import torch,restore_isolated,trajectory,digest,save,record,causal_ce,clip_grad_accurate,pack,extra_rng,restore_extra_rng,read,write

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def capacity():
 assert shutil.disk_usage(ROOT).free>64*1024**2,'Persistent ledger reserve insufficient'
 assert shutil.disk_usage(SCRATCH).free>500*1024**2,'Checkpoint atomic reserve insufficient'
 lim_path=pathlib.Path('/sys/fs/cgroup/memory.max')
 lim_text=lim_path.read_text().strip() if lim_path.exists() else 'max'
 if lim_text!='max':
  available=int(lim_text)-int(pathlib.Path('/sys/fs/cgroup/memory.current').read_text())
 else:
  available=int(next(s.split()[1] for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
 assert available>1024**3,'Insufficient available RAM'

def data():return json.load(gzip.open(P/'corpus.json.gz','rt')),json.load(gzip.open(P/'schedule.json.gz','rt'))
def rows(c,b):return [dict(tokens=c[r['record']]['tokens'][r['start']:r['start']+r['length']]) for r in b]
def integrity(o):return digest({k:v for k,v in o.items() if k!='integrity'})
def payload(m,o,r,cursor,trace):
 x=dict(trajectory=trajectory(m,o,r,[],cursor,[],13399+cursor),extra_rng=extra_rng(),sampler=dict(cursor=cursor,schedule_sha256=sha(P/'schedule.json.gz')),active_cursor=cursor,prefix_checkpoint_sha256='fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7',prefix_targets=590144,cumulative_targets=590144+sum(z['targets'] for z in trace),trace=trace,plan_sha256=sha(P/'PLAN.json'));x['integrity']=integrity(x);return x

def step(m,opt,r,c,b,i,phase,trace):
 capacity();x,y=pack(rows(c,b));m.train();opt.zero_grad(set_to_none=True)
 for g in opt.param_groups:
  assert tuple(g['betas'])==(.9,.999) and g['eps']==1e-8 and g['weight_decay']==.05
  g['lr']=3e-5
 assert {g['lr'] for g in opt.param_groups}=={3e-5}
 loss=causal_ce(m(x),y);loss.backward();norm=float(clip_grad_accurate(m.parameters(),1.))
 assert torch.isfinite(loss) and all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters()) and __import__('math').isfinite(norm)
 assert int(y.ne(-100).sum())==sum(len(r['tokens'])-1 for r in rows(c,b))
 z=dict(step=i+1,targets=int(y.ne(-100).sum()),loss=float(loss.detach()),gradient_norm=norm,clipped=norm>1,LF_targets=int(y.eq(16).sum()),EOS_targets=int(y.eq(2).sum()),batch_rows=len(b),batch_width=x.shape[1],lr=3e-5)
 z['body_nonLF_targets']=int(((y>5)&(y!=16)).sum());z['role_targets']=int(((y==3)|(y==4)).sum());z['source_targets']={}
 for ref in b:z['source_targets'][c[ref['record']]['source']]=z['source_targets'].get(c[ref['record']]['source'],0)+ref['length']-1
 before=[p.detach().clone() for p in m.parameters()]
 record(P/'UPDATES.jsonl',dict(event='intent',phase=phase,trace=z));opt.step();record(P/'UPDATES.jsonl',dict(event='completed',phase=phase,trace=z))
 assert all(torch.isfinite(p).all() for p in m.parameters()),'Nonfinite post-update model'
 assert all(torch.isfinite(v).all() for st in opt.state.values() for v in st.values() if torch.is_tensor(v)),'Nonfinite Adam state'
 d2=sum(float((p.detach().double()-old.double()).square().sum()) for p,old in zip(m.parameters(),before))
 adam_steps=sorted({int(st['step']) for st in opt.state.values()})
 record(P/'UPDATE_MAGNITUDES.jsonl',dict(phase=phase,step=i+1,Adam_steps=adam_steps,LR=3e-5,delta_L2=__import__('math').sqrt(d2),delta_RMS=__import__('math').sqrt(d2/sum(p.numel() for p in m.parameters())),parameters=sum(p.numel() for p in m.parameters())))
 opt.zero_grad(set_to_none=True);trace.append(z);return z
