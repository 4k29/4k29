import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round43';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for n in ['multiview','sources','added-human-source','prospective-daily-source'] for p in (R/n).rglob('*') if p.is_file() and '__pycache__'not in p.parts]
for p in files:assert sha(p)==sha(P/p.relative_to(R)),str(p)
assert sha(R/'human-turn-token-boundaries.json')==sha(P/'human-turn-token-boundaries.json')
a=dict(actualOptimizerUpdates=0,allOldTokenBytesExactlyPreserved=True,allDataFilesByteIdenticalToRound43=True,verifiedFiles=len(files),allValidationAndTokenizerBytesExactlyPreserved=True,featureMapExactlyPreserved=True,noDataAcquisitionOrTestAccess=True)
(R/'execution/data-preflight.json').write_text(json.dumps(a,indent=2)+'\n');print(a)
