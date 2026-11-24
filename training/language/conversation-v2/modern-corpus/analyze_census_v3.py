"""Stream all quarantined source snapshots through own BPE and extraction rules."""
import pathlib,json,gzip,hashlib,sys,collections,re,statistics,os
from extract_prose import extract
from acquire_pilot import Text
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent))
from new_tokenizer import Encoder

def main():
 status=json.loads((D/'CENSUS_STATUS.json').read_text());assert status['complete'];tok=json.loads((D.parent/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']];pilot={r['id']:r for r in map(json.loads,gzip.open(D/'private/pilot-candidates.jsonl.gz','rt'))};counts=collections.Counter();years=collections.Counter();body_lens=[];safe_lens=[];canon=set();ids=set();changed=[];index=[]
 with gzip.open(D/'private/census-prose-v3.pending','wt')as out:
  for receipt in status['receipts']:
   path=D/'private/census'/f"{receipt['page']:03d}.json.gz";raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
   for post in json.loads(raw):
    assert post['id']not in ids;ids.add(post['id']);content=post['content']['rendered'];content_sha=hashlib.sha256(content.encode()).hexdigest();parser=Text();parser.feed(content);full='\n'.join(x.strip()for x in ''.join(parser.parts).splitlines()if x.strip());ts=enc(full);assert b''.join(pieces[t]for t in ts)==full.encode();canon_sha=hashlib.sha256(''.join(full.split()).casefold().encode()).hexdigest();counts['canonical_duplicate_articles']+=canon_sha in canon;canon.add(canon_sha);counts['full_candidate_characters']+=len(full);counts['full_candidate_body_tokens']+=len(ts);body_lens.append(len(ts));years[post['date_gmt'][:4]]+=1
    if post['id']in pilot:
     counts['overlap_with_initial100']+=1
     if content_sha!=pilot[post['id']]['raw_content_sha256']:changed.append(post['id'])
    whole_hold=bool(re.search(r'転載|再掲載|再掲|コンテンツ共有|協力を得て|with permission|originally (?:published|appeared) (?:by|on|in)|翻訳転載',content,re.I));safe=0
    for para in extract(content):
     if para['exclusion_reasons']or whole_hold:continue
     text=para['text'];t=enc(text);assert b''.join(pieces[x]for x in t)==text.encode();safe+=1;counts['mechanically_eligible_characters']+=len(text);counts['mechanically_eligible_body_tokens']+=len(t);counts['replacement_characters_in_candidates']+=text.count('\ufffd');safe_lens.append(len(t));out.write(json.dumps(dict(article_id=post['id'],source_url=post['link'],source_content_sha256=content_sha,source_response_sha256=receipt['sha256'],source_paragraph_index=para['ordinal'],source_block_index=para['source_block_index'],text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),body_token_count=len(t),author_source_id=post['author'],date_gmt=post['date_gmt'],modified_gmt=post['modified_gmt'],categories=post['categories'],admission='quarantined mechanically filtered candidate',EOS_approved=False),ensure_ascii=False)+'\n')
    counts['mechanically_eligible_paragraphs']+=safe;counts['articles_with_eligible_paragraphs']+=safe>0;index.append(dict(id=post['id'],url=post['link'],title=post['title']['rendered'],date_gmt=post['date_gmt'],modified_gmt=post['modified_gmt'],categories=post['categories'],raw_content_sha256=content_sha,candidate_body_tokens=len(ts),filtered_paragraphs=safe,whole_article_hold=whole_hold))
 os.replace(D/'private/census-prose-v3.pending',D/'private/census-prose-v3.jsonl.gz')
 result=dict(unique_articles=len(ids),new_unique_articles_beyond_initial100=len(ids)-counts['overlap_with_initial100'],counts=dict(counts),publication_years=dict(sorted(years.items())),changed_content_since_pilot=changed,full_article_token_length=dict(min=min(body_lens),median=statistics.median(body_lens),max=max(body_lens)),filtered_paragraphs_fit_context256=sum(n+2<=256 for n in safe_lens),filtered_paragraphs_over_context256=sum(n+2>256 for n in safe_lens),admitted_body_tokens=0,optimizer_updates=0,all_full_and_filtered_text_byte_roundtrip=True,warning='Filtered is not rights/semantic/factual/privacy approval; attribution incomplete beyond100. Original paragraph order indices preserved, no artificial EOS.')
 (D/'CENSUS_TOKEN_AUDIT-v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(D/'CENSUS_INDEX-v3.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
