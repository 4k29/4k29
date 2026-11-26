"""Verify frozen comparisons, full Git archives, and the actual optimizer ledger."""
import json
import math
import subprocess
import sys

from distribution import collect
from review import cases
from run import ROOT,PREV,INITIAL,LR,PIECES,inputs,digest,dump,git_checkpoint,read,restore,sha,start

def ledger(p):
    return [json.loads(x) for x in p.read_text().splitlines()]

def verify(run_witness=False):
    plan,schedule=inputs()
    assert sha((ROOT/'PLAN.json').read_bytes())==(ROOT/'PLAN.sha256').read_text().split()[0]
    distribution=collect(plan)
    assert json.loads(json.dumps(distribution))==read(ROOT/'DISTRIBUTION.json')
    rows=ledger(ROOT/'LEDGER.jsonl')
    assert len(rows)==len(schedule)==plan['b_steps'][-1]-INITIAL
    for step,(entry,batch) in enumerate(zip(rows,schedule,strict=True),INITIAL+1):
        n=sum(len(seq)-1 for seq in batch['rows'])
        assert n==entry['targets']==entry['nonpad']==batch['targets']
        assert entry['raw_positions']==len(batch['rows'])*max(len(seq)-1 for seq in batch['rows'])
        assert n==sum(v[0] for v in entry['by_source'].values())
        assert math.isclose(entry['loss'],sum(v[1] for v in entry['by_source'].values())/n,rel_tol=1e-6)
        assert entry['step']==step and entry['lr']==batch['lr']==LR
        assert entry['clip']==(entry['norm']>1)
        assert all(math.isfinite(entry[k]) for k in ('loss','norm','delta','cpu','wall'))
    assert sum(row['targets'] for row in rows)+plan['initial_targets']==plan['main_targets']
    benchmark=read(ROOT/'BENCHMARK.json')
    assert all(rows[0][k]==benchmark['calls'][0][k] for k in ('targets','norm','delta','loss'))
    endings=[distribution['A-2950'],distribution[f"B-{plan['b_steps'][-1]}"]]
    assert {d['cumulative_targets'] for d in endings}=={plan['main_targets']}
    assert abs(endings[0]['prose']/endings[0]['targets']-.50)<.001
    assert abs(endings[1]['prose']/endings[1]['targets']-.70)<.000001
    for src in ('jaquad','jma','jawikivoyage','jawikibooks'):
        first,second=[d['sources'][src]/d['prose'] for d in endings]
        assert abs(first-second)<.001

    m,o,_=start()
    anchor=digest(m,o)
    assert anchor==read(PREV/'BENCHMARK.json')['initial_digest']==read(ROOT/'BENCHMARK.json')['start_digest']==read(ROOT/'PREFLIGHT.json')['initial_digest']
    cp=git_checkpoint(PREV/'artifacts/A-2950')
    assert cp['cursor']==cp['optimizer_step']==2950
    assert cp['initial_digest']==anchor and cp['initial_sha']==plan['checkpoint_sha']
    prior_plan=read(PREV/'PLAN.json')
    assert cp['schedule_sha']==prior_plan['schedule_sha']
    assert cp['plan_sha']==sha((PREV/'PLAN.json').read_bytes())
    assert cp['ledger']==ledger(PREV/'LEDGER.jsonl')[:2950-INITIAL]
    assert sum(entry['targets'] for entry in cp['ledger'])+plan['initial_targets']==plan['main_targets']
    digests={}
    for point in plan['b_steps'][1:]:
        saved=git_checkpoint(ROOT/'artifacts'/f'B-{point}')
        assert saved['cursor']==saved['optimizer_step']==point
        assert saved['ledger']==rows[:point-INITIAL]
        assert saved['schedule_sha']==plan['schedule_sha'] and saved['initial_sha']==plan['checkpoint_sha']
        assert saved['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
        m,o=restore('A',saved)
        assert {int(x['step']) for x in o.state.values()}=={point}
        assert sum(p.numel() for p in m.parameters())==11_225_280
        digests[str(point)]=digest(m,o)
    dev={r['id']:r for r in read(ROOT/'DEV.json')+read(PREV/'MONITOR.json')}
    held={k for k,r in dev.items() if r['panel']=='ratio-heldout'}
    assert len(held)==plan['holdout_cases']
    for k in held:
        row=dev[k]
        assert row['gold'] and sha(row['text'].encode())==row['sha']
        assert b''.join(PIECES[i] for i in row['prefix']+row['gold']).decode()==row['text']
    states=['start',*[f'A-{k}' for k in plan['a_steps']],*[f'B-{k}' for k in plan['b_steps']],
            'holdout-start','holdout-A','holdout-B']
    for state in states:
        outputs=cases(state)
        expected=held if state.startswith('holdout') else set(dev)-held
        if state=='A-1476':
            expected={k for k in expected if dev[k]['panel']!='independent'}
        assert {r['id'] for r in outputs}==expected and len(outputs)==len(expected),state
        for r in outputs:
            case=dev[r['id']]
            assert r['gold']==case['gold'],(state,r['id'])
            assert len(r['gold'])==len(r['ref'])
            assert r['generated']==[x['top'][0][0] for x in r['steps']]
            assert len(r['generated'])<=min(case['budget'],256-len(case['prefix']))
            assert b''.join(PIECES[i] for i in r['generated']).hex()==r['rawBytesHex']
            assert (r['generated'][-1]==2)==(r['stop']=='EOS')
    if run_witness:
        a,b=[json.loads(subprocess.check_output([sys.executable,str(ROOT/'run.py'),'witness'])) for _ in range(2)]
        assert a==b
        dump(ROOT/'COLD_RESUME.json',dict(digests=digests,witness=a,discarded_calls=2))
    else:
        assert digests==read(ROOT/'COLD_RESUME.json')['digests']
        assert read(ROOT/'COLD_RESUME.json')['witness']['match']
    print('Verified exact target budgets, nested sources, ledgers, checkpoints and raw generation.')

if __name__=='__main__':verify('--witness' in sys.argv)
