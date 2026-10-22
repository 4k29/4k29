"""Paired TRAIN self-negative termination counts, never language judgments."""
import pathlib,argparse,json,hashlib,collections
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round35';p=argparse.ArgumentParser();p.add_argument('--through',required=True,type=int);a=p.parse_args();assert a.through in (200,1000,5000,10000)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
newpath=E/f'retained-paired-{a.through}/training-rollouts.jsonl'if a.through<10000 else R/'continue-10000/training-rollouts.jsonl';oldpath=P/'continue-10000/training-rollouts.jsonl'
rows=lambda p:[json.loads(x)for x in p.read_text().splitlines()if json.loads(x)['step']<=a.through]
old,new=rows(oldpath),rows(newpath);assert len(old)==len(new)==a.through//10;totals={}
for x,y in zip(old,new,strict=True):assert x['step']==y['step']and x['sourceRow']==y['sourceRow']and x['prefixLength']==y['prefixLength']and x['tokens'][:x['prefixLength']]==y['tokens'][:y['prefixLength']]
for name,data in [('controlRound35',old),('newRound36',new)]:
 groups={}
 for genre in ['all','human-chat','nonhuman']:
  selected=[r for r in data if genre=='all'or (r['sourceRow']['site']=='human-chat')==(genre=='human-chat')];c=collections.Counter()
  for row in selected:
   generated=row['tokens'][row['prefixLength']:];assert len(generated)==row['generatedTokens'];eos=bool(generated and generated[-1]==2)
   c['calls']+=1;c['generatedTokensIncludingEos']+=len(generated);c['eosEndedCalls']+=eos;c['immediateEosCalls']+=generated==[2];c['negativePositions']+=row['negativePositions'];c['zeroRepeatedNegativeCalls']+=row['negativePositions']==0;c['full64TokenCalls']+=len(generated)==64
  groups[genre]=dict(c)
 totals[name]=groups
report=dict(actualComparedUpdatesEach=a.through,pairedFirstRowAndPrefixHistoriesExactlyEqual=True,counts=totals,controlTraceSha256=sha(oldpath),newRetainedTraceSha256=sha(newpath),scope='Only sampled TRAIN self-negative prefixes and own64-token greedy generations; not fixed DEV, positive targets or language evaluation',notMeaningEvidence=True,noModelForwardOrOptimizer=True,codeSha256=sha(pathlib.Path(__file__)))
(E/f'training-termination-{a.through}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
