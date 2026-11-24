"""Cross existing exposed TRAIN/DEV only. Never searches or opens sealed TEST."""
import pathlib,json,gzip,collections,hashlib,re
from deduplicate import canonical,shingles,signature
P=pathlib.Path(__file__).resolve().parent;OLD=pathlib.Path('/workspace/4k29/training/language/conversation-v2')

def references():
 old=OLD/'modern-corpus/next-foundation/corpus.jsonl.gz'
 with gzip.open(old,'rt')as f:
  for line in f:
   r=json.loads(line);text=r.get('text','')
   # Very short captions are not sufficient evidence of paragraph reuse.
   if len(canonical(text))>=80:yield dict(id=r['id'],kind='previous_TRAIN',text=text)
 for path in [OLD/'modern-corpus/next-foundation/EVALUATION.json',P/'PARAGRAPH_DEV_PROTOCOL.json']:
  d=json.loads(path.read_text())
  for i,r in enumerate(d['cases']):
   text=r.get('source_text',r.get('text',''))
   if text:yield dict(id=r.get('id',str(i)),kind='exposed_DEV',text=text)

def audit(rows):
 refs=[];sets=[];idx=collections.defaultdict(set);exact={}
 for r in references():
  ss=shingles(r['text']);j=len(refs);refs.append(r);sets.append(ss);exact[canonical(r['text'])]=j
  for h in signature(ss):idx[h].add(j)
 held=[];kept=[];comparisons=0
 for r in rows:
  text=canonical(r['text']);ss=shingles(r['text']);matches=set().union(*(idx[h]for h in signature(ss)));why=None
  if text in exact:matches.add(exact[text])
  for j in sorted(matches):
   comparisons+=1;other=canonical(refs[j]['text']);inter=len(ss&sets[j]);jac=inter/len(ss|sets[j]);contain=inter/min(len(ss),len(sets[j]));ratio=min(len(ss),len(sets[j]))/max(len(ss),len(sets[j]))
   if text==other or jac>=.8 or(contain>=.9 and ratio>=.6)or(min(len(text),len(other))>=120 and(text in other or other in text)):
    why=dict(reason='previous_train_or_exposed_DEV_overlap',reference_id=refs[j]['id'],reference_kind=refs[j]['kind'],jaccard=jac,containment=contain);break
  if why:held.append(dict(text_sha256=r['text_sha256'],source_cache=r['source_cache'],body_tokens=r['body_tokens'],**why))
  else:kept.append(r)
 return kept,held,dict(reference_units=len(refs),comparisons=comparisons,sealed_TEST_opened=False,method='Canonical full text and character13gram LSH candidates; exact containment >=120 chars; not exhaustive semantic duplicate detection',remaining_risk='Cannot certify author independence or absence of paraphrase overlap; common facts and phrases may appear across sources.')
