"""Publisher-provided RSS credits, bounded10-item pages, no restricted user lookup."""
import pathlib,json,gzip,hashlib,urllib.request,urllib.error,time,datetime,re,html,xml.etree.ElementTree as ET,shutil,os
D=pathlib.Path(__file__).resolve().parent
def atomic_json(path,value):
 tmp=path.with_suffix('.pending')
 with tmp.open('w')as out:out.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n');out.flush();os.fsync(out.fileno())
 os.replace(tmp,path)
def fetch(url):
 for attempt in range(1,4):
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  try:
   with urllib.request.urlopen(url,timeout=45)as response:return response.read(8*1024**2+1),dict(response.headers)
  except (urllib.error.URLError,TimeoutError)as error:
   code=getattr(error,'code',None);retry=attempt<3 and(code is None or 500<=code<600)
   path=D/'FEED_HTTP_FAILURES.json';events=json.loads(path.read_text())if path.exists()else[];events.append(dict(url=url,attempt=attempt,start_utc=start,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status=code,error=str(error),will_retry=retry));atomic_json(path,events)
   if not retry:raise
   time.sleep(20*attempt)
P=D/'private/feed-credits';P.mkdir(exist_ok=True)
protocol=dict(first_page=23,last_page=291,server_items_per_page=10,delay_seconds=10,max_raw_bytes=100*1024**2,max_response_bytes=8*1024**2,scope='Original author and translator credits supplied in public RSS footer; never a TRAIN admission. Public feed limits preserved. Stop once all API target IDs covered; count unmatched and duplicate IDs explicitly.')
p=D/'FEED_CREDITS_PROTOCOL.json'
if p.exists():assert json.loads(p.read_text())==protocol
else:p.write_text(json.dumps(protocol,indent=2)+'\n')
target={r['id']for r in json.loads((D/'CENSUS_INDEX.json').read_text())};by={};receipts=[];total=0;duplicates=0;parse_failures=[];ns={'dc':'http://purl.org/dc/elements/1.1/','c':'http://purl.org/rss/1.0/modules/content/'}
for page in range(protocol['first_page'],protocol['last_page']+1):
 assert shutil.disk_usage(D).free>1024**3
 path=P/f'{page:03d}.xml.gz';rp=P/f'{page:03d}.receipt.json';url=f'https://jp.globalvoices.org/feed/?paged={page}'
 if path.exists():b=gzip.decompress(path.read_bytes());r=json.loads(rp.read_text());assert hashlib.sha256(b).hexdigest()==r['sha256']
 else:
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  b,headers=fetch(url)
  assert len(b)<=protocol['max_response_bytes']and total+len(b)<=protocol['max_raw_bytes'];path.write_bytes(gzip.compress(b,mtime=0));r=dict(page=page,url=url,request_start_utc=start,response_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(b).hexdigest(),raw_bytes=len(b),headers=headers);rp.write_text(json.dumps(r,indent=2)+'\n');time.sleep(protocol['delay_seconds'])
 r=dict(r);r['headers']={k:v for k,v in r.get('headers',{}).items()if k.lower()not in {'set-cookie','cookie','authorization','proxy-authorization'}}
 total+=len(b);receipts.append(r)
 try:items=ET.fromstring(b).findall('./channel/item')
 except ET.ParseError as error:
  parse_failures.append(dict(page=page,sha256=r['sha256'],error=str(error),action='Raw response preserved unchanged; page skipped, missing article credits remain unresolved'))
  atomic_json(D/'FEED_PARSE_FAILURES.json',parse_failures)
  continue
 assert len(items)<=10,'Unexpected feed page size'
 for item in items:
  link=item.findtext('link')or'';match=re.search(r'/(\d+)/?$',link)
  if not match:continue
  ident=int(match[1])
  if ident not in target:continue
  if ident in by:duplicates+=1;continue
  content=item.findtext('c:encoded',default='',namespaces=ns);footer=content[content.rfind("<div",0,content.find("gv-rss-footer")):]if'gv-rss-footer'in content else'';plain=html.unescape(re.sub('<[^>]+>',' ',footer));plain=re.sub(r'\s+',' ',plain).strip();links=re.findall(r'<a[^>]+href=[\"\x27]([^\"\x27]+)[\"\x27][^>]*>(.*?)</a>',footer,re.S)
  by[ident]=dict(id=ident,url=link,feed_creator=item.findtext('dc:creator',default='',namespaces=ns),public_credit_footer=plain,credit_links=[dict(url=u,label=html.unescape(re.sub('<[^>]+>','',t)).strip())for u,t in links],published=item.findtext('pubDate'),source_response_sha256=r['sha256'],source_feed_page=page,author_role_inference='Preserve supplied labels; creator alone not assumed original author',attribution_complete=bool(plain))
 status=dict(pages=len(receipts),covered_API_articles=len(by),target_API_articles=len(target),duplicate_feed_entries=duplicates,parse_failures=parse_failures,missing_ids=sorted(target-set(by)),complete=False,admitted_tokens=0,optimizer_updates=0,raw_bytes=total,receipts=receipts)
 atomic_json(D/'FEED_CREDITS_STATUS.json',status);atomic_json(D/'FEED_ATTRIBUTIONS.json',list(by.values()));print('credits',page,len(by),'/',len(target),flush=True)
 if set(by)==target or not items:break
status['complete']=True;status['all_target_ids_covered']=set(by)==target;atomic_json(D/'FEED_CREDITS_STATUS.json',status)
