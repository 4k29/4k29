"""Licensed explanatory source paragraphs, no QA pairs or rewritten sentences."""
import concurrent.futures,datetime,importlib.util,json,pathlib,re,urllib.error,urllib.parse,urllib.robotparser
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('original_collection',ROOT.parent/'collect_sources.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
POLICY=base.POLICIES['jma'];SEEDS=['https://www.jma.go.jp/jma/kishou/know/faq/index.html','https://www.jma.go.jp/jma/kishou/know/yougo_hp/index.html']
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    policies=[base.snapshot(POLICY,'government')];robots='https://www.jma.go.jp/robots.txt'
    try:
        raw,meta=base.fetch(robots);text,encoding=base.decode(raw);rp=urllib.robotparser.RobotFileParser();rp.parse(text.splitlines());policies.append(dict(url=robots,text=text,sha256=base.digest(raw),encoding=encoding,**meta))
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        rp=None;policies.append(dict(url=robots,status=404))
    old=[json.loads(x) for x in (ROOT.parent/'round2/documents.jsonl').read_text().splitlines()];known={d['url'] for d in old};seen=set(known);frontier=SEEDS;docs=[];failed=[];discovery=[]
    def safe(url):
        try:
            if rp is not None and not rp.can_fetch(base.USER_AGENT,url):raise ValueError('Robots excludes URL')
            raw,meta=base.fetch(url);text,encoding=base.decode(raw);parser=base.Page();parser.feed(text)
            links=[]
            for link in parser.links:
                target=urllib.parse.urljoin(meta['finalUrl'],link).split('#')[0];parts=urllib.parse.urlparse(target)
                if parts.hostname=='www.jma.go.jp' and parts.path.startswith('/jma/kishou/know/') and parts.path.endswith('.html') and not parts.query:links.append(target)
            blocks=[b for b in parser.blocks if b['tag']=='p' and len(b['text'])>=30 and not base.boilerplate(b['text']) and b['text'][-1:] in '。！？」']
            body='\n'.join(b['text'] for b in blocks)
            if re.search(r'転載禁止|無断転載|別途許諾',body):raise ValueError('Individual rights restriction')
            doc=None
            if len(body)>=200 and len(re.findall(r'[ぁ-ゖァ-ヺ一-龯]',body))/len(body)>=.25:
                doc=dict(id='jma:url:'+base.digest(meta['finalUrl'].encode())[:16],site='jma',url=url,**meta,title=''.join(parser.title).strip(),author='気象庁',text=body,textSha256=base.digest(body.encode()),htmlSha256=base.digest(raw),encoding=encoding,license='公共データ利用規約（第1.0版）',licenseUrl=base.LICENSE,policyUrl=POLICY,modifications='Original complete p paragraphs only, no question headings, QA wrappers, synthetic words, tables, navigation or contact boilerplate; layout whitespace normalized.')
            return doc,sorted(set(links)),dict(url=url,htmlSha256=base.digest(raw),links=len(set(links))),None
        except Exception as e:return None,[],None,dict(url=url,error=str(e))
    for depth in range(4):
        urls=sorted(set(frontier)-seen,key=lambda u:base.digest(('1329|'+u).encode()))[:max(0,180-len(discovery)-len(failed))];seen.update(urls);frontier=[]
        if not urls:break
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for i,(doc,links,index,error) in enumerate(pool.map(safe,urls)):
                if doc:docs.append(doc)
                frontier.extend(links)
                if index:discovery.append(index)
                if error:failed.append(error)
                if i%20==0:print(json.dumps(dict(depth=depth,completed=i+1,total=len(urls),accepted=len(docs))),flush=True)
    hashes={d['textSha256'] for d in old};unique=[]
    for d in sorted(docs,key=lambda d:d['id']):
        if d['textSha256'] not in hashes:unique.append(d);hashes.add(d['textSha256'])
    out=ROOT/'weather-documents.jsonl';out.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in unique));write(ROOT/'weather-credits.json',[{k:v for k,v in d.items() if k!='text'} for d in unique])
    report=dict(retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),documents=len(unique),characters=sum(len(d['text']) for d in unique),utf8Bytes=sum(len(d['text'].encode()) for d in unique),documentsSha256=base.digest(out.read_bytes()),policies=policies,discovery=discovery,failed=failed,sourceQuestionsUsedAsLabels=False,externalWeightsOrTokenizerOrGeneration=False)
    write(ROOT/'weather-sources.json',report);print(json.dumps({k:report[k] for k in ['documents','characters','utf8Bytes']}),flush=True)
if __name__=='__main__':main()
