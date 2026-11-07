"""Pin completed R39 terminal control, before viewing R40 final generations."""
import pathlib,json,hashlib,datetime,os
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round39';E=R/'execution';D=P/'execution/terminal-state-diagnostic'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=P/'execution/artifact-manifest.json';a=read(manifest);verified=[]
for item in a['files']:
 if not item['path'].startswith('execution/terminal-state-diagnostic/'):continue
 p=P/item['path'];assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],item['path'];verified.append(item)
assert verified
m=read(D/'mechanical-complete.json');assert m['actualTerminalUpdates']==10000 and not m['terminalAndSelectedWeightsExactlyEqual']
reading=read(D/'full-reading-complete.json');assert reading['all42FullPrefixesAndContinuationsActuallyRead']
assert read(P/'execution/final-assessment.json')['fullOutputReviewPending'] is False
groups=[('original17','new-validation.json',17),('daily12','daily-new-python.json',12),('native8','content-native-dev/new-python.json',8),('mrmp5','fixed-source-mrmp-dev/new-python.json',5)];refs=[]
for group,selected,count in groups:
 p=D/f'{group}-python.json';c=P/'execution'/selected;x,y=read(p),read(c);assert len(x['rows'])==len(y['rows'])==count
 for u,v in zip(x['rows'],y['rows'],strict=True):assert u['id']==v['id'] and u['prefix']==v['prefix']
 refs.append(dict(group=group,inputs=count,terminalPath=os.path.relpath(p,R),terminalSha256=sha(p),selectedControlPath=os.path.relpath(c,R),selectedControlSha256=sha(c)))
review=read(D/'original17-review.json')
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),controlRound=38,actualControlCompletedUpdates=10000,controlEvaluatedUpdates=10000,controlSelectedUpdates=m['originalTrialSelectedStep'],controlTerminalCommonDevNll=m['terminalCommonDevNll'],controlFinalArtifactManifestSha256=sha(manifest),verifiedTerminalArtifacts=verified,groups=refs,controlOriginal17Passed=review['passed'],controlOriginal17Nonloop=review['fullOutputNonLoop'],controlOriginal17WholeMeaning=review['fullOutputMeaningful'],priorControlFullReadingProvenanceVerified=True,noNewJudgmentsAssigned=True,noNewModelGeneration=True,noOptimizerOrRngUsed=True,comparisonIsAdditionalMatchedUpdateDiagnostic=True,officialSelectedComparisonAndSelectorUnchanged=True,notNewTest=True,notRound40LanguageResult=True,codeSha256=sha(pathlib.Path(__file__)))
(E/'terminal-control-reference.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['verifiedTerminalArtifacts','groups']}))
