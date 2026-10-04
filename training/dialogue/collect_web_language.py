"""Raw Japanese from approved open government sites, excluding Wikipedia.

No external generative API or weights. Preserve URLs, policy snapshots, hashes,
retrieval metadata and processing details. Text only; no images/third-party files.
"""
from html.parser import HTMLParser
import datetime
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
USER_AGENT='4k29-own-transformer-language-research/1.0'
LICENSE='https://www.digital.go.jp/resources/open_data/public_data_license_v1.0'
POLICIES={'jma':'https://www.jma.go.jp/jma/kishou/info/coment.html','maff':'https://www.maff.go.jp/j/use/link.html'}
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.stack=[];self.blocks=[];self.links=[];self.block=None;self.title=[]
    def scoped(self):return any(t=='main' or a.get('id')=='main_content' for t,a in self.stack)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag not in VOID:self.stack.append((tag,a))
        if self.scoped() and not any(t in ['script','style','nav','header','footer'] for t,a in self.stack):
            if tag in ['h1','h2','h3','p','li'] and self.block is None:self.block=[tag,len(self.stack),[]]
            if tag=='a' and a.get('href'):self.links.append(a['href'])
    def handle_endtag(self,tag):
        if self.block and tag==self.block[0] and len(self.stack)==self.block[1]:
            text=re.sub(r'\s+',' ',''.join(self.block[2])).strip()
            if text:self.blocks.append(dict(tag=tag,text=text))
            self.block=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:del self.stack[i:];break
    def handle_data(self,text):
        if any(t in ['script','style'] for t,a in self.stack):return
        if self.block:self.block[2].append(text)
        if any(t=='title' for t,a in self.stack):self.title.append(text)
def fetch(url):
    host=urllib.parse.urlparse(url).hostname
    if host not in ['www.jma.go.jp','www.maff.go.jp','www.digital.go.jp']:raise ValueError('Source host is not approved')
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read();headers=dict(lastModified=r.headers.get('Last-Modified'),contentType=r.headers.get('Content-Type'))
    try:html=raw.decode('utf-8')
    except UnicodeDecodeError:html=raw.decode('cp932')
    page=Page();page.feed(html)
    return page,html,raw,headers
def main():
    policies=[]
    for site,url in POLICIES.items():
        page,html,raw,headers=fetch(url)
        if '公共データ利用規約' not in html or LICENSE not in html:raise ValueError('Review changed usage terms: '+url)
        policies.append(dict(site=site,url=url,htmlSha256=hashlib.sha256(raw).hexdigest(),paragraphs=[b['text'] for b in page.blocks if b['tag'] in ['h1','h2','h3','p']],**headers))
    urls=[('jma',f'https://www.jma.go.jp/jma/kishou/know/faq/faq{n}.html') for n in [1,2,3,4,5,6,7,8,9,11,13,14,17,19,20,21,22,27,29,33]]
    for category in ['nougyou','kome_tukurikata','kome_sonota','mame','syokuhin','yasai1','niku','ringyou','suisan','sonota']:
        index='https://www.maff.go.jp/j/heya/kodomo_sodan/'+category+'.html'
        page,_,_,_=fetch(index)
        links=[]
        for link in page.links:
            u=urllib.parse.urljoin(index,link)
            if re.search(r'/kodomo_sodan/\d{4}/[^/]+\.html$',u) and u not in links:links.append(u)
        urls.extend(('maff',u) for u in links[:3])
    documents=[];sources=[]
    # Source pages, rather than random sentence fragments, define holdouts.
    for i,(site,url) in enumerate(urls):
        page,html,raw,headers=fetch(url)
        blocks=[];seen=set()
        for b in page.blocks:
            text=b['text']
            if text in seen or (b['tag'] in ['p','li'] and len(text)<25):continue
            if re.search(r'お問い合わせ|お問合せ|代表：|電話番号|FAX|All Rights|Copyright|印刷する',text,re.I):continue
            seen.add(text);blocks.append(b)
        text='\n'.join(b['text'] for b in blocks)
        if len(text)<100:raise ValueError('Extraction too short: '+url)
        partition='validation' if i%10==8 else 'test' if i%10==9 else 'train'
        title=''.join(page.title).strip()
        sha=hashlib.sha256(text.encode()).hexdigest()
        documents.append(dict(id=f'{site}:{i}',site=site,url=url,title=title,partition=partition,text=text,blocks=blocks,textSha256=sha))
        sources.append(dict(id=f'{site}:{i}',author='気象庁' if site=='jma' else '農林水産省',url=url,title=title,attribution=f"出典：{'気象庁' if site=='jma' else '農林水産省'}ホームページ（{url}）を加工して作成",policyUrl=POLICIES[site],license='公共データ利用規約（第1.0版）',licenseUrl=LICENSE,htmlSha256=hashlib.sha256(raw).hexdigest(),textSha256=sha,modifications='HTML main-content prose only; headings/paragraphs extracted, whitespace collapsed, repeated text/navigation/contact details excluded. No images, linked files or synthetic rewriting.',**headers))
        print(json.dumps(dict(event='page',completed=i+1,total=len(urls),site=site,characters=len(text))),flush=True)
    (HERE/'web-language-documents.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in documents))
    manifest=dict(schemaVersion=1,retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),excludedSources=['Wikipedia','pretrained model weights','generative AI APIs'],sourceKind='Official Japanese explanatory text and FAQ; raw language data, not model-generated answers.',policySnapshots=policies,partitions={p:sum(r['partition']==p for r in documents) for p in ['train','validation','test']},characters=sum(len(r['text']) for r in documents),sources=sources)
    (HERE/'web-language-sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(event='complete',pages=len(documents),characters=manifest['characters'],partitions=manifest['partitions'])),flush=True)
if __name__=='__main__':main()
