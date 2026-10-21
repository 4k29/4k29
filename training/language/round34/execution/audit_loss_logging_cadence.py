"""Describe fixed logging cadence; do not infer an all-update total-loss mean."""
import pathlib,json,hashlib,statistics
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round33'
policy=json.loads((R/'policy.json').read_text());factor=policy['sequenceUnlikelihood']['coefficient'];period=policy['sequenceUnlikelihood']['everyUpdates'];assert period==10
records={}
for label,root in [('round33',P),('round34',R)]:
 trace=[json.loads(s)for s in (root/'continue-10000/training-rollouts.jsonl').read_text().splitlines()if s.strip()and json.loads(s)['step']<=5000]
 assert len(trace)==500 and [x['step']for x in trace]==list(range(10,5001,10))
 logs=[]
 for s in (root/'execution/train.log').read_text().splitlines():
  try:x=json.loads(s)
  except json.JSONDecodeError:continue
  if 0<x.get('step',0)<=5000 and 'sequenceUnlikelihoodLoss'in x:logs.append(x)
 assert [x['step']for x in logs]==list(range(100,5001,100))
 bystep={x['step']:x for x in trace}
 assert all(abs(x['sequenceUnlikelihoodLoss']-bystep[x['step']]['loss'])<1e-7 for x in logs)
 records[label]=dict(actualUpdates=5000,allRecordedSequenceCalls=500,periodicLossRecords=50,allPeriodicLossRecordsAreSequenceUpdates=True,sequenceCoefficient=factor,meanScaledSequenceContributionAcrossAll5000UpdatesFromRecordedFloats=factor*sum(x['loss']for x in trace)/5000,meanScaledSequenceContributionInPeriodicLogs=factor*statistics.mean(x['sequenceUnlikelihoodLoss']for x in logs),allUpdateCrossEntropyAndTotalMeanNotAvailableFromPeriodicLogs=True)
out=dict(scope='First retained5000 actual updates each; TRAIN logs only',records=records,validationNllIsSeparatePureTeacherForcedCrossEntropy=True,reportedComponentAveragesUsePythonFloatNotBitExactFp32ObjectiveArithmetic=True,doNotTreatPeriodicTrainingLossAsAllUpdateMean=True,doNotInferGradientMagnitudesFromLossMagnitudes=True,noTrainingOrSelectionChange=True,noModelOrOptimizerUsed=True,noSemanticJudgments=True,codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
(E/'loss-logging-cadence-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
