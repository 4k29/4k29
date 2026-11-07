"""Prospective human-government source expansion; exact snapshots, no teachers."""
import pathlib,json,hashlib,re,sys,datetime,urllib.request,urllib.parse,concurrent.futures,importlib.util
R=pathlib.Path(__file__).resolve().parent;B=R.parent
sys.path.insert(0,str(B.parent/'dialogue'))
from collect_web_language import Page,LICENSE,POLICIES
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
class Prose(Page):
 def handle_starttag(self,tag,attrs):
  if tag=='a' and dict(attrs).get('href'):self.links.append(dict(attrs)['href'])
  super().handle_starttag(tag,attrs)
 def handle_data(self,t):
  if any(tag in ['rt','rp','script','style'] for tag,a in self.stack):return
  super().handle_data(t)
def fetch(url):
 assert urllib.parse.urlparse(url).hostname in ['www.jma.go.jp','www.maff.go.jp']
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'4k29-own-transformer-language-research/1.0'}),timeout=25) as h:
  assert urllib.parse.urlparse(h.url).hostname==urllib.parse.urlparse(url).hostname
  raw=h.read(4*1024*1024);meta=dict(finalUrl=h.url,lastModified=h.headers.get('Last-Modified'),contentType=h.headers.get('Content-Type'))
 try:text=raw.decode('utf-8')
 except UnicodeDecodeError:text=raw.decode('cp932')
 p=Prose();p.feed(text);return raw,text,p,meta
if __name__=='__main__':
 p=read(R/'collection-policy.json');out=R/'sources';out.mkdir(exist_ok=False);(out/'html').mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 terms=[]
 for site,url in POLICIES.items():
  raw,html,page,meta=fetch(url);assert '公共データ利用規約' in html and LICENSE in html
  (out/f'{site}-terms.html').write_bytes(raw);terms.append(dict(site=site,url=url,htmlSha256=sha(raw),licenseUrl=LICENSE,retrievedAt=now,**meta))
 old=[json.loads(l) for l in (B/'round10/documents.jsonl').read_text().splitlines()];parts={x['document']:x['partition'] for x in read(B/'round10/split.json')['assignments']}
 knownUrls={d['url'] for d in old};held=[d['text'] for d in old if parts[d['id']]!='train'];train=[d['text'] for d in old if parts[d['id']]=='train']
 extra=[json.loads(l) for l in (B/'round18/sources/documents.jsonl').read_text().splitlines()];knownUrls.update(d['url'] for d in extra);held.extend(d['text'] for d in extra if d['partition']=='reserved')
 urls=[('jma',u) for u in p['jmaUrls']];failures=[];indexRecords=[]
 raw,html,page,meta=fetch(p['jmaKnowledgeIndex']);(out/'html'/'jma-knowledge-index.html').write_bytes(raw);indexRecords.append(dict(url=p['jmaKnowledgeIndex'],htmlSha256=sha(raw),**meta))
 links=sorted({urllib.parse.urljoin(p['jmaKnowledgeIndex'],l).split('#')[0] for l in page.links if urllib.parse.urljoin(p['jmaKnowledgeIndex'],l).startswith('https://www.jma.go.jp/jma/kishou/know/') and urllib.parse.urljoin(p['jmaKnowledgeIndex'],l).split('#')[0].endswith('.html')})
 urls.extend(('jma',u) for u in links if u not in knownUrls)
 urls=urls[:len(p['jmaUrls'])+p['maxSortedNewJmaKnowledgeLinks']]
 for cat in p['maffCategories']:
  url=f'https://www.maff.go.jp/j/heya/kodomo_sodan/{cat}.html'
  try:
   raw,html,page,meta=fetch(url);(out/'html'/f'{sha(url.encode())[:16]}.html').write_bytes(raw);indexRecords.append(dict(url=url,htmlSha256=sha(raw),**meta))
   links=sorted({urllib.parse.urljoin(url,l).split('#')[0] for l in page.links if re.search(r'/kodomo_sodan/\d{4}/[^/]+\.html(?:#.*)?$',urllib.parse.urljoin(url,l))})
   urls.extend(('maff',u) for u in sorted([u for u in links if u not in knownUrls],reverse=True)[:p['maxSortedLinksPerMaffCategory']])
  except Exception as ex:failures.append(dict(url=url,error=str(ex)))
 urls=sorted(set((s,u) for s,u in urls if u not in knownUrls))
 spec=importlib.util.spec_from_file_location('legacy',B/'round3/prepare.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
 sources=[];units=[];records=[]
 def work(item):
  site,url=item
  try:return site,url,fetch(url),None
  except Exception as ex:return site,url,None,str(ex)
 with concurrent.futures.ThreadPoolExecutor(max_workers=p['workers']) as pool:
  for site,url,result,error in pool.map(work,urls):
   if error:failures.append(dict(url=url,error=error));continue
   raw,html,page,meta=result;key=sha(url.encode())[:16];(out/'html'/f'{key}.html').write_bytes(raw)
   blocks=[]
   for b in page.blocks:
    t=b['text']
    if b['tag']!='p' or not re.search('[。！？]',t) or re.search('お問い合わせ|お問合せ|電話|Copyright|出典|資料：|参考文献|転載|写真提供',t,re.I):continue
    if t not in blocks:blocks.append(t)
   text='\n'.join(blocks);part='reserved' if int(sha(url.encode()),16)%10==0 else 'train';did=f'{site}-expanded:'+key
   author='気象庁' if site=='jma' else '農林水産省'
   doc=dict(id=did,site=site,url=url,partition=part,text=text,blocks=blocks,title=''.join(page.title),author=author,license='公共データ利用規約（第1.0版）',licenseUrl=LICENSE,policyUrl=POLICIES[site],attribution=f'出典：{author}ウェブサイト（{url}）を加工して作成',retrievedAt=now,htmlSha256=sha(raw),textSha256=sha(text.encode()),processing='Main paragraphs only; omit ruby, images, navigation, contact and credit paragraphs; normalize HTML whitespace; legacy source chains; no rewriting.',**meta)
   sources.append(doc)
   for a,b,t in legacy.chains(doc):
    if not p['minimumUnitCharacters']<=len(t)<=p['maximumUnitCharacters'] or len(re.findall('[ぁ-ゖァ-ヺ一-龯]',t))/len(t)<p['minimumJapaneseFraction'] or len(re.findall('[。！？]',t))<p['minimumSentenceTerminators']:continue
    assert t=='\n'.join(blocks[a:b])
    units.append(dict(doc,originalDocument=did,originalTextSha256=doc['textSha256'],startLine=a,endLine=b,unitKey=did+':chain:'+str(a),id=did+':unit:'+str(a),text=t,blocks=t.splitlines(),textSha256=sha(t.encode())))
   print(json.dumps(dict(url=url,characters=len(text),partition=part)),flush=True)
 # Mechanical access to held text is duplicate-only; never loss, generation or selection.
 held.extend(d['text'] for d in sources if d['partition']=='reserved')
 candidates=[d for d in units if d['partition']=='train'];wanted={d['text'][i:i+64] for d in candidates for i in range(len(d['text'])-63)}
 forbidden=set()
 for t in held+train:
  for i in range(max(0,len(t)-63)):
   g=t[i:i+64]
   if g in wanted:forbidden.add(g)
 admitted=[];excluded=[];seen=set()
 for d in candidates:
  spans={d['text'][i:i+64] for i in range(len(d['text'])-63)}
  if spans & (forbidden|seen):excluded.append(dict(unitKey=d['unitKey'],reason='64-character overlap with existing source, reserved source or already admitted unit'));continue
  admitted.append(d);seen.update(spans)
 (out/'documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in admitted))
 (out/'source-documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in sources))
 write(out/'license-records.json',dict(policies=terms,licenseUrl=LICENSE))
 manifest=dict(retrievedAt=now,collectionPolicySha256=sha((R/'collection-policy.json').read_bytes()),sourcesRequested=len(urls),fetchedDocuments=len(sources),indexRecords=indexRecords,failures=failures,sourceDocumentsSha256=sha((out/'source-documents.jsonl').read_bytes()),candidateTrainUnits=len(candidates),admittedUnits=len(admitted),admittedCharacters=sum(len(d['text']) for d in admitted),bySite={s:dict(units=sum(d['site']==s for d in admitted),characters=sum(len(d['text']) for d in admitted if d['site']==s)) for s in ['jma','maff']},reservedDocuments=sum(d['partition']=='reserved' for d in sources),excluded=excluded,existingNonTrainRawDocumentsAudited=sum(parts[d['id']]!='train' for d in old),testReadForDuplicateAudit=True,testScoredOrGenerated=False,reservedEncoded=False,foldsChanged=False)
 write(out/'manifest.json',manifest);print(json.dumps({k:v for k,v in manifest.items() if k not in ['excluded','failures','indexRecords']}))
 assert len(admitted)>=p['minimumTrainUnits'] and manifest['admittedCharacters']>=p['minimumTrainCharacters'] and sum(v['units']>0 for v in manifest['bySite'].values())>=p['minimumTrainSites'],'Prospective minimum intervention not reached'
