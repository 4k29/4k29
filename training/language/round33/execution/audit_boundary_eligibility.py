"""Intrinsic TRAIN boundary features; NO alternate prefix/model condition executed.
Optionally preserve a derived feature map for a future separately frozen round.
"""
import argparse,pathlib,json,hashlib,collections,bisect,sys,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));from batching import sampler
p=argparse.ArgumentParser();p.add_argument('--raw-train-cache',type=pathlib.Path,default=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train'));p.add_argument('--mapping-out',type=pathlib.Path,required=True);a=p.parse_args();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();idx=read(R/'multiview/train.index.json');assert sha(R/'multiview/train.tokens.bin')==idx['tokensSha256'];values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x)for x in read(R/'multiview/tokenizer.json')['bytes']];bl=np.array([len(x)for x in vocab],dtype=np.int64);units={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())};assert len(units)==8975;docs=collections.defaultdict(list);rows=collections.defaultdict(list)
for d in idx['documents']:
 if d['site']=='human-chat':docs[d['sourceDocument']].append(d)
for row in idx['rows']:
 if row['site']=='human-chat':rows[row['unit']].append(row)
stats=collections.defaultdict(collections.Counter);mapping={};changed=set();lengths=[];utts=embedded=empty=0
for key,u in units.items():
 raw=(a.raw_train_cache/pathlib.PurePosixPath(u['sourcePath']).name).read_bytes();assert hashlib.sha256(raw).hexdigest()==u['sourceSha256'];texts=[x['text']for x in json.loads(raw)['utterances']];text='\n'.join(texts);assert text==u['text']and len(texts)==u['utteranceCount'];payload=text.encode();boundaries=[];offset=0;utts+=len(texts);embedded+=sum(t.count('\n')for t in texts);empty+=sum(not t for t in texts)
 for i,t in enumerate(texts):
  offset+=len(t.encode())
  if i<len(texts)-1:offset+=1;boundaries.append(offset)
 assert offset==len(payload);charends={0};pos=0
 for char in text:pos+=len(char.encode());charends.add(pos)
 for d in docs[key]:
  seq=values[d['offset']:d['offset']+d['length']];assert int(seq[0])==1 and int(seq[-1])==2;assert b''.join(vocab[int(t)]for t in seq)==payload;sums=np.concatenate([np.array([0],dtype=np.int64),np.cumsum(bl[seq])]);assert int(sums[-1])==len(payload);aligned=[];c=stats[d['variant']];c['documents']+=1;c['trueInteriorBoundaries']+=len(boundaries)
  for b in boundaries:
   j=int(np.searchsorted(sums,b,side='left'))
   if j<len(sums)and int(sums[j])==b:aligned.append(j)
   else:c['notAlignedAfterTrueSeparator']+=1
  c['alignedAfterTrueSeparator']+=len(aligned);mapping[d['id']]=aligned
  for row in rows[d['id']]:
   base=min(32,row['length']-1);start=row['start'];lo=int(sums[start]);hi=int(sums[start+base]);startok=lo in charends;c['windows']+=1;c['baselinePrefixStartInsideCharacter']+=not startok;c['baselinePrefixEndInsideCharacter']+=hi not in charends;c['positiveWindowEndInsideCharacter']+=int(sums[row['end']])not in charends
   left=bisect.bisect_left(aligned,start+8);right=bisect.bisect_right(aligned,start+base)
   if right>left:
    n=aligned[right-1]-start;c['hasAlignedTrueTurnEndWithin8to32']+=1
    if n==base:c['alreadyEndsAtSuchBoundary']+=1
    elif startok:
     assert 8<=n<base and int(sums[start+n])in charends;c['wouldShortenToLatestSuchEndWithoutRetokenization']+=1;c['originalPrefixTokensForTheseRows']+=base;c['alternativePrefixTokensForTheseRows']+=n;changed.add((row['unit'],row['start'],row['end']));lengths.append(n)
    else:c['availableButOriginalStartInsideCharacter']+=1
   else:c['noSuchAlignedEndFallbackWouldKeepOriginal']+=1
assert utts==269877;strata,weights,_=sampler(idx['rows'],read(R/'policy.json')['genreSampling']);mass=0.;byview=collections.Counter()
for k,rs in strata.items():
 count=sum((r['unit'],r['start'],r['end'])in changed for r in rs);q=weights[k]*count/len(rs);mass+=q;byview[k[1]]+=q
feature=dict(description='Original human TRAIN after-interior-utterance-separator token-end indices, including own BOS in unit token indexing. No BPE splitting/reencoding/EOS/BOS/data change.',sourceDocumentsSha256=sha(R/'sources/documents.jsonl'),trainIndexSha256=sha(R/'multiview/train.index.json'),trainTokensSha256=idx['tokensSha256'],tokenizerSha256=sha(R/'multiview/tokenizer.json'),boundariesByUnit=mapping,notUsedByCurrentTrainer=True)
a.mapping_out.parent.mkdir(parents=True,exist_ok=True);a.mapping_out.write_text(json.dumps(feature,ensure_ascii=False,separators=(',',':'))+'\n');out=dict(admittedHumanTrainDocuments=len(units),humanUtterances=utts,embeddedOriginalNewlinesNotUsedAsTurnMarkers=embedded,emptyOriginalUtterances=empty,perVariant={str(k):dict(v)for k,v in sorted(stats.items())},hypotheticalEligibilityRuleOnly='Latest already-token-aligned true after-turn-separator at8..32 original prefix tokens; only clean original start; otherwise retain original. No alternate prefix was fed to any model.',expectedFrozenSamplerMassOfRowsWhosePrefixWouldChange=mass,expectedMassByView=dict(byview),possibleChangedPrefixLengthStats=dict(count=len(lengths),min=min(lengths)if lengths else None,median=float(np.median(lengths))if lengths else None,mean=float(np.mean(lengths))if lengths else None,max=max(lengths)if lengths else None),featureMapSha256=sha(a.mapping_out),featureMapBytes=a.mapping_out.stat().st_size,auditorSha256=sha(pathlib.Path(__file__)),notUsedByCurrentTrainer=True,noModelOrOptimizerInstantiated=True,additionalOptimizerUpdates=0,noDevOrTestRead=True,noAlternativeLearningConditionExecuted=True,limits='Data-feature/eligibility counts, not evidence that the hypothetical selection improves meaning. Selecting a turn end also changes prefix length; a separate future control would be needed to isolate length from boundary semantics. Partial-character byte-BPE windows do not mean the original UTF8 source or full target coverage is corrupt.')
(E/'turn-boundary-eligibility-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
