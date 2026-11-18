from freeze import *
from collections import Counter
import statistics
from math import sqrt
def main():
    rows=read(P/'TRAIN.json')
    sources=[V/'gv-prose-pilot/corpus-C.jsonl.gz',V/'gv-collapse-diagnostic/ADDITIONAL.jsonl.gz']
    pool=[x for f in sources for x in map(json.loads,gzip.open(f))]
    audit=[];calls={}
    for r in rows:
        origin=pool[r['index']]
        entry={k:v for k,v in origin.items() if k in ('id','family','title','source','source_url','original_GV_URL','attribution','revision','timestamp','raw_content_SHA','text_SHA','license','transform','author_status','quality_admission','review_reason','verification_SHA','genre','category')}
        entry.update(A_unique=len(r['prefix']+r['gold'])-1,B_unique=len(r['gold']),passes=75,A_processed=75*(len(r['prefix']+r['gold'])-1),B_processed=75*len(r['gold']),EOS=0)
        audit.append(entry)
    save(P/'SOURCE_AUDIT.json',audit)
    for arm in 'AB':
        log=read(P/f'{arm}-ledger.json')
        calls[arm]=dict(retained=len(log),preflight_discarded=1,uninterrupted_step101_witness_discarded=1,optimizer_calls=len(log)+2,processed=sum(r['targets'] for r in log),clip_count=sum(r['clipped'] for r in log),mean_preclip_norm=statistics.mean(r['norm'] for r in log),initial4_mean_loss=statistics.mean(r['loss'] for r in log[:4]),final4_mean_loss=statistics.mean(r['loss'] for r in log[-4:]))
    calls['evaluation_forwards']={f.name:json.load(gzip.open(f))['forwards'] for f in P.glob('*.json.gz') if f.name not in ('TRAJECTORIES.json.gz',)}
    save(P/'CALLS.json',calls)
    save(P/'CHECKPOINT_INDEX.json',{p.parent.name:read(p)['sha256'] for p in sorted((P/'artifacts').glob('*/checkpoint.json'))})
if __name__=='__main__':main()
