"""Observational actual TRAIN prefix audit; no alternative condition or model run.
Use original utterance offsets, not newline heuristics. No DEV/TEST read.
"""
import pathlib,json,hashlib,io,collections,sys,torch,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';torch.set_num_threads(1);read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest();cachepath=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/train');source={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())};index=read(R/'multiview/train.index.json');docs={d['id']:d for d in index['documents']};values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');vocab=[bytes.fromhex(x)for x in read(R/'multiview/tokenizer.json')['bytes']];sourcecache={};tokenbytecache={};models={}
for label,C in [('round28',R.parent/'round28'),('round33',R)]:
 rawcp=(C/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(rawcp),map_location='cpu',weights_only=False);assert (C/'multiview/train.index.json').read_bytes()==(R/'multiview/train.index.json').read_bytes();trace=[]
 for line in (C/'continue-10000/training-rollouts.jsonl').read_text().splitlines(keepends=True):
  if line.endswith('\n'):
   x=json.loads(line)
   if x['step']<=cp['step']:trace.append(x)
 assert [x['step']for x in trace]==list(range(10,cp['step']+1,10))and len(trace)==cp['rolloutCalls'];rows=[];bos=0
 for x in trace:
  row=x['sourceRow'];d=docs[row['unit']];prefix=x['tokens'][:x['prefixLength']];assert prefix==list(map(int,values[row['offset']:row['offset']+len(prefix)]));bos+=prefix[0]==1
  if d['site']!='human-chat':continue
  key=d['sourceDocument'];u=source[key]
  if key not in sourcecache:
   raw=(cachepath/pathlib.PurePosixPath(u['sourcePath']).name).read_bytes();assert sha(raw)==u['sourceSha256'];utterances=json.loads(raw)['utterances'];texts=[z['text']for z in utterances];assert '\n'.join(texts)==u['text']and len(texts)==u['utteranceCount'];ends=[];offset=0
   for i,text in enumerate(texts):
    offset+=len(text.encode())
    if i<len(texts)-1:offset+=1;ends.append(offset)
   assert offset==len(u['text'].encode());sourcecache[key]=(set(ends),set(b-1 for b in ends),offset,sum(t.count('\n')for t in texts))
  after,before,total,embedded=sourcecache[key]
  if d['id']not in tokenbytecache:
   full=values[d['offset']:d['offset']+d['length']];sums=[0]
   for t in full:sums.append(sums[-1]+len(vocab[int(t)]))
   assert sums[-1]==total;tokenbytecache[d['id']]=sums
  sums=tokenbytecache[d['id']];start=sums[row['start']];end=sums[row['start']+len(prefix)];rows.append(dict(step=x['step'],sourceDocument=key,sourceSha256=u['sourceSha256'],variant=row['variant'],prefixTokens=len(prefix),prefixStartByte=start,prefixEndByte=end,beginsWithBos=prefix[0]==1,endAfterTrueInteriorTurnSeparator=end in after,endBeforeTrueInteriorTurnSeparator=end in before,endAtDialogueTextEndBeforeEos=end==total,visibleTrueInteriorSeparators=sum(start<b<=end for b in after),sourceContainsEmbeddedNewlines=embedded>0))
 summary=dict(actualRetainedLocalUpdates=cp['step'],allRecordedNegativeCalls=len(trace),allSourcePrefixTokensExact=True,allCallsWithBos=bos,allCallsWithoutBos=len(trace)-bos,humanNegativeCalls=len(rows),humanPrefixEndsAfterTrueInteriorTurnSeparator=sum(x['endAfterTrueInteriorTurnSeparator']for x in rows),humanPrefixEndsBeforeTrueInteriorTurnSeparator=sum(x['endBeforeTrueInteriorTurnSeparator']for x in rows),humanPrefixEndsAtDialogueTextEndBeforeEos=sum(x['endAtDialogueTextEndBeforeEos']for x in rows),humanPrefixesSeeingAtLeastOneTrueSeparator=sum(x['visibleTrueInteriorSeparators']>0 for x in rows),humanCallsByVariant=dict(collections.Counter(x['variant']for x in rows)))
 models[label]=dict(summary=summary,checkpointSha256=sha(rawcp),rows=rows)
out=dict(models=models,actualTrainOnly=True,noDevOrTestRead=True,noModelInstantiated=True,noAlternativePrefixConditionExecuted=True,noLearningInputOrConditionChanged=True,additionalOptimizerUpdates=0,sourceDocumentsSha256=sha((R/'sources/documents.jsonl').read_bytes()),trainIndexSha256=sha((R/'multiview/train.index.json').read_bytes()),auditorSha256=sha(pathlib.Path(__file__).read_bytes()),limits='Counts where recorded negatives started, not whether alternate positions would improve semantics. True offsets use original human utterance arrays; embedded newlines are not fabricated turn boundaries. BOS/mid-utterance distribution alone does not establish a causal failure mechanism.')
p=E/f"negative-turn-position-audit-{models['round33']['summary']['actualRetainedLocalUpdates']}.json";p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v['summary']for k,v in models.items()}))
