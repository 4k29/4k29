"""Fixed prose and retained response panels; full-vocabulary, no repair, no TEST."""
import argparse,gzip,json,pathlib
from runtime import H,V,torch,initial,snapshot,restore_isolated,sha,pack
from eval_core import greedy
from new_tokenizer import Encoder
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='initial');a=p.parse_args();out=H/'evaluation';out.mkdir(exist_ok=True)
 assert not(out/(a.model+'.json')).exists(),'Never overwrite past evaluation'
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);base=initial()if a.model=='initial'else snapshot(a.model);model,_,_=restore_isolated(base['trajectory']);model.eval();tok=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(t)for t in tok['bytes']];schedule=json.load(gzip.open(H/'schedule.json.gz','rt'));cases=json.loads((H/'prose-dev.json').read_text())['cases'];prose=[];tot=nt=0;losses=[]
 with torch.no_grad():
  for i in range(0,len(schedule['dev']),4):
   windows=schedule['dev'][i:i+4];x,y=pack(windows);logits=model(x);loss=torch.nn.functional.cross_entropy(logits.reshape(-1,3997),y.reshape(-1),ignore_index=-100,reduction='sum');n=int(y.ne(-100).sum());tot+=float(loss);nt+=n;losses.append(dict(window_ids=[w['id']for w in windows],nll_sum=float(loss),targets=n))
  for c in cases:prose.append({**c,**greedy(model,c['prefix'],pieces,max_new=128)})
  if a.model=='initial':
   old=json.loads((V/'grounded-objective/evaluation/initial3470.json').read_text());old_rows=[r for r in old['cases']if r['partition']=='DEV'];legacy=old['legacy'];reuse=dict(path='grounded-objective/evaluation/initial3470.json',sha256=sha(V/'grounded-objective/evaluation/initial3470.json'),why='same exact3470 model/BPE/core/eval_core and identical old prefixes/greedy budgets; no retraining or score overwrite')
  else:
   dp=json.loads((V/'grounded-objective/data.json').read_text());plan=json.loads((V/'grounded-objective/PLAN.json').read_text());by={r['id']:r for r in dp['dev']};old_rows=[]
   for ident in plan['evaluation']['dev_ids']:
    r=by[ident];old_rows.append(dict(id=r['id'],task=r['task'],prompt=r['prompt'],program_teacher=r['answer'],**greedy(model,r['prefix'],pieces,max_new=64)))
   legacy=[];native=json.loads((V/'epoch1/content-dev.json').read_text())['cases'];provided=json.loads((V/'response-data/final/active-dev.json').read_text())['cases']
   for c in native:legacy.append(dict(id=c['id'],panel='native24',requirement=c['minimumSemanticRequirement'],**greedy(model,c['prefixTokens'],pieces,max_new=192)))
   for c in provided:legacy.append(dict(id=c['id'],panel='provided23',**greedy(model,[1,3]+enc(c['prompt'])+[2,4],pieces,max_new=c['generation']['max_new_tokens'])))
   reuse=None
  cf=json.loads((V/'grounded-objective/CONTEXT_PROBE_PLAN.json').read_text())['cases'];contexts=[]
  for c in cf:contexts.append({**c,**greedy(model,c['prefix'],pieces,max_new=48)})
  # Exact retained old self-history protocol; never insert EOS after budget termination.
  dp=json.loads((V/'grounded-objective/data.json').read_text());plan=json.loads((V/'grounded-objective/PLAN.json').read_text());by={r['id']:r for r in dp['dev']};self_cases=[dict(id=i,prefix=by[i]['prefix'],followups=['この資料のWi-Fiについても教えてください。','では駐車場について教えてください。'])for i in plan['evaluation']['dev_ids'][:2]]
  prompts=[('明日は図書館で本を借り、その後スーパーで牛乳を買う予定です。最初にどこへ行きますか。',['その後はどこへ行く予定でしたか。','買うものは何でしたか。']),('昼食はパンかおにぎりにします。小麦を避けたいので、どちらを選ぶとよいですか。',['なぜその方を選んだのですか。','選んだ食べ物をもう一度教えてください。'])]
  self_cases +=[dict(id='new-assistant-authored-context-'+str(i),prefix=[1,3]+enc(q)+[2,4],followups=qs)for i,(q,qs)in enumerate(prompts)];episodes=[]
  for c in self_cases:
   ids=c['prefix'][:];turns=[]
   for k in range(3):
    if len(ids)+24>256:turns.append(dict(unsupported_full_history=True));break
    g=greedy(model,ids,pieces,max_new=24);turns.append(dict(prefix=ids[:],**g));ids+=g['tokensIncludingEos']
    if not g['eos']:break
    if k<2:ids+=[3]+enc(c['followups'][k])+[2,4]
   episodes.append(dict(**c,turns=turns))
 result=dict(model=a.model,source_checkpoint_unique_updates=base['trajectory']['uniqueUpdates'],actual_optimizer_updates=0,prose_dev=prose,prose_tf_nll=tot/nt,prose_tf_targets=nt,prose_tf_batches=losses,grounded36=old_rows,legacy=legacy,legacy_baseline_reuse=reuse,context12=contexts,self_history=episodes,formal_human_evaluation=False)
 write(out/(a.model+'.json'),result);summary=dict(prose_tf_nll=tot/nt,prose_count=len(prose),prose_EOS=sum(r['eos']for r in prose),prose_repetition=sum(r['repeated4gram']is not None for r in prose),old_native24_generation_count=sum(r['panel']=='native24'for r in legacy),meaning_success_not_automatically_inferred=True);write(out/(a.model+'-summary.json'),summary);print(a.model,summary,flush=True)
if __name__=='__main__':main()
