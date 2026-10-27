"""Conservative derived wiki prose; raw XML/wikitext and attribution stay intact.

Community authorship is NOT certified human-only. No training admission.
"""
import argparse,bz2,collections,gzip,hashlib,json,pathlib,re,sys,time,xml.etree.ElementTree as ET
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,'/dev/shm/foundation-parser')
import mwparserfromhell
from build import norm,sha_file,sha_bytes,write

SENTINEL='REMOVED_NONPROSE_NODE'
DROP_TAGS={'ref','references','gallery','math','source','syntaxhighlight','code','pre','table','timeline','imagemap','score','poem'}
def prose(text):
 code=mwparserfromhell.parse(text);counts=collections.Counter()
 for node in list(code.filter_templates(recursive=True)):
  try:code.replace(node,SENTINEL);counts['templatesRemoved']+=1
  except ValueError:pass
 for node in list(code.filter_tags(recursive=True)):
  if str(node.tag).lower()in DROP_TAGS:
   try:code.replace(node,''if str(node.tag).lower()in {'ref','references'}else SENTINEL);counts['nonproseTagsRemoved']+=1
   except ValueError:pass
 for node in list(code.filter_wikilinks(recursive=True)):
  title=str(node.title).strip().lower()
  if re.match(r'^(ファイル|画像|file|image|category|カテゴリ|カテゴリー):',title):
   try:code.replace(node,SENTINEL);counts['mediaCategoryLinksRemoved']+=1
   except ValueError:pass
 plain=code.strip_code(normalize=False,collapse=False,keep_template_params=False)
 paragraphs=[]
 for block in re.split(r'\n\s*\n',plain):
  if not block.strip():continue
  counts['derivedBlocksBeforeFilter']+=1
  if SENTINEL in block:counts['blocksRejectedRemovedNode']+=1;continue
  lines=[]
  for line in block.splitlines():
   if re.match(r'^\s*[*#;:|!]',line):counts['listOrTableLinesExcluded']+=1
   else:lines.append(line)
  paragraph='\n'.join(lines).strip()
  if len(paragraph)<40:counts['blocksRejectedShort']+=1;continue
  if len(paragraph)>20000:counts['blocksRejectedOversized']+=1;continue
  japanese=sum(bool(re.match(r'[ぁ-ゖァ-ヺ一-鿿]',c))for c in paragraph)
  if japanese/len(paragraph)<.30:counts['blocksRejectedLowJapaneseRatio']+=1;continue
  if any(marker in paragraph for marker in ['{{','}}','[[',']]','{|','|}','http://','https://','\\begin','<','>']):counts['blocksRejectedResidualMarkupOrUrl']+=1;continue
  paragraphs.append(paragraph)
 counts['retainedParagraphs']=len(paragraphs)
 return paragraphs,counts

def build(a):
 started=time.monotonic();m=json.loads(a.manifest.read_text());source=pathlib.Path(m['path'])
 if sha_file(source)!=m['sha256']or source.stat().st_size!=m['bytes']:raise ValueError('Raw official dump changed')
 a.output.mkdir(parents=True,exist_ok=False);stats=collections.Counter();newer=collections.Counter();old=collections.Counter();bookfamilies=set();doc_count=0
 raw_path=a.output/'raw-pages.jsonl.gz';derived_path=a.output/'derived-pages.jsonl.gz'
 with gzip.GzipFile(filename=str(raw_path),mode='wb',mtime=0)as rawout,gzip.GzipFile(filename=str(derived_path),mode='wb',mtime=0)as derivedout,bz2.open(source,'rb')as xml:
  iterator=ET.iterparse(xml,events=('start','end'));_,root=next(iterator)
  for event,page in iterator:
   if event!='end'or page.tag.rsplit('}',1)[-1]!='page':continue
   ns=page.tag.split('}')[0]+'}'if'}'in page.tag else''
   def field(element,name):
    q=element.find(ns+name);return q.text if q is not None and q.text is not None else''
   stats['allPages']+=1
   if field(page,'ns')!='0':stats['excludedNamespace']+=1;page.clear();root.clear();continue
   title=field(page,'title');revision=page.find(ns+'revision')
   if revision is None:stats['excludedMissingRevision']+=1;page.clear();root.clear();continue
   text=field(revision,'text');revision_id=field(revision,'id');timestamp=field(revision,'timestamp');contributor=revision.find(ns+'contributor')
   username=field(contributor,'username')if contributor is not None else''
   contributor_id=field(contributor,'id')if contributor is not None else''
   raw=dict(source=m['source'],dumpRevision=m['revision'],title=title,pageId=field(page,'id'),revisionId=revision_id,
    timestamp=timestamp,lastContributorUsername=username,lastContributorId=contributor_id,text=text,rawWikitextSha256=sha_bytes(text.encode()),
    sourceXmlSha256=m['sha256'],license=m['license'],humanStatus=m['humanStatus'])
   rawout.write((json.dumps(raw,ensure_ascii=False,separators=(',',':'))+'\n').encode());stats['namespace0Pages']+=1;stats['rawWikitextCharacters']+=len(text)
   if 'bot'in username.lower():stats['lastContributorNameContainsBotHeuristic']+=1
   if page.find(ns+'redirect')is not None or re.match(r'^\s*#(?:redirect|転送)',text,re.I):stats['excludedRedirects']+=1;page.clear();root.clear();continue
   paragraphs,removed=prose(text);stats.update(removed)
   if not paragraphs:stats['pagesWithNoRetainedProse']+=1;page.clear();root.clear();continue
   family_title=norm(title.split('/',1)[0])if m['source']=='jawikibooks'else norm(title)
   family=m['source']+'|'+family_title
   # A book family may contain many chapter documents. The pipeline explicitly
   # joins them before split; generic record ID remains the actual page ID.
   doc=dict(id=m['source']+':'+raw['pageId'],source=m['source'],title=norm(title),family=family,
    url='https://'+('ja.wikibooks.org'if m['source']=='jawikibooks'else'ja.wikivoyage.org')+'/w/index.php?oldid='+revision_id,
    historyUrl='https://'+('ja.wikibooks.org'if m['source']=='jawikibooks'else'ja.wikivoyage.org')+'/w/index.php?title='+__import__('urllib.parse',fromlist=['quote']).quote(title)+'&action=history',
    revision=revision_id,dumpRevision=m['revision'],timestamp=timestamp,license=m['license'],licenseUrl=m['licenseUrl'],
    humanStatus=m['humanStatus'],admission='candidate-not-admitted',derivedSourceText=True,
    rawWikitextSha256=raw['rawWikitextSha256'],sourceXmlSha256=m['sha256'],lastContributorUsername=username,lastContributorId=contributor_id,
    latestRevisionBefore2022=bool(timestamp and timestamp<'2022-01-01T00:00:00Z'),
    pre2022IsNotHumanAuthorshipProof=True,geographicSemanticFamilyUnresolved=m['source']=='jawikivoyage',
    extraction='mwparserfromhell0.7.2; templates/code/math/table/media blocks rejected; refs removed; lists filtered; strip_code, no paraphrase',
    extractionCounts=dict(removed),paragraphs=[dict(ordinal=i,text=t,rawDocumentDerived=True)for i,t in enumerate(paragraphs)])
   derivedout.write((json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n').encode());doc_count+=1;bookfamilies.add(family)
   group=old if doc['latestRevisionBefore2022']else newer;group['documents']+=1;group['paragraphs']+=len(paragraphs);group['characters']+=sum(map(len,paragraphs))
   page.clear();root.clear()
 wheel=next(pathlib.Path('/dev/shm/foundation-parser-wheel').glob('*.whl'))
 result=dict(status='derived-candidate-NOT-admitted',source=m['source'],sourceManifestSha256=sha_file(a.manifest),rawXmlSha256=m['sha256'],
  adapterSha256=sha_file(__file__),parser=dict(name='mwparserfromhell',version=mwparserfromhell.__version__,license='MIT',wheel=wheel.name,wheelSha256=sha_file(wheel),installation='/dev/shm/foundation-parser only; no global environment changes'),
  stats=dict(stats),derivedDocuments=doc_count,documentFamilies=len(bookfamilies),pre2022LatestRevisionSubset=dict(old),laterOrUnknownSubset=dict(newer),
  humanOnlyCertified=False,pre2022DoesNotProveHumanOnly=True,sourceRawUntouched=True,optimizerUpdates=0,modelObjectsCreated=0,
  elapsedSeconds=time.monotonic()-started,files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha_file(p))for p in [raw_path,derived_path]])
 write(a.output/'receipt.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);build(p.parse_args())
