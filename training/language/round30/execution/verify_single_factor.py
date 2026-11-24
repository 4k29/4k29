"""Independent complete data identity and one-factor source audit; zero updates."""
import pathlib,json,hashlib,collections,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=read(R/'policy.json');q=read(C/'policy.json')
for n in q['codeHashes']:
 if n!='train.py':assert sha(R/n)==sha(C/n)==p['codeHashes'][n],n
old=(C/'train.py').read_text();new=(R/'train.py').read_text();assert new==old.replace('max_new_tokens=64,eos=2,window=64',"max_new_tokens=policy['sequenceUnlikelihood']['maxNewTokens'],eos=2,window=64")
for k in ['sourceHashes','parentCheckpointSha256','parentManifestSha256','seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','genreSampling','preparedPolicySha256','newSourceManifestSha256','newSourceDocumentsSha256','meaningGatePolicySha256']:assert p[k]==q[k],k
a=dict(p['sequenceUnlikelihood']);b=dict(q['sequenceUnlikelihood']);assert a.pop('maxNewTokens')==128 and b.pop('maxNewTokens')==64 and a==b
for n in ['data.json','train.index.json','train.tokens.bin','validation.index.json','validation.tokens.bin','tokenizer.json']:assert sha(R/'multiview'/n)==sha(C/'multiview'/n),n
v=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');i=read(R/'multiview/train.index.json');vocab=[bytes.fromhex(b) for b in read(R/'multiview/tokenizer.json')['bytes']];rows=collections.defaultdict(list)
for r in i['rows']:rows[r['unit']].append(r)
for d in i['documents']:
 t=v[d['offset']:d['offset']+d['length']];assert t[0]==1 and t[-1]==2 and all(4<=int(x)<len(vocab) for x in t[1:-1]);raw=b''.join(vocab[int(x)] for x in t[1:-1]);raw.decode('utf8');assert len(raw)==d['utf8Bytes'];assert sha(C/'multiview/tokenizer.json')==read(R/'multiview/data.json')['tokenizerSha256'];covered=1
 for r in rows[d['id']]:
  assert r['offset']==d['offset']+r['start'] and r['length']==r['end']-r['start']<=257;assert r['start']+r['prefixLength']==covered;covered=r['end']
 assert covered==len(t)
report=dict(scientificControl='round25',oneChangedFactor='self-generated negative maxNewTokens64→128',allPositiveDataAndTokenizersByteidentical=True,allTrainLabelsCoveredExactlyOnce=True,allRawTrainDocumentsValidUtf8=True,trainingDocuments=len(i['documents']),trainingRows=len(i['rows']),contextCapacity=256,longestPrefixPlusRollout=160,allOtherLearningPolicyUnchanged=True,actualExperimentalUpdates=0,policySha256=sha(R/'policy.json'))
(E/'single-factor-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
