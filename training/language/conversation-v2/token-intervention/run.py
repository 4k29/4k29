"""Single forced token; unmodified greedy after it, followed by causal replay."""
import gzip, json, sys, hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
V=P.parent
sys.path[:0]=[str(V),str(V/'foundation-data/research')]
import torch
from core import decoder
from zero_update_preflight import load_checkpoint

def recurrence(seq, j):
    seen={}
    for k in range(len(seq)-3):
        gram=tuple(seq[k:k+4])
        if k>j and gram in seen:
            return dict(start=k,first=seen[gram],distance=k-j,tokens=list(gram))
        seen.setdefault(gram,k)

def main():
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    plan=json.loads((P/'PLAN.json').read_text())
    archived=json.load(gzip.open(V/'gv-collapse-diagnostic/DIAGNOSTIC.json.gz'))['cases']
    cases={(x['model'],x['id']):x for x in archived}
    pieces=[bytes.fromhex(s) for s in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
    blanks=[i for i,p in enumerate(pieces) if p and set(p)=={32}]
    out=[]
    with torch.inference_mode():
        for name,ref in plan['models'].items():
            state=load_checkpoint(V/ref['path'],ref['sha'])
            model=decoder(state['trajectory']['config']).eval()
            model.load_state_dict(state['trajectory']['model'])
            del state
            assert not any(m.training for m in model.modules())
            for e in plan['selection']:
                if e['model']!=name or not e['rank']:continue
                x=cases[name,e['id']]
                j=e['j']
                seq=x['generated'][:j]+[e['token']]
                prefix=x['prefix']
                steps=[]
                while len(seq)<128:
                    hist=prefix+seq
                    assert len(hist)<=256
                    logits=model(torch.tensor([hist]))[0,-1]
                    prob=logits.double().softmax(0)
                    t=int(logits.argmax())
                    steps.append(dict(t=t,p=float(prob[t]),eos=float(prob[2]),lf=float(prob[16]),space=float(prob[blanks].sum())))
                    seq.append(t)
                    if t==2:break
                replay=model(torch.tensor([prefix+seq[:-1]]))[0,len(prefix)-1:]
                ids=replay.argmax(-1).tolist()
                assert ids[:j+1]==x['generated'][:j+1] and ids[j+1:]==seq[j+1:]
                assert abs(float(replay[j].double().softmax(0)[e['token']])-e['p'])<1e-5
                raw=b''.join(pieces[t] for t in seq)
                out.append(dict(model=name,id=e['id'],arm=e['arm'],j=j,tokens=seq,steps=steps,
                    replay_argmax=ids,recurrence=recurrence(seq,j),raw_hex=raw.hex(),text=raw.decode(errors='replace'),
                    suffix=b''.join(pieces[t] for t in seq[j+1:]).decode(errors='replace'),
                    stop='EOS' if seq[-1]==2 else 'limit',forwards=len(steps)+1))
    (P/'RESULTS.json.gz').write_bytes(gzip.compress(json.dumps(dict(optimizer_calls=0,forwards=sum(x['forwards'] for x in out),cases=out),ensure_ascii=False,separators=(',',':')).encode(),mtime=0))

if __name__=='__main__':main()
