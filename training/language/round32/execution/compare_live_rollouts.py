"""Read-only paired actual TRAIN rollout comparison, not language assessment."""
import hashlib,io,json,pathlib,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';torch.set_num_threads(1)
raw=(R/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);step=cp['step'];assert step>0
paths={n:(R.parent/n/'continue-10000/training-rollouts.jsonl') for n in ['round25','round32']};traces={}
for n,p in paths.items():
 rows=[]
 for line in p.read_text().splitlines(keepends=True):
  if not line.endswith('\n'):continue
  r=json.loads(line)
  if r['step']<=step:rows.append(r)
 assert [r['step'] for r in rows]==list(range(10,step+1,10));traces[n]=rows
for a,b in zip(traces['round25'],traces['round32'],strict=True):
 assert a['sourceRow']==b['sourceRow'] and a['prefixLength']==b['prefixLength'];k=a['prefixLength'];assert a['tokens'][:k]==b['tokens'][:k]
summary={}
for n,rows in traces.items():
 total=sum(r['generatedTokens'] for r in rows);negative=sum(r['negativePositions'] for r in rows)
 summary[n]=dict(calls=len(rows),generatedTokensIncludingEos=total,repeatedFourgramPositions=negative,repeatedPositionFraction=negative/total,meanGeneratedLength=total/len(rows),eosTerminated=sum(r['tokens'][-1]==2 for r in rows),retainedTraceCanonicalSha256=hashlib.sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
assert summary['round32']['calls']==cp['rolloutCalls'] and summary['round32']['generatedTokensIncludingEos']==cp['rolloutGeneratedTokens'] and summary['round32']['repeatedFourgramPositions']==cp['rolloutNegativePositions']
record=dict(actualRetainedUpdates=step,checkpointSha256=hashlib.sha256(raw).hexdigest(),sameOriginalTrainSourceRowsAndTruePrefixTokensEveryCall=True,models=summary,scope='Recorded TRAIN greedy≤64 self-negatives; no extra inference, no optimizer, no DEV/TEST',additionalOptimizerUpdates=0,languageOrUnseenImprovementEstablished=False,limits='Training histories affect their own regularizer, not independent assessment. EOS length and repeat fraction must be reported together. Recorded loss values are not compared as same estimator because scoring dropout mode differs. R25 history is matched in actual update count, not selected inference-step count.')
(E/'interim-rollout-comparison.json').write_text(json.dumps(record,indent=2)+'\n')
history=E/'interim-rollout-history.jsonl'
prior=[json.loads(l) for l in history.read_text().splitlines()] if history.exists() else []
if step not in {r['actualRetainedUpdates'] for r in prior}:
 with history.open('a') as f:f.write(json.dumps(record)+'\n')
print(json.dumps(record))
