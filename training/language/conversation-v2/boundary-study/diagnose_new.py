"""Zero-update probability audit on saved, exact original histories, not resampling."""
import argparse,collections,gzip,json,math,statistics
from eval_runtime import *
def teacher_frequency(windows):
 hist=collections.Counter();counts=collections.Counter()
 for w in windows:
  s=w['tokens'];counts['windows']+=1;counts['targets']+=len(s)-1;counts['EOS']+=s[1:].count(2);counts['BOS']+=s[1:].count(1);counts['role']+=sum(t in[3,4]for t in s[1:]);counts['window_end_EOS']+=s[-1]==2
  for j,t in enumerate(s[1:]):
   if t==2:hist[str(j//32*32)]+=1
 return dict(counts,EOS_position_bins32=dict(hist),EOS_fraction=counts['EOS']/counts['targets'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',required=True);args=p.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);out=N/'diagnostic-new';out.mkdir(exist_ok=True);tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(b)for b in tok['bytes']];groups={k:[]for k in ['whitespace','newline','ASCII_digits_only','contains_ASCII_digit']}
 for i,b in enumerate(pieces):
  if i<6:continue
  try:s=b.decode()
  except UnicodeDecodeError:continue
  if s and s.isspace():groups['whitespace'].append(i)
  if '\n'in s or '\r'in s:groups['newline'].append(i)
  if s and all(c in'0123456789'for c in s):groups['ASCII_digits_only'].append(i)
  if any(c in'0123456789'for c in s):groups['contains_ASCII_digit'].append(i)
 pure=json.load(gzip.open(H/'schedule.json.gz','rt'));mix=json.load(gzip.open(H/'mixed-schedule.json.gz','rt'));freq={}
 for label,ws in [('prose_TRAIN',[w for b in pure['batches']for w in b]),('prose_DEV',pure['dev']),('mixed_TRAIN',[w for b in mix['batches']for w in b])]:freq[label]=teacher_frequency(ws)
 qa=json.loads((H/'qa-data.json').read_text());freq['QA_TRAIN']=dict(examples=len(qa['train']),reply_targets=sum(len(r['answer_ids'])for r in qa['train']),EOS=len(qa['train']));freq['QA_DEV']=dict(examples=len(qa['dev']),reply_targets=sum(len(r['answer_ids'])for r in qa['dev']),EOS=len(qa['dev']))
 write(out/'FREQUENCY.json',freq);write(out/'PROTOCOL.json',dict(models=['control','boundary','clip5'],source_protocol_sha=sha(H/'TOKEN_BOUNDARY_PROTOCOL.json'),scope='All fixed24 source-token-boundary saved greedy histories; full causal forward scores every saved position without changing chosen tokens. Teacher/reference path is original source remainder. Group masses are token spelling proxies; no semantic interpretation of first token departure.',token_groups=groups,optimizer_updates=0))
 eos_windows={p:[w for w in ws if 2 in w['tokens'][1:]]for p,ws in [('train',[w for b in pure['batches']for w in b]),('dev',pure['dev'])]}
 summary=json.loads((out/'SUMMARY.json').read_text())if(out/'SUMMARY.json').exists()else{}
 for name in args.models:
  target=out/(name+'.json');assert not target.exists();model,_,_=restore_isolated((initial()if name=='initial'else snapshot(name))['trajectory']);model.eval();cases=json.loads((N/'evaluation'/(name+'.json')).read_text())['prose_dev'];rows=[];endstats={}
  with torch.no_grad():
   for r in cases:
    pre=r['prefix'];gen=r['tokensIncludingEos'];gold=r['reference_tokens'];K=min(len(gen),len(gold));ar=model(torch.tensor([pre+gen[:-1]]))[0,len(pre)-1:];tf=model(torch.tensor([pre+gold[:-1]]))[0,len(pre)-1:];pa=ar.softmax(-1);pt=tf.softmax(-1);steps=[]
    for j in range(len(gen)):
     p=pa[j];seen=set(gen[max(0,j-16):j]);z=dict(position=j,history_length=len(pre)+j,saved_chosen=gen[j],rescored_argmax=int(p.argmax()),p_chosen=float(p[gen[j]]),p_EOS=float(p[2]),p_previous16_tokens=float(p[list(seen)].sum())if seen else 0,**{'p_'+key:float(p[ids].sum())for key,ids in groups.items()})
     if j<K:z.update(gold=gold[j],p_gold_self_history=float(p[gold[j]]),p_gold_correct_history=float(pt[j,gold[j]]),p_EOS_correct_history=float(pt[j,2]),correct_history_argmax=int(pt[j].argmax()),KL_correct_to_self=float((pt[j]*(pt[j].log()-p.log())).sum()))
     steps.append(z)
    rows.append(dict(id=r['id'],prefix=pre,prefix_text=r['prefix_text'],tokensIncludingEos=gen,rawBytesHex=r['rawBytesHex'],text=r['text'],eos=r['eos'],stopReason=r['stopReason'],repeated4gram=r['repeated4gram'],first_gold_departure=next((j for j,(a,b)in enumerate(zip(gen,gold))if a!=b),None),max_history_length=len(pre)+len(gen)-1,steps=steps))
   for partition,ws in eos_windows.items():
    probs=[]
    for i in range(0,len(ws),4):
     chunk=ws[i:i+4];x=torch.zeros((len(chunk),256),dtype=torch.long)
     for b,w in enumerate(chunk):x[b,:len(w['tokens'])-1]=torch.tensor(w['tokens'][:-1])
     logits=model(x)
     for b,w in enumerate(chunk):
      for j,t in enumerate(w['tokens'][1:]):
       if t==2:probs.append(dict(window=w['id'],position=j,p_EOS=float(logits[b,j].softmax(-1)[2]),argmax=int(logits[b,j].argmax())))
    endstats[partition]=dict(positions=probs,mean_EOS_probability=sum(x['p_EOS']for x in probs)/len(probs)if probs else None,EOS_top1=sum(x['argmax']==2 for x in probs))
   # This probes the actual positional capacity, never rolls or fabricates EOS.
   w=next(w for w in pure['dev']if len(w['tokens'])==257);seq=w['tokens'][:256];at256=int(model(torch.tensor([seq]))[0,-1].argmax());err=None
   try:model(torch.tensor([seq+[at256]]))
   except (IndexError,RuntimeError)as e:err=type(e).__name__+': '+str(e)
   assert err is not None
  write(target,dict(model=name,cases=rows,true_prose_endpoints=endstats,context_probe=dict(input_tokens256_valid=True,next_token=at256,input_tokens257_error=err,saved_primary_cases_never_exceed256=all(r['max_history_length']<=256 for r in rows)),optimizer_updates=0))
  flattened=[z for r in rows for z in r['steps']];summary[name]=dict(EOS=sum(r['eos']for r in rows),repeated4gram=sum(r['repeated4gram']is not None for r in rows),median_first_repeat_completion=statistics.median([r['repeated4gram']['completion']for r in rows if r['repeated4gram']])if any(r['repeated4gram']for r in rows)else None,first8_mean_pEOS=statistics.mean(z['p_EOS']for z in flattened if z['position']<8),last_mean_pEOS=statistics.mean(r['steps'][-1]['p_EOS']for r in rows),rescoring_argmax_mismatch=sum(z['saved_chosen']!=z['rescored_argmax']for z in flattened),first8_correct_history_gold_NLL=statistics.mean(-math.log(max(z['p_gold_correct_history'],1e-40))for z in flattened if z['position']<8 and'p_gold_correct_history'in z),first8_self_history_gold_NLL=statistics.mean(-math.log(max(z['p_gold_self_history'],1e-40))for z in flattened if z['position']<8 and'p_gold_self_history'in z),true_end_TRAIN_mean_pEOS=endstats['train']['mean_EOS_probability'],true_end_DEV_mean_pEOS=endstats['dev']['mean_EOS_probability']);write(out/'SUMMARY.json',summary);print(name,summary[name],flush=True)
if __name__=='__main__':main()
