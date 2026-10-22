"""Hash-only prospective overlap audit; no model/tokenizer/heldout generation or admission."""
import pathlib,json,hashlib,datetime
R=pathlib.Path(__file__).resolve().parent;B=pathlib.Path('/workspace/4k29/training/language');CACHE=pathlib.Path('/workspace/daily-conversation-source-audit');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=R/'upstream-train.json';assert sha(raw)==read(R/'acquisition.json')['sha256'];data=read(raw);protected=set();records=[];documents=0;characters=0
def grams(t):
 for i in range(max(0,len(t)-63)):yield hashlib.sha256(t[i:i+64].encode()).digest()[:16]
def add(t):
 global documents,characters
 protected.update(grams(t));documents+=1;characters+=len(t)
for file in [B/'round10/units.json',B/'round22/sources/source-documents.jsonl',B/'round37/sources/documents.jsonl']:
 rows=read(file)if file.suffix=='.json'else(json.loads(s)for s in file.read_text().splitlines())
 for x in rows:add(x['text'])
 records.append(dict(path=str(file),sha256=sha(file)))
meta=read(CACHE/'human-source-acquisition.json');folds=read(CACHE/'prospective-speaker-folds.json')['speakerFolds'];held=[]
for x in meta['records']:
 if x['fold']not in ['development','reserved-test']:continue
 p=CACHE/'human-only-raw'/x['fold']/pathlib.PurePosixPath(x['sourcePath']).name;assert sha(p)==x['sha256'];d=read(p);assert all(folds[s]==x['fold']for s in d['interlocutors']);add('\n'.join(u['text']for u in d['utterances']));held.append(dict(sourcePath=x['sourcePath'],fold=x['fold'],sha256=x['sha256']))
print('Hash-only protected index built',documents,len(protected),flush=True)
rejected=[];clean=[];newseen=set()
for d in data:
 text='\n'.join(x['text']for x in d['dialog']);digest=hashlib.sha256(text.encode()).hexdigest();reasons=[]
 if d['dialog_id']=='03042':reasons.append('exposed-upstream-readme-sample')
 if digest in newseen:reasons.append('exact-candidate-train-text-duplicate')
 newseen.add(digest)
 if any(g in protected for g in grams(text)):reasons.append('existing-protected64-character-overlap')
 if reasons:rejected.append(dict(dialogueId=d['dialog_id'],textSha256=digest,reasons=reasons))
 else:clean.append(dict(dialogueId=d['dialog_id'],textSha256=digest,utterances=len(d['dialog']),characters=sum(len(x['text'])for x in d['dialog'])))
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rawTrainSha256=sha(raw),candidateDialogues=len(data),protectedDocuments=documents,protectedCharacters=characters,protectedHash64Count=len(protected),protectedSources=records,existingHumanHeldoutHashOnlySources=held,overlapCharacters=64,hashBits=128,rejectedCandidateDialogues=rejected,remainingCandidateCount=len(clean),remainingCandidateUtterances=sum(x['utterances']for x in clean),remainingCandidateCharacters=sum(x['characters']for x in clean),remainingCandidates=clean,notAdmittedToAnyTraining=True,currentRound37InputsUnmodified=True,noShortOrApproximateOverlapGuarantee=True,rawHeldoutUsedOnlyForHygieneHashes=True,heldoutSemanticallyRead=False,heldoutTokenizedOrModelEvaluated=False,upstreamJmrdValidAndTestNotAcquired=True,noGenerationOrOptimizer=True,codeSha256=sha(pathlib.Path(__file__)))
(R/'protected-overlap.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['existingHumanHeldoutHashOnlySources','remainingCandidates','rejectedCandidateDialogues']}),flush=True)
