"""Replay actual parent and child TRAIN draws; no model forward or optimizer.
Union original human target byte positions across both stages and all views.
"""
import collections,hashlib,io,json,pathlib,random,sys,torch,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';C=R.parent/'round28';sys.path.insert(0,str(R));import train as t
torch.set_num_threads(1);raw=(R/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);parent=torch.load(C/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);zero=torch.load(C/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);childzero=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False)
assert parent['step']==10000 and childzero['pythonRng']==parent['pythonRng'];assert parent['settings']['genreSampling']==cp['settings']['genreSampling'];assert (C/'multiview/train.index.json').read_bytes()==(R/'multiview/train.index.json').read_bytes()
info,values=t.load_partition(R/'multiview','train');bl=np.array([len(bytes.fromhex(b))for b in t.read(R/'multiview/tokenizer.json')['bytes']],dtype=np.int64);human={d['id']:d for d in info['documents']if d['site']=='human-chat'};sources={d['sourceDocument']:d['utf8Bytes']for d in human.values()};ranges=collections.defaultdict(list);cached={};sampled=set();source_seen=set();tokens=byt=htokens=hbytes=draws=0;snapshots={}
rng=random.Random();rng.setstate(zero['pythonRng']);strata,weights,masses=t.sampler(info['rows'],cp['settings']['genreSampling'])
def coverage():
 unique=0
 for intervals in ranges.values():
  lo,hi=sorted(intervals)[0]
  for a,b in sorted(intervals)[1:]:
   if a<=hi:hi=max(hi,b)
   else:unique+=hi-lo;lo,hi=a,b
  unique+=hi-lo
 return dict(humanSampledRows=draws,humanTargetTokensIncludingEos=htokens,humanCumulativeTargetBytes=hbytes,uniqueRawHumanTargetBytesAcrossViews=unique,humanRawSourceBytesOneCopyAcrossViews=sum(sources.values()),uniqueRawByteCoverage=unique/sum(sources.values()),humanDistinctSampledWindows=len(sampled),humanSourceDocumentsEverSampled=len(source_seen),allTargetTokens=tokens,allTargetBytes=byt)
for step in range(1,10000+cp['step']+1):
 width,rows=t.draw(rng,cp['settings']['batch'],strata,weights,masses)
 for row in rows:
  a=row['offset']+row['prefixLength'];b=row['offset']+row['length'];n=b-a;nb=int(bl[values[a:b]].sum());tokens+=n;byt+=nb
  if row['site']!='human-chat':continue
  draws+=1;htokens+=n;hbytes+=nb;sampled.add((row['unit'],row['start'],row['end']));d=human[row['unit']];key=d['sourceDocument'];source_seen.add(key)
  if d['id']not in cached:
   seq=values[d['offset']:d['offset']+d['length']];prefix=np.concatenate([np.array([0],dtype=np.int64),np.cumsum(bl[seq])]);assert int(prefix[-1])==d['utf8Bytes'];cached[d['id']]=prefix
  prefix=cached[d['id']];lo=int(prefix[a-d['offset']]);hi=int(prefix[b-d['offset']]);assert hi-lo==nb and 0<=lo<=hi<=sources[key]
  if hi>lo:ranges[key].append((lo,hi))
 if step==10000:
  assert rng.getstate()==parent['pythonRng'] and tokens==parent['seen_tokens'] and byt==parent['seen_bytes'];snapshots['parentActual10000']=coverage();ptokens,pbytes=tokens,byt
assert rng.getstate()==cp['pythonRng'] and tokens-ptokens==cp['seen_tokens'] and byt-pbytes==cp['seen_bytes'];snapshots['parentPlusChild']=coverage();assert snapshots['parentPlusChild']['uniqueRawByteCoverage']>=snapshots['parentActual10000']['uniqueRawByteCoverage']
out=dict(parentActualUpdates=10000,childActualRetainedUpdates=cp['step'],parentOptimizerCounter=20000,childOptimizerCounter=20000+cp['step'],childCheckpointSha256=hashlib.sha256(raw).hexdigest(),samplerRngAndTargetCountsExactlyMatchBothStages=True,humanSourceDocuments=len(sources),humanGenreSamplingMass=cp['settings']['genreSampling']['human-chat'],snapshots=snapshots,noDevOrTestRead=True,noModelForwardOrOptimizer=True,additionalOptimizerUpdates=0,notSemanticDiversityOrMeaningProof=True,limits='Original target byte union only; repeated views overlap. Context-only exposure is not target exposure. No planned update or forecast counted as completed.')
p=E/f"continued-human-exposure-{cp['step']}.json";p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
