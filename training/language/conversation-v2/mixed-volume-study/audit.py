"""Original-position disjointness, byte preservation and exact teacher/batch contracts. No model."""
from build import *
def audit():
 prev=V/'mixed-retention-study';old=json.load(gzip.open(prev/'corpus.json.gz','rt'));om=json.load(gzip.open(prev/'POSITION_MAP.json.gz','rt'));osched=json.load(gzip.open(prev/'schedule.json.gz','rt'));c=json.load(gzip.open(P/'corpus.json.gz','rt'));maps=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));s=json.load(gzip.open(P/'schedule.json.gz','rt'));pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']];used=set();new=set();by=collections.Counter();types=collections.Counter();hist=collections.Counter();per=[];pad=0
 for b in osched:
  for r in b:
   i=r['record']
   for j in range(r['start']+1,r['start']+r['length']):used.add((old[i]['source'],old[i]['id'],om[i]['new_to_original_token_position'][j]))
 assert len(used)==590144 and c[:len(old)]==old
 for b in s:
  count=collections.Counter();width=max(r['length']-1 for r in b);pad+=len(b)*width-sum(r['length']-1 for r in b)
  for r in b:
   i=r['record'];t=c[i]['tokens'][r['start']:r['start']+r['length']];assert len(t)==r['length'] and 2<=len(t)<=257;assert 0 not in t and 5 not in t and 1 not in t[1:];hist[str(len(t)-1)]+=1
   for j,v in enumerate(t[1:],r['start']+1):
    k=(c[i]['source'],c[i]['id'],maps[i]['new_to_original_token_position'][j]);assert k not in used and k not in new;new.add(k);by[c[i]['source']]+=1;count[c[i]['source']]+=1;types['targets']+=1;types['body_nonLF']+=v>5 and v!=16;types['LF']+=v==16;types['EOS']+=v==2;types['role']+=v in [3,4]
  per.append(dict(count))
 for r in c:
  if r['source']=='realpersona':
   offset=1
   for u in r['utterances']:
    assert r['tokens'][offset]==u['localRoleToken'];offset+=1;b=[]
    while r['tokens'][offset]!=2:b.append(r['tokens'][offset]);offset+=1
    assert b''.join(pieces[t] for t in b)==u['text'].encode();offset+=1
   assert offset==len(r['tokens'])
  else:assert b''.join(pieces[t] for t in r['tokens'] if t>5)==r['text'].encode()
 assert len(new)==409856 and sum(by.values())==409856
 expected={k:r['actual'] for k,r in read(P/'SOURCE_AUDIT.json')['source_stats'].items()};assert dict(by)==expected
 result=dict(passed=True,prefix_positions=len(used),additional_positions=len(new),overlap=0,all_byte_roundtrips=True,teacher_shift='each source position j predicts t[j] from row preceding token at j-1; no cross document concatenation',teacher_counts=dict(types),padding_ignored=pad,input_length_histogram=dict(hist),batch_source_targets=per,cumulative_targets=1000000,midpoint_cumulative=800000,optimizer_updates=0,model_forwards=0)
 write(P/'TEACHER_AUDIT.json',result);print('Audit PASS',types)
if __name__=='__main__':audit()
