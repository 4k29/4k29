"""Train the 70% schedule and log unchanged greedy decoding."""
import collections
import gzip
import json
import math
import resource
import runpy
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PREV=BASE/'prose-development'
old=runpy.run_path(str(PREV/'run.py'))
torch=old['torch']
r=old['previous']
read, dump, sha, start, restore, make_batch, digest, git_checkpoint = (
    old[k] for k in ('read','dump','sha','start','restore','make_batch','digest','git_checkpoint'))
PIECES=old['PIECES']
INITIAL=985
LR=3e-5

def inputs():
    plan=read(ROOT/'PLAN.json')
    assert all(sha((ROOT/name).read_bytes())==h for name,h in plan['inputs'].items())
    raw=(ROOT/'SCHEDULE.json.gz').read_bytes()
    assert sha(raw)==plan['schedule_sha']
    return plan,json.loads(gzip.decompress(raw))

def update(m,o,item,meta):
    x,y=make_batch(item['rows'])
    wall=time.monotonic()
    cpu=time.process_time()
    m.train()
    o.param_groups[0]['lr']=LR
    o.zero_grad(set_to_none=True)
    n=item['targets']
    scores=torch.nn.functional.cross_entropy(m(x).flatten(0,1),y.flatten(),ignore_index=-100,reduction='none')
    assert n==int(y.ne(-100).sum())
    loss=scores.sum()/n
    per_row=scores.detach().reshape_as(y).sum(dim=1).tolist()
    loss.backward()
    norm=float(torch.nn.utils.clip_grad_norm_(m.parameters(),1.,error_if_nonfinite=True))
    before=[p.detach().clone() for p in m.parameters()]
    o.step()
    delta=math.sqrt(sum(float((p.detach()-q).square().sum()) for p,q in zip(m.parameters(),before)))
    by_source=collections.defaultdict(lambda:[0,0.0])
    for (key,_),seq,ce in zip(item['ids'],item['rows'],per_row,strict=True):
        obs=by_source[meta[key]['src']]
        obs[0]+=len(seq)-1
        obs[1]+=ce
    assert math.isfinite(delta) and math.isfinite(float(loss))
    return dict(targets=n,nonpad=int(x.ne(0).sum()),raw_positions=x.numel(),length=x.shape[1],
                lr=LR,loss=float(loss.detach()),norm=norm,clip=norm>1,delta=delta,by_source=dict(by_source),
                cpu=time.process_time()-cpu,wall=time.monotonic()-wall,
                rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

def save(folder,m,o,step,ledger,plan):
    folder.mkdir(parents=True,exist_ok=True)
    p=folder/'rolling.pt'
    q=p.with_suffix('.tmp')
    torch.save(dict(config=m.config,model=m.state_dict(),optimizer=o.state_dict(),
        torch_rng=torch.get_rng_state(),cursor=step,optimizer_step=step,ledger=ledger,
        initial_sha=plan['checkpoint_sha'],plan_sha=sha((ROOT/'PLAN.json').read_bytes()),
        schedule_sha=plan['schedule_sha']),q)
    q.replace(p)
    return p

@torch.inference_mode()
def evaluate(m, cases, label, check=False):
    m.eval()
    started=time.monotonic()
    rows=[]
    for case in cases:
        prefix,gold=case['prefix'],case['gold']
        assert 0<len(prefix)<256 and len(prefix)+len(gold)<=257
        assert gold or case['panel']=='caption'
        refs=old['gold_scores'](m,prefix,gold)
        if check:continue
        gold_space=[]
        if gold:
            q=m(torch.tensor([(prefix+gold)[:-1]]))[0,len(prefix)-1:].log_softmax(-1)
            gold_space=q[:,38].exp().tolist()
        output=[]
        trace=[]
        for j in range(min(case['budget'],256-len(prefix))):
            q=m(torch.tensor([prefix+output]))[0,-1].log_softmax(-1)
            token=int(q.argmax())
            top=q.topk(5)
            p=q.exp()
            trace.append(dict(top=list(zip(top.indices.tolist(),top.values.exp().tolist())),
                ref=float(q[gold[j]]) if j<len(gold) else None,space=float(p[38]),lf=float(p[16]),
                eos=float(p[2]),digits=float(p[54:64].sum()),entropy=float(-(q*p).sum())))
            output.append(token)
            if token==2:break
        rows.append(dict(id=case['id'],panel=case['panel'],gold=gold,ref=refs,gold_space=gold_space,generated=output,
            steps=trace,stop='EOS' if output[-1]==2 else 'budget',
            first=next((j for j,(a,b) in enumerate(zip(output,gold)) if a!=b),None),
            repeat=old['repeated_gram'](output),**old['byte_payload'](output,PIECES)))
    if not check:
        path=ROOT/f'{label}.json.gz'
        temporary=path.with_suffix('.tmp')
        temporary.write_bytes(gzip.compress(json.dumps(dict(rows=rows,seconds=time.monotonic()-started),
            ensure_ascii=False,allow_nan=False).encode(),mtime=0))
        temporary.replace(path)

def train():
    plan,sched=inputs()
    meta=read(PREV/'TRAIN_INDEX.json')
    dev=read(ROOT/'DEV.json')
    regular=[c for c in dev if c['panel']!='ratio-heldout']+read(PREV/'MONITOR.json')
    m,o,_=start()
    rolling=ROOT/'rolling'
    ledger=[]
    cursor=INITIAL
    if (rolling/'rolling.pt').exists():
        saved=r.load_checkpoint(rolling)
        assert saved['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
        m,o=restore('A',saved)
        cursor,ledger=saved['cursor'],saved['ledger']
        lines=(ROOT/'LEDGER.jsonl').read_text().splitlines()
        assert [json.loads(line) for line in lines[:len(ledger)]]==ledger
        if len(lines)>len(ledger):
            (ROOT/f'interrupted-{time.time_ns()}.jsonl').write_text('\n'.join(lines[len(ledger):])+'\n')
            (ROOT/'LEDGER.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in ledger))
    if cursor==INITIAL:
        evaluate(m,regular,'preflight',check=True)
        evaluate(m,[c for c in dev if c['panel']=='ratio-heldout'],'heldout-preflight',check=True)
        dump(ROOT/'PREFLIGHT.json',dict(gold=sum(bool(c['gold']) for c in regular+dev if c['panel']=='ratio-heldout')+
             sum(bool(c['gold']) for c in regular),caption=sum(not c['gold'] for c in regular),
             initial_digest=digest(m,o),heldout_result_observed=False))
    total=plan['initial_targets']+sum(x['targets'] for x in ledger)
    for step,item in enumerate(sched[cursor-INITIAL:],cursor+1):
        entry=update(m,o,item,meta)
        entry['step']=step
        assert int(next(iter(o.state.values()))['step'])==step
        ledger.append(entry)
        total+=item['targets']
        with (ROOT/'LEDGER.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        stage=plan['stages'].get(str(step))
        if step%100==0 or stage:save(rolling,m,o,step,ledger,plan)
        if stage:
            assert total==stage
            if total>=2_000_000:
                r.archive(save(ROOT/'artifacts'/f'B-{step}',m,o,step,ledger,plan))
            evaluate(m,regular,f'B-{step}')
        if step%100==0 or stage:print(step,total,entry['loss'],flush=True)

def evaluate_terminals():
    plan,_=inputs()
    heldout=[c for c in read(ROOT/'DEV.json') if c['panel']=='ratio-heldout']
    end=plan['b_steps'][-1]
    state=git_checkpoint(ROOT/'artifacts'/f'B-{end}')
    model,_=restore('A',state)
    evaluate(model,heldout,'holdout-B')
    state=git_checkpoint(PREV/'artifacts/A-2950')
    model,_=restore('A',state)
    evaluate(model,heldout,'holdout-A')
    model,_,_=start()
    evaluate(model,heldout,'holdout-start')

def witness():
    plan,sched=inputs()
    point=plan['b_steps'][1]
    saved=git_checkpoint(ROOT/'artifacts'/f'B-{point}')
    assert saved['cursor']==saved['optimizer_step']==point
    m,o=restore('A',saved)
    row=update(m,o,sched[point-INITIAL],read(PREV/'TRAIN_INDEX.json'))
    result={k:row[k] for k in ('norm','loss','delta','targets')}
    actual=json.loads((ROOT/'LEDGER.jsonl').read_text().splitlines()[point-INITIAL])
    match=all(result[k]==actual[k] for k in result)
    assert match
    print(json.dumps(dict(step=point+1,match=match,digest=digest(m,o),metrics=result)))

if __name__=='__main__':
    {'train':train,'holdout':evaluate_terminals,'witness':witness}[sys.argv[1]]()
