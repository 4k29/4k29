"""Freeze all actual learning inputs before any optimizer update."""
import pathlib,json,hashlib,os,datetime
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';E=R/'execution';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
assert not (R/'continue-10000/checkpoint.pt').exists() and not (E/'train.log').exists();assert read(E/'single-factor-audit.json')['allOtherLearningPolicyUnchanged']
paths=set()
for f in R.rglob('*'):
 if not f.is_file() or '__pycache__' in f.parts or 'continue-10000' in f.parts or f.name in ['source-manifest.json','frozen-preflight.json','preflight-runtime.json','initial-development-preflight.json'] or f.suffix=='.log' or f.name in ['README.md','REPRODUCTION.md']:continue
 paths.add(str(f.relative_to(R)))
for row in read(C/'source-manifest.json')['files']:
 f=(C/row['path']).resolve();assert f.is_file();paths.add(os.path.relpath(f,R))
for n in ['../round25/policy.json','../round25/train.py','../round25/execution/artifact-manifest.json','../round25/execution/adoption.json','../round25/continue-10000/model.js','../round25/continue-10000/checkpoint.pt','../round25/continue-10000/metrics.json','../round28/prospective-daily-source/human-source-acquisition.json.gz','../round28/prospective-daily-source/prospective-speaker-folds.json','../round29/execution/evaluation-reference-exposure.json','../round31/RESULTS.md','../round31/execution/artifact-manifest.json','../round31/execution/evaluation-reference-exposure.json','../round24/next-candidate-drafts/adoption-policy.json']:paths.add(n)
files=[dict(path=n,sha256=sha(R/n),bytes=(R/n).stat().st_size) for n in sorted(paths)]
(R/'source-manifest.json').write_text(json.dumps(dict(files=files,actualExperimentalUpdatesAtFreeze=0,scientificControl='round25',oneLearningFactor='Self-negative rescoring dropout mode train to eval'),indent=2)+'\n')
(E/'frozen-preflight.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualExperimentalOptimizerUpdates=0,requestedUpdates=10000,trainingCompleted=False,policySha256=sha(R/'policy.json'),sourceManifestSha256=sha(R/'source-manifest.json')),indent=2)+'\n');print('Frozen',len(files),'inputs')
