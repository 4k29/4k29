"""Known-open DEV only. Exact and bounded lexical near overlap, not semantic independence."""
import collections,gzip,json,pathlib,re,unicodedata
from build import HERE,V2,canonical,sha

def all_strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,list):
  for v in x:yield from all_strings(v)
 elif isinstance(x,dict):
  for v in x.values():yield from all_strings(v)
def main():
 refs=[];files=[]
 for partition in ['train','dev']:
  p=V2/'data'/(partition+'.docs.jsonl');files.append({'path':str(p.relative_to(V2)),'sha256':sha(p.read_bytes())})
  for l in p.open():
   d=json.loads(l)
   for u in d['utterances']:refs.append((partition+':'+d['id']+':'+str(u['ordinal']),canonical(u['text'])))
 for name in ['epoch1/content-dev.json','epoch1/unified32-dev.json','foundation-data/evaluation/human-dev.json','foundation-data/evaluation/researcher-input-dev.json']:
  p=V2/name;files.append({'path':name,'sha256':sha(p.read_bytes())})
  d=json.loads(p.read_text())
  for i,s in enumerate(all_strings(d.get('cases',d))):refs.append((name+':'+str(i),canonical(s)))
 exact=collections.defaultdict(list);post=collections.defaultdict(list);gramcache={}
 for ident,text in refs:
  exact[text].append(ident)
  if len(text)<20:continue
  gs={sha(text[i:i+5].encode())[:16]for i in range(len(text)-4)};gramcache[ident]=(len(text),gs)
  for sig in sorted(gs)[:4]:post[sig].append(ident)
 unique={}
 for name in ['conversations.jsonl.gz','oasst-conversations.jsonl.gz']:
  p=HERE/'derived'/name
  for l in gzip.open(p,'rt'):
   for u in json.loads(l)['utterances']:unique[u['id']]=canonical(u['text'])
 hits=[];short=collections.Counter();near=[];comparisons=0;skipped=0
 for ident,text in unique.items():
  if text in exact:
   if len(text)>=20:hits.append({'id':ident,'reference_ids':exact[text],'text_sha256':sha(text.encode()),'characters':len(text)})
   else:short[len(text)]+=1
  if len(text)<20:continue
  g={sha(text[i:i+5].encode())[:16]for i in range(len(text)-4)};candidates=collections.Counter()
  for sig in sorted(g)[:4]:
   if len(post[sig])>512:skipped+=1;continue
   candidates.update(post[sig])
  for rid,n in candidates.items():
   if n<2:continue
   length,other=gramcache[rid]
   if min(length,len(text))/max(length,len(text))<.8:continue
   comparisons+=1;j=len(g&other)/len(g|other)
   if j>=.85:near.append({'id':ident,'reference_id':rid,'jaccard':j,'same_exact':text in exact})
 result={'sources':files,'new_unique_messages':len(unique),'nontrivial_exact_overlaps':hits,'short_exact_overlap_unique_messages_by_length':dict(short),'verified_lexical_near_overlaps':near,'near_comparisons':comparisons,'frequent_signature_skips':skipped,'method':'NFC+whitespace removal; >=20chars;4minimumSHA256char5gram signatures >=2 shared;postingcap512;lengthratio>=.8;fullJaccard>=.85','limitations':'Known-open DEV and priorRP only. Short expressions reported separately. Not semantic/paraphrase/family independence or exhaustive near-duplicate proof. No sealedTEST read.'}
 (HERE/'derived/known-data-overlap.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k not in ['sources','nontrivial_exact_overlaps','verified_lexical_near_overlaps']});print('exact',len(hits),'near',len(near))
if __name__=='__main__':main()
