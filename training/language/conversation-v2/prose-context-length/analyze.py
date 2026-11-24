"""Produce the paired NLL and fixed-panel tables from raw saved outputs."""
import gzip
import json
import math
from collections import Counter,defaultdict
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'prose-budget-scale'
POINTS=(300,400,450,500,600)

def read(path):
    return json.loads(path.read_text())

def raw(path):
    return json.loads(gzip.decompress(path.read_bytes()))

def save(name,obj):
    (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n')

def files(arm,k):
    directory=(OLD.parent/'prose-lr-decay' if k==300 else OLD if arm=='A' and k in (450,600)
               else ROOT/'control' if arm=='A' else ROOT)
    base=directory/f'C-{k}'
    return Path(f'{base}.json.gz'),Path(f'{base}-sample.json')

def average(seq):
    return math.fsum(seq)/len(seq) if seq else None

def prediction(case):
    losses=[-math.log(v['p_ref']) for v,t in zip(case['teacher'],case['gold']) if t not in (2,16)]
    i=case['first_mismatch']
    gap=[] if i is None else [
        math.log(b['p_ref'])-math.log(a['p_ref'])
        for a,b in zip(case['steps'][i:i+32],case['teacher'][i:i+32]) if a['p_ref'] and b['p_ref']]
    repeat=case['repeat']['start'] if case['repeat'] else None
    return losses,gap,repeat

def signatures():
    judged=read(OLD/'CASE_RESULTS.json')
    known={}
    for k in (300,450,600):
        data=raw(files('A',k)[0])
        for case,label in zip(data['cases'],judged[f'C-{k}'],strict=True):
            assert case['id']==label['id']
            known[(case['id'],tuple(case['generated']))]=label
    return judged,known

def main():
    judged,known=signatures()
    baseline=judged['C-300']
    acquired=read(ROOT/'SEMANTIC.json')
    banks=set()
    for p in (OLD/'TRAIN.json',ROOT.parent/'broad-prose-replay/TRAIN.json'):
        for row in read(p):
            t=row['prefix']+row['gold'][:row.get('eligible_targets',len(row['gold']))]
            banks.update(tuple(t[i:i+12]) for i in range(len(t)-11))
    labels={}
    score={}
    forwards=0
    for arm in 'AB':
        for k in POINTS:
            key=f'{arm}-{k}'
            f,m=files(arm,k)
            data=raw(f)
            if f.is_relative_to(ROOT):
                forwards+=data['forwards']
            cases=[]
            counts=Counter()
            nll=defaultdict(list)
            gaps=defaultdict(list)
            repeats=defaultdict(list)
            for i,(r,base) in enumerate(zip(data['cases'],baseline,strict=True)):
                p=base['panel']
                assert base['id']==r['id']
                previous=known.get((r['id'],tuple(r['generated'])))
                note=acquired.get(key,{}).get(str(i))
                if p!='train':
                    assert previous is not None or note is not None,(key,i,r['text'])
                if note is None:
                    note=previous
                loss,gap,repeat=prediction(r)
                nll[p].extend(loss)
                gaps[p].extend(gap)
                if repeat is not None:
                    repeats[p].append(repeat)
                seq=r['generated']
                matches=[j for j in range(len(seq)-11) if tuple(seq[j:j+12]) in banks]
                one=bool(note and note.get('one'))
                two=bool(note and note.get('two'))
                caption=bool(note and note.get('caption'))
                counts.update({p:1,f'{p}_one':int(one),f'{p}_two':int(two),f'{p}_eos':int(r['stop']=='EOS'),
                               f'{p}_repeat4':int(repeat is not None),f'{p}_match12':int(bool(matches))})
                if p=='caption':
                    counts.update(caption_natural=int(caption),caption_retained=int(caption and base['initial_caption']),
                                  caption_added=int(caption and not base['initial_caption']))
                manual=note and (note.get('manual') or note)
                if manual and 'harmful_repetition' in manual:
                    counts.update({f'{p}_harmful':int(manual['harmful_repetition']),f'{p}_judged_harm':1})
                cases.append(dict(id=r['id'],panel=p,caption=caption,initial_caption=base['initial_caption'],
                    nll=average(loss),gap=average(gap),repeat4=repeat,first_departure=r['first_mismatch'],
                    first_repeat_topk=r['steps'][repeat] if repeat is not None else None,
                    stop=r['stop'],match12=matches,one=one,two=two,review=manual))
            sample=read(m)
            labels[key]=cases
            score[key]=dict(counts=counts,nll={p:average(v) for p,v in nll.items()},
                reference_self_logp_gap={p:average(v) for p,v in gaps.items()},
                median_repeat4={p:median(v) for p,v in repeats.items()},train_sample=sample['nll'],
                replay=sample['historically_seen_disjoint_monitor_nll'])
    paired={}
    for arm in 'AB':
        data=raw(ROOT/'paired'/f'{arm}.json.gz')
        forwards+=data['forwards']
        rows=defaultdict(list)
        detail=[]
        for r in data['cases']:
            loss,gap,repeat=prediction(r)
            rows[r['id'].rsplit(':',1)[-1]].extend(loss)
            detail.append(dict(id=r['id'],nll=average(loss),repeat4=repeat,gap=average(gap)))
        paired[arm]=dict(nll={name:average(v) for name,v in rows.items()},
                         targets={name:len(v) for name,v in rows.items()},cases=detail)
    for arm in 'AB':
        p=OLD/'heldout-600.json.gz' if arm=='A' else ROOT/'paired/heldout-B-600.json.gz'
        data=raw(p)
        if arm=='B':
            forwards+=data['forwards']
        r=data['cases'][0]
        loss,gap,repeat=prediction(r)
        score[f'heldout-{arm}']=dict(id=r['id'],nll=average(loss),gap=average(gap),repeat4=repeat,
                                  review=acquired[f'heldout-{arm}']['0'])
    save('METRICS.json',score)
    save('CASE_RESULTS.json',labels)
    save('PAIRED_METRICS.json',paired)
    calls=Counter()
    for f in (ROOT/'CALL_JOURNAL.jsonl',ROOT/'control/CALL_JOURNAL.jsonl'):
        rows=[json.loads(line) for line in f.read_text().splitlines()]
        assert rows[::2]==[dict(r,event='begin') for r in rows[1::2]]
        calls.update(r['kind'] for r in rows[1::2])
    monitor_forwards=6*(32+2)
    save('CALLS.json',dict(optimizer_calls=dict(calls),optimizer_total=calls.total(),
        generation_and_teacher_forward=forwards,monitor_forward=monitor_forwards,
        forward_total=calls.total()+forwards+monitor_forwards))
    lines=['|条件・更新|固定DEV NLL|追加DEV NLL|TRAIN標本 NLL|STAIR監視 NLL|旧caption保持|全caption|自然な一文／二文（各25件）|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm in 'AB':
        for k in POINTS:
            r=score[f'{arm}-{k}'];c=r['counts'];n=r['nll']
            lines.append(f"|{arm} {k}|{n['prose']:.4f}|{n['new']:.4f}|{r['train_sample']:.4f}|{r['replay']:.4f}|{c['caption_retained']}/21|{c['caption_natural']}/32|{c['prose_one']+c['new_one']}／{c['prose_two']+c['new_two']}|")
    lines += ['','|600更新：対象TRAIN行|元の履歴NLL|短い履歴NLL|差（短−元）|','|---|---:|---:|---:|']
    for arm in 'AB':
        n=paired[arm]['nll']
        lines.append(f"|{arm}|{n['full']:.4f}|{n['short']:.4f}|{n['short']-n['full']:+.4f}|")
    (ROOT/'TABLES.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    main()
