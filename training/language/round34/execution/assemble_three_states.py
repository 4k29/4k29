"""Save full unedited old/selected/terminal text; never create semantic judgments."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';P=R.parent/'round33'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=read(R/'continue-10000/result.json');terminal=read(D/'mechanical-complete.json');control=read(P/'continue-10000/result.json')
assert result['completedRun'] and result['completedSteps']==10000
assert terminal['actualTerminalUpdates']==10000
same=terminal['terminalAndSelectedWeightsExactlyEqual']
assert not same or terminal['duplicateGenerationAvoided']
groups=[('original17','old-validation.json','new-validation.json',17),('daily12','daily-old-python.json','daily-new-python.json',12),('native8','content-native-dev/old-python.json','content-native-dev/new-python.json',8),('mrmp5','fixed-source-mrmp-dev/old-python.json','fixed-source-mrmp-dev/new-python.json',5)]
lines=['# Round34 — full old / selected / terminal generations','','Actual Round34 training completed10000 updates. Old comparator is Round33 selected'+str(control['bestStep'])+'. Round34 selected'+str(result['bestStep'])+' and terminal10000 use the same fixed inputs and unchanged bounded greedy generation. All texts below are unedited. This file records saved texts, NOT a claim that semantic reading or language gates are complete. See individual SHA-bound manual judgments and final assessment for actual reading scope. These are exposed DEV inputs, not a new TEST. Source5 are one cast family.','']
records=[];total=0
for group,op,np,count in groups:
 oldpath=E/op;newpath=E/np;endpath=newpath if same else D/f'{group}-python.json'
 old,new,end=read(oldpath),read(newpath),read(endpath)
 assert len(old['rows'])==len(new['rows'])==len(end['rows'])==count
 lines.extend([f'## {group}','',f'Old SHA {sha(oldpath)}; selected SHA {sha(newpath)}; terminal SHA {sha(endpath)}.',''])
 for a,b,c in zip(old['rows'],new['rows'],end['rows'],strict=True):
  assert a['id']==b['id']==c['id'] and a['prefix']==b['prefix']==c['prefix']
  assert a['inputTokens']==b['inputTokens']==c['inputTokens']
  assert all(len(row['tokens'])<=min(192,256-row['inputTokens'])for row in (a,b,c))
  if same:
   assert all(b[k]==c[k]for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens'])
  lines.extend([f"### {b['id']}",'','Prefix:','```text',b['prefix'],'```',''])
  for label,row in [(f"Round33 selected{control['bestStep']}",a),(f"Round34 selected{result['bestStep']}",b),('Round34 terminal10000',c)]:
   lines.extend([label+':','```text',row['text'],'```',''])
  total+=1
 records.append(dict(group=group,inputs=count,oldPath=str(oldpath.relative_to(R)),oldSha256=sha(oldpath),selectedPath=str(newpath.relative_to(R)),selectedSha256=sha(newpath),terminalPath=str(endpath.relative_to(R)),terminalSha256=sha(endpath)))
assert total==42
out=E/'FULL_THREE_STATE_GENERATIONS.md';out.write_text('\n'.join(lines)+'\n')
report=dict(actualCompletedUpdates=10000,selectedStep=result['bestStep'],controlSelectedStep=control['bestStep'],fixedInputs=42,savedStateOutputs=126,terminalAndSelectedWeightsExactlyEqual=same,additionalTerminalGenerationRequired=not same,allSavedTextsUnedited=True,notSemanticJudgments=True,noReadingClaimMadeByThisScript=True,notNewTest=True,groups=records,outputSha256=sha(out),codeSha256=sha(pathlib.Path(__file__)))
(E/'three-state-output-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
