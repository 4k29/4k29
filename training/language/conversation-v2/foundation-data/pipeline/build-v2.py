"""Candidate-only human-source corpus: provenance, dedup families, split and own-BPE audit.

No optimizer/model objects, pretrained tokenizer, rewritten answer or TEST fetch.
Raw paragraphs/QAs remain verbatim; NFC/line endings are separate derived text.
"""
import argparse,collections,gzip,hashlib,itertools,json,pathlib,re,resource,sys,time,unicodedata,zlib

HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parents[1]
REPO=BASE.parents[2]
sys.path.insert(0,str(BASE))
from new_tokenizer import Encoder

SPLIT_SALT='foundation-data-split-v1|'
def sha_bytes(x):return hashlib.sha256(x).hexdigest()
def sha_file(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def norm(s):return unicodedata.normalize('NFC',s.replace('\r\n','\n').replace('\r','\n'))
def canonical(s):return ''.join(norm(s).split())
def book_family(title):
 root=norm(title.split('/',1)[0])
 law=re.match(r'^(.+?法)第[0-9０-９一二三四五六七八九十百千万]+条',root)
 return law.group(1)if law else root
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
class Union:
 def __init__(self,keys):self.parent={x:x for x in keys}
 def find(self,x):
  while self.parent[x]!=x:self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
  return x
 def join(self,a,b):
  a=self.find(a);b=self.find(b)
  if a!=b:self.parent[max(a,b)]=min(a,b)
def split(family):
 bucket=int(sha_bytes((SPLIT_SALT+family).encode()),16)%100
 return 'dev'if bucket<10 else'reserve'if bucket<15 else'train'
def shingles(s,n=5):return {s[i:i+n]for i in range(max(0,len(s)-n+1))}
def near_pairs(texts,posting_cap=200):
 """Candidate retrieval via16 smallest CRC32 shingles; exact Jaccard verification.

 Not exhaustive semantic dedup. Frequent fingerprint buckets are skipped and
 reported rather than silently implying all near duplicates were ruled out.
 """
 index=collections.defaultdict(list);skipped=0;comparisons=0;matches=[]
 for i,text in enumerate(texts):
  if len(text)<80:continue
  ss=shingles(text)
  fingerprints=sorted({zlib.crc32(s.encode())for s in ss})[:16]
  candidates=collections.Counter()
  for key in fingerprints:
   posting=index[key]
   if len(posting)>posting_cap:skipped+=1;continue
   candidates.update(posting)
  for j,shared in candidates.items():
   if shared<2 or min(len(text),len(texts[j]))/max(len(text),len(texts[j]))<.8:continue
   comparisons+=1;other=shingles(texts[j]);score=len(ss&other)/len(ss|other)
   if score>=.85:matches.append((j,i,score))
  for key in fingerprints:index[key].append(i)
 return matches,dict(method='16-smallest CRC32 character5gram candidate retrieval; >=2 shared; lengthratio>=0.8; exactJaccard>=0.85',
  comparisons=comparisons,matchedPairs=len(matches),skippedFrequentPostings=skipped,
  exhaustiveNearOrSemanticDedup=False,postingCap=posting_cap)
def distribution(values):
 s=sorted(values)
 def q(p):return s[round((len(s)-1)*p)]if s else None
 return dict(n=len(s),min=s[0]if s else None,p50=q(.5),p90=q(.9),p99=q(.99),max=s[-1]if s else None,
  exceed={str(n):sum(x>n for x in s)for n in [256,512,1024]})
def ingest_jaquad(manifest):
 m=json.loads(manifest.read_text());articles={};receipts=[];qids={};duplicate_qids=[]
 for shard in m['shards']:
  path=pathlib.Path(shard['rawPath'])
  if sha_file(path)!=shard['sha256']or path.stat().st_size!=shard['bytes']:raise ValueError('Raw source changed')
  raw=json.loads(path.read_text());receipts.append({k:shard[k]for k in ['part','url','bytes','sha256']})
  for ai,article in enumerate(raw['data']):
   title=norm(article['title']);family='jaquad|'+title
   doc=articles.setdefault(family,dict(id='jaquad:'+sha_bytes(title.encode())[:24],source='jaquad',title=title,family=family,
    url='https://ja.wikipedia.org/wiki/'+__import__('urllib.parse',fromlist=['quote']).quote(title),
    revision=m['revision'],license='CC-BY-SA-3.0',humanStatus='Human-annotated QA declared by dataset authors; Wikipedia context authorship human/bot unverified',
    admission='candidate-not-admitted',paragraphs=[]))
   for pi,p in enumerate(article['paragraphs']):
    text=p['context'];derived=norm(text)
    for q in p['qas']:
     if q['id']in qids:duplicate_qids.append(q['id'])
     qids[q['id']]=family
     for a in q['answers']:
      if text[a['answer_start']:a['answer_start']+len(a['text'])]!=a['text']:raise ValueError('Original QA offset mismatch')
    doc['paragraphs'].append(dict(ordinal=len(doc['paragraphs']),sourcePart=shard['part'],sourceArticleOrdinal=ai,sourceParagraphOrdinal=pi,
     text=text,normalizedText=derived,normalizationChanged=text!=derived,rawTextSha256=sha_bytes(text.encode()),
     normalizedSha256=sha_bytes(derived.encode()),canonicalSha256=sha_bytes(canonical(text).encode()),qas=p['qas']))
 if duplicate_qids:raise ValueError('Duplicate original QA IDs: '+str(duplicate_qids[:10]))
 return list(articles.values()),receipts,m
def locked_rp():
 result=collections.defaultdict(set);count=0
 for partition in ['train','dev']:
  with (BASE/'data'/f'{partition}.docs.jsonl').open()as f:
   for line in f:
    d=json.loads(line)
    for u in d['utterances']:result[sha_bytes(canonical(u['text']).encode())].add(partition);count+=1
 return result,count
def build(a):
 started=time.monotonic();a.output.mkdir(parents=True,exist_ok=False)
 docs,receipts,manifest=ingest_jaquad(a.manifest);docs.sort(key=lambda d:d['family'])
 if a.generic:
  for path in a.generic:
   with gzip.open(path,'rt')if str(path).endswith('.gz')else path.open()as f:
    for line in f:
     d=json.loads(line)
     if d['source']=='jawikibooks':
      original=d['family'];d['family']='jawikibooks|'+book_family(d['title'])
      if original!=d['family']:d['sourceFamilyBeforeCanonicalization']=original;d['familyCanonicalization']='Clear law-name+article-number chapter grouped to whole law book; no text change'
     for i,p in enumerate(d['paragraphs']):
      t=p['text'];p.update(ordinal=i,normalizedText=norm(t),normalizationChanged=t!=norm(t),rawTextSha256=sha_bytes(t.encode()),normalizedSha256=sha_bytes(norm(t).encode()),canonicalSha256=sha_bytes(canonical(t).encode()))
     docs.append(d)
 families=[d['family']for d in docs]
 if len({d['id']for d in docs})!=len(docs):raise ValueError('Duplicate document ID')
 union=Union(families);paragraphs=[(d,p)for d in docs for p in d['paragraphs']]
 raw_seen={};canonical_seen={};exact=[];normalized=[]
 for i,(d,p)in enumerate(paragraphs):
  p['keepForCandidateTraining']=True
  if p['rawTextSha256']in raw_seen:
   j=raw_seen[p['rawTextSha256']];exact.append(dict(first=j,duplicate=i));union.join(d['family'],paragraphs[j][0]['family']);p['keepForCandidateTraining']=False;p['duplicateOfParagraph']=j
  else:raw_seen[p['rawTextSha256']]=i
  if p['canonicalSha256']in canonical_seen:
   j=canonical_seen[p['canonicalSha256']];union.join(d['family'],paragraphs[j][0]['family'])
   if p['keepForCandidateTraining']:normalized.append(dict(first=j,duplicate=i));p['keepForCandidateTraining']=False;p['duplicateOfParagraph']=j
  else:canonical_seen[p['canonicalSha256']]=i
 near,near_receipt=near_pairs([canonical(p['text'])for _,p in paragraphs])
 near_removed=0
 for j,i,score in near:
  union.join(paragraphs[j][0]['family'],paragraphs[i][0]['family'])
  p=paragraphs[i][1]
  if p['keepForCandidateTraining']:
   p.update(keepForCandidateTraining=False,nearDuplicateOfParagraph=j,nearJaccard=score);near_removed+=1
 locked,locked_count=locked_rp();overlap=[];component_locked=collections.defaultdict(set)
 for i,(d,p)in enumerate(paragraphs):
  hit=locked.get(p['canonicalSha256'])
  if hit:component_locked[union.find(d['family'])].update(hit);overlap.append(dict(paragraph=i,family=d['family'],existingRpSplits=sorted(hit)))
 prior_path=BASE/'epoch1/jaquad-candidate/sample.json';prior={norm(r['articleTitle'])for r in json.loads(prior_path.read_text())['rows']}
 splits=[]
 for d in docs:
  component=union.find(d['family']);hits=component_locked.get(component,set())
  part='quarantine'if'dev'in hits else'train'if'train'in hits else split(component)
  d.update(component=component,split=part,priorCandidateViewed=d['source']=='jaquad'and d['title']in prior)
  splits.append({k:d[k]for k in ['id','source','title','family','component','split','priorCandidateViewed']})
 write(a.output/'article-splits.json',dict(rule='SHA256(foundation-data-split-v1|component-family) mod100 <10dev,10..14reserve,elseTRAIN; component min-family after dedup union; existingRPDEV overlap quarantine, RPTRAIN overlap TRAIN',
  reserveIsSealedTest=False,articlePayloadVisibleToPipeline=True,articles=splits))
 tokenizer=json.loads((BASE/'data/tokenizer.json').read_text());enc=Encoder(tokenizer);pieces=[bytes.fromhex(v)for v in tokenizer['bytes']]
 stats={};all_unknown=collections.Counter();by_source={}
 for part in ['train','dev','reserve','quarantine']:
  group=[d for d in docs if d['split']==part];tokens=chars=raw_chars=unknown_occ=fallback_bytes=fallback_tokens=0;lengths=[];doc_lengths=[];normalized_changed=0
  for d in group:
   total=0
   for p in d['paragraphs']:
    raw_chars+=len(p['text']);normalized_changed+=p['normalizationChanged']
    if not p['keepForCandidateTraining']:continue
    text=p['normalizedText'];ids=enc(text)
    if b''.join(pieces[t]for t in ids)!=text.encode():raise AssertionError('Own BPE byte roundtrip failed')
    p['ownBpeTokens']=len(ids);total+=len(ids);tokens+=len(ids);chars+=len(text);lengths.append(len(ids))
    for c in text:
     if c not in enc.glyphs:
      unknown_occ+=1;all_unknown[c]+=1;fallback_bytes+=len(c.encode());fallback_tokens+=len(enc.cache[c])
   doc_lengths.append(total)
  stats[part]=dict(documents=len(group),retainedParagraphs=len(lengths),rawCharacters=raw_chars,retainedNormalizedCharacters=chars,
   retainedOwnBpeBodyTokens=tokens,charactersPerToken=chars/tokens if tokens else None,tokensPerCharacter=tokens/chars if chars else None,
   unknownGlyphOccurrences=unknown_occ,unknownGlyphUtf8Bytes=fallback_bytes,unknownGlyphPreWordAssemblyTokens=fallback_tokens,
   normalizationChangedParagraphs=normalized_changed,paragraphTokenLengths=distribution(lengths),documentTokenLengths=distribution(doc_lengths),
   documentLengthPolicy='Sum per-paragraph encodings, no artificial separator tokens counted',byteExactRoundtrip=True)
 for source in sorted({d['source']for d in docs}):
  ds=[d for d in docs if d['source']==source];ps=[p for d in ds for p in d['paragraphs']];kept=[p for p in ps if p['keepForCandidateTraining']]
  by_source[source]=dict(documents=len(ds),rawParagraphs=len(ps),retainedParagraphs=len(kept),rawCharacters=sum(len(p['text'])for p in ps),
   retainedNormalizedCharacters=sum(len(p['normalizedText'])for p in kept),ownBpeTokens=sum(p['ownBpeTokens']for p in kept),
   splitDocuments=dict(collections.Counter(d['split']for d in ds)),admissionStatus=dict(collections.Counter(d['admission']for d in ds)))
 with gzip.GzipFile(filename=str(a.output/'documents.jsonl.gz'),mode='wb',mtime=0)as f:
  for d in docs:f.write((json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n').encode())
 # reserve payload is kept only inside the general candidate archive, never an
 # evaluation/test artifact. It was inspected by pipeline: no sealed TEST claim.
 dedup=dict(rawExactParagraphDuplicates=len(exact),whitespaceNfcDuplicatesBeyondRaw=len(normalized),near=near_receipt,
  rawExactPairs=exact,normalizedPairs=normalized,nearPairs=[dict(first=j,second=i,jaccard=s)for j,i,s in near],
  crossSourceExactOrNormalized=sum(paragraphs[x['first']][0]['source']!=paragraphs[x['duplicate']][0]['source']for x in exact+normalized),
  existingRpUtterancesCompared=locked_count,existingRpOverlaps=overlap,
  nearMatchesGroupedBeforeSplit=True,verifiedNearDuplicateParagraphsRemoved=near_removed,
  nearParagraphsRetainedAsDistinctText=False,
  topicOrSemanticFamilyDisjointnessProven=False)
 write(a.output/'dedup.json',dedup)
 files=[]
 for name in ['documents.jsonl.gz','article-splits.json','dedup.json']:
  p=a.output/name;files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha_file(p)))
 result=dict(status='candidate-corpus-built-NOT-admitted-NO-model-training',pipelineSha256=sha_file(__file__),
  sourceManifestSha256=sha_file(a.manifest),sourceRevision=manifest['revision'],sourceReceipts=receipts,
  tokenizerPath=str(BASE/'data/tokenizer.json'),tokenizerSha256=sha_file(BASE/'data/tokenizer.json'),vocabulary=len(tokenizer['bytes']),
  normalizedTextPolicy='NFC + CRLF/CR to LF; whitespace-only canonical hash for matching; raw text/QAs untouched; no NFKC/paraphrase',
  sourceStats=by_source,splitStats=stats,totalRawDocuments=len(docs),totalRawParagraphs=len(paragraphs),
  unknownGlyphTypes=len(all_unknown),unknownGlyphs=dict(all_unknown),dedupSummary={k:v for k,v in dedup.items()if k not in ['rawExactPairs','normalizedPairs','nearPairs','existingRpOverlaps']},
  testUsed=False,reserveIsSealedTest=False,optimizerUpdates=0,modelObjectsCreated=0,tokenizerFitted=False,
  admittedSources=[],elapsedSeconds=time.monotonic()-started,maximumRssKiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,files=files)
 write(a.output/'receipt.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['sourceReceipts','unknownGlyphs']},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--generic',type=pathlib.Path,action='append');build(p.parse_args())
