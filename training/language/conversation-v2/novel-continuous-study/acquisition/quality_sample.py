import os
import json,gzip,pathlib,hashlib,collections
V=pathlib.Path(__file__).resolve().parents[2];P=V/'novel-continuous-study';C=pathlib.Path(os.environ.get('NOVEL_CACHE','/workspace/scratch/continuous'));a=[json.loads(x)for x in gzip.decompress((P/'pool.jsonl.gz').read_bytes()).splitlines()];out=[]
for source in sorted({x['source']for x in a}):
 bins=collections.defaultdict(list)
 for r in a:
  if r['source']!=source:continue
  bins[(r['category'],'short'if len(r['tokens'])<=200 else'long')].append(r)
 seen=collections.Counter()
 for key,rr in sorted(bins.items()):
  rr.sort(key=lambda r:hashlib.sha256(('novel-source-quality-v1|'+r['id']).encode()).hexdigest());n=0
  for r in rr:
   if seen[r['family']]>=4:continue
   out.append(r);seen[r['family']]+=1;n+=1
   if n>=(2 if source=='jawikibooks_new'else 1):break
assert len({r['id']for r in out})==len(out)
(C/'quality-wiki-private.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('sample',collections.Counter(x['source']for x in out))
for i,r in enumerate(out[:8]):print(i,r['id'],r['title'],r['text'])
