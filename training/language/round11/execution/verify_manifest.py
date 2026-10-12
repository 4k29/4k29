"""Verify persisted execution artifacts and referenced immutable source bytes."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'execution/artifact-manifest.json').read_text())
for row in manifest['files']:
 p=ROOT/row['path']
 assert p.stat().st_size==row['bytes'],row['path']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
assert manifest['actualCompletedUpdates']==1000 and manifest['remainingUpdates']==9000 and not manifest['completedRun']
print(json.dumps(dict(verifiedFiles=len(manifest['files']),actualCompletedUpdates=1000,completedRun=False)))
