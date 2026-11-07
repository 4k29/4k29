import copy,shutil,time
from common import *
from state import starting

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(P/'PLAN.json');batches=json.load(gzip.open(P/'schedule.json.gz','rt'))['batches'];results={}
 for f,h in plan['input_sha256'].items():assert sha(ROOT/f)==h
 for arm in ['A','B','C']:
  model,opt,rng,base=starting(arm);drop=torch.get_rng_state().clone();before=digest(model.state_dict());ost=digest(opt.state_dict());x,y=pack(batches[0]);assert torch.equal(x[:,1:][y[:,1:]!=-100],y[:,:-1][y[:,1:]!=-100]);model.eval()
  with torch.no_grad():
   one=model(x);assert torch.equal(one,model(x));z=x.clone();z[:,64:]=6;other=model(z);causal_error=float((one[:,:64]-other[:,:64]).abs().max());assert causal_error<2e-6
   short=model(x[:,:64]);prefix_error=float((short-one[:,:64]).abs().max());assert prefix_error<2e-5
   direct=torch.nn.functional.cross_entropy(one[y!=-100],y[y!=-100]);assert torch.allclose(direct,causal_ce(one,y))
  model.train();torch.set_rng_state(drop);start=time.monotonic();opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert torch.isfinite(loss)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());elapsed=time.monotonic()-start
  assert digest(model.state_dict())==before and digest(opt.state_dict())==ost;opt.zero_grad(set_to_none=True)
  results[arm]=dict(loss=float(loss.detach()),gradient_norm_before_clip=norm,causal_future_error=causal_error,prefix_error=prefix_error,backward_seconds=elapsed,zero_optimizer_updates=True,source_model_SHA256=digest(model.state_dict()),initial_adam_step_values=sorted({int(v['step'])for v in opt.state.values()}),dropout_initial_rng_sha256=digest(drop),state_unchanged=True)
 assert results['A']['source_model_SHA256']==results['B']['source_model_SHA256']!=results['C']['source_model_SHA256'];assert len({r['dropout_initial_rng_sha256']for r in results.values()})==1
 assert shutil.disk_usage(P).free>3*1024**3
 write(P/'PREFLIGHT.json',dict(pass_all=True,arms=results,free_bytes=shutil.disk_usage(P).free,no_optimizer_updates=0,restored_source_sha256=plan['initial_sha256']));print(read(P/'PREFLIGHT.json'))
if __name__=='__main__':main()
