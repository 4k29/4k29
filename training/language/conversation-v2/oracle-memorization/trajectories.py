"""Aligned position summaries; generated pieces and probabilities remain in state files."""
import gzip,json,math,statistics
from collections import Counter
from freeze import P,read,save
def main():
    metrics=[];records=[]
    for state,labels in read(P/'SEMANTIC.json').items():
        rows=json.load(gzip.open(P/f'{state}.json.gz'))['cases']
        groups={}
        for r,label in zip(rows,labels):
            rep=r['repeat']
            j=rep['start'] if rep else None
            raw_step=r['steps'][j] if rep else None
            gold_step=r['teacher'][j] if rep and j<len(r['teacher']) else None
            row=dict(id=r['id'],state=state,panel=r['panel'],forced=len(r['forced']),first_ref_divergence=r['first_mismatch'],repeat_start=j,pre_repeat=r['steps'][max(0,j-1)] if rep else None,at_repeat=raw_step,teacher_at_repeat=gold_step,repeat_tokens=rep['tokens'] if rep else None,stop=r['stop'],autonomous=len(r['generated']))
            records.append(row)
            groups.setdefault((r['panel'],len(r['forced'])),[]).append(row)
        for (panel,k),group in groups.items():
            comparable=[r for r in group if r['teacher_at_repeat'] and r['at_repeat']]
            metrics.append(dict(state=state,panel=panel,k=k,paired_at_repeat=len(comparable),mean_p_gold_teacher=statistics.mean(r['teacher_at_repeat']['p_ref'] for r in comparable) if comparable else None,mean_p_gold_self=statistics.mean(r['at_repeat']['p_ref'] for r in comparable) if comparable else None))
    save(P/'TRAJECTORY_SUMMARY.json',metrics)
    (P/'TRAJECTORIES.json.gz').write_bytes(gzip.compress(json.dumps(records,separators=(',',':')).encode(),mtime=0))
if __name__=='__main__':main()
