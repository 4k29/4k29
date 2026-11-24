"""Deterministic full-thread audit sampling. Does not infer rights or alter text."""
import argparse, gzip, hashlib, json
from pathlib import Path

def select(records, max_per_source=40, max_total=80):
    eligible=[]; counts={}; exclusions={}
    for r in records:
        reason=None
        if r.get('split') not in ('TRAIN','train','unassigned'): reason='not-train-or-explicit-unassigned'
        turns=r.get('utterances',[])
        if len(turns)<2: reason='less-than-two-turns'
        if sum(len(t['text']) for t in turns)>12000: reason='full-thread-over-character-cap'
        if reason:
            exclusions[reason]=exclusions.get(reason,0)+1; continue
        source=r['source']; thread=str(r.get('id',r.get('conversation_id')))
        key=hashlib.sha256(f'sns-quality-v1|{source}|{thread}'.encode()).hexdigest()
        eligible.append((key,r))
    out=[]; families=set()
    for key,r in sorted(eligible,key=lambda v:v[0]):
        source=r['source']; family=(source,r.get('conversation_family',r.get('id',r.get('conversation_id'))))
        if family in families or counts.get(source,0)>=max_per_source: continue
        if len(out)>=max_total: break
        out.append({'selectionSha256':key,'record':r})
        counts[source]=counts.get(source,0)+1; families.add(family)
    return {'plan':'PLAN.json','eligibleThreads':len(eligible),'exclusionCounts':exclusions,'selectedBySource':counts,'selectedThreads':len(out),'threads':out,'formalHumanEvaluation':False,'automaticAdmission':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');a=p.parse_args()
    path=Path(a.input); op=gzip.open if path.suffix=='.gz' else open
    with op(path,'rt',encoding='utf-8') as f: records=[json.loads(line) for line in f if line.strip()]
    out=select(records); out['inputSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    out['planSha256']=hashlib.sha256(Path(__file__).with_name('PLAN.json').read_bytes()).hexdigest()
    Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in out.items() if k!='threads'})
if __name__=='__main__': main()
