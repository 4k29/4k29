"""Matched finite schedules, inherited state, full ledger and exact process replay."""
import argparse,fcntl,copy,gzip,math,os,resource,shutil,signal,subprocess,sys,time
from common import *
from mixed_runtime import pack
STOP=False
def stop(*_):
 global STOP;STOP=True

def main():
 p=argparse.ArgumentParser();p.add_argument('--arm',choices=['control','boundary','clip5'],required=True);p.add_argument('--resume',action='store_true');p.add_argument('--replay',action='store_true');args=p.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=json.loads((N/'PLAN.json').read_text());arm=plan['arms'][args.arm];plan_sha=sha(N/'PLAN.json')
 for path,want in plan['input_sha256'].items():assert sha(N.parents[3]/path)==want,path
 assert json.loads((V/'epoch1/medium/archive/checkpoint.pt.chunks.json').read_text())['sha256']==plan['initial_checkpoint_sha256']
 out=N/'run'/args.arm;out.mkdir(parents=True,exist_ok=True);events=[];
 if args.arm=='clip5':
  gate=json.loads((N/'CLIP5_GO.json').read_text());assert gate['go']and not gate['learning_comparison_primary_success']and gate['boundary_run_receipt_sha256']==sha(N/'run/boundary/receipt.json')
 if not args.replay:
  lock=(N/'run/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 schedule=json.load(gzip.open(N/'schedule.json.gz','rt'))[arm['schedule']];assert len(schedule)==plan['updates_each']
 if(out/'receipt.json').exists():raise SystemExit('Complete arm: refuse additional updates')
 if args.replay:saved=torch.load(out/'after2.pt',map_location='cpu',weights_only=False);start=2;end=4
 elif args.resume:
  saved=torch.load(out/'checkpoint.pt',map_location='cpu',weights_only=False);start=saved['active_cursor'];end=len(schedule);events=list(map(json.loads,(out/'updates.jsonl').read_text().splitlines()));assert[(r['phase'],r['step'])for r in events if r['event']=='intent']==[(r['phase'],r['step'])for r in events if r['event']=='completed'],'Ambiguous interrupted optimizer call, do not invent count'
 else:
  assert not(out/'updates.jsonl').exists(),'Use explicit resume';assert shutil.disk_usage(N).free>700*1024**2;saved=dict(trajectory=initial()['trajectory'],active_cursor=0,trace=[],elapsed_seconds=0,plan_sha256=plan_sha);start=0;end=len(schedule)
 assert saved['plan_sha256']==plan_sha;st=saved['trajectory'];before=digest(st);model,opt,rng=restore_isolated(st);assert digest(st)==before;assert all(g['lr']==3e-5 for g in opt.param_groups);assert{int(v['step'])for v in opt.state.values()}=={3470+start};trace=saved['trace'][:];t0=time.monotonic();prior=saved.get('elapsed_seconds',0);done={e['step']:e['trace']for e in events if e['event']=='completed'and e['phase']=='retained'}
 if not args.replay:signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 def payload(cursor):return dict(contract='natural-paragraph-and-original-humanAB-v1',arm=args.arm,plan_sha256=plan_sha,active_cursor=cursor,elapsed_seconds=prior+time.monotonic()-t0,trace=trace,trajectory=trajectory(model,opt,rng,st['order'],st['cursor'],st['history'],3470+cursor))
 for i in range(start,end):
  x,y=pack(schedule[i]);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);assert torch.isfinite(loss);loss.backward();ps=list(model.parameters());assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in ps);squares=sum(float(p.grad.double().square().sum())for p in ps);gsum=sum(float(p.grad.double().sum())for p in ps);count=sum(p.numel()for p in ps);norm=float(clip_grad_accurate(ps,arm['clip']));assert math.isfinite(norm);row=dict(step=i+1,loss=float(loss.detach()),gradient_norm_before_clip=norm,gradient_variance=squares/count-(gsum/count)**2,clip=arm['clip'],target_tokens=int(y.ne(-100).sum()),EOS_targets=int(y.eq(2).sum()),body_targets=int(y.ge(6).sum()));phase='resume-validation'if args.replay else'recovery-replay'if i+1 in done else'retained'
  record(out/'updates.jsonl',dict(event='intent',phase=phase,step=i+1,trace=row));opt.step();record(out/'updates.jsonl',dict(event='completed',phase=phase,step=i+1,trace=row));opt.zero_grad(set_to_none=True)
  if phase=='recovery-replay':assert row==done[i+1],'Replayed unsaved update differs'
  trace.append(row)
  if i+1 in[2,4]or(i+1)%128==0 or i+1==end or STOP:
   obj=payload(i+1)
   if args.replay:write(out/'replay.json',dict(trajectory_digest=digest(obj['trajectory']),trace=trace));os._exit(73)
   assert shutil.disk_usage(N).free>200*1024**2
   save(out/('after2.pt'if i+1==2 else'checkpoint.pt'),obj)
   if i+1==4:
    proc=subprocess.run([sys.executable,str(N/'train.py'),'--arm',args.arm,'--replay']);assert proc.returncode==73;r=json.loads((out/'replay.json').read_text());assert r==dict(trajectory_digest=digest(obj['trajectory']),trace=trace);(out/'after2.pt').unlink();write(out/'RESUME_AUDIT.json',dict(real_updates_3_to4_exact_after_process_restart=True,optimizer_model_RNG_and_trace_exact=True))
   if STOP:
    if i+1==2:save(out/'checkpoint.pt',obj)
    print('Stopped after saved optimizer boundary',i+1,flush=True);return
  if(i+1)%128==0:print(args.arm,i+1,len(schedule),loss.item(),flush=True)
 events=list(map(json.loads,(out/'updates.jsonl').read_text().splitlines()));calls=[e for e in events if e['event']=='completed'];receipt=dict(actual_optimizer_updates=len(calls),retained_updates=len(schedule),replay_updates=sum(e['phase']!='retained'for e in calls),retained_targets=sum(r['target_tokens']for r in trace),elapsed_seconds=prior+time.monotonic()-t0,maximum_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,retained_trace=trace);assert receipt['retained_targets']==plan['targets_each'];write(out/'receipt.json',receipt);print(args.arm,{k:v for k,v in receipt.items()if k!='retained_trace'},flush=True)
if __name__=='__main__':main()
