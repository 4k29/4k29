"""Audit source coordinates, schedule statistics and committed restart states."""
import collections
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

from run import ROOT,OLD,INITIAL,PIECES,LR,load_schedule,inputs,read,dump,sha,restore,digest,start,git_checkpoint,make_batch,update

def add_rows(schedule,index,seen,sources,families,documents,counts,prose):
    for b in schedule:
        assert b['targets']==sum(len(seq)-1 for seq in b['rows'])
        for (key,offset),seq in zip(b['ids'],b['rows'],strict=True):
            row=index[key]
            n=len(seq)-1
            assert 1<=n<=256 and offset%256==0 and offset+len(seq)<=row['length']
            assert 0 not in seq and 1 not in seq[1:] and not set(seq)&{3,4,5}
            if 2 in seq:
                assert seq[-1]==2 and seq.count(2)==1 and offset+len(seq)==row['length']
            assert (key,offset) not in seen
            seen.add((key,offset))
            counts['targets']+=n
            counts['eos']+=seq[1:].count(2)
            counts['lf']+=seq[1:].count(16)
            counts['space']+=seq[1:].count(38)
            sources[row['src']]+=n
            families[row['family']]+=n
            documents[key]=row['length']
            if row['src']!='stair' and 'sentences' in row:prose[key]=row['sentences']

def audit_positions(write):
    plan,schedule=inputs()
    assert sha((ROOT/'PLAN.json').read_bytes())==(ROOT/'PLAN.sha256').read_text().strip()
    old_index=read(OLD/'TRAIN_INDEX.json')
    old={k:dict(src=r['source'],family=r['family'],length=r['tokens']) for k,r in old_index.items()}
    new=read(ROOT/'TRAIN_INDEX.json')
    seen=set();sources=collections.Counter();families=collections.Counter();docs={};counts=collections.Counter();prose={}
    add_rows(load_schedule(OLD),old,seen,sources,families,docs,counts,prose)
    assert counts['targets']==plan['initial_targets']
    windows=collections.Counter()
    rows=[]
    stages={int(k):v for k,v in plan['stages'].items()}
    for k,b in enumerate(schedule,INITIAL+1):
        assert b['lr']==LR
        add_rows([b],new,seen,sources,families,docs,counts,prose)
        windows.update(tuple(seq) for seq in b['rows'])
        if k in stages:
            assert counts['targets']==stages[k]
            rows.append(dict(step=k,cumulative_targets=counts['targets'],by_source=dict(sources),
                           family_count=len(families),documents=len(docs),largest_family=max(families.values()),
                           eos=counts['eos'],lf=counts['lf'],space=counts['space'],
                           additional_mean_raw_sentences=statistics.mean(prose.values()),
                           document_token_median=statistics.median(docs.values()),
                           new_identical_window_occurrences=sum(n-1 for n in windows.values()),
                           new_identical_window_targets=sum((n-1)*(len(seq)-1) for seq,n in windows.items())))
    assert counts['targets']==plan['train_targets']
    dev=read(ROOT/'DEV.json')
    assert len({r['id'] for r in dev})==len(dev)
    for r in dev:
        assert r['prefix'] and 1<=len(r['prefix'])<256 and len(r['prefix'])+len(r['gold'])<=257
        assert (r['panel']=='caption')==not_gold(r)
        if r['panel']=='independent':
            assert b''.join(PIECES[t] for t in r['prefix']+r['gold']).decode()==r['text']
            assert sha(r['text'].encode())==r['sha']
    if write:dump(ROOT/'DISTRIBUTION.json',rows)
    else:assert rows==read(ROOT/'DISTRIBUTION.json')
    return plan,schedule

def not_gold(r):
    return not r['gold']

def witness(step):
    _,schedule=inputs()
    s=git_checkpoint(ROOT/'artifacts'/f'A-{step}')
    m,o=restore('A',s)
    result=update(m,o,*make_batch(schedule[step-INITIAL]['rows']),LR)
    print(json.dumps(dict(row=result,state_digest=digest(m,o))))

def verify_cold(extra_update=False):
    plan,schedule=audit_positions(False)
    m,o,s=start()
    assert digest(m,o)==read(ROOT/'BENCHMARK.json')['initial_digest']
    led=list(map(json.loads,(ROOT/'LEDGER.jsonl').read_text().splitlines()))
    assert len(schedule)==len(led)
    stages={int(k):v for k,v in plan['stages'].items()}
    for i,(b,row) in enumerate(zip(schedule,led,strict=True),INITIAL+1):
        assert row['step']==i and row['targets']==row['nonpad']==b['targets'] and row['lr']==LR
        assert row['raw_positions']==max(len(seq)-1 for seq in b['rows'])*len(b['rows'])
        assert all(math.isfinite(row[k]) for k in ('loss','norm','delta','wall','cpu'))
    cold={}
    for k in stages:
        if stages[k]<2_000_000:continue
        s=git_checkpoint(ROOT/'artifacts'/f'A-{k}')
        assert s['optimizer_step']==s['cursor']==k and s['ledger']==led[:k-INITIAL]
        assert s['initial_sha']==plan['checkpoint_sha'] and s['schedule_sha']==plan['schedule_sha']
        assert s['initial_digest']==read(ROOT/'BENCHMARK.json')['initial_digest']
        m,o=restore('A',s)
        assert sum(p.numel() for p in m.parameters())==11_225_280
        assert {int(r['step']) for r in o.state.values()}=={k}
        cold[str(k)]=digest(m,o)
    assert read(ROOT/'RESUME.json')['match']
    if extra_update:
        k=min(k for k in stages if stages[k]>=2_000_000)
        outputs=[json.loads(subprocess.check_output([sys.executable,__file__,'witness',str(k)])) for _ in range(2)]
        assert outputs[0]==outputs[1]
        target=led[k-INITIAL]
        assert all(target[k]==v for k,v in outputs[0]['row'].items())
        dump(ROOT/'COLD_RESUME.json',dict(checkpoint_digests=cold,witness_step=k+1,discarded_optimizer_calls=2,**outputs[0]))
    else:
        assert cold==read(ROOT/'COLD_RESUME.json')['checkpoint_digests']
    print('PASS: indexed unique teachers, all cold archives and actual optimizer ledgers')

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='positions':audit_positions(True)
    elif cmd=='witness':witness(int(sys.argv[2]))
    else:verify_cold(cmd=='cold-witness')
