"""Zero-update audit: probabilities along saved greedy and exact source teacher histories."""
import argparse,math,statistics
from common import *
from state import starting,snapshot

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True);ap.add_argument('--label',required=True);a=ap.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);out=P/'probabilities';out.mkdir(exist_ok=True);assert not(out/(a.label+'.json')).exists()
 if a.arm=='initial':model,_,_,_=starting('A')
 else:model,_,_=restore_isolated(snapshot(a.arm)['trajectory'])
 model.eval();saved=read(P/'evaluation'/(a.label+'.json'))['cases'];pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];groups={k:[]for k in ['whitespace','newline','digits']}
 for i,b in enumerate(pieces):
  if i<6:continue
  try:t=b.decode()
  except UnicodeDecodeError:continue
  if t and t.isspace():groups['whitespace'].append(i)
  if '\n'in t:groups['newline'].append(i)
  if any(c in'0123456789'for c in t):groups['digits'].append(i)
 rows=[];ends={};fixed_tf_first8=[]
 with torch.inference_mode():
  for r in saved:
   if r['panel']=='train4':continue
   pre=r['prefix'];gen=r['tokensIncludingEos'];gold=r.get('reference_tokens',r.get('reference_suffix',[]))[:128];gold=gold[:256-len(pre)];assert gold
   ar=model(torch.tensor([pre+gen[:-1]]))[0,len(pre)-1:].softmax(-1);tf=model(torch.tensor([pre+gold[:-1]]))[0,len(pre)-1:].softmax(-1);steps=[]
   if r['panel']=='old24':fixed_tf_first8.extend(float(tf[j,gold[j]])for j in range(min(8,len(gold))))
   for j,t in enumerate(gen):
    p=ar[j];seen=set(gen[max(0,j-16):j]);z=dict(position0=j,token=t,rescored_argmax=int(p.argmax()),p_EOS=float(p[2]),p_previous16=float(p[list(seen)].sum())if seen else 0,**{'p_'+k:float(p[ids].sum())for k,ids in groups.items()})
    if j<len(gold):z.update(gold=gold[j],p_gold_correct=float(tf[j,gold[j]]),p_gold_self=float(p[gold[j]]),correct_history_argmax=int(tf[j].argmax()))
    steps.append(z)
   rows.append(dict(id=r['id'],panel=r['panel'],eos=r['eos'],repeated4gram=r['repeated4gram'],steps=steps))
  train=sorted([r for r in gzrows(P/'corpus.jsonl.gz')if r['split']=='train'and r['EOS']],key=lambda r:rank('endpoint|'+r['id']))[:32];dev=read(N/'paragraph-dev.json')
  if isinstance(dev,dict):dev=dev.get('dev',dev.get('cases',[]))
  for label,source in [('train32',train),('old_complete_DEV3',dev)]:
   values=[]
   for r in source:
    seq=r['tokens'];start=((len(seq)-2)//256)*256;seq=seq[start:];assert len(seq)<=257 and seq[-1]==2;p=model(torch.tensor([seq[:-1]]))[0,-1].softmax(-1);values.append(dict(id=r['id'],p_EOS=float(p[2]),top1=int(p.argmax())))
   ends[label]=dict(rows=values,mean_pEOS=statistics.mean(z['p_EOS']for z in values),EOS_top1=sum(z['top1']==2 for z in values))
 flat=[s for r in rows if r['panel']=='old24'for s in r['steps']];paired=[z for z in flat if z['position0']<8 and'gold'in z];summary=dict(label=a.label,fixed_first8_TF_positions=len(fixed_tf_first8),fixed_first8_TF_NLL=statistics.mean(-math.log(max(v,1e-40))for v in fixed_tf_first8),paired_actual_first8_positions=len(paired),early_EOS_censoring_scope='Paired TF/self means compare the same actually generated positions within each checkpoint; they are not uncensored cross-checkpoint means.',old24_first8_gold_NLL_correct=statistics.mean(-math.log(max(z['p_gold_correct'],1e-40))for z in paired),old24_first8_gold_NLL_self=statistics.mean(-math.log(max(z['p_gold_self'],1e-40))for z in paired),old24_first8_gold_top1_correct=sum(z['correct_history_argmax']==z['gold']for z in paired)/len(paired),old24_first8_gold_top1_self=sum(z['rescored_argmax']==z['gold']for z in paired)/len(paired),old24_first8_pEOS=statistics.mean(z['p_EOS']for z in flat if z['position0']<8),rescoring_argmax_disagreements=sum(z['token']!=z['rescored_argmax']for r in rows for z in r['steps']),median_repeat_completion_position0=statistics.median(r['repeated4gram']['completion']for r in rows if r['repeated4gram'])if any(r['repeated4gram']for r in rows)else None,endpoint_summary={k:{kk:vv for kk,vv in d.items()if kk!='rows'}for k,d in ends.items()},optimizer_updates=0,first_gold_departure_not_semantic_failure=True)
 write(out/(a.label+'.json'),dict(summary=summary,cases=rows,endpoints=ends));write(out/(a.label+'-summary.json'),summary);print(summary,flush=True)
if __name__=='__main__':main()
