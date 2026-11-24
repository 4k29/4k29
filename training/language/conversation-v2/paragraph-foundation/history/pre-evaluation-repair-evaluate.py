"""Fixed whole-vocabulary greedy, raw bytes and exposed-source paragraph diagnostics."""
import argparse,collections,time
from study_runtime import *
from load_model import load
from prose_decode import greedy

def history_metrics(model,c,g,pieces):
 prefix=c['prefix'];reference=c.get('reference_tokens',[]);emitted=g['tokensIncludingEos'];n=min(64,len(reference),len(emitted),256-len(prefix));result={}
 if not n:return result
 gold=torch.tensor([prefix+reference[:n]],dtype=torch.long);self_ids=torch.tensor([prefix+emitted[:n]],dtype=torch.long)
 tf=model(gold)[0,len(prefix)-1:len(prefix)-1+n];sf=model(self_ids)[0,len(prefix)-1:len(prefix)-1+n];target=torch.tensor(reference[:n]);probs=sf.softmax(-1)
 same=[j for j in range(n)if emitted[:j]==reference[:j]]
 result=dict(common_reference_positions=n,teacher_forced_reference_nll=float(torch.nn.functional.cross_entropy(tf,target)),self_history_reference_nll=float(torch.nn.functional.cross_entropy(sf,target)),teacher_forced_top1_reference_matches=int(tf.argmax(-1).eq(target).sum()),self_history_top1_reference_matches=int(sf.argmax(-1).eq(target).sum()),mean_self_history_EOS_probability=float(probs[:,2].mean()),same_history_argmax_disagreements=sum(int(tf[j].argmax())!=int(sf[j].argmax())for j in same),reference_is_one_valid_continuation_not_unique_semantic_truth=True)
 return result

def main():
 a=argparse.ArgumentParser();a.add_argument('--model',required=True);args=a.parse_args();dest=P/'evaluation'/(args.model+'.json');assert not dest.exists(),'Never overwrite past output';dest.parent.mkdir(exist_ok=True)
 assert read(P/'PREFLIGHT.json')['pass_all'];plan=read(P/'PLAN.json');torch.set_num_threads(2);torch.use_deterministic_algorithms(True);started=time.monotonic();model,_=load(args.model);model.eval();tok=read(P.parent/'data/tokenizer.json');pieces=[bytes.fromhex(x)for x in tok['bytes']];old=read(P.parent/'modern-corpus/next-foundation/EVALUATION.json');new=read(P/'PARAGRAPH_DEV_PROTOCOL.json');cases=[];totals=collections.defaultdict(lambda:[0.,0])
 with torch.inference_mode():
  for key in ['old_dev_windows','caption_dev','maff_dev']:
   rows=old[key]
   for i in range(0,len(rows),4):
    batch=rows[i:i+4];x,y=legacy.pack(batch);log=model(x)
    for j,r in enumerate(batch):
     v=float(torch.nn.functional.cross_entropy(log[j],y[j],ignore_index=-100,reduction='sum'));name=r.get('panel',key);totals[name][0]+=v;totals[name][1]+=int(y[j].ne(-100).sum())
  for c in old['cases']+new['cases']:
   limit=160 if c['panel']=='new_source_heldout_paragraph5'else 128;assert len(c['prefix'])+limit<=256
   g=greedy(model,c['prefix'],pieces,max_new=limit);g['stopReason']='genuine-source-unit-end-token2'if g['eos']else'fixed-max-new-tokens'
   if c['panel']=='new_source_heldout_paragraph5':g['history_diagnostic']=history_metrics(model,c,g,pieces)
   cases.append(dict(**c,**g));print(args.model,c['panel'],c['id'],'EOS',g['eos'],flush=True)
 panels={name:dict(cases=sum(c['panel']==name for c in cases),EOS=sum(c['eos']for c in cases if c['panel']==name),repeat4=sum(c['repeated4gram']is not None for c in cases if c['panel']==name))for name in sorted({c['panel']for c in cases})}
 checkpoint_sha=plan['initial_checkpoint_sha256']if args.model=='base-0'else(read(P/'artifacts'/args.model/'checkpoint.json')['sha256']if(P/'artifacts'/args.model/'checkpoint.json').exists()else sha(P/'private/run'/args.model.split('-')[0]/'checkpoint.pt'))
 summary=dict(model=args.model,checkpoint_sha256=checkpoint_sha,checkpoint_initial_SHA=plan['initial_checkpoint_sha256'],panels=panels,NLL={k:dict(nll=v[0]/v[1],targets=v[1])for k,v in totals.items()},seconds=time.monotonic()-started,optimizer_updates=0,paragraph_protocol_sha256=sha(P/'PARAGRAPH_DEV_PROTOCOL.json'),evaluation_is_exposed_research_DEV=True,independent_human_evaluation=False,semantic_success='Requires entire unmodified generation reading; not inferred from NLL/EOS or first sentence')
 write(dest,dict(summary=summary,cases=cases));write(dest.with_name(dest.stem+'-summary.json'),summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
