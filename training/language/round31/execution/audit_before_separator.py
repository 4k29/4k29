"""Read-only prospective framing footprint on admitted R29 human TRAIN only.
No model, optimizer, TEST, tokenizer training, or corpus mutation.
"""
import array,bisect,collections,hashlib,json,pathlib
E=pathlib.Path(__file__).resolve().parent;R=E.parents[1]/'round29'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
units={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())}
cache=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train')
ends={};embedded=0;utterances=0
for key,d in units.items():
 p=cache/pathlib.PurePosixPath(d['sourcePath']).name;assert sha(p)==d['sourceSha256'];texts=[u['text'] for u in read(p)['utterances']]
 assert '\n'.join(texts)==d['text'] and len(texts)==d['utteranceCount']
 n=0;cuts=[]
 for i,text in enumerate(texts):
  embedded+=text.count('\n');n+=len(text.encode())
  if i<len(texts)-1:cuts.append(n);n+=1
 assert n==len(d['text'].encode());ends[key]=cuts;utterances+=len(texts)
vocab=[bytes.fromhex(x) for x in read(R/'multiview/tokenizer.json')['bytes']]
values=array.array('I');values.frombytes((R/'multiview/train.tokens.bin').read_bytes())
counts=collections.defaultdict(collections.Counter);examples=[]
for doc in read(R/'multiview/train.index.json')['documents']:
 if doc['site']!='human-chat':continue
 source=units[doc['sourceDocument']];tokens=values[doc['offset']+1:doc['offset']+doc['length']-1]
 assert b''.join(vocab[t] for t in tokens)==source['text'].encode()
 positions=[];n=0
 for token in tokens:n+=len(vocab[token]);positions.append(n)
 c=counts[doc['variant']];c['dialogues']+=1;c['trueInteriorBoundaries']+=len(ends[doc['sourceDocument']])
 for cut in ends[doc['sourceDocument']]:
  j=bisect.bisect_left(positions,cut)
  if positions[j]==cut:c['alreadyTokenAlignedBeforeSeparator']+=1
  else:
   c['requiresPieceSplitBeforeSeparator']+=1;start=positions[j-1] if j else 0;piece=vocab[tokens[j]];local=cut-start
   assert 0<local<len(piece) and piece[local:local+1]==b'\n'
   # Real utterance boundaries, not arbitrary newline guesses.
   piece[:local].decode('utf8');piece[local:].decode('utf8')
   if len(examples)<24:examples.append(dict(sourceDocument=doc['sourceDocument'],sourceSha256=source['sourceSha256'],variant=doc['variant'],tokenId=tokens[j],tokenBytesHex=piece.hex(),splitAtByte=local))
assert len(units)==8975 and utterances==269877 and embedded==21
out=dict(scope='Admitted R29 human TRAIN only, no heldout reads',scientificComparatorIfTrained='round29',separateAdoptionAnchor='round25',sourceDocumentsSha256=sha(R/'sources/documents.jsonl'),sourceIndexSha256=sha(R/'multiview/train.index.json'),sourceTokensSha256=sha(R/'multiview/train.tokens.bin'),auditorSha256=sha(pathlib.Path(__file__)),admittedTrainDialogues=len(units),humanUtterances=utterances,trueInteriorBoundaries=sum(map(len,ends.values())),embeddedOriginalNewlines=embedded,variants={str(k):dict(v) for k,v in counts.items()},splitExamples=examples,noReservedDevOrTestRead=True,fullTokenBytesVerifiedAgainstEveryAdmittedHumanSource=True,trainingDataChanged=False,modelOrOptimizerInstantiated=False,actualOptimizerUpdates=0,framingCandidateTrained=False,interpretation='Before-separator EOS avoids directly teaching EOS immediately after newline, but splits existing pieces and changes sequence length/window/target distribution. Raw native input omits proposed historical EOS markers, an unresolved serialization mismatch. This count does not validate a training design or establish semantic improvement. No framing or LR change has been trained in R31.')
(E/'before-separator-footprint.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='splitExamples'}))
