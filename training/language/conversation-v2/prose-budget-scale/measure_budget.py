"""Aggregate fixed-panel NLL, semantic decisions and collapse diagnostics."""
import gzip
import json
import math
from collections import Counter,defaultdict
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PREV=BASE/'prose-lr-decay'

def read(p):
    return json.loads(p.read_text())

def panel(p):
    return json.loads(gzip.decompress(p.read_bytes()))

def save(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')

def first_cycle(seq):
    return next((i for i in range(len(seq)) if any(
        seq[i:i+w]==seq[i+w:i+2*w]==seq[i+2*w:i+3*w]
        for w in range(1,min(16,(len(seq)-i)//3)+1))),None)

def build():
    judgments=read(PREV/'JUDGMENTS.json')
    initial={r['id'] for r in judgments['C-300'] if r['initial_caption']}
    assert len(initial)==21
    reference=panel(PREV/'C-300.json.gz')
    known={}
    for k in (175,200,250,300):
        for case,label in zip(panel(PREV/f'C-{k}.json.gz')['cases'],judgments[f'C-{k}'],strict=True):
            if case['panel']=='caption':
                known[(case['id'],tuple(case['generated']))]=label['caption']
    categories={r['id']:r['panel'] for r in judgments['C-300']}
    selections=read(ROOT/'SEMANTIC_REVIEW.json')
    train_grams=set()
    for r in read(ROOT/'TRAIN.json')+read(BASE/'broad-prose-replay/TRAIN.json'):
        seq=r['prefix']+r['gold'][:r.get('eligible_targets',len(r['gold']))]
        train_grams.update(tuple(seq[i:i+12]) for i in range(len(seq)-11))
    report={}
    scores={}
    baseline_nll={}
    steps=[('C-300',reference),('C-450',panel(ROOT/'C-450.json.gz')),('C-600',panel(ROOT/'C-600.json.gz'))]
    steps.extend((f'heldout-{k}',panel(ROOT/f'heldout-{k}.json.gz')) for k in (300,600))
    for name,results in steps:
        counts=Counter()
        nll=defaultdict(list)
        gaps=defaultdict(list)
        repeat_points=defaultdict(list)
        detail=[]
        for i,r in enumerate(results['cases']):
            p=categories.get(r['id'],'heldout')
            q=selections.get(name,{}).get(str(i))
            seq=r['generated']
            cap=p=='caption' and (known.get((r['id'],tuple(seq)),False) if q is None else q['caption'])
            if p=='caption' and (r['id'],tuple(seq)) not in known:
                assert q is not None
            one=bool(q and q.get('one'))
            two=bool(q and q.get('two'))
            if p in ('prose','new','heldout') and name!='C-300':
                assert q is not None and (not two or one)
            count_losses=[-math.log(s['p_ref']) for s,t in zip(r['teacher'],r['gold']) if t not in (2,16)]
            nll[p].extend(count_losses)
            mismatch=r['first_mismatch']
            gap=[]
            if mismatch is not None:
                for a,b in zip(r['steps'][mismatch:mismatch+32],r['teacher'][mismatch:mismatch+32]):
                    if a['p_ref'] and b['p_ref']:
                        gap.append(math.log(b['p_ref'])-math.log(a['p_ref']))
            gaps[p].extend(gap)
            repeat=r['repeat']['start'] if r['repeat'] else None
            if repeat is not None:
                repeat_points[p].append(repeat)
            cycle=first_cycle(seq)
            hits=[i for i in range(len(seq)-11) if tuple(seq[i:i+12]) in train_grams]
            if q and 'harmful_repetition' in q:
                counts.update({f'{p}_harmful_repetition':int(q['harmful_repetition']),
                               f'{p}_appropriate_eos':int(q.get('appropriate_eos',False))})
            counts.update({p:1,f'{p}_one':one,f'{p}_two':two,f'{p}_eos':r['stop']=='EOS',
                           f'{p}_clip_cycle':cycle is not None,f'{p}_match12':bool(hits)})
            if p=='caption':
                counts.update(caption_natural=cap,caption_retained=cap and r['id'] in initial,caption_new=cap and r['id'] not in initial)
            result_nll=math.fsum(count_losses)/len(count_losses) if count_losses else None
            if name in ('C-300','heldout-300'):
                baseline_nll[r['id']]=result_nll
            nll_delta=result_nll-baseline_nll[r['id']] if result_nll is not None else None
            detail.append(dict(id=r['id'],panel=p,nll=result_nll,nll_delta_from_300=nll_delta,
                 reference_logp_gap=math.fsum(gap)/len(gap) if gap else None,first_mismatch=mismatch,
                 repeat=repeat,cycle=cycle,
                 harmful_cycle_candidate=cycle if q and q.get('harmful_repetition') else None,
                 match12=hits,stop=r['stop'],lf=seq.count(16),space=r['text'].count(' '),
                 caption=cap,initial_caption=r['id'] in initial,one=one,two=two,manual=q,
                 before_repeat=r['steps'][max(0,repeat-1)] if repeat is not None else None))
        scores[name]=dict(counts=counts,nll={p:math.fsum(v)/len(v) for p,v in nll.items() if v},
                          mean_reference_logp_gap={p:math.fsum(v)/len(v) for p,v in gaps.items() if v},
                          repeat_median={p:median(v) for p,v in repeat_points.items()},forwards=results['forwards'])
        report[name]=detail
    for k in (300,450,600):
        sample=read((PREV if k==300 else ROOT)/f'C-{k}-sample.json')
        scores[f'C-{k}'].update(train_sample=sample['nll'],replay=sample['historically_seen_disjoint_monitor_nll'])
    save(ROOT/'CASE_RESULTS.json',report)
    save(ROOT/'METRICS.json',scores)
    train=read(ROOT/'TRAIN.json')
    schedule=read(ROOT/'SCHEDULE.json')
    ledger=read(ROOT/'LEDGER.json')
    path=0.
    audited=[]
    for batch,row in zip(schedule,ledger,strict=True):
        sources=Counter(stair=row['replay'])
        for i,_,n in batch['prose']:
            sources[train[i]['source']]+=n
        path+=row['delta']
        audited.append(dict(step=row['step'],source_targets=sources,path_since_300=path,
                            post_clip_norm=row['norm']*min(1.,1./(row['norm']+1e-6))))
    save(ROOT/'OPTIMIZATION.json',audited)
    journal=[json.loads(line) for line in (ROOT/'CALL_JOURNAL.jsonl').read_text().splitlines()]
    calls=Counter(r['kind'] for r in journal if r['event']=='returned')
    eval_forwards=sum(r['forwards'] for key,r in scores.items() if key!='C-300')
    monitor_forwards=2*(32+2)
    save(ROOT/'CALLS.json',dict(retained=calls['retained'],discarded_witness=calls['witness'],
        reconstruction=0,unpaired_begin=len(journal)-2*calls.total(),
        optimizer_calls=calls.total(),greedy_panel_forwards=eval_forwards,
        monitoring_forwards=monitor_forwards,total_forwards=calls.total()+eval_forwards+monitor_forwards))
    lines=['|更新|固定DEV NLL|追加DEV NLL|TRAIN標本 NLL|STAIR監視 NLL|caption保持|全caption|固定・追加の自然な二文|',
           '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for k in (300,450,600):
        r=scores[f'C-{k}'];n=r['nll'];c=r['counts']
        lines.append(f"|{k}|{n['prose']:.4f}|{n['new']:.4f}|{r['train_sample']:.4f}|{r['replay']:.4f}|{c['caption_retained']}/21|{c['caption_natural']}/32|{c['prose_two']+c['new_two']}/25|")
    lines.extend(['','|隔離診断|本文NLL|自然な一文|自然な二文|最初の機械的4-gram再出現位置|',
                  '|---:|---:|---:|---:|---:|'])
    for k in (300,600):
        r=scores[f'heldout-{k}'];c=r['counts']
        lines.append(f"|{k}|{r['nll']['heldout']:.4f}|{int(c['heldout_one'])}/1|{int(c['heldout_two'])}/1|{r['repeat_median']['heldout']}|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    build()
