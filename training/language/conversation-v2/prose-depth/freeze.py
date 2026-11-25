"""Select and lock a single, disjoint, audited causal training stream."""
import collections
import gzip
import json
import math
import random
import re
import unicodedata

from train import ROOT,BASE,CONFIG,DEPTHS,read,dump,sha
from new_tokenizer import Encoder

CORPUS=BASE/'modern-corpus/next-foundation/corpus.jsonl.gz'
SOURCES={'stair','jawikibooks','jawikivoyage','jaquad','jma'}
REVIEWED=set('まな板 茶筅 茶杓 茶托 益子焼 破魔矢 備前焼 升 お手玉 樽 飾り結び つまみ細工 縄跳び 天体観測 影絵 万年筆 圧力鍋 たわし 木版画 和紙 巻き簾 缶詰 弁当箱 曲げわっぱ 張り子'.split())

def norm(s):
    return ''.join(unicodedata.normalize('NFKC',s).split()).casefold()

def grams(tokens):
    return zip(*(tokens[i:] for i in range(12)))

def labels(row):
    values=[row.get(k) for k in ('family','title','id') if isinstance(row.get(k),str)]
    return {norm(v) for v in values}|{norm(v.split('|')[-1].split('/')[0]) for v in values}

def corpus(path):
    with gzip.open(path,'rt') as f:
        yield from map(json.loads,f)

def prepare_dev(enc,pieces):
    fixed=read(BASE/'gv-prose-pilot/EVALUATION_INPUTS.json')
    reg=[]
    for panel,rows in [('fixed',fixed['prose']),('extra',read(BASE/'broad-prose-replay/NEW_DEV.json')),('caption',fixed['caption'])]:
        for r in rows:
            tokens=r.get('tokens',[])
            prefix=r['prefix']
            if tokens and tokens[:len(prefix)]!=prefix:
                if prefix[0]==1 and [1]+tokens[:len(prefix)-1]==prefix:tokens=[1]+tokens
                else:raise ValueError(r['id'])
            reg.append(dict(id=r['id'],panel=panel,prefix=prefix,gold=tokens[len(prefix):],
                            family=r.get('family',r['id']),title=r.get('title',''),budget=r.get('maxNewTokens',128)))
    histories=[CORPUS,BASE/'diverse-foundation/corpus.jsonl.gz',BASE/'foundation-absorption-study/corpus.jsonl.gz']
    old=read(BASE/'prose-teacher-distribution/DEV.json')['cases']+read(BASE/'prose-teacher-distribution/DEV_PART2.json')['cases']
    seen_families=set().union(*(labels(r) for r in old+reg))
    candidates=[]
    for r in read(ROOT/'SOURCE_SNAPSHOTS.json'):
        if r.get('title') not in REVIEWED:continue
        sentences=[s+'。' for s in r['extract'].strip().split('。')[:-1]]
        first=sentences[0]
        suffix=''.join(sentences[1:3]).rstrip()
        p,g=enc(first),enc(suffix)
        if len(sentences)<3 or len(p)+len(g)>255 or enc(first+suffix)!=p+g: continue
        assert b''.join(pieces[t] for t in p+g).decode()==first+suffix
        rev=r['revisions'][0]['revid']
        candidates.append(dict(id='wiki:'+r['title'],title=r['title'],family=r['title'],panel='independent',
             prefix=[1]+p,gold=g,budget=96,text=first+suffix,sha=sha((first+suffix).encode()),
             revision=rev,license='CC BY-SA 4.0',url=f'https://ja.wikipedia.org/w/index.php?oldid={rev}',
             attribution=f'https://ja.wikipedia.org/wiki/{r["title"]}?action=history'))
    index=collections.defaultdict(set)
    blocked=collections.defaultdict(set)
    for r in candidates:
        for gram in grams(r['prefix'][1:]+r['gold']):index[gram].add(r['id'])
        if labels(r)&seen_families:blocked[r['id']].add('prior DEV family')
    names={norm(r['title']):r['id'] for r in candidates}
    # PR105 is the complete candidate source for this run. Additional archived
    # corpora extend historical coverage and remain separate from the new TRAIN.
    for path in histories:
        for row in corpus(path):
            for label in labels(row)&names.keys():
                blocked[names[label]].add(path.parent.name+': family')
            if row.get('source') in SOURCES and row.get('source')!='stair':
                for gram in grams(row['tokens']):
                    for i in index.get(gram,()):
                        blocked[i].add(path.parent.name+': 12-token match')
    for r in candidates:
        if r['id'] not in blocked:reg.append(r)
    dump(ROOT/'DEV_AUDIT.json',dict(archives={str(p.relative_to(BASE)):sha(p.read_bytes()) for p in histories},
        rejected={k:sorted(v) for k,v in blocked.items()},count=sum(r['panel']=='independent' for r in reg),
        scope='Title/family and exact contiguous BPE overlap, known archives only. Same concepts and undetected near duplicates remain possible. Single assistant source review.'))
    dump(ROOT/'DEV.json',reg)
    return reg

def pack(ordered):
    bins=collections.defaultdict(list)
    out=[]
    totals=collections.Counter()
    for key,ids in ordered:
        for start in range(0,len(ids)-1,256):
            seq=ids[start:start+257]
            if len(seq)<2:continue
            n=len(seq)-1
            bucket=(n-1)//24
            batch=bins[bucket]
            batch.append([key,start,seq])
            totals[bucket]+=n
            if totals[bucket]>=990:
                out.append(batch)
                bins[bucket]=[]
                totals[bucket]=0
    out.extend(v for v in bins.values() if v)
    return out

def main():
    tokenizer=read(BASE/'data/tokenizer.json')
    enc=Encoder(tokenizer)
    pieces=list(map(bytes.fromhex,tokenizer['bytes']))
    dev=prepare_dev(enc,pieces)
    protected=set().union(*(labels(r) for r in dev))
    test_grams=set().union(*(set(grams(r['prefix']+r['gold'])) for r in dev))
    protected_images=set(read(BASE/'modern-corpus/STAIR_DEV_FAMILIES.json')['original_TRAIN_image_ids_reserved_for_DEV'])
    old_dev=read(BASE/'prose-teacher-distribution/DEV.json')['cases']+read(BASE/'prose-teacher-distribution/DEV_PART2.json')['cases']
    protected.update(set().union(*(labels(r) for r in old_dev)))
    for r in old_dev:
        test_grams.update(grams(r['full']+r['gold']))
    groups=collections.defaultdict(list);meta={};seen=set();excluded=collections.Counter()
    for row in corpus(CORPUS):
        src=row['source']
        if src not in SOURCES:continue
        ids=row['tokens']
        signature=tuple(t for t in ids if t>=6)
        if row['id'] in meta or signature in seen:
            excluded['duplicate']+=1
            continue
        if labels(row)&protected or row.get('original_image_id') in protected_images or not test_grams.isdisjoint(grams(ids)):
            excluded['dev_overlap']+=1
            continue
        if src!='stair' and row['text'].count('。')<2:
            excluded['prose_lt_two_sentences']+=1
            continue
        assert not set(ids)&{0,3,4,5}
        assert ids.count(2)<=1 and (2 not in ids or ids[-1]==2)
        assert b''.join(pieces[t] for t in ids).decode()==row['text']
        k=row['id']
        meta[k]=dict(source=src,family=row['family'],body_sha=sha(row['text'].encode()),tokens=len(ids))
        groups[src].append((k,ids))
        seen.add(signature)
    rng=random.Random(131803)
    for group in groups.values():rng.shuffle(group)
    # Balance across prose genres and short captions without duplicating positions.
    prose=[]
    weights={'jawikibooks':.22,'jawikivoyage':.14,'jaquad':.63,'jma':.01}
    counts=collections.Counter()
    while weights:
        s=min(weights,key=lambda x:counts[x]/weights[x])
        if not groups[s]:
            del weights[s]
            continue
        item=groups[s].pop()
        counts[s]+=len(item[1])-1
        prose.append(item)
        if len(prose)>9000:break
    buckets=dict(caption=pack(groups['stair']),prose=pack(prose))
    for batch in buckets.values():rng.shuffle(batch)
    schedule=[]; used=set(); counts=collections.Counter(); mix=collections.Counter();points=[]; total=0
    end=1_000_000
    while total<end:
        group=min(buckets,key=lambda s:mix[s])
        batch=buckets[group].pop()
        target=sum(len(seq)-1 for _,_,seq in batch)
        for k,_,seq in batch:
            used.add(k);counts[meta[k]['source']]+=len(seq)-1
        schedule.append(dict(ids=[[k,start] for k,start,_ in batch],rows=[seq for _,_,seq in batch],targets=target))
        mix[group]+=target
        total+=target
        if len(points)==0 and total>=500_000:
            points.append(len(schedule))
    points.append(len(schedule))
    for k,item in enumerate(schedule,1):
        item['lr']=.0002*k/128 if k<=128 else 3e-5+(.0002-3e-5)*.5*(1+math.cos(math.pi*(k-128)/(len(schedule)-128)))
    compressed=gzip.compress(json.dumps(schedule,separators=(',',':')).encode(),mtime=0)
    (ROOT/'SCHEDULE.json.gz').write_bytes(compressed)
    dump(ROOT/'TRAIN_INDEX.json',{k:meta[k] for k in sorted(used)})
    dump(ROOT/'DATA_AUDIT.json',dict(targets_by_source=counts,mix=mix,exclusion=excluded,types=len(used),
        families=len({meta[k]['family'] for k in used}),original_source_sha=sha(CORPUS.read_bytes())))
    inputs={name:sha((ROOT/name).read_bytes()) for name in
            ['DEV.json','DEV_AUDIT.json','TRAIN_INDEX.json','DATA_AUDIT.json','SOURCE_SNAPSHOTS.json','train.py',
             '../data/tokenizer.json','../../model.py','../eval_core.py','BENCHMARK.json']}
    dump(ROOT/'PLAN.json',dict(configs={k:dict(CONFIG,layers=n) for k,n in DEPTHS.items()},
         seed=131801,dropout_seed=131802,sampler_seed=131803,points=points,witness=25,targets=total,
         counts=counts,secure_scope='private Git-only',schedule_sha=sha(compressed),inputs=inputs,
         primary='Terminal independent held-out family full-vocabulary greedy, new natural two connected sentences',
         secondary='Fixed18/extra7/caption32 and NLL; no case changes after training',
         shaping='Select separately bucketed caption/prose, proper causal shift and PAD mask, independent source locations. No synthetic EOS.',
         stop='Source/hash, nonfinite, resume, or durable storage failure. Fixed budget across models.'))
    print(len(schedule),points,total,counts,read(ROOT/'DEV_AUDIT.json')['count'])

if __name__=='__main__':
    main()
