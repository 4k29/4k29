"""Verify final tracking/restore closure; no writes, model forward or optimizer."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];repo=R.parents[2];read=lambda p:json.loads(p.read_text());m=read(R/'execution/artifact-manifest.json');tracked=set(subprocess.check_output(['git','ls-files'],cwd=repo,text=True).splitlines());restorable=[];seen=set()
for x in m['files']+m['inputs']:
 p=(R/x['path']).resolve();key=str(p.relative_to(repo));assert p.exists()
 if key in tracked:continue
 if key in seen:continue
 seen.add(key);manifest=p.with_name(p.name+'.chunks.json');assert manifest.exists(),f'Untracked and not restorable: {key}';d=read(manifest);assert d['sha256']==x['sha256']and d['bytes']==x['bytes'];assert str(manifest.relative_to(repo))in tracked
 h=hashlib.sha256();size=0
 for part in d['chunks']:
  q=(manifest.parent/part['path']).resolve();assert str(q.relative_to(repo))in tracked;data=q.read_bytes();assert len(data)==part['bytes']and hashlib.sha256(data).hexdigest()==part['sha256'];h.update(data);size+=len(data)
 assert h.hexdigest()==x['sha256']and size==x['bytes'];restorable.append(key)
for x in m['assembledCheckpoints']:
 p=R/x['chunksManifest'];assert str(p.relative_to(repo))in tracked
 for part in read(p)['chunks']:assert str((p.parent/part['path']).relative_to(repo))in tracked
assert str((R/'execution/artifact-manifest.json').relative_to(repo))in tracked
print(json.dumps(dict(actualUpdates=m['actualCompletedUpdates'],allSavedFilesAndReferencedInputsTrackedOrLosslesslyRestorable=True,savedFiles=len(m['files']),inputReferences=len(m['inputs']),fullStates=len(m['assembledCheckpoints']),untrackedRawRestorable=restorable)))
