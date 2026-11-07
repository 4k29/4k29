"""Prove only daily-human corpus mass changes; no optimizer updates."""
import pathlib,hashlib,json
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=read(R/'policy.json');q=read(C/'policy.json')
for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py']:assert sha(R/n)==sha(C/n)==p['codeHashes'][n],n
for k in ['sourceHashes','parentCheckpointSha256','parentManifestSha256','seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','sequenceUnlikelihood','meaningGatePolicySha256']:assert p[k]==q[k],k
assert p['genreSampling']['human-chat']==.1 and set(p['genreSampling'])==set(q['genreSampling'])|{'human-chat'}
for k,v in q['genreSampling'].items():assert abs(p['genreSampling'][k]-.9*v)<1e-15
assert abs(sum(p['genreSampling'].values())-1)<1e-15
assert read(R/'multiview/data.json')['originalPreparedDataSha256']==sha(C/'multiview/data.json')
s=read(R/'sources/manifest.json');assert s['sourcePolicySha256']==sha(R/'source-policy.json');assert not s['reservedTestTokenizedOrModelEvaluated'];assert s['documentsSha256']==sha(R/'sources/documents.jsonl')==p['newSourceDocumentsSha256'];assert sha(R/'sources/manifest.json')==p['newSourceManifestSha256']
assert read(R/'execution/data-preflight.json')['allNewLabelsCoveredExactlyOnce']
record=dict(scientificControl='round25',oneChangedFactor='Human everyday-conversation TRAIN mass0→0.10; old relative masses preserved',coreLearningCodeExactlyIdentical=True,modelTokenizerObjectiveLrSeedAndValidationUnchanged=True,newTrainDialogues=s['admittedUnits'],humanRawTestHashesForHygieneOnly=True,testTokenizedOrModelEvaluated=False,noHumanDevTrainingTargets=True,sourcePolicySha256=sha(R/'source-policy.json'),policySha256=sha(R/'policy.json'),actualExperimentalUpdates=0,controlManifestSha256=sha(C/'execution/artifact-manifest.json'))
(R/'execution/single-factor-audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record))

for n in ["data.json","train.index.json","train.tokens.bin","tokenizer.json","validation.index.json","validation.tokens.bin"]:assert sha(R/"multiview"/n)==sha(R.parent/"round28/multiview"/n),n
