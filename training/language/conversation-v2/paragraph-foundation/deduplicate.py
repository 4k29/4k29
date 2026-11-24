"""Conservative exact and auditable near-duplicate decisions, no text repair."""
import re,hashlib,zlib,collections

def canonical(text):return ''.join(text.split()).casefold()
def shingles(text,n=13):
 s=canonical(text);return {zlib.crc32(s[i:i+n].encode())for i in range(max(1,len(s)-n+1))}
def signature(s,n=24):return sorted(s)[:n]
def deduplicate(rows,threshold=.80,containment=.90):
 kept=[];held=[];index=collections.defaultdict(set);exact={};sets=[];paragraph_owner={}
 for row in sorted(rows,key=lambda r:(-int(r['source_cache'].split('-')[1].startswith('r')),r['source_cache'],r['serial'])):
  text=row['text'];h=hashlib.sha256(canonical(text).encode()).hexdigest();reason=None;match=None;metrics={}
  if h in exact:reason='canonical_exact_unit';match=exact[h]
  paragraph_hashes=[hashlib.sha256(canonical(p).encode()).hexdigest()for p in text.split('\n\n')]
  if reason is None:
   owners=[paragraph_owner[p]for p in paragraph_hashes if p in paragraph_owner]
   if owners:reason='reused_original_paragraph_within_unit';match=owners[0]
  ss=shingles(text);sig=signature(ss)
  if reason is None:
   candidates=set().union(*(index[x]for x in sig))if sig else set()
   for j in sorted(candidates):
    prior=sets[j];intersection=len(ss&prior);jac=intersection/len(ss|prior);contain=intersection/min(len(ss),len(prior));ratio=min(len(ss),len(prior))/max(len(ss),len(prior))
    if jac>=threshold or(contain>=containment and ratio>=.60):reason='near_duplicate_character13grams';match=kept[j]['text_sha256'];metrics=dict(jaccard=jac,containment=contain,length_ratio=ratio);break
  if reason:
   held.append(dict(text_sha256=row['text_sha256'],source_cache=row['source_cache'],serial=row['serial'],reason=reason,matched_text_sha256=match,body_tokens=row['body_tokens'],**metrics));continue
  j=len(kept);kept.append(row);sets.append(ss);exact[h]=row['text_sha256']
  for x in sig:index[x].add(j)
  for p in paragraph_hashes:paragraph_owner[p]=row['text_sha256']
 return kept,held
