"""Restore the latest committed 70% state when a worker loses its rolling file."""
import json
import time

from run import ROOT,PREV,dump,evaluate,git_checkpoint,inputs,read,restore,save

def main():
    plan,_=inputs()
    rolling=ROOT/'rolling/rolling.pt'
    if rolling.exists():
        raise SystemExit('Rolling state exists. Use run.py train after backfilling any missing stage evaluation.')
    available=[k for k in plan['b_steps'][1:] if (ROOT/'artifacts'/f'B-{k}'/'checkpoint.json').exists()]
    if not available:
        raise SystemExit('No durable archive. Use the original frozen run to start from A-985.')
    step=max(available)
    state=git_checkpoint(ROOT/'artifacts'/f'B-{step}')
    assert state['cursor']==state['optimizer_step']==step and state['schedule_sha']==plan['schedule_sha']
    model,optimizer=restore('A',state)
    log=ROOT/'LEDGER.jsonl'
    committed=state['ledger']
    previous=[json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    assert previous[:min(len(previous),len(committed))]==committed[:len(previous)]
    if len(previous)>len(committed):
        discarded=ROOT/f'rollback-{step}-{time.time_ns()}.jsonl'
        discarded.write_text(''.join(json.dumps(r)+'\n' for r in previous[len(committed):]))
    temporary=log.with_suffix('.tmp')
    temporary.write_text(''.join(json.dumps(r)+'\n' for r in committed))
    temporary.replace(log)
    save(rolling.parent,model,optimizer,step,committed,plan)
    if not (ROOT/f'B-{step}.json.gz').exists():
        cases=[r for r in read(ROOT/'DEV.json') if r['panel']!='ratio-heldout']+read(PREV/'MONITOR.json')
        evaluate(model,cases,f'B-{step}')
    dump(ROOT/'LAST_RESTORE.json',dict(step=step,source='Git objects',recovered_updates=len(committed),
         discarded_ledger_entries=max(0,len(previous)-len(committed))))
    print('Recovered B state',step)

if __name__=='__main__':main()
