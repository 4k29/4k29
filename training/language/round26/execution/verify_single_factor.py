"""Verify corpus mixture is the only learning-factor change before actual updates."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p,q=read(R/'policy.json'),read(C/'policy.json')
for name in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py']:
 assert sha(R/name)==sha(C/name)==p['codeHashes'][name],name
for key in ['sourceHashes','parentCheckpointSha256','parentManifestSha256','seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','sequenceUnlikelihood','meaningGatePolicySha256']:
 assert p[key]==q[key],key
assert p['genreSampling']['wiki2019']==.1
for key,value in q['genreSampling'].items():assert abs(p['genreSampling'][key]-.9*value)<1e-15
D=R.parent/'round24/next-candidate-drafts/wiki-addition/source-cache/quality-sources';docs=[json.loads(l) for l in (D/'source-documents.jsonl').read_text().splitlines()];reserved={x['id'] for x in docs if x['partition']=='reserved'};assert len(reserved)==16
for x in docs:
 expected='reserved' if int(hashlib.sha256(('wiki2019:'+str(x['pageid'])).encode()).hexdigest(),16)%10==0 else 'train'
 assert x['partition']==expected and x['revisionTimestamp']<='2019-12-31T23:59:59Z'
units=[json.loads(l) for l in (D/'documents.jsonl').read_text().splitlines()];assert len(units)==528 and len({x['originalDocument'] for x in units})==115
assert all(x['partition']=='train' and x['originalDocument'] not in reserved for x in units)
assert read(R/'multiview/data.json')['originalPreparedDataSha256']==sha(C/'multiview/data.json')
record=dict(scientificControl='round25',coreLearningCodeExactlyIdentical=True,modelTokenizerObjectiveLrSeedAndValidationUnchanged=True,oneChangedFactor='wiki2019 corpus mixture0→0.1; old relative masses preserved',reservedDocuments=16,allCanonicalPageIdFoldsVerified=True,allRevisionsPre2020=True,newTrainUnits=528,newTrainDocuments=115,noReservedUnitEncoded=True,actualExperimentalUpdates=0,policySha256=sha(R/'policy.json'),controlManifestSha256=sha(C/'execution/artifact-manifest.json'))
(E/'single-factor-audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record))
