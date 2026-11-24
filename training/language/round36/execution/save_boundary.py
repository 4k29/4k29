import pathlib,json,hashlib,datetime,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(E/'optimizer-audit.json');assert a['actualCompletedUpdates']==10000 and a['optimizerCounters']==[30000]
source=read(R/'source-manifest.json')
for x in source['files']:assert sha(R/x['path'])==x['sha256'],x['path']
keys=['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens'];paths=[('original17',17,'new-validation.json','new-validation-js.json','export-rounding.json'),('daily12',12,'daily-new-python.json','daily-new-javascript.json','daily-new-unrounded.json'),('native8',8,'content-native-dev/new-python.json','content-native-dev/new-javascript.json','content-native-dev/new-rounding.json'),('mrmp5',5,'fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-javascript.json','fixed-source-mrmp-dev/new-unrounded.json')];parity=[]
for state in ['selected','terminal']:
 for group,n,g,j,u in paths:
  ps=[E/g,E/j,E/u]if state=='selected'else[E/'terminal-state-diagnostic'/f'{group}-{v}.json'for v in ['python','javascript','unrounded']]
  ds=[read(p)for p in ps];assert all(len(d['rows'])==n for d in ds)
  counts=[sum(all(x[k]==y[k]for k in keys)for x,y in zip(ds[0]['rows'],ds[i]['rows'],strict=True))for i in [1,2]]
  assert counts==[n,n]and ds[1]['completeGenerationParity']
  parity.append(dict(state=state,group=group,total=n,pythonJavascriptMatching=counts[0],rawRoundedMatching=counts[1],generationSha256=sha(ps[0])))
assembled=[]
for p in sorted(R.rglob('*.pt.chunks.json')):
 m=read(p);h=hashlib.sha256();size=0
 for x in m['chunks']:
  b=(p.parent/x['path']).read_bytes();assert len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256'];h.update(b);size+=len(b)
 assert size==m['bytes']and h.hexdigest()==m['sha256']
 assembled.append(dict(manifest=str(p.relative_to(R)),sha256=m['sha256'],bytes=size))
assert len(assembled)==6
status=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boundaryRequestedByUser=True,actualCompletedUpdates=10000,selectedStep=8000,optimizerCounters=[30000],selectedOptimizerCounters=[28000],commonDevNll=a['bestWeightedDevelopmentNllPerByte'],humanDevNll=read(E/'daily-human-new-likelihood.json')['nllPerSerializedUtf8Byte'],fullSemanticReviewPending=True,newSemanticScoresAssigned=False,adoptionPendingFullReview=True,publicModelChanged=False,nextRoundStarted=False,all168RawStateOutputsSaved=True,newNumericalParity=parity,verifiedCheckpointStates=assembled,frozenInputsVerified=len(source['files']),sourceManifestSha256=sha(R/'source-manifest.json'),additionalOptimizerUpdatesByBoundarySave=0)
(E/'boundary-status.json').write_text(json.dumps(status,indent=2)+'\n')
(R/'README.md').write_text('''# Round36 — completed training; semantic review pending\n\nActual additional optimizer updates: **10000/10000**. The run has finished, with Adam counter30000. The predeclared common-DEV selector chose actual8000 with aligned Adam28000; selected and terminal model/optimizer/RNG states are saved separately. Only EOS auxiliary coefficient1.0→0.3 changed against Round35; both trials used the same aligned Round28 parent and fixed remaining settings.\n\nSelected common DEV NLL/byte:0.9677411390068936 (Round35:0.9678213304515457). Human DEV99 NLL/serialized byte:0.9073871096397005 (Round35:0.9107185711429243). These are exposed DEV diagnostics, not a new TEST or proof of improved Japanese meaning.\n\nAll168 old/new selected/terminal full state outputs are saved in [execution/MECHANICAL_ALL_FOUR_STATE_GENERATIONS.md](execution/MECHANICAL_ALL_FOUR_STATE_GENERATIONS.md). New selected42 and terminal42 full sequences each match Python/JavaScript and raw/rounded inference in the measured scope. The known historical Round10 numerical divergence remains recorded; this does not establish universal parity.\n\n**Full semantic reading and strict language-gate judgment are pending.** No semantic score has been invented, no model has been newly adopted, and the public model/site is unchanged. At the user's request this is a stopping boundary: no Round37 has started.\n\n[execution/boundary-status.json](execution/boundary-status.json) records verified states and numerical scope. [execution/boundary-artifact-manifest.json](execution/boundary-artifact-manifest.json) hashes saved artifacts; it is a handoff manifest, not a completed language assessment. [REPRODUCTION.md](REPRODUCTION.md), [HYPOTHESES.md](HYPOTHESES.md) and [EOS_LOCATION_DIAGNOSTIC.md](EOS_LOCATION_DIAGNOSTIC.md) preserve reproduction and bounded analysis. Do not retrain the completed10000 updates.\n\nNext work: read all42 new selected and42 new terminal full prefixes/continuations, bind actual judgments to generation hashes, compare the unchanged strict gates and daily guardrails, then finish the assessment and final artifact manifest. Do not run the pending-reading finalizer before that work.\n''')
files=[]
for p in sorted(R.rglob('*')):
 if not p.is_file()or '__pycache__'in p.parts or p.suffix in ['.pt','.pyc','.tmp']or p.name in ['train.tokens.bin','.training.lock','.controller.lock','boundary-artifact-manifest.json']:continue
 files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(actualCompletedUpdates=10000,languageAssessmentComplete=False,semanticReadingPending=True,nextRoundStarted=False,files=files,assembledCheckpoints=assembled,frozenTrainingInputs=source['files'],sourceManifestSha256=sha(R/'source-manifest.json'))
(E/'boundary-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
subprocess.run(['git','add','--',*[str(R/x['path'])for x in files],str(E/'boundary-artifact-manifest.json')],cwd=R.parents[2],check=True)
print(json.dumps(dict(actualCompletedUpdates=10000,verifiedFullStates=len(assembled),files=len(files),newFullSequencesMatching=84,semanticReadingPending=True,nextRoundStarted=False)))
