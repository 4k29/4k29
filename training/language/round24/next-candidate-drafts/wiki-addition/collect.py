"""Prospective historical human-community prose only; no model calls or updates."""
import pathlib,json,hashlib,re,datetime,urllib.request,urllib.parse,concurrent.futures,importlib.util,argparse,time
import mwparserfromhell
R=pathlib.Path(__file__).resolve().parent
REPO=next(p for p in R.parents if (p/'.git').exists());B=REPO/'training/language'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def fetch(url,limit=2097152):
    host=urllib.parse.urlparse(url).hostname
    assert host in ['ja.wikipedia.org','foundation.wikimedia.org','creativecommons.org']
    req=urllib.request.Request(url,headers={'User-Agent':'4k29-own-transformer-language-research/1.0 (https://github.com/4k29/4k29)'})
    with urllib.request.urlopen(req,timeout=30) as h:
        assert urllib.parse.urlparse(h.url).hostname==host
        raw=h.read(limit+1);assert len(raw)<=limit
        return raw,dict(finalUrl=h.url,contentType=h.headers.get('Content-Type'),retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat())
def extract(wikitext,p):
    if any(x in wikitext for x in p['machineTranslationMarkersExcluded']):return [],'machine_translation_marker'
    if re.search(r'転載許可|GFDLのみ|fair.use',wikitext,re.I):return [],'licensing_exception_marker'
    code=mwparserfromhell.parse(wikitext)
    for tag in list(code.filter_tags()):
        if str(tag.tag).lower() in ['ref','references']:
            try:code.replace(tag,'')
            except ValueError:pass
    for tag in list(code.filter_tags()):
        if str(tag.tag).lower() in ['table','blockquote','poem','math','score','gallery','timeline','syntaxhighlight']:
            try:code.replace(tag,'__EXCLUDED__')
            except ValueError:pass
    for template in list(code.filter_templates(recursive=False)):code.replace(template,'__EXCLUDED__')
    for link in list(code.filter_wikilinks()):
        if re.match(r'\s*:?(File|Image|Category|ファイル|画像|カテゴリ|カテゴリー):',str(link.title),re.I):
            try:code.replace(link,'__EXCLUDED__')
            except ValueError:pass
    raw=re.sub(r'(?m)^(=+[^\n]*=+)\s*$',r'\n\n\1\n\n',str(code));blocks=[];count=0
    for block in re.split(r'\n\s*\n',raw):
        block=block.strip()
        if not block:continue
        heading=re.fullmatch(r'=+\s*(.*?)\s*=+',block)
        if heading:
            title=heading.group(1).strip('= ')
            if title in p['stopBeforeReferenceHeadings']:break
            blocks.append(str(mwparserfromhell.parse(title).strip_code()).strip());continue
        if '__EXCLUDED__' in block or re.search(r'(?m)^\s*[|!*#;:]|\{\||\|\}',block):continue
        text=re.sub(r'\s+',' ',str(mwparserfromhell.parse(block).strip_code())).strip()
        if not p['minimumParagraphCharacters']<=len(text)<=p['maximumParagraphCharacters']:continue
        if len(re.findall('[ぁ-ゖァ-ヺ一-龯]',text))/len(text)<p['minimumJapaneseFraction']:continue
        if text[-1:] not in '。！？」）' or not re.search('[。！？]',text):continue
        if re.search(r'「[^」]{31,}」|『[^』]{31,}』',text):continue
        if '\ufffd' in text or re.search(r'__\w+__|\{\{|\}\}|<ref|https?://',text):continue
        blocks.append(text);count+=1
        if count==p['maxAcceptedParagraphsPerDocument']:break
    return blocks,None
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',type=pathlib.Path,default=R/'sources');args=a.parse_args();p=read(R/'collection-policy.json');out=args.out;out.mkdir(exist_ok=False);(out/'raw').mkdir();(out/'terms').mkdir()
    assert mwparserfromhell.__version__=='0.7.2'
    terms=[]
    for name,url in [('cc-by-sa-4',p['licenseUrl']),('cc-by-sa-3',p['historicLicenseUrl']),('wikimedia',p['termsUrl'])]:
        raw,meta=fetch(url);(out/'terms'/f'{name}.html').write_bytes(raw);terms.append(dict(url=url,sha256=sha(raw),**meta))
    rights_url=p['api']+'?'+urllib.parse.urlencode(dict(action='query',meta='siteinfo',siprop='rightsinfo',format='json'))
    raw,meta=fetch(rights_url);rights=json.loads(raw);assert '4.0' in json.dumps(rights) and 'creativecommons.org' in json.dumps(rights);(out/'terms/site-rights.json').write_bytes(raw)
    spec=importlib.util.spec_from_file_location('legacy_chains',B/'round3/prepare.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    def work(title):
        url=p['api']+'?'+urllib.parse.urlencode(dict(action='query',prop='revisions',titles=title,redirects='1',rvprop='ids|timestamp|content',rvslots='main',rvstart=p['revisionCutoff'],rvlimit='1',format='json',formatversion='2'))
        errors=[]
        for attempt in range(p['attempts']):
            try:
                raw,meta=fetch(url,p['maxResponseBytes']);data=json.loads(raw);page=data['query']['pages'][0];rev=page['revisions'][0];assert rev['timestamp']<=p['revisionCutoff']
                return title,url,raw,meta,page,rev,errors
            except Exception as ex:
                errors.append(str(ex));
                if attempt+1<p['attempts']:time.sleep(1)
        return title,url,None,None,None,None,errors
    sources=[];units=[];failures=[];seen_pages=set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=p['workers']) as pool:
        for title,url,raw,meta,page,rev,errors in pool.map(work,p['titles']):
            if raw is None:failures.append(dict(title=title,url=url,errors=errors));continue
            key=sha(title.encode())[:16];(out/'raw'/f'{key}.json').write_bytes(raw)
            if page['pageid'] in seen_pages:failures.append(dict(title=title,reason='same canonical pageid as earlier requested title'));continue
            seen_pages.add(page['pageid']);slot=rev['slots']['main']
            if 'texthidden' in slot or 'content' not in slot:
                failures.append(dict(title=title,revision=rev['revid'],reason='Revision text not publicly available; skipped without alternate retrieval'));continue
            wt=slot['content'];(out/'raw'/f'{key}.wikitext').write_text(wt)
            blocks,reason=extract(wt,p);text='\n'.join(blocks);did='wiki2019:'+str(page['pageid']);partition='reserved' if int(sha(did.encode()),16)%10==0 else 'train'
            permanent='https://ja.wikipedia.org/w/index.php?oldid='+str(rev['revid']);history='https://ja.wikipedia.org/w/index.php?'+urllib.parse.urlencode(dict(title=page['title'],action='history'))
            doc=dict(id=did,site='wiki2019',title=page['title'],requestedTitle=title,pageid=page['pageid'],revision=rev['revid'],revisionTimestamp=rev['timestamp'],partition=partition,url=permanent,historyUrl=history,author='日本語版ウィキペディア「'+page['title']+'」の執筆者',license=p['license'],licenseUrl=p['licenseUrl'],historicLicenseUrl=p['historicLicenseUrl'],policyUrl=p['termsUrl'],attribution='出典：Wikipedia contributors, '+page['title']+' ('+permanent+'); authors/history: '+history+'; adapted markup and paragraph selection, CC BY-SA4.0.',text=text,blocks=blocks,textSha256=sha(text.encode()),wikitextSha256=sha(wt.encode()),apiResponseSha256=sha(raw),rawFile='raw/'+key+'.json',wikitextFile='raw/'+key+'.wikitext',processing=p['processing'],extractionExclusionReason=reason,retriedErrors=errors,**meta)
            sources.append(doc)
            if partition=='train':
                for start,end,t in legacy.chains(doc):
                    if not p['minimumUnitCharacters']<=len(t)<=p['maximumUnitCharacters'] or len(re.findall('[ぁ-ゖァ-ヺ一-龯]',t))/len(t)<p['minimumJapaneseFraction'] or len(re.findall('[。！？]',t))<p['minimumSentenceTerminators']:continue
                    assert t=='\n'.join(blocks[start:end])
                    units.append(dict(doc,id=did+':unit:'+str(start),originalDocument=did,originalTextSha256=doc['textSha256'],unitKey=did+':chain:'+str(start),startLine=start,endLine=end,text=t,blocks=t.splitlines(),textSha256=sha(t.encode())))
            print(json.dumps(dict(title=title,partition=partition,characters=len(text),excluded=reason)),flush=True)
    old=[json.loads(l) for l in (B/'round10/documents.jsonl').read_text().splitlines()];parts={x['document']:x['partition'] for x in read(B/'round10/split.json')['assignments']}
    held=[d['text'] for d in old if parts[d['id']]!='train'];train=[d['text'] for d in old if parts[d['id']]=='train'];old_held=len(held)
    for path in [B/'round18/sources/documents.jsonl',B/'round22/sources/source-documents.jsonl']:
        extra=[json.loads(l) for l in path.read_text().splitlines()];held.extend(d['text'] for d in extra if d['partition']=='reserved');train.extend(d['text'] for d in extra if d['partition']=='train')
    held.extend(d['text'] for d in sources if d['partition']=='reserved')
    wanted={d['text'][i:i+64] for d in units for i in range(len(d['text'])-63)};forbidden=set()
    for t in held+train:
        for i in range(max(0,len(t)-63)):
            g=t[i:i+64]
            if g in wanted:forbidden.add(g)
    admitted=[];excluded=[];seen=set()
    for d in units:
        grams={d['text'][i:i+64] for i in range(len(d['text'])-63)}
        if grams & (forbidden|seen):excluded.append(dict(unitKey=d['unitKey'],reason='64-character exact overlap with old source, reserved source or earlier admitted TRAIN unit'));continue
        admitted.append(d);seen.update(grams)
    (out/'documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in admitted));(out/'source-documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in sources))
    write(out/'license-records.json',dict(policies=terms,rightsInfo=rights,rightsInfoSha256=sha((out/'terms/site-rights.json').read_bytes()),sourceSubsetLicense=p['license'],noImagesOrExternalLinkedMaterials=True))
    manifest=dict(retrievedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),collectionPolicySha256=sha((R/'collection-policy.json').read_bytes()),collectorSha256=sha(pathlib.Path(__file__).read_bytes()),sourcesRequested=len(p['titles']),fetchedDocuments=len(sources),admittedDocuments=len({d['originalDocument'] for d in admitted}),candidateTrainUnits=len(units),admittedUnits=len(admitted),admittedCharacters=sum(len(d['text']) for d in admitted),reservedDocuments=sum(d['partition']=='reserved' for d in sources),sourceDocumentsSha256=sha((out/'source-documents.jsonl').read_bytes()),documentsSha256=sha((out/'documents.jsonl').read_bytes()),existingNonTrainRawDocumentsAudited=old_held,failures=failures,excluded=excluded,testReadForDuplicateAudit=True,testScoredOrGenerated=False,reservedEncoded=False,existingFoldsChanged=False,experimentalOptimizerUpdates=0,minimumInterventionReached=len({d['originalDocument'] for d in admitted})>=p['minimumTrainDocuments'] and len(admitted)>=p['minimumTrainUnits'] and sum(len(d['text']) for d in admitted)>=p['minimumTrainCharacters'])
    write(out/'manifest.json',manifest);print(json.dumps({k:v for k,v in manifest.items() if k not in ['failures','excluded']}),flush=True);assert manifest['minimumInterventionReached'],'Frozen collection minimum not met; no training on this attempt'
