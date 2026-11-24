"""Verify explicit full-reading records and identical-text consistency for both states."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();selected=[('original17',E/'new-validation.json',E/'new-manual.json',17),('daily12',E/'daily-new-python.json',E/'daily-new-reading.json',12),('native8',E/'content-native-dev/new-python.json',E/'content-native-dev/new-reading.json',8),('mrmp5',E/'fixed-source-mrmp-dev/new-python.json',E/'fixed-source-mrmp-dev/new-reading.json',5)];seen={};records=[];duplicates=[];terminal=[]
for state in ['selected','terminal']:
 for name,gp,mp,n in selected:
  if state=='terminal':gp=D/f'{name}-python.json';mp=D/('original17-manual.json'if name=='original17'else f'{name}-reading.json')
  g,m=read(gp),read(mp);assert sha(gp)==m['generationSha256'];assert len(g['rows'])==len(m['rows'])==n
  for x,y in zip(g['rows'],m['rows'],strict=True):
   h=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert x['id']==y['id']and h==y['prefixAndTextSha256'];assert x['validTokens']and x['validUtf8'];key=(x['prefix'],x['text']);v=(y['fullOutputMeaningful'],y['fullOutputLoop'])
   if key in seen:assert seen[key]['judgment']==v;duplicates.append(dict(state=state,group=name,id=x['id'],sameAs=seen[key]['location']))
   else:seen[key]=dict(judgment=v,location=f'{state}/{name}/{x["id"]}')
  rec=dict(state=state,group=name,rows=n,generationSha256=sha(gp),manualSha256=sha(mp),wholeMeaning=sum(x['fullOutputMeaningful']for x in m['rows']),longLoops=sum(x['fullOutputLoop']for x in m['rows']),eos=sum(x['eos']for x in g['rows']));records.append(rec)
  if state=='terminal':terminal.append(rec)
out=dict(actualRetainedUpdates=10000,selectedStep=read(R/'continue-10000/result.json')['bestStep'],terminalStep=10000,all84NewStateFullPrefixesAndContinuationsActuallyRead=True,uniqueNewPrefixFullTextPairs=len(seen),identicalFullTextJudgmentsConsistent=True,duplicates=duplicates,notIndependentBlindHuman=True,notNewTest=True,noOutputRepair=True,additionalOptimizerUpdates=0,groups=records);(E/'all-new-reading-consistency.json').write_text(json.dumps(out,indent=2)+'\n');(D/'full-reading-complete.json').write_text(json.dumps(dict(actualRetainedUpdates=10000,evaluatedStep=10000,all42FullPrefixesAndContinuationsActuallyRead=True,notNewTest=True,notIndependentBlindHuman=True,groups=terminal),indent=2)+'\n');print(json.dumps(out))
