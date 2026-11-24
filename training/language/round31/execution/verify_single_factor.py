"""Independent TRAIN bytes, exact positive coverage and one-condition audit."""
import pathlib,json,hashlib,collections,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=read(R/'policy.json');q=read(C/'policy.json')
for n in q['codeHashes']:assert sha(R/n)==sha(C/n)==p['codeHashes'][n],n
for k in ['sourceHashes','parentCheckpointSha256','parentManifestSha256','seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','genreSampling','preparedPolicySha256','sequenceUnlikelihood','newSourceManifestSha256','newSourceDocumentsSha256','meaningGatePolicySha256']:assert p[k]==q[k],k
for n in ['tokenizer.json','validation.index.json','validation.tokens.bin']:assert sha(R/'multiview'/n)==sha(C/'multiview'/n),n
assert sha(R/'dedup-policy.json')==p['dataTransformationPolicySha256']
a=read(E/'suffix-transformation.json');changes={d['id']:d for d in a['changes']};old=read(C/'multiview/train.index.json');new=read(R/'multiview/train.index.json');ov=np.memmap(C/'multiview/train.tokens.bin',dtype='<u4',mode='r');nv=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x) for x in read(R/'multiview/tokenizer.json')['bytes']];before={d['id']:d for d in old['documents']};rows=collections.defaultdict(list)
for row in new['rows']:rows[row['unit']].append(row)
seen=set()
for d in new['documents']:
 seen.add(d['id']);b=before[d['id']];key=d['id'].rsplit(':view:',1)[0]+':view:0';t=nv[d['offset']:d['offset']+d['length']];orig=ov[b['offset']:b['offset']+b['length']];raw=b''.join(vocab[int(x)] for x in t[1:-1]);oldraw=b''.join(vocab[int(x)] for x in orig[1:-1]);assert t[0]==1 and t[-1]==2 and all(4<=int(x)<len(vocab) for x in t[1:-1]);assert len(raw)==d['utf8Bytes'] and hashlib.sha256(raw).hexdigest()==d['textSha256'];assert raw.decode().strip()
 if key in changes:assert oldraw.startswith(raw) and len(raw)<len(oldraw)
 else:assert np.array_equal(t,orig) and d['textSha256']==b['textSha256']
 covered=1
 for row in rows[d['id']]:assert row['offset']==d['offset']+row['start'] and row['start']+row['prefixLength']==covered and row['length']==row['end']-row['start']<=257;covered=row['end']
 assert covered==len(t)
for key in before.keys()-seen:assert changes[key.rsplit(':view:',1)[0]+':view:0']['emptyUnitDropped']
report=dict(scientificControl='round25',oneChangedFactor='TRAIN duplicate suffix cleanup',allOtherLearningPolicyUnchanged=True,coreTrainingCodeByteidenticalToControl=True,unchangedUnitTokensExact=True,allChangedBytesAreSuffixDeletion=True,allTrainLabelsCoveredExactlyOnce=True,noEmptyTargets=True,allRawTrainValidUtf8=True,validationAndTokenizerByteidentical=True,actualExperimentalUpdates=0,trainingDocuments=len(new['documents']),trainingRows=len(new['rows']),transformationSha256=sha(E/'suffix-transformation.json'))
(E/'single-factor-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
