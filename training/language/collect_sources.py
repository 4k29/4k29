"""Attributed RAW Japanese only: open government, MDN, public-domain works.

No questions authored as labels, generated teacher prose, Wikipedia, pretrained
weights or tokenizer. Original and extracted SHA, terms and credits retained.
"""
import argparse,collections,concurrent.futures,csv,datetime,hashlib,html,io,json,pathlib,re,sys,time,urllib.parse,urllib.request,zipfile
from html.parser import HTMLParser
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'dialogue'))
from collect_web_language import Page,VOID,USER_AGENT,POLICIES,LICENSE
from collect_mdn_language import Prose
AOZORA_POLICY='https://www.aozora.gr.jp/guide/kijyunn.html'
AOZORA_INDEX='https://www.aozora.gr.jp/index_pages/list_person_all_extended_utf8.zip'
MDN_POLICY='https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Attrib_copyright_license'
AUTHORS={'芥川竜之介','太宰治','宮沢賢治','夏目漱石','国木田独歩','梶井基次郎','新美南吉','中島敦','夢野久作','寺田寅彦','岡本かの子','林芙美子','有島武郎','堀辰雄'}
HOSTS={'www.aozora.gr.jp','www.jma.go.jp','www.maff.go.jp','www.digital.go.jp','developer.mozilla.org'}
def digest(b):return hashlib.sha256(b).hexdigest()
def fetch(url):
    if urllib.parse.urlparse(url).hostname not in HOSTS:raise ValueError('Unapproved public source host')
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
    with urllib.request.urlopen(req,timeout=30) as response:
        if urllib.parse.urlparse(response.url).hostname not in HOSTS:raise ValueError('Redirect left source whitelist')
        raw=response.read(4*1024*1024+1)
        if len(raw)>4*1024*1024:raise ValueError('Individual source too large')
        metadata=dict(finalUrl=response.url,lastModified=response.headers.get('Last-Modified'),contentType=response.headers.get('Content-Type'))
    return raw,metadata
def decode(raw):
    for encoding in ['utf-8','cp932','euc-jp']:
        try:return raw.decode(encoding),encoding
        except UnicodeDecodeError:continue
    raise ValueError('Source encoding could not be decoded exactly')
class Literature(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.stack=[];self.parts=[];self.seen_main=False
    def inside(self):return any('main_text' in a.get('class','').split() for _,a in self.stack)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag not in VOID:self.stack.append((tag,a))
        if 'main_text' in a.get('class','').split():self.seen_main=True
        if self.inside() and tag=='br':self.parts.append('\n')
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:del self.stack[i:];break
    def handle_data(self,text):
        if self.inside() and not any(t in ['rt','rp','script','style'] or 'notes' in a.get('class','').split() for t,a in self.stack):self.parts.append(text)
    def text(self):
        text=''.join(self.parts).replace('\r','')
        return '\n'.join(line.rstrip() for line in text.splitlines() if line.strip()).strip()
def snapshot(url,kind):
    raw,metadata=fetch(url);text,encoding=decode(raw)
    plain=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',text)))
    if kind=='aozora' and not all(s in plain for s in ['著作権の切れている作品','自由に複製','了解を求めたりする必要はありません']):raise ValueError('Changed public-domain terms require review')
    if kind=='mdn' and not ('creativecommons.org/licenses/by-sa/2.5/' in text and 'any later version' in text):raise ValueError('Changed MDN terms require review')
    if kind=='government' and not ('公共データ利用規約' in text and LICENSE in text):raise ValueError('Changed government terms require review')
    return dict(url=url,kind=kind,retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),htmlSha256=digest(raw),encoding=encoding,text=plain,**metadata)
def mdn_paths():
    result=['JavaScript/Reference/Global_Objects/'+s for s in ['Array/at','Array/filter','Array/map','Array/reduce','Array/find','Array/forEach','Array/slice','Array/splice','Array/sort','Array/includes','String/includes','String/slice','String/substring','String/split','String/replace','String/match','String/normalize','Number','Number/isNaN','Number/isInteger','Math','Math/random','Math/max','Math/min','Math/floor','Math/round','Date','Date/now','JSON/parse','JSON/stringify','Object/keys','Object/values','Object/entries','Promise/all','Promise/then','Promise/catch','Error','RegExp','WeakMap','Symbol','BigInt','Intl','Intl/NumberFormat','Intl/DateTimeFormat','Function','TypedArray','ArrayBuffer','Uint8Array','DataView','encodeURI','parseFloat','parseInt']]
    result+=['HTML/Reference/Elements/'+s for s in ['a','article','section','header','footer','nav','main','p','span','div','button','form','label','select','option','video','audio','canvas','picture','img','details','dialog','table','ol','ul','li','strong','em','time','progress','meter']]
    result+=['CSS/'+s for s in ['grid','position','margin','padding','border','box-sizing','width','height','background-color','font-size','font-weight','line-height','text-align','text-decoration','white-space','overflow','word-break','opacity','transform','transition','animation','align-items','justify-content','gap','object-fit','aspect-ratio','z-index']]
    return result
def boilerplate(value):
    return value.strip() in {'ブラウザーの互換性','ブラウザー互換性','関連情報','仕様書'} or bool(re.search(r'お問い合わせ|お問合せ|電話番号|FAX|Copyright|All Rights|印刷する|このページはコミュニティー|View in English|Always switch to English|この機能は広く実装|この機能の一部は|すべてのブラウザーで利用可能|MDN の寄稿者|フィードバック|ブラウザー互換性一覧表を表示|Help improve MDN|Report a problem|View this page on GitHub',value,re.I))
def prose_record(site,url,extra=None):
    raw,metadata=fetch(url);text,encoding=decode(raw);parser=Prose() if site=='mdn' else Page();parser.feed(text)
    blocks=[];seen=set()
    for b in parser.blocks:
        value=b['text']
        if value in seen or b['tag']=='li' or (b['tag']=='p' and len(value)<25):continue
        if boilerplate(value):continue
        seen.add(value);blocks.append(b)
    body='\n'.join(b['text'] for b in blocks)
    ja=len(re.findall(r'[ぁ-ゖァ-ヺ一-龯]',body))
    if len(body)<200 or ja/max(1,len(body))<.25:raise ValueError('Insufficient Japanese prose')
    title=''.join(parser.title).strip()
    return dict(id=site+':url:'+digest(metadata['finalUrl'].encode())[:16],site=site,url=url,title=title,text=body,blocks=blocks,textSha256=digest(body.encode()),htmlSha256=digest(raw),encoding=encoding,author='MDN contributors' if site=='mdn' else '農林水産省' if site=='maff' else '気象庁',license='CC BY-SA 4.0' if site=='mdn' else '公共データ利用規約（第1.0版）',licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/' if site=='mdn' else LICENSE,policyUrl=MDN_POLICY if site=='mdn' else POLICIES[site],modifications='Main headings and whole prose paragraphs. Whitespace normalized; navigation/contact/code/tables/list fragments/translation and browser-support boilerplate excluded. No synthetic rewriting.',**metadata)
def literature_record(r):
    url=r['XHTML/HTMLファイルURL'];raw,metadata=fetch(url);text,encoding=decode(raw);parser=Literature();parser.feed(text);body=parser.text()
    if not parser.seen_main or not 3000<=len(body)<=180000:raise ValueError('Non-prose, too short or long public-domain work')
    if body.count('※')>2:raise ValueError('Unresolved external glyphs in main prose')
    if len(re.findall(r'[ぁ-ゖァ-ヺ一-龯]',body))/len(body)<.6:raise ValueError('Insufficient native Japanese prose')
    return dict(id='aozora:work:'+r['作品ID'],site='aozora',url=url,cardUrl=r['図書カードURL'],title=r['作品名'],author=r['姓']+r['名'],text=body,textSha256=digest(body.encode()),htmlSha256=digest(raw),encoding=encoding,license='Public-domain Japanese original; Aozora public-domain handling standard',licenseUrl=AOZORA_POLICY,policyUrl=AOZORA_POLICY,workCopyright=r['作品著作権フラグ'],personCopyright=r['人物著作権フラグ'],orthography=r['文字遣い種別'],bibliography=r,modifications='Only main_text. Ruby pronunciation, editorial notes, images, title/credit/navigation/footer outside main prose excluded. Paragraph boundaries preserved; no kana modernization or invented text. Full inputter/proofreader/publication credits retained in bibliography.',**metadata)
def main():
    p=argparse.ArgumentParser();p.add_argument('--aozora-per-author',type=int,default=12);p.add_argument('--maff-extra',type=int,default=200);p.add_argument('--workers',type=int,default=3);args=p.parse_args()
    policies=[snapshot(AOZORA_POLICY,'aozora'),snapshot(MDN_POLICY,'mdn'),*[snapshot(u,'government') for u in POLICIES.values()]]
    docs=[];existing=set();failed=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Preserve prior raw source documents, not authored QA/profile prose.
    for name in ['web','mdn']:
        old_manifest=json.loads((HERE.parent/'dialogue'/f'{name}-language-sources.json').read_text());sources={s['id']:s for s in old_manifest['sources']}
        for line in (HERE.parent/'dialogue'/f'{name}-language-documents.jsonl').read_text().splitlines():
            old=json.loads(line);source=sources[old['id']]
            assert digest(old['text'].encode())==old['textSha256']
            if old['site']=='mdn':body='\n'.join(b['text'] for b in old['blocks'] if not boilerplate(b['text']))
            else:body=old['text']
            record={**source,**old,'text':body,'originalTextSha256':old['textSha256'],'textSha256':digest(body.encode()),'reusedSourceSnapshot':True};record.pop('partition',None);docs.append(record);existing.add(old['url'])
    baseline=dict(documents=len(docs),characters=sum(len(d['text']) for d in docs),sites=dict(collections.Counter(d['site'] for d in docs)))
    urls=[]
    for category in ['nougyou','kome_tukurikata','kome_sonota','mame','syokuhin','yasai1','niku','ringyou','suisan','sonota']:
        index='https://www.maff.go.jp/j/heya/kodomo_sodan/'+category+'.html';raw,_=fetch(index);page=Page();page.feed(decode(raw)[0])
        for link in page.links:
            url=urllib.parse.urljoin(index,link)
            if re.search(r'/kodomo_sodan/\d{4}/[^/]+\.html$',url) and url not in existing:urls.append(('maff',url));existing.add(url)
    urls=sorted(urls,key=lambda row:digest(row[1].encode()))[:args.maff_extra]
    urls += [('mdn','https://developer.mozilla.org/ja/docs/Web/'+path) for path in mdn_paths() if 'https://developer.mozilla.org/ja/docs/Web/'+path not in existing]
    def safe_prose(item):
        try:return prose_record(*item),None
        except Exception as error:return None,dict(site=item[0],url=item[1],error=str(error))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i,(record,error) in enumerate(pool.map(safe_prose,urls)):
            if record:docs.append(record)
            if error:failed.append(error)
            if i%20==0:print(json.dumps(dict(event='modern-prose',completed=i+1,total=len(urls),characters=sum(len(d['text']) for d in docs))),flush=True)
    raw,metadata=fetch(AOZORA_INDEX);(HERE/'aozora-index.zip').write_bytes(raw);archive=zipfile.ZipFile(io.BytesIO(raw));rows=list(csv.DictReader(io.StringIO(archive.read('list_person_all_extended_utf8.csv').decode('utf-8-sig'))))
    by_work=collections.defaultdict(list)
    for r in rows:by_work[r['作品ID']].append(r)
    candidates=collections.defaultdict(list)
    for entries in by_work.values():
        if not all(r['作品著作権フラグ']=='なし' and r['人物著作権フラグ']=='なし' and r['役割フラグ']=='著者' for r in entries):continue
        r=entries[0];author=r['姓']+r['名']
        if author not in AUTHORS or r['文字遣い種別']!='新字新仮名' or not r['XHTML/HTMLファイルURL']:continue
        candidates[author].append(r)
    selected=[]
    for author in sorted(candidates):selected.extend(sorted(candidates[author],key=lambda r:digest(r['作品ID'].encode()))[:args.aozora_per_author*3])
    count=collections.Counter()
    def safe_literature(r):
        try:return literature_record(r),None
        except Exception as error:return None,dict(site='aozora',url=r['XHTML/HTMLファイルURL'],title=r['作品名'],error=str(error))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i,(record,error) in enumerate(pool.map(safe_literature,selected)):
            if record and count[record['author']]<args.aozora_per_author:docs.append(record);count[record['author']]+=1
            if error:failed.append(error)
            if i%30==0:print(json.dumps(dict(event='literature',completed=i+1,total=len(selected),accepted=sum(count.values()),characters=sum(len(d['text']) for d in docs))),flush=True)
    # Freeze raw snapshots; document/near-duplicate grouping follows separately.
    unique=[];seen_text=set();seen_urls=set()
    for d in docs:
        url=d.get('finalUrl',d['url'])
        if d['textSha256'] in seen_text or url in seen_urls:continue
        seen_text.add(d['textSha256']);seen_urls.add(url);unique.append(d)
    unique.sort(key=lambda d:d['id'])
    (HERE/'documents.jsonl').write_text('\n'.join(json.dumps(d,ensure_ascii=False,separators=(',',':')) for d in unique)+'\n')
    manifest=dict(schemaVersion=1,retrievedAt=now,baseline=baseline,documents=len(unique),characters=sum(len(d['text']) for d in unique),utf8Bytes=sum(len(d['text'].encode()) for d in unique),sites={site:dict(documents=sum(d['site']==site for d in unique),characters=sum(len(d['text']) for d in unique if d['site']==site)) for site in sorted({d['site'] for d in unique})},authors=dict(count),policies=policies,aozoraIndex=dict(url=AOZORA_INDEX,zipSha256=digest(raw),**metadata),excludedSources=['Wikipedia','protected-copyright Aozora works','translations','external generated teacher prose','pretrained weights','pretrained tokenizer'],failed=failed,processing='Raw source text only. No QA wrappers, labels or own-profile additions. Full retained credit metadata; no author text cut to a character budget.')
    manifest['documentsFileSha256']=digest((HERE/'documents.jsonl').read_bytes());(HERE/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:manifest[k] for k in ['documents','characters','utf8Bytes','sites','baseline']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
