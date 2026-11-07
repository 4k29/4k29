import pathlib,json,hashlib,collections,bisect,array,datetime
R=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tok=read(R/'multiview/tokenizer.json');vocab=[bytes.fromhex(x) for x in tok['bytes']];idx=read(R/'multiview/train.index.json');values=array.array('I');values.frombytes((R/'multiview/train.tokens.bin').read_bytes());units={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())};counts=collections.defaultdict(collections.Counter)
for d in idx['documents']:
 if d['site']!='human-chat':continue
 raw=units[d['sourceDocument']]['text'].encode();ends=[];end=0
 for t in values[d['offset']+1:d['offset']+d['length']-1]:end+=len(vocab[t]);ends.append(end)
 assert end==len(raw);endset=set(ends);c=counts[d['variant']];c['dialogues']+=1
 for n,b in enumerate(raw):
  if b==10:c['newlines']+=1;c['beforeNewlineInsidePiece']+=n not in endset;c['afterNewlineInsidePiece']+=(n+1) not in endset
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='TRAIN-only representation diagnostic for a possible future isolated experiment; no token streams changed and no model updates',sourceSha256=sha(R/'sources/documents.jsonl'),trainTokensSha256=sha(R/'multiview/train.tokens.bin'),variants=dict(counts),interiorBosOrEosInCurrentHumanStreams=False,currentDialogueTerminalEos=8975,humanUtterances=269877,warning='Newline audit is not proof of utterance boundaries if original utterances themselves contain newline. Inserting EOS before/after every newline cannot always preserve current segmentation. Audit source utterance byte offsets separately before any future marker experiment.')
(R/'execution/turn-boundary-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
