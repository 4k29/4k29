import pathlib,json,hashlib,numpy as np
R=pathlib.Path('/workspace/4k29/training/language/round38');P=R.parent/'round37';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
old=read(P/'sources/manifest.json');add=read(R/'added-human-source/manifest.json');combined=read(R/'sources/manifest.json')
for k in list(combined):
 if k not in {'sourceRepository','sourceRepositories','admittedUnits','admittedCharacters','admittedUtf8Bytes','admittedUtterances','documentsSha256','priorExistingSourceDocumentsSha256','priorExistingSourcePrefixBytesExactlyPreserved','newAdditionManifestSha256','sourceSpeakerDisjointnessClaim','sourceTextRewritten'}:combined.pop(k)
combined['existingRealPersonaManifest']=old;combined['addedJmrdManifest']=add;write(R/'sources/manifest.json',combined)
f=read(P/'human-turn-token-boundaries.json');idx=read(R/'multiview/train.index.json');vals=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x)for x in read(R/'multiview/tokenizer.json')['bytes']];docs={d['originalDocument']:d for d in map(json.loads,(R/'added-human-source/documents.jsonl').read_text().splitlines())}
counts={0:0,1:0,2:0}
for d in idx['documents']:
 if d['sourceDocument']not in docs:continue
 text=docs[d['sourceDocument']]['text'];ends=set();pos=0
 for t in text.split('\n')[:-1]:pos+=len(t.encode())+1;ends.add(pos)
 tokens=vals[d['offset']:d['offset']+d['length']];offset=0;bounds=[]
 for j,t in enumerate(tokens[1:-1],1):
  offset+=len(vocab[int(t)])
  if offset in ends:bounds.append(j+1)
 assert offset==len(text.encode());assert d['id']not in f['boundariesByUnit'];f['boundariesByUnit'][d['id']]=bounds;counts[d['variant']]+=len(bounds)
for key,path in [('sourceDocumentsSha256','sources/documents.jsonl'),('trainIndexSha256','multiview/train.index.json'),('trainTokensSha256','multiview/train.tokens.bin'),('tokenizerSha256','multiview/tokenizer.json')]:f[key]=sha(R/path)
assert all(f['boundariesByUnit'][k]==v for k,v in read(P/'human-turn-token-boundaries.json')['boundariesByUnit'].items());write(R/'human-turn-token-boundaries.json',f)
p=read(R/'policy.json');p['newSourceManifestSha256']=sha(R/'sources/manifest.json')
for key in ['humanNegativePrefix','humanUtteranceEndEos']:p[key]['featureMapSha256']=sha(R/'human-turn-token-boundaries.json')
write(R/'policy.json',p)
g=read(R/'execution/human-train-gap-plan.json')
for k,v in list(g.items()):
 if k.endswith('Sha256'):
  for name in ['sources/documents.jsonl','multiview/train.index.json','multiview/train.tokens.bin']:
   if v==sha(P/name):g[k]=sha(R/name)
g['sampleScope']='Same inherited legacy RealPersona TRAIN99; not new JMRD or whole TRAIN';write(R/'execution/human-train-gap-plan.json',g)
write(R/'execution/appended-boundary-audit.json',dict(oldBoundaryListsExactlyPreserved=True,addedUnits=len(docs),addedViewBoundaryCounts=counts,onlyExistingExactTokenEnds=True,modelUpdates=0))
print('boundaries complete',counts)
