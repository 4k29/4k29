"""Reallocate prose CE targets over the original unchanged model inputs."""
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OLD=BASE/'prose-budget-scale'
sys.path.insert(0,str(OLD))
import run_budget as prior
from verify_budget import recover
from protocol import read,save,sha

torch=prior.torch
base_batch=prior.batch_for

def positions(row,start,count):
    length=row['eligible_targets']
    available=len(row['prefix'])+length-1
    return [1+(q*available)//length for q in range(start,start+count)]

def batch(arm,k):
    x,y,g,n=base_batch(arm,k)
    for j,(i,start,count) in enumerate(prior.schedule[k-301]['prose']):
        row=prior.prose[i]
        tokens=row['prefix']+row['gold']
        indices=positions(row,start,count)
        assert max(indices)<len(row['prefix'])+start+count
        y[j,:]=-100
        g[j,:]=-1
        y[j,[p-1 for p in indices]]=torch.tensor([tokens[p] for p in indices])
        g[j,[p-1 for p in indices]]=0
    return x,y,g,n

def audit():
    seen=set()
    rows=[]
    for k,section in enumerate(prior.schedule,301):
        x,y,g,n=base_batch('C',k)
        a,b,h,d=batch('C',k)
        assert torch.equal(x,a) and d==n
        assert torch.equal(y[g==1],b[h==1]) and torch.equal(g==1,h==1)
        assert int((g==0).sum())==int((h==0).sum())
        for i,start,count in section['prose']:
            ps=positions(prior.prose[i],start,count)
            assert not seen.intersection((i,p) for p in ps)
            seen.update((i,p) for p in ps)
            rows.append([k,i,ps])
    assert len(seen)==46012
    return rows

def freeze():
    save(ROOT/'MASK.json',audit())
    paths=[ROOT/'MASK.json',Path(__file__),OLD/'TRAIN.json',OLD/'SCHEDULE.json',OLD/'REPLAY.json',
           OLD/'LEDGER.json',OLD/'PLAN.json',prior.parent/'checkpoint.json',OLD/'artifacts/C-600/checkpoint.json',
           BASE/'prose-context-length/artifacts/B-600/checkpoint.json']
    save(ROOT/'PLAN.json',dict(inputs={str(p.relative_to(BASE)):sha(p) for p in paths},
        intervention='Unique deterministic article-wide article targets. For teacher ordinal q, use token index 1+floor(q*(prefix length+eligible targets-1)/eligible targets).',
        start=300,stop=600,eval=[400,450,500,600],lr=1.65e-5,clip=1,targets=92025,replay=46013,
        primary='Fixed 18+7 new natural sentences A/B at 600, caption retention and paired common-position NLL; inherited A at all five stages.',
        independent_DEV='Separate evaluation if provenance and isolation permit; Part 1 not counted as a fresh Part 2 holdout.',
        conditional_C='Omitted to prioritize the two matched conditions on 2 CPU.'))

    (ROOT/'PLAN.sha256').write_text(sha(ROOT/'PLAN.json')+'\n')

def journal(k,kind,event):
    with (ROOT/'CALL_JOURNAL.jsonl').open('a') as f:
        f.write(json.dumps(dict(step=k,kind=kind,event=event))+'\n')
        f.flush()
        os.fsync(f.fileno())

def main():
    if sys.argv[1]=='freeze':
        freeze()
        return
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    assert all(sha(BASE/p)==d for p,d in plan['inputs'].items())
    assert audit()==read(ROOT/'MASK.json')
    prior.batch_for=batch
    prior.journal=journal
    initial={n:p.detach().clone() for n,p in prior.lr.previous.initial('initial').named_parameters()}
    m,o,st=prior.start(prior.parent)
    if sys.argv[1]=='witness':
        row=prior.update(m,o,301,initial,'witness')
        print(json.dumps(dict(row=row,digest=prior.decay.signature(m,o))))
        return
    assert not (ROOT/'CALL_JOURNAL.jsonl').exists()
    assert recover(OLD/'artifacts/C-600')['history']==st['history']+read(OLD/'LEDGER.json')
    expected=json.loads(subprocess.check_output([sys.executable,__file__,'witness']))
    history=list(st['history'])
    for k in range(301,601):
        row=prior.update(m,o,k,initial,'retained')
        if k==301:
            assert expected==dict(row=row,digest=prior.decay.signature(m,o))
            save(ROOT/'RESUME.json',expected)
        history.append(row)
        save(ROOT/'ledger.tmp',history[300:])
        (ROOT/'ledger.tmp').replace(ROOT/'LEDGER.json')
        if k==600:
            prior.decay.archive(m,o,k,history,ROOT/'artifacts/B-600')
        if k in plan['eval']:
            rng=torch.get_rng_state().clone()
            prior.ROOT=ROOT
            prior.generate(m,k)
            assert torch.equal(rng,torch.get_rng_state())
        if k%25==0:
            print(k,flush=True)

if __name__=='__main__':
    main()
