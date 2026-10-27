"""Further candidate-only provenance subsets and source-balanced zero-update PF inputs."""
import argparse,collections,gzip,hashlib,json,pathlib,re,sys
from build import BASE,Encoder,distribution,sha_file,sha_bytes,write
HERE=pathlib.Path(__file__).resolve().parent
def genre(title):
 for label,pattern in [('daily-life-travel',r'料理|調理|健康|家事|旅行|観光|飲食|生活|育児'),('programming-computing',r'Python|Java|C\+\+|C言語|プログラ|コンピュータ|情報|Linux|HTML|Ruby|Perl|ソフトウェア|ネットワーク'),('mathematics',r'数学|算数|幾何|代数|解析|微分|積分|確率'),('natural-science',r'化学|物理|生物|科学|地学|医学|電気'),('language-learning',r'英語|日本語|ドイツ語|フランス語|中国語|言語'),('humanities-social',r'歴史|地理|政治|経済|法律|法学|社会|哲学|文学')]:
  if re.search(pattern,title,re.I):return label
 return 'other-or-unclassified'
def run(a):
 receipt=json.loads((a.input/'receipt.json').read_text());docs_path=a.input/'documents.jsonl.gz'
 expected=next(x for x in receipt['files']if pathlib.Path(x['path']).name==docs_path.name)
 if sha_file(docs_path)!=expected['sha256']:raise ValueError('Final candidate archive changed')
 stats=collections.defaultdict(lambda:collections.Counter());lengths=collections.defaultdict(list);by_source=collections.defaultdict(lambda:collections.Counter());genres=collections.defaultdict(lambda:collections.Counter());candidates=collections.defaultdict(list);samples=collections.defaultdict(list)
 with gzip.open(docs_path,'rt')as f:
  for line in f:
   d=json.loads(line);ps=[p for p in d['paragraphs']if p['keepForCandidateTraining']];tokens=sum(p['ownBpeTokens']for p in ps);chars=sum(len(p['normalizedText'])for p in ps);groups=['all-candidate']
   if d.get('latestRevisionBefore2022'):
    groups.append('wiki-latest-revision-before2022')
    if 'bot'not in d.get('lastContributorUsername','').lower():groups.append('wiki-latest-before2022-and-last-name-not-bot')
   for group in groups:
    key=group+'|'+d['split'];stats[key].update(documents=1,nonemptyDocuments=bool(ps),paragraphs=len(ps),characters=chars,tokens=tokens)
   key=d['source']+'|'+d['split'];by_source[key].update(documents=1,paragraphs=len(ps),characters=chars,tokens=tokens);lengths[key].extend(p['ownBpeTokens']for p in ps)
   if d['split']=='train':
    label=genre(d['family'])
    if d.get('familyCanonicalization'):label='law-text-commentary-section'
    if d['source']=='jawikivoyage':label='travel-geography'
    genres[label].update(documents=1,paragraphs=len(ps),tokens=tokens)
    if tokens>=255:
     rank=sha_bytes(('foundation-native-pf-v1|'+d['id']).encode());candidates[d['source']].append((rank,d))
    for p in ps:
     rank=sha_bytes(('foundation-quality-train-v1|'+d['id']+'|'+str(p['ordinal'])).encode());samples[d['source']].append((rank,d,p))
 # Source-balanced PF is a diagnostic selection, never a training sampler.
 tok=json.loads((BASE/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']];pf=[];quality=[]
 for source,n in [('jaquad',6),('jawikibooks',6),('jawikivoyage',4)]:
  selected=0
  for rank,d in sorted(candidates[source],key=lambda x:x[0]):
   ps=[p for p in d['paragraphs']if p['keepForCandidateTraining']];text='\n\n'.join(p['normalizedText']for p in ps);body=enc(text);stream=[1]+body+[2]
   if len(stream)<257:continue
   if b''.join(pieces[t]for t in body)!=text.encode():raise AssertionError('Native stream byte roundtrip failed')
   rawsha=d.get('rawWikitextSha256')or sha_bytes(json.dumps([p['text']for p in d['paragraphs']],ensure_ascii=False,separators=(',',':')).encode())
   pf.append(dict(id='native-'+source+'-'+str(selected).zfill(2),documentId=d['id'],family=d['family'],component=d['component'],partition='train',source=source,sourceSha256=rawsha,
    sourceSha256Meaning='Original raw wikitext SHA'if d.get('rawWikitextSha256')else'Canonical JSON list of verbatim original paragraph texts SHA; original shard hashes in corpus receipt',
    sourceUrl=d['url'],license=d['license'],humanStatus=d['humanStatus'],admission=d['admission'],format='native-prose-bos-body-eos',
    documentTokenOffset=0,documentTokenCount=len(stream),tokens=stream[:257],sourceBalancedSelectionRank=rank,
    ordinaryDocumentTextJoin='Two LF characters between retained normalized source paragraphs',eosPolicy='EOS2 only at actual derived whole-document end; no paragraph/window EOS inserted'))
   selected+=1
   if selected==n:break
  if selected!=n:raise ValueError('Insufficient eligible source-balanced TRAIN PF documents')
  for rank,d,p in sorted(samples[source],key=lambda x:x[0])[:20]:
   quality.append(dict(source=source,documentId=d['id'],title=d['title'],family=d['family'],split='train',paragraphOrdinal=p['ordinal'],text=p['normalizedText'],sourceUrl=d['url'],license=d['license'],humanStatus=d['humanStatus'],derivedSourceText=d.get('derivedSourceText',False),rank=rank,admitted=False))
 a.output.mkdir(parents=True,exist_ok=True)
 write(a.output/'subsets.json',dict(allCandidateUnadmitted=True,pre2022OrNoBotNameIsNotHumanAuthorshipProof=True,
  latestRevisionDoesNotDescribeAllHistoricalAuthors=True,groupStats=dict(stats),sourceSplitStats={k:dict(v,paragraphTokens=distribution(lengths[k]))for k,v in by_source.items()},
  trainGenreHeuristic=dict(genres),genrePolicy='First matching title/book-family keyword only; voyage travel label; not human quality validation or topic-family independence proof',
  tokenizerSha256=sha_file(BASE/'data/tokenizer.json'),corpusArchiveSha256=expected['sha256'],optimizerUpdates=0))
 write(a.output/'native-train-candidates.json',dict(scope='Source-balanced audit-only inputs; NOT training admission or mixture',selection='Per source SHA256(foundation-native-pf-v1|documentID) ascending; 6JaQuAD+6Wikibooks+4Wikivoyage docunique TRAIN',tokenizerSha256=sha_file(BASE/'data/tokenizer.json'),finalSplitManifestSha256=sha_file(a.input/'article-splits.json'),modelObjectsCreated=0,optimizerUpdates=0,windows=pf))
 write(a.output/'quality-train-sample.json',dict(scope='Unadmitted source quality review;20SHAselected TRAIN paragraphs/source; no model predictions',rows=quality))
 print(json.dumps(dict(passed=True,pfWindows=len(pf),qualityParagraphs=len(quality),optimizerUpdates=0,groupStats=dict(stats)),ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);run(p.parse_args())
