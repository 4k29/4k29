"""Read-only actual retained TRAIN prefix/Unicode audit and metadata correction.
Reuses the earlier independent source-byte audit, not generation or training.
"""
import hashlib,io,json,pathlib,torch,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest();torch.set_num_threads(1)
rawcp=(R/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(rawcp),map_location='cpu',weights_only=False);step=cp['step'];vocab=[bytes.fromhex(x)for x in read(R/'multiview/tokenizer.json')['bytes']];index=read(R/'multiview/train.index.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');docs={d['id']:d for d in index['documents']};records=[]
for line in (R/'continue-10000/training-rollouts.jsonl').read_text().splitlines(keepends=True):
 if line.endswith('\n'):
  x=json.loads(line)
  if x['step']<=step:records.append(x)
assert [x['step']for x in records]==list(range(10,step+1,10))and len(records)==cp['rolloutCalls'];cache={};rows=[]
for x in records:
 row=x['sourceRow'];d=docs[row['unit']];prefix=x['tokens'][:x['prefixLength']];assert prefix==list(map(int,values[row['offset']:row['offset']+len(prefix)]))
 if d['id']not in cache:
  full=values[d['offset']:d['offset']+d['length']];raw=b''.join(vocab[int(t)]for t in full);assert sha(raw)==d['textSha256'];bounds={0};offset=0
  for char in raw.decode():offset+=len(char.encode());bounds.add(offset)
  sums=[0]
  for token in full:sums.append(sums[-1]+len(vocab[int(token)]))
  cache[d['id']]=(sums,bounds)
 sums,bounds=cache[d['id']];start=sums[row['start']];end=sums[row['start']+len(prefix)];pbytes=b''.join(vocab[int(t)]for t in prefix)
 try:pbytes.decode();valid=True
 except UnicodeDecodeError:valid=False
 rows.append(dict(step=x['step'],unit=d['id'],variant=row['variant'],sourceStartToken=row['start'],prefixTokens=len(prefix),sourceStartByte=start,sourceEndByte=end,startAtUnicodeBoundary=start in bounds,endAtUnicodeBoundary=end in bounds,prefixDecodesUtf8=valid,containsPadding=0 in prefix,beginsWithBos=prefix[0]==1))
s=dict(actualRetainedUpdates=step,calls=len(rows),allPrefixTokensExactlyMatchTrueSource=True,startInsideCharacter=sum(not r['startAtUnicodeBoundary']for r in rows),endInsideCharacter=sum(not r['endAtUnicodeBoundary']for r in rows),prefixDoesNotDecodeUtf8=sum(not r['prefixDecodesUtf8']for r in rows),prefixContainsPadding=sum(r['containsPadding']for r in rows),unitStartBosPrefixes=sum(r['beginsWithBos']for r in rows),laterWindowPrefixesWithoutBos=sum(not r['beginsWithBos']for r in rows))
out=dict(summary=s,rows=rows,checkpointSha256=sha(rawcp),retainedCanonicalTraceSha256=sha(json.dumps(records,sort_keys=True,separators=(',',':')).encode()),trainIndexSha256=sha((R/'multiview/train.index.json').read_bytes()),auditorSha256=sha(pathlib.Path(__file__).read_bytes()),actualTrainOnly=True,noModelInstantiated=True,additionalOptimizerUpdates=0,noLearningConditionChanged=True,interpretation='All retained true source prefixes in the stated checkpoint; not all positive windows or proof of semantics. Policy prefixSelection wording including own BOS applies only to unit-start windows; later overlapping windows start in real context. Frozen implementation/condition is unchanged.')
(E/'current-prefix-character-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(s))
