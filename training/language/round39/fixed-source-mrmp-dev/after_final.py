"""Durable supplemental evaluation after the main completed pipeline; no training.
Never modifies weights, frozen learning inputs, Git, grades or acceptance rules.
"""
import datetime,hashlib,json,pathlib,subprocess,sys,time
D=pathlib.Path(__file__).resolve().parent;R=D.parent;E=R/'execution';repo=R.parents[2];O=E/'fixed-source-mrmp-dev';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'mechanical-complete.json').exists():raise SystemExit('Already measured; do not duplicate')
while True:
 time.sleep(45)
 try:
  flag=E/'automatic-publish-complete.json';mech=E/'mechanical-status.json';result=R/'continue-10000/result.json';ready=False
  if result.exists()and read(result).get('completedRun')and read(result)['completedSteps']==10000:
   if flag.exists()and read(flag)['actualRetainedAdditionalUpdates']==10000:ready=True
   elif mech.exists()and read(mech)['actualRetainedAdditionalUpdates']==10000:
    pid=read(E/'launch.json')['pid'];proc=pathlib.Path(f'/proc/{pid}/cmdline')
    try:alive='round39/execution/supervise.py'in proc.read_bytes().decode(errors='replace')
    except OSError:alive=False
    ready=not alive
 except (json.JSONDecodeError,FileNotFoundError):continue
 if ready:break
O.mkdir(exist_ok=True);statuses={}
def run(args,log,check=True):
 with (O/log).open('ab',buffering=0)as f:return subprocess.run(args,cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,check=check).returncode
for label,C in [('old',R.parent/'round38'),('new',R)]:
 model=C/'continue-10000/model.js';g=O/f'{label}-python.json'
 run([sys.executable,str(D/'evaluate.py'),'--model',str(model),'--out',str(g)],f'{label}-generation.log')
 statuses[label]=run(['node',str(R.parent/'round10/evaluate_js.mjs'),str(model),str(g),str(O/f'{label}-javascript.json')],f'{label}-parity.log',False)
 run([sys.executable,str(D/'check_rounding.py'),'--model',str(model),'--checkpoint',str(C/'continue-10000/checkpoint.pt'),'--generation',str(g),'--out',str(O/f'{label}-unrounded.json')],f'{label}-rounding.log')
a,b=read(O/'old-python.json'),read(O/'new-python.json');assert len(a['rows'])==len(b['rows'])==5 and a['probeSha256']==b['probeSha256'];lines=['# Fixed exposed MRMP human DEV — all10 unedited outputs','','Five first-meeting source documents, ONE speaker-combination family, THREE public pseudonymous speakers. Source CC-BY-SA4.0 and attribution in ../../fixed-source-mrmp-dev; no persona/profile data. Originally frozen at R32, now exposed source DEV; not a new TEST. R38 versus R39, both actual10000 from the same aligned Round28 parent. Same unrestricted own greedy192, Python1thread, no repair or decoding changes. Full tokens in JSON. Semantic assessment pending actual complete reading.','']
for old,new in zip(a['rows'],b['rows'],strict=True):
 assert old['id']==new['id']and old['prefix']==new['prefix'];lines += [f"## {new['id']}",'','Prefix:','```text',new['prefix'],'```','','R38:','```text',old['text'],'```','','R39:','```text',new['text'],'```','']
(O/'FULL_GENERATIONS.md').write_text('\n'.join(lines)+'\n');record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualRetainedR39Updates=10000,probeSha256=sha(D/'probes.json'),contexts=5,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,javascriptExitCodes=statuses,allRawOutputsSaved=True,semanticReadingPending=True,noSemanticScoreGuessed=True,notTest=True,usedForCheckpointSelection=False,trainingConditionChanged=False,publicModelChanged=False,additionalOptimizerUpdates=0);(O/'mechanical-complete.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
