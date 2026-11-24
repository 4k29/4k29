"""Supplemental unchanged legacy content24 protocol; no model selection/training."""
import copy,hashlib,importlib.util,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,digest
from eval_core import greedy,response_scores

def main():
 torch.set_num_threads(1);torch.use_deterministic_algorithms(True);panel=json.loads((V/'epoch1/content-dev.json').read_text());cases=panel['cases'];settings=json.loads((V/'PLAN.json').read_text())['training'];tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(x)for x in tok['bytes']];s=importlib.util.spec_from_file_location('ownloader',V/'foundation-data/research/zero_update_preflight.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);initial=m.load_checkpoint(V/'epoch1/medium/archive/checkpoint.pt.chunks.json','5ad249d2c8d5910090c9baba94f94483e9c037139d15b9c4360fd3e975409544');out=H/'evaluation14';summaries={}
 for name in ['initial3470','control3484','treatment3484']:
  state=initial['trajectory']
  if name!='initial3470':
   mp=H/'execution14'/('control'if name=='control3484'else'treatment')/'archive/checkpoint.json';md=json.loads(mp.read_text());state=m.load_checkpoint(mp.resolve(),md['sha256'])['trajectory']
  model,opt,rng=restore(copy.deepcopy(state),settings);model.eval();before=digest(model.state_dict());rows=[]
  with torch.no_grad():
   for c in cases:
    logits,score=response_scores(model,c['prefixTokens'],c['goldTokens'],pieces);g=greedy(model,c['prefixTokens'],pieces,c['goldTokens'],logits,max_new=c['generationMaxNewTokens']);rows.append({'id':c['id'],'prefixText':c['prefixText'],'minimumSemanticRequirement':c['minimumSemanticRequirement'],'targetText':c['targetText'],'reference_not_unique':True,'tf':score,**g})
  assert digest(model.state_dict())==before
  (out/(name+'-native24.json')).write_text(json.dumps({'model':name,'cases':rows,'optimizer_updates':0,'legacy_protocol_unchanged':True},ensure_ascii=False,indent=2)+'\n');n=sum(r['tf']['body']['tokens']for r in rows);summaries[name]={'body_tokens':n,'teacher_forced_body_nll':sum(r['tf']['body']['nllSum']for r in rows)/n,'eos':sum(r['eos']for r in rows),'mechanical_repeated4':sum(r['repeated4gram']is not None for r in rows)}
 (out/'native24-summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
if __name__=='__main__':main()
