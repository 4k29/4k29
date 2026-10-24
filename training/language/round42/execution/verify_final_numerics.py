"""Verify measured full-sequence numerical scope without hiding historical ties."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();specs=[('original17','new-validation.json','new-validation-js.json','export-rounding.json',17),('daily12','daily-new-python.json','daily-new-javascript.json','daily-new-unrounded.json',12),('native8','content-native-dev/new-python.json','content-native-dev/new-javascript.json','content-native-dev/new-rounding.json',8),('mrmp5','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-javascript.json','fixed-source-mrmp-dev/new-unrounded.json',5)];js_errors=[];raw_errors=[];reports=[];core=['id','prefix','text','tokens','eos','validTokens','validUtf8','inputTokens']
def errors(obj):
 return [v for ref in obj.get('references',[])for k,v in ref.items()if k in ['maxAbsoluteError','maxAbsoluteLogitError']]
for state in ['selected','terminal']:
 for group,gp,jp,rp,n in specs:
  if state=='terminal':gp=D/f'{group}-python.json';jp=D/f'{group}-javascript.json';rp=D/f'{group}-unrounded.json'
  else:gp=E/gp;jp=E/jp;rp=E/rp
  g,j,raw=map(read,[gp,jp,rp]);assert j['completeGenerationParity'];assert len(g['rows'])==len(j['rows'])==len(raw['rows'])==n
  for a,b,c in zip(g['rows'],j['rows'],raw['rows'],strict=True):
   assert all(a[k]==b[k]==c[k]for k in core),a['id']
  js_errors+=errors(j);raw_errors+=errors(raw);reports.append(dict(state=state,group=group,sequences=n,allPythonJavascriptAndRawRoundedMatch=True,pythonSha256=sha(gp),javascriptSha256=sha(jp),rawSha256=sha(rp)))
# Daily raw reference errors are held in its companion report.
raw_errors+=errors(read(E/'daily-rounding-comparison.json')['models']['new'])
tolerance=2e-4;assert max(js_errors+raw_errors)<tolerance;known=R.parent/'round11/execution/old-numerical-divergence.json';assert sha(known)==read(E/'numerical-divergence.json')['knownRound10Branch']['sha256']
old_js=[]
for _,gp,jp,_,n in specs:
 oldjp=E/str(jp).replace('new','old');v=read(oldjp);assert v['completeGenerationParity']and len(v['rows'])==n;old_js.append(dict(path=str(oldjp.relative_to(R)),sha256=sha(oldjp),sequences=n))
report=dict(newStateOutputs=84,newPythonJavascriptFullSequenceMatches=84,newRawFp32VersusSevenDecimalExportFullSequenceMatches=84,maxMeasuredNewPythonJavascriptReferenceLogitError=max(js_errors),maxMeasuredNewRawExportReferenceLogitError=max(raw_errors),unchangedTolerance=tolerance,referenceLogitsAreSampledNotAllStepsOrHardwareGuarantee=True,oldSelectedCurrentJavascriptScope=42,oldSelectedCurrentRawScope=25,oldOriginal17RawNotRerun=True,oldTerminalEvidenceHistorical=True,knownRound10NearTieReference=str(known.relative_to(R.parent)),knownRound10NearTieSha256=sha(known),knownRound10StrictSequenceParity='16/17 in historical diagnosis; not repaired or hidden',noOutputRepair=True,noWeightOrKernelChange=True,additionalOptimizerUpdates=0,groups=reports,oldSelectedJavascript=old_js)
(E/'final-numerical-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['groups','oldSelectedJavascript']}))
