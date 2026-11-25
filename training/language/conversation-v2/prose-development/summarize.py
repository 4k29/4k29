"""Summarize frozen raw outputs without changing their text, tokens or ordering."""
import collections
import json
import math
import statistics
from review import ROOT,OLD,PIECES,read,dump,stage
from run import INITIAL,load_schedule

def grams(ids):
    return zip(*(ids[i:] for i in range(12)))

def extract(rows):
    refs=[-p for r in rows for t,p in zip(r['gold'],r['ref'],strict=True) if t>=6 and t!=16]
    gaps=[r['ref'][i]-s['ref'] for r in rows if r['first'] is not None
          for i,s in enumerate(r['steps']) if r['first']<=i<r['first']+32 and s['ref'] is not None]
    repeats=[r['repeat']['repeatStart'] for r in rows if r['repeat']]
    departures=[r['first'] for r in rows if r['first'] is not None]
    tokens=[t for r in rows for t in r['generated']]
    out=dict(n=len(rows),body_targets=len(refs),nll=statistics.mean(refs) if refs else None,
      tf_self_gap=statistics.mean(gaps) if gaps else None,gap_terms=len(gaps),
      repeat4=len(repeats),repeat4_median=statistics.median(repeats) if repeats else None,
      first_departure_median=statistics.median(departures) if departures else None,
      eos=sum(r['stop']=='EOS' for r in rows),lf=tokens.count(16),space=tokens.count(38),
      digits=sum(54<=v<=63 for v in tokens),generated=len(tokens),invalid_utf8=sum(r['text'] is None for r in rows))
    decisions=[s for r in rows for s in r['steps']]
    for field in ('lf','space','eos','digits'):
        probs=[s[field] for s in decisions if field in s]
        out[f'mean_p_{field}']=statistics.mean(probs) if probs else None
    out['median_first_token_top1_probability']=statistics.median(r['steps'][0]['top'][0][1] for r in rows)
    return out

def main():
    plan=read(ROOT/'PLAN.json')
    stages={int(k):v for k,v in plan['stages'].items()}
    archived=[k for k in stages if stages[k]>=2_000_000]
    points=[f'A-{k}' for k in [INITIAL]+list(stages)]+[f'holdout-{k}' for k in dict.fromkeys([INITIAL,archived[0],archived[-1]])]
    dev={r['id']:r for r in read(ROOT/'DEV.json')+read(ROOT/'MONITOR.json')}
    labels=read(ROOT/'REVIEW.json')
    lines=[json.loads(x) for x in (ROOT/'LEDGER.jsonl').read_text().splitlines()]
    old_labels=read(OLD/'REVIEW.json')['A-985']
    start_caption={k for k,v in old_labels.items() if v['caption']}
    start_21={f'stair:{n}' for n in (709013,164607,780709,54096,363439,468221,705596,808794,
        269737,728815,314944,822181,287488,372931,90795,293007,322805,401499,526115,346709,337807)}
    outputs={p:stage(p) for p in points}
    desired={g for out in outputs.values() for r in out for g in grams(r['generated'])}
    matches={}
    for s in (load_schedule(OLD),load_schedule(ROOT)):
        for b in s:
            for (key,loc),seq in zip(b['ids'],b['rows'],strict=True):
                for i,g in enumerate(grams(seq)):
                    if g in desired:matches.setdefault(g,[key,loc+i])
    metrics={};cases={}
    for p,rows in outputs.items():
        expected={k for k,d in dev.items() if (d['panel']=='independent')==p.startswith('holdout-')}
        assert len(rows)==len(expected) and {r['id'] for r in rows}==expected,p
        metrics[p]={}
        cases[p]=[]
        k=int(p.split('-')[-1])
        for r in rows:
            d=dev[r['id']]
            assert r['gold']==d['gold'],(p,r['id'])
            assert len(r['generated'])<=min(d['budget'],256-len(d['prefix']))
            assert r['generated'] and len(r['steps'])==len(r['generated'])
            assert b''.join(PIECES[t] for t in r['generated']).hex()==r['rawBytesHex']
            assert r['generated']==[v['top'][0][0] for v in r['steps']]
            assert all(math.isfinite(x) for x in r['ref'])
            score=labels[p][r['id']] if r['panel']!='train' else {}
            mx=[dict(generated_at=i,teacher_at=matches[g]) for i,g in enumerate(grams(r['generated'])) if g in matches]
            cases[p].append(dict(id=r['id'],panel=r['panel'],**extract([r]),match12=mx,**score))
        panels=sorted({r['panel'] for r in rows})
        for panel in panels:
            out=[r for r in rows if r['panel']==panel]
            q=metrics[p][panel]=extract(out)
            q['match12_cases']=sum(bool(x['match12']) for x in cases[p] if x['panel']==panel)
            if panel!='train':
                j=[labels[p][r['id']] for r in out]
                for key in ('clause','one','two','topic','harmful','off_topic','caption'):
                    q[key]=sum(bool(x.get(key)) for x in j)
                if panel=='caption':
                    ids={r['id'] for r in out if labels[p][r['id']]['caption']}
                    q.update(overlap_21=len(ids&start_21),retained_17=len(ids&start_caption),lost_17=sorted(start_caption-ids),
                             new_vs_985=sorted(ids-start_caption))
        if p.startswith('A-'):
            running=lines[:k-INITIAL]
            n=sum(r['targets'] for r in running)
            w=math.fsum(r['wall'] for r in running)
            metrics[p]['work']=dict(cumulative_targets=n+1_000_985,additional=n,retained=len(running),
              wall=w,cpu=math.fsum(r['cpu'] for r in running),train_ce=math.fsum(r['loss']*r['targets'] for r in running)/n if n else None,
              teachers_per_second=n/w if w else None,max_RSS_KiB=max((r['rss_KiB'] for r in running),default=None),
              mean_gradient_norm=statistics.mean(r['norm'] for r in running) if running else None,
              clips=sum(r['clip'] for r in running),actual_update_path=math.fsum(r['delta'] for r in running))
    holdout=[p for p in points if p.startswith('holdout-')]
    indexed={p:{r['id']:r for r in outputs[p]} for p in holdout}
    paired={p:{'reference':[],'self':[]} for p in holdout}
    common_cases=0
    for identifier in indexed[holdout[0]]:
        rows={p:indexed[p][identifier] for p in holdout}
        if any(r['first'] is None for r in rows.values()):continue
        common=set.intersection(*[
            {i for i,t in enumerate(r['steps']) if t['ref'] is not None and r['first']<=i<r['first']+32}
            for r in rows.values()])
        common_cases+=bool(common)
        for p,r in rows.items():
            for i in sorted(common):
                paired[p]['reference'].append(-r['ref'][i])
                paired[p]['self'].append(-r['steps'][i]['ref'])
    dump(ROOT/'PAIRED_HISTORY.json',dict(cases=common_cases,
        positions=len(paired[holdout[0]]['self']),by_state={
            p:{k:statistics.mean(v) for k,v in x.items()} for p,x in paired.items()}))
    dump(ROOT/'RESULTS.json',metrics)
    dump(ROOT/'CASES.json',cases)
    table=['|累積教師|更新|固定18 NLL|追加7 NLL|既閲覧24 NLL|TRAIN監視 NLL|caption|旧21重複|A-985の17保持|既閲覧49 一文／二文|',
           '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for p,m in metrics.items():
        if not p.startswith('A-'):continue
        n=sum(m[k]['one'] for k in ('fixed','extra','depth24'))
        t=sum(m[k]['two'] for k in ('fixed','extra','depth24'))
        c=m['caption']
        table.append(f"|{m['work']['cumulative_targets']:,}|{p.split('-')[-1]}|{m['fixed']['nll']:.5f}|{m['extra']['nll']:.5f}|{m['depth24']['nll']:.5f}|{m['train']['nll']:.5f}|{c['caption']}/32|{c['overlap_21']}/21|{c['retained_17']}/17|{n}／{t}|")
    table.extend(['','|新規独立34件|本文NLL|自然な一文／二文|有害反復|EOS|参照と自己履歴の差（nat）|','|---|---:|---:|---:|---:|---:|'])
    for p,m in metrics.items():
        if not p.startswith('holdout-'):continue
        r=m['independent']
        table.append(f"|{p}|{r['nll']:.5f}|{r['one']}／{r['two']}|{r['harmful']}/34|{r['eos']}/34|{r['tf_self_gap']:.4f}|")
    (ROOT/'TABLES.md').write_text('\n'.join(table)+'\n')

if __name__=='__main__':main()
