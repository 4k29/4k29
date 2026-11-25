"""Score the unchanged PR125 supplemental references after a serialization omission."""
import gzip
import json
import sys
import time
from pathlib import Path

from train import ROOT, BASE, read, dump, sha, setup, torch, load_inputs, make_batch, update, restore, load_checkpoint, digest

def freeze_reference():
    source=BASE/'broad-prose-replay/NEW_DEV.json'
    rows=read(source)
    fixed={r['id']:r for r in read(ROOT/'DEV.json') if r['panel']=='extra'}
    for r in rows:
        item=fixed.pop(r['id'])
        assert item['prefix']==r['prefix']
    assert not fixed
    _,schedule=load_inputs()
    def grams(tokens):
        return zip(*(tokens[i:] for i in range(12)))
    refs={g for r in rows for g in grams(r['prefix']+r['gold'])}
    assert not any(refs.intersection(grams(seq)) for batch in schedule for seq in batch['rows'])
    dump(ROOT/'EXTRA_REFERENCES.json',
         dict(archive_sha=sha(source.read_bytes()),rows=[{k:r[k] for k in ('id','prefix','gold')} for r in rows]))

def score(arm,k,snapshot=None):
    plan,schedule=load_inputs()
    start=time.monotonic()
    m,o=setup(arm)
    receipt=dict(optimizer_replays=0)
    if k==plan['points'][-1]:
        m,o=restore(arm,load_checkpoint(ROOT/'artifacts'/arm))
    elif snapshot:
        saved=torch.load(snapshot,weights_only=True,map_location='cpu')
        assert saved['cursor']==k and saved['plan_sha']==sha((ROOT/'PLAN.json').read_bytes())
        m,o=restore(arm,saved)
    elif k:
        calls=list(map(json.loads,(ROOT/f'{arm}-calls.jsonl').read_text().splitlines()))
        for step, item in enumerate(schedule[:k],1):
            observed=update(m,o,*make_batch(item['rows']),item['lr'])
            assert all(calls[step-1][name]==value for name,value in observed.items()),step
            receipt['optimizer_replays']+=1
            if step%100==0: print('verified replay',arm,step,flush=True)
    receipt.update(state_digest=digest(m,o),seconds=time.monotonic()-start)
    with gzip.open(ROOT/f'{arm}-{k}-eval.json.gz','rt') as f:
        original={r['id']:r for r in json.load(f)['rows'] if r['panel']=='extra'}
    m.eval()
    outputs={}
    with torch.inference_mode():
        for case in read(ROOT/'EXTRA_REFERENCES.json')['rows']:
            key=case['id']
            prefix,gold=case['prefix'],case['gold']
            gen=original.pop(key)
            ref=m(torch.tensor([(prefix+gold)[:-1]]))[0,len(prefix)-1:].log_softmax(-1)
            refs=ref.gather(1,torch.tensor(gold)[:,None]).flatten().tolist()
            first=next((i for i,(a,b) in enumerate(zip(gen['generated'],gold)) if a!=b),None)
            self_logp={}
            if first is not None:
                for j in range(first,min(first+32,len(gold),len(gen['generated']))):
                    p=m(torch.tensor([prefix+gen['generated'][:j]]))[0,-1].log_softmax(-1)
                    assert int(p.argmax())==gen['generated'][j]
                    self_logp[str(j)]=float(p[gold[j]])
            outputs[key]=dict(ref=refs,gold=gold,first=first,self_logp=self_logp)
    assert not original
    dump(ROOT/f'{arm}-{k}-extra.json',dict(scores=outputs,provenance=receipt))

if __name__=='__main__':
    if sys.argv[1]=='freeze':
        freeze_reference()
    else:
        score(sys.argv[1],int(sys.argv[2]),Path(sys.argv[3]) if len(sys.argv)>3 else None)
