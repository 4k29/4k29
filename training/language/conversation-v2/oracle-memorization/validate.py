from experiment import *
from collections import Counter
calls=read(P/'CALLS.json')
for arm in 'AB':
    log=read(P/f'{arm}-ledger.json')
    expected_count=0
    for k,row in enumerate(log,1):
        idx=3*((k-1)%4);batch=train[idx:idx+3]
        expected=sum(len(r['gold'])+(len(r['prefix'])-1 if arm=='A' else 0) for r in batch)
        assert row['targets']==expected and row['ids']==[r['id'] for r in batch] and row['step']==k
        expected_count+=expected
    assert expected_count==calls[arm]['processed'] and len(log)==300
    assert log[100]==read(P/f'{arm}-probe.json')['row']
    assert log[0]==read(P/f'{arm}-preflight.json')
for name in ['initial','B-terminal','C-terminal','A-100','A-300','B-100','B-300']:
    f=P/f'{name}.json.gz'
    rows=json.load(gzip.open(f))['cases']
    for r in rows:
        assert len(r['generated'])<=r['budget'] and len(r['prefix']+r['forced']+r['generated'])-1<=256
        if r['panel']=='prose':
            d=next(d for d in read(V/'gv-prose-pilot/EVALUATION_INPUTS.json')['prose'] if r['id']==d['id'])
            assert r['prefix']+r['forced']+r['gold']==d['tokens']
            if name in plan['models']:assert r['budget']==112
        assert 2 not in r['generated'][:-1]
print('PASS: split, masks, schedule, resume ledger, oracle alignment and generation limits')
