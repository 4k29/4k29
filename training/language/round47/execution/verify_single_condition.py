"""Verify the complete policy/code delta and static evaluation executable closure."""
import pathlib,json,hashlib,copy,re,subprocess
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round46';E=R/'execution';repo=R.parents[2]
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a,b=read(P/'policy.json'),read(R/'policy.json');assert a['sequenceUnlikelihood']['coefficient']==.1 and b['sequenceUnlikelihood']['coefficient']==.2;assert a['learningRate']==b['learningRate']==4.4999999999999996e-5;assert a['contextPreference']['coefficient']==b['contextPreference']['coefficient']==.1
x,y=copy.deepcopy(a),copy.deepcopy(b);y['sequenceUnlikelihood']['coefficient']=a['sequenceUnlikelihood']['coefficient']
for k in ['experiment','rationale','controlManifestSha256','nllSuccessThreshold','sourcePolicySha256']:x.pop(k,None);y.pop(k,None)
assert x==y,'Other policy configuration changed'
for n in b['codeHashes']:assert (R/n).read_bytes()==(P/n).read_bytes(),n
assert len(b['codeHashes'])==10
required={E/'diagnose_parity.mjs',R.parent/'round10/evaluate.py',R.parent/'round10/evaluate_js.mjs',R.parent/'round10/review.py'}
compiled=0;shells=0
for p in R.rglob('*'):
 if not p.is_file()or '__pycache__'in p.parts:continue
 if p.suffix=='.py':compile(p.read_text(),str(p),'exec');compiled+=1
 if p.suffix=='.sh':subprocess.run(['bash','-n',str(p)],check=True);shells+=1
 if p.suffix in ['.py','.sh','.mjs']:
  for rel in re.findall(r'training/language/round47/[A-Za-z_0-9./-]+\.(?:py|sh|mjs)',p.read_text()):required.add(repo/rel)
for p in required:assert p.is_file(),'Missing static executable: '+str(p)
subprocess.run(['node','--check',str(E/'diagnose_parity.mjs')],check=True)
for rel in re.findall(r"from ['\"](\.[^'\"]+)['\"]",(E/'diagnose_parity.mjs').read_text()):assert (E/rel).resolve().is_file(),rel
out=dict(actualOptimizerUpdates=0,onlyPolicyLearningDelta='sequenceUnlikelihood.coefficient0.1 to0.2',allOtherPolicyFieldsExactlyMatchExceptDeclaredMetadata=True,allTenCoreLearningFilesByteIdentical=True,mainSamplingUnchanged=True,poolSha256=b['contextPreference']['poolSha256'],pythonSourcesCompiled=compiled,shellSourcesSyntaxChecked=shells,requiredStaticExecutablesChecked=len(required),diagnoseParityMjsPresentAndSyntaxChecked=True,notAFormalDynamicClosureProof=True,noModelForwardOrOptimizerByThisAudit=True,sourceHashes={str(p.relative_to(repo)):sha(p)for p in sorted(required)})
(E/'single-condition-and-executable-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='sourceHashes'}))
