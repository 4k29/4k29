"""Audit matched position counts, raw output and Git-only full state."""
import collections

from train import BASE, ROOT, CONFIG, DEPTHS, load_checkpoint, load_inputs, read, restore, sha, torch

def main():
    plan,schedule=load_inputs()
    index=read(ROOT/'TRAIN_INDEX.json')
    seen=collections.defaultdict(set)
    counts=collections.Counter()
    eos=0
    for batch in schedule:
        assert len(batch['ids'])==len(batch['rows'])
        assert sum(len(x)-1 for x in batch['rows'])==batch['targets']
        for (key,start),ids in zip(batch['ids'],batch['rows'],strict=True):
            n=index[key]['tokens']
            assert 2<=len(ids)<=257 and start%256==0 and start+len(ids)<=n
            assert all(0<i<3997 for i in ids)
            assert 1 not in ids[1:] and not set(ids)&{3,4,5}
            if 2 in ids:
                assert ids[-1]==2 and start+len(ids)==n and ids.count(2)==1
                eos+=1
            positions=set(range(start+1,start+len(ids)))
            assert seen[key].isdisjoint(positions)
            seen[key].update(positions)
            counts[index[key]['source']]+=len(ids)-1
    assert counts==plan['counts'] and sum(counts.values())==plan['targets']
    assert set(seen)==set(index)
    configs=[plan['configs'][key] for key in DEPTHS]
    assert {k:v for k,v in configs[0].items() if k!='layers'}=={k:v for k,v in configs[1].items() if k!='layers'}==CONFIG
    tokenizer=read(BASE/'data/tokenizer.json')
    pieces=list(map(bytes.fromhex,tokenizer['bytes']))
    dev={r['id']:r for r in read(ROOT/'DEV.json')}
    for r in dev.values():
        if r['panel']=='independent':
            assert b''.join(pieces[t] for t in r['prefix']+r['gold']).decode()==r['text']
            assert sha(r['text'].encode())==r['sha']
    import gzip
    import json
    for arm in DEPTHS:
        state=load_checkpoint(ROOT/'artifacts'/arm,git_only=True)
        assert state['cursor']==state['optimizer_step']==len(schedule)
        assert state['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
        assert state['schedule_sha']==plan['schedule_sha']
        assert state['config']==plan['configs'][arm]
        m,o=restore(arm,state)
        assert sum(p.numel() for p in m.parameters())==read(ROOT/'BENCHMARK.json')[arm]['parameters']
        assert {int(x['step']) for x in o.state.values()}=={len(schedule)}
        assert all(torch.isfinite(p).all() for p in m.parameters())
        assert read(ROOT/f'{arm}-resume.json')['match']
        calls=list(map(json.loads,(ROOT/f'{arm}-calls.jsonl').read_text().splitlines()))
        assert calls==state['ledger']
        assert len(calls)==len(schedule)
        for a,b in zip(calls,schedule,strict=True):
            assert a['targets']==b['targets'] and a['lr']==b['lr']
        for step in [0]+plan['points']:
            with gzip.open(ROOT/f'{arm}-{step}-eval.json.gz','rt') as f:
                result=json.load(f)
            assert {r['id'] for r in result['rows']}=={r['id'] for r in dev.values()
                if r['panel']!='independent' or step==len(schedule)}
            for r in result['rows']:
                assert b''.join(pieces[t] for t in r['generated']).hex()==r['rawBytesHex']
                assert r['generated']==[t['top'][0][0] for t in r['steps']]
                assert len(r['generated'])<=min(dev[r['id']]['budget'],256-len(dev[r['id']]['prefix']))
                assert (r['stop']=='EOS')==(r['generated'][-1]==2)
    print(f'PASS: {len(schedule)} matched updates, {sum(counts.values())} independent positions, {eos} original EOS, two Git-only states')
if __name__=='__main__':
    main()
