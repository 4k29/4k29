"""Historical actual-TRAIN exposure audit, no forward/optimizer or heldout reads.
Replay every original draw; union actual target byte spans across three views.
Cumulative exposure is not distinct data or a coverage guarantee.
"""
import collections,hashlib,json,pathlib,random,sys,torch,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));import train as t
torch.set_num_threads(1);out={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['round28','round29']:
 C=R.parent/name;cp=torch.load(C/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);zero=torch.load(C/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);assert cp['step']==10000
 info,values=t.load_partition(C/'multiview','train');indexsha=sha(C/'multiview/train.index.json');vocab= t.read(C/'multiview/tokenizer.json');bl=np.array([len(bytes.fromhex(x)) for x in vocab['bytes']],dtype=np.int64)
 docs={d['id']:d for d in info['documents']};human={k:d for k,d in docs.items() if d['site']=='human-chat'};sources={};ranges=collections.defaultdict(list);cached={};sampled=set();draws=0;htokens=hbytes=tokens=bytes_seen=0;source_draws=collections.Counter()
 for d in human.values():
  key=d['sourceDocument'];n=d['utf8Bytes']
  if key in sources:assert sources[key]==n
  sources[key]=n
 rng=random.Random();rng.setstate(zero['pythonRng']);strata,weights,masses=t.sampler(info['rows'],cp['settings']['genreSampling'])
 for step in range(1,10001):
  width,rows=t.draw(rng,cp['settings']['batch'],strata,weights,masses)
  for row in rows:
   a=row['offset']+row['prefixLength'];b=row['offset']+row['length'];n=b-a;nb=int(bl[values[a:b]].sum());tokens+=n;bytes_seen+=nb
   if row['site']!='human-chat':continue
   draws+=1;htokens+=n;hbytes+=nb;sampled.add((row['unit'],row['start'],row['end']));d=human[row['unit']];key=d['sourceDocument'];source_draws[key]+=1
   if d['id'] not in cached:
    seq=values[d['offset']:d['offset']+d['length']];prefix=np.concatenate([np.array([0],dtype=np.int64),np.cumsum(bl[seq])]);assert int(prefix[-1])==d['utf8Bytes'];cached[d['id']]=prefix
   prefix=cached[d['id']];lo=int(prefix[a-d['offset']]);hi=int(prefix[b-d['offset']]);assert 0<=lo<=hi<=sources[key] and hi-lo==nb
   if hi>lo:ranges[key].append((lo,hi))
 assert rng.getstate()==cp['pythonRng'] and tokens==cp['seen_tokens'] and bytes_seen==cp['seen_bytes']
 unique=0
 for intervals in ranges.values():
  last_lo,last_hi=sorted(intervals)[0]
  for lo,hi in sorted(intervals)[1:]:
   if lo<=last_hi:last_hi=max(last_hi,hi)
   else:unique+=last_hi-last_lo;last_lo,last_hi=lo,hi
  unique+=last_hi-last_lo
 total=sum(sources.values());available=sum(r['site']=='human-chat' for r in info['rows']);assert unique<=min(hbytes,total)
 out[name]=dict(actualUpdates=10000,checkpointSha256=sha(C/'continue-10000/checkpoint.pt'),trainIndexSha256=indexsha,trainTokensSha256=info['tokensSha256'],samplerReplayExactRngAndAllTargetCounts=True,humanGenreSamplingMass=cp['settings']['genreSampling']['human-chat'],humanSourceDocuments=len(sources),humanRawSourceBytesOneCopyAcrossViews=total,humanSampledRows=draws,humanTargetTokensIncludingEos=htokens,humanCumulativeTargetBytes=hbytes,cumulativeByteExposureOverOneCopyCorpus=hbytes/total,humanDistinctSampledWindows=len(sampled),humanAvailableWindowsAcrossViews=available,distinctWindowFraction=len(sampled)/available,humanSourceDocumentsEverSampled=len(source_draws),uniqueRawHumanTargetBytesAcrossViews=unique,uniqueRawByteCoverage=unique/total,untouchedRawHumanBytes=total-unique,notes='Union matches byte positions, not semantic diversity or completed original utterances. EOS has zero source bytes. Sampled context prefixes do not count as targets. Different views overlap the same original byte positions. All direct inputs are historical actual TRAIN only.')
 del cp,zero,info,values,cached
record=dict(models=out,auditorSha256=sha(pathlib.Path(__file__)),noDevOrTestRead=True,noModelForwardOrOptimizer=True,additionalOptimizerUpdates=0,currentR32ConditionChanged=False,interpretation='Quantifies actual exposure/coverage rather than assuming epochs from planned steps. Incomplete coverage makes underexposure plausible, not a proof that more updates improve autoregressive meaning; genre/framing/objective/model limitations remain.')
(E/'human-exposure-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
