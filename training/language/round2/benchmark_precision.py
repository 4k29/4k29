"""Isolated, discarded optimizer steps: precision timing, not quality proof."""
import argparse,copy,json,pathlib,random,statistics,sys,time
sys.path.insert(1,str(pathlib.Path(__file__).resolve().parent.parent))
import torch
from torch.nn import functional as F
from train import Decoder,load_partition,pack,read,sha,write,ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('--merges',type=int,required=True);args=p.parse_args()
    torch.set_num_threads(2);torch.manual_seed(929);torch.use_deterministic_algorithms(True)
    directory=ROOT/f'paragraph-bpe-{args.merges}';tok=read(directory/'tokenizer.json');info,values=load_partition(directory,'train')
    rng=random.Random(929);rows=[rng.choice(info['rows']) for _ in range(8)];x,y=pack(rows,values,256)
    cfg=dict(vocabulary=len(tok['bytes']),dim=192,layers=6,heads=4,hidden=768,context=256,dropout=.1,epsilon=1e-5)
    model=Decoder(cfg);initial=copy.deepcopy(model.state_dict());initial_rng=torch.get_rng_state();objectives={}
    for precision in ['float32','bfloat16']:
        def objective(x,y,enabled=precision=='bfloat16'):
            with torch.autocast('cpu',dtype=torch.bfloat16,enabled=enabled):
                return F.cross_entropy(model(x).reshape(-1,cfg['vocabulary']),y.reshape(-1))
        objectives[precision]=torch.compile(objective,dynamic=False)
    reports=[];completed=0
    for precision in ['float32','bfloat16','bfloat16','float32']:
        model.load_state_dict(initial);torch.set_rng_state(initial_rng);model.train();opt=torch.optim.AdamW(model.parameters(),lr=.0005,weight_decay=.05);times=[];losses=[]
        begin=time.monotonic()
        for step in range(15):
            started=time.perf_counter();opt.zero_grad(set_to_none=True);loss=objectives[precision](x,y)
            if not torch.isfinite(loss):raise ValueError('Nonfinite benchmark')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();completed+=1
            if step>=5:times.append(time.perf_counter()-started);losses.append(float(loss.detach()))
        reports.append(dict(precision=precision,warmupDiscardedUpdates=5,measuredDiscardedUpdates=10,seconds=times,losses=losses,totalSeconds=time.monotonic()-begin))
        print(json.dumps(dict(precision=precision,medianSeconds=statistics.median(times),discardedUpdates=completed)),flush=True)
    medians={p:statistics.median([t for r in reports if r['precision']==p for t in r['seconds']]) for p in ['float32','bfloat16']}
    chosen='bfloat16' if medians['bfloat16']<.8*medians['float32'] else 'float32'
    write(ROOT/'precision-benchmark.json',dict(config=cfg,seed=929,threads=2,batch=8,order=['float32','bfloat16','bfloat16','float32'],sourceTokenSha256=info['tokensSha256'],parameters=sum(p.numel() for p in model.parameters()),discardedOptimizerUpdates=completed,retainedOptimizerUpdates=0,reports=reports,medianSeconds=medians,chosenPrecision=chosen,selectionRule='BF16 only if measured median >=20% faster; otherwise FP32. Timing only, not Japanese quality. All model/optimizer updates discarded. FP32 parameters/optimizer and final inference for either precision.',trainerSha256=sha(ROOT/'train.py'),torchVersion=torch.__version__))

if __name__=='__main__':main()
