"""Finite paragraph-distribution experiment; durable ledger and full-state recovery."""
import argparse,fcntl,signal,subprocess,resource
from study_runtime import *
STOP=False
def stop(*_):
 global STOP;STOP=True

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=['A','B'],required=True);ap.add_argument('--until',type=int,required=True);ap.add_argument('--resume',action='store_true');ap.add_argument('--replay',action='store_true');args=ap.parse_args()
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(P/'PLAN.json');psha=sha(P/'PLAN.json');pre=read(P/'PREFLIGHT.json');assert pre['pass_all']and pre['plan_sha256']==psha
 for rel,expected in plan['input_sha256'].items():assert sha(ROOT/rel)==expected,rel
 out=P/'private/run'/args.arm;out.mkdir(parents=True,exist_ok=True);ledger=DURABLE/args.arm/'actual-updates.jsonl';end=4 if args.replay else args.until
 corpus,schedule=load_data();batches=schedule['arms'][args.arm];assert 4<=end<=len(batches)
 if not args.replay:
  lock=(P/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
  assert not(out/f'receipt-{end:05d}.json').exists(),'Completed stage must not be replayed'
 if args.resume or args.replay:
  saved=DURABLE/args.arm/'checkpoint.pt';receipt=read(saved.with_name('checkpoint-receipt.json'));assert sha(saved)==receipt['sha256'];obj=torch.load(saved,map_location='cpu',weights_only=False);assert integrity(obj)==obj['state_integrity_sha256']and obj['plan_sha256']==psha
  if args.replay:assert obj['active_cursor']==2
 else:
  assert not ledger.exists(),'Existing updates require explicit resume'
  inherited=source();s=inherited['trajectory'];model,opt,rng=restore_isolated(s);restore_extra_rng(inherited['extra_rng']);obj=payload(model,opt,rng,s['uniqueUpdates'],args.arm,0,[],psha,plan['schedule_sha256']);del model,opt,rng,inherited
 start=obj['active_cursor'];assert start<end;st=obj['trajectory'];original=digest(st);model,opt,rng=restore_isolated(st);restore_extra_rng(obj['extra_rng']);trace=copy.deepcopy(obj['trace']);base=plan['initial_model_unique_updates'];assert {int(v['step'])for v in opt.state.values()}=={plan['initial_adam_step']+start}
 events=[json.loads(l)for l in ledger.read_text().splitlines()]if ledger.exists()else[]
 assert [(e['phase'],e['step'])for e in events if e['event']=='intent']==[(e['phase'],e['step'])for e in events if e['event']=='completed'],'Uncertain optimizer call: require explicit audit, never guess'
 previous={e['step']:e['trace']for e in events if e['event']=='completed'and e['phase']in ['retained','recovery-replay']}
 begun=time.monotonic()
 for i in range(start,end):
  ensure_capacity();rows=windows(corpus,batches[i]);x,y=pack(rows);assert int(y.ne(-100).sum())==schedule['target_counts'][i]
  for g in opt.param_groups:g['lr']=plan['learning_rate']
  model.train();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),plan['clip']))
  assert math.isfinite(norm)and torch.isfinite(loss)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters())
  row=dict(step=i+1,targets=int(y.ne(-100).sum()),loss=float(loss.detach()),gradient_norm=norm,clipped=norm>plan['clip'],EOS_targets=int(y.eq(2).sum()),role_targets=int(((y==3)|(y==4)).sum()),batch_rows=len(rows),batch_width=x.shape[1],lr=plan['learning_rate'])
  phase='resume-validation'if args.replay else'recovery-replay'if i+1 in previous else'retained'
  if phase=='recovery-replay':assert row==previous[i+1],'Recovery trace mismatch before call'
  journal(args.arm,dict(event='intent',phase=phase,step=i+1,trace=row));opt.step();journal(args.arm,dict(event='completed',phase=phase,step=i+1,trace=row));opt.zero_grad(set_to_none=True);trace.append(row)
  if i+1 in {2,4,end}or(i+1)%128==0 or STOP:
   current=payload(model,opt,rng,base,args.arm,i+1,trace,psha,plan['schedule_sha256'])
   if args.replay:write(out/'replay-proof.json',dict(integrity=integrity(current),trace=trace));return
   if i+1==4:
    subprocess.run([sys.executable,str(P/'train.py'),'--arm',args.arm,'--until','4','--replay'],check=True);assert read(out/'replay-proof.json')==dict(integrity=integrity(current),trace=trace)
    write(out/'UPDATE_RESUME_AUDIT.json',dict(exact_all_state_after2_to4=True,separate_process=True,replay_loaded_durable_checkpoint=True,additional_optimizer_calls=2))
   save(out/'checkpoint.pt',current);mirror(args.arm,current);write(out/'latest-checkpoint.json',dict(cursor=i+1,sha256=sha(out/'checkpoint.pt'),integrity=integrity(current)))
   write(P/'LIVE_STATUS.json',dict(arm=args.arm,retained_updates=i+1,targets=sum(t['targets']for t in trace),planned_updates=len(batches),stage_end=end,elapsed_current_process_seconds=time.monotonic()-begun,last_trace=row,persistent_free_bytes=shutil.disk_usage(DURABLE).free))
   if STOP:write(out/'PAUSED.json',dict(cursor=i+1,full_state_saved=True));return
  if(i+1)%128==0:print(args.arm,i+1,end,row,flush=True)
 assert digest(st)==original,'Inherited Adam/model state was aliased'
 events=[json.loads(l)for l in ledger.read_text().splitlines()];completed=[e for e in events if e['event']=='completed'];receipt=dict(arm=args.arm,retained_updates=end,retained_targets=sum(t['targets']for t in trace),actual_optimizer_calls=len(completed),resume_validation_calls=sum(e['phase']=='resume-validation'for e in completed),recovery_replay_calls=sum(e['phase']=='recovery-replay'for e in completed),elapsed_current_process_seconds=time.monotonic()-begun,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_sha256=sha(out/'checkpoint.pt'),state_integrity_sha256=integrity(current),plan_sha256=psha)
 write(out/f'receipt-{end:05d}.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
