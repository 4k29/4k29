"""Freeze the rate comparison and the exact inherited evidence."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
SOURCE=BASE/'broad-prose-replay'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    return json.loads(path.read_text())
def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    plan=read(SOURCE/'PLAN.json')
    assert sha(SOURCE/'PLAN.json')==(SOURCE/'PLAN.sha256').read_text().strip()
    assert all(sha(SOURCE/f)==h for f,h in plan['frozen'].items())
    files=[SOURCE/f for f in ('PLAN.json','TRAIN.json','NEW_DEV.json','SCHEDULE.json','run.py','C-ledger.json','REVIEW_NOTES.json','JUDGMENTS.json')]
    files.extend([SOURCE/f'C-{k}.json.gz' for k in (10,20,50,100,200,300)])
    files.extend([BASE/f for f in ('replay-study/REPLAY.json','replay-study/SCHEDULE.json','replay-study/run.py','data/tokenizer.json','gv-prose-pilot/EVALUATION_INPUTS.json','oracle-memorization/evaluate.py')])
    save(ROOT/'PLAN.json',dict(baseline=plan['baseline'],source_arm='C',seed=12103,lr={'A':.0001,'B':.00003},
        adam='fresh AdamW beta=.9/.999 eps=1e-8 decay=.01',clip=1,updates=300,prose=46013,replay=46012,
        steps=[0,10,20,50,100,150,200,250,300],save_steps=[100,200,300],diagnostic_steps=[0,100,200,300],
        primary='At 300: natural topical continuation of two connected sentences with no harmful loops. One sentence separate. Greedy as in PR125.',
        control_reconstruction='Load PR125 C-100. Reproduce steps 101–250; each loss, norm, parameter delta and mask count must exactly match archived ledger. Run A150 and A250 greedy; A200 diagnostic. Early absolute distances reconstruct first 50 steps separately.',
        frozen={str(f.relative_to(BASE)):sha(f) for f in files}))
    (ROOT/'PLAN.sha256').write_text(sha(ROOT/'PLAN.json')+'\n')
