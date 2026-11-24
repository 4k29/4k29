"""Frozen diagnostic generation, exact raw token/text dumps; no training."""
import copy,hashlib,importlib.util,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,digest
from eval_core import greedy
from new_tokenizer import Encoder

def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);plan=json.loads((H/'PLAN14.json').read_text());cases=json.loads((V/'response-data/final/active-dev.json').read_text())['cases'];assert hashlib.sha256((V/'response-data/final/active-dev.json').read_bytes()).hexdigest()==plan['generation']['dev_sha256']
 s=importlib.util.spec_from_file_location('ev_prepare',V/'response-data/evaluation/benchmark.py');ev=importlib.util.module_from_spec(s);s.loader.exec_module(ev);prepared=ev.prepare(cases);prep={r['id']:r for r in prepared};tok=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']];settings=json.loads((V/'PLAN.json').read_text())['training'];s=importlib.util.spec_from_file_location('own_loader',V/'foundation-data/research/zero_update_preflight.py');loader=importlib.util.module_from_spec(s);s.loader.exec_module(loader);initial=loader.load_checkpoint(V/'epoch1/medium/archive/checkpoint.pt.chunks.json',plan['initial_checkpoint_sha256'])
 out=H/'evaluation14';out.mkdir(exist_ok=True);summaries={}
 for name in ['initial3470','control3484','treatment3484']:
  saved=initial
  if name!='initial3470':
   mp=H/'execution14'/('control'if name=='control3484'else'treatment')/'archive/checkpoint.json';md=json.loads(mp.read_text());saved=loader.load_checkpoint(mp.resolve(),md['sha256'])
  if name!='initial3470':assert {int(x['step'])for x in saved['trajectory']['optimizer']['state'].values()}=={3484}
  model,opt,rng=restore(copy.deepcopy(saved['trajectory']),settings);model.eval();before=digest(model.state_dict());rng_before=torch.get_rng_state().clone();rows=[];episodes=[]
  with torch.no_grad():
   for c in cases:
    p=prep[c['id']];r=greedy(model,p['input_ids'],pieces,max_new=c['generation']['max_new_tokens']);rows.append({'id':c['id'],'prompt':c['prompt'],'prefix_ids':p['input_ids'],'source_license':c['source']['license'],**r})
   for ident in plan['generation']['self_history_cases']:
    ids=prep[ident]['input_ids'][:];turns=[]
    for k in range(3):
     if len(ids)+24>256:turns.append({'unsupported_full_context':True,'prefix_ids':ids});break
     r=greedy(model,ids,pieces,max_new=24);turns.append({'turn':k,'prefix_ids':ids[:],**r});ids+=r['tokensIncludingEos']
     if not r['eos']:break
     if k<2:ids +=[3]+enc(plan['generation']['self_history_followups'][k])+[2,4]
    episodes.append({'id':ident,'turns':turns})
  assert before==digest(model.state_dict())and torch.equal(rng_before,torch.get_rng_state())
  (out/(name+'.json')).write_text(json.dumps({'model':name,'generations':rows,'self_history_episodes':episodes,'model_and_rng_unchanged':True,'optimizer_updates':0},ensure_ascii=False,indent=2)+'\n')
  summaries[name]={'cases':len(rows),'eos':sum(r['eos']for r in rows),'repeated4':sum(r['repeated4gram']is not None for r in rows),'unique_raw_outputs':len({r['rawBytesHex']for r in rows}),'formal_language_pass':False,'semantic_reading_required':True}
 (out/'mechanical-summary.json').write_text(json.dumps(summaries,indent=2)+'\n');print('Saved all23 unmodified diagnostic generations and self-history episodes for 3 checkpoints')
if __name__=='__main__':main()
