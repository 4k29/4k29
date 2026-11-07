"""TRAIN-only read-only true human utterance boundary audit; no token/data/model changes."""
import pathlib,json,hashlib,array,collections,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest();cache=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train');units={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())};offsets={};embedded=0;utterances=0
for key,d in units.items():
 p=cache/pathlib.PurePosixPath(d['sourcePath']).name;raw=p.read_bytes();assert sha(raw)==d['sourceSha256'];u=json.loads(raw)['utterances'];texts=[x['text'] for x in u];assert '\n'.join(texts)==d['text'];assert len(u)==d['utteranceCount'];ends=[];n=0
 for i,text in enumerate(texts):
  embedded+=text.count('\n');n+=len(text.encode())
  if i<len(texts)-1:n+=1;ends.append(n)
 assert n==len(d['text'].encode());offsets[key]=ends;utterances+=len(u)
index=read(R/'multiview/train.index.json');vocab=[bytes.fromhex(x) for x in read(R/'multiview/tokenizer.json')['bytes']];values=array.array('I');values.frombytes((R/'multiview/train.tokens.bin').read_bytes());counts=collections.defaultdict(collections.Counter);affected=[]
for d in index['documents']:
 if d['site']!='human-chat':continue
 boundaries=offsets[d['sourceDocument']];c=counts[d['variant']];c['dialogues']+=1;c['trueInteriorTurnBoundaries']+=len(boundaries);ends=[];tokens=values[d['offset']+1:d['offset']+d['length']-1];n=0
 for token in tokens:n+=len(vocab[token]);ends.append(n)
 endset=set(ends);c['alreadyAlignedAfterSeparator']+=sum(b in endset for b in boundaries)
 import bisect
 for b in boundaries:
  if b not in endset:
   j=bisect.bisect_left(ends,b);start=ends[j-1] if j else 0;piece=vocab[tokens[j]];cut=b-start;assert piece[cut-1]==10
   affected.append(dict(sourcePath=units[d['sourceDocument']]['sourcePath'],sourceSha256=units[d['sourceDocument']]['sourceSha256'],variant=d['variant'],tokenIndex=j,tokenId=tokens[j],tokenBytesHex=piece.hex(),splitAtByte=cut,actualTurnOffsetAfterSeparator=b));c['requiresPieceSplitAfterSeparator']+=1
assert len(units)==8975 and utterances==269877
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Admitted human TRAIN only; reserved DEV/TEST not accessed',sourceDocumentsSha256=sha((R/'sources/documents.jsonl').read_bytes()),trainTokensSha256=sha((R/'multiview/train.tokens.bin').read_bytes()),auditorSha256=sha(pathlib.Path(__file__).read_bytes()),admittedTrainDialogues=len(units),humanUtterances=utterances,trueInteriorTurnBoundaries=sum(map(len,offsets.values())),embeddedOriginalNewlines=embedded,variants=dict(counts),affectedPieces=affected,trainingDataChanged=False,modelOrOptimizerInstantiated=False,optimizerUpdates=0,hypotheticalAdditionalEosPerView=utterances-len(units),conclusion='After-separator EOS would preserve almost all existing token IDs but requires explicitly documented splitting at listed true boundaries. It is a future turn-framing representation experiment, not an EOS-only proof or a condition of Round29.')
(E/'true-turn-boundary-diagnostic.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='affectedPieces'}))
