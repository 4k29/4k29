"""Frozen full-vocabulary raw greedy and teacher-forced DEV, never sealed TEST."""
import argparse,collections
from common import *
from state import starting
from prose_decode import greedy

def load(name):
 if name in ['initialA','initialB']:return starting(name[-1])[0],0
 arm,step=name.split('-');p=D/'run'/arm/f'checkpoint-{int(step):05d}.pt'
 if p.exists():obj=torch.load(p,weights_only=False)
 else:
  p=D/'run'/arm/f'archive-{int(step):05d}'/'checkpoint.json';obj=loader.load_checkpoint(p,read(p)['sha256'])
 return restore_isolated(obj['trajectory'])[0],obj['active_cursor']

def main():
 a=argparse.ArgumentParser();a.add_argument('--model',required=True);args=a.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);out=D/'evaluation';out.mkdir(exist_ok=True);assert not(out/(args.model+'.json')).exists();proto=read(D/'EVALUATION.json');model,step=load(args.model);model.eval();pieces=[bytes.fromhex(t)for t in read(V/'data/tokenizer.json')['bytes']];totals=collections.defaultdict(lambda:[0.,0]);cases=[]
 with torch.inference_mode():
  for i in range(0,len(proto['dev_windows']),4):
   batch=proto['dev_windows'][i:i+4];x,y=pack(batch);log=model(x)
   for j,r in enumerate(batch):
    loss=float(torch.nn.functional.cross_entropy(log[j],y[j],ignore_index=-100,reduction='sum'));totals[r['panel']][0]+=loss;totals[r['panel']][1]+=int(y[j].ne(-100).sum())
  for c in proto['cases']:
   g=greedy(model,c['prefix'],pieces,max_new=128);g['stopReason']='genuine-eos-token2'if g['eos']else'fixed-max-new-tokens';cases.append({**{k:v for k,v in c.items()if k!='text'},'source_reference_text':c.get('text'),**g})
 panels={p:dict(count=sum(r['panel']==p for r in cases),EOS=sum(r['eos']for r in cases if r['panel']==p),repeat4=sum(r['repeated4gram']is not None for r in cases if r['panel']==p))for p in sorted({r['panel']for r in cases})};summary=dict(model=args.model,cursor=step,NLL={k:dict(nll=v[0]/v[1],nll_sum=v[0],targets=v[1])for k,v in totals.items()},panels=panels,strict_semantic_success='requires full reading; not inferred from EOS/NLL',independent_human_evaluation=False,optimizer_updates=0,all_exposed_DEV=True,plan_sha256=sha(D/'PLAN.json'));write(out/(args.model+'.json'),dict(summary=summary,cases=cases));write(out/(args.model+'-summary.json'),summary);print(summary,flush=True)
if __name__=='__main__':main()
