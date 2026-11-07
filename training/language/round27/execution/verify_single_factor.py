"""Verify identical data/objective/optimizer policy; only FFN capacity changes."""
import hashlib, json, pathlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=R.parent/read(E/'creation-context.json')['scientificControl'];p=read(R/'policy.json');q=read(C/'policy.json')
unchanged=['batching.py','objective.py','sequence_objective.py','rollout_trace.py']
for name in unchanged:
 if (C/name).exists():assert sha(R/name)==sha(C/name)==p['codeHashes'][name],name
keys=['sourceHashes','parentCheckpointSha256','parentManifestSha256','seed','requestedUpdates','views','validationViews','learningRate','schedule','unlikelihood','sequenceUnlikelihood','meaningGatePolicySha256','genreSampling','preparedPolicySha256','sourceManifestReference','newSourceManifestSha256','newSourceDocumentsSha256']
for key in keys:assert p.get(key)==q.get(key),key
files=['data.json','train.index.json','train.tokens.bin','validation.index.json','validation.tokens.bin','tokenizer.json']
for name in files:assert sha(R/'multiview'/name)==sha(C/'multiview'/name),name
assert p['capacity']['oldHidden']==768 and p['capacity']['newHidden']==1536
assert p['capacity']['oldParameters']==4655808 and p['capacity']['newParameters']==7021248
assert p['capacity']['newCoordinateIndependentBiasCorrectionAge'] is False
old_model_sha=next(x['sha256'] for x in read(C/'source-manifest.json')['files'] if x['path']=='../model.py')
assert sha(R.parent/'model.py')==old_model_sha
assert not (R/'continue-10000/checkpoint.pt').exists(), 'Run only before experimental training'
assert not list(R.rglob('test.tokens.bin'))
for name in ['capacity.py','capacity_audit.py']:assert sha(R/name)==p['codeHashes'][name]
record=dict(scientificControl=C.name,oneChangedFactor='FFN hidden768→1536 only',identicalPreparedTrainValidationTokenizerBytes=True,identicalGenreSamplingObjectiveLearningRateSeedSchedule=True,unchangedLearningCode={n:sha(R/n) for n in unchanged if (R/n).exists()},changedCoreLearningFiles=['train.py','initialization.py'],capacityHelpers=['capacity.py','capacity_audit.py'],declaredInitializationPolicy=dict(oldCoordinateMoments='retain bitexact',newIncoming='own seeded random',newOutgoingAndMoments='zero',newCoordinatesAdamWTensorAge=10000),actualModelMomentVerification='Separate preflight-runtime and initial-equivalence audits; this script checks policy/data only',actualExperimentalOptimizerUpdates=0,noNewTrainSources=True,reservedTestEncoded=False,policySha256=sha(R/'policy.json'),controlManifestSha256=sha(C/'execution/artifact-manifest.json'),preparedDataHashes={n:sha(R/'multiview'/n) for n in files})
(E/'single-factor-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
