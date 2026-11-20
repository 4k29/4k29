"""Derive evaluation tables from immutable generations and review decisions."""
import gzip
import json
import math
from collections import Counter,defaultdict
from statistics import median
from build import ROOT,BASE,OLD,FAMILY,read,save

def load(path):
    with gzip.open(path) as stream:return json.load(stream)['cases']

def archived(step):
    if step==0:return load(FAMILY/'C-0.json.gz'),read(FAMILY/'JUDGMENTS.json')['C-0']
    rows=load(OLD/f'C-{step}.json.gz')
    labels=read(OLD/'JUDGMENTS.json')[f'C-{step}']
    return rows,labels

def summarize():
    plan=read(ROOT/'PLAN.json')
    notes=read(ROOT/'REVIEW_NOTES.json')
    initial={r['id']:r['generated'] for r in archived(0)[0]}
    initial_caption={r['id'] for r in archived(0)[1] if r['caption']}
    train=read(ROOT/'TRAIN.json')
    new_ids={r['id'] for r in read(ROOT/'NEW_DEV.json')}
    metrics=[];judgments={}
    for arm in 'ABC':
        indexed=defaultdict(set)
        for i in list(range(14)) if arm=='A' else plan['arms'][arm]:
            r=train[i];seq=r['prefix']+r['gold']
            for j in range(len(seq)-11):
                indexed[tuple(seq[j:j+12])].add(r['id'])
        for step in plan['steps']:
            key=f'{arm}-{step}'
            if arm=='A' or step==0:
                rows,labels=archived(step)
                path=ROOT/f'A-{step}.json.gz'
                if path.exists(): rows+=load(path)
            else:
                rows=load(ROOT/f'{key}.json.gz'); labels=[]
            overrides=notes.get(key,notes.get('A-0',{}) if step==0 else {})
            counts=Counter(); nll=defaultdict(list); reps=defaultdict(list);items=[]
            for i,r in enumerate(rows):
                panel='new' if r['id'] in new_ids else r['panel']
                exact=panel=='train' and r['generated']==r['gold']
                base=labels[i] if i<len(labels) else None
                if base:assert base['id']==r['id']
                caption=panel=='caption' and (bool(base and base['caption']) or i in overrides.get('caption',[]) or
                          r['id'] in initial_caption and r['generated']==initial[r['id']])
                two=panel!='caption' and (exact or bool(base and base['two']) or i in overrides.get('two',[]))
                one=two or i in overrides.get('one',[])
                leak=(base or {}).get('leakage_example') or overrides.get('leakage',{}).get(str(i))
                counts[panel]+=1
                counts[f'{panel}_two']+=two
                counts[f'{panel}_one']+=one
                counts[f'{panel}_eos']+=r['stop']=='EOS'
                counts[f'{panel}_exact']+=exact
                if caption:
                    counts['caption_natural']+=1
                    counts['caption_retained']+=r['id'] in initial_caption
                nll[panel].extend(-math.log(s['p_ref']) for s,t in zip(r['teacher'],r['gold']) if t not in (2,16))
                if r['repeat']:reps[panel].append(r['repeat']['start'])
                seq=r['generated']
                hits=[]
                if panel in ('prose','new','caption'):
                    hits=[[j,sorted(indexed[tuple(seq[j:j+12])])] for j in range(len(seq)-11) if tuple(seq[j:j+12]) in indexed]
                    counts[f'{panel}_hit']+=bool(hits)
                cycle=None
                if not two and not caption:
                    for j in range(len(seq)):
                        if any(seq[j:j+n]==seq[j+n:j+2*n]==seq[j+2*n:j+3*n] for n in range(1,min(16,(len(seq)-j)//3)+1)):
                            cycle=j
                            break
                items.append(dict(id=r['id'],panel=panel,exact=exact,caption=caption,one=one,two=two,
                    repeat=r['repeat'],triple_cycle=cycle,leakage_example=leak,mechanical_match=hits,
                    judgment='exact reference' if exact else 'natural continuation' if one or caption else 'insufficient semantic continuation',
                    eos=r['stop']=='EOS',stop=r['stop']))
            sample=ROOT/f'{key}-sample.json'
            if arm=='A':sample=OLD/f'C-{step}-nll.json'
            metrics.append(dict(arm=arm,step=step,counts=counts,nll={k:math.fsum(v)/len(v) for k,v in nll.items() if v},
                                repeat_median={k:median(v) for k,v in reps.items() if v},
                                sampled=read(sample) if sample.exists() else None))
            judgments[key]=items
    save(ROOT/'METRICS.json',metrics)
    save(ROOT/'JUDGMENTS.json',judgments)
    lines=['|条件|更新|共通TRAIN再現|共通TRAIN NLL|固定DEV一文/二文|固定DEV NLL|追加DEV一文/二文|追加DEV NLL|caption保持|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in metrics:
        c=r['counts'];n=r['nll']
        matched=f"{c.get('new_one',0)}/{c.get('new_two',0)} ({c['new']}件)" if c['new'] else '—'
        new_nll=f"{n['new']:.3f}" if 'new' in n else '—'
        lines.append(f"|{r['arm']}|{r['step']}|{c['train_exact']}/14|{n['train']:.3f}|{c['prose_one']}/{c['prose_two']}|{n['prose']:.3f}|{matched}|{new_nll}|{c['caption_retained']}/21|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    summarize()
