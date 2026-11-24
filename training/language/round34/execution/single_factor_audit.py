"""Prospective factor separation; no model forwards or optimizer."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round33';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
rows=[]
for dirname in ['multiview','sources','prospective-daily-source']:
 for p in sorted((P/dirname).rglob('*')):
  if p.is_file()and '__pycache__'not in p.parts:
   rel=p.relative_to(P);assert sha(p)==sha(R/rel);rows.append(dict(path=str(rel),sha256=sha(p),bytes=p.stat().st_size))
for n in ['batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','source-policy.json']:assert sha(P/n)==sha(R/n),n
a,b=read(P/'policy.json'),read(R/'policy.json')
for k in ['sourceHashes','genreSampling','learningRate','seed','views','validationViews','unlikelihood','parentCheckpointSha256','parentManifestSha256','parentOptimizerUpdates','parentLatestWeightLineageUpdates','preparedPolicySha256']:assert a[k]==b[k],k
x=a['sequenceUnlikelihood'].copy();y=b['sequenceUnlikelihood'].copy();x.pop('prefixSelection');y.pop('prefixSelection');assert x==y
s=(R/'train.py').read_text().replace('\nfrom prefix_selection import load_selector','')
line=next(x for x in s.splitlines()if x.strip().startswith('prefix_selector=load_selector('));s=s.replace(line+'\n','')
s=s.replace("            prefix_length=prefix_selector.length(rows[0],int(x[0,0]))\n            prefix=x[:1,:prefix_length]", "            prefix=x[:1,:min(policy['sequenceUnlikelihood']['prefixTokens'],rows[0]['length']-1)]")
assert s==(P/'train.py').read_text(),'Trainer differs beyond deterministic prefix selector'
assert sha(R/'human-turn-token-boundaries.json')==b['humanNegativePrefix']['featureMapSha256']=='835d6da37308c68c5a5bc4a61c727a6ee4d2978006890c21f0416345dc02dc56'
out=dict(actualOptimizerUpdates=0,scientificComparator='round33',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='Human negative prefix endpoint policy only',allPositiveDataByteidentical=rows,unchangedCoreFiles=['batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py'],trainerReversePatchExactlyEqualsControl=True,allObjectivesCoefficientsLrSeedViewsAndInitialStateUnchanged=True,shorterPrefixLengthPartOfTreatment=True,sourceMapSha256=sha(R/'human-turn-token-boundaries.json'),noModelForwardOrOptimizer=True)
(R/'execution/single-factor-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Single-factor verified; positive files',len(rows),'actual optimizer updates0')
