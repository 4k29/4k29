import json,pathlib,hashlib,collections,statistics,re,unicodedata
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=ROOT/'training/language/conversation-v2';R=ROOT/'training/language/round46'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ''.join(unicodedata.normalize('NFKC',s).split())
def quant(xs):
 xs=sorted(xs);return {'count':len(xs),'min':xs[0],'p25':xs[int((len(xs)-1)*.25)],'median':statistics.median(xs),'p75':xs[int((len(xs)-1)*.75)],'p95':xs[int((len(xs)-1)*.95)],'p99':xs[int((len(xs)-1)*.99)],'max':xs[-1],'mean':statistics.mean(xs)}
docs={};duplicates=0;inputs=[]
for n in ['sources/documents.jsonl','added-human-source/documents.jsonl']:
 p=R/n;inputs.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
 for line in p.open():
  d=json.loads(line);assert d['partition']=='train'and d['license']=='CC-BY-SA-4.0'
  key=d['originalDocument']
  if key in docs: assert docs[key]['textSha256']==d['textSha256'];duplicates+=1
  else:docs[key]=d
jm=pathlib.Path('/workspace/next-source-candidate-jmrd/upstream-train.json');rawjm={d['dialog_id']:d for d in json.load(jm.open())};inputs.append({'path':str(jm),'sha256':sha(jm)})
res={};families=collections.Counter(norm(d['text'])for d in docs.values());rawhashes=[]
for source in ['realpersona','jmrd']:
 ds=[d for k,d in docs.items()if k.startswith(source+':')];turns=[];starts=[];speakers=set();movies=collections.Counter();empty=0
 for d in ds:
  id=d['originalDocument'].split(':')[1]
  if source=='realpersona':
   p=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')/(id+'.json');raw=json.load(p.open());h=sha(p);assert h==d['sourceSha256'];rawhashes.append((str(p),h));speakers.update(raw['interlocutors']);us=raw['utterances'];assert '\n'.join(x['text']for x in us)==d['text'];assert all(us[j]['interlocutor_id']!=us[j-1]['interlocutor_id']for j in range(1,len(us)));turns.extend(x['text']for x in us);starts.extend(x['text']for x in us[:2])
  else:
   raw=rawjm[id];movies[norm(raw['movie_title'])]+=1;us=raw['dialog'];assert '\n'.join(x['text']for x in us)==d['text'];turns.extend(x['text']for x in us);starts.extend(x['text']for x in us[:2])
 counts=collections.Counter(turns);ncounts=collections.Counter(norm(s)for s in turns)
 greeting=lambda s: bool(re.search(r'こんにちは|こんばんは|おはよう|よろしく|初めまして|はじめまして',s))
 tails=collections.Counter()
 for s in turns:
  if re.search(r'[、,]$',s):tails['trailing_comma']+=1
  if re.search(r'(て|けど|ですが|けれど|ので|のに|なら|とは|たり|し)$',s):tails['conjunctive_or_fragment_surface']+=1
  if re.search(r'[。！？!?」』）)ー〜～…♪笑w]$',s):tails['punctuation_or_colloquial_ending']+=1
 res[source]={'documents':len(ds),'utterances':len(turns),'characters':sum(map(len,turns)),'utf8Bytes':sum(len(s.encode())for s in turns),'documentTurns':quant([d['utteranceCount']for d in ds]),'utteranceCharacters':quant(list(map(len,turns))),'shortAtMost8Characters':sum(len(s)<=8 for s in turns),'exactUniqueUtterances':len(counts),'exactDuplicateOccurrenceBeyondFirst':sum(c-1 for c in counts.values()),'normalizedUniqueUtterances':len(ncounts),'greetingSurfaceOccurrences':sum(greeting(s)for s in turns),'greetingAmongFirstTwoTurns':sum(greeting(s)for s in starts),'firstTwoTurnCount':len(starts),'tailSurfaceProxies':dict(tails),'uniqueDeclaredSpeakerIds':len(speakers)if source=='realpersona'else None,'speakerIdentityLimitation':None if source=='realpersona'else 'recommender/seeker are public roles, not persistent person identities','uniqueNormalizedMovieTitleFamilies':len(movies)if movies else None,'largestMovieTitleFamily':max(movies.values())if movies else None,'top20ExactUtterances':counts.most_common(20),'sourceDomain':'general daily chat with persona'if source=='realpersona'else'movie recommendation and discussion; domain-limited'}
report={'schemaVersion':1,'scope':'Existing admitted human TRAIN only; no development or reserved TEST content opened','sourceDocumentsRows':18125,'uniqueDocuments':len(docs),'duplicateDocumentRowsBeyondFirst':duplicates,'normalizedWholeDocumentDuplicateFamilies':sum(n>1 for n in families.values()),'sources':res,'sourceReceipts':inputs,'originalRealPersonaTrainReceiptsCount':len(rawhashes),'originalRealPersonaTrainReceiptsDigest':hashlib.sha256(json.dumps(sorted(rawhashes),separators=(',',':')).encode()).hexdigest(),'license':'CC-BY-SA-4.0; per-document attribution and pinned commit URLs retained','limitations':['Surface greeting, shortness and ending proxies are not semantic quality labels; do not auto-remove colloquial speech','Embedded newlines exist within original utterances; do not recover turn boundaries by text.split(newline)', 'Original human turns can be unfinished or factually wrong; original target match is not semantic success','No explicit reply-to annotation: adjacency+other speaker does not guarantee semantic appropriateness','Never add knowledge/review/questionnaire fields from JMRD to human gold','Old TRAIN holdout is fresh for new scratch series only; not unseen for R46','Training pool already includes JMRD duplicate index rows across two source files; deduplicate by originalDocument before any sampling'],'recommendations':['Use RP-dominant daily conversation; report JMRD separately and avoid movie facts dominating','Preserve utterance ordinal/speaker identity in metadata; learn utterance-end EOS, not document-only EOS','Avoid treating greeting/single-token rate reductions alone as language success','Hash-fixed document+speaker holdout for RP and normalized movie-title family holdout for JMRD before tokenizer/statistics fitting','BPE fit on new-series TRAIN only; using old BPE contaminates new scratch holdout tokenizer exposure and must be called an exposed tokenizer diagnostic'],'modelInstantiated':False,'optimizerUpdates':0,'sealedTestRead':False}
index=json.load((R/'multiview/train.index.json').open());policy=json.load((R/'policy.json').open());inventory={}
for site in sorted({d['site']for d in index['documents']}):
 ds=[d for d in index['documents']if d['site']==site and d['variant']==0]
 inventory[site]={'canonicalUnits':len(ds),'uniqueOriginalDocuments':len({d['sourceDocument']for d in ds}),'canonicalTokens':sum(d['length']for d in ds)}
report['existingRound46GenreSampling']=policy['genreSampling'];report['existingRound46CanonicalTrainingInventory']=inventory;report['existingRound46InventoryLimitation']='Canonical units can be chains from the same original source; do not call unit count unique document count.'
(OUT/'data-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'sources':{s:{k:v for k,v in x.items()if k not in ['top20ExactUtterances']}for s,x in res.items()},'uniqueDocuments':len(docs),'duplicateRows':duplicates},ensure_ascii=False,indent=2))
