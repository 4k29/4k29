"""Read-only live checkpoint inspection; never trim a running trace or duplicate updates."""
import pathlib,json,torch,hashlib
R=pathlib.Path(__file__).resolve().parents[1];torch.set_num_threads(1);path=R/'continue-10000/checkpoint.pt';cp=torch.load(path,map_location='cpu',weights_only=False)
assert cp['step']>=0 and sorted({int(v['step']) for v in cp['optimizer']['state'].values()})==[20000+cp['step']]
for key in ['model','beststate']:assert all(torch.isfinite(x).all() for x in cp[key].values())
for s in cp['optimizer']['state'].values():assert all(torch.isfinite(s[k]).all() for k in ['exp_avg','exp_avg_sq'])
policy=json.loads((R/'policy.json').read_text());expected_lr=2.2499999999999998e-5 if cp['step']==0 else policy['learningRate']
assert all(g['lr']==expected_lr for g in cp['optimizer']['param_groups'])
assert cp['settings']['experimentPolicySha256']==hashlib.sha256((R/'policy.json').read_bytes()).hexdigest()
trace=R/'continue-10000/training-rollouts.jsonl';rows=[]
if trace.exists():
 for line in trace.read_text().splitlines(keepends=True):
  if line.endswith('\n'):
   row=json.loads(line)
   if row['step']<=cp['step']:rows.append(row)
assert [r['step'] for r in rows]==list(range(10,cp['step']+1,10))
assert len(rows)==cp['rolloutCalls'] and sum(r['generatedTokens'] for r in rows)==cp['rolloutGeneratedTokens'] and sum(r['negativePositions'] for r in rows)==cp['rolloutNegativePositions']
assert cp['settings']['trainerSourceSha256']==hashlib.sha256((R/'train.py').read_bytes()).hexdigest()
context_trace=R/'continue-10000/context-preference.jsonl';context=[]
if context_trace.exists():
 for line in context_trace.read_text().splitlines(keepends=True):
  if line.endswith('\n'):
   row=json.loads(line)
   if row['step']<=cp['step']:context.append(row)
assert [r['step'] for r in context]==list(range(10,cp['step']+1,10))
assert len(context)==cp['contextPreferenceCalls']==cp['step']//10 and sum(r['pairs'] for r in context)==cp['contextPreferencePairs']
print(json.dumps(dict(retainedActualUpdates=cp['step'],optimizerCounters=[20000+cp['step']],contextPreferenceCalls=cp['contextPreferenceCalls'],contextPreferencePairs=cp['contextPreferencePairs'],rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],actualOptimizerLearningRate=expected_lr,learningRateMatchesFrozenPolicyAndZeroTiming=True,allWeightsAndMomentsFinite=True,retainedTraceMatches=True,trainerSourceUnchanged=True,additionalOptimizerUpdates=0,liveTraceNotModified=True)))
