"""Bounded, cached official JMA explanatory FAQ acquisition, not a live SNS collector."""
import urllib.request,datetime,time,re,html
from html.parser import HTMLParser
from common import *
S=D/'sources';S.mkdir(exist_ok=True)
class FAQ(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.active=False;self.tag=None;self.buf=[];self.sections=[];self.cur=None;self.ignore=0
 def handle_starttag(self,t,a):
  if t=='h1':self.active=True
  if not self.active:return
  if t in ['h2','p']:
   self.tag=t;self.buf=[]
  if t in ['script','style']:self.ignore+=1
 def handle_endtag(self,t):
  if t=='main':self.active=False;self.tag=None
  if t in ['script','style']:self.ignore=max(0,self.ignore-1)
  if t==self.tag:
   s=''.join(self.buf).strip()
   if t=='h2':
    if self.cur:self.sections.append(self.cur)
    self.cur=dict(question=s,paragraphs=[])
   elif self.cur and s:self.cur['paragraphs'].append(s)
   self.tag=None
 def handle_data(self,s):
  if self.tag and not self.ignore:self.buf.append(s)
 def finish(self):
  if self.cur:self.sections.append(self.cur)
  return self.sections
prior={r['url']:r for r in read(D/'ACQUISITION.json')}if(D/'ACQUISITION.json').exists()else{}
receipts=[];rows=[]
for n in [1,2,3,4,5,6,8,9,13,14,19,20,21,22,33]:
 url=f'https://www.jma.go.jp/jma/kishou/know/faq/faq{n}.html';p=S/f'jma-faq{n}.html'
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'4k29-Japanese-research/1.0 (bounded public explanation audit)'}),timeout=45)as response:
   b=response.read();headers=dict(response.headers)
  p.write_bytes(b);time.sleep(1)
 else:b=p.read_bytes();headers={}
 receipt=dict(url=url,acquired_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=sha(p),bytes=len(b),version='HTTP snapshot; revision ID unavailable',response_headers=headers,license='PDL-1.0 subject to JMA terms and third-party exclusions',terms_url='https://www.jma.go.jp/jma/kishou/info/coment.html',method='one bounded GET per page; cached reruns; no authentication or access circumvention')
 if url in prior:
  assert prior[url]['sha256']==sha(p),'Frozen source changed; use separate acquisition/version, never silently replace'
  receipt=prior[url]
 receipts.append(receipt);parser=FAQ();parser.feed(b.decode('utf-8'));sections=parser.finish()
 for i,r in enumerate(sections):
  text=r['question']+'\n'+'\n'.join(r['paragraphs']);reason=None
  if not r['paragraphs']or not r['paragraphs'][-1].endswith(('。','！','？')):reason='incomplete section'
  elif len(text)<80:reason='too short for prose review'
  elif re.search(r'下図|上図|図[0-9１２３]|下記|以下の|次の|こちら|参照|著作|引用|提供|出典|参考|写真|転載|TEL|@|https?://',text):reason='external/figure/third-party dependency proxy'
  rows.append(dict(id=f'jma:faq{n}:{i}',source='jma',component=f'jma:faq{n}',family=f'jma:faq{n}',title=r['question'],text=text,provenance=receipt,paragraphs=r['paragraphs'],split='dev'if n in [2,5,13]else'train',hold_reason=reason,BOS=True,EOS=True,boundary_contract='complete original FAQ question plus all following answer paragraphs, standalone section task; not claimed page end'))
write(D/'ACQUISITION.json',receipts);gzwrite(D/'jma-candidates.jsonl.gz',rows)
write(D/'JMA_CANDIDATE_COUNTS.json',dict(pages=len(receipts),sections=len(rows),eligible=sum(not r['hold_reason']for r in rows),network_corpus='official explanatory text only',robots='official robots.txt returned404; no disallow file found; no bypass'))
print(read(D/'JMA_CANDIDATE_COUNTS.json'))
