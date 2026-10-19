"""Saved4000-step TRAIN negative-rollout EOS diagnosis; not fixed DEV generation."""
import pathlib,json,hashlib,collections,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';paths={'round25':R.parent/'round25/continue-10000/training-rollouts.jsonl','round28':R.parent/'round28/continue-10000/training-rollouts.jsonl','round29':E/'retained-progress-4000/training-rollouts.jsonl'};models={}
for name,p in paths.items():
 rows=[json.loads(l) for l in p.read_text().splitlines()];rows=[r for r in rows if r['step']<=4000];assert [r['step'] for r in rows]==list(range(10,4001,10));groups=collections.defaultdict(collections.Counter)
 for r in rows:
  tokens=r['tokens'];assert len(tokens)==r['prefixLength']+r['generatedTokens'];eos=tokens[-1]==2;assert eos or r['generatedTokens']==64
  for key in ['all',r['sourceRow']['site']]:
   c=groups[key];c['rollouts']+=1;c['eosTerminated']+=int(eos);c['generatedTokens']+=r['generatedTokens'];c['negativePositions']+=r['negativePositions']
 models[name]=dict(traceSha256=hashlib.sha256(p.read_bytes()).hexdigest(),actualUpdatesCovered=4000,groups=dict(groups))
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='TRAIN-prefix own negative-only rollout regularizer, first400calls at actual4000updates, max64, mixedsegmentation, model evolves duringrun',developmentOrUnseenGeneration=False,usedForSelection=False,trainingConditionChanged=False,optimizerUpdatesByThisAnalysis=0,models=models,limitations='Different sampled prefixes/views/corpus exposures and evolving weights; genre-specific EOS counts are diagnostics, not matched-prompt causal estimates, fluency scores, or final language gates. EOS alone is not coherent meaning.')
(E/'rollout-termination-through-4000.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({n:v['groups'] for n,v in models.items()}))
