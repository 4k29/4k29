"""Additional equal-update terminal comparison; no generations or judgments."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=read(E/'terminal-control-reference.json');m=read(D/'mechanical-complete.json');result=read(R/'continue-10000/result.json')
assert result['completedRun'] and result['completedSteps']==m['actualTerminalUpdates']==ref['controlEvaluatedUpdates']==10000
same=m['terminalAndSelectedWeightsExactlyEqual'];primary={'original17':'new-validation.json','daily12':'daily-new-python.json','native8':'content-native-dev/new-python.json','mrmp5':'fixed-source-mrmp-dev/new-python.json'}
lines=['# Matched terminal comparison — actual10000 updates each','','Additional diagnostic, not a replacement of official NLL-selected comparisons or the selector. Both states continued from the same aligned Round28 latest for10000 actual updates, with within-human source weights RealPersona25% and JMRD5% as the sole learning-condition change. Existing exposed DEV, same fixed inputs and bounded greedy conditions. Old Round46 terminal outputs are retained historical outputs, not a new current-runtime rerun. All text is unedited. Saving text does not assign language scores or certify actual reading. Full token arrays and numerical evidence remain in their source JSON files.',''];records=[];total=0
for item in ref['groups']:
 group=item['group'];oldpath=R/item['terminalPath'];newpath=E/primary[group]if same else D/f'{group}-python.json'
 assert sha(oldpath)==item['terminalSha256']
 old,new=read(oldpath),read(newpath);assert len(old['rows'])==len(new['rows'])==item['inputs']
 lines.extend([f'## {group}','',f'R46 SHA {sha(oldpath)}; R47 SHA {sha(newpath)}.',''])
 for a,b in zip(old['rows'],new['rows'],strict=True):
  assert a['id']==b['id'] and a['prefix']==b['prefix']
  assert a['inputTokens']==b['inputTokens']
  assert all(len(row['tokens'])<=min(192,256-row['inputTokens'])for row in (a,b))
  lines.extend([f"### {b['id']}",'','Prefix:','```text',b['prefix'],'```','','Round46 terminal10000:','```text',a['text'],'```','','Round47 terminal10000:','```text',b['text'],'```','']);total+=1
 records.append(dict(group=group,inputs=item['inputs'],oldSha256=sha(oldpath),newSha256=sha(newpath)))
assert total==42
out=E/'MATCHED_10000_FULL_GENERATIONS.md';out.write_text('\n'.join(lines)+'\n')
report=dict(actualAdditionalUpdatesEach=10000,inputs=42,savedStateOutputs=84,selectedComparisonUnchanged=True,groups=records,noNewGenerationOrOptimizer=True,noJudgmentsAssigned=True,notNewTest=True,oldControlReferenceSha256=sha(E/'terminal-control-reference.json'),outputSha256=sha(out),codeSha256=sha(pathlib.Path(__file__)))
(E/'matched-terminal-output-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
