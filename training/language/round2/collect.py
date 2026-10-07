"""Collect attributed government prose, never model-authored training text."""
import concurrent.futures, datetime, hashlib, json, pathlib, re, urllib.parse, urllib.request
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
HOSTS = {'www.soumu.go.jp', 'www.env.go.jp'}
POLICIES = {'mic': 'https://www.soumu.go.jp/menu_kyotsuu/policy/tyosaku.html',
            'env': 'https://www.env.go.jp/mail.html'}
AUTHORS = {'mic': '総務省', 'env': '環境省'}
VOID = {'br', 'img', 'meta', 'link', 'input', 'hr', 'source', 'wbr', 'area', 'embed', 'param'}

def sha(b): return hashlib.sha256(b).hexdigest()
def write(name, obj): (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
def fetch(url):
    if urllib.parse.urlparse(url).hostname not in HOSTS: raise ValueError('Host outside reviewed scope')
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'OwnJapaneseResearch/2.0 (attributed public prose)'}), timeout=25) as r:
        if urllib.parse.urlparse(r.url).hostname not in HOSTS: raise ValueError('Redirect outside scope')
        raw = r.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024: raise ValueError('Source exceeds bound')
        final = r.url
    for encoding in ['utf-8', 'cp932', 'euc-jp']:
        try: return raw, raw.decode(encoding), encoding, final
        except UnicodeDecodeError: pass
    raise ValueError('No exact decoding')

class Prose(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.stack=[]; self.parts=None; self.paragraphs=[]; self.title=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag not in VOID: self.stack.append((tag,a))
        if tag=='p': self.parts=[]
    def handle_endtag(self, tag):
        if tag=='p' and self.parts is not None:
            text=re.sub(r'\s+', ' ', ''.join(self.parts)).strip(); self.parts=None
            if len(text)>=40 and text[-1:] in '。！？」' and len(re.findall(r'[ぁ-ゖァ-ヺ一-龯]',text))/len(text)>=.25:
                if text not in self.paragraphs: self.paragraphs.append(text)
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag: del self.stack[i:]; break
    def handle_data(self, text):
        if any(t=='title' for t,a in self.stack): self.title.append(text)
        inside=any(a.get('id')=='contents' or t=='main' or any(k in a.get('class','').split() for k in ['honbun','hakusho']) for t,a in self.stack)
        excluded=any(t in {'script','style','table','nav','header','footer','figure','sup'} or any(k in a.get('class','').split() for k in ['fn','footnote','figure','figRefer','figName','caption','figblock']) for t,a in self.stack)
        if self.parts is not None and inside and not excluded: self.parts.append(text)

def links(url, pattern):
    raw, text, encoding, final=fetch(url)
    found=sorted({urllib.parse.urljoin(final,h.split('#')[0]) for h in re.findall(r'href=[\"\']([^\"\']+)',text,re.I) if re.search(pattern,h)})
    return found,dict(url=url,finalUrl=final,htmlSha256=sha(raw),encoding=encoding,discovered=len(found))

def record(item):
    site,url=item
    try:
        raw,text,encoding,final=fetch(url); p=Prose();p.feed(text); body='\n'.join(p.paragraphs)
        if len(body)<200: raise ValueError('Insufficient complete main prose')
        if re.search(r'転載禁止|無断転載|別途許諾',body): raise ValueError('Individual rights restriction requires review')
        return dict(id=site+':url:'+sha(final.encode())[:16],site=site,url=url,finalUrl=final,title=''.join(p.title).strip(),author=AUTHORS[site],text=body,textSha256=sha(body.encode()),htmlSha256=sha(raw),encoding=encoding,license='公共データ利用規約（第1.0版）',licenseUrl='https://www.digital.go.jp/resources/open_data/public_data_license_v1.0',policyUrl=POLICIES[site],modifications='Official main prose paragraphs only; layout whitespace normalized; figures, tables, footnotes, navigation and footnote markers omitted. No synthetic rewriting.'),None
    except Exception as e: return None,dict(site=site,url=url,error=str(e))

def main():
    policies=[];indexes=[];urls=[];failed=[]
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for site,url in POLICIES.items():
        raw,text,encoding,final=fetch(url)
        if '公共データ利用規約' not in text: raise ValueError('Reviewed terms changed')
        policies.append(dict(site=site,url=url,finalUrl=final,htmlSha256=sha(raw),encoding=encoding,html=text))
        rraw,rtext,rencoding,rfinal=fetch('https://'+urllib.parse.urlparse(url).hostname+'/robots.txt')
        policies.append(dict(site=site,url=rfinal,htmlSha256=sha(rraw),encoding=rencoding,text=rtext))
    for year in ['r08','r07','r06']:
        for site,url,pattern in [('mic',f'https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/{year}/html/datashu.html',r'(?:^|/)nd[0-9a-z]+\.html'),('env',f'https://www.env.go.jp/policy/hakusyo/{year}/index.html',r'(?:^|/)hj[0-9_]+\.html')]:
            try:
                found,index=links(url,pattern);indexes.append(index);urls.extend((site,u) for u in found)
            except Exception as e: failed.append(dict(url=url,error=str(e)))
    urls=sorted(set(urls));docs=[];seen=set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,(d,error) in enumerate(pool.map(record,urls)):
            if d and d['textSha256'] not in seen: docs.append(d);seen.add(d['textSha256'])
            if error: failed.append(error)
            if i%25==0: print(json.dumps(dict(completed=i+1,total=len(urls),accepted=len(docs),characters=sum(len(d['text']) for d in docs))),flush=True)
    docs.sort(key=lambda d:d['id'])
    path=ROOT/'modern-documents.jsonl';path.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in docs))
    report=dict(retrievedAt=now,documents=len(docs),characters=sum(len(d['text']) for d in docs),utf8Bytes=sum(len(d['text'].encode()) for d in docs),documentsSha256=sha(path.read_bytes()),policies=policies,indexes=indexes,failed=failed,excluded=['Wikipedia','external generated prose','pretrained weights/tokenizer','access-denied sources','figures/tables/third-party images'])
    write('modern-sources.json',report);write('source-credits.json',[{k:v for k,v in d.items() if k!='text'} for d in docs]);print(json.dumps({k:report[k] for k in ['documents','characters','utf8Bytes']}),flush=True)

if __name__=='__main__': main()
