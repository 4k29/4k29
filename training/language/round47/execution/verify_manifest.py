import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[1];a=json.loads((R/'execution/artifact-manifest.json').read_text())
assert a['actualCompletedUpdates']==10000
for row in a['files']+a['inputs']:
 p=R/row['path'];assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
print('SHA and sizes verified',len(a['files']),'files;',a['actualCompletedUpdates'],'actual updates')

def sha_raw(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for raw in a['assembledCheckpoints']:
 manifest=R/raw['chunksManifest'];parts=json.loads(manifest.read_text());h=hashlib.sha256();total=0
 for row in parts['chunks']:
  p=manifest.parent/row['path'];data=p.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'];h.update(data);total+=len(data)
 assert total==raw['bytes']==parts['bytes'] and h.hexdigest()==raw['sha256']==parts['sha256']
 if (R/raw['path']).exists():assert sha_raw(R/raw['path'])==raw['sha256']
