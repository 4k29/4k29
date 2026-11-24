"""Combine fixed generations, individual judgments, exposure and gradient records."""
import gzip
import json
import math
from collections import Counter
from statistics import median
from prepare import ROOT,BASE,FAMILY,read,save

def output_path(arm,step):
    if step==0 or arm=='A' and step!=10:
        return FAMILY/f'C-{step}.json.gz'
    return ROOT/f'{arm}-{step}.json.gz'

def rows(arm,step):
    return json.load(gzip.open(output_path(arm,step)))['cases']

def summarize():
    plan=read(ROOT/'PLAN.json')
    annotations=read(ROOT/'REVIEW_NOTES.json')
    archived=read(FAMILY/'JUDGMENTS.json')
    train=read(FAMILY/'TRAIN.json')
    replay=read(ROOT/'REPLAY.json')
    schedule=read(ROOT/'SCHEDULE.json')
    start={r['id'] for r in archived['C-0'] if r['caption']}
    assert len(start)==21
    initial_tokens={r['id']:r['generated'] for r in rows('A',0) if r['panel']=='caption'}
    lookup={}
    for i,r in enumerate(train):
        tokens=r['prefix']+r['gold']
        for j in range(len(tokens)-11):
            lookup.setdefault(tuple(tokens[j:j+12]),set()).add(r['id'])
    results=[]
    readings={}
    collapse={}
    exposures={}
    for arm in 'ABCD':
        if arm!='A':
            ledger=read(ROOT/f'{arm}-ledger.json')
            counts={k:Counter() for k in ('prose','replay')}
            for batch in schedule[arm]:
                for group,source in [('prose',train),('replay',replay)]:
                    for i,start_i,n in batch[group]:
                        counts[group].update((i,j) for j in range(start_i,start_i+n))
            exposures[arm]={k:dict(independent=len(v),total=sum(v.values()),min=min(v.values(),default=0),
                             max=max(v.values(),default=0),by_document=dict(Counter({i:sum(n for (q,_),n in v.items() if q==i) for i in {idx for idx,_ in v}}))) for k,v in counts.items()}
            exposures[arm]['replay_eos']=sum(n for (i,j),n in counts['replay'].items() if replay[i]['gold'][j]==2)
        else:
            ledger=read(FAMILY/'C-ledger.json')
        for step in plan['steps']:
            key=f'{arm}-{step}'
            sample=rows(arm,step)
            shared=step==0 or arm=='A' and step!=10
            current=archived[f'C-{step}'] if shared else None
            notes=annotations.get(key,{})
            totals=Counter()
            nll={'prose':[],'train':[]}
            repeat=[]
            details=[]
            pairs=[]
            for i,r in enumerate(sample):
                panel=r['panel']; tokens=r['generated']; text=r['text']
                exact=panel=='train' and tokens==r['gold']
                label=current[i] if shared else None
                if label is not None:
                    assert label['id']==r['id']
                caption=bool(label['caption']) if shared else i in notes.get('caption',[])
                if panel=='caption' and r['id'] in start and tokens==initial_tokens[r['id']]:
                    caption=True
                two=bool(label['two']) if shared else exact or i in notes.get('two',[])
                endings=bool(label.get('ending_only')) if shared else i in notes.get('ending',[])
                leaked=label.get('leakage') if shared else notes.get('leakage',{}).get(str(i))
                cycle=None
                if not two and not caption:
                    for j in range(len(tokens)):
                        if any(tokens[j:j+n]==tokens[j+n:j+2*n]==tokens[j+2*n:j+3*n]
                               for n in range(1,min(16,(len(tokens)-j)//3)+1)):
                            cycle=j
                            break
                hit=[]
                if panel!='train':
                    for j in range(len(tokens)-11):
                        refs=lookup.get(tuple(tokens[j:j+12]))
                        if refs:
                            hit.append([j,sorted(refs)])
                totals[panel]+=1
                totals[f'{panel}_eos']+=r['stop']=='EOS'
                totals[f'{panel}_exact']+=exact
                totals[f'{panel}_two']+=two
                totals[f'{panel}_mechanical']+=bool(hit)
                totals[f'{panel}_leakage_examples']+=bool(leaked)
                totals[f'{panel}_triple_cycle']+=cycle is not None
                if panel in nll:
                    nll[panel].extend(-math.log(s['p_ref']) for s,t in zip(r['teacher'],r['gold']) if t not in (2,16))
                if panel=='caption':
                    totals['caption_natural']+=caption
                    totals['caption_retained']+=caption and r['id'] in start
                    totals['caption_new']+=caption and r['id'] not in start
                    totals['caption_ending_only']+=endings
                if panel=='prose' and r['repeat']:
                    point=r['repeat']['start']
                    repeat.append(point)
                    if step==300 and point<len(r['teacher']) and r['steps'][point]['p_ref'] is not None:
                        pairs.append(dict(id=r['id'],first_mismatch=r['first_mismatch'],repeat=r['repeat'],
                            teacher=r['teacher'][point],self=r['steps'][point]))
                reason=('人手資料の継続と全token一致' if exact else
                        '入力に沿う自然な短文' if caption else
                        '新しい二文で話題を展開' if two else
                        '空白・即時終了' if not text.strip() else
                        '候補なし。反復または文意・文脈の基準未達')
                details.append(dict(id=r['id'],panel=panel,exact=exact,two=two,caption=caption,
                                    initial_caption=r['id'] in start,ending_only=endings,
                                    mechanical_12token_hits=hit,leakage_example=leaked,triple_cycle=cycle,reason=reason))
            readings[key]=details
            if step==300:
                collapse[arm]=dict(pairs=pairs,repeat_median=median(repeat) if repeat else None)
            mon=ROOT/f'{key}-nll.json'
            scores={panel:math.fsum(values)/len(values) for panel,values in nll.items()}
            results.append(dict(arm=arm,step=step,counts=dict(totals),nll=scores,
                grad_clip=sum(row['clipped'] for row in ledger[:step]),
                median_repeat=median(repeat) if repeat else None,
                monitor=read(mon) if mon.exists() else None))
    save(ROOT/'METRICS.json',results)
    save(ROOT/'JUDGMENTS.json',readings)
    save(ROOT/'COLLAPSE.json',collapse)
    save(ROOT/'EXPOSURES.json',exposures)
    lines=['|条件|更新|TRAIN再現|DEV二文|caption保持|caption自然|TRAIN本文NLL|DEV本文NLL|Replay監視NLL|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in results:
        c=r['counts'];replay_nll=r['monitor']
        monitor_value=f"{replay_nll['historically_seen_disjoint_monitor_nll']:.3f}" if replay_nll else '—'
        lines.append(f"|{r['arm']}|{r['step']}|{c['train_exact']}/14|{c['prose_two']}/18|{c['caption_retained']}/21|{c['caption_natural']}/32|{r['nll']['train']:.3f}|{r['nll']['prose']:.3f}|{monitor_value}|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    summarize()
