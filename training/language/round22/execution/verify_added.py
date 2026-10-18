"""Independent recovered-original bytes, fold, view and mask audit; zero updates."""
import pathlib,json,hashlib,numpy as np,sys
R=pathlib.Path(__file__).resolve().parents[1];B=R.parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
docs={d['id']:d for d in [json.loads(l) for l in (R/'sources/source-documents.jsonl').read_text().splitlines()]};parts={k:d['partition'] for k,d in docs.items()};new=[json.loads(l) for l in (R/'sources/documents.jsonl').read_text().splitlines()];idx=read(R/'multiview/train.index.json');base=read(B/'round19/multiview/train.index.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x) for x in read(R/'multiview/tokenizer.json')['bytes']];checked=0
assert idx['rows'][:len(base['rows'])]==base['rows'] and idx['documents'][:len(base['documents'])]==base['documents']
lookup={d['id']:d for d in idx['documents']};assert len(lookup)==len(idx['documents'])
for d in new:
 original=docs[d['originalDocument']];assert parts[original['id']]=='train' and int(hashlib.sha256(original['url'].encode()).hexdigest(),16)%10!=0;assert original['htmlSha256']==sha(R/'sources/html'/(hashlib.sha256(original['url'].encode()).hexdigest()[:16]+'.html')); assert d['text']=='\n'.join(original['text'].splitlines()[d['startLine']:d['endLine']]);assert d['textSha256']==hashlib.sha256(d['text'].encode()).hexdigest()
 for view in range(3):
  key=d['unitKey']+':view:'+str(view);m=lookup[key];ts=values[m['offset']:m['offset']+m['length']];assert b''.join(vocab[t] for t in ts[1:-1])==d['text'].encode();covered=[]
  for row in idx['rows']:
   if row['unit']==key:covered.extend(values[row['offset']+row['prefixLength']:row['offset']+row['length']].tolist())
  assert covered==ts[1:].tolist();checked+=1
assert checked==len(new)*3
record={'addedUnits':len(new),'addedCharacters':sum(len(d['text']) for d in new),'viewsVerified':checked,'allOriginalTextExact':True,'allOriginalSourcePartitionsTrain':True,'originalRowsAndDocumentsPreservedExactly':True,'maskedTargetsExactlyOnce':True,'uniqueViewIds':True,'sourceDocumentsSha256':sha(R/'sources/documents.jsonl'),'additionalOptimizerUpdates':0};(R/'execution/addition-integrity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
