"""Actual positive TRAIN bytes and repeated statistical-course lines; no heldout."""
import pathlib,json,hashlib,collections,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest();i=read(R/'multiview/train.index.json');v=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x) for x in read(R/'multiview/tokenizer.json')['bytes']];matches=[];stat=[];lines=collections.defaultdict(list);scanned=0
for d in i['documents']:
 if d['variant']!=0:continue
 raw=b''.join(vocab[int(t)] for t in v[d['offset']:d['offset']+d['length']]);assert sha(raw)==d['textSha256'];text=raw.decode();scanned+=1;n=text.count('エーアイキャット')
 if n:matches.append(dict(source=d['sourceDocument'],site=d['site'],unit=d['id'],occurrences=n,rawSha256=sha(raw)))
 if d['site']=='stat':
  stat.append(d)
  for line in text.splitlines():
   if len(line)>=20:lines[line].append(d['sourceDocument'])
write=lambda n,x:(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
write('persona-string-training-audit.json',dict(needle='エーアイキャット',partition='actual-positive-TRAIN-only',canonicalDocumentsScanned=scanned,matches=matches,notProofOfCausalAttribution=True,additionalOptimizerUpdates=0))
common=[dict(line=s,occurrences=len(ids),distinctSources=len(set(ids))) for s,ids in lines.items() if len(set(ids))>=3];common.sort(key=lambda x:(-x['distinctSources'],-x['occurrences'],x['line']))
write('stat-shared-line-diagnostic.json',dict(canonicalStatUnits=len(stat),statSources=len({d['sourceDocument'] for d in stat}),personaMatchedUnits=len(matches),personaMatchedSources=len({d['source'] for d in matches}),personaLiteralOccurrences=sum(d['occurrences'] for d in matches),commonLines=common,trainOnly=True,additionalOptimizerUpdates=0,causalEffectNotEstablished=True,notAllRepeatedLinesAreBoilerplate=True,policyNotChanged=True))
ids={d['source'] for d in matches};meta=[]
for line in (R.parent/'round10/documents.jsonl').open():
 d=json.loads(line)
 if d['id'] in ids:meta.append({k:d.get(k) for k in ['id','site','url','title','license','licenseUrl','policyUrl']})
assert len(meta)==len(ids)
write('persona-training-source-metadata.json',dict(trainSourceIds=sorted(ids),metadata=meta,onlyActualTrainMatchedDocumentsInspected=True));print(json.dumps(dict(canonicalTrainUnitsVerified=scanned,statUnits=len(stat),matchedSourceDocuments=len(ids),personaOccurrences=sum(d['occurrences'] for d in matches),sharedExactLines=len(common),additionalOptimizerUpdates=0)))
