"""Freeze the matched-budget A/B contrast and independent prose cases."""
import collections
import gzip
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
PREV = BASE/'prose-development'
DEPTH = BASE/'prose-depth'
sys.path.insert(0,str(PREV))
from freeze_helpers import inherited
blob, read, sha, items, grams, labels, batches = (inherited[k] for k in
    ('blob','read','sha','items','grams','labels','batches'))
Encoder = inherited['Encoder']

def write(path, obj):
    (ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True)+'\n')

def load(path):
    return json.loads(gzip.decompress(path.read_bytes()))

def select_dev():
    old = read(PREV/'DEV.json')
    blocked = old + read(BASE/'prose-teacher-distribution/DEV.json')['cases'] + read(BASE/'prose-teacher-distribution/DEV_PART2.json')['cases']
    excluded = set().union(*(labels(r) for r in blocked))
    excluded_tokens = set().union(*(set(grams(r.get('prefix',r.get('full',[]))+r['gold'])) for r in blocked))
    tok = read(BASE/'data/tokenizer.json')
    enc = Encoder(tok)
    pieces = list(map(bytes.fromhex,tok['bytes']))
    sources = {r['title']:r for r in read(ROOT/'SOURCES.json')}
    candidates, indexed = {}, collections.defaultdict(set)
    rejections = {}
    for title, paragraph, genre in read(ROOT/'DEV_SELECTION.json'):
        r = sources[title]
        sentences = [s+'。' for s in r['paragraphs'][paragraph].split('。')[:-1]][:3]
        text = ''.join(sentences)
        prefix, gold = [1]+enc(sentences[0]), enc(''.join(sentences[1:]))
        key = f'ratio:{title}'
        if len(sentences)!=3 or len(prefix)+len(gold)>256 or prefix[1:]+gold!=enc(text):
            rejections[key] = ['BPE boundary/length']
            continue
        assert b''.join(pieces[t] for t in prefix[1:]+gold).decode()==text
        if labels({'title':title}) & excluded or not excluded_tokens.isdisjoint(grams(prefix+gold)):
            rejections[key] = ['previous evaluation title/12-token']
            continue
        rev=r['revision']
        candidates[key] = dict(id=key,title=title,family=title,genre=genre,panel='ratio-heldout',prefix=prefix,gold=gold,
            budget=96,text=text,sha=sha(text.encode()),revision=rev,license='CC BY-SA 4.0',
            url=f'https://ja.wikipedia.org/w/index.php?oldid={rev}',attribution=r['url']+'?action=history')
        for gram in grams(prefix+gold):
            indexed[gram].add(key)
    by_label = {next(iter(labels({'title':r['title']}))):k for k,r in candidates.items()}
    archives={}
    for path in [inherited['CORPUS']]+[BASE/x for x in inherited['HIST']]:
        raw = blob(path)
        name = str(path.relative_to(BASE))
        archives[name]=sha(raw)
        for row in items(path,raw):
            overlap = {by_label[k] for k in labels(row)&by_label.keys()}
            for gram in grams(row.get('tokens') or row['prefix']+row['gold']):
                overlap.update(indexed.get(gram,()))
            for key in overlap:
                if name not in rejections.setdefault(key,[]):
                    rejections[key].append(name)
    chosen=[r for key,r in candidates.items() if key not in rejections]
    assert chosen
    write('DEV.json',old+chosen)
    write('DEV_AUDIT.json',dict(archives=archives,rejections=rejections,accepted=[r['id'] for r in chosen],
        method='Normalized title and contiguous 12-token archive scan; near-topic titles screened manually; earlier exposure and semantic near-duplicates outside checked archives cannot be ruled out.'))
    return len(chosen)

def size(rows):
    return sum(len(r[2])-1 for r in rows)

def flat(schedule):
    return [[k,o,seq] for b in schedule for (k,o),seq in zip(b['ids'],b['rows'],strict=True)]

def take(rows, budget):
    selected=[]
    for row in rows:
        if not budget:break
        n=min(budget,len(row[2])-1)
        selected.append([row[0],row[1],row[2][:n+1]])
        budget-=n
    assert budget==0
    return selected

def main():
    meta=read(PREV/'TRAIN_INDEX.json')
    pool=load(PREV/'SCHEDULE.json.gz')
    prev_plan=read(PREV/'PLAN.json')
    assert sha((PREV/'SCHEDULE.json.gz').read_bytes())==prev_plan['schedule_sha']
    a=pool[:2950-985]
    start_targets=prev_plan['initial_targets']
    budget=sum(item['targets'] for item in a)
    prose_budget=round(.70*budget)
    a_groups=collections.defaultdict(list)
    tail=collections.defaultdict(list)
    for rows,groups in ((flat(a),a_groups),(flat(pool[len(a):]),tail)):
        for row in rows:
            groups[meta[row[0]]['src']].append(row)
    rng=random.Random(134985)
    prose=[]
    short=take(a_groups.pop('stair'),budget-prose_budget)
    a_prose=sum(map(size,a_groups.values()))
    remaining=prose_budget-a_prose
    additions={}
    for src, rows in a_groups.items():
        requested=round((prose_budget-a_prose)*size(rows)/a_prose)
        additions[src]=min(size(tail[src]),requested)
        remaining-=additions[src]
    for src in sorted(additions,key=lambda k:-size(tail[k])):
        extra=min(size(tail[src])-additions[src],remaining)
        additions[src]+=extra
        remaining-=extra
    assert remaining==0
    for src,rows in a_groups.items():
        prose.extend(rows+take(tail[src],additions[src]))
    rng.shuffle(prose)
    rng.shuffle(short)
    queues={name:batches(rows) for name,rows in [('prose',prose),('short',short)]}
    for q in queues.values():rng.shuffle(q)
    counts=collections.Counter()
    schedule=[]
    cuts=[1500000,2000000,start_targets+budget]
    stages={}
    for _ in range(sum(map(len,queues.values()))):
        name=min((k for k,v in queues.items() if v),key=lambda k:counts[k]/(.70 if k=='prose' else .30))
        rows=queues[name].pop()
        n=size(rows)
        schedule.append(dict(ids=[[k,o] for k,o,_ in rows],rows=[seq for _,_,seq in rows],targets=n,lr=3e-5))
        counts[name]+=n
        total=start_targets+sum(counts.values())
        if total>=cuts[0]:
            stages[str(985+len(schedule))]=total
            cuts.pop(0)
    assert not cuts and sum(counts.values())==budget and counts['prose']==prose_budget
    anchor={(k,o) for k,o,_ in flat(load(DEPTH/'SCHEDULE.json.gz'))}
    initial=collections.Counter()
    for k,o,seq in flat(load(DEPTH/'SCHEDULE.json.gz')):
        initial[read_initial[k]['source'] if 'source' in read_initial[k] else read_initial[k]['src']]+=len(seq)-1
    summary={}
    for name, sch in [('A',a),('B',schedule)]:
        coordinates=set()
        docs=set()
        family=collections.Counter()
        srcs=collections.Counter()
        freq=collections.Counter()
        for k,o,seq in flat(sch):
            assert (k,o) not in anchor and (k,o) not in coordinates
            coordinates.add((k,o))
            docs.add(k)
            family[meta[k]['family']]+=len(seq)-1
            srcs[meta[k]['src']]+=len(seq)-1
            freq.update(seq[1:])
        summary[name]=dict(sources=dict(srcs),documents=len(docs),families=len(family),largest_family=family.most_common(1)[0],
            windows=len(coordinates),updates=len(sch),token_counts={str(i):freq[i] for i in [2,16,38,*range(54,64)]})
    write('DATA_AUDIT.json',dict(available=read(PREV/'DATA_AUDIT.json')['available'],initial=dict(initial),summary=summary,
        extra_by_source=additions,budget=budget,weights=dict(counts),inherited_pool=prev_plan['schedule_sha'],
        new_training_sources=[],full_approx_4m_prose_shortage=2100000-read(PREV/'DATA_AUDIT.json')['available']['prose']))
    number=select_dev()
    packed=gzip.compress(json.dumps(schedule,separators=(',',':')).encode(),mtime=0)
    (ROOT/'SCHEDULE.json.gz').write_bytes(packed)
    files=['DEV.json','DEV_AUDIT.json','DEV_SELECTION.json','SOURCES.json','RIGHTS.json','DATA_AUDIT.json','run.py','freeze.py',
           '../data/tokenizer.json','../prose-development/PLAN.json','../prose-development/SCHEDULE.json.gz',
           '../prose-depth/artifacts/A/checkpoint.json','../prose-development/artifacts/A-2950/checkpoint.json']
    write('PLAN.json',dict(initial=985,initial_targets=start_targets,checkpoint_sha=prev_plan['checkpoint_sha'],
        stages=stages,a_steps=[1476,1967,2950],b_steps=list(map(int,stages)),main_targets=start_targets+budget,
        lr=3e-5,holdout_cases=number,schedule_sha=sha(packed),a_reference='PR #133 A-2950',
        inputs={n:sha((ROOT/n).read_bytes()) for n in files},
        review='Prefix excluded. Complete natural topical novel one/two sentences; separate topic, harmful repetition, topic drift and EOS. Greedy only. Blind final model labels.'))
    print(stages,summary,number)

if __name__=='__main__':
    read_initial=read(DEPTH/'TRAIN_INDEX.json')
    main()
