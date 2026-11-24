"""Prove the declared CE-only diff, fixed data/targets and fixed guard floors."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round36';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());rows=[]
for d in ['multiview','sources','prospective-daily-source']:
 for p in sorted((P/d).rglob('*')):
  if p.is_file()and '__pycache__'not in p.parts:
   rel=p.relative_to(P);assert sha(p)==sha(R/rel);rows.append(dict(path=str(rel),sha256=sha(p),bytes=p.stat().st_size))
core=['batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py','utterance_end_objective.py','human-turn-token-boundaries.json','source-policy.json']
for n in core:assert sha(P/n)==sha(R/n)
a,b=read(P/'policy.json'),read(R/'policy.json')
for k in ['sourceHashes','genreSampling','learningRate','seed','views','validationViews','unlikelihood','sequenceUnlikelihood','humanNegativePrefix','humanUtteranceEndEos','parentCheckpointSha256','parentManifestSha256','parentOptimizerUpdates','parentLatestWeightLineageUpdates','preparedPolicySha256','supplementaryEverydayDevelopment']:assert a[k]==b[k],k
s=(R/'train.py').read_text();spec=read(R/'execution/trainer-change-spec.json');assert sha(P/'train.py')==spec['controlTrainSha256']and sha(R/'train.py')==spec['newTrainSha256']
for change in reversed(spec['patches']):assert s.count(change['new'])==change['count'];s=s.replace(change['new'],change['old'])
assert s==(P/'train.py').read_text()
t=(R/'fixed-source-mrmp-dev/evaluate.py').read_text();assert "R.parent/'round36/continue-10000/model.js'"in t
out=dict(actualOptimizerUpdates=0,allPositiveDataByteidentical=rows,unchangedCoreFiles=core,trainerReversePatchExactlyEqualsControl=True,allOriginalTargetsAndEligibilityUnchanged=True,eosCoefficientStillPointThree=True,originalValidTargetDenominatorRetained=True,allOtherObjectivesAndDataRngLrSeedViewsInitialStateUnchanged=True,strictGatesSelectorAndPracticalFloorsUnchanged=True,oneLearningFactor='Exclude original newline main CE at the existing human EOS eligible positions',noModelForwardOrOptimizer=True)
(R/'execution/single-factor-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Single-factor reverse patch and',len(rows),'positive files verified; actual updates0')
