"""Measure free generation, token NLL and trajectory in the matched panels."""
import gzip
import json
import math
from collections import Counter,defaultdict
from statistics import median
from protocol import ROOT,BASE,SOURCE,read,save

def raw(arm,k):
    old=SOURCE/f'C-{k}.json.gz'
    if k==0:
        paths=[BASE/'family-diversity/C-0.json.gz',SOURCE/'A-0.json.gz']
    elif arm=='A' and old.exists():
        paths=[old]
    else:
        paths=[ROOT/f'{arm}-{k}.json.gz']
    return [row for p in paths for row in json.load(gzip.open(p))['cases']]

def summarize():
    plan=read(ROOT/'PLAN.json')
    labels=read(ROOT/'REVIEW_NOTES.json')
    archive=read(SOURCE/'JUDGMENTS.json')
    new={r['id'] for r in read(SOURCE/'NEW_DEV.json')}
    training=read(SOURCE/'TRAIN.json')
    bank=defaultdict(set)
    for row in training:
        seq=row['prefix']+row['gold']
        for j in range(len(seq)-11):
            bank[tuple(seq[j:j+12])].add(row['id'])
    baseline={r['id'] for r in archive['C-0'] if r['caption']}
    reused={}
    for k in (0,10,20,50,100,200,300):
        stored={l['id']:l for l in archive[f'{"A" if k==0 else "C"}-{k}']}
        for r in raw('A',k):
            if r['panel']=='caption':
                reused[(r['id'],tuple(r['generated']))]=stored[r['id']]['caption']
    pieces=[bytes.fromhex(s) for s in read(BASE/'data/tokenizer.json')['bytes']]
    metrics=[]
    decisions={}
    for arm in 'AB':
        ledger=read(SOURCE/'C-ledger.json') if arm=='A' else read(ROOT/'B-ledger.json')
        for k in plan['steps']:
            key=f'{arm}-{k}'
            sample=raw(arm,k)
            review=labels.get(key,{})
            counts=Counter()
            nll=defaultdict(list)
            repeats=defaultdict(list)
            cases=[]
            for i,r in enumerate(sample):
                panel='new' if r['id'] in new else r['panel']
                gen=r['generated']
                caption=panel=='caption' and (i in review.get('caption',[]) or reused.get((r['id'],tuple(gen)),False))
                exact=panel=='train' and gen==r['gold']
                two=exact or i in review.get('two',[])
                one=two or i in review.get('one',[])
                counts[panel]+=1
                counts[f'{panel}_two']+=two
                counts[f'{panel}_one']+=one
                counts[f'{panel}_eos']+=r['stop']=='EOS'
                counts[f'{panel}_exact']+=exact
                if panel=='caption':
                    counts['caption_natural']+=caption
                    counts['caption_retained']+=caption and r['id'] in baseline
                    counts['caption_new']+=caption and r['id'] not in baseline
                nll[panel].extend(-math.log(s['p_ref']) for s,t in zip(r['teacher'],r['gold']) if t not in (2,16))
                rep=r['repeat']
                point=rep['start'] if rep else None
                if rep:repeats[panel].append(point)
                trip=None
                if not two and not caption:
                    trip=next((j for j in range(len(gen)) if any(gen[j:j+n]==gen[j+n:j+2*n]==gen[j+2*n:j+3*n]
                         for n in range(1,min(16,(len(gen)-j)//3)+1))),None)
                hits=[]
                if panel!='train':
                    for j in range(len(gen)-11):
                        ids=bank.get(tuple(gen[j:j+12]))
                        if ids:hits.append([j,sorted(ids)])
                    counts[f'{panel}_12token_matches']+=bool(hits)
                source_note=review.get('leakage',{}).get(str(i))
                if arm=='A' and k in (10,20,50,100,200,300):
                    source_note=source_note or archive[f'C-{k}'][i].get('leakage_example')
                visible=b''.join(pieces[t] for t in gen).decode(errors='replace')
                detail=dict(id=r['id'],panel=panel,natural_caption=caption,initial_pass=r['id'] in baseline,
                    exact=exact,one=one,two=two,stop=r['stop'],first_reference_departure=r['first_mismatch'],
                    repeat=rep,triple_cycle_witness=trip,first_harmful_character_loop=review.get('harm',{}).get(str(i)),
                    before_repeat=r['steps'][max(0,point-1)] if point is not None else None,
                    at_repeat=r['steps'][point] if point is not None else None,
                    lf=gen.count(16),mean_eos_probability=math.fsum(t['p_eos'] for t in r['steps'])/len(gen),
                    mean_ascii_space_probability=math.fsum(t['p_space'] for t in r['steps'])/len(gen),
                    digit_count=sum(c.isdecimal() for c in visible),ascii_spaces=visible.count(' '),matches_12=hits,leakage_example=source_note,
                    reason='原文再現' if exact else '自然な短文補完' if caption else '話題に沿う継続' if one else '話題または文意の成立基準を満たさない')
                cases.append(detail)
            path=ROOT/f'{key}-sample.json'
            if not path.exists():
                path=SOURCE/f'C-{k}-sample.json'
            dist=ROOT/f'{key}-distance.json'
            metrics.append(dict(arm=arm,step=k,counts=counts,body_nll={p:math.fsum(v)/len(v) for p,v in nll.items() if v},
                median_repeat={p:median(v) for p,v in repeats.items()},
                sampled=read(path) if path.exists() else None,
                displacement=read(dist)['total'] if dist.exists() else 0.,
                clips=sum(r['clipped'] for r in ledger[:k]),cumulative_path_norm=math.fsum(r['delta'] for r in ledger[:k])))
            decisions[key]=cases
    save(ROOT/'METRICS.json',metrics)
    save(ROOT/'JUDGMENTS.json',decisions)
    lines=['|条件|更新|標本TRAIN NLL|固定DEV NLL|追加DEV NLL|Replay監視NLL|固定二文|追加二文|caption保持|初期からのL2|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in metrics:
        s=r['sampled'];n=r['body_nll'];c=r['counts']
        lines.append(f"|{r['arm']}|{r['step']}|{s['nll']:.3f}|{n['prose']:.3f}|{n['new']:.3f}|{s['historically_seen_disjoint_monitor_nll']:.3f}|{c['prose_two']}/18|{c['new_two']}/7|{c['caption_retained']}/21|{r['displacement']:.3f}|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':summarize()
