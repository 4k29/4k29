"""Finite one-pass pretraining; independent full states, fixed target schedule and durable actual-call ledger."""
import argparse,fcntl,math,os,resource,shutil,signal,subprocess,time
from common import *
from state import starting,rate
STOP=False
def stopping(*_):
 global STOP;STOP=True

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=['A','B','C'],required=True);ap.add_argument('--until',type=int,required=True);ap.add_argument('--resume',action='store_true');ap.add_argument('--replay',action='store_true');a=ap.parse_args();assert a.arm=='A';torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(P/'CLEAN_PLAN.json');psha=sha(P/'CLEAN_PLAN.json');assert read(P/'PREFLIGHT.json')['pass_all'];out=P/'run'/a.arm;out.mkdir(exist_ok=True,parents=True)
 if not a.replay:lock=(P/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for f,h in plan['input_sha256'].items():assert sha(ROOT/f)==h,f
 batches=json.load(gzip.open(P/'schedule-clean.json.gz','rt'))['batches'];assert 4<=a.until<=len(batches);events=[]
 if(out/('receipt-clean-%04d.json'%a.until)).exists()and not a.replay:raise SystemExit('Completed finite stage; refuse duplicate')
 if a.replay:obj=torch.load(out/'after2.pt',map_location='cpu',weights_only=False);end=plan['resume_test_second']
 elif a.resume:
  obj=torch.load(out/'checkpoint.pt',map_location='cpu',weights_only=False);end=a.until;events=list(map(json.loads,(out/'updates-clean.jsonl').read_text().splitlines()));assert[(r['phase'],r['step'])for r in events if r['event']=='intent']==[(r['phase'],r['step'])for r in events if r['event']=='completed'],'Ambiguous actual call: halt, never guess'
 else:
  raise RuntimeError('Clean runner requires explicit full-state --resume');model,opt,rng,base=starting(a.arm);obj=dict(trajectory=trajectory(model,opt,rng,[],0,[],3470 if a.arm!='C'else 0),active_cursor=0,trace=[],elapsed_seconds=0,plan_sha256=psha,arm=a.arm);end=a.until
 assert obj['plan_sha256']==psha and obj['arm']==a.arm;start=obj['active_cursor'];assert start<end;st=obj['trajectory'];source_digest=digest(st);model,opt,rng=restore_isolated(st);trace=obj['trace'][:];t0=time.monotonic();prior=obj['elapsed_seconds'];base_steps=3470 if a.arm=='A'else 0;model_prior=0 if a.arm=='C'else 3470
 if start or a.arm=='A':assert{int(v['step'])for v in opt.state.values()}=={base_steps+start}
 else:assert not opt.state
 old_events=list(map(json.loads,(P/plan['old_ledger']).read_text().splitlines()));done={r['step']:r['trace']for r in old_events if r['event']=='completed'and r['phase']=='retained'and r['step']<=plan['known_uncontaminated_through']};done.update({r['step']:r['trace']for r in events if r['event']=='completed'and r['phase']=='retained'})
 if not a.replay:signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
 def payload(cur):return dict(trajectory=trajectory(model,opt,rng,[],cur,[],model_prior+cur),arm=a.arm,active_cursor=cur,trace=trace,elapsed_seconds=prior+time.monotonic()-t0,plan_sha256=psha,optimizer_base_steps=base_steps)
 for i in range(start,end):
  x,y=pack(batches[i]);lr=rate(i+1,plan)
  for g in opt.param_groups:g['lr']=lr
  opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());norm=float(clip_grad_accurate(model.parameters(),plan['clipping']));assert math.isfinite(norm)
  row=dict(step=i+1,loss=float(loss.detach()),gradient_norm_before_clip=norm,lr=lr,targets=int(y.ne(-100).sum()),EOS_targets=int(y.eq(2).sum()),BOS_targets=int(y.eq(1).sum()));phase='resume-validation'if a.replay else'recovery-replay'if i+1 in done else'retained'
  record(out/'updates-clean.jsonl',dict(event='intent',phase=phase,step=i+1,trace=row));opt.step();record(out/'updates-clean.jsonl',dict(event='completed',phase=phase,step=i+1,trace=row));opt.zero_grad(set_to_none=True)
  if phase=='recovery-replay':assert row==done[i+1]
  trace.append(row)
  if i+1 in [plan['resume_test_first'],plan['resume_test_second']]or(i+1)%128==0 or i+1==end or STOP:
   obj=payload(i+1)
   if a.replay:write(out/'replay.json',dict(trajectory_digest=digest(obj['trajectory']),trace=trace));os._exit(73)
   assert shutil.disk_usage(P).free>600*1024**2,'Preserve last full checkpoint, insufficient atomic reserve';save(out/('after2.pt'if i+1==plan['resume_test_first']else'checkpoint.pt'),obj)
   if i+1==plan['resume_test_second']:
    p=subprocess.run([sys.executable,str(P/'train_clean.py'),'--arm',a.arm,'--until',str(end),'--replay']);assert p.returncode==73;assert read(out/'replay.json')==dict(trajectory_digest=digest(obj['trajectory']),trace=trace);(out/'after2.pt').unlink();write(out/'CLEAN_RESUME_AUDIT.json',dict(model_Adam_RNG_cursor_trace_exact_after_actual_2_to4=True,replay_updates=2))
   if i+1 in {512,1024,1536,2048,2560,len(batches)}:
    target=out/('checkpoint-%04d.pt'%(i+1));assert not target.exists();os.link(out/'checkpoint.pt',target)
   if STOP:
    if i+1==plan['resume_test_first']:save(out/'checkpoint.pt',obj)
    write(out/'PAUSED.json',dict(cursor=i+1,full_state_saved=True));return
  if(i+1)%128==0:print(a.arm,i+1,end,row,flush=True)
 assert digest(st)==source_digest,'Adam alias';calls=[json.loads(l)for l in(out/'updates-clean.jsonl').read_text().splitlines()if json.loads(l)['event']=='completed'];old_calls=[r for r in old_events if r['event']=='completed'];receipt=dict(old_v2_actual_calls=len(old_calls),clean_actual_calls=len(calls),total_A_actual_calls=len(old_calls)+len(calls),excluded_v2_tail_updates=28,arm=a.arm,stage_until=end,actual_optimizer_calls=len(old_calls)+len(calls),retained_updates=end,resume_validation_calls=2+sum(r['phase']=='resume-validation'for r in calls),recovery_replay_calls=sum(r['phase']=='recovery-replay'for r in calls),retained_targets=sum(r['targets']for r in trace),elapsed_seconds=prior+time.monotonic()-t0,all_actual_training_elapsed_seconds=plan['old_v2_elapsed']+prior+time.monotonic()-t0-plan['base512_elapsed'],maximum_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(out/'checkpoint.pt'),plan_sha256=psha)
 write(out/('receipt-clean-%04d.json'%end),receipt)
 if end==len(batches):write(out/'receipt.json',receipt)
 print(receipt,flush=True)
if __name__=='__main__':main()
