import pathlib,json,hashlib,gzip,collections
P=pathlib.Path(__file__).resolve().parent;root=P.parents[3];plan=json.loads((P/'PLAN.json').read_text())
for rel,h in plan['sha256'].items():
 if rel.startswith(str(P.relative_to(root))+'/'):assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==h,rel
c=json.load(gzip.open(P/'corpus.json.gz','rt'));m=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));s=json.load(gzip.open(P/'schedule.json.gz','rt'));seen=set();by=collections.Counter()
for b in s:
 for r in b:
  i=r['record']
  for j in range(r['start']+1,r['start']+r['length']):
   k=(c[i]['source'],c[i]['id'],m[i]['new_to_original_token_position'][j]);assert k not in seen;seen.add(k);by[c[i]['source']]+=1
assert len(seen)==409856;assert dict(by)=={k:v['actual'] for k,v in json.loads((P/'SOURCE_AUDIT.json').read_text())['source_stats'].items()}
ledger=P/'UPDATES.jsonl'
if ledger.exists() and not ledger.is_symlink():
 x=[json.loads(l) for l in ledger.read_text().splitlines()];a=[(r['phase'],r['trace']) for r in x if r['event']=='intent'];b=[(r['phase'],r['trace']) for r in x if r['event']=='completed'];assert a==b
 ret=[r['trace'] for r in x if r['event']=='completed' and r['phase']=='retained'];assert [r['step'] for r in ret]==list(range(1,len(ret)+1));assert sum(r['targets'] for r in ret)==sum(q['length']-1 for batch in s[:len(ret)] for q in batch)
print('Frozen input and distinct teacher positions / ledger: PASS')
