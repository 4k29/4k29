"""Post-primary exploratory curriculum, new TRAIN entities and explicit assumptions."""
import copy,hashlib,json,pathlib,sys,collections,importlib.util
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from core import restore,trajectory,causal_ce,clip_grad_accurate
from new_tokenizer import Encoder
spec=importlib.util.spec_from_file_location('grounded_training_contract',H/'train.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);batch,save,ledger=module.batch,module.save,module.ledger

def build():
 data=json.loads((H/'data.json').read_text());tok=json.loads((V/'data/tokenizer.json').read_text());enc=Encoder(tok);used={r['entity']for r in data['train'][:2048]};by={r['entity']:r for r in data['train']if r['entity']not in used};names=sorted(by,key=lambda s:hashlib.sha256(('contrast-v1|'+s).encode()).hexdigest())[:96];rows=[]
 for name in names:
  for slot,label in [('parking','駐車場'),('wifi','Wi-Fi')]:
   for free in [False,True]:
    f={'parking':'有り(無料)'if int(hashlib.sha256(name.encode()).hexdigest()[0],16)%2 else'無し','wifi':'有り(無料)'};f[slot]='有り(無料)'if free else'無し';prompt='仮定の設備資料（実際の施設情報とは異なる仮定です）\n施設:'+name+'、駐車場:'+f['parking']+'、Wi-Fi:'+f['wifi']+'\n質問：資料にある'+label+'の利用条件を教えてください。';ans=label+('は無料で利用できます。'if free else'はありません。');pre=[1,3]+enc(prompt)+[2,4];answer=enc(ans)+[2];assert len(pre+answer)<=257;rows.append(dict(id=hashlib.sha256((name+slot+str(free)).encode()).hexdigest(),entity=name,task=slot,prompt=prompt,answer=ans,prefix=pre,answer_ids=answer,sequence=pre+answer,answer_start=len(pre),required=[f[slot]],authorship='program-composed counterfactual teacher',source_object_sha256=by[name]['provenance']['source_object_sha256']))
 assert len(rows)==4*len(names)and len(names)>=32;plan={'data_sha256':hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest(),'steps_per_arm':len(names),'actual_step_ceiling':2*len(names),'new_TRAIN_entities':len(names),'new_cases':len(rows),'previous_TRAIN_entity_overlap':0,'all_examples_explicit_assumptions':True,'frozen_after_primary_evaluation_before_extra_updates':True,'selection':'SHA-first previously unused TRAIN entity, max96; four distinct conditional examples/entity','initial':'each objective own512 endpoint, not a new common-initial strict comparison; shared curriculum continuation','objective_lr_model_unchanged':True,'oldDEV_not_added_to_TRAIN':True};(H/'contrast-data.json').write_text(json.dumps(rows,ensure_ascii=False)+'\n');(H/'CONTRAST_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');print('Frozen extra updates each',len(names))
def run():
 if (H/'run/contrast-receipt.json').exists():raise SystemExit('Completed continuation: refusing additional updates.')
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);rows=json.loads((H/'contrast-data.json').read_text());plan=json.loads((H/'CONTRAST_PLAN.json').read_text());assert hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()==plan['data_sha256'];n=plan['steps_per_arm'];settings=json.loads((V/'PLAN.json').read_text())['training']
 for arm in ['full','response']:
  parent=torch.load(H/'run'/(arm+'-512.pt'),map_location='cpu',weights_only=False);st=parent['trajectory'];model,opt,rng=restore(copy.deepcopy(st),settings);assert all(int(s['step'])==3982 for s in opt.state_dict()['state'].values());trace=[]
  for i in range(n):
   x,y,dose=batch(rows[4*i:4*i+4],arm);opt.zero_grad(set_to_none=True);loss=causal_ce(model(x),y);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all()for p in model.parameters()if p.requires_grad);norm=float(clip_grad_accurate(model.parameters(),1.));ledger(H/'run/contrast-updates.jsonl',dict(arm=arm,step=i+1,event='intent'));opt.step();ledger(H/'run/contrast-updates.jsonl',dict(arm=arm,step=i+1,event='completed'));opt.zero_grad(set_to_none=True);trace.append(dict(step=i+1,loss=float(loss.detach()),gradient_norm=norm,**dose))
   if (i+1)%16==0 or i+1==n:save(H/'run'/(arm+'-extra.pt'),dict(modelName='medium',trajectory=trajectory(model,opt,rng,st['order'],st['cursor'],st['history'],3983+i),trace=trace,active_cursor=i+1,parent_retained_updates=512,extra_updates=i+1,contract='grounded-objective-v1'))
  print('extra',arm,n,flush=True)
 (H/'run/contrast-receipt.json').write_text(json.dumps({'actual_optimizer_updates':2*n,'retained_updates':2*n,'updates_each':n,'replayed_updates':0,'example_repeats':0},indent=2)+'\n')
if __name__=='__main__':build()if sys.argv[-1]=='--build'else run()
