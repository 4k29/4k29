"""One finite pass of approved prose; inherited own3470/Adam/RNG. No role remap."""
import argparse,copy,gzip,json,math,os,pathlib,resource,shutil,signal,subprocess,sys,time
from mixed_runtime import H,V,torch,initial,save,record,sha,pack,restore_isolated,trajectory,digest,causal_ce,clip_grad_accurate
STOP=False
def request_stop(*_):
 global STOP;STOP=True
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--replay',action='store_true');args=parser.parse_args()
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=json.loads((H/'MIXED_PLAN.json').read_text());plan_sha=sha(H/'MIXED_PLAN.json')
 for name,want in plan['input_sha256'].items():assert sha(H.parents[3]/name)==want,name
 schedule=json.load(gzip.open(H/'mixed-schedule.json.gz','rt'));batches=schedule['batches'];N=len(batches);out=H/'mixed-run';out.mkdir(exist_ok=True)
 if (out/'receipt.json').exists():raise SystemExit('Completed experiment; no unrecorded additional updates')
 if args.replay:
  saved=torch.load(out/'after2.pt',map_location='cpu',weights_only=False);start=2;end=4;events=[]
 elif args.resume:
  saved=torch.load(out/'foundation.pt',map_location='cpu',weights_only=False);start=saved['active_cursor'];end=N;events=[json.loads(l)for l in(out/'updates.jsonl').read_text().splitlines()]
  # An incomplete intent cannot establish whether the Python step returned. Halt honestly.
  intents=[(e['phase'],e['step'])for e in events if e['event']=='intent'];done=[(e['phase'],e['step'])for e in events if e['event']=='completed'];assert intents==done,'Ambiguous interrupted call; preserve state and report lower/upper counts, do not guess'
 else:
  assert not(out/'updates.jsonl').exists(),'Use --resume, never repeat a completed ledger';assert shutil.disk_usage(out).free>480*1024**2
  base=initial();saved=dict(trajectory=base['trajectory'],trace=[],active_cursor=0,plan_sha256=plan_sha,elapsed_seconds=0);start=0;end=N;events=[]
 assert saved['plan_sha256']==plan_sha if 'plan_sha256'in saved else args.replay
 st=saved['trajectory'];source_digest=digest(st);model,opt,rng=restore_isolated(st)
 assert digest(st)==source_digest and all(int(s['step'])==3470+start for s in opt.state.values());assert all(g['lr']==3e-5 for g in opt.param_groups)
 trace=saved['trace'][:];started=time.monotonic();previous_elapsed=saved.get('elapsed_seconds',0);already={e['step']:e['trace']for e in events if e['event']=='completed'and e['phase']=='retained'}
 if not args.replay:signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)
 def payload(cursor):return dict(modelName='medium',contract='plain-prose-source-boundaries-v1',plan_sha256=plan_sha,trajectory=trajectory(model,opt,rng,st['order'],st['cursor'],st['history'],3470+cursor),trace=trace,active_cursor=cursor,elapsed_seconds=previous_elapsed+time.monotonic()-started)
 for i in range(start,end):
  tick=time.monotonic();x,y=pack(batches[i]);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();ps=list(model.parameters());assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in ps)
  squares=sum(float(p.grad.double().square().sum())for p in ps);sums=sum(float(p.grad.double().sum())for p in ps);count=sum(p.numel()for p in ps);norm=float(clip_grad_accurate(ps,1));assert math.isfinite(norm)
  row=dict(step=i+1,loss=float(loss.detach()),gradient_norm_before_clip=norm,gradient_variance=squares/count-(sums/count)**2,target_tokens=int(y.ne(-100).sum()),body_targets=int((y>=6).sum()),eos_targets=int(y.eq(2).sum()),padded_slots=len(batches[i])*256)
  phase='resume-validation'if args.replay else'recovery-replay'if i+1 in already else'retained'
  record(out/'updates.jsonl',dict(event='intent',phase=phase,step=i+1,trace=row));opt.step();record(out/'updates.jsonl',dict(event='completed',phase=phase,step=i+1,trace=row));opt.zero_grad(set_to_none=True)
  if phase=='recovery-replay':assert row==already[i+1],'Recovery trace changed; halt'
  trace.append(row)
  if not args.replay:record(out/'speed.jsonl',dict(step=i+1,target_tokens=row['target_tokens'],optimizer_step_seconds=time.monotonic()-tick))
  if i+1==2 and not args.replay:save(out/'after2.pt',payload(2))
  if i+1==4:
   state=payload(4);proof=dict(trajectory_digest=digest(state['trajectory']),trace=trace)
   if args.replay:(out/'replay.json').write_text(json.dumps(proof,indent=2)+'\n');os._exit(73)
   proc=subprocess.run([sys.executable,str(H/'train_mixed.py'),'--replay']);assert proc.returncode==73;assert json.loads((out/'replay.json').read_text())==proof
   (out/'after2.pt').unlink();(out/'RESUME_AUDIT.json').write_text(json.dumps(dict(real_updates_3_to4_exact_after_process_restart=True,discarded_replay_updates=2,all_model_adam_rng_sampler_and_trace_digest_equal=True),indent=2)+'\n');save(out/'foundation.pt',state)
   recent=[json.loads(l)for l in(out/'speed.jsonl').read_text().splitlines()];speed=sum(r['target_tokens']for r in recent)/sum(r['optimizer_step_seconds']for r in recent);assert speed>=plan['minimum_targets_per_second'];print('4-update preflight passed, actual targets/sec',speed,flush=True)
  if (i+1)%128==0 or i+1==N or STOP:
   assert shutil.disk_usage(out).free>180*1024**2,'Leave previous snapshot intact, insufficient atomic reserve';save(out/'foundation.pt',payload(i+1));print('step',i+1,'/',N,'targets',sum(r['target_tokens']for r in trace),'loss',row['loss'],flush=True)
   if STOP and i+1<N:
    (out/'PAUSED.json').write_text(json.dumps(dict(cursor=i+1,reason='signal boundary, full snapshot durable',resume='python train.py --resume'),indent=2)+'\n');return
 assert digest(st)==source_digest,'Restored optimizer aliased inherited state'
 calls=[json.loads(l)for l in(out/'updates.jsonl').read_text().splitlines()if json.loads(l)['event']=='completed'];counts={p:sum(e['phase']==p for e in calls)for p in ['retained','resume-validation','recovery-replay']}
 receipt=dict(actual_optimizer_updates=len(calls),retained_updates=N,replay_updates=len(calls)-N,counts=counts,actual_targets=sum(r['target_tokens']for r in trace),independent_body_tokens=plan['independent_body_tokens'],one_pass=True,elapsed_seconds=previous_elapsed+time.monotonic()-started,maximum_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt,flush=True)
if __name__=='__main__':main()
