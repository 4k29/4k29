"""Verify the source locks, changed supervision and committed full states."""
from summarize import raw,KEYS
from study import ROOT,BASE,OLD,prior,read,sha,audit,recover,torch

def main():
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    assert all(sha(BASE/p)==d for p,d in plan['inputs'].items())
    masks=audit()
    assert masks==read(ROOT/'MASK.json')
    assert sum(len(p) for _,_,p in masks)==46012
    assert sum(x<len(prior.prose[i]['prefix']) for _,i,p in masks for x in p)==11112
    dev,terminal=([r for r in read(ROOT/f'{n}.json')['cases']] for n in ('DEV','DEV_PART2'))
    assert {r['family'] for r in dev}.isdisjoint(r['family'] for r in terminal)
    for name in ('DEV','DEV_PART2'):
        assert sha(ROOT/f'{name}.json')==(ROOT/f'{name}.sha256').read_text().strip()
    for r in dev:
        assert r['full'][r['cut']:]==r['short']
        assert len(r['full'])+r['maxNewTokens']<=257
    pieces=list(map(bytes.fromhex,read(BASE/'data/tokenizer.json')['bytes']))
    for r in dev+terminal:
        assert b''.join(pieces[t] for t in r['full']+r['gold']).decode()==r['text']
    led=read(ROOT/'LEDGER.json')
    shared=recover(prior.parent)
    archive=recover(OLD/'artifacts/C-600')
    changed=recover(ROOT/'artifacts/B-600')
    assert len(led)==300 and sum(r['denominator'] for r in led)==92025
    assert sum(r['replay'] for r in led)==46013 and sum(r['prose'] for r in led)==46012
    for step,r in enumerate(led,301):
        assert r['step_adam']==r['step']==step and r['lr']==plan['lr'] and not r['nonfinite']
    assert changed['history']==shared['history']+led
    assert archive['history']==shared['history']+read(OLD/'LEDGER.json')
    assert torch.equal(changed['torchRng'],archive['torchRng'])
    assert read(ROOT/'RESUME.json')['row']==led[0]
    assert {int(x['step']) for x in changed['optimizer']['state'].values()}=={600}
    paths=[ROOT/f'part1-{k}.json.gz' for k in KEYS]+[ROOT/f'C-{k}.json.gz' for k in plan['eval']]
    paths+=[ROOT/f'part2-heldout-{k}.json.gz' for k in 'AB']
    for p in paths:
        for r in raw(p)['cases']:
            assert not r['forced'] and r['generated']==[s['top5'][0][0] for s in r['steps']]
            assert b''.join(pieces[t] for t in r['generated']).hex()==r['raw_hex']
    print('PASS: source hashes, exact input equivalence, unique supervision, archived and cold-restored states, raw greedy')

if __name__=='__main__':
    main()
