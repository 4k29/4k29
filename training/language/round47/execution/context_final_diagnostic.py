"""Frozen TRAIN pair diagnostic across four fixed final states; never a selector."""
import pathlib,json,hashlib,sys,importlib.util,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';O=E/'context-final-diagnostic';O.mkdir(exist_ok=True);torch.set_num_threads(1)
result=json.loads((R/'continue-10000/result.json').read_text());assert result['completedRun'] and result['completedSteps']==10000
sys.path.insert(0,str(R.parent/'round10'));s=importlib.util.spec_from_file_location('own_ev',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(s);s.loader.exec_module(ev)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pool_keys={(x['document'],x['turn']) for x in json.loads((E/'context-auxiliary-pool.json').read_text())['rows']}
states={'old-selected':R.parent/'round46/continue-10000/best-aligned-checkpoint.pt','new-selected':R/'continue-10000/best-aligned-checkpoint.pt','old-terminal':R.parent/'round46/continue-10000/checkpoint.pt','new-terminal':R/'continue-10000/checkpoint.pt'}
for label,path in states.items():
 dest=O/f'{label}.json'
 if dest.exists():
  old=json.loads(dest.read_text());assert old['checkpointSha256']==sha(path);continue
 cp=torch.load(path,map_location='cpu',weights_only=False);m=ev.Decoder(cp['config']);m.load_state_dict(cp['model']);m.eval();groups={}
 for group,planpath in [('diagnostic64',E/'context-plan.json'),('auxiliary1024',E/'context-auxiliary-pool.json')]:
  plan=json.loads(planpath.read_text());rows=[]
  with torch.no_grad():
   for i,r in enumerate(plan['rows']):
    nll=[]
    for key in ['prefixTokens','wrongPrefixTokens']:
     p=[1]+r[key];seq=p+r['targetTokens'];logits=m(torch.tensor([seq[:-1]]))[0,len(p)-1:];nll.append(float(torch.nn.functional.cross_entropy(logits,torch.tensor(r['targetTokens']))))
    rows.append(dict(index=i,document=r['document'],turn=r['turn'],exactAuxiliaryPair=(r['document'],r['turn']) in pool_keys,correctNllPerToken=nll[0],mismatchedNllPerToken=nll[1],contextGain=nll[1]-nll[0]))
  groups[group]=dict(planSha256=sha(planpath),pairs=len(rows),meanCorrectNll=sum(x['correctNllPerToken'] for x in rows)/len(rows),meanMismatchedNll=sum(x['mismatchedNllPerToken'] for x in rows)/len(rows),meanContextGain=sum(x['contextGain'] for x in rows)/len(rows),positiveContextGain=sum(x['contextGain']>0 for x in rows),rows=rows)
 for value in groups.values():
  value['subsetsRelativeToCurrentAuxiliaryPool']={}
  for flag,name in [(True,'currentPoolPair'),(False,'notCurrentPoolPair')]:
   subset=[x for x in value['rows']if x['exactAuxiliaryPair']==flag]
   value['subsetsRelativeToCurrentAuxiliaryPool'][name]=dict(pairs=len(subset),meanCorrectNll=sum(x['correctNllPerToken']for x in subset)/len(subset)if subset else None,meanMismatchedNll=sum(x['mismatchedNllPerToken']for x in subset)/len(subset)if subset else None,meanContextGain=sum(x['contextGain']for x in subset)/len(subset)if subset else None)
 report=dict(label=label,checkpointSha256=sha(path),rawCheckpointStep=cp['step'],actualTrialCompletedUpdates=10000,sourceCodeSha256=sha(pathlib.Path(__file__)),partition='TRAIN ONLY, not heldout/test or semantic generation assessment',trainingUpdates=0,usedForSelection=False,rawFp32PythonOnly=True,groups=groups);dest.write_text(json.dumps(report,indent=2)+'\n');print(label,{k:{a:v for a,v in g.items() if a!='rows'} for k,g in groups.items()},flush=True)
