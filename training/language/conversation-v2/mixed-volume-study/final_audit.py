"""Independent saved-result audit for CI: prefix disjointness, actual ledger, checkpoints. No torch."""
import pathlib,json,gzip,hashlib,collections
P=pathlib.Path(__file__).resolve().parent
load=lambda f:json.loads(f.read_text())
old={tuple(x) for x in json.load(gzip.open(P/'PREFIX_POSITIONS.json.gz','rt'))};assert len(old)==590144
c=json.load(gzip.open(P/'corpus.json.gz','rt'));mp=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));s=json.load(gzip.open(P/'schedule.json.gz','rt'));seen=set()
for batch in s:
 for r in batch:
  i=r['record']
  for j in range(r['start']+1,r['start']+r['length']):
   k=(c[i]['source'],c[i]['id'],mp[i]['new_to_original_token_position'][j]);assert k not in old and k not in seen;seen.add(k)
assert len(seen)==409856
l=[json.loads(z) for z in (P/'UPDATES.jsonl').read_text().splitlines()];a=[(r['phase'],r['trace']) for r in l if r['event']=='intent'];b=[(r['phase'],r['trace']) for r in l if r['event']=='completed'];assert a==b and len(a)==405
ret=[r['trace'] for r in l if r['event']=='completed' and r['phase']=='retained'];assert len(ret)==401 and [r['step'] for r in ret]==list(range(1,402));assert sum(r['targets'] for r in ret)==409856
for n in [4,205,401]:
 proof=load(P/f'GIT_RESTORE-{n}.json');assert proof['passed'] and proof['full_model_Adam_RNG_sampler_cursor_trace_integrity'];assert proof['optimizer_calls']==0
print('Completed result audit: disjoint590144+409856,405 actual calls,401 retained, full cold restore receipts: PASS')
