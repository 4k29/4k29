"""Supplementary newly consumed TRAIN probes; never DEV success or checkpoint selection."""
import argparse,re,hashlib
from study_runtime import *
from load_model import load
from prose_decode import greedy

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');ap.add_argument('--model');a=ap.parse_args();path=P/'TRAIN_PROBE_PROTOCOL.json';tok=read(P.parent/'data/tokenizer.json');pieces=[bytes.fromhex(x)for x in tok['bytes']]
 if a.freeze:
  assert not path.exists();assert not any(DURABLE.glob('*/actual-updates.jsonl')),'Freeze before comparative optimizer calls'
  corpus,schedule=load_data();cases=[]
  for arm in ['A','B']:
   used=sorted({r['record']for b in schedule['arms'][arm]for r in b},key=lambda i:hashlib.sha256(('paragraph-new-TRAIN-probe-v1|'+corpus[i]['id']).encode()).hexdigest());selected=0
   for i in used:
    r=corpus[i];tokens=r['tokens'];body=[t for t in tokens if t>=6]
    if arm=='A':n=max(2,len(tokens)//2)
    else:
     if not r['BOS']or len(tokens)>257 or r['text'].count('。')<3 or re.search(r'[（）()]|法律|法第',r['text']):continue
     boundary=r['text'].find('。')+1;wanted=r['text'][:boundary].encode();matches=[j for j in range(2,min(80,len(tokens)))if b''.join(pieces[t]for t in tokens[:j]).rstrip()==wanted]
     if not matches:continue
     n=max(matches)
    if not 2<=n<len(tokens)-2 or n+160>256:continue
    cases.append(dict(id=r['id'],panel='new_TRAIN_'+arm,source_text=r['text'],source_reference_text_sha256=hashlib.sha256(r['text'].encode()).hexdigest(),prefix=tokens[:n],reference_tokens=tokens[n:],source_family=r['family'],source_url=r.get('source_url'),purpose='TRAIN prediction/memorization diagnostic only; never unknown-family generalization'));selected+=1
    if selected==10:break
   assert selected==10
  write(path,dict(cases=cases,selection='SHA only, fixed before comparative updates and before these new source outputs',model_outputs_seen_for_selection=False,main_evaluation_unchanged=True,decode=dict(greedy=True,max_new_tokens=160,context256_full_history=True),scoring='Exact reference-prefix reproduction indicates memorization only. Read full output separately for naturalness; never add TRAIN successes to DEV numerator.'))
  print('Frozen20 new TRAIN probes');return
 assert a.model;out=P/'train-probes'/(a.model+'.json');assert not out.exists();out.parent.mkdir(exist_ok=True);torch.set_num_threads(2);torch.use_deterministic_algorithms(True);model,_=load(a.model);model.eval();cases=[]
 with torch.inference_mode():
  for c in read(path)['cases']:
   ref=c['reference_tokens'];n=min(len(ref),256-len(c['prefix']));ids=c['prefix']+ref[:n];log=model(torch.tensor([ids],dtype=torch.long))[0,len(c['prefix'])-1:len(c['prefix'])-1+n];target=torch.tensor(ref[:n]);nll=float(torch.nn.functional.cross_entropy(log,target));g=greedy(model,c['prefix'],pieces,max_new=160);cases.append(dict(**c,**g,teacher_forced_nll=nll,teacher_forced_positions=n,reference_prefix_exact=g['tokensIncludingEos'][:n]==ref[:n]));print(a.model,c['id'],flush=True)
 write(out,dict(model=a.model,plan_sha256=sha(P/'PLAN.json'),probe_protocol_sha256=sha(path),cases=cases,optimizer_updates=0,not_DEV=True,not_generalization=True))
if __name__=='__main__':main()
