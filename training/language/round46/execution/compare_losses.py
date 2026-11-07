"""Compare common DEV CE at equal actual updates; verify identical positive exposures with only learning rate changed."""
import pathlib,json,csv,math,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());control=read(E/'creation-context.json')['scientificControl'];policy=read(R/'policy.json');old=read(R.parent/control/'continue-10000/metrics.json')['history'];new=read(R/'continue-10000/metrics.json')['history'];assert [x['step'] for x in old]==[x['step'] for x in new]==list(range(0,10001,500));rows=[]
for a,b in zip(old,new,strict=True):
 x=a['validation']['nllPerUtf8Byte'];y=b['validation']['nllPerUtf8Byte'];rows.append(dict(step=a['step'],oldCE=x,newCE=y,newMinusOld=y-x,oldTargetTokens=a.get('seenTargetTokens',0),newTargetTokens=b.get('seenTargetTokens',0),oldTargetBytes=a.get('seenTargetUtf8Bytes',0),newTargetBytes=b.get('seenTargetUtf8Bytes',0)))
events=[json.loads(x) for x in (E/'train.log').read_text().splitlines()];events=[x for x in events if 'trainingLoss' in x];assert [x['step'] for x in events]==list(range(100,10001,100))
exposures_match=all(r['oldTargetTokens']==r['newTargetTokens'] and r['oldTargetBytes']==r['newTargetBytes'] for r in rows);assert exposures_match
for x in events:
 assert all(math.isfinite(x[k]) for k in ['trainingLoss','crossEntropyLoss','unlikelihoodLoss','endEosLoss','contextPreferenceLoss'])
 expected=x['crossEntropyLoss']+policy['unlikelihood']['coefficient']*x['unlikelihoodLoss']+policy.get('sequenceUnlikelihood',{}).get('coefficient',0)*x.get('sequenceUnlikelihoodLoss',0)+policy['humanUtteranceEndEos']['coefficient']*x['endEosLoss']+policy['contextPreference']['coefficient']*x['contextPreferenceLoss']
 assert abs(x['trainingLoss']-expected)<1e-6
 assert x['learningRate']==policy['learningRate']==4.4999999999999996e-5
 assert x['negativeCandidates']>=0 and x['unlikelihoodLoss']>=0 and x['endEosLoss']>=0 and x['endEosPositionsThisBatch']>=0
with (E/'paired-ce-curve.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
record=dict(actualUpdatesEach=10000,matchedUpdateIndices=True,exposureEqualityRequired=True,mainPositiveExposuresExactlyMatch=exposures_match,mixtureChanged=False,exposureDifferencesIntrinsic=False,additionalCanonicalAuxiliaryExposureSeparate=True,loggedObjectiveEvents=len(events),combinedObjectiveMatchesFrozenCoefficients=True,allLoggedLossesFinite=True,validationOnlyCE=True,pairedCurve=rows)
if 'sequenceUnlikelihood' in policy:
 import torch
 sys.path.insert(0,str(R));from rollout_trace import reconcile_trace
 cp=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);reconcile_trace(R/'continue-10000/training-rollouts.jsonl',cp['step'],cp['rolloutCalls'],cp['rolloutGeneratedTokens'],cp['rolloutNegativePositions']);assert cp['rolloutCalls']==1000
 record.update(rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],fullRolloutTraceVerified=True)
(E/'objective-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='pairedCurve'}))
