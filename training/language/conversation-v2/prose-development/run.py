"""Continue the vetted 8-layer decoder with its intact optimizer and RNG."""
import gzip
import json
import math
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OLD=BASE/'prose-depth'
sys.path.insert(0,str(OLD))
import train as previous
from train import torch, make_batch, update, restore, digest, dump, read, sha
from eval_core import byte_payload,repeated_gram

LR=3e-5
INITIAL=985
PIECES=[bytes.fromhex(t) for t in read(BASE/'data/tokenizer.json')['bytes']]

def load_schedule(folder):
    return json.loads(gzip.decompress((folder/'SCHEDULE.json.gz').read_bytes()))

def start():
    state=previous.load_checkpoint(OLD/'artifacts/A',git_only=True)
    assert state['cursor']==state['optimizer_step']==INITIAL
    assert sum(r['targets'] for r in state['ledger'])==1_000_985
    m,o=restore('A',state)
    assert o.param_groups[0]['lr']==LR
    assert {int(x['step']) for x in o.state.values()}=={INITIAL}
    return m,o,state

def benchmark():
    m,o,s=start()
    before=digest(m,o)
    old=load_schedule(OLD)
    start_wall=time.monotonic()
    start_cpu=time.process_time()
    rows=[update(m,o,*make_batch(item['rows']),LR) for item in old[-12:]]
    dump(ROOT/'BENCHMARK.json',dict(teachers=sum(r['targets'] for r in rows),optimizer_calls=len(rows),
         wall=time.monotonic()-start_wall,cpu=time.process_time()-start_cpu,
         rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,initial_digest=before,
         config=m.config,initial_checkpoint_sha=read(OLD/'artifacts/A/checkpoint.json')['sha256'],
         free_bytes=__import__('shutil').disk_usage(ROOT).free,stage_state_bytes=read(OLD/'artifacts/A/checkpoint.json')['bytes']))

def inputs():
    plan=read(ROOT/'PLAN.json')
    for name,want in plan['inputs'].items():
        assert sha((ROOT/name).read_bytes())==want,name
    assert sha((ROOT/'SCHEDULE.json.gz').read_bytes())==plan['schedule_sha']
    return plan,load_schedule(ROOT)

def gold_scores(m,prefix,gold):
    if not gold:return []
    assert len(prefix)+len(gold)<=257
    p=m(torch.tensor([(prefix+gold)[:-1]]))[0,len(prefix)-1:].log_softmax(-1)
    refs=p.gather(1,torch.tensor(gold)[:,None]).flatten().tolist()
    assert len(refs)==len(gold) and all(math.isfinite(p) for p in refs)
    return refs

@torch.inference_mode()
def evaluate(m, rows, name, check=False):
    m.eval()
    now=time.monotonic()
    all_cases=[]
    for r in rows:
        p,g=r['prefix'],r['gold']
        refs=gold_scores(m,p,g)
        if check:continue
        out=[]
        steps=[]
        for j in range(min(r['budget'],256-len(p))):
            q=m(torch.tensor([p+out]))[0,-1].log_softmax(-1)
            token=int(q.argmax())
            top=q.topk(5)
            steps.append(dict(top=list(zip(top.indices.tolist(),top.values.exp().tolist())),
                ref=float(q[g[j]]) if j<len(g) else None,
                lf=float(q[16].exp()),eos=float(q[2].exp()),space=float(q[38].exp()),
                digits=float(q[[54+i for i in range(10)]].exp().sum())))
            out.append(token)
            if token==2:break
        first=next((i for i,(a,b) in enumerate(zip(out,g)) if a!=b),None)
        all_cases.append(dict(id=r['id'],panel=r['panel'],gold=g,ref=refs,generated=out,steps=steps,
            stop='EOS' if out[-1]==2 else 'budget',first=first,repeat=repeated_gram(out),**byte_payload(out,PIECES)))
    if check:return
    result=dict(rows=all_cases,seconds=time.monotonic()-now,tokens=sum(len(x['generated']) for x in all_cases))
    p=ROOT/f'{name}.json.gz'
    t=p.with_suffix('.tmp')
    t.write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False,allow_nan=False).encode(),mtime=0))
    t.replace(p)

def save(path,m,o,step,rows,plan,initial_digest):
    path.mkdir(exist_ok=True,parents=True)
    checkpoint=path/'rolling.pt'
    tmp=path/'rolling.tmp'
    torch.save(dict(config=m.config,model=m.state_dict(),optimizer=o.state_dict(),
         torch_rng=torch.get_rng_state(),cursor=step,optimizer_step=step,ledger=rows,
         initial_sha=plan['checkpoint_sha'],initial_digest=initial_digest,
         plan_sha=sha((ROOT/'PLAN.json').read_bytes()),schedule_sha=plan['schedule_sha']),tmp)
    tmp.replace(checkpoint)
    return checkpoint

def restore_here(folder,git_only=False):
    return previous.load_checkpoint(folder,git_only=git_only) if not git_only else git_checkpoint(folder)

def git_checkpoint(folder):
    import io
    repo=ROOT.parents[3]
    manifest=read(folder/'checkpoint.json')
    data=io.BytesIO()
    for part in manifest['chunks']:
        p=(folder/part['path']).relative_to(repo)
        block=subprocess.check_output(['git','show',f'HEAD:{p}'],cwd=repo)
        assert len(block)==part['bytes'] and sha(block)==part['sha256']
        data.write(block)
    assert data.tell()==manifest['bytes'] and sha(data.getbuffer())==manifest['sha256']
    data.seek(0)
    return torch.load(data,weights_only=True,map_location='cpu')

def run():
    plan,schedule=inputs()
    dev=read(ROOT/'DEV.json')
    monitor=read(ROOT/'MONITOR.json')
    regular=[r for r in dev if r['panel']!='independent']+monitor
    stages={int(k):v for k,v in plan['stages'].items()}
    last=max(stages)
    cold,o,ss=start()
    d=digest(cold,o)
    assert d==read(ROOT/'BENCHMARK.json')['initial_digest']
    rolling=ROOT/'rolling'
    recorded=[]
    cursor=INITIAL
    if (rolling/'rolling.pt').exists():
        cp=restore_here(rolling)
        assert cp['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
        cold,o=restore('A',cp)
        cursor,recorded=cp['cursor'],cp['ledger']
        log=(ROOT/'LEDGER.jsonl')
        old=[json.loads(x) for x in log.read_text().splitlines()]
        assert old[:len(recorded)]==recorded
        if len(old)>len(recorded):
            discarded=ROOT/f'discarded-after-{cursor}-{time.time_ns()}.jsonl'
            discarded.write_text(''.join(json.dumps(x)+'\n' for x in old[len(recorded):]))
            log.write_text(''.join(json.dumps(x)+'\n' for x in recorded))
    else:
        evaluate(cold,regular,'A-985',check=True)
        dump(ROOT/'PREFLIGHT.json',dict(decoder_digest=d,passes=True,teacher_forced=sum(bool(r['gold']) for r in regular),
                caption_without_gold=sum(not r['gold'] for r in regular),heldout_token_validation_only=True))
        evaluate(cold,monitor,'monitor-985')
    if cursor==INITIAL:
        expected=json.loads(subprocess.check_output([sys.executable,__file__,'witness']))
    total=plan['initial_targets']+sum(r['targets'] for r in recorded)
    first_index=cursor-INITIAL
    for step,item in enumerate(schedule[first_index:],cursor+1):
        x,y=make_batch(item['rows'])
        wall=time.monotonic();cpu=time.process_time()
        obs=update(cold,o,x,y,LR)
        obs.update(step=step,cpu=time.process_time()-cpu,wall=time.monotonic()-wall,
                   rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        assert obs['targets']==item['targets'] and item['lr']==LR
        recorded.append(obs)
        with (ROOT/'LEDGER.jsonl').open('a') as f:f.write(json.dumps(obs)+'\n')
        total+=obs['targets']
        if step==986:
            actual=digest(cold,o)
            assert actual==expected['digest'] and obs['loss']==expected['loss']
            dump(ROOT/'RESUME.json',dict(expected,match=True,own_retained_step=986,witness_optimizer_calls=1))
        if step%100==0 or step in stages:save(rolling,cold,o,step,recorded,plan,d)
        if step in stages:
            assert total==stages[step]
            # The 1.5M point is a diagnostic. Preserve full states at other points.
            if total>=2_000_000:
                archive_dir=ROOT/'artifacts'/f'A-{step}'
                path=save(archive_dir,cold,o,step,recorded,plan,d)
                previous.archive(path)
            evaluate(cold,regular,f'A-{step}')
        if step%100==0 or step in stages:print(step,total,obs['loss'],flush=True)
    assert int(next(iter(o.state.values()))['step'])==last

def final_holdout():
    plan,_=inputs()
    stages={int(k):v for k,v in plan['stages'].items()}
    archived=[k for k,v in stages.items() if v>=2_000_000]
    assert (ROOT/f'A-{max(stages)}.json.gz').exists()
    assert all((ROOT/'artifacts'/f'A-{k}'/'checkpoint.json').is_file() for k in archived)
    rows=[r for r in read(ROOT/'DEV.json') if r['panel']=='independent']
    wanted=[INITIAL]+[k for k in archived if stages[k]<2_002_000 or k==max(archived)]
    for k in dict.fromkeys(wanted):
        if k==INITIAL:m,_,_=start()
        else:m,_=restore('A',restore_here(ROOT/'artifacts'/f'A-{k}'))
        evaluate(m,rows,f'holdout-{k}')
        print('holdout',k,flush=True)

if __name__=='__main__':
    name=sys.argv[1]
    if name=='benchmark':benchmark()
    elif name=='run':run()
    elif name=='holdout':final_holdout()
    elif name=='witness':
        _,schedule=inputs()
        m,o,_=start()
        info=update(m,o,*make_batch(schedule[0]['rows']),LR)
        print(json.dumps(dict(digest=digest(m,o),loss=info['loss'])))
