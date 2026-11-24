"""Bounded official API pilot; private candidates, never automatic TRAIN admission."""
import pathlib,urllib.request,json,datetime,hashlib,time,gzip,re
from html.parser import HTMLParser
D=pathlib.Path(__file__).resolve().parent;P=D/'private';P.mkdir(exist_ok=True)
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,s):self.parts.append(s)
 def handle_endtag(self,t):
  if t in ['p','h2','h3','li']:self.parts.append('\n')
def main():
 receipts=[];rows=[]
 for page in range(1,5):
  url=f'https://jp.globalvoices.org/wp-json/wp/v2/posts?per_page=25&page={page}&before=2022-01-01T00:00:00&_embed=author';path=P/f'pilot-{page}.json';receipt=P/f'pilot-{page}.receipt.json'
  if path.exists():b=path.read_bytes();r=json.loads(receipt.read_text());assert hashlib.sha256(b).hexdigest()==r['sha256']
  else:
   start=datetime.datetime.now(datetime.timezone.utc).isoformat()
   with urllib.request.urlopen(url,timeout=45)as response:b=response.read();headers=dict(response.headers)
   path.write_bytes(b);r=dict(url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),headers=headers);receipt.write_text(json.dumps(r,indent=2)+'\n');time.sleep(10)
  receipts.append(r)
  for post in json.loads(b):
   raw=post['content']['rendered'];parser=Text();parser.feed(raw);text='\n'.join(s.strip()for s in ''.join(parser.parts).splitlines()if s.strip());reasons=[]
   if re.search(r'<blockquote|<iframe|<script|<pre|転載|無断|©|all rights reserved',raw,re.I):reasons.append('third-party quote/embed/rights proxy; manual review required')
   if re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}',text,re.I):reasons.append('contact information proxy')
   rows.append(dict(id=post['id'],url=post['link'],date=post['date_gmt'],modified=post['modified_gmt'],title=post['title']['rendered'],authors=[dict(id=a['id'],name=a['name'],link=a['link'])for a in post.get('_embedded',{}).get('author',[])if all(k in a for k in ['id','name','link'])],author_source_id=post['author'],text=text,raw_content_sha256=hashlib.sha256(raw.encode()).hexdigest(),text_sha256=hashlib.sha256(text.encode()).hexdigest(),license='CC-BY-3.0 for GV-created text; individual exceptions pending',status='quarantined candidate',hold_reasons=reasons,human_authorship='pre2022 is not proof of exclusively human authorship',EOS_approved=False))
 with gzip.open(P/'pilot-candidates.jsonl.gz','wt')as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 summary=dict(acquired_posts=len(rows),characters=sum(len(r['text'])for r in rows),proxy_unflagged=sum(not r['hold_reasons']for r in rows),admitted_posts=0,admitted_tokens=0,optimizer_updates=0,receipts=receipts,sample_ids=[r['id']for r in sorted(rows,key=lambda r:hashlib.sha256(('modern-pilot-v1|'+str(r['id'])).encode()).hexdigest())[:12]],sample_fixed_before_manual_review=True)
 (D/'PILOT_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in summary.items()if k!='receipts'},flush=True)
if __name__=='__main__':main()
