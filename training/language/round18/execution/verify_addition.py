"""Independent new-source byte and window audit; no optimizer or generation."""
import pathlib,json,hashlib,sys,numpy as np
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
i=read(R/'multiview/train.index.json');tok=read(R/'multiview/tokenizer.json');v=[bytes.fromhex(x) for x in tok['bytes']];x=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');docs=[json.loads(l) for l in (R/'sources/documents.jsonl').read_text().splitlines()];source={d['id']:d for d in docs if d['partition']=='train'};reserved={d['id'] for d in docs if d['partition']=='reserved'}
assert not any(d['sourceDocument'] in reserved for d in i['documents'])
rows=[]
for d in i['documents']:
 if d['sourceDocument'] not in source:continue
 text=source[d['sourceDocument']]['text'];t=x[d['offset']:d['offset']+d['length']]
 assert b''.join(v[a] for a in t[1:-1])==text.encode()
 windows=[r for r in i['rows'] if r['unit']==d['id']];covered=[]
 for r in windows:covered.extend(x[r['offset']+r['prefixLength']:r['offset']+r['length']].tolist())
 assert covered==t[1:].tolist()
 rows.append({'id':d['id'],'variant':d['variant'],'textSha256':hashlib.sha256(text.encode()).hexdigest(),'windows':len(windows),'originalBytesExact':True,'maskedTargetsExactlyOnce':True})
assert len(rows)==3*len(source)==30
record={'addedViews':rows,'reservedSourcesEncoded':False,'testEncoded':False,'tokenizerSha256':sha(R/'multiview/tokenizer.json'),'newSourceDocumentsSha256':sha(R/'sources/documents.jsonl'),'additionalOptimizerUpdates':0}
(R/'execution/addition-audit.json').write_text(json.dumps(record,indent=2)+'\n');print('30/30 added views: exact original bytes, masked targets once; reserved excluded')
