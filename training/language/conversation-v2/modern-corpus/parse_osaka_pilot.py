"""Extract original municipal HTML body, excluding navigation and contact blocks."""
from html.parser import HTMLParser
import pathlib,json,gzip,hashlib
D=pathlib.Path(__file__).resolve().parent
class Body(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.active=False;self.parts=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='div':
   if d.get('id')=='mol_contents':self.active=True;self.depth=1
   elif self.active:self.depth+=1
  if self.active and t in {'p','br','li','h2','h3','h4','tr'}:self.parts.append('\n')
 def handle_endtag(self,t):
  if self.active and t=='div':
   self.depth-=1
   if self.depth==0:self.active=False
  if self.active and t in {'p','li','h2','h3','h4','tr'}:self.parts.append('\n')
 def handle_data(self,s):
  if self.active:self.parts.append(s)
def main():
 rows=[]
 for path in sorted((D/'private/osaka').glob('*.html.gz')):
  raw=gzip.decompress(path.read_bytes());r=json.loads(path.with_name(path.name.replace('.html.gz','.receipt.json')).read_text());assert hashlib.sha256(raw).hexdigest()==r['sha256'];p=Body();p.feed(raw.decode('utf-8'));text='\n'.join(x.strip()for x in ''.join(p.parts).splitlines()if x.strip());assert text
  rows.append(dict(id=r['id'],url=r['url'],source_sha256=r['sha256'],text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),EOS_approved=False,admission='quarantined original HTML body; includes procedures/lists; semantic and rights review pending'))
 with gzip.open(D/'private/osaka-candidates.jsonl.gz','wt')as out:
  for r in rows:out.write(json.dumps(r,ensure_ascii=False)+'\n')
 print('Candidate pages',len(rows),'characters',sum(len(r['text'])for r in rows))
if __name__=='__main__':main()
