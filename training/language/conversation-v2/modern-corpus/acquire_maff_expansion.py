"""Expand a previously reviewed public MAFF QA source with bounded polite requests.
Original source reuse is recorded separately from new HTTP acquisition; never admission.
"""
import pathlib,json,gzip,hashlib,urllib.request,urllib.parse,urllib.robotparser,urllib.error,datetime,time,re,os,shutil
from html.parser import HTMLParser
D=pathlib.Path(__file__).resolve().parent;P=D/'private/maff-expanded';P.mkdir(exist_ok=True);BASE='https://www.maff.go.jp/j/heya/kodomo_sodan/'
CATEGORIES=['kome_sonota','kome_tukurikata','kudamono','mame','niku','nougyou','ringyou','sonota','suisan','syokuhin','yasai1','yasai2']
protocol=dict(categories=CATEGORIES,max_answers=240,max_per_category=20,delay_seconds=5,max_response_bytes=2*1024**2,max_total_new_bytes=40*1024**2,min_free_bytes=1024**3,selection='SHA256 maff-expansion-v1 URL ordering, up to20 per source category before reading answer content',license='MAFF PDL1.0 with third-party exceptions; candidate only',admitted_tokens=0,http_error_policy='Do not retry denied URL or change user-agent/access route. Skip individually denied source URL; halt whole expansion after3 HTTP403 responses. Continue only other officially linked public categories within original240-page bound.',max_forbidden_responses=3)
f=D/'MAFF_EXPANSION_PROTOCOL.json'
if f.exists():assert json.loads(f.read_text())==protocol
else:f.write_text(json.dumps(protocol,indent=2)+'\n')
old_dir=D.parent/'diverse-foundation/future-sources/maff';old={r['url']:r for r in json.loads((old_dir/'acquisition.json').read_text())if'snapshot'in r};receipts=[];total=0

def get(url):
 global total
 assert shutil.disk_usage(D).free>protocol['min_free_bytes'];ident=hashlib.sha256(url.encode()).hexdigest()[:20];path=P/(ident+'.html.gz');rp=P/(ident+'.receipt.json')
 if path.exists():b=gzip.decompress(path.read_bytes());r=json.loads(rp.read_text());assert hashlib.sha256(b).hexdigest()==r['sha256']
 elif url in old:
  prior=old[url];b=gzip.decompress((old_dir/prior['snapshot']).read_bytes());assert hashlib.sha256(b).hexdigest()==prior['raw_sha256'];r=dict(url=url,sha256=prior['raw_sha256'],raw_bytes=len(b),acquisition='reused prior verified snapshot, not new HTTP',prior_provenance=prior);path.write_bytes(gzip.compress(b,mtime=0));rp.write_text(json.dumps(r,indent=2)+'\n')
 else:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'4k29-Japanese-research/1.0 bounded-source-audit'}),timeout=45)as response:b=response.read(protocol['max_response_bytes']+1);headers={k:v for k,v in response.headers.items()if k.lower()not in {'set-cookie','cookie','authorization','proxy-authorization'}}
  assert len(b)<=protocol['max_response_bytes'];total+=len(b);assert total<=protocol['max_total_new_bytes'];r=dict(url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),raw_bytes=len(b),headers=headers,acquisition='new HTTP');tmp=path.with_suffix('.pending');tmp.write_bytes(gzip.compress(b,mtime=0));os.replace(tmp,path);rp.write_text(json.dumps(r,indent=2)+'\n');time.sleep(5)
 receipts.append(r);return b
robot=urllib.robotparser.RobotFileParser();robot.parse(get('https://www.maff.go.jp/robots.txt').decode().splitlines());get('https://www.maff.go.jp/j/use/link.html')
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  if t=='a':self.links.append(dict(a).get('href')or'')
prior_failure=json.loads((D/'MAFF_EXPANSION_FAILURE.json').read_text());denied={prior_failure['failed_url']};errors=[dict(url=prior_failure['failed_url'],status=403,attempt='prior run; not retried')]
def allowed_get(url):
 if url in denied:return None
 try:return get(url)
 except urllib.error.HTTPError as error:
  errors.append(dict(url=url,status=error.code,action='Not retried or bypassed'));(D/'MAFF_HTTP_ERRORS.json').write_text(json.dumps(errors,indent=2)+'\n')
  if error.code==403:
   denied.add(url)
   if len(denied)>=protocol['max_forbidden_responses']:raise RuntimeError('Source403 limit reached; stop')from error
  time.sleep(protocol['delay_seconds']);return None
pool={}
for cat in CATEGORIES:
 u=BASE+cat+'.html';assert robot.can_fetch('4k29-Japanese-research',u);b=allowed_get(u)
 if b is None:continue
 a=Links();a.feed(b.decode('utf-8'))
 for link in a.links:
  url=urllib.parse.urljoin(u,link).split('#')[0]
  if re.fullmatch(re.escape(BASE)+r'\d{4}/[^/]+\.html',url):pool.setdefault(url,cat)
chosen=[]
for cat in CATEGORIES:chosen+=sorted([u for u,c in pool.items()if c==cat],key=lambda u:hashlib.sha256(('maff-expansion-v1'+u).encode()).hexdigest())[:20]
(D/'MAFF_EXPANSION_SELECTION.json').write_text(json.dumps(dict(discovered=len(pool),selected=[dict(url=u,category=pool[u])for u in chosen]),indent=2)+'\n')
for i,u in enumerate(chosen):
 assert robot.can_fetch('4k29-Japanese-research',u)
 if allowed_get(u)is None:continue
 status=dict(answer_pages_completed=i+1,selected_answer_pages=len(chosen),receipts=receipts,new_HTTP_responses=sum(r['acquisition']=='new HTTP'for r in receipts),reused_prior_responses=sum(r['acquisition']!='new HTTP'for r in receipts),complete=False,admitted_tokens=0,optimizer_updates=0)
 temp=D/'MAFF_EXPANSION_STATUS.pending';temp.write_text(json.dumps(status,indent=2)+'\n');os.replace(temp,D/'MAFF_EXPANSION_STATUS.json');print('MAFF',i+1,'/',len(chosen),flush=True)
status['complete']=True;(D/'MAFF_EXPANSION_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
