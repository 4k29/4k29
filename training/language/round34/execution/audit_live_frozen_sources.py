"""Post-freeze read-only recheck; never reads model or optimizer states."""
import pathlib,json,hashlib,datetime
R=pathlib.Path(__file__).resolve().parents[1];p=R/'source-manifest.json';raw=p.read_bytes();source=json.loads(raw);total=0
for item in source['files']:
 path=R/item['path'];assert path.stat().st_size==item['bytes'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],item['path'];total+=item['bytes']
rows=[]
for line in (R/'execution/train.log').read_text().splitlines():
 try:rows.append(json.loads(line))
 except json.JSONDecodeError:pass
last=rows[-1]
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceManifestSha256=hashlib.sha256(raw).hexdigest(),allFrozenSourceFilesUnchanged=True,verifiedFiles=len(source['files']),verifiedBytes=total,lastLoggedActualUpdates=last.get('step',last.get('completedUpdates',0)),noModelOrOptimizerOpened=True,noFrozenInputModified=True,notLanguageEvidence=True)
(R/'execution/live-frozen-source-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
