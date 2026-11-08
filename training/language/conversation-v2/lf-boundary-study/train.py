"""Explicit stages, finite one-pass LF1 schedule and full-state resumption."""
from lf_runtime import *
import argparse,math,resource

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--until',type=int,required=True);ap.add_argument('--preflight',action='store_true');args=ap.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 plan=read(P/'PLAN.json')
 for name,h in plan['sha256'].items():assert sha(ROOT/name)==h,name
 c,bs=data();started=time.monotonic();src=torch.load(SCRATCH/'initial.pt',map_location='cpu',weights_only=False);assert sha(SCRATCH/'initial.pt')==plan['initial_checkpoint_sha256']
 assert digest(src['trajectory'])=='274761c1209cc47c9e7a62a8d6a2d5b93dddbd13514fdddf372b9f980f8e5b33'
 def fresh():
  m,o,r=restore_isolated(src['trajectory']);restore_extra_rng(src['extra_rng']);return m,o,r
 if args.preflight:
  assert not(P/'PREFLIGHT.json').exists()
  m,o,r=fresh();assert {int(v['step']) for v in o.state.values()}=={6361};trace=[]
  for i in range(2):step(m,o,r,c,bs[i],i,'preflight-original',trace)
  state=payload(m,o,r,2,trace);save(SCRATCH/'preflight.pt',state);h=sha(SCRATCH/'preflight.pt')
  step(m,o,r,c,bs[2],2,'preflight-original',trace);target=payload(m,o,r,3,trace)
  # New objects loaded from serialized state; no shared Adam storage.
  re=torch.load(SCRATCH/'preflight.pt',map_location='cpu',weights_only=False);assert integrity(re)==re['integrity'];assert sha(SCRATCH/'preflight.pt')==h
  m2,o2,r2=restore_isolated(re['trajectory']);restore_extra_rng(re['extra_rng']);tr=copy.deepcopy(re['trace']);step(m2,o2,r2,c,bs[2],2,'preflight-replay',tr);actual=payload(m2,o2,r2,3,tr)
  assert integrity(actual)==integrity(target),'Update-after-resume mismatch'
  assert digest(src['trajectory'])=='274761c1209cc47c9e7a62a8d6a2d5b93dddbd13514fdddf372b9f980f8e5b33'
  write(P/'PREFLIGHT.json',dict(passed=True,full_state_resume_exact=True,checkpoint_sha256=h,actual_optimizer_calls=4,retained_updates=0,discarded_original_calls=3,replay_calls=1,source_state_unchanged=True,seconds=time.monotonic()-started,free_scratch_bytes=shutil.disk_usage(SCRATCH).free,free_persistent_bytes=shutil.disk_usage('/workspace').free,torch=torch.__version__,cpu_threads=2));return
 assert read(P/'PREFLIGHT.json')['passed'];assert args.until in [4,289,579]
 path=SCRATCH/'LF1-latest.pt'
 if path.exists():
  obj=torch.load(path,map_location='cpu',weights_only=False);assert integrity(obj)==obj['integrity'] and obj['plan_sha256']==sha(P/'PLAN.json');m,o,r=restore_isolated(obj['trajectory']);restore_extra_rng(obj['extra_rng']);trace=obj['trace'];start=obj['active_cursor']
 else:m,o,r=fresh();trace=[];start=0
 assert start<args.until
 for i in range(start,args.until):
  z=step(m,o,r,c,bs[i],i,'retained',trace)
  if i+1 in [4,289,579] or (i+1)%64==0:
   obj=payload(m,o,r,i+1,trace);save(path,obj);assert integrity(torch.load(path,map_location='cpu',weights_only=False))==obj['integrity']
   if i+1 in [4,289,579]:save(SCRATCH/f'LF1-{i+1}.pt',obj)
   write(P/'LIVE.json',dict(cursor=i+1,targets=sum(t['targets'] for t in trace),elapsed_process_seconds=time.monotonic()-started,checkpoint_sha256=sha(path),last=z));print(json.dumps(read(P/'LIVE.json')),flush=True)
 write(P/f'TRAIN-{args.until}.json',dict(cursor=args.until,targets=sum(t['targets'] for t in trace),elapsed_process_seconds=time.monotonic()-started,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(path),integrity=obj['integrity']))
if __name__=='__main__':main()
