"""Separate next-corpus pilot. NEVER modify current frozen corpus/schedule or run optimizer."""
import urllib.request,urllib.parse,urllib.robotparser,datetime,time,re
from html.parser import HTMLParser
from common import *
F=D/'future-sources/maff';F.mkdir(parents=True,exist_ok=True)
BASE='https://www.maff.go.jp/j/heya/kodomo_sodan/'
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,t,a):
  if t=='a'and'href'in dict(a):self.urls.append(dict(a)['href'])
class Article(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.start=None;self.tag=None;self.buf=[];self.title='';self.paragraphs=[];self.done=False
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='div':
   self.depth+=1
   if a.get('class')=='content_left':self.start=self.depth
  if self.start is None or self.done:return
  if t in ['h1','h2','h3','p','li']:self.tag=t;self.buf=[]
 def handle_endtag(self,t):
  if t=='div':
   if self.start==self.depth:self.start=None
   self.depth-=1
  if t==self.tag:
   s=''.join(self.buf).strip();self.tag=None
   if re.match('参考資料|お問い合わせ|お問合せ|出典|関連情報',s):self.done=True;return
   if t=='h1':self.title=s
   elif t in ['p','li']and s:self.paragraphs.append(s)
 def handle_data(self,s):
  if self.start is not None and self.tag and not self.done:self.buf.append(s)
records=[];robot=urllib.robotparser.RobotFileParser();robot.parse((D/'future-sources/maff-robots.html').read_text().splitlines())
def get(url):
 assert url.startswith(BASE)and robot.can_fetch('4k29-Japanese-research',url);ident=hashlib.sha256(url.encode()).hexdigest()[:20];p=F/(ident+'.html.gz')
 if p.exists():b=gzip.open(p,'rb').read()
 else:
  try:b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'4k29-Japanese-research/1.0 bounded corpus pilot'}),timeout=35).read()
  except Exception as e:records.append(dict(url=url,error=str(e)));return None
  with gzip.open(p,'wb')as z:z.write(b)
  time.sleep(1)
 records.append(dict(url=url,raw_sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),snapshot=p.name,acquired_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),revision='HTTP snapshot no stable revision available',license='PDL-1.0, MAFF third-party exceptions apply',terms='https://www.maff.go.jp/j/use/link.html',attribution='農林水産省ウェブサイトの原文からHTML表示用要素・連絡先・参考資料一覧を分離して作成; 政府が作成した学習コーパスではない'))
 return b
pool={}
for category in ['syokuhin','yasai1','mame','kome_tukurikata']:
 url=BASE+category+'.html';b=get(url)
 if b is None:continue
 links=Links();links.feed(b.decode('utf8'))
 for link in links.urls:
  u=urllib.parse.urljoin(url,link).split('#')[0]
  if re.match(re.escape(BASE)+r'\d{4}/[^/]+\.html$',u):pool[u]=category
# Fixed source-topic-balanced pilot before inspecting content; at most60 answer-page requests.
chosen=[]
for cat in ['syokuhin','yasai1','mame','kome_tukurikata']:
 chosen += sorted([u for u in pool if pool[u]==cat],key=rank)[:15]
enc=Encoder(read(V/'data/tokenizer.json'));pieces=[bytes.fromhex(s)for s in enc.tok['bytes']];rows=[]
for url in chosen:
 b=get(url)
 if b is None:continue
 a=Article();a.feed(b.decode('utf8'));text=a.title+'\n'+'\n'.join(a.paragraphs);hold=None
 if not a.title or not a.paragraphs or not text.endswith(('。','？','！')):hold='incomplete answer extraction'
 elif re.search(r'図[0-9１２３]|下の図|下の表|写真|著作|転載|引用|図を|をご覧|こちら|次のとおり|病気|食中毒|アレルギ|医療|治療',text):hold='figure/external/third-party or health advice requires further review'
 ids=enc(text);assert b''.join(pieces[t]for t in ids)==text.encode()
 rows.append(dict(id='maff:'+hashlib.sha256(url.encode()).hexdigest()[:20],source='maff',component='maff|'+pool[url],genre=pool[url],title=a.title,text=text,body_tokens=ids,provenance=records[-1],hold_reason=hold,status='private candidate only; not current frozen TRAIN',true_boundary='full extracted original answer section before references, not arbitrary window',BOS=True,EOS=True))
# Unreviewed bodies remain local. Only explicit future admission can publish a subset.
gzwrite(F/'candidates.private.jsonl.gz',rows);write(F/'acquisition.json',records);write(F/'CANDIDATE_STATS.json',dict(candidate_pages=len(rows),body_tokens=sum(len(r['body_tokens'])for r in rows),proxy_eligible_pages=sum(r['hold_reason']is None for r in rows),proxy_eligible_body_tokens=sum(len(r['body_tokens'])for r in rows if r['hold_reason']is None),genre_counts={g:sum(r['genre']==g for r in rows)for g in sorted({r['genre']for r in rows})},current_TRAIN_addition=0,new_model_updates=0))
sample=[]
for genre in sorted({r['genre']for r in rows}):
 sample += sorted([r for r in rows if r['genre']==genre and not r['hold_reason']],key=lambda r:rank('review|'+r['id']))[:2]
write(F/'sample.private.json',sample);print(read(F/'CANDIDATE_STATS.json'),flush=True)
