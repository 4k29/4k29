import json,gzip,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
V=P.parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    files=[V/'gv-prose-pilot/corpus-C.jsonl.gz',V/'gv-collapse-diagnostic/ADDITIONAL.jsonl.gz']
    pool=[r for f in files for r in map(json.loads,gzip.open(f))]
    ev=V/'gv-prose-pilot/EVALUATION_INPUTS.json'
    dev=read(ev)['prose']
    pieces=[bytes.fromhex(s) for s in read(V/'data/tokenizer.json')['bytes']]
    selected=[]
    for i in [3,8,10,21,29,62,67,68,70,72,73,74]:
        r=pool[i]; seq=r['tokens']; first=r['text'].split('。')[0]+'。'
        assert b''.join(pieces[t] for t in seq)==r['text'].encode()
        n=next(k for k in range(2,len(seq)) if b''.join(pieces[t] for t in seq[:k])==first.encode())
        assert r['family'] not in {d['family'] for d in dev} and r['text'][len(first):].count('。')>=2 and 2 not in seq
        selected.append(dict(id=r['id'],family=r['family'],source=r['source'],source_url=r['source_url'],license=r['license'],text_SHA=r['text_SHA'],index=i,prefix=seq[:n],gold=seq[n:],category=r['category']))
    assert len({s['family'] for s in selected})==len(selected)
    save(P/'TRAIN.json',selected)
    save(P/'PLAN.json',dict(inputs={str(f.relative_to(V)):sha(f) for f in files+[ev,V/'data/tokenizer.json',P/'TRAIN.json']},models=read(V/'gv-collapse-diagnostic/PLAN.json')['models'],
      oracle=[0,1,4,8,16,32],oracle_free_budget=112,train_eval='First sentence; free budget = number of remaining excerpt tokens. EOS not taught, no inference of document ending.',dev_eval='Original 128 token budget and caption32 original limits.',seed=12103,batch=3,order='fixed TRAIN order; cycle four batches 75 times',updates=[0,100,300],lr=0.0001,clip=1,adam='fresh AdamW betas .9/.999 eps 1e-8 decay .01',loss='mean over active shifted positions; A all, B continuation only',primary='Two newly generated complete, natural, connected topical sentences; reference mismatch alone is not failure. Ignore supplied tokens, reject loops/nonsense. Log first mechanically repeated autonomous 4gram separately from harmful repetition.',stop='Stop on nonfinite gradient/parameters, failed resume equivalence, digest or disk failure. No outcome-dependent changes.'))
    (P/'PLAN.sha256').write_text(sha(P/'PLAN.json')+'\n')
