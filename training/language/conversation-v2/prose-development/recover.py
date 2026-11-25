"""Reinstate the latest frozen-stage archive if a stopped job lost its rolling file."""
import json
from run import ROOT,INITIAL,git_checkpoint,read,sha,torch

def main():
    if (ROOT/'rolling/rolling.pt').exists():
        print('Use run.py run with the existing rolling state.')
        return
    plan=read(ROOT/'PLAN.json')
    candidates=[int(k) for k in plan['stages'] if (ROOT/'artifacts'/f'A-{k}'/'checkpoint.json').exists()]
    if not candidates:raise SystemExit('No committed continuation archive yet.')
    k=max(candidates)
    archive=ROOT/'artifacts'/f'A-{k}'
    state=git_checkpoint(archive)
    assert state['cursor']==k and state['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
    ledger=ROOT/'LEDGER.jsonl'
    if ledger.exists():
        records=[json.loads(x) for x in ledger.read_text().splitlines()]
        assert records[:k-INITIAL]==state['ledger']
        if len(records)>k-INITIAL:
            backup=ROOT/f'interrupted-calls-{k}.jsonl'
            with backup.open('x') as f:
                f.write(''.join(json.dumps(x)+'\n' for x in records[k-INITIAL:]))
    ledger.write_text(''.join(json.dumps(x)+'\n' for x in state['ledger']))
    (ROOT/'rolling').mkdir(exist_ok=True)
    torch.save(state,ROOT/'rolling/rolling.pt')
    print(f'Restored checkpoint {k}; execute run.py run to continue.')

if __name__=='__main__':main()
