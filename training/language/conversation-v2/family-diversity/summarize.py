"""Build evidence tables from judgment records and unchanged model outputs."""
import gzip
import json
import math
from collections import Counter, defaultdict
from statistics import mean, median
from prepare import ROOT, BASE, PREVIOUS, read, save

def overlap_index(train, indices, width):
    lookup=defaultdict(set)
    for i in indices:
        seq=train[i]['prefix']+train[i]['gold']
        for j in range(len(seq)-width+1):
            lookup[tuple(seq[j:j+width])].add(i)
    return lookup

def summarize():
    plan=read(ROOT/'PLAN.json')
    train=read(ROOT/'TRAIN.json')
    schedule=read(ROOT/'SCHEDULE.json')
    labels=read(ROOT/'JUDGMENTS.json')
    initial={r['id']:r['decision']=='natural_short_text_only'
             for r in read(BASE/'gv-prose-pilot/SEMANTIC_REVIEW.json')['cases']['initial'] if 'decision' in r}
    records=[]
    exposures={}
    evidence={}
    for arm, indices in plan['arms'].items():
        lookup=overlap_index(train,indices,12)
        ledger=read(ROOT/f'{arm}-ledger.json')
        coverage=defaultdict(Counter)
        frequencies=Counter()
        for batch in schedule[arm]:
            for i,start,count in batch:
                coverage[i].update(range(start,start+count))
                frequencies.update(train[i]['gold'][start:start+count])
        exposures[arm]=dict(
            targets=sum(frequencies.values()), lf=frequencies[16], eos=frequencies[2],
            token_frequencies=frequencies,
            families=[dict(id=train[i]['id'],family=train[i]['family'],positions=len(coverage[i]),
                           processed=sum(coverage[i].values()),per_position_min=min(coverage[i].values()),
                           per_position_max=max(coverage[i].values())) for i in indices])
        for step in plan['steps']:
            key=f'{arm}-{step}'
            result=json.load(gzip.open(ROOT/f'{key}.json.gz'))
            counts=Counter()
            teacher=defaultdict(list)
            recurrences=defaultdict(list)
            evidence[key]=[]
            for row,label in zip(result['cases'],labels[key],strict=True):
                assert row['id']==label['id']
                panel=row['panel']
                seq=row['generated']
                counts[panel]+=1
                counts[f'{panel}_two']+=bool(label.get('two'))
                counts[f'{panel}_harm']+=bool(label.get('harm'))
                counts[f'{panel}_eos']+=row['stop']=='EOS'
                counts[f'{panel}_exact']+=bool(row['gold']) and seq==row['gold']
                if row['repeat']:
                    recurrences[panel].append(row['repeat']['start'])
                teacher[panel].extend(-math.log(s['p_ref']) for s,t in zip(row['teacher'],row['gold']) if t not in (2,16))
                if panel=='train' and row['id'] in {train[i]['id'] for i in plan['arms']['A']}:
                    counts['shared_exact']+=seq==row['gold']
                if panel=='caption':
                    counts['caption_natural']+=label['caption']
                    counts['caption_retained']+=label['caption'] and initial[row['id']]
                    counts['caption_new']+=label['caption'] and not initial[row['id']]
                    counts['caption_ending_only']+=label.get('ending_only',False)
                if panel!='train':
                    hits=[]
                    for j in range(len(seq)-11):
                        gram=tuple(seq[j:j+12])
                        if gram in lookup:
                            hits.append([j,sorted(lookup[gram])])
                    counts[f'{panel}_mechanical_hits']+=bool(hits)
                    counts[f'{panel}_leakage']+=bool(label.get('leakage'))
                    evidence[key].append(dict(id=row['id'],hits_12token=hits,contextual=label.get('leakage')))
            records.append(dict(arm=arm,step=step,counts=dict(counts),forward_calls=result['forwards'],
                                nll={k:math.fsum(v)/len(v) for k,v in teacher.items() if v},
                                repeat_median={k:median(v) for k,v in recurrences.items() if v},
                                cumulative_clip=sum(r['clipped'] for r in ledger[:step]),
                                mean_grad_norm=mean(r['norm'] for r in ledger[:step]) if step else None,
                                total_step_delta=math.fsum(r['delta'] for r in ledger[:step])))
    save(ROOT/'METRICS.json',records)
    save(ROOT/'EXPOSURES.json',exposures)
    save(ROOT/'LEAKAGE.json',evidence)
    lines=['|条件|更新|TRAIN完全再現|共通6再現|TRAIN本文NLL|DEV本文NLL|DEV二文|caption保持|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in records:
        c=row['counts']; n=row['nll']
        lines.append(f"|{row['arm']}|{row['step']}|{c['train_exact']}/{c['train']}|{c.get('shared_exact',0)}/6|{n['train']:.3f}|{n['prose']:.3f}|{c['prose_two']}/18|{c['caption_retained']}/21|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    summarize()
