"""Bind unedited four-state outputs only; never judge semantics or modify a model."""
import pathlib,json,hashlib,re,os
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round39';E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=read(R/'continue-10000/result.json');assert result['completedRun']and result['completedSteps']==10000
oldresult=read(P/'continue-10000/result.json');assert oldresult['completedSteps']==10000
terminal=read(D/'mechanical-complete.json');same=terminal['terminalAndSelectedWeightsExactlyEqual'];manifest=read(P/'execution/artifact-manifest.json');bound={x['path']:x for x in manifest['files']}
spec=[('original17','old-validation.json','new-validation.json',17),('daily12','daily-old-python.json','daily-new-python.json',12),('native8','content-native-dev/old-python.json','content-native-dev/new-python.json',8),('mrmp5','fixed-source-mrmp-dev/old-python.json','fixed-source-mrmp-dev/new-python.json',5)];core=['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens'];records=[];lines=['# Round40 — all four states, complete raw continuations','','Both experiments performed10000 actual updates from the same full R28 initial model/Adam/RNG. Only the anchored human context-preference auxiliary objective is added in R40. Main source25%/5%, existing losses, sampling, model, LR, selector and generation stay fixed. Auxiliary canonical exposure is separate.','','42 exposed DEV inputs,168 state outputs, not168 independent examples. No new TEST. Source5 uses ONE cast family/three public pseudonymous speakers. Every prefix and continuation below is unedited; full token IDs remain in the referenced JSON. This assembly assigns no semantic scores and does not certify manual reading. Old terminal outputs retain verified historical provenance.','']
def block(text):
 fence='`'*max(3,1+max([len(x)for x in re.findall(r'`+',text)]or[0]));return [fence+'text',text,fence]
for group,op,np,n in spec:
 paths=[E/op,E/np,P/'execution/terminal-state-diagnostic'/f'{group}-python.json',E/np if same else D/f'{group}-python.json'];states=[read(p)['rows']for p in paths];historical=P/'execution'/np;old=read(historical)['rows'];assert all(len(s)==n for s in states)
 for p in [historical,paths[2]]:
  k=str(p.relative_to(P));assert sha(p)==bound[k]['sha256']and p.stat().st_size==bound[k]['bytes']
 for a,b in zip(states[0],old,strict=True):assert all(a[k]==b[k]for k in core),a['id']
 lines += [f'## {group}','']
 for rows in zip(*states,strict=True):
  assert len({x['id']for x in rows})==len({x['prefix']for x in rows})==1;lines += [f"### {rows[0]['id']}",'','Full prefix:']+block(rows[0]['prefix'])+['']
  for label,row in zip([f"R39 selected{oldresult['bestStep']}",f"R40 selected{result['bestStep']}",'R39 terminal10000','R40 terminal10000'],rows,strict=True):lines += [label+':']+block(row['text'])+['']
 records.append(dict(group=group,inputs=n,paths=[dict(path=os.path.relpath(p,R),sha256=sha(p))for p in paths],oldSelectedRawCoresExactlyMatchHistorical=True))
out=E/'ALL_FOUR_STATE_GENERATIONS.md';out.write_text('\n'.join(lines)+'\n');a=dict(actualCompletedUpdatesEach=10000,savedFourStateOutputs=168,uniqueFixedInputs=42,selectedStep=result['bestStep'],terminalSelectedWeightsExactlyEqual=same,oldFinalManifestSha256=sha(P/'execution/artifact-manifest.json'),allRawTextUnmodified=True,noSemanticScoresAssigned=True,semanticReadingCertifiedByAssembler=False,notNewTest=True,groups=records,fullTextSha256=sha(out),codeSha256=sha(pathlib.Path(__file__)));(E/'raw-four-state-assembly.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps({k:v for k,v in a.items()if k!='groups'}))
