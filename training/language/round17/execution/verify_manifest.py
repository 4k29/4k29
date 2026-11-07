import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[1];a=json.loads((R/'execution/artifact-manifest.json').read_text())
assert a['actualCompletedUpdates']==10000
for row in a['files']+a['inputs']:
 p=R/row['path'];assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
print('SHA and sizes verified',len(a['files']),'files;',a['actualCompletedUpdates'],'actual updates')
