"""Independent exact single-factor and full TRAIN byte/coverage audit, zero updates."""
import pathlib,json,hashlib,collections,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=read(R/'policy.json');q=read(C/'policy.json')
for n in q['codeHashes']:
 assert sha(R/n)==p['codeHashes'][n]
 if n!='sequence_objective.py':assert sha(R/n)==sha(C/n)
expected=(C/'sequence_objective.py').read_text().replace('            model.train(was_training)','            model.eval()  # Negative scoring matches rollout mode; gradients remain enabled.')
assert (R/'sequence_objective.py').read_text()==expected
for k in ['sourceHashes','parentCheckpointSha256','parentManifestSha256','seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','genreSampling','preparedPolicySha256','newSourceManifestSha256','newSourceDocumentsSha256','meaningGatePolicySha256']:assert p[k]==q[k],k
s=dict(p['sequenceUnlikelihood']);assert s.pop('negativeScoringMode')=='eval, gradients enabled, restore caller mode in finally' and s==q['sequenceUnlikelihood']
for n in ['tokenizer.json','train.index.json','train.tokens.bin','validation.index.json','validation.tokens.bin','data.json']:assert sha(R/'multiview'/n)==sha(C/'multiview'/n),n
index=read(R/'multiview/train.index.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x) for x in read(R/'multiview/tokenizer.json')['bytes']];rows=collections.defaultdict(list)
for row in index['rows']:rows[row['unit']].append(row)
for d in index['documents']:
 tokens=values[d['offset']:d['offset']+d['length']];assert tokens[0]==1 and tokens[-1]==2 and len(tokens)>2;raw=b''.join(vocab[int(t)] for t in tokens[1:-1]);assert len(raw)==d['utf8Bytes'] and hashlib.sha256(raw).hexdigest()==d['textSha256'];assert raw.decode().strip();covered=1
 for row in rows[d['id']]:assert row['offset']==d['offset']+row['start'] and row['start']+row['prefixLength']==covered and row['length']==row['end']-row['start']<=257;covered=row['end']
 assert covered==len(tokens)
a=dict(scientificControl='round25',oneChangedFactor='Self-negative rescoring dropout mode train to eval',allOtherLearningPolicyUnchanged=True,allOtherCoreCodeByteidenticalToControl=True,allTrainDataByteidentical=True,allTrainLabelsCoveredExactlyOnce=True,noEmptyTargets=True,allRawTrainValidUtf8=True,validationAndTokenizerByteidentical=True,actualExperimentalUpdates=0,trainingDocuments=len(index['documents']),trainingRows=len(index['rows']))
(E/'single-factor-audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a))
