"""Recheck cached data-only addition without model forward/backward or TEST encoding."""
import pathlib,json,hashlib,argparse,array,collections
p=argparse.ArgumentParser();p.add_argument('--prepared',type=pathlib.Path,required=True);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--sources',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=read(a.base/'train.index.json');n=read(a.prepared/'train.index.json');data=read(a.prepared/'data.json');tok=read(a.prepared/'tokenizer.json');vocab=[bytes.fromhex(x) for x in tok['bytes']]
for f in ['validation.index.json','validation.tokens.bin','tokenizer.json']:assert sha(a.prepared/f)==sha(a.base/f),f
assert n['rows'][:len(b['rows'])]==b['rows'] and n['documents'][:len(b['documents'])]==b['documents']
oldbytes=(a.base/'train.tokens.bin').read_bytes();newbytes=(a.prepared/'train.tokens.bin').read_bytes();assert newbytes[:len(oldbytes)]==oldbytes
assert hashlib.sha256(newbytes).hexdigest()==n['tokensSha256']
values=array.array('I');values.frombytes(newbytes);assert values.itemsize==4
units=[json.loads(l) for l in (a.sources/'documents.jsonl').read_text().splitlines()];assert len(units)==528 and all(x['partition']=='train' for x in units);source={x['unitKey']:x for x in units};assert len(source)==528
newdocs=n['documents'][len(b['documents']):];newrows=n['rows'][len(b['rows']):];byunit=collections.defaultdict(list)
for row in newrows:byunit[row['unit']].append(row)
seen=set()
for doc in newdocs:
 uid=doc['id'];unit,variant=uid.rsplit(':view:',1);s=source[unit];assert doc['variant']==int(variant) and doc['site']=='wiki2019';assert uid not in seen;seen.add(uid)
 full=values[doc['offset']:doc['offset']+doc['length']];assert full[0]==1 and full[-1]==2 and all(6<=i<len(vocab) for i in full[1:-1]);raw=b''.join(vocab[i] for i in full[1:-1]);assert raw==s['text'].encode('utf8') and hashlib.sha256(raw).hexdigest()==doc['textSha256']==s['textSha256']
 targets=[]
 for row in byunit[uid]:
  assert row['site']=='wiki2019' and row['variant']==int(variant) and row['length']<=257
  targets.extend(values[row['offset']+row['prefixLength']:row['offset']+row['length']])
 assert targets==list(full[1:]),uid
assert len(newdocs)==len(seen)==1584 and set(byunit)==seen
assert {x['id'] for x in data['addedTrainViews']}==seen
manifest=read(a.sources/'manifest.json');assert data['newSourceManifestSha256']==sha(a.sources/'manifest.json') and data['newSourceDocumentsSha256']==sha(a.sources/'documents.jsonl')
record=dict(oldTrainRowsAndDocumentsExactlyPreserved=True,oldTrainTokenPrefixExactlyPreserved=True,validationAndTokenizerByteIdentical=True,newTrainUnits=528,newViews=1584,newRows=len(newrows),allNewViewsExactlyOriginalUtf8=True,eachMaskedTargetExactlyOnce=True,onlyDeclaredTrainUnitsEncoded=True,reservedAndTestEncoded=False,additionalOptimizerUpdates=0,newManifestSha256=sha(a.sources/'manifest.json'),newIndexSha256=sha(a.prepared/'train.index.json'))
a.out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
