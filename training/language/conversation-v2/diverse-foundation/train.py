"""Finite actual-update worker, full-state atomic checkpoints, separate-process resume proof."""
import argparse,fcntl,os,signal,subprocess,time,shutil,resource
from common import *
from state import starting,rate
STOP=False
def stop(*args):
 global STOP;STOP=True

def main():
 a=argparse.ArgumentParser();a.add_argument('--arm',choices=['A','B'],required=True);a.add_argument('--until',type=int,required=True);a.add_argument('--resume',action='store_true');a.add_argument('--replay',action='store_true');args=a.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(D/'PLAN.json');psha=sha(D/'PLAN.json');assert read(D/'PREFLIGHT.json')['pass_all'];assert read(D/'health/receipt.json')['all_three_exact'];out=D/'run'/args.arm;out.mkdir(exist_ok=True,parents=True)
 if not args.replay:lock=(D/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for f,h in plan['input_sha256'].items():assert sha(ROOT/f)==h,f
 assert not(out/f'receipt-{args.until:05d}.json').exists()or args.replay,'Refuse completed-stage replay'
 batches=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];assert 4<=args.until<=len(batches)
 if args.replay:obj=torch.load(out/'after2.pt',weights_only=False);end=4
 elif args.resume:obj=torch.load(out/'checkpoint.pt',weights_only=False);end=args.until
 else:
  assert not(out/'updates.jsonl').exists(),'Existing calls require explicit audited resume';model,opt,rng,base=starting(args.arm);obj=dict(trajectory=trajectory(model,opt,rng,[],0,[],3470 if args.arm=='A'else 0),arm=args.arm,active_cursor=0,trace=[],elapsed_seconds=0.,plan_sha256=psha);end=args.until
 assert obj['plan_sha256']==psha and obj['arm']==args.arm;start=obj['active_cursor'];assert start<end;st=obj['trajectory'];original=digest(st);model,opt,rng=restore_isolated(st);trace=obj['trace'][:];t0=time.monotonic();prior=obj['elapsed_seconds'];base_count=3470 if args.arm=='A'else 0
 if start:assert {int(v['step'])for v in opt.state.values()}=={start}
 else:assert not opt.state
 events=[json.loads(l)for l in(out/'updates.jsonl').read_text().splitlines()]if(out/'updates.jsonl').exists()else[]
 assert[(r['phase'],r['step'])for r in events if r['event']=='intent']==[(r['phase'],r['step'])for r in events if r['event']=='completed'],'Ambiguous actual call, refuse guess'
 prior_done={r['step']:r['trace']for r in events if r['event']=='completed'and r['phase']in ['retained','recovery-replay']}
 if not args.replay:signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def payload(cur):return dict(trajectory=trajectory(model,opt,rng,[],cur,[],base_count+cur),arm=args.arm,active_cursor=cur,trace=trace,elapsed_seconds=prior+time.monotonic()-t0,plan_sha256=psha)
 for i in range(start,end):
  assert shutil.disk_usage(D).free>600*1024**2,'Storage reserve';x,y=pack(batches[i]);lr=rate(i+1,plan)
  for g in opt.param_groups:g['lr']=lr
  model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert math.isfinite(norm)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());row=dict(step=i+1,loss=float(loss.detach()),gradient_norm_before_clip=norm,lr=lr,targets=int(y.ne(-100).sum()),EOS_targets=int(y.eq(2).sum()),role_targets=int(((y==3)|(y==4)).sum()));phase='resume-validation'if args.replay else'recovery-replay'if i+1 in prior_done else'retained';record(out/'updates.jsonl',dict(event='intent',phase=phase,step=i+1,trace=row));opt.step();record(out/'updates.jsonl',dict(event='completed',phase=phase,step=i+1,trace=row));opt.zero_grad(set_to_none=True)
  if phase=='recovery-replay':assert row==prior_done[i+1]
  trace.append(row)
  if i+1 in [2,4]or(i+1)%128==0 or i+1==end or STOP:
   obj=payload(i+1)
   if args.replay:write(out/'replay.json',dict(trajectory_digest=digest(obj['trajectory']),trace=trace));os._exit(73)
   save(out/('after2.pt'if i+1==2 else'checkpoint.pt'),obj)
   if i+1==4:
    p=subprocess.run([sys.executable,str(D/'train.py'),'--arm',args.arm,'--until','4','--replay']);assert p.returncode==73;assert read(out/'replay.json')==dict(trajectory_digest=digest(obj['trajectory']),trace=trace);write(out/'RESUME_AUDIT.json',dict(exact_model_adam_rng_sampler_cursor_trace_after_actual2_to4=True,additional_optimizer_calls=2,checkpoint_after2_sha256=sha(out/'after2.pt')));(out/'after2.pt').unlink()
   if i+1 in {plan['comparison_updates'],plan['midpoint_updates'],plan['full_pass_updates']}:
    p=out/f'checkpoint-{i+1:05d}.pt';assert not p.exists();os.link(out/'checkpoint.pt',p)
   write(D/'LIVE_STATUS.json',dict(arm=args.arm,retained_updates=i+1,retained_targets=sum(r['targets']for r in trace),planned_stage=end,full_pass_updates=len(batches),last_loss=row['loss'],elapsed_seconds=obj['elapsed_seconds'],free_bytes=shutil.disk_usage(D).free))
   if STOP:
    if i+1==2:save(out/'checkpoint.pt',obj)
    write(out/'PAUSED.json',dict(cursor=i+1,full_state_saved=True));return
  if(i+1)%256==0:print(args.arm,i+1,end,row,flush=True)
 assert digest(st)==original,'Source Adam alias';calls=[json.loads(l)for l in(out/'updates.jsonl').read_text().splitlines()if json.loads(l)['event']=='completed'];receipt=dict(arm=args.arm,retained_updates=end,actual_optimizer_calls=len(calls),resume_validation_calls=sum(r['phase']=='resume-validation'for r in calls),recovery_replay_calls=sum(r['phase']=='recovery-replay'for r in calls),retained_targets=sum(r['targets']for r in trace),elapsed_seconds=prior+time.monotonic()-t0,maximum_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(out/'checkpoint.pt'),plan_sha256=psha);write(out/f'receipt-{end:05d}.json',receipt);print(receipt,flush=True)
if __name__=='__main__':main()
