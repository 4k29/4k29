"""Preserve all fixed old/new full texts; semantic assessment is separate."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(R/'continue-10000/result.json');assert r['completedRun']and r['completedSteps']==10000
oldmodel=R.parent/'round46/continue-10000/model.js';newmodel=R/'continue-10000/model.js'
lines=['# Round47 — all84 old/new unedited full continuations','','Scientific paired comparator Round46 versus Round47, both actual10000 from the same aligned Round28 parent. Each model uses its declared common-DEV selected state, not an assumed terminal state. Same original inputs, own full-vocabulary greedy192, Python1thread, no output repair. Exposed DEV only, not new TEST. Full tokens remain in each JSON. This assembly does not assign semantic scores. Source licenses and attribution remain in content-native-dev and ../../fixed-source-mrmp-dev. Source5 share ONE speaker-combination family.',''];groups=[]
for label,op,np,nrows in [('original17',E/'old-validation.json',E/'new-validation.json',17),('daily12',E/'daily-old-python.json',E/'daily-new-python.json',12),('native8',E/'content-native-dev/old-python.json',E/'content-native-dev/new-python.json',8),('mrmp5',E/'fixed-source-mrmp-dev/old-python.json',E/'fixed-source-mrmp-dev/new-python.json',5)]:
 a,b=read(op),read(np);assert len(a['rows'])==len(b['rows'])==nrows and a['maxNewTokens']==b['maxNewTokens']==192 and a['evaluationThreads']==b['evaluationThreads']==1
 assert a['modelFileSha256']==sha(oldmodel)and b['modelFileSha256']==sha(newmodel)
 lines += [f'## {label}',f'Old JSON SHA {sha(op)}; new JSON SHA {sha(np)}','']
 for o,n in zip(a['rows'],b['rows'],strict=True):
  assert o['id']==n['id']and o['prefix']==n['prefix'];lines += [f"### {n['id']}",'','Prefix:','```text',n['prefix'],'```','','Round46:','```text',o['text'],'```','','Round47 selected:','```text',n['text'],'```','']
 groups.append(dict(group=label,rowsEach=nrows,oldGenerationSha256=sha(op),newGenerationSha256=sha(np)))
out=E/'FINAL_FULL_GENERATIONS.md';out.write_text('\n'.join(lines)+'\n');(E/'full-output-assembly.json').write_text(json.dumps(dict(actualChildUpdates=10000,groups=groups,all84FullTextsSaved=True,markdownSha256=sha(out),noSemanticJudgmentByAssembler=True,noOutputRepair=True),indent=2)+'\n');print('All84 old/new full texts assembled; no semantic scores inferred')
