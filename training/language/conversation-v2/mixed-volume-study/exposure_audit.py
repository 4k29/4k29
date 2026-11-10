"""Save exact earlier original positions and per-boundary exposure. No model."""
from build import *
prev=V/'mixed-retention-study';oldc=json.load(gzip.open(prev/'corpus.json.gz','rt'));oldm=json.load(gzip.open(prev/'POSITION_MAP.json.gz','rt'));olds=json.load(gzip.open(prev/'schedule.json.gz','rt'));c=json.load(gzip.open(P/'corpus.json.gz','rt'));m=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));s=json.load(gzip.open(P/'schedule.json.gz','rt'))
def positions(cs,mp,bs):
 return {(cs[r['record']]['source'],cs[r['record']]['id'],mp[r['record']]['new_to_original_token_position'][j]) for b in bs for r in b for j in range(r['start']+1,r['start']+r['length'])}
old=positions(oldc,oldm,olds);new=positions(c,m,s);mid=positions(c,m,s[:205]);assert len(old)==590144 and len(new)==409856 and not old&new;gzwrite(P/'PREFIX_POSITIONS.json.gz',sorted(old));cases=[]
for q in read(V/'paragraph-foundation/paragraph-context-use/INPUT_PAIRS.json'):
 r=q['correct'];cases.append(dict(id='new32-'+str(q['index']),source_id=r['source_id'],original_position=r['source_position']))
for r in read(V/'paragraph-foundation/newline-followup/EIGHT_CASE_AUDIT.json')['cases']:cases.append(dict(id='old8-'+str(r['index']),source_id=r['source_id'],original_position=r['source_offset']))
for r in cases:
 k=('env_whitepaper',r['source_id'],r['original_position']);r.update(previous_prefix=k in old,additional_midpoint=k in mid,additional_terminal=k in new,classification='previous_prefix' if k in old else 'newly_exposed_addition' if k in new else 'not_exposed_this_series')
write(P/'BOUNDARY_EXPOSURE.json',dict(cases=cases,counts=dict(collections.Counter(r['classification'] for r in cases)),note='Not exposed this series does not imply never exposed in earlier model history; all are exposed research TRAIN diagnostics'))
print('Exposure',dict(collections.Counter(r['classification'] for r in cases)))
