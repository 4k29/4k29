"""Zero-update real-model numerical and full-size atomic checkpoint audit."""
import array,hashlib,importlib.util,json,math,os,pathlib,sys,tempfile
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,trajectory,digest,exact,pack,causal_ce,clip_grad_accurate

def run():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 path=V/'foundation-data/research/zero_update_preflight.py';s=importlib.util.spec_from_file_location('prior_checkpoint_io',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 plan=json.loads((V/'foundation-data/research/PREFLIGHT_PLAN.json').read_text());repo=V.parents[2];saved=m.load_checkpoint(repo/plan['checkpointManifestPath'],plan['checkpointSha256']);state=saved['trajectory'];assert state['uniqueUpdates']==3470
 model,opt,rng=restore(state,json.loads((V/'PLAN.json').read_text())['training']);snap=lambda:trajectory(model,opt,rng,state['order'],state['cursor'],state['history'],3470)
 assert exact(snap(),state);before=digest(snap());original=torch.get_rng_state().clone();attempts=[]
 def forbidden(*a,**k):attempts.append(True);raise AssertionError('No optimizer update allowed')
 opt.step=forbidden
 meta=json.loads((V/'data/data.json').read_text());values=array.array('I');values.frombytes((repo/meta['trainTokensPath']).read_bytes());schedule=json.loads((H/'schedule.json').read_text());rows=[]
 for batch in schedule['rows'][:2]:
  for arm in ['control','treatment']:
   torch.set_rng_state(original);opt.zero_grad(set_to_none=True);x,y,dose=pack(values,meta['trainWindows'],batch[arm+'_window_ids'],model.config['vocabulary']);loss=causal_ce(model(x),y);loss.backward()
   ps=[p for p in model.parameters()if p.requires_grad];assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in ps);norm=float(clip_grad_accurate(ps,1.));post=sum(float(p.grad.double().square().sum())for p in ps)**.5;assert math.isfinite(norm)and post<=1.00002
   rows.append(dict(step=batch['step'],arm=arm,loss=float(loss.detach()),gradient_norm=norm,postclip_norm=post,**dose));opt.zero_grad(set_to_none=True)
 torch.set_rng_state(original);assert digest(snap())==before and not attempts
 # Two actual full-size generations and interrupted pending write, private test files only.
 with tempfile.TemporaryDirectory(prefix='full-checkpoint-probe-',dir=H)as td:
  p=pathlib.Path(td);sizes=[]
  for generation in [0,1]:
   with(p/'pending.tmp').open('wb')as f:torch.save(saved,f);f.flush();os.fsync(f.fileno())
   os.replace(p/'pending.tmp',p/f'committed-{generation}.pt');fd=os.open(p,os.O_RDONLY);os.fsync(fd);os.close(fd);sizes.append((p/f'committed-{generation}.pt').stat().st_size)
  (p/'pending.tmp').write_bytes(b'incomplete write - must not replace committed generation')
  recovered=torch.load(p/'committed-1.pt',map_location='cpu',weights_only=False);assert exact(recovered,saved)
 result={'actual_optimizer_updates':0,'optimizer_step_attempts':len(attempts),'forward_backward_batches':len(rows),'reports':rows,'initial_trajectory_digest':before,'final_trajectory_digest':digest(snap()),'model_adam_rng_sampler_history_unchanged':True,'two_full_checkpoint_atomic_fsync_generations_passed':True,'recovered_after_partial_write_exact':True,'serialized_checkpoint_bytes':sizes,'post_update_restart_test_performed':False,'training_authorized':False}
 (H/'NUMERICAL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: 4 forward/backward batches, 0 optimizer updates, exact full-size checkpoint recovery')
if __name__=='__main__':run()
