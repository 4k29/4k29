"""MAFF-authored explanatory prose only; immutable HTML snapshots and attribution.
No images, external links, AI outputs or tokenizer training. Refuse overwrite.
"""
import concurrent.futures,datetime,hashlib,json,pathlib,re,sys,urllib.request
from urllib.parse import urljoin
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]/'dialogue'))
from collect_web_language import Page,LICENSE
class Prose(Page):
 def handle_data(self,text):
  if any(t in ['rt','rp','script','style'] for t,a in self.stack):return
  super().handle_data(text)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def fetch(u):
 assert u.startswith('https://www.maff.go.jp/')
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'4k29-own-transformer-language-research/1.0'}),timeout=25) as r:
  assert r.url.startswith('https://www.maff.go.jp/')
  b=r.read(4*1024*1024);meta={'finalUrl':r.url,'lastModified':r.headers.get('Last-Modified'),'contentType':r.headers.get('Content-Type')}
 p=Prose();p.feed(b.decode('utf-8'));return b,p,meta
if __name__=='__main__':
 out=ROOT/'sources';out.mkdir(exist_ok=False);(out/'html').mkdir()
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();terms='https://www.maff.go.jp/j/use/link.html';b,p,m=fetch(terms)
 assert '公共データ利用規約' in b.decode() and LICENSE in b.decode()
 (out/'terms.html').write_bytes(b)
 urls=[]
 for crop,prefix in [('ine','i'),('nasu','n'),('satuma','s'),('zyaga','z')]:
  urls += [f'https://www.maff.go.jp/j/kids/agri/{crop}/{prefix}0{i}.html' for i in range(1,5)]
 urls += [f'https://www.maff.go.jp/j/kids/rice_history/stage{i}.html' for i in range(1,7)]
 old=[json.loads(l) for l in (ROOT.parent/'round10/documents.jsonl').read_text().splitlines()]
 units=json.loads((ROOT.parent/'round10/units.json').read_text())
 heldout=[u['text'] for u in units if u['partition']!='train']
 # Exact 64-character spans, rather than generation scores, detect cross-fold text leakage.
 grams={t[i:i+64] for t in heldout for i in range(max(0,len(t)-63))}
 oldurls={d.get('url') for d in old};oldtext={d['textSha256'] for d in old}
 docs=[];records=[];failures=[]
 def work(u):
  try:return u,fetch(u),None
  except Exception as e:return u,None,type(e).__name__+': '+str(e)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for u,result,error in pool.map(work,urls):
   if error:failures.append({'url':u,'error':error});print(error,u,flush=True);continue
   b,p,m=result;key=sha(u.encode())[:16];(out/'html'/f'{key}.html').write_bytes(b)
   blocks=[];seen=set()
   for x in p.blocks:
    t=x['text']
    if x['tag']!='p' or len(t)<40 or not re.search('[。！？]',t):continue
    if re.search('お問い合わせ|お問合せ|代表：|電話|Copyright|出典|資料：|参考文献',t,re.I):continue
    if t not in seen:blocks.append(t);seen.add(t)
   text='\n'.join(blocks);reason=None
   if len(text)<160:reason='insufficient explanatory prose'
   elif u in oldurls or sha(text.encode()) in oldtext:reason='existing document'
   elif any(text[i:i+64] in grams for i in range(max(0,len(text)-63))):reason='64-character overlap with existing heldout text'
   partition='reserved' if int(sha(u.encode()),16)%10==0 else 'train'
   rec=dict(url=u,id='maff-kids:'+key,title=''.join(p.title),htmlSha256=sha(b),textSha256=sha(text.encode()),characters=len(text),partition=partition,exclusion=reason,attribution=f'出典：農林水産省ウェブサイト（{u}）を加工して作成',author='農林水産省',license='公共データ利用規約（第1.0版）',licenseUrl=LICENSE,policyUrl=terms,retrievedAt=now,processing='Main-content paragraphs only; HTML ruby readings/navigation/images omitted; whitespace normalized; no authored or generated rewriting.',**m)
   records.append(rec)
   if reason is None:docs.append(dict(id=rec['id'],site='maff',url=u,title=rec['title'],partition=partition,text=text,blocks=blocks,textSha256=rec['textSha256']))
   print(json.dumps(dict(url=u,chars=len(text),partition=partition,excluded=reason)),flush=True)
 (out/'documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in docs))
 write(out/'manifest.json',dict(retrievedAt=now,licenseHtmlSha256=sha((out/'terms.html').read_bytes()),licenseUrl=LICENSE,sourcePolicyUrl=terms,sources=records,failures=failures,overlapAudit=dict(spanCharacters=64,existingHeldoutUnits=len(heldout),heldoutUsedForTraining=False),counts={p:sum(d['partition']==p for d in docs) for p in ['train','reserved']},characters={p:sum(len(d['text']) for d in docs if d['partition']==p) for p in ['train','reserved']}))
 assert sum(d['partition']=='train' for d in docs)>=10,'Do not freeze a trivially small intervention'
