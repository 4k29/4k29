"""Summarize observed parity without concealing historical near-tie divergence."""
import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
def read(p):return json.loads(p.read_text())
reference=R.parent/'round11/execution/old-numerical-divergence.json'
out={n:read(E/f'{n}-numerical-divergence.json') for n in ['old','new']}
out.update(knownRound10Branch=dict(reference='../round11/execution/old-numerical-divergence.json',sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),strictSequenceParity='16/17 in recorded Round10 diagnosis; near-tie is not repaired or hidden'),toleranceUnchanged=0.0002)
(E/'numerical-divergence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
