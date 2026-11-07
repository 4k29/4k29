"""Post-hoc failure localization on saved outputs and true TRAIN histories; no updates."""
import hashlib,collections,re
from study_runtime import *
from load_model import load

def main():
 out=P/'NEWLINE_COLLAPSE_DIAGNOSIS.json';assert not out.exists();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);tok=read(P.parent/'data/tokenizer.json');pieces=[bytes.fromhex(x)for x in tok['bytes']];nl=pieces.index(b'\n');corpus,schedule=load_data();used={r['record']for b in schedule['arms']['B']for r in b};runhist=collections.Counter();events=[];newline_targets=0;targets=0
 for idx in used:
  s=corpus[idx]['text'];runhist.update(len(x)for x in re.findall(r'\n+',s))
 for batch in schedule['arms']['B']:
  for ref in batch:
   seq=corpus[ref['record']]['tokens'][ref['start']:ref['start']+ref['length']];newline_targets+=seq[1:].count(nl);targets+=len(seq)-1
   for j in range(2,len(seq)):
    if seq[j-2:j]==[nl,nl]and seq[j]!=nl:events.append(dict(ref=ref,target_offset=j,source_id=corpus[ref['record']]['id']))
 events.sort(key=lambda e:hashlib.sha256(('actual-two-NL-history-v1|'+e['source_id']+'|'+str(e['ref']['start'])+'|'+str(e['target_offset'])).encode()).hexdigest());events=events[:32];assert len(events)==32;models={}
 for name in ['base-0','A-579','B-579']:
  model,_=load(name);model.eval();ev=[];gen=[]
  with torch.inference_mode():
   for e in events:
    ref=e['ref'];seq=corpus[ref['record']]['tokens'][ref['start']:ref['start']+ref['length']];j=e['target_offset'];log=model(torch.tensor([seq[:-1]],dtype=torch.long))[0,j-1];p=log.softmax(-1);ev.append(dict(source_id=e['source_id'],source_offset=ref['start']+j,gold=seq[j],argmax=int(log.argmax()),P_newline=float(p[nl]),P_gold=float(p[seq[j]]),P_EOS=float(p[2])))
   for c in read(P/'evaluation'/(name+'.json'))['cases']:
    if c['panel']!='new_source_heldout_paragraph5':continue
    prefix=c['prefix'];emitted=c['tokensIncludingEos'];seq=prefix+emitted;log=model(torch.tensor([seq],dtype=torch.long))[0,len(prefix)-1:len(prefix)-1+len(emitted)];p=log.softmax(-1);points=[i for i in [0,1,2,4,8,16,32,64,127,159]if i<len(emitted)];gen.append(dict(id=c['id'],first_reference_token_departure=next((j for j,(a,b)in enumerate(zip(emitted,c['reference_tokens']))if a!=b),None),departure_is_not_semantic_failure_onset=True,generated_newline_tokens=emitted.count(nl),generated_tokens=len(emitted),replay_argmax_disagreements=int(log.argmax(-1).ne(torch.tensor(emitted)).sum()),probability_trace=[dict(position=i,chosen=emitted[i],P_newline=float(p[i,nl]),P_EOS=float(p[i,2]))for i in points]))
  models[name]=dict(true_TRAIN_two_newline_events=ev,true_history_next_token_is_never_newline=True,train_events_argmax_newline=sum(e['argmax']==nl for e in ev),mean_train_two_NL_P_newline=sum(e['P_newline']for e in ev)/len(ev),mean_train_two_NL_P_gold=sum(e['P_gold']for e in ev)/len(ev),free_generation=gen);del model
 write(out,dict(posthoc_exploratory_diagnostic=True,not_new_DEV_or_TEST=True,selection='Fixed hash32 actual B TRAIN rows with two real newline tokens immediately before a non-newline target. Chosen by observed failure type, not an independent ability benchmark.',newline_token_id=nl,TRAIN_text_newline_run_histogram=dict(runhist),TRAIN_actual_newline_targets=newline_targets,TRAIN_targets=targets,TRAIN_contains_runs_over2=any(k>2 for k in runhist),models=models,actual_optimizer_updates=0,interpretation='Long newline loops are not literal training examples. Distinguish failure even on correct two-newline histories from amplification after self-generated extra newlines. This does not identify a unique cause or prove a specific repair.'))
 print(json.dumps({k:dict(actual_TRAIN_history_NL_argmax=v['train_events_argmax_newline'],events=32,mean_P_NL=v['mean_train_two_NL_P_newline'])for k,v in models.items()}))
if __name__=='__main__':main()
