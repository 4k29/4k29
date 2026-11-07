import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((R/'execution/optimizer-audit.json').read_text());assert a['actualCompletedUpdates']==10000
files=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact-manifest.json':files.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size))
inputs=json.loads((R/'source-manifest.json').read_text())['files']
for f in ['../round16/execution/artifact-manifest.json','../round16/execution/new-validation.json','../round16/execution/new-manual.json','../round16/continue-10000/model.js','../round10/full-meaning-policy.json','../round10/review.py','../round10/evaluate.py','../round10/evaluate_js.mjs']:
 p=R/f;inputs.append(dict(path=f,sha256=sha(p),bytes=p.stat().st_size))
manifest=dict(actualCompletedUpdates=10000,requestedUpdates=10000,files=files,inputs=inputs,publicModelChanged=False,newTestGenerated=False)
(R/'execution/artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('frozen files',len(files))
