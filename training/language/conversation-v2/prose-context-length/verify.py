"""Verify frozen seams, label equivalence, cold states and execution evidence."""
from collections import Counter
from train import ROOT, BASE, OLD, prior, audit, recover, read, sha, torch
from analyze import files, raw, POINTS

def main():
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    for name,d in plan['inputs'].items():
        assert sha(BASE/name)==d
    pairs=audit()
    assert pairs==read(ROOT/'PAIRS.json') and len({r['family'] for r in pairs})==16
    pieces=[bytes.fromhex(t) for t in read(BASE/'data/tokenizer.json')['bytes']]
    for r in pairs:
        removed=b''.join(pieces[t] for t in r['full'][:r['absolute_cut']]).decode()
        retained=b''.join(pieces[t] for t in r['short']).decode()
        assert removed.endswith('。') and '。' in retained
        assert r['full'][r['absolute_cut']:]==r['short']
    assert sum(len(r['targets']) for r in pairs)==plan['changed_targets']==985
    b=read(ROOT/'LEDGER.json')
    a=read(OLD/'LEDGER.json')
    assert sum(r['denominator'] for r in b)==92025 and sum(r['replay'] for r in b)==46013
    for k,(source,dest) in enumerate(zip(a,b,strict=True),301):
        for key in ('denominator','prose','replay','shape','step','step_adam','lr'):
            assert source[key]==dest[key]
        assert dest['step']==k and not dest['nonfinite']
    assert a[:13]==b[:13]
    assert read(ROOT/'RESUME.json')['row']==b[0]
    c300=recover(prior.parent)
    c600=recover(OLD/'artifacts/C-600')
    b600=recover(ROOT/'artifacts/B-600')
    for k,s in ((300,c300),(600,c600),(600,b600)):
        assert s['uniqueUpdates']==len(s['history'])==k
        assert {int(z['step']) for z in s['optimizer']['state'].values()}=={k}
    assert c600['history']==c300['history']+a and b600['history']==c300['history']+b
    assert torch.equal(c600['torchRng'],b600['torchRng'])
    assert read(ROOT/'control/RECONSTRUCTION.json')['matches']==list(range(301,501))
    assert read(ROOT/'CALLS.json')['optimizer_calls']=={'retained':300,'witness':1,'control_reconstruction':200}
    paths={files(arm,k)[0] for arm in 'AB' for k in POINTS}
    paths.update(ROOT/'paired'/f'{name}.json.gz' for name in ('A','B','heldout-B-600'))
    for path in paths:
        for row in raw(path)['cases']:
            assert not row['forced']
            assert row['generated']==[v['top5'][0][0] for v in row['steps']]
            assert row['raw_hex']==b''.join(pieces[t] for t in row['generated']).hex()
            assert len(row['generated'])<=row['budget']
    print('PASS frozen source and vocabulary, 985 aligned substitutions, 501 calls, cold states and unmodified generations')

if __name__=='__main__':
    main()
