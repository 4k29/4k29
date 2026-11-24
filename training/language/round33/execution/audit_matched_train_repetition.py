"""Observed own-negative repetition vs original TRAIN continuation, same prefixes.
No alternative learning condition, model forward, optimizer or heldout access.
"""
import pathlib,json,io,hashlib,sys,collections,torch,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));from sequence_objective import repeated_generated_positions
torch.set_num_threads(1);read=lambda p:json.loads(p.read_text());idx=read(R/'multiview/train.index.json');docs={d['id']:d for d in idx['documents']};values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');models={}
def mask(tokens,p):
 repeated,generated=repeated_generated_positions(torch.tensor([tokens]),p,64);return repeated[generated].tolist()
for name,C in [('round28',R.parent/'round28'),('round33',R)]:
 raw=(C/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);trace=[]
 for line in (C/'continue-10000/training-rollouts.jsonl').read_text().splitlines(keepends=True):
  if line.endswith('\n'):
   x=json.loads(line)
   if x['step']<=cp['step']:trace.append(x)
 assert len(trace)==cp['rolloutCalls']and[x['step']for x in trace]==list(range(10,cp['step']+1,10));assert sum(x['generatedTokens']for x in trace)==cp['rolloutGeneratedTokens'];assert sum(x['negativePositions']for x in trace)==cp['rolloutNegativePositions'];groups=collections.defaultdict(collections.Counter);rows=[]
 for x in trace:
  row=x['sourceRow'];d=docs[row['unit']];p=x['prefixLength'];generated=x['tokens'];prefix=generated[:p];start=row['offset'];assert prefix==list(map(int,values[start:start+p]));source=list(map(int,values[start:min(start+p+64,d['offset']+d['length'])]));assert len(source)>p;amask=mask(generated,p);bmask=mask(source,p);assert sum(amask)==x['negativePositions']and len(amask)==x['generatedTokens'];common=min(len(amask),len(bmask));assert common>0
  rec=dict(step=x['step'],site=row['site'],variant=row['variant'],prefixTokens=p,modelTokens=len(amask),sourceTokens=len(bmask),modelRepeatedPositions=sum(amask),sourceRepeatedPositions=sum(bmask),sameHorizonPositions=common,modelSameHorizonRepeatedPositions=sum(amask[:common]),sourceSameHorizonRepeatedPositions=sum(bmask[:common]),modelEos=generated[-1]==2,sourceEos=source[-1]==2);rows.append(rec)
  for group in ['allSites',row['site']]:
   c=groups[group];c['calls']+=1
   for key in ['modelTokens','sourceTokens','modelRepeatedPositions','sourceRepeatedPositions','sameHorizonPositions','modelSameHorizonRepeatedPositions','sourceSameHorizonRepeatedPositions','modelEos','sourceEos']:c[key]+=rec[key]
 summaries={}
 for group,c in groups.items():summaries[group]={**dict(c),'modelSameHorizonRepeatFraction':c['modelSameHorizonRepeatedPositions']/c['sameHorizonPositions'],'sourceSameHorizonRepeatFraction':c['sourceSameHorizonRepeatedPositions']/c['sameHorizonPositions'],'modelFullRepeatFraction':c['modelRepeatedPositions']/c['modelTokens'],'sourceFullRepeatFraction':c['sourceRepeatedPositions']/c['sourceTokens']}
 models[name]=dict(actualRetainedLocalUpdates=cp['step'],checkpointSha256=hashlib.sha256(raw).hexdigest(),summaries=summaries,rows=rows)
out=dict(models=models,sourceIndexSha256=hashlib.sha256((R/'multiview/train.index.json').read_bytes()).hexdigest(),auditorSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),actualTrainOnly=True,noModelInstantiatedOrForward=True,additionalOptimizerUpdates=0,noAlternativeLearningCondition=True,limits='Own negatives affect their training regularizer, so this is not independent assessment. Original next up-to64 TRAIN tokens are measured only, not added new labels. Same-horizon comparison uses min(observed own/source continuation lengths), with own and source EOS reported. Fourgram repetition is not semantic coherence; different lengths/views/sites/source style remain explicit.')
p=E/f"matched-train-repetition-{models['round33']['actualRetainedLocalUpdates']}.json";p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({name:{k:v for k,v in m['summaries'].items()if k in ['allSites','human-chat']}for name,m in models.items()}))
