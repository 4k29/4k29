"""Separate untrained configuration resource probes. No optimizer, learning, or corpus changes."""
import argparse,time,resource,subprocess,os
from common import *

def main():
 a=argparse.ArgumentParser();a.add_argument('--dim',type=int);a.add_argument('--context',type=int,default=256);a.add_argument('--all',action='store_true');args=a.parse_args();out=D/'resource-probes';out.mkdir(exist_ok=True)
 if args.all:
  for dim,ctx in [(320,256),(512,256),(704,256),(320,512),(320,1024)]:
   p=out/f'd{dim}-c{ctx}.json'
   if not p.exists():subprocess.run([sys.executable,str(D/'resource_probe.py'),'--dim',str(dim),'--context',str(ctx)],check=True,timeout=120)
  write(D/'RESOURCE_PROBES.json',dict(probes=[read(p)for p in sorted(out.glob('*.json'))],optimizer_updates=0,scope='Only random-own-model single forward/backward feasibility; not learning/capacity evidence. Runs may overlap study worker under CPU2 quota. Adam moments not allocated; estimate adds8bytes/parameter to measured RSS. GPU unmeasured.'))
  return
 assert args.dim in [320,512,704]and args.context in [256,512,1024];torch.set_num_threads(2);torch.use_deterministic_algorithms(True);cfg=dict(read(D/'PLAN.json')['model'],dim=args.dim,hidden=4*args.dim,context=args.context);selected=[]
 with gzip.open(D/'corpus.jsonl.gz','rt')as f:
  for l in f:
   r=json.loads(l)
   if r['split']=='train'and len(r['tokens'])>=args.context+1:selected.append(r)
   if len(selected)==4:break
 assert selected
 unique=len(selected)
 while len(selected)<4:selected.append(selected[0])
 x=torch.tensor([r['tokens'][:args.context]for r in selected]);y=torch.tensor([r['tokens'][1:args.context+1]for r in selected]);torch.manual_seed(61029);model=decoder(cfg);n=sum(p.numel()for p in model.parameters());assert n<55_000_000;model.train();wall=time.monotonic();cpu=time.process_time();loss=causal_ce(model(x),y);loss.backward();norm=math.sqrt(sum(float(p.grad.detach().double().square().sum())for p in model.parameters()if p.grad is not None));assert math.isfinite(norm)and all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters());elapsed=time.monotonic()-wall;cpus=time.process_time()-cpu
 result=dict(config=cfg,parameters=n,batch=4,genuine_targets=4*args.context,source_unit_ids=[r['id']for r in selected],unique_source_units=unique,source_tokens_sha256=digest([r['tokens'][:args.context+1]for r in selected]),seed=61029,forward_backward_wall_seconds=elapsed,process_CPU_seconds=cpus,observed_targets_per_wall_second=4*args.context/elapsed,maximum_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,gradient_norm=norm,loss=float(loss.detach()),FP32_model_bytes=4*n,FP32_model_plus_Adam_bytes_estimate=12*n,extra_Adam_RSS_bytes_not_measured=8*n,optimizer_updates=0,learned_weights_retained=False,language_capability_measured=False,paid_resources=False,thread_count=2,GPU=False)
 write(out/f'd{args.dim}-c{args.context}.json',result);print(args.dim,args.context,n,elapsed,result['maximum_RSS_KiB'],flush=True)
if __name__=='__main__':main()
