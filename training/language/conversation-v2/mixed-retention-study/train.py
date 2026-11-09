"""Explicit stages, finite one-pass LF1 schedule and full-state resumption."""
from mix_runtime import *
import argparse,math,resource

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--until',type=int,required=True);ap.add_argument('--preflight',action='store_true');ap.add_argument('--replay-preflight',action='store_true');args=ap.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 plan=read(P/'PLAN.json')
 for name,h in plan['sha256'].items():assert sha(ROOT/name)==h,name
 c,bs=data();started=time.monotonic();src=torch.load(SCRATCH/'initial.pt',map_location='cpu',weights_only=False);assert sha(SCRATCH/'initial.pt')==plan['initial_checkpoint_sha256']
 assert digest(src['trajectory'])=='274761c1209cc47c9e7a62a8d6a2d5b93dddbd13514fdddf372b9f980f8e5b33'
 def fresh():
  m,o,r=restore_isolated(src['trajectory']);restore_extra_rng(src['extra_rng']);return m,o,r
 if args.replay_preflight:
  assert not(P/'PREFLIGHT.json').exists()
  state=torch.load(SCRATCH/'preflight.pt',map_location='cpu',weights_only=False);assert integrity(state)==state['integrity'] and state['active_cursor']==2
  m,o,r=restore_isolated(state['trajectory']);restore_extra_rng(state['extra_rng']);tr=copy.deepcopy(state['trace']);step(m,o,r,c,bs[2],2,'preflight-replay',tr);actual=payload(m,o,r,3,tr);write(P/'REPLAY_PROOF.json',dict(integrity=integrity(actual),trace=tr));return
 import fcntl
 lock=(P/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if args.preflight:
  assert not(P/'PREFLIGHT.json').exists() and not(P/'UPDATES.jsonl').exists()
  durable=pathlib.Path('/workspace/4k29')/P.relative_to(ROOT);durable.mkdir(parents=True,exist_ok=True);dest=durable/'UPDATES.jsonl';assert not dest.exists();dest.touch();(P/'UPDATES.jsonl').symlink_to(dest)
  m,o,r=fresh();assert {int(v['step']) for v in o.state.values()}=={6361};trace=[]
  initial_digest=digest(src['trajectory']);assert next(iter(o.state.values()))['exp_avg'].data_ptr()!=next(iter(src['trajectory']['optimizer']['state'].values()))['exp_avg'].data_ptr()
  for i in range(2):step(m,o,r,c,bs[i],i,'preflight-original',trace)
  state=payload(m,o,r,2,trace);save(SCRATCH/'preflight.pt',state);h=sha(SCRATCH/'preflight.pt')
  step(m,o,r,c,bs[2],2,'preflight-original',trace);target=payload(m,o,r,3,trace)
  import subprocess
  subprocess.run([sys.executable,str(P/'train.py'),'--until','4','--replay-preflight'],check=True);proof=read(P/'REPLAY_PROOF.json');assert proof==dict(integrity=integrity(target),trace=trace)
  assert digest(src['trajectory'])==initial_digest
  write(P/'PREFLIGHT.json',dict(passed=True,separate_process_resume_exact=True,full_state_resume_exact=True,checkpoint_sha256=h,actual_optimizer_calls=4,retained_updates=0,discarded_original_calls=3,replay_calls=1,source_state_unchanged=True,Adam_storage_isolated=True,seconds=time.monotonic()-started,free_scratch_bytes=shutil.disk_usage(SCRATCH).free,free_persistent_bytes=shutil.disk_usage('/workspace').free,torch=torch.__version__,cpu_threads=2,projected_serial_training_seconds=(time.monotonic()-started)*579/4));return
 assert read(P/'PREFLIGHT.json')['passed'];assert args.until in [4,289,579]
 path=SCRATCH/'MIX-latest.pt'
 if path.exists():
  obj=torch.load(path,map_location='cpu',weights_only=False);assert integrity(obj)==obj['integrity'] and obj['plan_sha256']==sha(P/'PLAN.json');m,o,r=restore_isolated(obj['trajectory']);restore_extra_rng(obj['extra_rng']);trace=obj['trace'];start=obj['active_cursor']
  es=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()];assert [(e['phase'],e['trace']['step']) for e in es if e['event']=='intent']==[(e['phase'],e['trace']['step']) for e in es if e['event']=='completed'];assert obj['trace']==[e['trace'] for e in es if e['event']=='completed' and e['phase']=='retained'],'Ledger/checkpoint mismatch: explicit recovery audit required'
 else:
  assert not any(json.loads(l)['phase']=='retained' for l in (P/'UPDATES.jsonl').read_text().splitlines());m,o,r=fresh();trace=[];start=0
 assert start<args.until
 for i in range(start,args.until):
  try:z=step(m,o,r,c,bs[i],i,'retained',trace)
  except AssertionError as exc:
   obj=payload(m,o,r,i,trace);save(path,obj);save(SCRATCH/f'MIX-{i}.pt',obj);write(P/'PAUSED.json',dict(cursor=i,reason=str(exc),checkpoint_sha256=sha(path)));raise
  if i+1 in [4,289,579] or (i+1)%64==0:
   obj=payload(m,o,r,i+1,trace);save(path,obj);assert integrity(torch.load(path,map_location='cpu',weights_only=False))==obj['integrity']
   if i+1 in [4,289,579]:save(SCRATCH/f'MIX-{i+1}.pt',obj)
   write(P/'LIVE.json',dict(cursor=i+1,targets=sum(t['targets'] for t in trace),elapsed_process_seconds=time.monotonic()-started,checkpoint_sha256=sha(path),last=z));print(json.dumps(read(P/'LIVE.json')),flush=True)
 write(P/f'TRAIN-{args.until}.json',dict(cursor=args.until,targets=sum(t['targets'] for t in trace),elapsed_process_seconds=time.monotonic()-started,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(path),integrity=obj['integrity']))
if __name__=='__main__':main()
