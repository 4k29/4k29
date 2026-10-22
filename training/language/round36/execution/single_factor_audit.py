"""Prove exact coefficient-only change and positive data equality before any update."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round35';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for dirname in ['multiview','sources','prospective-daily-source']:
 for p in sorted((P/dirname).rglob('*')):
  if p.is_file()and '__pycache__'not in p.parts:
   rel=p.relative_to(P);assert sha(p)==sha(R/rel),str(rel);rows.append(dict(path=str(rel),sha256=sha(p),bytes=p.stat().st_size))
core=['batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py','utterance_end_objective.py','human-turn-token-boundaries.json','source-policy.json']
for n in core:assert sha(P/n)==sha(R/n),n
old,new=read(P/'policy.json'),read(R/'policy.json')
for k in ['sourceHashes','genreSampling','learningRate','seed','views','validationViews','unlikelihood','sequenceUnlikelihood','humanNegativePrefix','parentCheckpointSha256','parentManifestSha256','parentOptimizerUpdates','parentLatestWeightLineageUpdates','preparedPolicySha256']:assert old[k]==new[k],k
x,y=old['humanUtteranceEndEos'].copy(),new['humanUtteranceEndEos'].copy();assert x.pop('coefficient')==1.0 and y.pop('coefficient')==.3 and x==y
assert old['supplementaryEverydayDevelopment']['additionalPracticalAdoptionGuard']==new['supplementaryEverydayDevelopment']['additionalPracticalAdoptionGuard']
s=(R/'train.py').read_text().replace("policy['humanUtteranceEndEos']['coefficient']==0.3","policy['humanUtteranceEndEos']['coefficient']==1.0").replace('same raw targets + 0.3 EOS auxiliary','same raw targets + 1.0 EOS auxiliary');assert s==(P/'train.py').read_text(),'Trainer differs beyond the declared coefficient guard/description'
t=(R/'fixed-source-mrmp-dev/evaluate.py').read_text();assert "R.parent/'round35/continue-10000/model.js'"in t and "round34/continue-10000/model.js"not in t
out=dict(actualOptimizerUpdates=0,scientificComparator='round35',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='EOS auxiliary coefficient1.0 to0.3 only',oldCoefficient=1.0,newCoefficient=.3,allPositiveDataByteidentical=rows,unchangedCoreFiles=core,trainerReversePatchExactlyEqualsControl=True,originalGoldTargetsAndEligibilityAndNormalizationUnchanged=True,negativePrefixPolicyAndAllOtherObjectivesLrSeedViewsAndInitialStateUnchanged=True,strictGatesSelectorAndPracticalGuardUnchanged=True,fixedSourceEvaluatorAllowlistProspectivelyCorrect=True,noModelForwardOrOptimizer=True)
(R/'execution/single-factor-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Coefficient-only exact reverse patch and',len(rows),'positive files verified; actual optimizer updates0')
