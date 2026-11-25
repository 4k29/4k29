"""Prepare a stopped continuation for restart from its last complete state."""
import json
from run import ROOT, INITIAL, git_checkpoint, read, sha, torch, restore, evaluate, previous

def main():
    rolling=ROOT/'rolling/rolling.pt'
    plan=read(ROOT/'PLAN.json')
    if rolling.exists():
        state=torch.load(rolling,weights_only=True,map_location='cpu')
    else:
        candidates=[int(k) for k in plan['stages'] if (ROOT/'artifacts'/f'A-{k}'/'checkpoint.json').exists()]
        if not candidates:raise SystemExit('No committed continuation archive yet.')
        state=git_checkpoint(ROOT/'artifacts'/f'A-{max(candidates)}')
    k=state['cursor']
    assert state['optimizer_step']==k and state['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())

    ledger=ROOT/'LEDGER.jsonl'
    if ledger.exists():
        records=[json.loads(x) for x in ledger.read_text().splitlines()]
        assert records[:k-INITIAL]==state['ledger']
        if len(records)>k-INITIAL:
            backup=ROOT/f'interrupted-calls-{k}.jsonl'
            with backup.open('x') as f:
                f.write(''.join(json.dumps(x)+'\n' for x in records[k-INITIAL:]))
    ledger.write_text(''.join(json.dumps(x)+'\n' for x in state['ledger']))

    if not rolling.exists():
        rolling.parent.mkdir(exist_ok=True)
        temporary=rolling.with_suffix('.tmp')
        torch.save(state,temporary)
        temporary.replace(rolling)
    count=plan['stages'].get(str(k))
    if count is not None:
        folder=ROOT/'artifacts'/f'A-{k}'
        if count>=2_000_000 and not (folder/'checkpoint.json').exists():
            folder.mkdir(exist_ok=True,parents=True)
            pending=folder/'rolling.pt'
            torch.save(state,pending)
            previous.archive(pending)
        if not (ROOT/f'A-{k}.json.gz').exists():
            model,_=restore('A',state)
            rows=[r for r in read(ROOT/'DEV.json') if r['panel']!='independent']+read(ROOT/'MONITOR.json')
            evaluate(model,rows,f'A-{k}')
    print(f'Restored checkpoint {k}; execute run.py run to continue.')

if __name__=='__main__':main()
