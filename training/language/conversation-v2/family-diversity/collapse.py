"""Compare held-out teacher forcing and greedy history at repeat positions."""
import gzip
import json
from statistics import mean, median
from prepare import ROOT, read, save

def summarize():
    results={}
    for arm in 'ABC':
        outputs=json.load(gzip.open(ROOT/f'{arm}-300.json.gz'))['cases']
        labels=read(ROOT/'JUDGMENTS.json')[f'{arm}-300']
        pairs=[]
        for row,label in zip(outputs,labels,strict=True):
            if row['panel']!='prose':continue
            point=row['repeat']['start'] if row['repeat'] else None
            known=point is not None and point<len(row['teacher']) and row['steps'][point]['p_ref'] is not None
            pairs.append(dict(id=row['id'],first_mismatch=row['first_mismatch'],repeat=row['repeat'],
                triple_cycle_witness=label['triple_cycle_witness'],p_gold_teacher=row['teacher'][point]['p_ref'] if known else None,
                p_gold_self=row['steps'][point]['p_ref'] if known else None,
                pre_repeat=row['steps'][max(0,point-1)] if point is not None else None,
                at_repeat=row['steps'][point] if point is not None else None))
        matched=[r for r in pairs if r['p_gold_teacher'] is not None]
        results[arm]=dict(matched=len(matched),p_gold_teacher=mean(r['p_gold_teacher'] for r in matched),
                          p_gold_self=mean(r['p_gold_self'] for r in matched),
                          first_mismatch_median=median(r['first_mismatch'] for r in pairs if r['first_mismatch'] is not None),
                          records=pairs)
    save(ROOT/'COLLAPSE.json',results)

if __name__=='__main__':
    summarize()
