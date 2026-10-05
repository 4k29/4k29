"""Own raw TRAIN numerical graph timing, discarded weights, no QA/held data."""
import json,pathlib,time
import torch
from torch.nn import functional as F
from model import Decoder
from train import load_partition,pack
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 torch.set_num_threads(2);config=dict(vocabulary=4358,dim=192,layers=4,heads=4,hidden=768,context=256,dropout=.1)
 info,values=load_partition(ROOT/'bpe-4096','train');x,y=pack(info['rows'][:8],values,256);rows=[]
 for bf16 in [False,True]:
  torch.manual_seed(429);model=Decoder(config);optimizer=torch.optim.AdamW(model.parameters(),lr=.0005)
  def loss_fn(a,b):
   with torch.autocast('cpu',dtype=torch.bfloat16,enabled=bf16):return F.cross_entropy(model(a).flatten(0,1),b.flatten())
  objective=torch.compile(loss_fn,dynamic=False)
  def update():
   optimizer.zero_grad(set_to_none=True);loss=objective(x,y);loss.backward();optimizer.step();return float(loss.detach())
  warm=time.monotonic()
  for _ in range(3):update()
  warm=time.monotonic()-warm;started=time.monotonic()
  losses=[update() for _ in range(20)];duration=time.monotonic()-started
  row=dict(bf16=bf16,compiled=True,warmupDiscardedUpdates=3,timedDiscardedUpdates=20,secondsPerUpdate=duration/20,lastLoss=losses[-1],finite=all(bool(torch.isfinite(p).all()) for p in model.parameters()),compileWarmupSeconds=warm);rows.append(row);print(json.dumps(row),flush=True)
 report=dict(config=config,batch=8,threads=2,seed=429,rows=rows,benchmarkOnly=True,retainedWeights=False,input='First8 own TRAIN stream windows; no VAL/TEST',concurrentMainTraining=True,note='Discarded timing updates, excluded from retained model training counts. Main training ran concurrently, so absolute speed is descriptive only. FP32 and BF16 are different arithmetic, not a claim of bit-identical training or better language.')
 (ROOT/'compiled-precision-benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
