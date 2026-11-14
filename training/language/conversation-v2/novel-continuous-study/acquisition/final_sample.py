import os
import json,gzip,pathlib,hashlib,collections
C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));P=pathlib.Path(__file__).resolve().parents[1];a=[json.loads(x)for x in gzip.decompress((P/'new-pool-reviewed-by-machine.jsonl.gz').read_bytes()).splitlines()];out=[]
for source in sorted({x['source']for x in a}):
 bins=collections.defaultdict(list)
 for r in a:
  if r['source']!=source:continue
  bins[(r['category'],'short'if len(r['tokens'])<=256 else'long')].append(r)
 seen=collections.Counter()
 for key,rr in sorted(bins.items()):
  rr.sort(key=lambda r:hashlib.sha256(('novel-FINAL-quality-v1|'+r['id']).encode()).hexdigest());n=0
  for r in rr:
   if seen[r['family']]>=4:continue
   out.append(r);seen[r['family']]+=1;n+=1
   if n>=(1 if source=='jawikivoyage_new'else 2):break
assert len({r['id']for r in out})==len(out);(C/'FINAL_SAMPLE-private.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(P/'FINAL_SAMPLE_LOCK.json').write_text(json.dumps(dict(seed='novel-FINAL-quality-v1',before_model=True,records=[dict(id=r['id'],source=r['source'],family=r['family'],text_SHA=r['text_SHA'],category_proxy=r['category'],length=len(r['tokens']))for r in out],private_full_sample_SHA=hashlib.sha256((C/'FINAL_SAMPLE-private.json').read_bytes()).hexdigest(),rule='Per source/category/BPE<=256orlong stratum SHA order; max4perfamily; 2perstratum for major sources,1forVoyage; no model-output-based selection',optimizer_calls=0,model_forwards=0),ensure_ascii=False,indent=2)+'\n');print('sample',len(out),collections.Counter(x['source']for x in out))
for i,r in enumerate(out[:8]):print(i,r['id'],r['title'],r['text'])
