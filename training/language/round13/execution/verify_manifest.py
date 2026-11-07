import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'execution/artifact-manifest.json').read_text())
for row in m['files']:
 p=ROOT/row['path'];assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
print(json.dumps(dict(verifiedFiles=len(m['files']),actualCompletedUpdates=m['actualCompletedUpdates'],completedRun=m['completedRun'])))
