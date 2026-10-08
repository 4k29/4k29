"""Sequential CPU2 pilots/main; vocabulary selection precedes any generation."""
import hashlib,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def command(merges,steps,seed,run,ancestor=None):
 args=[sys.executable,str(ROOT/'train.py'),'--merges',str(merges),'--steps',str(steps),'--dim','192','--layers','8','--heads','4','--batch','8','--threads','2','--seed',str(seed),'--lr','0.00015','--validation-every','1000','--run',run,'--compile','--precision','bfloat16']
 if ancestor:args+=['--ancestor',ancestor]
 return args

def main():
 first=ROOT/'word-512-pilot-1000'
 while not (first/'result.json').exists():time.sleep(10)
 assert read(first/'result.json')['completedRun'],'Interrupted pilot requires exact resume before stage progression'
 second=ROOT/'word-1024-pilot-1000';second_log=pathlib.Path('/workspace/.4k29-round10-pilot-1024.log')
 if not (second/'result.json').exists():
  assert not (second/'checkpoint.pt').exists(),'Existing unfinished pilot requires exact resume'
  with second_log.open('w') as log:subprocess.run(command(1024,1000,2029,second.name),stdout=log,stderr=subprocess.STDOUT,check=True)
 candidates=[]
 for folder in [first,second]:
  result=read(folder/'result.json');metrics=read(folder/'metrics.json');assert result['completedRun'] and result['completedSteps']==1000 and result['checkpointSha256']==sha(folder/'checkpoint.pt')
  assert result['trainerSourceSha256']==sha(ROOT/'train.py') and result['experimentPolicySha256']==sha(ROOT/'training-policy.json')
  candidates.append(dict(run=folder.name,wordMerges=result['wordMerges'],bestStep=result['bestStep'],bestValidationNllPerByte=metrics['bestValidationNllPerByte'],checkpointSha256=sha(folder/'checkpoint.pt'),resultSha256=sha(folder/'result.json'),metricsSha256=sha(folder/'metrics.json'),completedUpdates=1000,parentSelectedWeightLineageUpdates=result['parentSelectedWeightLineageUpdates']))
 selected=min(candidates,key=lambda c:(c['bestValidationNllPerByte'],c['wordMerges']))
 choice=dict(candidates=candidates,selectedRun=selected['run'],wordMerges=selected['wordMerges'],selectedPilotStep=selected['bestStep'],checkpointSha256=selected['checkpointSha256'],bestValidationNllPerByte=selected['bestValidationNllPerByte'],selection='Canonical VAL NLL/UTF8 byte only; ties prefer fewer word rules',completedPilotUpdates=2000,selectedWeightLineageUpdates=selected['parentSelectedWeightLineageUpdates']+selected['bestStep'],trainingPolicySha256=sha(ROOT/'training-policy.json'),generationUsed=False,testUsed=False)
 target=ROOT/'vocabulary-choice.json'
 if target.exists():assert read(target)==choice
 else:write(target,choice)
 print(json.dumps(dict(event='vocabulary-selected',**choice)),flush=True)
 run=f"word-{selected['wordMerges']}-continue-10000";folder=ROOT/run
 if not (folder/'result.json').exists():
  assert not (folder/'checkpoint.pt').exists(),'Existing unfinished main requires exact resume'
  with pathlib.Path('/workspace/.4k29-round10-main-training.log').open('w') as log:subprocess.run(command(selected['wordMerges'],10000,2039,run,selected['run']),stdout=log,stderr=subprocess.STDOUT,check=True)
 assert read(folder/'result.json')['completedRun'] and read(folder/'result.json')['completedSteps']==10000
 print(json.dumps(dict(event='main-completed',run=run)),flush=True)
if __name__=='__main__':main()
