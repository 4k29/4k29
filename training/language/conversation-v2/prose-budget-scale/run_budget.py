"""Continue the archived C-300 model with fresh teacher positions and inherited Adam."""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
sys.path.insert(0,str(BASE/'prose-lr-decay'))
import decay

lr = decay.lr
torch = lr.torch
engine = lr.engine
read = decay.read
save = decay.save
parent = BASE/'prose-lr-decay/artifacts/C-300'
plan = read(ROOT/'PLAN.json')
assert decay.sha(ROOT/'PLAN.json') == (ROOT/'PLAN.sha256').read_text().strip()
for name, checksum in plan['frozen'].items():
    assert decay.sha(ROOT/name) == checksum
assert read(parent/'checkpoint.json')['sha256'] == plan['parent_checkpoint']
prose, replay, schedule = [read(ROOT/name) for name in ('TRAIN.json','REPLAY.json','SCHEDULE.json')]
inherited_batch = engine.batch_for

def batch_for(arm,k):
    original = engine.train,engine.replay,engine.schedule
    try:
        engine.train,engine.replay,engine.schedule = prose,replay,{'C':schedule}
        return inherited_batch('C',k-300)
    finally:
        engine.train,engine.replay,engine.schedule = original

def journal(k,kind,event):
    with (ROOT/'CALL_JOURNAL.jsonl').open('a') as report:
        report.write(json.dumps(dict(step=k,kind=kind,event=event))+'\n')
        report.flush()
        os.fsync(report.fileno())

def update(m,o,k,initial,kind):
    x,y,group,n = batch_for('C',k)
    o.zero_grad(set_to_none=True)
    z = m(x)
    ce = torch.nn.functional.cross_entropy
    losses = ce(z.flatten(0,1),y.flatten(),reduction='none').reshape_as(y)
    loss = ce(z.flatten(0,1),y.flatten(),reduction='sum')/n
    assert torch.isfinite(loss)
    loss.backward()
    norm = float(engine.clip_grad_accurate(m.parameters(),1.))
    assert math.isfinite(norm)
    before = [p.detach().clone() for p in m.parameters()]
    journal(k,kind,'begin')
    o.step()
    journal(k,kind,'returned')
    delta = math.sqrt(math.fsum(float((p.detach()-b).double().square().sum()) for p,b in zip(m.parameters(),before)))
    distance = lr.displacement(m,initial)['total']
    assert math.isfinite(delta) and math.isfinite(distance)
    assert {int(v['step']) for v in o.state.values()} == {k}
    return dict(step=k,lr=o.param_groups[0]['lr'],step_adam=k,loss=float(loss.detach()),
        prose_loss=float(losses[group==0].sum().detach())/n,replay_loss=float(losses[group==1].sum().detach())/n,
        prose=int((group==0).sum()),replay=int((group==1).sum()),denominator=n,norm=norm,clipped=norm>1,
        delta=delta,distance=distance,shape=list(x.shape),nonfinite=False)

def start(folder):
    m,o,state = decay.restore(folder)
    k = state['uniqueUpdates']
    assert len(state['history']) == k and {int(v['step']) for v in o.state.values()} == {k}
    assert o.param_groups[0]['lr'] == plan['lr']
    if k==300:
        old = BASE/'prose-learning-rate/B-ledger.json'
        assert state['history']==read(old)[:150]+read(BASE/'prose-lr-decay/C-ledger.json')
        assert k==plan['start']
    return m,o,state

def generate(m,k,heldout=False):
    b = lr.broad
    b.ROOT = ROOT
    if heldout:
        b.new_dev = [dict(r,tokens=r['prefix']+r['gold'],teacher_continuation=r['gold'][:32])
                     for r in read(ROOT/'HELDOUT.json')]
        b.generate(m,'heldout',k,only_new=True)
    else:
        b.stats(m,'C',k)
        b.generate(m,'C',k)

def main():
    initial = {n:p.detach().clone() for n,p in lr.previous.initial('initial').named_parameters()}
    if sys.argv[1]=='witness':
        m,o,_ = start(parent)
        row = update(m,o,301,initial,'witness')
        print(json.dumps(dict(row=row,digest=decay.signature(m,o))))
        return
    assert not (ROOT/'CALL_JOURNAL.jsonl').exists()
    m,o,st = start(parent)
    rows = list(st['history'])
    expected = json.loads(subprocess.check_output([sys.executable,__file__,'witness']))
    for k in range(301,plan['stop']+1):
        row = update(m,o,k,initial,'retained')
        if k==301:
            assert expected==dict(row=row,digest=decay.signature(m,o))
            save(ROOT/'RESUME.json',expected)
        rows.append(row)
        # Atomic decimal JSON ledger deposition after each retained optimizer call.
        save(ROOT/'ledger.tmp',rows[300:])
        (ROOT/'ledger.tmp').replace(ROOT/'LEDGER.json')
        if k in plan['checkpoint']:
            decay.archive(m,o,k,rows,ROOT/'artifacts'/f'C-{k}')
        if k in plan['evaluation']:
            rng = torch.get_rng_state().clone()
            generate(m,k)
            assert torch.equal(rng,torch.get_rng_state())
        if k%50==0:
            print(k, flush=True)
    if plan['heldout_evaluation']:
        generate(start(parent)[0],300,True)
        generate(start(ROOT/'artifacts'/f'C-{plan["stop"]}')[0],plan['stop'],True)

if __name__=='__main__':
    main()
