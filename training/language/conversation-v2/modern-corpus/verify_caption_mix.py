"""Verify byte restoration, genuine boundary contracts and complete teacher coverage.
Standard-library only: suitable for public CI, no model or sealed TEST loading.
"""
import pathlib,json,gzip,hashlib,collections
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation'
def main():
 audit=json.loads((D/'DATASET_AUDIT.json').read_text());cp=D/'corpus.jsonl.gz';sp=D/'schedule.json.gz';assert hashlib.sha256(cp.read_bytes()).hexdigest()==audit['corpus_sha256'];assert hashlib.sha256(sp.read_bytes()).hexdigest()==audit['schedule_sha256'];pieces=[bytes.fromhex(s)for s in json.loads((N.parent/'data/tokenizer.json').read_text())['bytes']];rows=[json.loads(s)for s in gzip.open(cp,'rt')];schedule=json.load(gzip.open(sp,'rt'));ids=set();counts=collections.Counter();held={r['id']for r in json.loads((N/'STAIR_SPLIT_AUDIT.json').read_text())['held']};dev_images=set(json.loads((N/'STAIR_DEV_FAMILIES.json').read_text())['original_TRAIN_image_ids_reserved_for_DEV'])
 for r in rows:
  assert r['id']not in ids;ids.add(r['id']);t=r['tokens'];assert 0 not in t and 5 not in t and 1 not in t[1:];assert(t[0]==1)==bool(r.get('BOS',True));assert sum(v>=6 for v in t)==r['body_token_count'];assert all(0<=v<len(pieces)for v in t)
  if r['source']=='realpersona':
   cur=1
   for u in r['utterances']:
    assert t[cur]==u['localRoleToken'];cur+=1;body=[]
    while t[cur]!=2:assert t[cur]>=6;body.append(t[cur]);cur+=1
    assert b''.join(pieces[v]for v in body)==u['text'].encode();cur+=1
   assert cur==len(t)
  else:assert b''.join(pieces[v]for v in t if v>=6)==r['text'].encode()
  if r['source']=='jaquad':assert 2 not in t
  if r['source']=='stair':
   assert r['id']not in held and r['original_image_id']not in dev_images
   assert t[0]==1 and t[-1]==2 and len(t)<=257 and set(t[1:-1]).isdisjoint({0,1,2,3,4,5})
 expected={(i,start)for i,r in enumerate(rows)for start in range(0,len(r['tokens'])-1,256)};observed=set();targets=0
 for batch in schedule['batches']:
  valid=sum(ref['length']-1 for ref in batch);width=max(ref['length']-1 for ref in batch);assert valid<=1024 and len(batch)<=128 and width*len(batch)<=2048
  for ref in batch:
   i,start=ref['record'],ref['start'];assert(i,start)not in observed;observed.add((i,start));t=rows[i]['tokens'][start:start+ref['length']];assert ref['length']==min(257,len(rows[i]['tokens'])-start);targets+=len(t)-1;counts.update(dict(EOS=t[1:].count(2),roles=t[1:].count(3)+t[1:].count(4),BOS=t[1:].count(1),PAD=t[1:].count(0)))
 assert expected==observed;assert targets==audit['full_pass_targets']==schedule['targets'];assert counts['BOS']==counts['PAD']==0;assert counts['EOS']==audit['counts']['EOS_targets']and counts['roles']==audit['counts']['role_targets'];print('Verified',len(rows),'units,',targets,'unique teacher positions, exact source UTF8, preserved no-BOS excerpts and no fake EOS; counts',dict(counts))
if __name__=='__main__':main()
