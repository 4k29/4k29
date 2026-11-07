"""Paired CE curve and separately logged combined/CE/UL objective audit."""
import pathlib,json,csv,math
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
read=lambda p:json.loads(p.read_text())
old=read(R.parent/'round25/continue-10000/metrics.json')['history']
new=read(R/'continue-10000/metrics.json')['history']
assert [x['step'] for x in old]==[x['step'] for x in new]==list(range(0,10001,500))
rows=[]
for a,b in zip(old,new,strict=True):
 if a['step']:
  assert a['seenTargetTokens']==b['seenTargetTokens'] and a['seenTargetUtf8Bytes']==b['seenTargetUtf8Bytes']
 x=a['validation']['nllPerUtf8Byte'];y=b['validation']['nllPerUtf8Byte']
 rows.append(dict(step=a['step'],oldCE=x,newCE=y,newMinusOld=y-x))
events=[json.loads(x) for x in (E/'train.log').read_text().splitlines()]
events=[x for x in events if 'trainingLoss' in x]
assert [x['step'] for x in events]==list(range(100,10001,100))
for x in events:
 assert all(math.isfinite(x[k]) for k in ['trainingLoss','crossEntropyLoss','unlikelihoodLoss','sequenceUnlikelihoodLoss'])
 assert abs(x['trainingLoss']-x['crossEntropyLoss']-1.0*x['unlikelihoodLoss']-.1*x['sequenceUnlikelihoodLoss'])<1e-6
 assert x['negativeCandidates']>=0 and x['unlikelihoodLoss']>=0
with (E/'paired-ce-curve.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
record=dict(actualUpdatesEach=10000,matchedEveryValidationExposure=True,loggedObjectiveEvents=len(events),combinedEqualsCEPlusTeacherULPlusPointOneSequenceUL=True,allLoggedLossesFinite=True,validationOnlyCE=True,pairedCurve=rows)
(E/'objective-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='pairedCurve'}))

import torch
from sys import path as import_path
import_path.insert(0,str(R))
from rollout_trace import reconcile_trace
cp=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
reconcile_trace(R/'continue-10000/training-rollouts.jsonl',cp['step'],cp['rolloutCalls'],cp['rolloutGeneratedTokens'],cp['rolloutNegativePositions'])
assert cp['rolloutCalls']==1000 and cp['rolloutNegativePositions']>0
record.update(rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],fullRolloutTraceVerified=True)
(E/'objective-audit.json').write_text(json.dumps(record,indent=2)+'\n')
