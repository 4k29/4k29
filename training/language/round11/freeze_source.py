"""Snapshot preparation only; actual training is audited separately."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
files=[]
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.name=='source-manifest.json' or 'continue-10000' in p.parts:continue
    files.append(dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(ROOT/'source-manifest.json').write_text(json.dumps(dict(files=files,completedUpdatesAtSourceFreeze=0,scope='Immutable pre-optimizer code/data snapshot; training results excluded'),indent=2)+'\n')
print(json.dumps(dict(frozenFiles=len(files),optimizerUpdates=0)))
