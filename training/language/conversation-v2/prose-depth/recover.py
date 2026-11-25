"""Resume a stopped arm from its last complete rolling checkpoint."""
import json
import sys

from train import ROOT, load_checkpoint, load_inputs, restore, evaluation, run, sha

def main(arm):
    folder=ROOT/'artifacts'/arm
    plan,schedule=load_inputs()
    state=load_checkpoint(folder)
    assert state['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
    cursor=state['cursor']
    ledger=state['ledger']
    path=ROOT/f'{arm}-calls.jsonl'
    calls=[json.loads(line) for line in path.read_text().splitlines()]
    assert calls[:cursor]==ledger
    assert len(ledger)==cursor
    if len(calls)>cursor:
        orphan=0
        while (ROOT/f'{arm}-rollback-{orphan}.jsonl').exists():
            orphan+=1
        receipt=ROOT/f'{arm}-rollback-{orphan}.jsonl'
        receipt.write_text(''.join(json.dumps(r)+'\n' for r in calls[cursor:]))
        temporary=path.with_suffix('.tmp')
        temporary.write_text(''.join(json.dumps(r)+'\n' for r in ledger))
        temporary.replace(path)
    if cursor in plan['points'] and not (ROOT/f'{arm}-{cursor}-eval.json.gz').exists():
        model,_=restore(arm,state)
        evaluation(model,arm,cursor,cursor==len(schedule))
    if cursor==len(schedule):
        from train import archive
        if (folder/'rolling.pt').exists():
            archive(folder/'rolling.pt')
    else:
        run(arm)

if __name__=='__main__':
    main(sys.argv[1])
