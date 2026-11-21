"""Score archived predictions and generate matched case-level tables."""
import gzip
import json
import math
from collections import Counter,defaultdict
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OLD=BASE/'prose-learning-rate'

def read(path):
    return json.loads(path.read_text())

def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n')

def raw(arm,k):
    p=OLD/f'B-{k}.json.gz' if k==150 or arm=='A' and k!=175 else ROOT/f'{arm}-{k}.json.gz'
    with gzip.open(p) as f:
        data=json.load(f)
    return data

def measure():
    plan=read(ROOT/'PLAN.json')
    old=read(OLD/'JUDGMENTS.json')
    notes=read(ROOT/'REVIEWS.json')
    initial={r['id'] for r in old['B-0'] if r['initial_pass']}
    assert len(initial)==21
    recognized={}
    for k in (150,200,250,300):
        for r,j in zip(raw('A',k)['cases'],old[f'B-{k}'],strict=True):
            assert r['id']==j['id']
            if r['panel']=='caption':
                recognized[(r['id'],tuple(r['generated']))]=j['natural_caption']
    train_bank=defaultdict(set)
    for r in read(BASE/'broad-prose-replay/TRAIN.json'):
        t=r['prefix']+r['gold']
        for j in range(len(t)-11):
            train_bank[tuple(t[j:j+12])].add(r['id'])
    new={r['id'] for r in read(BASE/'broad-prose-replay/NEW_DEV.json')}
    reference={}
    rows=[];decisions={}
    forwards=0
    for arm in 'ABC':
        ledger=read(ROOT/f'{arm}-ledger.json')
        for k in plan['steps']:
            key=f'{arm}-{k}'
            data=raw(arm,k)
            if k!=150 and (arm!='A' or k==175):
                forwards+=data['forwards']
            index=notes.get(key,{})
            sums=Counter();nll=defaultdict(list);repeats=defaultdict(list);labels=[]
            for i,r in enumerate(data['cases']):
                seq=r['generated'];panel='new' if r['id'] in new else r['panel']
                exact=panel=='train' and seq==r['gold']
                cap=panel=='caption' and (recognized.get((r['id'],tuple(seq)),False) or i in index.get('caption',[]))
                two=exact or i in index.get('two',[])
                one=two or i in index.get('one',[])
                sums[panel]+=1
                sums[f'{panel}_one']+=one
                sums[f'{panel}_two']+=two
                sums[f'{panel}_eos']+=r['stop']=='EOS'
                sums[f'{panel}_exact']+=exact
                if cap:
                    sums['caption_pass']+=1
                    sums['caption_retained']+=r['id'] in initial
                    sums['caption_new']+=r['id'] not in initial
                point=r['repeat']['start'] if r['repeat'] else None
                if point is not None:repeats[panel].append(point)
                cycle=None
                if not two and not cap:
                    cycle=next((j for j in range(len(seq)) if any(seq[j:j+n]==seq[j+n:j+2*n]==seq[j+2*n:j+3*n]
                                  for n in range(1,min(16,(len(seq)-j)//3)+1))),None)
                sums[f'{panel}_cycle']+=cycle is not None
                hits=[]
                if panel!='train':
                    hits=[[j,sorted(train_bank[tuple(seq[j:j+12])])] for j in range(len(seq)-11) if tuple(seq[j:j+12]) in train_bank]
                    sums[f'{panel}_match']+=bool(hits)
                v=[-math.log(s['p_ref']) for s,t in zip(r['teacher'],r['gold']) if t not in (2,16)]
                nll[panel].extend(v)
                score=math.fsum(v)/len(v) if v else None
                if arm=='A' and k==150:reference[r['id']]=score
                prev=reference[r['id']]
                reason='自然な短文補完' if cap else '参照の完全再現' if exact else '話題に沿う継続' if one else '文意または話題の基準未達'
                labels.append(dict(id=r['id'],panel=panel,caption=cap,initial_caption=r['id'] in initial,
                    one=one,two=two,reason=reason,stop=r['stop'],exact=exact,first_reference_departure=r['first_mismatch'],
                    nll=score,nll_delta_from_150=score-prev if score is not None else None,
                    repeat=r['repeat'],first_obvious_cycle=cycle,lf=seq.count(16),spaces=r['text'].count(' '),
                    train_matches_12=hits,leakage=index.get('leakage',{}).get(str(i)),
                    before_repeat=r['steps'][max(0,point-1)] if point is not None else None))
            decisions[key]=labels
            stats=ROOT/f'{key}-sample.json'
            if k==150 or arm=='A' and k!=175:stats=OLD/f'B-{k}-sample.json'
            sample=read(stats)
            present=ledger[:k-150]
            rows.append(dict(arm=arm,step=k,counts=sums,nll={p:math.fsum(v)/len(v) for p,v in nll.items() if v},
                            repeat_median={p:median(v) for p,v in repeats.items()},
                            train_sample=sample['nll'],replay_monitor=sample['historically_seen_disjoint_monitor_nll'],
                            cumulative=math.fsum(r['delta'] for r in present),
                            distance=present[-1]['distance'] if present else read(OLD/'B-150-distance.json')['total'],
                            clip=sum(r['clipped'] for r in present)))
    save(ROOT/'JUDGMENTS.json',decisions)
    save(ROOT/'METRICS.json',rows)
    save(ROOT/'CALLS.json',dict(retained=300,reconstruction=200,witness_discarded=4,optimizer_total=504,
         generated_panel_forwards=forwards,sampled_nll_forwards=306,gradient_forward=7,optimization_forward=504,
         total_forwards=forwards+306+7+504))
    lines=['|条件|更新|固定DEV NLL|追加DEV NLL|標本TRAIN NLL|Replay監視NLL|固定二文|追加二文|caption保持|初期からL2|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        c=r['counts'];n=r['nll']
        lines.append(f"|{r['arm']}|{r['step']}|{n['prose']:.3f}|{n['new']:.3f}|{r['train_sample']:.3f}|{r['replay_monitor']:.3f}|{c['prose_two']}/18|{c['new_two']}/7|{c['caption_retained']}/21|{r['distance']:.3f}|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    measure()
