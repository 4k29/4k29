"""Durable raw rollout trace reconciled to the exact retained optimizer checkpoint."""
import json,datetime

def reconcile_trace(path,step,calls,generated,negative):
    rows=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    kept=[r for r in rows if r['step']<=step];extra=[r for r in rows if r['step']>step]
    assert [r['step'] for r in kept]==list(range(10,step+1,10)), 'Retained rollout steps missing or duplicated'
    assert len(kept)==calls and sum(r['generatedTokens'] for r in kept)==generated and sum(r['negativePositions'] for r in kept)==negative
    if extra:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        path.with_name('unretained-rollouts-'+stamp+'.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in extra))
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in kept))

def append_trace(path,step,row,loss,record):
    data={k:v for k,v in record.items() if k!='tokens'}
    data.update(step=step,sourceRow=row,tokens=record['tokens'][0].tolist(),loss=float(loss.detach()))
    with path.open('a') as f:f.write(json.dumps(data,ensure_ascii=False)+'\n');f.flush()
