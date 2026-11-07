"""Read-only detached inference controller; no training, selection, retries or overwrite."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,time
HERE=pathlib.Path(__file__).resolve().parent;REPO=HERE.parents[3]
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,v):
 t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def events():
 p=HERE/'recovery-process-ledger.jsonl';return [json.loads(x)for x in p.read_text().splitlines()]if p.exists()else[]
def alive(pid):
 try:os.kill(pid,0);return True
 except ProcessLookupError:return False

def ready(model,amendment_sha):
 p=HERE/model/'receipt.json'
 if not p.exists():return None
 r=read(p)
 if r.get('recoveryAmendmentSha256')!=amendment_sha:return None
 if r['status']!='completed-first-train-epoch' or r['uniqueUpdates']!=3470 or r['actualContinuationUpdates']!={'medium':3052,'small':2960}[model]:raise ValueError('Terminal receipt does not satisfy frozen complete-epoch dose')
 if r['windowsProcessed']!=13878 or r['finalAdamCounters']!=[3470.]:raise ValueError('Incomplete TRAIN windows or Adam counter')
 audits=[read(x)for x in (HERE/model).glob('recovery-wrapper-audit-*.json')]
 if not any(x.get('amendmentSha256')==amendment_sha and x.get('preflightOnly')is False and x.get('model')==model for x in audits):return None
 exits=[x for x in events()if x.get('event')=='exit'and x.get('model')==model]
 if not exits:return None
 if exits[-1]['exitCode']!=0:raise ValueError('Training wrapper exited unsuccessfully')
 m=pathlib.Path(r['checkpointManifest']);archive=read(m)
 if archive['sha256']!=r['checkpointSha256']:raise ValueError('Terminal checkpoint manifest mismatch')
 return r

def main(a):
 if sha(a.plan)!=a.plan_sha:raise ValueError('Monitor execution plan SHA mismatch')
 plan=read(a.plan)
 if sha(__file__)!=plan['monitorSourceSha256']:raise ValueError('Monitor source changed')
 for p,h in plan['sourceReceipts'].items():
  if sha(REPO/p)!=h:raise ValueError('Read-only evaluation utility changed: '+p)
 if sha(HERE/'EVAL_PLAN.json')!=plan['evalPlanSha256']or sha(HERE/'RECOVERY_AMENDMENT.json')!=plan['recoveryAmendmentSha256']:raise ValueError('Evaluation or recovery plan changed')
 target=HERE/'final-eval-monitor-receipt.json'
 if target.exists():raise ValueError('Refuse duplicate inference monitor')
 receipt=dict(status='waiting-for-fixed-first-epoch-terminals',pid=os.getpid(),ppid=os.getppid(),session=os.getsid(0),startedUnix=time.time(),monitorSourceSha256=plan['monitorSourceSha256'],executionPlanSha256=a.plan_sha,trainingUpdates=0,automaticRetry=False,outputsOverwritten=False,completed=[])
 write(target,receipt)
 try:
  for model in ['medium','small']:
   while True:
    r=ready(model,plan['recoveryAmendmentSha256'])
    if r:break
    es=events()
    if any(x.get('event')=='exit'and x.get('exitCode',0)!=0 for x in es):raise RuntimeError('Training failure; no evaluation of partial endpoint')
    if not alive(plan['trainingControllerPid']):raise RuntimeError('Training controller unavailable before complete terminal receipt')
    time.sleep(10)
   out=HERE/'evaluation'/(model+'-epoch1')
   if out.exists():raise ValueError('Refuse existing endpoint directory; no automatic overwrite/retry')
   command=[sys.executable,str(HERE/'evaluate_epoch.py'),'--plan',str(HERE/'EVAL_PLAN.json'),'--plan-sha',plan['evalPlanSha256'],'--model',model,'--endpoint',model+'-epoch1','--expected-updates','3470','--checkpoint-sha',r['checkpointSha256'],'--manifest',r['checkpointManifest']]
   print(json.dumps(dict(event='evaluate',model=model,unix=time.time(),checkpointSha256=r['checkpointSha256'])),flush=True)
   started=time.time()
   with (HERE/f'evaluation-{model}-epoch1.log').open('x')as log:
    code=subprocess.run(command,cwd=REPO,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,check=False).returncode
   row=dict(model=model,command=command,checkpointSha256=r['checkpointSha256'],exitCode=code,startedUnix=started,endedUnix=time.time(),trainingReceiptSha256=sha(HERE/model/'receipt.json'))
   receipt['completed'].append(row);write(target,receipt)
   if code!=0:raise RuntimeError('Evaluation failed; no automatic retry')
  for script in ['compare_evaluations.py','audit_eval_results.py','build_blind_pack.py']:
   with (HERE/('final-'+script.replace('.py','.log'))).open('x')as log:
    code=subprocess.run([sys.executable,str(HERE/script)],cwd=REPO,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,check=False).returncode
   if code!=0:raise RuntimeError('Read-only final evaluation utility failed: '+script)
  pack=read(HERE/'blind-pack.json');singles=sum(x.get('kind')!='selfplay'for x in pack['rows']);episodes=sum(x.get('kind')=='selfplay'for x in pack['rows'])
  if singles!=224 or episodes!=16:raise AssertionError('Incomplete fixed4endpoint blind output inventory')
  receipt.update(status='complete',endedUnix=time.time(),singleFullOutputs=singles,selfplayEpisodes=episodes,semanticReadersLaunched=False,sealedTestUsed=False,blindPackSha256=sha(HERE/'blind-pack.json'),evaluationAuditSha256=sha(HERE/'evaluation-audit.json'))
  write(target,receipt);print(json.dumps(receipt),flush=True)
 except BaseException as e:
  receipt.update(status='failed-no-automatic-retry',error=repr(e),endedUnix=time.time());write(target,receipt);raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha',required=True);main(p.parse_args())
