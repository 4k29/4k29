import copy,hashlib,importlib.util,json,pathlib,sys,collections,re
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from checkpoint_io import load as load_snapshot
from core import restore
from eval_core import greedy
from new_tokenizer import Encoder

def score(r,text):
 if r['task']=='fee':return bool(re.search(r'(?<!\d)'+re.escape(r['required'][0])+r'(?!\d)',text))and'円'in text
 if r['task'].startswith('compare'):
  label=r['required'][0]
  return ('同じ'in text or'同額'in text)if label=='同じ'else bool(re.search(label+r'.{0,8}安',text))and not bool(re.search(('子供'if label=='大人'else'大人')+r'.{0,6}安',text))
 if r['task']=='condition':return r['required'][0]in text and not('満たしません'in text and r['required'][0]=='満たします')
 value=r['required'][0]
 if value=='有り(無料)':return'無料'in text and not re.search('無料では|無料じゃ|無料でない|有料',text)
 if value=='有り(有料)':return'有料'in text and'無料'not in text
 return bool(re.search('ありません|ない|無し',text))and not('無料'in text or'有料'in text)
def main():
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);data=json.loads((H/'data.json').read_text());plan=json.loads((H/'PLAN.json').read_text());caseby={r['id']:r for r in data['dev']};cases=[caseby[i]for i in plan['evaluation']['dev_ids']];probe=data['train'][:8];tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(x)for x in tok['bytes']];enc=Encoder(tok);settings=json.loads((V/'PLAN.json').read_text())['training'];s=importlib.util.spec_from_file_location('ownloader',V/'foundation-data/research/zero_update_preflight.py');loader=importlib.util.module_from_spec(s);s.loader.exec_module(loader);initial=loader.load_checkpoint(V/'epoch1/medium/archive/checkpoint.pt.chunks.json',plan['initial_checkpoint_sha256']);out=H/'evaluation-extra';out.mkdir(exist_ok=True);summary={}
 for name in ['full-extra','response-extra']:
  state=initial['trajectory']if name=='initial3470'else load_snapshot(name.replace('32','-32').replace('512','-512'))['trajectory'];model,opt,rng=restore(copy.deepcopy(state),settings);model.eval();rows=[];episodes=[]
  with torch.no_grad():
   for partition,group in [('DEV',cases),('TRAIN-probe',probe)]:
    for r in group:
     seq=r['sequence'];logits=model(torch.tensor([seq[:-1]]))[0];start=r['answer_start']-1;target=torch.tensor(seq[r['answer_start']:]);nll=float(torch.nn.functional.cross_entropy(logits[start:],target,reduction='sum'));g=greedy(model,r['prefix'],pieces,max_new=64);rows.append({'id':r['id'],'task':r['task'],'partition':partition,'prompt':r['prompt'],'program_teacher':r['answer'],'teacher_authorship':r['authorship'],'response_nll_sum':nll,'response_tokens':len(target),'auto_content_candidate':bool(g['strictUtf8'] and score(r,g['text'])),'automated_score_not_formal_semantic_pass':True,**g})
   for r in cases[:2]:
    ids=r['prefix'][:];turns=[]
    for k in range(3):
     if len(ids)+24>256:turns.append({'unsupported_full_history':True});break
     g=greedy(model,ids,pieces,max_new=24);turns.append(g);ids+=g['tokensIncludingEos']
     if not g['eos']:break
     if k<2:ids +=[3]+enc(['この資料のWi-Fiについても教えてください。','では駐車場について教えてください。'][k])+[2,4]
    episodes.append({'id':r['id'],'turns':turns})
   # Existing exposed diagnostics preserved, not a new TEST.
   legacy=json.loads((V/'epoch1/content-dev.json').read_text())['cases'];old23=json.loads((V/'response-data/final/active-dev.json').read_text())['cases'];old=[]
   for c in legacy:old.append({'panel':'native24','id':c['id'],'requirement':c['minimumSemanticRequirement'],**greedy(model,c['prefixTokens'],pieces,max_new=192)})
   for c in old23:pre=[1,3]+enc(c['prompt'])+[2,4];old.append({'panel':'provided23','id':c['id'],**greedy(model,pre,pieces,max_new=c['generation']['max_new_tokens'])})
  (out/(name+'.json')).write_text(json.dumps({'model':name,'cases':rows,'self_history':episodes,'legacy':old,'optimizer_updates':0},ensure_ascii=False,indent=2)+'\n');dev=[r for r in rows if r['partition']=='DEV'];summary[name]={'DEV_auto_candidates':sum(r['auto_content_candidate']for r in dev),'DEV_count':len(dev),'response_NLL_including_EOS':sum(r['response_nll_sum']for r in dev)/sum(r['response_tokens']for r in dev),'TRAIN_auto_candidates':sum(r['auto_content_candidate']for r in rows if r['partition']=='TRAIN-probe'),'mechanical_repetition':sum(r['repeated4gram']is not None for r in dev),'EOS':sum(r['eos']for r in dev),'automatic_not_human_semantic_pass':True};(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(name,summary[name],flush=True)
if __name__=='__main__':main()
