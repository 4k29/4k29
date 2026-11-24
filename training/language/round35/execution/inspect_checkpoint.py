"""Read-only live checkpoint inspection; never trim a running trace or duplicate updates."""
import pathlib,json,torch,hashlib
R=pathlib.Path(__file__).resolve().parents[1];torch.set_num_threads(1);path=R/'continue-10000/checkpoint.pt';cp=torch.load(path,map_location='cpu',weights_only=False)
assert cp['step']>=0 and sorted({int(v['step']) for v in cp['optimizer']['state'].values()})==[20000+cp['step']]
for key in ['model','beststate']:assert all(torch.isfinite(x).all() for x in cp[key].values())
for s in cp['optimizer']['state'].values():assert all(torch.isfinite(s[k]).all() for k in ['exp_avg','exp_avg_sq'])
trace=R/'continue-10000/training-rollouts.jsonl';rows=[]
if trace.exists():
 for line in trace.read_text().splitlines(keepends=True):
  if line.endswith('\n'):
   row=json.loads(line)
   if row['step']<=cp['step']:rows.append(row)
assert [r['step'] for r in rows]==list(range(10,cp['step']+1,10))
assert len(rows)==cp['rolloutCalls'] and sum(r['generatedTokens'] for r in rows)==cp['rolloutGeneratedTokens'] and sum(r['negativePositions'] for r in rows)==cp['rolloutNegativePositions']
assert cp['settings']['trainerSourceSha256']==hashlib.sha256((R/'train.py').read_bytes()).hexdigest()
print(json.dumps(dict(retainedActualUpdates=cp['step'],optimizerCounters=[20000+cp['step']],rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],allWeightsAndMomentsFinite=True,retainedTraceMatches=True,trainerSourceUnchanged=True,additionalOptimizerUpdates=0,liveTraceNotModified=True)))
