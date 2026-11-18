"""Derive quantitative summaries; semantic labels are read separately."""
import gzip,json,math,statistics
from collections import Counter
from freeze import P,V,read,save
def summarize(rows):
    teacher=[s for r in rows for s in r['teacher']]
    auto=[s for r in rows for s in r['steps'] if s['p_ref'] is not None]
    reps=[r['repeat']['start'] for r in rows if r['repeat']]
    out=dict(cases=len(rows),two=sum(r['judgment']['two'] for r in rows),exact=sum(r['generated']==r['gold'] for r in rows if r['gold']),eos=sum(r['stop']=='EOS' for r in rows),repeated=len(reps),median_repeat=statistics.median(reps) if reps else None,teacher_nll=-math.fsum(math.log(s['p_ref']) for s in teacher)/len(teacher) if teacher else None,aligned_self_ref_nll=-math.fsum(math.log(s['p_ref']) for s in auto)/len(auto) if auto else None,median_exact_prefix=statistics.median([r['first_mismatch'] if r['first_mismatch'] is not None else min(len(r['generated']),len(r['gold'])) for r in rows]))
    return out
def main():
    names=['initial','B-terminal','C-terminal','A-100','A-300','B-100','B-300']
    pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']]
    labels=read(P/'SEMANTIC.json')
    summary={};lines=['|状態|評価|参照長|件数|二文成立|完全再現|4-gram再出現|開始中央値|EOS|参照NLL|caption自然候補|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name in names:
        groups={}
        for i,r in enumerate(json.load(gzip.open(P/f'{name}.json.gz'))['cases']):
            assert r['raw_hex']==b''.join(pieces[t] for t in r['generated']).hex()
            assert r['generated']==[s['top5'][0][0] for s in r['steps']]
            lab=labels[name][i];assert (r['id'],len(r['forced']))==(lab['id'],lab['forced'])
            r['judgment']=lab
            groups.setdefault((r['panel'],len(r['forced'])),[]).append(r)
        summary[name]={}
        for (panel,k),rows in groups.items():
            a=summarize(rows);summary[name][f'{panel}-{k}']=a
            if panel=='caption':
                a['natural']=sum(r['judgment']['caption'] for r in rows)
                a['retained']=sum(r['judgment']['caption'] and r['judgment']['initial_caption'] for r in rows)
            nll=a['teacher_nll']
            lines.append('|'+ '|'.join(map(str,[name,panel,k,len(rows),a['two'],a['exact'],a['repeated'],a['median_repeat'],a['eos'],round(nll,3) if nll else '—',a.get('natural','—')]))+'|')
    save(P/'SUMMARY.json',summary)
    (P/'TABLES.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
