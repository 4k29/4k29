import pathlib,time,json,subprocess,hashlib,sys
repo=pathlib.Path('/workspace/4k29');base=repo/'training/language/conversation-v2/epoch1';pid=12035
plan=base/'TRAIN_PLAN.json';expected='f458f073d06632b42e641a6d4fd3475bb6c15b86e54d35e84a0611f582a488a1'
if hashlib.sha256(plan.read_bytes()).hexdigest()!=expected:raise ValueError('Frozen plan changed')
print(json.dumps({'event':'monitor_started','mediumPid':pid,'trainingConditionsChanged':False}),flush=True)
while pathlib.Path(f'/proc/{pid}/cmdline').exists():
    if time.time()>json.loads(plan.read_text())['globalDeadlineUnix']+60:raise TimeoutError('Global deadline passed')
    time.sleep(20)
m=json.loads((base/'medium/receipt.json').read_text())
if m['status']!='completed-first-train-epoch' or m['uniqueUpdates']!=3470:raise ValueError('Medium incomplete; small not launched')
if not (base/'medium/resume-wrapper-audit.json').exists():raise ValueError('Resume wrapper completion audit missing')
print(json.dumps({'event':'medium_complete','checkpointSha256':m['checkpointSha256'],'actualContinuationUpdates':m['actualContinuationUpdates']}),flush=True)
cmd=[sys.executable,str(base/'continue_train.py'),'--plan',str(plan),'--plan-sha',expected,'--model','small','--deadline',str(json.loads(plan.read_text())['globalDeadlineUnix'])]
with (base/'training-small.log').open('w')as log:
    subprocess.run(cmd,cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
s=json.loads((base/'small/receipt.json').read_text())
print(json.dumps({'event':'small_complete','status':s['status'],'checkpointSha256':s['checkpointSha256'],'actualContinuationUpdates':s['actualContinuationUpdates']}),flush=True)
