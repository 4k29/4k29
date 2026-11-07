"""Inventory actual finished experiment and all immutable input references."""
import pathlib,json,hashlib,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((ROOT/'continue-10000/result.json').read_text());a=json.loads((ROOT/'execution/optimizer-audit.json').read_text());c=json.loads((ROOT/'execution/comparison.json').read_text())
assert r['completedRun'] and r['completedSteps']==a['actualCompletedUpdates']==c['actualCompletedUpdates']==10000
manifest=ROOT/'execution/artifact-manifest.json'
paths={p.resolve() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest}
for row in json.loads((ROOT/'source-manifest.json').read_text())['files']:paths.add((ROOT/row['path']).resolve())
for p in [ROOT.parent/'round11/execution/artifact-manifest.json',ROOT.parent/'round11/continue-10000/model.js',ROOT.parent/'round11/execution/new-manual.json',ROOT.parent/'round11/execution/new-validation.json',ROOT.parent/'round10/word-512-continue-10000/checkpoint.pt',ROOT.parent/'round10/full-meaning-policy.json',ROOT.parent/'round10/evaluate.py',ROOT.parent/'round10/evaluate_js.mjs',ROOT.parent/'round10/review.py']:paths.add(p.resolve())
paths.add((ROOT.parent/'round13/THREE_ROUND_POLICY.json').resolve())
paths.add((ROOT.parent/'round13/execution/build_round_report.py').resolve())
paths.add((ROOT.parent/'round13/execution/build_cohort_report.py').resolve())
paths.add((ROOT.parent/'round13/THREE_ROUND_RESULTS.md').resolve())
paths.add((ROOT.parent/'round13/COHORT_COMPARISON.json').resolve())
paths.add((ROOT.parent/'round12/execution/train-development-gap.json').resolve())
record=dict(actualCompletedUpdates=10000,selectedStep=r['bestStep'],completedRun=True,baseGitCommit='6995194d5a6cb5b063c36b6269813f2f3260c662',files=[dict(path=os.path.relpath(p,ROOT),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(paths)])
manifest.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(verifiedFiles=len(paths),actualCompletedUpdates=10000)))
