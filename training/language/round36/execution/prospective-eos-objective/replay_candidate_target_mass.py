"""Read-only TRAIN draw replay of completed R33; untrained candidate counts."""
import pathlib,json,sys,random,collections,bisect,hashlib,numpy as np,torch
R=pathlib.Path('/workspace/4k29/training/language/round33');F=R.parent/'round34';E=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(R));from batching import sampler,draw
load=lambda p:json.loads(p.read_text());torch.set_num_threads(1)
zero=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);cp=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);assert zero['step']==0 and cp['step']==10000
info=load(R/'multiview/train.index.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');feature=load(F/'human-turn-token-boundaries.json');docs={x['id']:x for x in info['documents']};ends={u:[end for end in es if int(values[docs[u]['offset']+end-1])==16]for u,es in feature['boundariesByUnit'].items()}
eligible={}
for row in info['rows']:
 n=0
 if row['site']=='human-chat':
  es=ends[row['unit']];n=bisect.bisect_right(es,row['start']+row['length'])-bisect.bisect_left(es,row['start']+row['prefixLength']+1)
 eligible[(row['offset'],row['length'],row['prefixLength'])]=n
rng=random.Random();rng.setstate(zero['pythonRng']);strata,weights,masses=sampler(info['rows'],cp['settings']['genreSampling']);tokens=aux=0;ratios=[];batches=0;byview=collections.Counter()
for step in range(1,10001):
 width,rows=draw(rng,8,strata,weights,masses);den=sum(r['length']-r['prefixLength']for r in rows);num=0
 for row in rows:
  n=eligible[(row['offset'],row['length'],row['prefixLength'])];num+=n;byview[str(row['variant'])]+=n
 tokens+=den;aux+=num;ratios.append(num/den);batches+=bool(num)
assert rng.getstate()==cp['pythonRng'];assert tokens==cp['seen_tokens']
out=dict(completedControlRound=33,replayedActualControlDraws=10000,actualNewRoundOptimizerUpdates=0,controlEndingPrivatePythonRngExact=True,originalTargetCountMatchesControl=tokens,prospectiveAuxiliaryTargets=aux,prospectiveAuxiliaryByView=dict(byview),prospectiveRatioOfTotalAuxiliaryToOriginalTargets=aux/tokens,meanPerBatchProspectiveAuxiliaryToOriginalTargetRatio=sum(ratios)/len(ratios),batchesWithEligibleTarget=batches,noModelForwardBackwardOrOptimizer=True,checkpointTensorsLoadedButNotUsedForPrediction=True,noHeldoutOpened=True,noRound34FilesModified=True,notLanguageEvidence=True,notNewTrainingExposure=True,codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
(E/'candidate-target-mass-replay.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
