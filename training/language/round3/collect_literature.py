"""Additional attributed public-domain narrative; raw words, never QA/teachers."""
import collections,concurrent.futures,csv,datetime,hashlib,importlib.util,io,json,pathlib,urllib.error,urllib.robotparser,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('original_collection',ROOT.parent/'collect_sources.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
AUTHORS={'小川未明','山本周五郎','豊島与志雄','海野十三','菊池寛','江戸川乱歩','久生十蘭','坂口安吾','織田作之助','横光利一','新美南吉','太宰治','宮沢賢治','芥川竜之介'}
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    policies=[base.snapshot(base.AOZORA_POLICY,'aozora')]
    robots='https://www.aozora.gr.jp/robots.txt'
    try:
        raw,meta=base.fetch(robots);text,encoding=base.decode(raw)
        rp=urllib.robotparser.RobotFileParser();rp.parse(text.splitlines())
        if not rp.can_fetch(base.USER_AGENT,base.AOZORA_INDEX):raise ValueError('Robots excludes index')
        policies.append(dict(url=robots,text=text,sha256=base.digest(raw),encoding=encoding,**meta))
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        policies.append(dict(url=robots,status=404,note='No robots resource; no access-denied source is bypassed'))
        rp=None
    raw,meta=base.fetch(base.AOZORA_INDEX);(ROOT/'aozora-index.zip').write_bytes(raw)
    archive=zipfile.ZipFile(io.BytesIO(raw));csv_raw=archive.read('list_person_all_extended_utf8.csv');rows=list(csv.DictReader(io.StringIO(csv_raw.decode('utf-8-sig'))))
    prior=[json.loads(x) for x in (ROOT.parent/'round2/documents.jsonl').read_text().splitlines()];existing={d['id'] for d in prior};by_work=collections.defaultdict(list)
    for row in rows:by_work[row['作品ID']].append(row)
    candidates=collections.defaultdict(list)
    for entries in by_work.values():
        if not all(r['作品著作権フラグ']=='なし' and r['人物著作権フラグ']=='なし' and r['役割フラグ']=='著者' for r in entries):continue
        r=entries[0];author=r['姓']+r['名'];url=r['XHTML/HTMLファイルURL']
        if author not in AUTHORS or r['文字遣い種別']!='新字新仮名' or not url or 'aozora:work:'+r['作品ID'] in existing:continue
        if rp is not None and not rp.can_fetch(base.USER_AGENT,url):continue
        candidates[author].append(r)
    # A source quota limits collection requests, never truncates an accepted work.
    selected=[r for author in sorted(candidates) for r in sorted(candidates[author],key=lambda r:base.digest(('1329|'+r['作品ID']).encode()))[:48]]
    def safe(row):
        try:return base.literature_record(row),None
        except Exception as e:return None,dict(url=row['XHTML/HTMLファイルURL'],work=row['作品ID'],error=str(e))
    docs=[];failed=[];seen={d['textSha256'] for d in prior};duplicates=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,(doc,error) in enumerate(pool.map(safe,selected)):
            if doc:
                if doc['textSha256'] in seen:duplicates.append(doc['id'])
                else:docs.append(doc);seen.add(doc['textSha256'])
            if error:failed.append(error)
            if i%30==0:print(json.dumps(dict(completed=i+1,total=len(selected),accepted=len(docs),characters=sum(len(d['text']) for d in docs))),flush=True)
    docs.sort(key=lambda d:d['id']);out=ROOT/'additional-documents.jsonl';out.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in docs))
    write(ROOT/'source-credits.json',[{k:v for k,v in d.items() if k!='text'} for d in docs])
    report=dict(retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),documents=len(docs),characters=sum(len(d['text']) for d in docs),utf8Bytes=sum(len(d['text'].encode()) for d in docs),documentsSha256=base.digest(out.read_bytes()),index=dict(url=base.AOZORA_INDEX,zipSha256=base.digest(raw),csvSha256=base.digest(csv_raw),**meta),policies=policies,authors=dict(collections.Counter(d['author'] for d in docs)),failed=failed,duplicates=duplicates,processing='Reviewed public-domain original Japanese author works only, new-character/new-kana orthography. Entire main_text, ruby reading and notes omitted, unresolved glyphs excluded; no synthetic rewriting, truncation, QA, teacher or outside tokenizer/weights/API.')
    write(ROOT/'sources.json',report);print(json.dumps({k:report[k] for k in ['documents','characters','utf8Bytes']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
