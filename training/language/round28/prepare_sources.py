"""Apply pre-frozen corpus hygiene. TEST raw hashing only; no tokenizer/model imports."""
import collections,hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parent;B=R.parent;CACHE=pathlib.Path('/workspace/daily-conversation-source-audit');OUT=R/'sources'
read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
policy=read(R/'source-policy.json');assert policy['modelTrainingUpdatesAtPolicyFreeze']==0
meta=read(CACHE/'human-source-acquisition.json');foldraw=(CACHE/'prospective-speaker-folds.json').read_bytes();assert sha(foldraw)==policy['fixedSpeakerFoldSha256'];folds=json.loads(foldraw)['speakerFolds'];assert meta['sourceCommit']==policy['sourceCommit']
protected=set();protected_documents=0;protected_chars=0
# Entire original corpora block exact recycling as well as held-out contamination.
def grams(text):
 for i in range(max(0,len(text)-63)):yield hashlib.sha256(text[i:i+64].encode()).digest()[:16]
def protect(text):
 global protected_documents,protected_chars
 protected.update(grams(text));protected_documents+=1;protected_chars+=len(text)
for row in read(B/'round10/units.json'):protect(row['text'])
for line in (B/'round22/sources/source-documents.jsonl').read_text().splitlines():protect(json.loads(line)['text'])
held_canonical=set();held_rows=[]
for row in meta['records']:
 if row['fold'] not in ['development','reserved-test']:continue
 raw=(CACHE/'human-only-raw'/row['fold']/pathlib.PurePosixPath(row['sourcePath']).name).read_bytes();assert sha(raw)==row['sha256'];d=json.loads(raw);assert all(folds[s]==row['fold'] for s in d['interlocutors']);text='\n'.join(u['text'] for u in d['utterances']);protect(text)
 seq=[[d['interlocutors'].index(u['interlocutor_id']),u['text']] for u in d['utterances']];held_canonical.add(sha(json.dumps(seq,ensure_ascii=False,separators=(',',':')).encode()));held_rows.append(dict(sourcePath=row['sourcePath'],fold=row['fold'],sourceSha256=row['sha256']))
print('Protected source index built:',protected_documents,'documents;',len(protected),'hashed64-character substrings',flush=True)
seen=set();admitted=[];rejected=[];reasoncounts=collections.Counter();speakers=set();utterances=0
for row in sorted(meta['records'],key=lambda x:x['sourcePath']):
 if row['fold']!='train':continue
 raw=(CACHE/'human-only-raw/train'/pathlib.PurePosixPath(row['sourcePath']).name).read_bytes();assert sha(raw)==row['sha256'];d=json.loads(raw);assert all(folds[s]=='train' for s in d['interlocutors']);texts=[u['text'] for u in d['utterances']];assert all(u['interlocutor_id'] in d['interlocutors'] for u in d['utterances']);text='\n'.join(texts);seq=[[d['interlocutors'].index(u['interlocutor_id']),u['text']] for u in d['utterances']];h=sha(json.dumps(seq,ensure_ascii=False,separators=(',',':')).encode());reasons=[]
 if any(not t.strip() or any(ord(c)<32 and c not in '\n\t\r' for c in t) for t in texts):reasons.append('empty-or-control')
 if any('＊＊' in t for t in texts):reasons.append('original-redaction-mask')
 if h in seen:reasons.append('exact-train-dialogue-duplicate')
 seen.add(h)
 if h in held_canonical:reasons.append('exact-human-held-dialogue')
 if any(g in protected for g in grams(text)):reasons.append('protected64-character-overlap')
 if reasons:
  reasoncounts.update(reasons);rejected.append(dict(sourcePath=row['sourcePath'],sourceSha256=row['sha256'],reasons=reasons));continue
 key='realpersona:'+pathlib.PurePosixPath(row['sourcePath']).stem;url='https://github.com/'+meta['sourceRepository']+'/blob/'+meta['sourceCommit']+'/'+row['sourcePath'];speakers.update(d['interlocutors']);utterances+=len(texts)
 admitted.append(dict(id=key,originalDocument=key,unitKey=key+':dialogue',site='human-chat',partition='train',sourcePath=row['sourcePath'],dialogueIdMetadata=d['dialogue_id'],url=url,sourceSha256=row['sha256'],gitBlobSha1=row['gitBlobSha1'],text=text,textSha256=sha(text.encode()),startLine=1,endLine=text.count('\n')+1,utteranceCount=len(texts),canonicalSpeakerTurnHash=h,license='CC-BY-SA-4.0',licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/',attribution=meta['attribution'],processing=policy['serialization']))
assert len(admitted)+len(rejected)==meta['dialogueCounts']['train'];OUT.mkdir(exist_ok=True);docs=OUT/'documents.jsonl';docs.write_text(''.join(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n' for d in admitted));shutil.copyfile(CACHE/'real-persona-chat-LICENSE',OUT/'LICENSE');write(OUT/'rejected-train.json',rejected)
report=dict(sourceRepository=meta['sourceRepository'],sourceCommit=meta['sourceCommit'],license='CC-BY-SA-4.0',attribution=meta['attribution'],sourcePolicySha256=sha((R/'source-policy.json').read_bytes()),sourceAcquisitionManifestSha256=sha((CACHE/'human-source-acquisition.json').read_bytes()),foldPolicySha256=sha(foldraw),sourcePreparationCodeSha256=sha(pathlib.Path(__file__).read_bytes()),sourceGitPinned=True,originalTrainFiles=meta['dialogueCounts']['train'],admittedUnits=len(admitted),admittedCharacters=sum(len(d['text']) for d in admitted),admittedUtf8Bytes=sum(len(d['text'].encode()) for d in admitted),admittedUtterances=utterances,observedTrainSpeakers=len(speakers),excludedTrainFiles=len(rejected),rejectionReasonCounts=dict(reasoncounts),documentsSha256=sha(docs.read_bytes()),protectedDocuments=protected_documents,protectedCharacters=protected_chars,protectedHash64Count=len(protected),protectedSources=[dict(path='../round10/units.json',sha256=sha((B/'round10/units.json').read_bytes())),dict(path='../round22/sources/source-documents.jsonl',sha256=sha((B/'round22/sources/source-documents.jsonl').read_bytes()))],humanHeldHashOnlySources=held_rows,reservedTestParsedForSourceHygieneHashesOnly=True,reservedTestTokenizedOrModelEvaluated=False,reservedTestSemanticReading=False,protectedOverlapCharacters=64,protectedHashBits=128,noShortOrApproximateOverlapGuarantee=True,sourceUtteranceTextRewritten=False,onlyNewlineTurnSeparatorsInserted=True,noLlmLogsOrPersonaProfilesUsed=True,modelOrTokenizerExecuted=False,modelTrainingUpdates=0)
write(OUT/'manifest.json',report);print(json.dumps({k:v for k,v in report.items() if k!='humanHeldHashOnlySources'}),flush=True)
