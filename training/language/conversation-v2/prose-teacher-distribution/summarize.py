"""Summaries of fixed references, position interventions and objective evaluation."""
import gzip
import json
import math
import random
from collections import Counter,defaultdict
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PREV=BASE/'prose-context-length'
OLD=BASE/'prose-budget-scale'
KEYS=('start','control','shortened')
POINTS=(300,400,450,500,600)

def read(path):
    return json.loads(path.read_text())

def raw(path):
    return json.loads(gzip.decompress(path.read_bytes()))

def write(name,x):
    (ROOT/name).write_text(json.dumps(x,ensure_ascii=False,indent=1)+'\n')

def avg(xs):
    return math.fsum(xs)/len(xs) if xs else None

def losses(row):
    return [-math.log(s['p_ref']) for s,t in zip(row['teacher'],row['gold']) if t not in (2,16)]

def diagnostics(r):
    i=r['first_mismatch']
    gap=[] if i is None else [
        math.log(b['p_ref'])-math.log(a['p_ref'])
        for a,b in zip(r['steps'][i:i+32],r['teacher'][i:i+32]) if a['p_ref'] and b['p_ref']]
    return dict(first_departure=i,repeat4=r['repeat']['start'] if r['repeat'] else None,
                gap=avg(gap),stop=r['stop'])

def blind():
    order=[(key,i) for key in KEYS for i in range(len(raw(ROOT/f'part1-{key}.json.gz')['cases']))]
    random.Random(13107).shuffle(order)
    contents={k:raw(ROOT/f'part1-{k}.json.gz')['cases'] for k in KEYS}
    pieces=list(map(bytes.fromhex,read(BASE/'data/tokenizer.json')['bytes']))
    write('BLIND_ORDER.json',order)
    write('BLIND_TEXT.json',[dict(index=i,input=b''.join(pieces[t] for t in contents[key][j]['prefix']).decode(),
                               continuation=contents[key][j]['text']) for i,(key,j) in enumerate(order)])

def independent():
    dev={r['id']:r for r in read(ROOT/'DEV.json')['cases']}
    output={}
    table=[]
    score={(k,j):r for (k,j),r in zip(read(ROOT/'BLIND_ORDER.json'),read(ROOT/'PART1_REVIEW.json'),strict=True)}
    for key in KEYS:
        data=raw(ROOT/f'part1-{key}.json.gz')
        shifted=read(ROOT/f'part1-{key}-positions.json')
        cases={}
        group=defaultdict(lambda:defaultdict(list))
        for i,r in enumerate(data['cases']):
            case,length=r['id'].rsplit(':',1)
            meta=dev[case]
            nll=losses(r)
            values=cases.setdefault(case,dict(group=meta['group']))
            values[length]=dict(nll=avg(nll),review=score[key,i],**diagnostics(r))
            group[meta['group']][length].extend(nll)
            if length=='short':
                shifted_nll=[n for n,t in zip(shifted[case],r['gold'],strict=True) if t not in (2,16)]
                values['shifted']=avg(shifted_nll)
                group[meta['group']]['shifted'].extend(shifted_nll)
        output[key]=dict(cases=cases,group={g:{s:avg(v) for s,v in p.items()} for g,p in group.items()},
                         forwards=data['forwards']+len(dev))
    base=output['control']['cases'];after=output['shortened']['cases']
    for group in ('no_known_train_match','known_train_match','old_dev'):
        ids=[i for i in dev if dev[i]['group']==group]
        table.append(dict(group=group,count=len(ids),improved={s:sum(after[i][s]['nll']<base[i][s]['nll'] for i in ids) for s in ('full','short')},
                          shifted_improved=sum(after[i]['shifted']<base[i]['shifted'] for i in ids)))
    write('PART1_METRICS.json',dict(models=output,directions=table))

def previous_path(arm,k):
    folder=BASE/'prose-lr-decay' if k==300 else OLD if arm=='A' and k in (450,600) else PREV/'control' if arm=='A' else PREV
    return folder/f'C-{k}.json.gz'

def known_labels():
    labels=read(PREV/'CASE_RESULTS.json')
    seen={}
    for a in 'AB':
        for k in POINTS:
            for r,q in zip(raw(previous_path(a,k))['cases'],labels[f'{a}-{k}'],strict=True):
                seen[r['id'],tuple(r['generated'])]=q
    return labels,seen

def objective():
    labels,known=known_labels()
    notes=read(ROOT/'PART2_REVIEW.json')
    base=labels['A-300']
    metrics={}; detail={}
    for a in 'AB':
        for k in POINTS:
            key=f'{a}-{k}'
            path=previous_path('A',k) if a=='A' or k==300 else ROOT/f'C-{k}.json.gz'
            nll=defaultdict(list); gap=defaultdict(list); counts=Counter(); cases=[]
            for i,(r,b) in enumerate(zip(raw(path)['cases'],base,strict=True)):
                assert r['id']==b['id']
                p=b['panel']
                q=notes.get(key,{}).get(str(i)) or known.get((r['id'],tuple(r['generated'])))
                if p!='train':
                    assert q is not None,(key,i)
                q=q or {}
                case=dict(id=r['id'],panel=p,nll=avg(losses(r)),decision=q,**diagnostics(r))
                cases.append(case)
                nll[p].extend(losses(r))
                if case['gap'] is not None:gap[p].append(case['gap'])
                if p=='caption':
                    counts['caption']+=bool(q.get('caption'))
                    counts['retained']+=bool(q.get('caption') and b['initial_caption'])
                if p in ('prose','new'):
                    counts['one']+=bool(q.get('one'))
                    counts['two']+=bool(q.get('two'))
                    m=q.get('review') or q
                    if 'harmful_repetition' in m:
                        counts['harmful']+=bool(m['harmful_repetition'])
                        counts['harm_judged']+=1
                    counts['repeat4']+=case['repeat4'] is not None
                    counts['eos']+=case['stop']=='EOS'
            sample=read(path.with_name(path.name.removesuffix('.json.gz')+'-sample.json'))
            metrics[key]=dict(nll={p:avg(v) for p,v in nll.items()},gap={p:avg(v) for p,v in gap.items()},
                counts=counts,train_sample=sample['nll'],replay=sample['historically_seen_disjoint_monitor_nll'])
            detail[key]=cases
    for a in 'AB':
        held=raw(ROOT/f'part2-heldout-{a}.json.gz')
        cases=[]
        for i,r in enumerate(held['cases']):
            q=notes[f'heldout-{a}'][str(i)]
            cases.append(dict(id=r['id'],nll=avg(losses(r)),decision=q,**diagnostics(r)))
        detail[f'heldout-{a}']=cases
        metrics[f'heldout-{a}']=dict(nll=avg([x for r in held['cases'] for x in losses(r)]),
                                    one=sum(bool(x['decision']['one']) for x in cases),two=sum(bool(x['decision']['two']) for x in cases))
    write('PART2_METRICS.json',metrics)
    write('PART2_CASES.json',detail)
    lines=['|条件・更新|固定DEV NLL|追加DEV NLL|共通TRAIN NLL|STAIR監視 NLL|caption保持|全caption|自然な一文／二文|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for k,r in metrics.items():
        if k.startswith('heldout'):continue
        n=r['nll'];c=r['counts']
        lines.append(f"|{k}|{n['prose']:.5f}|{n['new']:.5f}|{r['train_sample']:.5f}|{r['replay']:.5f}|{c['retained']}/21|{c['caption']}/32|{c['one']}／{c['two']}|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    import sys
    {'blind':blind,'part1':independent,'part2':objective}[sys.argv[1]]()
