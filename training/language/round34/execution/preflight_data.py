"""Independent complete appended-data and target-coverage audit. No heldout tokenizer/model."""
import collections,hashlib,json,pathlib,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];C=R.parent/'round25';D=R/'multiview';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
tok=read(D/'tokenizer.json');vocab=[bytes.fromhex(x) for x in tok['bytes']];old=read(C/'multiview/train.index.json');new=read(D/'train.index.json');values=np.memmap(D/'train.tokens.bin',dtype='<u4',mode='r')
assert new['rows'][:len(old['rows'])]==old['rows'];assert new['documents'][:len(old['documents'])]==old['documents'];prefix=(C/'multiview/train.tokens.bin').read_bytes();assert (D/'train.tokens.bin').read_bytes().startswith(prefix)
for name in ['tokenizer.json','validation.index.json','validation.tokens.bin']:assert sha(D/name)==sha(C/'multiview'/name)
source={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())};assert len(source)==read(R/'sources/manifest.json')['admittedUnits'];added=new['documents'][len(old['documents']):];assert len(added)==3*len(source);assert len({d['id'] for d in new['documents']})==len(new['documents']);rows=collections.defaultdict(list)
for row in new['rows'][len(old['rows']):]:rows[row['unit']].append(row)
views=collections.Counter();targets=collections.Counter();seen_source_views=set()
for d in added:
 u=source[d['sourceDocument']];assert u['partition']=='train' and u['site']==d['site']=='human-chat';variant=d['variant'];assert variant in [0,1,2];key=(d['sourceDocument'],variant);assert key not in seen_source_views;seen_source_views.add(key)
 stream=values[d['offset']:d['offset']+d['length']];assert len(stream)==d['length'] and stream[0]==1 and stream[-1]==2;assert all(4<=int(x)<len(vocab) for x in stream[1:-1]);raw=b''.join(vocab[int(x)] for x in stream[1:-1]);assert raw==u['text'].encode() and hashlib.sha256(raw).hexdigest()==d['textSha256']==u['textSha256'];assert len(raw)==d['utf8Bytes']
 expected=1
 for row in rows[d['id']]:
  assert row['offset']==d['offset']+row['start'] and row['length']==row['end']-row['start']<=257
  assert row['prefixLength']==(1 if row['start']==0 else 32);assert row['start']+row['prefixLength']==expected;assert row['end']<=len(stream);assert row['variant']==variant;expected=row['end']
 assert expected==len(stream)
 if variant==2:
  cuts=d['characterCuts'];assert cuts==sorted(set(cuts)) and cuts[-1]==len(u['text']);prior=0
  for cut in cuts:assert 1<=cut-prior<=24;prior=cut
 else:assert not d['characterCuts']
 views[variant]+=1;targets[variant]+=len(stream)-1
report=dict(allOldRowsAndDocumentsExactlyPreserved=True,allOldTokenBytesExactlyPreserved=True,allValidationAndTokenizerBytesExactlyPreserved=True,allNewViewBytesExactlyOriginalSerializedHumanText=True,allNewViewTrueBosEosAndNoInteriorSpecials=True,allNewLabelsCoveredExactlyOnce=True,allNewCharacterCutsWithinUnicodeBoundaries=True,trainSourceUnits=len(source),newViewCounts=dict(views),newTargetCounts=dict(targets),newSourceOnly='human-chat TRAIN',testTokenizedOrModelUsed=False,rawTestHashAuditDocumentedSeparately=True,optimizerUpdates=0,trainIndexSha256=sha(D/'train.index.json'),trainTokensSha256=sha(D/'train.tokens.bin'),sourceDocumentsSha256=sha(R/'sources/documents.jsonl'))
(R/'execution/data-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
