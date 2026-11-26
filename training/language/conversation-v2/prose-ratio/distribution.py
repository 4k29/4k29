"""Report stage-wise target mix and the left neighbors of whitespace and digits."""
import collections
import gzip
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PREV=BASE/'prose-development'
DEPTH=BASE/'prose-depth'

def read(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)

def rows(schedule):
    for batch in schedule:
        for (doc,off),tokens in zip(batch['ids'],batch['rows'],strict=True):
            yield doc,off,tokens

def collect(plan):
    metadata=read(PREV/'TRAIN_INDEX.json')
    pieces=list(map(bytes.fromhex,read(BASE/'data/tokenizer.json')['bytes']))
    assert pieces[0]==pieces[2]==b'' and pieces[16]==b'\n' and pieces[38]==b' '
    assert [pieces[i] for i in range(54,64)]==[str(n).encode() for n in range(10)]
    p133=read(PREV/'SCHEDULE.json.gz')
    bs=read(ROOT/'SCHEDULE.json.gz')
    original=read(DEPTH/'SCHEDULE.json.gz')
    anchor=read(DEPTH/'TRAIN_INDEX.json')
    exposure={(doc,off) for doc,off,_ in rows(original)}
    a={(doc,off):tokens for doc,off,tokens in rows(p133[:2950-985])}
    b={(doc,off):tokens for doc,off,tokens in rows(bs)}
    pool={(doc,off):tokens for doc,off,tokens in rows(p133)}
    assert all(pool[k][:len(tokens)]==tokens for k,tokens in b.items())
    stair=lambda k:metadata[k[0]]['src']=='stair'
    assert all(b[k]==tokens for k,tokens in a.items() if not stair(k))
    assert all(a[k][:len(tokens)]==tokens for k,tokens in b.items() if stair(k))
    def stats(schedule, corpus, seen):
        references=set()
        use=collections.Counter()
        family=collections.Counter()
        source=collections.Counter()
        contexts={s:collections.Counter() for s in ('space','digits')}
        kinds=collections.Counter()
        for doc,offset,tokens in rows(schedule):
            assert (doc,offset) not in references and (doc,offset) not in seen
            references.add((doc,offset))
            n=len(tokens)-1
            record=corpus[doc]
            src=record.get('src',record.get('source'))
            use[doc]+=n
            source[src]+=n
            family[record['family']]+=n
            assert len(tokens)<=257 and set(tokens).isdisjoint({0,3,4,5}) and (2 not in tokens or tokens[-1]==2)
            for previous,target in zip(tokens,tokens[1:]):
                if target==2:kinds['eos']+=1
                if target==16:kinds['lf']+=1
                if target==38:
                    kinds['space']+=1
                    contexts['space'][previous]+=1
                if 54<=target<=63:
                    kinds['digits']+=1
                    contexts['digits'][previous]+=1
        targets=sum(source.values())
        return dict(sources=source,targets=targets,prose=targets-source['stair'],short=source['stair'],
            documents=len(use),families=len(family),max_family=family.most_common(1)[0],kinds=kinds,
            preceding={k:[dict(id=i,hex=pieces[i].hex(),count=n) for i,n in c.most_common(20)] for k,c in contexts.items()},
            repeated_coordinates=0,existing_document_count=len(use.keys()&anchor.keys()),
            token_length_median=statistics.median(corpus[k].get('length',corpus[k].get('tokens')) for k in use),
            prose_sentence_count_median=statistics.median(corpus[k]['sentences'] for k in use if k in metadata and corpus[k]['src']!='stair') if corpus is metadata else None)
    initial=stats(original,anchor,set())
    summary={'start':initial}
    for name,schedule,points in [('A',p133,plan['a_steps']),('B',bs,plan['b_steps'])]:
        for step in points:
            stage=stats(schedule[:step-985],metadata,exposure)
            stage.update(cumulative_prose=initial['prose']+stage['prose'],cumulative_targets=initial['targets']+stage['targets'])
            summary[f'{name}-{step}']=stage
    return summary

if __name__=='__main__':
    p=ROOT/'DISTRIBUTION.json'
    p.write_text(json.dumps(collect(read(ROOT/'PLAN.json')),ensure_ascii=False,indent=2)+'\n')
