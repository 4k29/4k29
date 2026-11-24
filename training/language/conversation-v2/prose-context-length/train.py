"""Matched-budget context shortening using audited original sentence boundaries."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OLD=BASE/'prose-budget-scale'
sys.path.insert(0,str(OLD))
import run_budget as prior
from verify_budget import recover
from protocol import read, save, sha

torch=prior.torch
base_batch=prior.batch_for
cuts={(k,i,s):(drop,reason) for k,i,s,drop,reason in read(ROOT/'CUTS.json')}

def batch(arm,k):
    x,y,g,n=base_batch(arm,k)
    changes=[]
    for row,(i,s,count) in enumerate(prior.schedule[k-301]['prose']):
        match=cuts.get((k,i,s))
        if not match:
            continue
        cut,_=match
        offset=len(prior.prose[i]['prefix'])-1+s
        end=offset+count
        assert 0<cut<=offset
        changes.append((row,cut,end))
    if not changes:
        return x,y,g,n
    for row,cut,end in changes:
        x[row,:end-cut]=x[row,cut:end].clone()
        x[row,end-cut:]=0
        y[row,:end-cut]=y[row,cut:end].clone()
        y[row,end-cut:]=-100
        g[row,:end-cut]=g[row,cut:end].clone()
        g[row,end-cut:]=-1
    return x,y,g,n

def audit():
    evidence=[]
    for k in range(301,601):
        x,y,g,n=base_batch('C',k)
        a,b,h,d=batch('C',k)
        assert a.shape==x.shape and d==n
        assert torch.equal(y[y!=-100],b[b!=-100])
        assert torch.equal(g[g>=0],h[h>=0])
        assert torch.equal(x[(g==1).any(dim=1)],a[(h==1).any(dim=1)])
        for i,start,count in prior.schedule[k-301]['prose']:
            if (k,i,start) not in cuts:
                continue
            drop,reason=cuts[(k,i,start)]
            r=prior.prose[i]
            both=r['prefix']+r['gold'][:start]
            evidence.append(dict(step=k,index=i,family=r['family'],id=r['id'],
                provenance=r['provenance'],sha=r['text_sha256'],absolute_cut=drop,
                full=both,short=both[drop:],start=start,targets=r['gold'][start:start+count],reason=reason))
    assert len(evidence)==len(cuts)
    return evidence

def freeze():
    evidence=audit()
    save(ROOT/'PAIRS.json',evidence)
    files=[ROOT/'CUTS.json',ROOT/'PAIRS.json',Path(__file__),OLD/'PLAN.json',OLD/'TRAIN.json',
           OLD/'SCHEDULE.json',OLD/'REPLAY.json',OLD/'LEDGER.json',OLD/'artifacts/C-600/checkpoint.json',
           prior.parent/'checkpoint.json']
    save(ROOT/'PLAN.json',dict(scope='original-context length fallback; no paraphrase or self-generated histories',
        inputs={str(p.relative_to(BASE)):sha(p) for p in files},
        start=300,end=600,lr=1.65e-5,targets=92025,replay=46013,
        changed_targets=sum(len(r['targets']) for r in evidence),
        eval=[400,450,500,600],control='PR128 archived A at 300/450/600, no stored intermediate states at 400/500',
        evaluation='Original fixed 18 + 7 and caption32; archived held-out diagnostic at terminal. Paired TRAIN continuation NLL and greedy at terminals. Score semantic natural sentences separately from token cycles.',
        notes='Batch extent and supervised label order unchanged; changed rows have right padding and original sentence suffix starts at position 0.'))
    (ROOT/'PLAN.sha256').write_text(sha(ROOT/'PLAN.json')+'\n')

def evaluate(m,k):
    saved=prior.ROOT
    prior.ROOT=ROOT
    try:
        prior.generate(m,k)
    finally:
        prior.ROOT=saved

def main():
    if sys.argv[1]=='freeze':
        freeze()
        return
    plan=read(ROOT/'PLAN.json')
    assert sha(ROOT/'PLAN.json')==(ROOT/'PLAN.sha256').read_text().strip()
    for p,h in plan['inputs'].items():
        assert sha(BASE/p)==h
    assert len(audit())==len(cuts)
    prior.batch_for=batch
    prior.journal=lambda k,kind,event: journal(k,kind,event)
    initial={n:p.detach().clone() for n,p in prior.lr.previous.initial('initial').named_parameters()}
    if sys.argv[1]=='witness':
        m,o,_=prior.start(prior.parent)
        r=prior.update(m,o,301,initial,'witness')
        print(json.dumps(dict(row=r,digest=prior.decay.signature(m,o))))
        return
    control=recover(OLD/'artifacts/C-600')
    m,o,st=prior.start(prior.parent)
    rows=list(st['history'])
    assert control['history']==rows+read(OLD/'LEDGER.json')
    del control
    expected=json.loads(subprocess.check_output([sys.executable,__file__,'witness']))
    for k in range(301,601):
        row=prior.update(m,o,k,initial,'retained')
        if k==301:
            assert expected==dict(row=row,digest=prior.decay.signature(m,o))
            save(ROOT/'RESUME.json',expected)
        rows.append(row)
        save(ROOT/'ledger.tmp',rows[300:])
        (ROOT/'ledger.tmp').replace(ROOT/'LEDGER.json')
        if k==600:
            prior.decay.archive(m,o,k,rows,ROOT/'artifacts/B-600')
        if k in plan['eval']:
            rng=torch.get_rng_state().clone()
            evaluate(m,k)
            assert torch.equal(rng,torch.get_rng_state())
        if k%25==0:
            print(k,flush=True)

def journal(k,kind,event):
    import os
    with (ROOT/'CALL_JOURNAL.jsonl').open('a') as f:
        f.write(json.dumps(dict(step=k,kind=kind,event=event))+'\n')
        f.flush()
        os.fsync(f.fileno())

if __name__=='__main__':
    main()
