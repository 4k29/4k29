"""Build fixed replay schedules from documented MIX-579 teacher windows."""
import gzip
import hashlib
import json
import random
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
REPO = ROOT.parents[3]
FAMILY = BASE/'family-diversity'
PREVIOUS = BASE/'oracle-memorization'

def read(path):
    return json.loads(path.read_text())

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False,indent=1)+'\n')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(path):
    return subprocess.check_output(['git','show',f'HEAD:{path.relative_to(REPO)}'],cwd=REPO)

def consume(order, records, amount, cursor):
    index, offset=cursor
    batch=[]
    while amount:
        i=order[index%len(order)]
        length=len(records[i]['gold'])
        count=min(amount,length-offset)
        batch.append([i,offset,count])
        amount-=count
        offset+=count
        if offset==length:
            index+=1
            offset=0
    return batch,(index,offset)

def prepare():
    train=read(FAMILY/'TRAIN.json')
    baseplan=read(FAMILY/'PLAN.json')
    order=baseplan['arms']['C']
    paths=[BASE/'mixed-retention-study'/f'{n}.json.gz' for n in ('corpus','schedule')]
    archives=[blob(path) for path in paths]
    raw, exposure=[json.loads(gzip.decompress(b)) for b in archives]
    receipts={n:blob(BASE/'modern-corpus'/f'STAIR_{n}.json') for n in
              ('DEV_FAMILIES','SPLIT_AUDIT','LICENSE_RECEIPT','ARCHIVE_RECEIPT')}
    assert 'CC-BY-4.0' in json.loads(receipts['LICENSE_RECEIPT'])['license']
    held=json.loads(receipts['DEV_FAMILIES'])['original_TRAIN_image_ids_reserved_for_DEV']
    excluded={r['id'] for r in json.loads(receipts['SPLIT_AUDIT'])['held']}
    dev=read(BASE/'gv-prose-pilot/EVALUATION_INPUTS.json')['caption']
    dev_ids={r['id'] for r in dev}
    assert len(dev_ids)==32
    pieces=[bytes.fromhex(s) for s in read(BASE/'data/tokenizer.json')['bytes']]
    candidates={}
    for step,batch in enumerate(exposure,1):
        for w in batch:
            i=w['record']
            row=raw[i]
            if row['source']!='stair' or w['start'] or w['length']!=len(row['tokens']):
                continue
            if row['id'] in excluded|dev_ids or row['original_image_id'] in held:
                continue
            tok=row['tokens']
            assert row['license']=='CC-BY-4.0' and tok[:1]==[1] and tok[-1]==2
            assert b''.join(pieces[t] for t in tok[1:-1])==row['text'].encode()
            assert sha(row['text'].encode())==row['source_text_sha256']
            candidates[i]=dict(row,old_record=i,old_update=step,prefix=tok[:1],gold=tok[1:])
    rng=random.Random(12103)
    order_replay=rng.sample(sorted(candidates),len(candidates))
    replay=[]
    families=set()
    texts=set()
    for i in order_replay:
        r=candidates[i]
        if r['family'] in families or r['text'] in texts:
            continue
        families.add(r['family'])
        texts.add(r['text'])
        replay.append(r)
    assert sum(len(r['gold']) for r in replay)>=46500
    # Freeze a small disjoint monitor subset from the same previously seen corpus.
    monitor=replay[-32:]
    replay=replay[:-32]
    assert sum(len(r['gold']) for r in replay)>=46013
    schedule={}
    for arm,divisor in [('B',4),('C',2)]:
        prose_cursor=replay_cursor=(0,0)
        batches=[]
        cumulative=0
        for step in range(300):
            total=307 if step<225 else 306
            n=(cumulative+total)//divisor-cumulative//divisor
            cumulative+=total
            prose,prose_cursor=consume(order,train,total-n,prose_cursor)
            captions,replay_cursor=consume(list(range(len(replay))),replay,n,replay_cursor)
            batches.append(dict(prose=prose,replay=captions,denominator=total))
        schedule[arm]=batches
    schedule['D']=[dict(batch,replay=[]) for batch in schedule['C']]
    used=max(i for b in schedule['C'] for i,_,_ in b['replay'])+1
    save(ROOT/'REPLAY.json',replay[:used])
    save(ROOT/'MONITOR.json',monitor)
    save(ROOT/'SCHEDULE.json',schedule)
    save(ROOT/'PROVENANCE.json',dict(
        archives={str(p.relative_to(BASE)):sha(b) for p,b in zip(paths,archives)},
        receipts={n:sha(b) for n,b in receipts.items()},
        complete_exposed_windows=len(candidates),available_distinct_families=len(families),
        selected=used,monitor=len(monitor),held_dev_ids=sorted(dev_ids),
        partition='Inherited audited PR108 TRAIN. Full previous MIX-579 window only. Monitor distinct from study replay but seen before MIX-579.'))
    save(ROOT/'PLAN.json',dict(baseline=baseplan['baseline'],seed=12103,lr=.0001,clip=1,
        steps=[0,10,20,50,100,200,300],save_steps=[100,300],diagnostic_steps=[0,100,300],
        optimizer='fresh AdamW beta=(.9,.999) eps=1e-8 decay=.01',
        A_reference='PR123 condition C; replay exactly 10 frozen updates separately for missing A-10',
        A_schedule_SHA=sha((FAMILY/'SCHEDULE.json').read_bytes()),train_SHA=sha((FAMILY/'TRAIN.json').read_bytes()),
        eval_SHA=sha((BASE/'gv-prose-pilot/EVALUATION_INPUTS.json').read_bytes()),
        diagnostic='C update 1 masks and shape, eval-mode deterministic component means and budget-weighted mixture, no optimizer',
        denominators='307 x225 then 306 x75, including D, where replay is masked',
        schedule_rule='C/D use identical forward inputs and padding. D masks replay. B/C floor(total seen/divisor) replay increments, balanced ordered streams.',
        evaluation='PR123 full-vocabulary greedy at fixed original limits; separate complete TRAIN reproduction, prose natural two sentences, initial caption retention. No new DEV.',
        frozen={n:sha((ROOT/n).read_bytes()) for n in ('REPLAY.json','MONITOR.json','SCHEDULE.json','PROVENANCE.json')}))
    (ROOT/'PLAN.sha256').write_text(sha((ROOT/'PLAN.json').read_bytes())+'\n')

if __name__=='__main__':
    prepare()
