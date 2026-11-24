"""Replay only sampler draws to verify exact resume/RNG and exposure counts.
No forward/backward/optimizer updates are executed. All data are TRAIN only.
"""
import pathlib,sys,json,hashlib,collections,struct
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from train import read,write,sha,load_partition,sampler,draw,torch,random,np
torch.set_num_threads(1)
cp=torch.load(ROOT/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);zero=torch.load(ROOT/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);result=read(ROOT/'continue-10000/result.json')
assert cp['step']==result['completedSteps']==10000 and result['completedRun']
assert sha(ROOT/'continue-10000/checkpoint.pt')==result['checkpointSha256']
rng=random.Random();rng.setstate(zero['pythonRng']);assert rng.getstate()==zero['pythonRng']
info,values=load_partition(ROOT/'multiview','train');strata,weights,masses=sampler(info['rows'],cp['settings']['genreSampling']);tok=read(ROOT.parent/'round11'/'multiview/tokenizer.json');byte_lengths=np.array([len(bytes.fromhex(b)) for b in tok['bytes']],dtype=np.int64)
counts=collections.Counter();byview=collections.defaultdict(lambda:dict(rows=0,targetTokens=0,targetUtf8Bytes=0));bysite=collections.Counter();bysource=collections.Counter();trace=hashlib.sha256();tokens=bytes_seen=0
for step in range(1,cp['step']+1):
 width,rows=draw(rng,cp['settings']['batch'],strata,weights,masses)
 for row in rows:
  bysource['jmrd' if row['document'].startswith('jmrd:')else'realpersona' if row['site']=='human-chat'else'other']+=1
  targets=values[row['offset']+row['prefixLength']:row['offset']+row['length']];n=len(targets);b=int(byte_lengths[targets].sum());tokens+=n;bytes_seen+=b;counts[(row['site'],row['variant'])]+=1;bysite[row['site']]+=1;d=byview[str(row['variant'])];d['rows']+=1;d['targetTokens']+=n;d['targetUtf8Bytes']+=b;trace.update(struct.pack('<QQQQQ',width,row['offset'],row['length'],row['prefixLength'],row['variant']))
assert rng.getstate()==cp['pythonRng'],'Sampler RNG does not match uninterrupted draw sequence'
assert tokens==cp['seen_tokens'] and bytes_seen==cp['seen_bytes']
assert sum(counts.values())==cp['step']*cp['settings']['batch']
total=sum(counts.values())
for d in byview.values():d['rowFraction']=d['rows']/total
write(ROOT/'execution/sampler-replay.json',dict(actualTrainingUpdates=cp['step'],samplerReplayDraws=cp['step'],additionalOptimizerUpdates=0,sampledRows=total,endingPythonRngExactlyMatches=True,seenTargetTokens=tokens,seenTargetUtf8Bytes=bytes_seen,exposureCountsExactlyMatchCheckpoint=True,byView=dict(sorted(byview.items())),bySite=dict(sorted(bysite.items())),byHumanSource=dict(sorted(bysource.items())),siteViewRows={f'{s}:{v}':n for (s,v),n in sorted(counts.items())},drawTraceSha256=trace.hexdigest(),trainIndexSha256=sha(ROOT/'multiview/train.index.json'),trainTokensSha256=info['tokensSha256'],checkpointSha256=result['checkpointSha256'],note='Independent execution of frozen sampler draw replay, not duplicate training. Ending RNG and exact masked target/byte counts match the uninterrupted run; duplicated source views are not independent text.'))
print(json.dumps(dict(actualTrainingUpdates=cp['step'],samplerRngMatched=True,targetCountsMatched=True,additionalOptimizerUpdates=0,byView=dict(byview))))
