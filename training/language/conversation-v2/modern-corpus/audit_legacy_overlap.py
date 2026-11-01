"""Bounded exact/character-shingle overlap against previously admitted train/dev only.
No sealed TEST files are opened. Matching shingles are a risk screen, not proof of leakage.
"""
import pathlib,json,gzip,hashlib,re,collections,time
D=pathlib.Path(__file__).resolve().parent
K=32;STRIDE=8
def canonical(s):return re.sub(r'\s+','',s).casefold()
def shingles(s):
 s=canonical(s)
 return {hashlib.blake2b(s[i:i+K].encode(),digest_size=8).digest()for i in range(0,max(0,len(s)-K+1),STRIDE)}
def main():
 start=time.time();reference=D.parent/'diverse-foundation/corpus.jsonl.gz';sets={'train':set(),'dev':set()};counts=collections.Counter();exact={'train':set(),'dev':set()}
 for line in gzip.open(reference,'rt'):
  row=json.loads(line);split=row['split']
  if split not in sets:continue
  text=row['text'];sets[split].update(shingles(text));exact[split].add(hashlib.sha256(canonical(text).encode()).hexdigest());counts[split]+=1
 out=[];summary=collections.Counter()
 for line in gzip.open(D/'private/contiguous-prose-runs.jsonl.gz','rt'):
  row=json.loads(line);ss=shingles(row['text']);sha=hashlib.sha256(canonical(row['text']).encode()).hexdigest();matches={split:len(ss&s)for split,s in sets.items()};is_exact={split:sha in s for split,s in exact.items()}
  for split in sets:summary[split+'_matching_runs']+=matches[split]>0;summary[split+'_exact_runs']+=is_exact[split]
  out.append(dict(article_id=row['article_id'],paragraph_indices=row['paragraph_indices'],text_sha256=row['text_sha256'],sampled_unique_shingles=len(ss),matches=matches,exact=is_exact,admission='hold'))
 with gzip.open(D/'private/legacy-overlap-runs.jsonl.gz','wt')as f:
  for r in out:f.write(json.dumps(r)+'\n')
 result=dict(reference=str(reference),reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),reference_rows=dict(counts),shingle_characters=K,stride=STRIDE,reference_unique_shingles={k:len(v)for k,v in sets.items()},candidate_runs=len(out),counts=dict(summary),seconds=time.time()-start,limitations='Whitespace/case canonicalization; sampled shingle screen may miss shifted near-duplicates and count shared common language. No author/family independence implied. No TEST inspected.',admitted_tokens=0)
 (D/'LEGACY_OVERLAP_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
