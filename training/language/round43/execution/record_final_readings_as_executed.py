"""Bind explicit SHA-restricted actual R43 reading notes; never grade unseen outputs."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();notes=read(E/'reading-notes-as-executed.json');keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];first={};whole={};refs=[]
spec=[('Original17','original17','new-validation.json','new-manual.json',17),('Daily12','daily12','daily-new-python.json','daily-new-reading.json',12),('Native8','native8','content-native-dev/new-python.json','content-native-dev/new-reading.json',8),('Mrmp5','mrmp5','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-reading.json',5)]
for n in [39,40,41,42]:
 P=R.parent/f'round{n}';bound={x['path']:x for x in read(P/'execution/artifact-manifest.json')['files']}
 for state in ['selected','terminal']:
  for _,group,g,m,_ in spec:
   if state=='terminal':g=f'terminal-state-diagnostic/{group}-python.json';m=f'terminal-state-diagnostic/{group}-'+('manual.json'if group=='original17'else'reading.json')
   gp=P/'execution'/g;mp=P/'execution'/m
   for p in [gp,mp]:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
   a,b=read(gp),read(mp);assert b['generationSha256']==sha(gp)
   for x,y in zip(a['rows'],b['rows'],strict=True):
    loc=f'R{n}/{state}/{group}/{x["id"]}';k=(x['prefix'],x['text']);v=(y['fullOutputMeaningful'],y['fullOutputLoop'])
    if k in whole:assert whole[k][0]==v
    whole[k]=(v,loc)
    if group=='original17'and'。'in x['text']:
     f=x['prefix']+x['text'].split('。')[0]+'。';v={k:y[k]for k in keys}
     if f in first:assert first[f][0]==v
     first[f]=(v,loc)
   refs.append(dict(round=n,state=state,group=group,generationSha256=sha(gp),manualSha256=sha(mp)))
for state in ['selected','terminal']:
 for suffix,group,g,m,n in spec:
  name=state+suffix
  if name not in notes:continue
  note=notes[name];assert note[f'all{n}FullPrefixesAndContinuationsActuallyRead']
  if state=='terminal':g=f'terminal-state-diagnostic/{group}-python.json';m=f'terminal-state-diagnostic/{group}-'+('manual.json'if group=='original17'else'reading.json')
  gp=E/g;mp=E/m;assert sha(gp)==note['generationSha256'],'Never apply historical notes to unseen future generation';gen=read(gp);assert len(gen['rows'])==len(note['reasons'])==n;rows=[]
  for i,x in enumerate(gen['rows']):
   v=(i in note['wholeMeaningIndices'],i in note['loopIndices']);k=(x['prefix'],x['text'])
   if k in whole:assert v==whole[k][0],(name,i,v,whole[k])
   row=dict(id=x['id'],fullOutputMeaningful=v[0],fullOutputLoop=v[1],intrusiveRepetition=v[1]or i in note.get('intrusiveRepetitionIndices',[]),reason=note['reasons'][i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
   assert row['reason']and((x['validTokens']and x['validUtf8'])or not v[0])
   if group=='original17':
    f=x['prefix']+x['text'].split('。')[0]+'。'if'。'in x['text']else None
    if f in first:scores,loc=first[f];row.update(scores,firstSentenceScoreProvenance='Literal full prefix+first sentence exactly matches '+loc+'; primary components unchanged')
    else:row.update(dict(zip(keys,note['freshFirstSentenceComponents'][str(i)],strict=True)),firstSentenceScoreProvenance='Explicit fresh first sentence or unclosed continuation actually read in R43; no automated semantic grader')
   rows.append(row)
  out=dict(generationSha256=sha(gp),readingNotesSha256=sha(E/'reading-notes-as-executed.json'),actualRetainedUpdates=10000,selectedStep=read(R/'continue-10000/result.json')['bestStep'],evaluatedStep=read(R/'continue-10000/result.json')['bestStep']if state=='selected'else 10000,allFullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(x['fullOutputMeaningful']for x in rows),longLoopsPrimary=sum(x['fullOutputLoop']for x in rows),eos=sum(x['eos']for x in gen['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,noOutputRepair=True,sensitivities=note.get('sensitivities',{}),rows=rows)
  if group=='original17':out.update(meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete R43 reading; not independent blind human',historicalFirstSentenceReferences=refs)
  if group=='native8':out.update(explicitRelevantReference=note.get('explicitRelevantReference',0),newRelevantInformation=note.get('newRelevantInformation',0))
  mp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(name,out['wholeMeaning'],out['longLoopsPrimary'],out['eos'])
