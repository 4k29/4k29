"""Frozen full-vocabulary raw greedy on old/exposed and newly exposed source-family DEV."""
import argparse,copy,math
from common import *
from state import snapshot,starting
from prose_decode import greedy

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True);ap.add_argument('--label',required=True);a=ap.parse_args();out=P/'evaluation';out.mkdir(exist_ok=True);target=out/(a.label+'.json');assert not target.exists();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 if a.arm in ['initial','fresh']:
  model,opt,rng,base=starting('A'if a.arm=='initial'else'C');counter=0
 else:base=snapshot(a.arm);model,_,_=restore_isolated(base['trajectory']);counter=base['active_cursor']
 model.eval();tok=read(V/'data/tokenizer.json');pieces=[bytes.fromhex(t)for t in tok['bytes']];proto=read(P/'DEV_PROTOCOL.json');old=proto['old24']['cases'];new=proto['cases'];sc=json.load(gzip.open(H/'schedule.json.gz','rt'));dev_ids={r['source_id']for r in new};extra=[r for r in gzrows(P/'corpus.jsonl.gz')if r['id']in dev_ids];nw=[]
 for r in extra:
  for i in range(0,len(r['tokens'])-1,256):nw.append(dict(id=r['id']+'@'+str(i),tokens=r['tokens'][i:i+257]))
 losses={};results=[]
 with torch.inference_mode():
  for name,windows in [('old_prose',sc['dev']),('new_family',nw)]:
   total=0.;count=0
   for i in range(0,len(windows),4):
    x,y=pack(windows[i:i+4]);log=model(x);total+=float(torch.nn.functional.cross_entropy(log.reshape(-1,3997),y.reshape(-1),ignore_index=-100,reduction='sum'));count+=int(y.ne(-100).sum())
   losses[name]=dict(nll=total/count,nll_sum=total,targets=count)
  for panel,rows in [('old24',old),('new9',new)]:
   for c in rows:results.append(dict(panel=panel,**c,**greedy(model,c['prefix'],pieces,max_new=128)))
  # Four deterministic TRAIN probes: memorization diagnostics, never unknown-input evidence.
  tr=sorted([r for r in gzrows(P/'corpus.jsonl.gz')if r['split']=='train'and 80<=len(r['body_tokens'])<=180],key=lambda r:rank('train-probe|'+r['id']))[:4]
  for r in tr:
   prefix=([1]if r['BOS']else[])+r['body_tokens'][:24];results.append(dict(panel='train4',id=r['id'],title=r['title'],prefix=prefix,reference=r['body_tokens'][24:],**greedy(model,prefix,pieces,max_new=128)))
 summary=dict(label=a.label,arm=a.arm,cursor=counter,NLL=losses,aggregate_NLL=sum(r['nll_sum']for r in losses.values())/sum(r['targets']for r in losses.values()),panels={p:dict(count=sum(r['panel']==p for r in results),EOS=sum(r['eos']for r in results if r['panel']==p),repeat4=sum(r['repeated4gram']is not None for r in results if r['panel']==p))for p in ['old24','new9','train4']},optimizer_updates=0,semantic_success_requires_full_reading=True,independent_human_evaluation=False)
 write(target,dict(summary=summary,cases=results));write(out/(a.label+'-summary.json'),summary);print(summary,flush=True)
if __name__=='__main__':main()
