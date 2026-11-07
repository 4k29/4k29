"""Mechanical actual-TRAIN prefix identity/character-boundary audit; zero updates."""
import pathlib,json,hashlib,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();models={}
for name,folder,trace in [('round25',R.parent/'round25',R.parent/'round25/continue-10000/training-rollouts.jsonl'),('round28',R.parent/'round28',R.parent/'round28/continue-10000/training-rollouts.jsonl'),('round29',R.parent/'round29',R.parent/'round29/continue-10000/training-rollouts.jsonl'),('round30',R.parent/'round30',R.parent/'round30/continue-10000/training-rollouts.jsonl'),('round31actual2000',R,E/'retained-progress-2000/training-rollouts.jsonl')]:
 vocab=[bytes.fromhex(x) for x in read(folder/'multiview/tokenizer.json')['bytes']];index=read(folder/'multiview/train.index.json');values=np.memmap(folder/'multiview/train.tokens.bin',dtype='<u4',mode='r');docs={d['id']:d for d in index['documents']};records=[json.loads(x) for x in trace.read_text().splitlines()];cache={};rows=[]
 for x in records:
  row=x['sourceRow'];d=docs[row['unit']];prefix=x['tokens'][:x['prefixLength']];assert prefix==list(map(int,values[row['offset']:row['offset']+len(prefix)]))
  if d['id'] not in cache:
   full=values[d['offset']:d['offset']+d['length']];raw=b''.join(vocab[int(t)] for t in full);assert hashlib.sha256(raw).hexdigest()==d['textSha256'];text=raw.decode();bounds={0};offset=0
   for ch in text:offset+=len(ch.encode());bounds.add(offset)
   cumsum=[0]
   for tok in full:cumsum.append(cumsum[-1]+len(vocab[int(tok)]))
   cache[d['id']]=(cumsum,bounds)
  offsets,bounds=cache[d['id']];start=offsets[row['start']];end=offsets[row['start']+len(prefix)];raw=b''.join(vocab[int(t)] for t in prefix)
  try:raw.decode();valid=True
  except UnicodeDecodeError:valid=False
  rows.append(dict(step=x['step'],unit=d['id'],variant=row['variant'],sourceStartToken=row['start'],prefixTokens=len(prefix),sourceStartByte=start,sourceEndByte=end,startAtUnicodeBoundary=start in bounds,endAtUnicodeBoundary=end in bounds,prefixDecodesUtf8=valid,containsPadding=0 in prefix))
 summary=dict(calls=len(rows),allPrefixTokensExactlyMatchTrueSource=True,startInsideCharacter=sum(not x['startAtUnicodeBoundary'] for x in rows),endInsideCharacter=sum(not x['endAtUnicodeBoundary'] for x in rows),prefixDoesNotDecodeUtf8=sum(not x['prefixDecodesUtf8'] for x in rows),prefixContainsPadding=sum(x['containsPadding'] for x in rows),traceSha256=sha(trace),trainIndexSha256=sha(folder/'multiview/train.index.json'))
 models[name]=dict(summary=summary,rows=rows);print(name,json.dumps(summary),flush=True)
(E/'rollout-character-boundaries.json').write_text(json.dumps(dict(auditorSha256=sha(pathlib.Path(__file__)),models=models,actualTrainOnly=True,additionalOptimizerUpdates=0,noLearningConditionChanged=True,interpretation='Boundary rates diagnose actual self-negative prefixes, not all positive windows or free-generation meaning. The sample is every recorded rollout in the stated traces; Round31 scope is actual2000 only. Valid source-wide UTF8 does not guarantee a fixed token crop is character-aligned.'),indent=2)+'\n')
