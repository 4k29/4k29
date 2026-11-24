"""Internal original-paragraph duplicate screen, with explicit approximate scope."""
import pathlib,gzip,json,re,zlib,collections,hashlib,time
D=pathlib.Path(__file__).resolve().parent

def canon(text):return re.sub(r'\s+','',text).casefold()
def grams(text):return {zlib.crc32(text[i:i+13].encode())for i in range(max(0,len(text)-12))}
def main():
 start=time.time();rows=[json.loads(line)for line in gzip.open(D/'private/census-prose-v3.jsonl.gz','rt')];exact={};unique=[];duplicates=[]
 for row in rows:
  key=hashlib.sha256(canon(row['text']).encode()).hexdigest()
  if key in exact:duplicates.append(dict(article_id=row['article_id'],paragraph=row['source_paragraph_index'],same_as=exact[key],sha256=key))
  else:exact[key]=dict(article_id=row['article_id'],paragraph=row['source_paragraph_index']);unique.append(row)
 buckets=collections.defaultdict(list);near=[];signatures=[];candidate_pairs=0
 for i,row in enumerate(unique):
  ss=grams(canon(row['text']));sig=sorted(ss)[:64];hits=collections.Counter()
  for h in sig:
   for j in buckets[h]:hits[j]+=1
  for j,n in hits.items():
   if n<4:continue
   candidate_pairs+=1;other=grams(canon(unique[j]['text']));ratio=len(ss&other)/min(len(ss),len(other))if ss and other else 0
   if ratio>=.85:near.append(dict(article_ids=[row['article_id'],unique[j]['article_id']],paragraphs=[row['source_paragraph_index'],unique[j]['source_paragraph_index']],shorter_shingle_containment=ratio))
  for h in sig:buckets[h].append(i)
 result=dict(input_paragraphs=len(rows),unique_canonical_paragraphs=len(unique),exact_duplicate_paragraph_positions=len(duplicates),near_duplicate_pairs=len(near),candidate_pairs_verified=candidate_pairs,method='64 lowest CRC32 of13-character shingles; >=4 shared signature values, then >=85% shorter-set shingle containment',limitations='Approximate screen, not exhaustive semantic similarity or author independence; same-family determination also requires original-story credits. Hash collisions possible. No source text released.',seconds=time.time()-start,exact=duplicates,near=near,admitted_tokens=0,optimizer_updates=0)
 (D/'INTERNAL_DUPLICATE_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in result.items()if k not in {'exact','near'}})
if __name__=='__main__':main()
