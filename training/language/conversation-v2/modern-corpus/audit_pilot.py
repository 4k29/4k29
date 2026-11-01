"""Local integrity and public byline audit; no TRAIN promotion or network requests."""
import pathlib,json,gzip,hashlib,re,html
D=pathlib.Path(__file__).resolve().parent;P=D/'private'
def run():
 rows=list(map(json.loads,gzip.open(P/'pilot-candidates.jsonl.gz','rt')));assert len(rows)==100 and len({r['id']for r in rows})==100
 receipts=json.loads((D/'REVIEW_PAGE_RECEIPTS.json').read_text());assert len(receipts)==12;attributions=[]
 for r in receipts:
  path=P/f"review-{r['id']}.html";raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];s=raw.decode()
  authors=re.findall(r'<meta\s+name=[\"\x27]author[\"\x27]\s+content=[\"\x27]([^\"\x27]+)',s,re.I)
  contributors=re.findall(r"<div class=['\"]contributor-name['\"]>(.*?)</div>",s,re.S)
  contributors=[html.unescape(re.sub('<[^>]+>',' ',x)).strip()for x in contributors]
  attributions.append(dict(id=r['id'],url=r['url'],declared_original_authors=sorted(set(map(html.unescape,authors))),public_credit_lines=sorted(set(contributors)),source_page_sha256=r['sha256'],rights='CC-BY3 only GV-created text; quotation/photo/partner exceptions still pending'))
 (D/'SAMPLE_ATTRIBUTIONS.json').write_text(json.dumps(attributions,ensure_ascii=False,indent=2)+'\n')
 for r in json.loads((D/'PILOT_SUMMARY.json').read_text())['receipts']:
  name='pilot-'+str(r['url'].split('page=')[-1].split('&')[0])+'.json';b=(P/name).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
 result=dict(candidate_posts=100,review_source_SHA_verified=12,review_public_author_meta_found=sum(bool(r['declared_original_authors'])for r in attributions),review_public_credit_lines_found=sum(bool(r['public_credit_lines'])for r in attributions),API_user_endpoint_bypass=False,TRAIN_admission=0,optimizer_updates=0)
 (D/'PILOT_INTEGRITY.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
