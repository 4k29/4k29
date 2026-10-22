"""TRAIN-only source structure and quality counts; no admission, model, tokenizer or heldout."""
import pathlib,json,hashlib,collections,statistics
R=pathlib.Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(R/'acquisition.json');assert sha(R/'upstream-train.json')==m['sha256'];data=read(R/'upstream-train.json');ids=[];lengths=[];turns=[];titles=set();speakers=collections.Counter();bad=collections.Counter();duplicates=collections.Counter();readme_present=False
for d in data:
 ids.append(d['dialog_id']);titles.add(d['movie_title']);readme_present|=d['dialog_id']=='03042';rows=d['dialog'];turns.append(len(rows));seq=[];previous=None
 for i,u in enumerate(rows):
  assert isinstance(u['text'],str)and isinstance(u['speaker'],str)
  text=u['text'];s=u['speaker'];lengths.append(len(text));speakers[s]+=1;bad['emptyUtterances']+=int(not text.strip());bad['utterancesWithEmbeddedNewline']+=int('\n'in text);bad['unexpectedControlCharacters']+=int(any(ord(c)<32 and c not in '\n\t\r'for c in text));bad['adjacentSameSpeakerMessages']+=int(previous==s);bad['utteranceIdMismatch']+=int(u['utterance_id']!=f"{d['dialog_id']}_{i:02d}");previous=s;seq.append([s,text])
 duplicates[hashlib.sha256(json.dumps(seq,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()]+=1
assert len(ids)==len(set(ids))==4575
out=dict(scope='Prospective upstream TRAIN only; no training admission',sourceSha256=m['sha256'],dialogues=len(ids),utterances=len(lengths),characters=sum(lengths),meanCharactersPerUtterance=statistics.mean(lengths),medianCharactersPerUtterance=statistics.median(lengths),meanUtterancesPerDialogue=statistics.mean(turns),maxUtterancesPerDialogue=max(turns),distinctMovieTitleStrings=len(titles),roleCounts=dict(speakers),qualityCounts=dict(bad),exactTrainDialogueDuplicateExcess=sum(n-1 for n in duplicates.values()),readmeSamplePresentAndMustBeExcluded=readme_present,knowledgeMetadataWillNotBePositiveTargets=True,rawUtteranceTextUnmodified=True,upstreamValidAndTestNotAcquired=True,oldProtectedCorpusAndHeldoutHashOnlyOverlapAuditPending=True,notAdmittedToRound37OrAnyRun=True,movieAndSpeakerGroupGeneralizationNotEstablished=True,codeSha256=sha(pathlib.Path(__file__)))
(R/'train-quality.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out))
