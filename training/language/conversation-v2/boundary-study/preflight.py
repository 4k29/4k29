import gzip,time,shutil,resource
from common import *
from mixed_runtime import pack

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);base=initial()['trajectory'];before=digest(base);d=json.load(gzip.open(N/'schedule.json.gz','rt'));rows=[]
 for arm in ['control','boundary']:
  model,opt,_=restore_isolated(base);tick=time.monotonic();n=0
  for b in d[arm][:4]:
   x,y=pack(b);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();norm=float(clip_grad_accurate(model.parameters(),1));assert torch.isfinite(loss)and all(torch.isfinite(p.grad).all()for p in model.parameters());n+=int(y.ne(-100).sum());rows.append(dict(arm=arm,loss=float(loss.detach()),gradient_norm=norm))
  assert digest(base)==before;rows.append(dict(arm=arm,forward_backward_targets_per_second=n/(time.monotonic()-tick)))
 assert shutil.disk_usage(N).free>700*1024**2;write(N/'PREFLIGHT.json',dict(optimizer_updates=0,initial_deepcopy_unchanged=True,torch=torch.__version__,threads=2,GPU=torch.cuda.device_count(),free_bytes=shutil.disk_usage(N).free,maximum_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,rows=rows));print('finite grad/loss and independent source, zero optimizer updates',flush=True)
if __name__=='__main__':main()
