import pathlib,json,hashlib,os
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round28';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
assert not (R/'continue-10000/checkpoint.pt').exists()
p=read(R/'policy.json');p['codeHashes']={n:sha(R/n)for n in ['train.py','batching.py','initialization.py','objective.py','sequence_objective.py','rollout_trace.py','prefix_selection.py']};(R/'policy.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
paths=set()
for f in R.rglob('*'):
 if f.is_file() and '__pycache__'not in f.parts and 'continue-10000'not in f.parts and f.name not in ['source-manifest.json','preflight-runtime.json','initial-development-preflight.json'] and f.suffix!='.log' and f.name not in ['README.md','REPRODUCTION.md']:paths.add(str(f.relative_to(R)))
for x in read(C/'source-manifest.json')['files']:paths.add(os.path.relpath((C/x['path']).resolve(),R))
for n in ['execution/artifact-manifest.json','continue-10000/checkpoint.pt','continue-10000/model.js','continue-10000/metrics.json','execution/daily-human-new-likelihood.json']:paths.add('../round28/'+n)
for n in ['execution/artifact-manifest.json','execution/adoption-decision.json','execution/final-assessment.json','execution/new-manual.json','execution/sampler-replay.json','continue-10000/checkpoint.pt','continue-10000/checkpoint-0.pt','continue-10000/training-rollouts.jsonl','continue-10000/model.js','continue-10000/metrics.json','RESULTS.md']:paths.add('../round33/'+n)
files=[dict(path=n,sha256=sha(R/n),bytes=(R/n).stat().st_size)for n in sorted(paths)]
(R/'source-manifest.json').write_text(json.dumps(dict(files=files,actualExperimentalUpdatesAtFreeze=0,scientificControl='round33',initializationParent='round28',adoptionAnchor='round25',oneLearningFactor='Human self-negative prefix end policy only'),indent=2)+'\n');print('Frozen inputs',len(files),'actual new optimizer updates0')
