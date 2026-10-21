"""Verify saved full outputs and preserve all four states; never assign grades."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';P=R.parent/'round33'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
keys=['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens'];same=lambda a,b:all(a[k]==b[k]for k in keys)
assert read(R/'continue-10000/result.json')['completedSteps']==10000
assert read(E/'selected-full-reading-complete.json')['all42FullPrefixesAndContinuationsActuallyRead']
assert read(D/'full-reading-complete.json')['all42FullPrefixesAndContinuationsActuallyRead']
assert sha(R/'multiview/tokenizer.json')==sha(P/'multiview/tokenizer.json')
paths=[('original17',17,'old-validation.json','new-validation.json','new-validation-js.json','export-rounding.json'),('daily12',12,'daily-old-python.json','daily-new-python.json','daily-new-javascript.json','daily-new-unrounded.json'),('native8',8,'content-native-dev/old-python.json','content-native-dev/new-python.json','content-native-dev/new-javascript.json','content-native-dev/new-rounding.json'),('mrmp5',5,'fixed-source-mrmp-dev/old-python.json','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-javascript.json','fixed-source-mrmp-dev/new-unrounded.json')]
expected_models={'selected':sha(R/'continue-10000/model.js'),'terminal':sha(D/'model.js')};old_model=sha(P/'continue-10000/model.js');oldnumeric=[]
parity={};identities=[];lines=['# All four states — complete unedited generations','','42 identical inputs: R33 selected8000, R34 selected8000, R33 terminal10000, R34 terminal10000. Both rounds actually completed10000 from the same aligned R28 model/Adam/RNG. Same own tokenizer, unrestricted bounded greedy192 and context256. No output repair. All84 new R34 selected/terminal full prefixes and continuations were actually read; individual SHA-bound judgments are separate. The84 R33 control state outputs retain prior completed reading provenance, not a claim of a new current-turn reread of all old outputs. These are exposed DEV, not new TEST; source5 are one cast family. Token arrays and numerical references remain in JSON.','']
pin=read(E/'terminal-control-reference.json');pinrows={x['group']:x for x in pin['groups']}
for state in ['selected','terminal']:
 records=[]
 for group,n,op,np,jp,rp in paths:
  gp=E/np if state=='selected'else D/f'{group}-python.json';js=E/jp if state=='selected'else D/f'{group}-javascript.json';raw=E/rp if state=='selected'else D/f'{group}-unrounded.json'
  a,b,c=read(gp),read(js),read(raw);assert a['modelFileSha256']==b['modelSha256']==expected_models[state]
  for modelkey in ['modelSha256','roundedModelSha256']:
   if modelkey in c:assert c[modelkey]==expected_models[state]
  assert a['maxNewTokens']==192
  assert len(a['rows'])==len(b['rows'])==len(c['rows'])==n
  for k in ['sourceGenerationSha256','roundedGenerationSha256']:
   if k in c:assert c[k]==sha(gp)
  jsmatch=sum(same(x,y)for x,y in zip(a['rows'],b['rows'],strict=True));rawmatch=sum(same(x,y)for x,y in zip(a['rows'],c['rows'],strict=True));assert b['completeGenerationParity']==(jsmatch==n)
  if 'matchingSequences'in c:assert c['matchingSequences']==rawmatch
  errs=[x['maxAbsoluteError']for x in b.get('references',[])if 'maxAbsoluteError'in x]
  assert all(x['validUtf8']and x['validTokens']for x in a['rows'])
  records.append(dict(group=group,inputs=n,pythonJavascriptMatching=jsmatch,rawExportMatching=rawmatch,maxMeasuredReferenceLogitError=max(errs)if errs else None,referenceWithinUnchangedTolerance=all(v<=2e-4 for v in errs),generationSha256=sha(gp),javascriptSha256=sha(js),rawSha256=sha(raw)))
 parity[state]=dict(groups=records,total=42,pythonJavascriptMatching=sum(x['pythonJavascriptMatching']for x in records),rawExportMatching=sum(x['rawExportMatching']for x in records))
for group,n,op,np,jp,rp in paths:
 oldgeneration=read(E/op);old=oldgeneration['rows'];oldjs=E/jp.replace('new-','old-');oldjsdata=read(oldjs);assert oldgeneration['modelFileSha256']==oldjsdata['modelSha256']==old_model
 oldrawpath=None if group=='original17'else E/rp.replace('new-','old-')
 if group=='native8':oldrawpath=E/'content-native-dev/old-rounding.json'
 oldraw=read(oldrawpath)['rows']if oldrawpath else []
 assert len(old)==len(oldjsdata['rows'])==n
 if oldrawpath:assert len(oldraw)==n
 oldnumeric.append(dict(group=group,inputs=n,pythonJavascriptMatching=sum(same(a,b)for a,b in zip(old,oldjsdata['rows'],strict=True)),rawExportMatching=sum(same(a,b)for a,b in zip(old,oldraw,strict=True))if oldrawpath else None,rawCurrentRuntimeScope=n if oldrawpath else 0,javascriptSha256=sha(oldjs),rawSha256=sha(oldrawpath)if oldrawpath else None))
 prior=read(P/'execution'/np)['rows'];new=read(E/np)['rows'];oldendpath=P/'execution/terminal-state-diagnostic'/f'{group}-python.json';assert sha(oldendpath)==pinrows[group]['terminalSha256'];oldend=read(oldendpath)['rows'];newend=read(D/f'{group}-python.json')['rows'];assert all(same(a,b)for a,b in zip(old,prior,strict=True))
 for a,b,c,d in zip(old,new,oldend,newend,strict=True):assert a['id']==b['id']==c['id']==d['id']and a['prefix']==b['prefix']==c['prefix']==d['prefix']and a['inputTokens']==b['inputTokens']==c['inputTokens']==d['inputTokens']
 identities.append(dict(group=group,inputs=n,selectedFullCoreIdentityCount=sum(same(a,b)for a,b in zip(old,new,strict=True)),terminalFullCoreIdentityCount=sum(same(a,b)for a,b in zip(oldend,newend,strict=True)),selectedDifferentIds=[a['id']for a,b in zip(old,new,strict=True)if not same(a,b)],terminalDifferentIds=[a['id']for a,b in zip(oldend,newend,strict=True)if not same(a,b)],oldCurrentRuntimeControlExactlyMatchesPriorSelected=True))
 lines.extend([f'## {group}',''])
 for a,b,c,d in zip(old,new,oldend,newend,strict=True):
  lines.extend([f"### {a['id']}",'','Prefix:','```text',a['prefix'],'```',''])
  for label,row in [('R33 selected8000',a),('R34 selected8000',b),('R33 terminal10000',c),('R34 terminal10000',d)]:lines.extend([label+':','```text',row['text'],'```',''])
out=E/'ALL_FOUR_STATE_GENERATIONS.md';out.write_text('\n'.join(lines)+'\n');legacy=R.parent/'round11/execution/old-numerical-divergence.json'
report=dict(actualCompletedUpdates=10000,selectedStep=8000,parity=parity,unchangedReferenceTolerance=2e-4,oldControlCurrentNumerical=oldnumeric,oldSelectedCurrentPythonJavascriptScope=sum(x['inputs']for x in oldnumeric),oldSelectedCurrentRawExportScope=sum(x['rawCurrentRuntimeScope']for x in oldnumeric),oldSelectedCurrentPythonJavascriptMatching=sum(x['pythonJavascriptMatching']for x in oldnumeric),oldSelectedCurrentRawExportMatching=sum(x['rawExportMatching']or 0 for x in oldnumeric),oldOriginal17RawNotRegeneratedInCurrentRuntime=True,oldTerminalEvidenceHistoricalNotNewCurrentRuntimeRerun=True,historicalRound10NearTieDivergenceRetained=dict(path='../round11/execution/old-numerical-divergence.json',sha256=sha(legacy)),universalParityClaim=False,noOutputRepair=True,noNewModelForwardOrOptimizerByThisVerifier=True,savedStateOutputs=168,newStateOutputsActuallyRead=84,notIndependent168Examples=True,fullFourStateOutputSha256=sha(out),pairedOutputIdentity=identities,codeSha256=sha(pathlib.Path(__file__)))
(E/'final-output-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(actualUpdates=10000,selected=parity['selected'],terminal=parity['terminal'],savedStateOutputs=168,newActuallyRead=84)))
