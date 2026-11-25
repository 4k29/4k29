"""Summarize recorded losses, generation diagnostics and fixed-output review."""
import collections
import gzip
import json
import math
import statistics
import sys

from train import ROOT, DEPTHS, read, dump

INITIAL_21={f'stair:{n}' for n in (709013,164607,780709,54096,363439,468221,705596,808794,
    269737,728815,314944,822181,287488,372931,90795,293007,322805,401499,526115,346709,337807)}
PANELS=('fixed','extra','independent','caption')

def raw(arm,k):
    with gzip.open(ROOT/f'{arm}-{k}-eval.json.gz','rt') as f:
        return json.load(f)

def mean(values):
    return statistics.mean(values) if values else None

def diagnostics(rows):
    losses=[-v for r in rows for t,v in zip(r['gold'],r['ref']) if t>=6 and t!=16]
    gaps=[s['ref']-r['ref'][j] for r in rows for j,s in enumerate(r['steps'])
        if r['first'] is not None and r['first']<=j<r['first']+32 and s['ref'] is not None]
    starts=[r['repeat']['repeatStart'] for r in rows if r['repeat']]
    departures=[r['first'] for r in rows if r['first'] is not None]
    return dict(cases=len(rows),body_targets=len(losses),nll=mean(losses),teacher_minus_self_logp=None if not gaps else -mean(gaps),
        eos=sum(r['stop']=='EOS' for r in rows),repeat4=len(starts),
        repeat4_median=statistics.median(starts) if starts else None,
        first_departure_median=statistics.median(departures) if departures else None)

def main():
    plan=read(ROOT/'PLAN.json')
    manual=read(ROOT/'REVIEW.json')
    metrics={}
    detail={}
    for arm in DEPTHS:
        calls=[json.loads(l) for l in (ROOT/f'{arm}-calls.jsonl').read_text().splitlines()]
        for k in [0]+plan['points']:
            key=f'{arm}-{k}'
            rows=raw(arm,k)
            run_rows=calls[:k]
            panel=metrics[key]={}
            detail[key]=[]
            for r in rows['rows']:
                score=manual[key][r['id']]
                one=bool(score.get('one'))
                two=bool(score.get('two'))
                assert not two or one
                detail[key].append(dict(id=r['id'],panel=r['panel'],nll=diagnostics([r])['nll'],
                    first=r['first'],repeat4=r['repeat'],eos=r['stop']=='EOS',**score))
            for group in PANELS:
                data=[r for r in rows['rows'] if r['panel']==group]
                if not data:continue
                out=panel[group]=diagnostics(data)
                for field in ('one','two','harmful','caption','topic'):
                    out[field]=sum(bool(manual[key][r['id']].get(field)) for r in data)
                if group=='caption':
                    out['initial_21']=sum(r['id'] in INITIAL_21 and bool(manual[key][r['id']].get('caption')) for r in data)
            n=sum(r['targets'] for r in run_rows)
            wall=sum(r['wall'] for r in run_rows)
            p=read(ROOT/'BENCHMARK.json')[arm]['parameters']
            panel['resource']=dict(targets=n,steps=k,train_ce=None if not n else sum(r['loss']*r['targets'] for r in run_rows)/n,
                teacher_per_second=n/wall if wall else None,nonpad_per_second=sum(r['nonpad'] for r in run_rows)/wall if wall else None,
                training_wall=wall,training_cpu=sum(r['cpu'] for r in run_rows),
                approx_flops=6*p*sum(r['raw_positions'] for r in run_rows),
                grad_norm=mean([r['norm'] for r in run_rows]),clip=sum(r['clip'] for r in run_rows),
                update_path=sum(r['delta'] for r in run_rows),rss=max([r['rss_KiB'] for r in run_rows],default=None),
                generated_tokens=rows['tokens'],eval_seconds=rows['seconds'],generated_per_second=rows['tokens']/rows['seconds'])
    for panel in ('fixed','extra','independent'):
        a={r['id']:r['nll'] for r in detail[f"A-{plan['points'][-1]}"] if r['panel']==panel}
        b={r['id']:r['nll'] for r in detail[f"B-{plan['points'][-1]}"] if r['panel']==panel}
        metrics[f"B-{plan['points'][-1]}"][panel]['nll_improved_vs_A']=sum(b[k]<a[k] for k in a)
    dump(ROOT/'RESULTS.json',metrics)
    dump(ROOT/'CASES.json',detail)
    lines=['|条件|教師|固定NLL|追加NLL|独立NLL|独立一文/二文|caption自然|旧21との重複|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    def nll(data):
        return f"{data['nll']:.5f}" if data else '—'
    for key,row in metrics.items():
        independent=row.get('independent')
        sentence=f"{independent['one']}/{independent['two']}" if independent else '—'
        lines.append(f"|{key}|{row['resource']['targets']:,}|{nll(row['fixed'])}|{nll(row['extra'])}|{nll(independent)}|{sentence}|{row['caption']['caption']}/32|{row['caption']['initial_21']}/21|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    if len(sys.argv)==3:
        for r in raw(sys.argv[1],int(sys.argv[2]))['rows']:
            print(r['id'],r['panel'],r['stop'],repr(r['text'] if r['panel']=='caption' else (r['text'] or '')[:200]))
    else:
        main()
