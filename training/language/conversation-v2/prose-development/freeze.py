"""Freeze the continuation stream and evaluation sources before updating weights."""
import collections
import gzip
import hashlib
import json
import random
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OLD=BASE/'prose-depth'
sys.path.insert(0,str(BASE))
from new_tokenizer import Encoder

CORPUS=BASE/'modern-corpus/next-foundation/corpus.jsonl.gz'
REVIEWED=set('根付 鉋 紙縒 囲炉裏 桶 千代紙 短冊 印籠 打楽器 音叉 砥石 彫刻刀 犬ぞり 譜面台 鍵盤楽器 モザイク 笛 墨 口琴 アコーディオン 横笛 西陣織 風車 太鼓 鐘 砂時計 撥 草木染め 足袋 旅籠 下駄 草履 手押し車 顕微鏡 双眼鏡 火打石 木琴 漏斗 万華鏡 水準器'.split())
# Distinct instruments with analogous descriptions are allowed; these near-pairs
# are conservatively represented by one title in the primary panel.
REVIEWED-={'横笛','撥','打楽器','草履','印籠','千代紙'}
SOURCES={'stair','jaquad','jawikibooks','jawikivoyage','jma'}
HIST=['diverse-foundation/corpus.jsonl.gz','foundation-absorption-study/corpus.jsonl.gz',
      'mixed-retention-study/corpus.json.gz','mixed-volume-study/corpus.json.gz',
      'pretraining-scale/corpus.jsonl.gz','broad-prose-replay/TRAIN.json','prose-budget-scale/TRAIN.json']

def read(p):return json.loads(p.read_bytes())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def grams(ids):return zip(*(ids[i:] for i in range(12)))
def norm(s):return ''.join(unicodedata.normalize('NFKC',s).split()).casefold()
def labels(r):
    fields=[r[k] for k in ('family','title','id') if isinstance(r.get(k),str)]
    return {norm(x) for v in fields for x in (v,v.split('|')[-1].split('/')[0])}

def blob(p):
    if p.exists():return p.read_bytes()
    repo=ROOT.parents[3]
    return subprocess.check_output(['git','show',f'HEAD:{p.relative_to(repo)}'],cwd=repo)

def items(p,raw):
    raw=gzip.decompress(raw) if p.name.endswith('.gz') else raw
    if p.name.endswith('.jsonl.gz'):return map(json.loads,raw.splitlines())
    rows=json.loads(raw)
    return rows['rows'] if isinstance(rows,dict) else rows

def dev_sets(pieces,enc,source):
    legacy=read(OLD/'DEV.json')
    extra={r['id']:r for r in read(OLD/'EXTRA_REFERENCES.json')['rows']}
    for row in legacy:
        if row['panel']=='independent':row['panel']='depth24'
        if row['panel']=='extra':
            assert row['prefix']==extra[row['id']]['prefix']
            row['gold']=extra[row['id']]['gold']
        row['gold']=row['gold'][:257-len(row['prefix'])]
        assert row['panel']=='caption' or row['gold']
    first=[r['id'] for r in legacy]
    candidate={}
    under=collections.defaultdict(set)
    by_title=collections.defaultdict(set)
    rejected=collections.defaultdict(set)
    old=legacy+read(BASE/'prose-teacher-distribution/DEV.json')['cases']+read(BASE/'prose-teacher-distribution/DEV_PART2.json')['cases']
    excluded=set().union(*(labels(r) for r in old))
    protected_grams=set().union(*(set(grams(r.get('prefix',r.get('full',[]))+r['gold'])) for r in old))
    for record in read(ROOT/'SOURCES.json'):
        title=record.get('title')
        if title not in REVIEWED or not record.get('revisions'):continue
        text=record.get('extract','').strip()
        sentences=[s+'。' for s in text.split('。')[:-1]]
        if len(sentences)<3:continue
        start=enc(sentences[0])
        gold=enc(''.join(sentences[1:3]))
        complete=''.join(sentences[:3])
        if len(start)+len(gold)>255 or start+gold!=enc(complete):continue
        assert b''.join(pieces[t] for t in start+gold).decode()==complete
        key=f'wiki-development:{title}'
        if norm(title) in excluded or not protected_grams.isdisjoint(grams(start+gold)):
            rejected[key].add('earlier DEV match')
            continue
        rev=record['revisions'][0]['revid']
        candidate[key]=dict(id=key,title=title,family=title,panel='independent',prefix=[1]+start,gold=gold,budget=96,
                            text=complete,sha=sha(complete.encode()),revision=rev,license='CC BY-SA 4.0',
                            url=f'https://ja.wikipedia.org/w/index.php?oldid={rev}',
                            attribution=f'https://ja.wikipedia.org/wiki/{title}?action=history')
        by_title[norm(title)].add(key)
        for gram in grams(start+gold):under[gram].add(key)
    archives={}
    for path in [CORPUS]+[BASE/x for x in HIST]:
        raw=source if path==CORPUS else blob(path)
        archives[str(path.relative_to(BASE))]=sha(raw)
        for row in items(path,raw):
            tokens=row.get('tokens') or row['prefix']+row['gold']
            for x in labels(row)&by_title.keys():
                for key in by_title[x]:rejected[key].add('family:'+str(path.relative_to(BASE)))
            for gram in grams(tokens):
                for key in under.get(gram,()):rejected[key].add('12-token:'+str(path.relative_to(BASE)))
    for row in candidate.values():
        if row['id'] in rejected:continue
        legacy.append(row)
        protected_grams.update(grams(row['prefix']+row['gold']))
        excluded.update(labels(row))
    dump(ROOT/'DEV_AUDIT.json',dict(archives=archives,rejected={k:sorted(v) for k,v in rejected.items()},
         old_ids=first,independent=[r['id'] for r in legacy if r['panel']=='independent'],
         method='Source text screening, normalized article/family and contiguous 12-token check; no complete semantic or historical exposure guarantee.'))
    return legacy,excluded,protected_grams

def batches(rows):
    pools=collections.defaultdict(list)
    totals=collections.Counter()
    out=[]
    for r in rows:
        width=(len(r[2])-2)//24
        pools[width].append(r)
        totals[width]+=len(r[2])-1
        if totals[width]>=990:
            out.append(pools.pop(width))
            totals[width]=0
    out.extend(pools.values())
    return out

def main():
    tok=read(BASE/'data/tokenizer.json')
    pieces=list(map(bytes.fromhex,tok['bytes']))
    source=CORPUS.read_bytes()
    dev,protected,protect_tokens=dev_sets(pieces,Encoder(tok),source)
    dump(ROOT/'DEV.json',dev)
    old=json.loads(gzip.decompress((OLD/'SCHEDULE.json.gz').read_bytes()))
    seen_positions=set()
    old_ids=set()
    old_windows=set()
    for b in old:
        for pair,seq in zip(b['ids'],b['rows'],strict=True):
            key,offset=pair
            old_ids.add(key)
            assert tuple(pair) not in seen_positions
            seen_positions.add(tuple(pair))
            old_windows.add(tuple(seq))
    old_index=read(OLD/'TRAIN_INDEX.json')
    original_text_hashes={r['body_sha'] for r in old_index.values()}
    protected_images=set(read(BASE/'modern-corpus/STAIR_DEV_FAMILIES.json')['original_TRAIN_image_ids_reserved_for_DEV'])
    prior_ids=old_ids
    new_text_hashes=set()
    groups=collections.defaultdict(list)
    meta={}
    excluded_counts=collections.Counter()
    length_counts=collections.Counter()
    overlap_bases=set()
    for row in items(CORPUS,source):
        src=row['source']
        if src not in SOURCES:continue
        ids=row['tokens']
        key=row['id']
        raw=row['text']
        text_sha=sha(raw.encode())
        if key in meta or (key not in prior_ids and text_sha in original_text_hashes) or text_sha in new_text_hashes:
            excluded_counts['same_text']+=1
            continue
        # Check existing and fresh evaluations against all proposed new positions.
        if labels(row)&protected or row.get('original_image_id') in protected_images or not protect_tokens.isdisjoint(grams(ids)):
            excluded_counts['dev_overlap']+=1
            continue
        if src!='stair' and raw.count('。')<2:
            excluded_counts['less_than_two_sentences']+=1
            continue
        assert not set(ids)&{0,3,4,5} and ids.count(2)<=1 and (2 not in ids or ids[-1]==2)
        assert b''.join(pieces[t] for t in ids).decode()==raw
        new_text_hashes.add(text_sha)
        if key in prior_ids:assert text_sha==old_index[key]['body_sha']
        for offset in range(0,len(ids)-1,256):
            seq=ids[offset:offset+257]
            if (key,offset) in seen_positions or tuple(seq) in old_windows:
                continue
            if key in prior_ids:overlap_bases.add(key)
            groups[src].append([key,offset,seq])
        meta[key]=dict(src=src,family=row['family'],length=len(ids),sentences=raw.count('。'),sha=text_sha)
    rng=random.Random(133811)
    for group in groups.values():rng.shuffle(group)
    short=batches(groups.pop('stair'))
    prose_round=[]
    weights=dict(jawikibooks=.135,jawikivoyage=.075,jaquad=.78,jma=.01)
    mix=collections.Counter()
    while weights:
        s=min(weights,key=lambda x:mix[x]/weights[x])
        if not groups[s]:
            del weights[s]
            continue
        row=groups[s].pop()
        prose_round.append(row)
        mix[s]+=len(row[2])-1
    prose=batches(prose_round)
    rng.shuffle(short)
    # Sorting only within 100-batch strata would bias exposure. Shuffle with fixed seed.
    rng.shuffle(prose)
    avail=dict(short=sum(len(x[2])-1 for b in short for x in b),
               prose=sum(len(x[2])-1 for b in prose for x in b))
    pool=dict(short=short,prose=prose)
    counts=collections.Counter()
    schedule=[]
    stages={}
    audit={}
    seen=set()
    cum=1_000_985
    total_targets=4_000_000 if min(avail.values())>=1_501_000 else 1_000_985+2*(min(avail.values())-1024)
    cutoff=[x for x in (1_500_000,2_000_000,3_000_000) if x<total_targets-2000]+[total_targets]
    for index in range(1,len(short)+len(prose)+1):
        name=min(counts or {'short':0,'prose':0},key=lambda k:counts[k]) if len(counts)==2 else ('short' if not counts['short'] else 'prose')
        batch=pool[name].pop()
        n=sum(len(seq)-1 for _,_,seq in batch)
        assert all((key,offset) not in seen for key,offset,_ in batch)
        seen.update((key,offset) for key,offset,_ in batch)
        schedule.append(dict(ids=[[k,off] for k,off,_ in batch],rows=[seq for _,_,seq in batch],targets=n,lr=3e-5))
        cum+=n
        counts[name]+=n
        if cum>=cutoff[0]:
            stages[str(985+index)]=cum
            cutoff.pop(0)
            if not cutoff:break
    used={k for k,_ in seen}
    compressed=gzip.compress(json.dumps(schedule,separators=(',',':')).encode(),mtime=0)
    (ROOT/'SCHEDULE.json.gz').write_bytes(compressed)
    dump(ROOT/'TRAIN_INDEX.json',{k:meta[k] for k in sorted(used)})
    monitor=[dict(id=f'monitor:{k}',panel='train',prefix=seq[:min(24,len(seq)-1)],gold=seq[min(24,len(seq)-1):],budget=32)
        for step in (8,27,58,114,212,299,392,451)
        for k,seq in zip((p[0] for p in old[step]['ids'][:1]),old[step]['rows'][:1])]
    dump(ROOT/'MONITOR.json',monitor)
    dump(ROOT/'DATA_AUDIT.json',dict(available=avail,applied_mix=counts,excluded=excluded_counts,
            overlap_document_ids=len(used&prior_ids),original_sha=sha(source),source_meta='Inherited #105 LICENSE_NOTICE',new_positions=cum-1_000_985))
    inp=['DEV.json','DEV_AUDIT.json','TRAIN_INDEX.json','DATA_AUDIT.json','MONITOR.json','SOURCES.json','RIGHTS.json',
         'freeze.py','run.py','BENCHMARK.json','../data/tokenizer.json','../../model.py','../prose-depth/PLAN.json',
         '../prose-depth/SCHEDULE.json.gz','../prose-depth/artifacts/A/checkpoint.json']
    dump(ROOT/'PLAN.json',dict(stages=stages,terminal_budget_requested=4_000_000,train_targets=cum,lr=3e-5,
        initial=985,initial_targets=1_000_985,checkpoint_sha=read(OLD/'artifacts/A/checkpoint.json')['sha256'],
        schedule_sha=sha(compressed),inputs={n:sha((ROOT/n).read_bytes()) for n in inp},
        rubric='Natural new complete sentence with topical information, second connected new sentence, grammatical clause separately. Harmful repetition, EOS, topic and caption diagnostic. No sampling.'))
    print('frozen',stages,counts,avail, 'new dev',sum(r['panel']=='independent' for r in dev))

if __name__=='__main__':main()
