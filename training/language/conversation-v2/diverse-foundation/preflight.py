from common import *
from state import starting
import shutil,time

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=read(D/'PLAN.json');batches=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];results={}
 for f,h in plan['input_sha256'].items():assert sha(ROOT/f)==h,f
 for arm in ['A','B']:
  model,opt,rng,base=starting(arm);assert not opt.state;source=digest(base);weights=digest(model.state_dict());ost=digest(opt.state_dict());rs=digest(torch.get_rng_state());x,y=pack(batches[0]);mask=y[:,1:]!=-100;assert torch.equal(x[:,1:][mask],y[:,:-1][mask]);model.eval()
  with torch.no_grad():
   one=model(x);assert torch.equal(one,model(x));z=x.clone();z[:,64:]=6;err=float((one[:,:64]-model(z)[:,:64]).abs().max());prefixerr=float((one[:,:64]-model(x[:,:64])).abs().max());assert err<2e-6 and prefixerr<2e-5
  model.train();t=time.monotonic();loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert math.isfinite(norm)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());opt.zero_grad(set_to_none=True);assert digest(model.state_dict())==weights and digest(opt.state_dict())==ost and digest(base)==source
  results[arm]=dict(loss=float(loss.detach()),gradient_norm=norm,future_attention_error=err,prefix_error=prefixerr,weights_digest=weights,adam_digest=ost,dropout_initial_rng_digest=rs,backward_seconds=time.monotonic()-t)
 assert results['A']['weights_digest']!=results['B']['weights_digest']and results['A']['adam_digest']==results['B']['adam_digest']and results['A']['dropout_initial_rng_digest']==results['B']['dropout_initial_rng_digest'];assert shutil.disk_usage(D).free>2_500_000_000
 # Full actual-size atomic save/load, stale pending cannot replace last complete state.
 obj=dict(trajectory=trajectory(model,opt,rng,[],0,[],0),active_cursor=0);p=D/'atomic-test.pt';save(p,obj);p.with_suffix('.pending').write_bytes(b'incomplete');loaded=torch.load(p,weights_only=False);assert digest(loaded)==digest(obj);p.unlink();p.with_suffix('.pending').unlink()
 write(D/'PREFLIGHT.json',dict(pass_all=True,arms=results,zero_updates=True,atomic_stale_pending_recovery=True,free_bytes=shutil.disk_usage(D).free,source_sha256=plan['initial_sha256']));print('preflight PASS',flush=True)
if __name__=='__main__':main()
