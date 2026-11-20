"""Freeze nested prose corpora and unchanged PR124 replay windows."""
import gzip
import hashlib
import itertools
import json
import random
import re
import subprocess
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
REPO=ROOT.parents[3]
OLD=BASE/'replay-study'
FAMILY=BASE/'family-diversity'

def read(path):
    return json.loads(path.read_text())

def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def archive(path):
    return subprocess.check_output(['git','show',f'HEAD:{(BASE/path).relative_to(REPO)}'],cwd=REPO)

def key(family):
    return re.sub(r'\s+','',family.split('|')[-1])

def grams(tokens,n=12):
    return {tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)}

def prepare():
    corpus_path='modern-corpus/next-foundation/corpus.jsonl.gz'
    schedule_path='modern-corpus/next-foundation/schedule.json.gz'
    corpus_blob,schedule_blob=map(archive,(corpus_path,schedule_path))
    old_schedule=json.loads(gzip.decompress(schedule_blob))
    exposure=defaultdict(set)
    for batch in old_schedule['batches']:
        for row in batch:
            exposure[row['record']].update(range(row['start']+1,row['start']+row['length']))
    held=read(BASE/'gv-prose-pilot/EVALUATION_INPUTS.json')['prose']
    tokens=[bytes.fromhex(x) for x in read(BASE/'data/tokenizer.json')['bytes']]
    existing=read(FAMILY/'TRAIN.json')
    original=read(FAMILY/'PLAN.json')['arms']['C']
    chosen=[dict(existing[i],archive='PR119/120',historical='previous research approval; MIX-579 exposure unresolved here') for i in original]
    baseline=read(OLD/'PLAN.json')
    schedule=read(OLD/'SCHEDULE.json')['C']
    excluded={key(r['family']) for r in held+chosen}
    excluded.update(['初めての街に到着する','キャンプ飯','子ども連れの旅','カーペット','買う',
                     '四国八十八箇所巡礼','歴史旅','園芸','調(音楽)','香港の歴史'])
    reserved=excluded-{key(r['family']) for r in held+chosen}
    bad=re.compile(r'^(また、|例えば|たとえば|このように|そのため|したがって|しかし|他、|上記|以下|次に)|https?://|\{\{|\[\[|\|\|')
    unsafe_topic=re.compile(r'化学|生物|軍|医学|薬|銃|兵器|爆発|テロ|病|有機|高校理科')
    occupied=set().union(*(grams(r['tokens']) for r in held))
    occupied.update(set().union(*(grams(r['prefix']+r['gold']) for r in chosen)))
    rng=random.Random(12103)
    pool=[]
    for i,line in enumerate(gzip.decompress(corpus_blob).splitlines()):
        row=json.loads(line)
        if row['source'] not in ('jawikibooks','jawikivoyage') or str(row.get('split')).upper()!='TRAIN':
            continue
        family=key(row['family']);text=row['text']; seq=row['tokens']
        if family in excluded-reserved or unsafe_topic.search(family) or bad.search(text) or not text.endswith('。'):
            continue
        if re.search(r'[–•]|^.{1,8}[:：]|\n.{1,8}[:：]',text):continue
        if text.count('。')<3 or len(seq)>256 or text.count('「')!=text.count('」'):
            continue
        if b''.join(tokens[t] for t in seq)!=text.encode() or set(seq[1:]) & {0,1,2,3,4}:
            continue
        boundary=len((text.split('。',1)[0]+'。').encode())
        ends=list(itertools.accumulate(len(tokens[t]) for t in seq))
        if boundary not in ends:
            continue
        split=ends.index(boundary)+1
        if split<10 or len(seq)-split<35 or len(seq)-split>220 or not row.get('provenance'):
            continue
        pool.append(dict(id=row['id'],family=family,source=row['source'],title=row['title'],text=text,
                         prefix=seq[:split],gold=seq[split:],prior_positions=[k-split for k in sorted(exposure[i]) if split<=k<len(seq)],
                         source_record=i,archived_metadata={k:v for k,v in row.items() if k not in ('text','tokens')},
                         text_sha=sha(text.encode()),archive=corpus_path))
    rng.shuffle(pool)
    dev=[]
    for family in sorted(reserved):
        for r in pool:
            if r['family']==family and not grams(r['prefix']+r['gold'])&occupied:
                dev.append(r)
                occupied.update(grams(r['prefix']+r['gold']))
                break
    groups=defaultdict(list)
    used=Counter()
    for r in pool:
        if r['family'] not in reserved:
            groups[r['family']].append(r)
    families=list(groups)
    rng.shuffle(families)
    cuts={}
    size=sum(len(r['gold']) for r in chosen)
    while size<46013:
        added=False
        for family in families:
            if used[family]>=1000:
                continue
            while groups[family]:
                r=groups[family].pop()
                seq=r['prefix']+r['gold']
                seen=grams(seq)
                if seen&occupied:
                    continue
                available=len(r['gold'])
                if 'B' not in cuts and size>=13000:
                    cuts['B']=list(range(len(chosen)))
                remaining=46013-size
                used_tokens=min(available,remaining)
                r['eligible_targets']=used_tokens
                chosen.append(r)
                occupied.update(seen)
                size+=used_tokens
                used[family]+=used_tokens
                added=True
                break
            if size==46013:
                break
        if not added:
            break
    cuts['C']=list(range(len(chosen)))
    assert size>=26000 and len(dev)>=5 and 'B' in cuts
    batches={}
    for arm,indices in cuts.items():
        pointer=offset=0
        batch=[]
        for old in schedule:
            amount=sum(n for _,_,n in old['prose'])
            selected=[]
            while amount:
                i=indices[pointer%len(indices)]
                length=chosen[i].get('eligible_targets',len(chosen[i]['gold']))
                count=min(amount,length-offset)
                selected.append([i,offset,count])
                offset+=count
                amount-=count
                if offset==length:
                    pointer+=1
                    offset=0
            batch.append(dict(old,prose=selected))
        batches[arm]=batch
    for row in dev:
        row.update(panel='new_prose',maxNewTokens=min(128,257-len(row['prefix'])),historical='PR105 corpus, past schedule overlap measured')
    save(ROOT/'TRAIN.json',chosen)
    save(ROOT/'NEW_DEV.json',dev)
    save(ROOT/'SCHEDULE.json',batches)
    save(ROOT/'PLAN.json',dict(baseline=baseline['baseline'],steps=baseline['steps'],seed=12103,
        fixed_replay_SHA=sha((OLD/'SCHEDULE.json').read_bytes()),replay_SHA=sha((OLD/'REPLAY.json').read_bytes()),
        data_archive_SHA=sha(corpus_blob),history_schedule_SHA=sha(schedule_blob),arms=cuts,
        prior_history='Counts use PR105 B schedule position indices. Further earlier histories and replay-period source reuse remain unresolved for positions with no match.',
        evaluation='PR124 fixed prose18/caption32/common14, source-held DEV greedy; sampled TRAIN teacher forcing.',
        frozen={f:sha((ROOT/f).read_bytes()) for f in ('TRAIN.json','NEW_DEV.json','SCHEDULE.json')}))
    (ROOT/'PLAN.sha256').write_text(sha((ROOT/'PLAN.json').read_bytes())+'\n')
    print(size,len(chosen),len(dev),{a:len(ids) for a,ids in cuts.items()})

if __name__=='__main__':
    prepare()
