"""Aggregate full-generation traces and blind case reviews into deterministic tables."""
import collections
import json
import math
import statistics
from pathlib import Path

from distribution import rows
from review import ROOT,PREV,DEPTH,cases,read

def mean(values):
    values=list(values)
    return statistics.mean(values) if values else None

def longest(tokens,token):
    best=run=0
    for value in tokens:
        run=run+1 if value==token else 0
        best=max(best,run)
    return best

def grams(ids):
    return zip(*(ids[i:] for i in range(12)))

def groups(outputs):
    result=collections.defaultdict(list)
    for r in outputs:
        key='short-monitor' if r['id'].startswith('monitor:stair:') else r['panel']
        result[key].append(r)
    return result

def measure(outputs, ratings, matches):
    nll=[-lp for r in outputs for token,lp in zip(r['gold'],r['ref'],strict=True) if token>=6 and token!=16]
    out=[t for r in outputs for t in r['generated']]
    series=[s for r in outputs for s in r['steps']]
    starts=[r['repeat']['repeatStart'] for r in outputs if r['repeat']]
    punc_ids=PUNCTUATION
    metrics=dict(cases=len(outputs),nll=mean(nll),body_positions=len(nll),tokens=len(out),space=out.count(38),
        digits=sum(54<=t<64 for t in out),lf=out.count(16),punctuation=sum(t in punc_ids for t in out),
        eos=out.count(2),max_space_run=max(longest(r['generated'],38) for r in outputs),
        only_whitespace=sum(r['text'] is not None and not r['text'].strip() for r in outputs),
        whitespace_nonempty=sum(bool(r['text']) and not r['text'].strip() for r in outputs),
        median_first=statistics.median(v) if (v:=[r['first'] for r in outputs if r['first'] is not None]) else None,
        first_repeat_median=statistics.median(starts) if starts else None,first_repeat_count=len(starts),
        match12=sum(any(g in matches for g in grams(r['generated'])) for r in outputs),
        entropy=mean(s['entropy'] for s in series if 'entropy' in s),
        gold_space=mean(p for r in outputs for p in r.get('gold_space',[])),
        self_space=mean(s['space'] for s in series),
        pre_repeat_maxp=mean(r['steps'][r['repeat']['repeatStart']-1]['top'][0][1]
                         for r in outputs if r['repeat'] and r['repeat']['repeatStart']>0))
    if ratings is not None:
        for flag in ('one','two','topic','off_topic','harmful','caption'):
            metrics[flag]=sum(bool(ratings[r['id']].get(flag)) for r in outputs)
        metrics['natural_end']=sum(r['stop']=='EOS' and any(ratings[r['id']].get(f) for f in ('one','two','caption'))
                                   and not ratings[r['id']].get('harmful') for r in outputs)

    return metrics

def paired(outputs,names):
    n=0
    episodes=0
    eos_omitted=0
    other_omitted=0
    per={x:{'ref':[],'self':[],'gold_space':[],'self_space':[]} for x in names}
    lookup={x:{r['id']:r for r in outputs[x]} for x in names}
    for key in lookup[names[0]]:
        group={x:lookup[x][key] for x in names}
        assert len({tuple(r['gold']) for r in group.values()})==1
        if any(r['first'] is None for r in group.values()):
            continue
        start=max(r['first'] for r in group.values())
        end=min([len(r['gold']) for r in group.values()]+[r['first']+32 for r in group.values()])
        usable=[]
        for i in range(start,end):
            missing=[r for r in group.values() if len(r['steps'])<=i]
            if missing:
                if any(r['stop']=='EOS' for r in missing):eos_omitted+=1
                else:other_omitted+=1
            else:usable.append(i)
        episodes+=bool(usable)
        n+=len(usable)
        for x,r in group.items():
            for i in usable:
                per[x]['ref'].append(-r['ref'][i])
                per[x]['self'].append(-r['steps'][i]['ref'])
                per[x]['gold_space'].append(r['gold_space'][i])
                per[x]['self_space'].append(r['steps'][i]['space'])
    return dict(positions=n,cases=episodes,excluded_cases=len(lookup[names[0]])-episodes,
        eos_omitted=eos_omitted,other_omitted=other_omitted,states={
            x:dict(**{k:mean(vals) for k,vals in clean.items()},
                   gap=mean(y-v for v,y in zip(clean['ref'],clean['self'],strict=True)))
            for x,clean in per.items()})

def work(log):
    n=sum(r['targets'] for r in log)
    seconds=math.fsum(r['wall'] for r in log)
    source=collections.defaultdict(lambda:[0,0.0])
    for row in log:
        for k,v in row.get('by_source',{}).items():
            source[k][0]+=v[0]
            source[k][1]+=v[1]
    return dict(updates=len(log),targets=n,raw_positions=sum(r['raw_positions'] for r in log),
        nonpad=sum(r['nonpad'] for r in log),wall=seconds,cpu=math.fsum(r['cpu'] for r in log),
        rss_KiB=max(r['rss_KiB'] for r in log),clip=sum(r['clip'] for r in log),
        norm=mean(r['norm'] for r in log),path=math.fsum(r['delta'] for r in log),
        ce=math.fsum(r['loss']*r['targets'] for r in log)/n,teachers_per_second=n/seconds,
        by_source={k:dict(targets=a,nll=b/a) for k,(a,b) in source.items()})

def dump(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,indent=2)+'\n')

def main():
    global PUNCTUATION
    import unicodedata
    pieces=[bytes.fromhex(x).decode(errors='replace') for x in read(ROOT.parent/'data/tokenizer.json')['bytes']]
    PUNCTUATION={i for i,p in enumerate(pieces) if p and all(unicodedata.category(c).startswith('P') for c in p)}
    plan=read(ROOT/'PLAN.json')
    a_names=[f'A-{k}' for k in plan['a_steps']]
    b_names=[f'B-{k}' for k in plan['b_steps']]
    h_names=['holdout-start','holdout-A','holdout-B']
    names=['start']+a_names+b_names+h_names
    outputs={k:cases(k) for k in names}
    old=read(PREV/'REVIEW.json')
    labels=read(ROOT/'REVIEW.json')
    start_captions={k for k,v in old['A-985'].items() if v['caption']}
    previous_21={f'stair:{n}' for n in (709013,164607,780709,54096,363439,468221,705596,808794,
        269737,728815,314944,822181,287488,372931,90795,293007,322805,401499,526115,346709,337807)}
    existing={'start':old['A-985']|old['holdout-985'],a_names[0]:old[a_names[0]],
              a_names[1]:old[a_names[1]]|old['holdout-1967'],a_names[2]:old[a_names[2]]}
    audit={}
    wanted={g for rs in outputs.values() for r in rs for g in grams(r['generated'])}
    for path in (DEPTH/'SCHEDULE.json.gz',PREV/'SCHEDULE.json.gz',ROOT/'SCHEDULE.json.gz'):
        schedule=read(path)
        if path==PREV/'SCHEDULE.json.gz':schedule=schedule[:2950-985]
        for identifier,off,seq in rows(schedule):
            for i,g in enumerate(grams(seq)):
                if g in wanted:audit.setdefault(g,[identifier,off+i])
    ledgers={name:[json.loads(x) for x in p.read_text().splitlines()]
             for name,p in [('A',PREV/'LEDGER.jsonl'),('B',ROOT/'LEDGER.jsonl')]}
    result={}
    individual={}
    for name in names:
        rates=existing.get(name,{})|labels.get(name,{})
        by_panel=groups(outputs[name])
        m=result[name]={k:measure(v,None if k in {'train','short-monitor'} else rates,audit) for k,v in by_panel.items()}
        individual[name]={
            r['id']:dict(**rates.get(r['id'],{}),
                body_nll=mean(-lp for token,lp in zip(r['gold'],r['ref'],strict=True) if token>=6 and token!=16),
                match12=[dict(out=i,source=audit[g]) for i,g in enumerate(grams(r['generated'])) if g in audit],
                first=r['first'],first4=r['repeat'],stop=r['stop'],spaces=r['generated'].count(38),
                pre_repeat_top5=r['steps'][r['repeat']['repeatStart']-1]['top'] if r['repeat'] and r['repeat']['repeatStart']>0 else None)
            for r in outputs[name]}
        if 'caption' in m:
            got={r['id'] for r in by_panel['caption'] if rates[r['id']]['caption']}
            m['caption'].update(initial_kept=len(start_captions&got),historic_21=len(previous_21&got),
                lost=sorted(start_captions-got),new=sorted(got-start_captions))
        if name[0] in 'AB':
            m['work']=work(ledgers[name[0]][:int(name.split('-')[-1])-985])
    histories=dict(main_AB=paired(outputs,h_names[1:]),with_start=paired(outputs,h_names))
    # Also record comparison on the exact legacy positions whose 4M diagnostic used all three #133 states.
    legacy={str(k):{r['id']:r for r in read(PREV/f'holdout-{k}.json.gz')['rows']} for k in (985,1967,3932)}
    cand={n:{r['id']:r for r in outputs[n] if r['panel']=='independent'} for n in (a_names[-1],b_names[-1])}
    count=0; missed=0
    lp={n:[[],[]] for n in cand}
    for key in legacy['985']:
        old_rows=[d[key] for d in legacy.values()]
        indexes=set.intersection(*[{i for i,t in enumerate(r['steps']) if t['ref'] is not None and r['first'] is not None and r['first']<=i<r['first']+32} for r in old_rows])
        count+=len(indexes)
        for i in sorted(indexes):
            if any(len(d[key]['steps'])<=i for d in cand.values()):
                missed+=1
                continue
            for n,d in cand.items():
                r=d[key]
                lp[n][0].append(-r['ref'][i])
                lp[n][1].append(-r['steps'][i]['ref'])
    histories['prior_1017']=dict(prior_positions=count,available=count-missed,unavailable=missed,
        states={n:dict(ref=mean(v[0]),self=mean(v[1]),gap=mean(y-x for x,y in zip(*v,strict=True))) for n,v in lp.items()})
    assert count==1017
    deltas={key:individual['holdout-B'][key]['body_nll']-individual['holdout-A'][key]['body_nll']
            for key in individual['holdout-A']}
    dump('NLL_DELTAS.json',dict(B_minus_A=deltas,improved=sum(n<0 for n in deltas.values()),
         tied=sum(n==0 for n in deltas.values()),worse=sum(n>0 for n in deltas.values())))
    dump('RESULTS.json',result)
    dump('CASES.json',individual)
    dump('PAIRED_HISTORY.json',histories)
    table=['|状態|累積教師|固定18 NLL|追加7 NLL|旧独立24 NLL|旧独立34 NLL|短文監視 NLL|caption|開始17件保持|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in names[:-3]:
        m=result[name]
        count=plan['initial_targets']+m.get('work',{}).get('targets',0)
        vals=[f"{m[k]['nll']:.5f}" if k in m else '—' for k in ('fixed','extra','depth24','independent','short-monitor')]
        table.append(f"|{name}|{count:,}|"+'|'.join(vals)+f"|{m['caption']['caption']}/32|{m['caption']['initial_kept']}/17|")
    table.extend(['','|新規独立評価|本文NLL|自然な一文／二文|話題維持|有害反復|EOS|空白token|数字token|最大連続空白|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|'])
    for name in h_names:
        m=result[name]['ratio-heldout']
        table.append(f"|{name}|{m['nll']:.5f}|{m['one']}／{m['two']}|{m['topic']}|{m['harmful']}|{m['eos']}|{m['space']/m['tokens']:.2%}|{m['digits']/m['tokens']:.2%}|{m['max_space_run']}|")
    (ROOT/'TABLES.md').write_text('\n'.join(table)+'\n')

if __name__=='__main__':main()
