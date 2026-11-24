"""Export actual logs, preserving instantaneous-batch versus full-DEV units."""
import csv,json,pathlib,math,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';result=json.loads((R/'continue-10000/result.json').read_text());assert result['completedRun'] and result['completedSteps']==10000
fields=['round','step','trainingLoss','originalCrossEntropyLoss','crossEntropyLoss','removedEligibleNewlineCe','unlikelihoodLoss','sequenceUnlikelihoodLoss','endEosLoss','contextPreferenceLoss','elapsedSeconds'];train=[]
for label,root in [('round41',R.parent/'round41'),('round42',R)]:
 events=[json.loads(l) for l in (root/'execution/train.log').read_text().splitlines()];events=[x for x in events if 'trainingLoss' in x];assert [x['step'] for x in events]==list(range(100,10001,100))
 for x in events:
  assert all(math.isfinite(v) for k,v in x.items() if k in fields and isinstance(v,(float,int)))
  train.append(dict(round=label,**{k:x.get(k,'') for k in fields if k!='round'}))
with (E/'instantaneous-training-loss-curve.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(train)
aux=[json.loads(l) for l in (R/'continue-10000/context-preference.jsonl').read_text().splitlines()];assert len(aux)==1000 and [x['step'] for x in aux]==list(range(10,10001,10))
with (E/'context-auxiliary-curve.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(aux[0]),lineterminator='\n');w.writeheader();w.writerows(aux)
meta=dict(actualCompletedUpdates=10000,instantaneousTrainingRows=200,rowsEachRound=100,trainingCurveUnit='Loss of one sampled mini-batch at each100th update; NOT full TRAIN mean. Original CE includes all original valid targets; main CE excludes eligible newline numerator but retains original denominator. Missing old contextPreferenceLoss is absent objective, not measured zero.',contextCurveRows=1000,contextCurveUnit='Pre-update loss and correct/wrong mean target NLL on two deterministic cyclic auxiliary pairs, eval mode with gradients; not an all-pool loss curve or generalization metric.',validationCurve='paired-ce-curve.csv from compare_losses.py: full unchanged DEV at0/every500; weighted3views, no language-success implication',codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),additionalOptimizerUpdates=0)
(E/'curve-units.json').write_text(json.dumps(meta,indent=2)+'\n');print(meta)
