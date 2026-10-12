"""Verify persisted execution artifacts and referenced immutable source bytes."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'execution/artifact-manifest.json').read_text())
for row in manifest['files']:
 p=ROOT/row['path']
 assert p.stat().st_size==row['bytes'],row['path']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
result=json.loads((ROOT/'continue-10000/result.json').read_text())
assert manifest['actualCompletedUpdates']==result['completedSteps']
assert manifest['remainingUpdates']==manifest['requestedUpdates']-manifest['actualCompletedUpdates']
assert manifest['completedRun']==result['completedRun']==(manifest['remainingUpdates']==0)
print(json.dumps(dict(verifiedFiles=len(manifest['files']),actualCompletedUpdates=manifest['actualCompletedUpdates'],completedRun=manifest['completedRun'])))
