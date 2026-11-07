"""Posthoc description of recorded TRAIN rollouts through retained5000 only."""
import pathlib,json,hashlib,statistics
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round33';E=R/'execution'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def traces(p):
 rows=[]
 for line in p.read_text().splitlines():
  try:x=json.loads(line)
  except json.JSONDecodeError:continue
  if x['step']<=5000:rows.append(x)
 return rows
old=traces(P/'continue-10000/training-rollouts.jsonl');new=traces(R/'continue-10000/training-rollouts.jsonl');assert len(old)==len(new)==500
pairs=list(zip(old,new,strict=True))
for a,b in pairs:assert a['step']==b['step'] and a['sourceRow']==b['sourceRow']
subsets={'all500':pairs,'human155':[(a,b)for a,b in pairs if a['sourceRow']['site']=='human-chat'],'changedHuman132':[(a,b)for a,b in pairs if a['prefixLength']!=b['prefixLength']]}
records={}
for label,subset in subsets.items():
 records[label]=dict(calls=len(subset))
 for side,k in [('controlRound33',0),('round34',1)]:
  rows=[p[k]for p in subset];records[label][side]=dict(meanPrefixLength=statistics.mean(r['prefixLength']for r in rows),medianPrefixLength=statistics.median(r['prefixLength']for r in rows),minPrefixLength=min(r['prefixLength']for r in rows),maxPrefixLength=max(r['prefixLength']for r in rows),totalGeneratedTokens=sum(r['generatedTokens']for r in rows),totalNegativePositions=sum(r['negativePositions']for r in rows),meanUnscaledSequenceLoss=statistics.mean(r['loss']for r in rows))
assert records['human155']['calls']==155 and records['changedHuman132']['calls']==132
out=dict(actualRetainedMilestone=5000,recordedNegativeCallsOnly=True,subsets=records,pairedCheckpointProofSha256=sha(E/'retained-paired-5000/snapshot.json'),notAllPositiveBatchTrace=True,notIndependentReplicates=True,noSemanticJudgments=True,notEvidenceOfMeaningImprovement=True,shorterPrefixAndEndpointAreCombinedPolicy=True,noOptimizerOrModelForward=True,notNewTest=True,codeSha256=sha(pathlib.Path(__file__)))
(E/'prefix-treatment-description-5000.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
