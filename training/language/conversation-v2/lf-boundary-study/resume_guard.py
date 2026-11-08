"""Fail closed before invoking the frozen trainer; never silently replay uncheckpointed calls."""
from lf_runtime import *
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--until',required=True,type=int);args=ap.parse_args()
es=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()]
assert [(e['phase'],e['trace']['step']) for e in es if e['event']=='intent']==[(e['phase'],e['trace']['step']) for e in es if e['event']=='completed'],'Uncertain optimizer call; stop and audit'
ret=[e['trace'] for e in es if e['event']=='completed' and e['phase']=='retained'];path=SCRATCH/'LF1-latest.pt'
if path.exists():
 obj=torch.load(path,map_location='cpu',weights_only=False);assert integrity(obj)==obj['integrity'];assert obj['plan_sha256']==sha(P/'PLAN.json');assert obj['trace']==ret and obj['active_cursor']==len(ret),'Ledger ahead of checkpoint: explicit recovery/replay accounting required, never automatic retained replay'
else:assert not ret,'Existing retained calls require checkpoint restoration'
import train
train.main()
