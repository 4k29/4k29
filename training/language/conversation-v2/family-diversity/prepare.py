"""Freeze nested conditions and exact per-step continuation masks."""
import gzip
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
PREVIOUS = BASE / 'oracle-memorization'

def read(path):
    return json.loads(path.read_text())

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare():
    paths = ['gv-prose-pilot/corpus-C.jsonl.gz', 'gv-collapse-diagnostic/ADDITIONAL.jsonl.gz']
    pool = [row for path in paths for row in map(json.loads, gzip.open(BASE/path))]
    train = read(PREVIOUS/'TRAIN.json')
    pieces = [bytes.fromhex(s) for s in read(BASE/'data/tokenizer.json')['bytes']]
    for index in (6, 9):
        source = pool[index]
        tokens = source['tokens']
        first = (source['text'].split('。')[0] + '。').encode()
        split = next(i for i in range(1,len(tokens)) if b''.join(pieces[t] for t in tokens[:i]) == first)
        train.append(dict(index=index, prefix=tokens[:split], gold=tokens[split:], **{
            k: source[k] for k in ('id','family','source','source_url','license','text_SHA','category')}))
    eval_path = BASE/'gv-prose-pilot/EVALUATION_INPUTS.json'
    dev = read(eval_path)['prose']
    assert len({r['family'] for r in train}) == 14
    for row in train:
        original = pool[row['index']]
        tokens = row['prefix'] + row['gold']
        assert tokens == original['tokens'] and b''.join(pieces[t] for t in tokens) == original['text'].encode()
        assert len(tokens)<=256 and not set(tokens[1:]) & {0,1,2,3,4}
        assert original['family'] not in {r['family'] for r in dev}
        assert all(original['text'] not in r['text'] and r['text'] not in original['text'] for r in dev)
    order = random.Random(12103).sample(range(12),12)
    # Preserve the twelve previously read families as the middle condition.
    low = []
    for source in sorted(set(r['source'] for r in train[:12])):
        count = sum(r['source']==source for r in train[:12])
        low.extend([i for i in order if train[i]['source']==source][:round(count/2)])
    arms = dict(A=low,B=order,C=order+[12,13])
    schedule = {}
    for arm, indices in arms.items():
        pointer = 0
        offset = dict.fromkeys(indices,0)
        batches = []
        for step in range(300):
            budget = 307 if step<225 else 306
            batch = []
            while budget:
                i = indices[pointer % len(indices)]
                length = len(train[i]['gold'])
                start = offset[i]
                count = min(length-start,budget)
                batch.append([i,start,count])
                offset[i] = (start+count)%length
                budget -= count
                pointer += offset[i]==0
            batches.append(batch)
        schedule[arm] = batches
    save(ROOT/'TRAIN.json',train)
    save(ROOT/'SCHEDULE.json',schedule)
    save(ROOT/'SOURCE_AUDIT.json',[{k:v for k,v in pool[r['index']].items() if k not in ('tokens','text')} for r in train])
    plan = dict(arms=arms, seed=12103, lr=.0001, clip=1., steps=[0,20,50,100,200,300], budget=92025,
        objective='Mean continuation CE only. Preserve exact original prefix and prior continuation; no synthesized EOS.',
        matching='Stratified by source. A selected within PR122 pool using seed. B uses PR122 pool. C adds geography and engineering.',
        schedule='Sequential cycling of source tokens across batches with exact equal per-update mask counts. A split record may expose input twice but a target has one loss exposure per cycle.',
        evaluation='Use fixed prose18 and caption32 with original limits, TRAIN continuation length. Whole-vocab greedy. Two novel coherent topical sentences; caption base 21 retention.',
        baseline=read(PREVIOUS/'PLAN.json')['models']['initial'],
        inputs={f:sha(BASE/f) for f in paths+['data/tokenizer.json','gv-prose-pilot/EVALUATION_INPUTS.json']},
        frozen={f:sha(ROOT/f) for f in ('TRAIN.json','SCHEDULE.json','SOURCE_AUDIT.json')})
    save(ROOT/'PLAN.json',plan)
    (ROOT/'PLAN.sha256').write_text(sha(ROOT/'PLAN.json')+'\n')

if __name__=='__main__':
    prepare()
