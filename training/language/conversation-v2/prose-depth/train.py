"""Matched fresh depth-only causal training on CPU."""
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time

import torch
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
sys.path[:0] = [str(BASE), str(BASE.parent)]
from model import Decoder
from eval_core import byte_payload, repeated_gram

torch.set_num_threads(2)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)
CONFIG = dict(vocabulary=3997, context=256, dim=320, heads=4, hidden=1280, dropout=.1)
DEPTHS = dict(A=8, B=14)

def read(p):
    return json.loads(p.read_bytes())

def dump(p, data):
    temporary = p.with_suffix(p.suffix+'.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False)+'\n')
    temporary.replace(p)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def setup(arm):
    torch.manual_seed(131801)
    model = Decoder(dict(CONFIG, layers=DEPTHS[arm]))
    optimizer = torch.optim.AdamW(model.parameters(), lr=.0002, betas=(.9,.999), eps=1e-8, weight_decay=.05)
    torch.manual_seed(131802)
    return model, optimizer

def digest(model, optimizer):
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().numpy().tobytes())
        for value in optimizer.state[p].values():
            h.update(value.numpy().tobytes())
    h.update(torch.get_rng_state().numpy().tobytes())
    return h.hexdigest()

def make_batch(rows):
    size = max(len(row)-1 for row in rows)
    x = torch.zeros((len(rows), size), dtype=torch.long)
    y = torch.full_like(x, -100)
    for i, row in enumerate(rows):
        x[i,:len(row)-1] = torch.tensor(row[:-1])
        y[i,:len(row)-1] = torch.tensor(row[1:])
    return x,y

def update(model, opt, x, y, lr, record=True):
    model.train()
    opt.param_groups[0]['lr'] = lr
    opt.zero_grad(set_to_none=True)
    n = int(y.ne(-100).sum())
    loss = F.cross_entropy(model(x).flatten(0,1), y.flatten(), ignore_index=-100, reduction='sum')/n
    loss.backward()
    norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True))
    before = [p.detach().clone() for p in model.parameters()] if record else []
    opt.step()
    delta = math.sqrt(sum(float((p.detach()-q).square().sum()) for p,q in zip(model.parameters(),before)))
    return dict(targets=n, nonpad=int(x.ne(0).sum()), raw_positions=x.numel(), length=x.shape[1],
                loss=float(loss.detach()), norm=norm, clip=norm>1, delta=delta, lr=lr)

def benchmark():
    positions = [make_batch([[1]+list(range(200,456)) for _ in range(4)]),
                 make_batch([[1]+list(range(200,225)) for _ in range(40)])]
    out = {}
    for arm in DEPTHS:
        m,o = setup(arm)
        start = time.monotonic()
        teacher = sum(update(m,o,*positions[i%2],.0002)['targets'] for i in range(8))
        out[arm] = dict(teachers=teacher, seconds=time.monotonic()-start, discarded_updates=8,
                        parameters=sum(p.numel() for p in m.parameters()))
    dump(ROOT/'BENCHMARK.json',out)

def save_state(path, m,o,k,ledger,plan):
    path.mkdir(exist_ok=True, parents=True)
    checkpoint = path/'rolling.pt'
    tmp = checkpoint.with_suffix('.tmp')
    torch.save(dict(config=m.config,model=m.state_dict(),optimizer=o.state_dict(),torch_rng=torch.get_rng_state(),
                    cursor=k,optimizer_step=k,plan_sha=sha((ROOT/'PLAN.json').read_bytes()),
                    schedule_sha=plan['schedule_sha'],ledger=ledger),tmp)
    tmp.replace(checkpoint)
    return checkpoint

def archive(checkpoint):
    folder=checkpoint.parent
    h=hashlib.sha256()
    parts=[]
    with checkpoint.open('rb') as file:
        while block:=file.read(32*1024*1024):
            part=f'part-{len(parts):03}.bin'
            (folder/part).write_bytes(block)
            h.update(block)
            parts.append(dict(path=part,sha256=sha(block),bytes=len(block)))
    dump(folder/'checkpoint.json',dict(sha256=h.hexdigest(),chunks=parts,bytes=checkpoint.stat().st_size))
    checkpoint.unlink()

def load_checkpoint(folder, git_only=False):
    rolling=folder/'rolling.pt'
    if not git_only and rolling.exists():
        return torch.load(rolling,weights_only=True,map_location='cpu')
    import io
    import subprocess
    manifest=read(folder/'checkpoint.json')
    full=io.BytesIO()
    for part in manifest['chunks']:
        p=folder/part['path']
        if git_only:
            repo=ROOT.parents[3]
            block=subprocess.check_output(['git','show',f'HEAD:{p.relative_to(repo)}'],cwd=repo)
        else:
            block=p.read_bytes()
        assert len(block)==part['bytes'] and sha(block)==part['sha256']
        full.write(block)
    assert full.tell()==manifest['bytes'] and sha(full.getbuffer())==manifest['sha256']
    full.seek(0)
    return torch.load(full,weights_only=True,map_location='cpu')

def restore(arm,saved):
    m,o=setup(arm)
    assert saved['config']==m.config
    m.load_state_dict(saved['model'])
    o.load_state_dict(saved['optimizer'])
    torch.set_rng_state(saved['torch_rng'])
    return m,o

def load_inputs():
    plan=read(ROOT/'PLAN.json')
    for name,value in plan['inputs'].items():
        assert sha((ROOT/name).read_bytes())==value, name
    schedule=json.loads(gzip.decompress((ROOT/'SCHEDULE.json.gz').read_bytes()))
    assert sha((ROOT/'SCHEDULE.json.gz').read_bytes())==plan['schedule_sha']
    return plan,schedule

def evaluation(m, arm, k, terminal=False):
    cases=read(ROOT/'DEV.json')
    pieces=[bytes.fromhex(t) for t in read(BASE/'data/tokenizer.json')['bytes']]
    rows=[]
    m.eval()
    start=time.monotonic()
    with torch.inference_mode():
        for r in cases:
            if (r['panel']=='independent') and not terminal: continue
            prefix,gold=r['prefix'],r['gold']
            n=min(r['budget'],256-len(prefix))
            if gold:
                logp=m(torch.tensor([(prefix+gold)[:-1]]))[0,len(prefix)-1:].log_softmax(-1)
                ref=logp.gather(1,torch.tensor(gold)[:,None]).flatten().tolist()
            else:
                ref=[]
            generated=[]
            steps=[]
            for j in range(n):
                p=m(torch.tensor([prefix+generated]))[0,-1].log_softmax(-1)
                token=int(p.argmax())
                top=p.topk(5)
                steps.append(dict(top=list(zip(top.indices.tolist(),top.values.exp().tolist())),
                                  ref=float(p[gold[j]]) if j<len(gold) else None,
                                  eos=float(p[2].exp()),lf=float(p[16].exp()),space=float(p[38].exp())))
                generated.append(token)
                if token==2: break
            first=next((j for j,(a,b) in enumerate(zip(generated,gold)) if a!=b),None)
            rows.append(dict(id=r['id'],panel=r['panel'],ref=ref,gold=gold,generated=generated,
                             stop='EOS' if generated[-1]==2 else 'budget',first=first,repeat=repeated_gram(generated),
                             steps=steps,**byte_payload(generated,pieces)))
    result=dict(rows=rows,seconds=time.monotonic()-start,tokens=sum(len(r['generated']) for r in rows))
    (ROOT/f'{arm}-{k}-eval.json.gz').write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False).encode(),mtime=0))

def run(arm):
    import subprocess
    plan,schedule=load_inputs()
    ends=set(plan['points'])
    folder=ROOT/'artifacts'/arm
    m,o=setup(arm)
    start=0
    ledger=[]
    if (folder/'rolling.pt').exists():
        saved=load_checkpoint(folder)
        assert saved['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
        m,o=restore(arm,saved)
        start=saved['cursor']
        ledger=saved['ledger']
    if start==0:
        evaluation(m,arm,0)
    witness_at=plan['witness']
    witness_path=ROOT/f'{arm}-resume.json'
    for n,item in enumerate(schedule[start:],start+1):
        x,y=make_batch(item['rows'])
        start_wall=time.monotonic()
        start_cpu=time.process_time()
        row=update(m,o,x,y,item['lr'])
        row.update(step=n,wall=time.monotonic()-start_wall,cpu=time.process_time()-start_cpu,
                   rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        assert row['targets']==item['targets']
        ledger.append(row)
        with (ROOT/f'{arm}-calls.jsonl').open('a') as log:
            log.write(json.dumps(row)+'\n')
        if n==witness_at+1:
            expected=json.loads(subprocess.check_output([sys.executable,__file__,'witness',arm]))
            actual=digest(m,o)
            assert actual==expected
            dump(witness_path,dict(step=n,digest=actual,match=True,discarded_updates=1))
        if n%25==0 or n in ends:
            checkpoint=save_state(folder,m,o,n,ledger,plan)
        if n in ends:
            evaluation(m,arm,n,n==len(schedule))
        if n%25==0 or n in ends:
            print(arm,n,sum(r['targets'] for r in ledger),round(row['loss'],4),flush=True)
    archive(checkpoint)

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='benchmark':
        benchmark()
    elif mode=='witness':
        arm=sys.argv[2]
        plan,schedule=load_inputs()
        saved=load_checkpoint(ROOT/'artifacts'/arm)
        assert saved['cursor']==plan['witness']
        m,o=restore(arm,saved)
        row=schedule[saved['cursor']]
        update(m,o,*make_batch(row['rows']),row['lr'])
        print(json.dumps(digest(m,o)))
    elif mode=='run':
        run(sys.argv[2])
