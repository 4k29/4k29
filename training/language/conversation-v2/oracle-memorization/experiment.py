"""CPU-only deterministic small-corpus study."""
from freeze import P,V,read,save,sha
import gzip,hashlib,io,json,os,random,shutil,sys
sys.path[:0]=[str(V),str(V/'foundation-data/research')]
import torch
from core import decoder,causal_ce,clip_grad_accurate,digest,trajectory
from zero_update_preflight import load_checkpoint
plan=read(P/'PLAN.json')
assert sha(P/'PLAN.json')==(P/'PLAN.sha256').read_text().strip()
for f,h in plan['inputs'].items():assert sha(V/f)==h
train=read(P/'TRAIN.json')
torch.set_num_threads(2)
torch.use_deterministic_algorithms(True)
def initial(name):
    ref=plan['models'][name]
    state=load_checkpoint(V/ref['path'],ref['sha'])['trajectory']
    m=decoder(state['config']);m.load_state_dict(state['model'])
    return m
def optimizer(m):return torch.optim.AdamW(m.parameters(),lr=plan['lr'],weight_decay=.01)
def update(m,o,arm,k):
    rows=train[3*((k-1)%4):3*((k-1)%4)+3]
    seqs=[r['prefix']+r['gold'] for r in rows]
    batch=torch.nn.utils.rnn.pad_sequence(list(map(torch.tensor,seqs)),batch_first=True)
    y=batch[:,1:].clone();y[y==0]=-100
    if arm=='B':
        for i,r in enumerate(rows):y[i,:len(r['prefix'])-1]=-100
    assert int((y!=-100).sum())==sum(len(r['gold']) if arm=='B' else len(s)-1 for r,s in zip(rows,seqs))
    o.zero_grad(set_to_none=True)
    loss=causal_ce(m(batch[:,:-1]),y);loss.backward()
    norm=clip_grad_accurate(m.parameters(),1.)
    first=next(m.parameters());before=first.detach().clone()
    o.step()
    assert all(torch.isfinite(p).all() for p in m.parameters())
    return dict(step=k,ids=[r['id'] for r in rows],targets=int((y!=-100).sum()),loss=loss.item(),norm=norm.item(),clipped=bool(norm>1),embedding_delta=(first-before).detach().norm().item())
def checkpoint(m,o,k,log,folder):
    folder.mkdir(parents=True,exist_ok=False)
    obj=trajectory(m,o,random.Random(plan['seed']),list(range(12)),k%4,log,k)
    buf=io.BytesIO();torch.save({'trajectory':obj},buf);buf.seek(0)
    whole=hashlib.sha256();parts=[]
    while b:=buf.read(32<<20):
        dest=folder/f'part-{len(parts):03}.bin'
        dest.write_bytes(b);whole.update(b)
        parts.append(dict(path=dest.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    tmp=folder/'manifest.tmp';save(tmp,dict(bytes=buf.tell(),chunks=parts,sha256=whole.hexdigest()));tmp.rename(folder/'checkpoint.json')
def restore(folder):
    f=folder/'checkpoint.json'
    st=load_checkpoint(f,read(f)['sha256'])['trajectory']
    m=decoder(st['config']);m.load_state_dict(st['model']);o=optimizer(m);o.load_state_dict(st['optimizer']);torch.set_rng_state(st['torchRng'])
    return m,o,st
def stage(arm,start,end):
    root=P/'artifacts'
    if start:
        m,o,st=restore(root/f'{arm}-{start}');log=st['history']
        assert st['cursor']==start%4 and len(log)==start
    else:
        m=initial('initial');o=optimizer(m);torch.manual_seed(plan['seed']);log=[]
        assert not o.state
    m.train()
    for k in range(start+1,end+1):
        row=update(m,o,arm,k);log.append(row)
        if k==101:
            expected=read(P/f'{arm}-probe.json')
            assert row==expected['row'] and digest([m.state_dict(),o.state_dict(),torch.get_rng_state()])==expected['digest']
    checkpoint(m,o,end,log,root/f'{arm}-{end}')
    save(P/f'{arm}-ledger.json',log)
    if end==100:
        row=update(m,o,arm,101)
        save(P/f'{arm}-probe.json',dict(row=row,digest=digest([m.state_dict(),o.state_dict(),torch.get_rng_state()])))
if __name__=='__main__':
    if sys.argv[1]=='probe':
        assert shutil.disk_usage(P).free>2_000_000_000
        for arm in 'AB':
            m=initial('initial');o=optimizer(m);torch.manual_seed(plan['seed']);r=update(m,o,arm,1)
            assert all(torch.isfinite(s['exp_avg']).all() and torch.isfinite(s['exp_avg_sq']).all() for s in o.state.values())
            save(P/f'{arm}-preflight.json',r)
    else:stage(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
