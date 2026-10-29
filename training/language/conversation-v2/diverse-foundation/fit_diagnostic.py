"""Fixed source-stratified TRAIN teacher fit. Auxiliary, not a new checkpoint selection score."""
import argparse,collections
from common import *
from study_checkpoint import load,model_history

def main():
 a=argparse.ArgumentParser();a.add_argument('--freeze',action='store_true');a.add_argument('--model');args=a.parse_args();p=D/'FIT_DIAGNOSTIC_PROTOCOL.json'
 if args.freeze:
  windows=[w for b in json.load(gzip.open(D/'schedule.json.gz','rt'))['batches']for w in b];selected=[]
  for source in sorted({w['source']for w in windows}):
   seen=set()
   for w in sorted([w for w in windows if w['source']==source],key=lambda w:rank('fit|'+w['id'])):
    if w['unit_id']in seen:continue
    selected.append(w);seen.add(w['unit_id'])
    if len(seen)>=64:break
  write(p,dict(windows=selected,fit_scope='64 unique original units per source, one original window per unit, fixed SHA rank; no optimizer; no selection/adoption changes',registered_after_A_terminal_before_secondary_B_terminal=True,reference_limit='TRAIN vs DEV source/topic and length differences remain; no inference of capacity from one pass alone'))
  return
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);model,cur=load(args.model);model.eval();rows=read(p)['windows'];sums=collections.defaultdict(lambda:[0.,0,0]);details=[]
 with torch.inference_mode():
  for i in range(0,len(rows),4):
   b=rows[i:i+4];x,y=pack(b);logits=model(x);loss=torch.nn.functional.cross_entropy(logits.reshape(-1,3997),y.reshape(-1),ignore_index=-100,reduction='none').reshape_as(y)
   for j,w in enumerate(b):
    for kind,m in [('all',y[j]!=-100),('body',y[j]>=6),('EOS',y[j]==2),('role',(y[j]==3)|(y[j]==4))]:
     if not m.any():continue
     n=int(m.sum());key=w['source']+':'+kind;sums[key][0]+=float(loss[j,m].sum());sums[key][1]+=n;sums[key][2]+=int(logits[j,m].argmax(-1).eq(y[j,m]).sum())
 summary={k:dict(NLL=v[0]/v[1],targets=v[1],gold_top1=v[2]/v[1])for k,v in sums.items()};out=D/'fit';out.mkdir(exist_ok=True);assert not(out/(args.model+'.json')).exists();write(out/(args.model+'.json'),dict(model=args.model,cursor=cur,summary=summary,protocol_sha256=sha(p),optimizer_updates=0));print(summary)
if __name__=='__main__':main()
