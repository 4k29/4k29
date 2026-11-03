"""Own inherited numerical stack; paragraph-study state and safe storage topology."""
import pathlib,sys,os,json,hashlib,shutil,copy,math,time
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
sys.path.insert(0,str(P.parent/'modern-corpus'))
from next_runtime import torch,restore_isolated,trajectory,digest,save,record,causal_ce,clip_grad_accurate,pack,extra_rng,restore_extra_rng,read,write,sha,legacy
DURABLE=pathlib.Path('/workspace/4k29')/P.relative_to(ROOT)/'private/durable'
RESERVE=256*1024**2

def ensure_capacity(additional_bytes=136000000):
 DURABLE.mkdir(parents=True,exist_ok=True)
 assert shutil.disk_usage(DURABLE).free>=RESERVE+additional_bytes,'Persistent atomic-write reserve exhausted'
 # /tmp is tmpfs: memory and free blocks are both real constraints.
 assert shutil.disk_usage(P).free>=3*additional_bytes,'Scratch archive reserve exhausted'
 mem={}
 for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
  k,v=line.split(':',1);mem[k]=int(v.split()[0])*1024
 assert mem['MemAvailable']>1024**3,'Less than 1GiB available RAM'
 limit=pathlib.Path('/sys/fs/cgroup/memory.max');used=pathlib.Path('/sys/fs/cgroup/memory.current')
 if limit.exists()and used.exists()and limit.read_text().strip()!='max':
  assert int(limit.read_text())-int(used.read_text())>1024**3,'Cgroup RAM reserve exhausted'

def journal(arm,event):
 d=DURABLE/arm;d.mkdir(parents=True,exist_ok=True);record(d/'actual-updates.jsonl',event)

def mirror(arm,obj):
 ensure_capacity();dest=DURABLE/arm/'checkpoint.pt';save(dest,obj)
 assert digest(torch.load(dest,map_location='cpu',weights_only=False))==digest(obj)
 write(DURABLE/arm/'checkpoint-receipt.json',dict(file='checkpoint.pt',sha256=sha(dest),state_digest=digest(obj),cursor=obj['active_cursor'],plan_sha256=obj['plan_sha256']))
 return dest

def integrity(obj):
 return digest({k:obj[k]for k in ['trajectory','extra_rng','sampler','arm','active_cursor','trace','plan_sha256']})

def seal(obj):obj['state_integrity_sha256']=integrity(obj);return obj

def source():
 plan=read(P/'PLAN.json');raw=P/'private/source-B-6361.pt';assert sha(raw)==plan['initial_checkpoint_sha256'];obj=torch.load(raw,map_location='cpu',weights_only=False)
 assert digest(obj['trajectory'])==read(P/'STATE_PREFLIGHT.json')['inherited_full_state_digest'];return obj

def load_data():
 import gzip
 corpus=[json.loads(x)for x in gzip.open(P/'corpus.jsonl.gz','rt')];schedule=json.load(gzip.open(P/'schedule.json.gz','rt'));return corpus,schedule

def windows(corpus,refs):
 return [dict(tokens=corpus[r['record']]['tokens'][r['start']:r['start']+r['length']],source=corpus[r['record']]['source'])for r in refs]

def payload(model,opt,rng,base,arm,cursor,trace,plan_sha,schedule_sha):
 return seal(dict(trajectory=trajectory(model,opt,rng,[],cursor,[],base+cursor),extra_rng=extra_rng(),arm=arm,active_cursor=cursor,trace=trace,sampler=dict(schedule_sha256=schedule_sha,arm=arm,batch_cursor=cursor),plan_sha256=plan_sha))
