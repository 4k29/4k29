"""Fixed fourteen-update execution validation. Explicitly counts discarded replay."""
import copy
import argparse,array,hashlib,importlib.util,json,math,os,pathlib,shutil,subprocess,sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,trajectory,digest,exact,pack,causal_ce,clip_grad_accurate

def write(p,x):
 with p.open('w')as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def load():
 s=importlib.util.spec_from_file_location('own_loader',V/'foundation-data/research/zero_update_preflight.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);plan=json.loads((V/'foundation-data/research/PREFLIGHT_PLAN.json').read_text());repo=V.parents[2];base=m.load_checkpoint(repo/plan['checkpointManifestPath'],plan['checkpointSha256']);meta=json.loads((V/'data/data.json').read_text());p=repo/meta['trainTokensPath'];assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['trainTokensSha256'];values=array.array('I');values.frombytes(p.read_bytes());return base,meta,values

def ledger(path,event):
 with path.open('a')as f:f.write(json.dumps(event)+'\n');f.flush();os.fsync(f.fileno())
def main():
 a=argparse.ArgumentParser();a.add_argument('--child',choices=['control','treatment']);args=a.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 plan=json.loads((H/'PLAN14.json').read_text());assert plan['actual_optimizer_step_ceiling']==42 and plan['retained_updates_per_arm']==14
 assert hashlib.sha256((H/'execute14.py').read_bytes()).hexdigest()==plan['runner_sha256']
 schedule=json.loads((V/'allocation-study/schedule.json').read_text());assert hashlib.sha256((V/'allocation-study/schedule.json').read_bytes()).hexdigest()==plan['schedule_sha256'];schedule=schedule['rows'];assert len(schedule)==14
 base,meta,values=load();settings=json.loads((V/'PLAN.json').read_text())['training'];out=H/'execution14';out.mkdir(exist_ok=True)
 for arm in ([args.child]if args.child else['control','treatment']):
  if args.child:saved=torch.load(out/(arm+'-resume7.pt'),map_location='cpu',weights_only=False);state=saved['trajectory'];trace=saved['trace'];start=7
  else:
   if (out/(arm+'.pt')).exists():raise ValueError('Refuse completed-arm overwrite')
   if shutil.disk_usage(out).free<3*135802269+32*1024**2:raise OSError('Insufficient atomic reserve')
   state=base['trajectory'];trace=[];start=0
  model,opt,rng=restore(copy.deepcopy(state),settings);assert all(g['lr']==3e-5 for g in opt.param_groups);history=state['history'];assert all(int(s['step'])==3470+start for s in opt.state_dict()['state'].values())
  for row in schedule[start:]:
   ids=row[arm+'_window_ids'];x,y,dose=pack(values,meta['trainWindows'],ids,model.config['vocabulary']);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters()if p.requires_grad);norm=float(clip_grad_accurate(model.parameters(),1.));assert math.isfinite(norm)
   ledger(out/'updates.jsonl',{'arm':arm,'step':row['step'],'replay':bool(args.child),'event':'intent'})
   opt.step();ledger(out/'updates.jsonl',{'arm':arm,'step':row['step'],'replay':bool(args.child),'event':'completed'})
   trace.append(dict(step=row['step'],loss=float(loss.detach()),gradient_norm=norm,**dose));opt.zero_grad(set_to_none=True)
   if row['step']in[7,14]:
    state_now=trajectory(model,opt,rng,state['order'],state['cursor'],history,3470+row['step']);payload={'modelName':'medium','trajectory':state_now,'trace':trace,'allocation_cursor':row['step'],'arm':arm,'parent_sha256':plan['initial_checkpoint_sha256'],'plan_sha256':hashlib.sha256((H/'PLAN14.json').read_bytes()).hexdigest()}
    if not args.child:
     with(out/'pending.tmp').open('wb')as f:torch.save(payload,f);f.flush();os.fsync(f.fileno())
     os.replace(out/'pending.tmp',out/(arm+('-resume7.pt'if row['step']==7 else'.pt')));fd=os.open(out,os.O_RDONLY);os.fsync(fd);os.close(fd)
   if row['step']==14:
    proof={'trajectory_digest':digest(state_now),'trace':trace,'retained_updates':14}
    write(out/(arm+('-replay-proof.json'if args.child else'-reference.json')),proof)
  if args.child:
   with(out/'pending.tmp').open('wb')as f:f.write(b'incomplete checkpoint after actual replay updates');f.flush();os.fsync(f.fileno())
   os._exit(73)
  old=hashlib.sha256((out/(arm+'-resume7.pt')).read_bytes()).hexdigest()
  proc=subprocess.run([sys.executable,str(H/'execute14.py'),'--child',arm],cwd=V.parents[2]);assert proc.returncode==73
  replay=json.loads((out/(arm+'-replay-proof.json')).read_text());reference=json.loads((out/(arm+'-reference.json')).read_text());assert exact(replay,reference);assert hashlib.sha256((out/(arm+'-resume7.pt')).read_bytes()).hexdigest()==old
  recovered=torch.load(out/(arm+'-resume7.pt'),map_location='cpu',weights_only=False);assert recovered['allocation_cursor']==7
  # Inject ENOSPC before any replace: committed file must remain byte-identical.
  current=hashlib.sha256((out/(arm+'.pt')).read_bytes()).hexdigest()
  try:raise OSError(28,'injected disk full before write')
  except OSError as e:assert e.errno==28
  assert hashlib.sha256((out/(arm+'.pt')).read_bytes()).hexdigest()==current
  write(out/(arm+'-recovery.json'),{'resume7_to14_trace_and_full_state_exact':True,'actual_updates':21,'retained_updates':14,'replay_discarded_updates':7,'process_exit':73,'partial_file_not_promoted':True,'ENOSPC_test':'injected before write, not actual disk exhaustion','committed_checkpoint_unchanged':True})
  (out/'pending.tmp').unlink();(out/(arm+'-resume7.pt')).unlink()
 events=[json.loads(l)for l in(out/'updates.jsonl').open()];completed=[e for e in events if e['event']=='completed'];assert len(completed)==42
 write(out/'receipt.json',{'actual_optimizer_updates':42,'retained_updates':28,'discarded_replay_updates':14,'steps_per_arm':14,'all_replay_state_and_trace_exact':True,'unaccounted_attempts':0,'purpose':'execution validation, not evidence of improved language','formal_adoption':False})
if __name__=='__main__':main()
