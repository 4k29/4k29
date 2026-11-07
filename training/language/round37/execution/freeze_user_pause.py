"""Freeze the actual partial-stop tree, never label it completed10000."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=read(E/'user-pause-verification.json');assert a['actualCompletedUpdates']==7553 and a['remainingUpdates']==2447 and a['noTrainingOrWaitingProcessStillRunning']
manifest=E/'paused-artifact-manifest.json';excluded={'checkpoint.pt','checkpoint-0.pt','best-aligned-checkpoint.pt','train.tokens.bin','.training.lock','.controller.lock','artifact-manifest.json'};files=[]
for p in sorted(R.rglob('*')):
 if p.is_file()and p!=manifest and '__pycache__'not in p.parts and p.name not in excluded and not p.name.endswith('.tmp'):files.append(dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size))
assembled=list(a['assembledCheckpoints'])
for n in [200,1000,5000]:
 p=E/f'retained-paired-{n}/checkpoint.pt.chunks.json';d=read(p);assembled.append(dict(path=str((p.parent/'checkpoint.pt').relative_to(R)),sha256=d['sha256'],bytes=d['bytes'],chunksManifest=str(p.relative_to(R))))
for row in assembled:
 p=R/row['chunksManifest'];d=read(p);h=hashlib.sha256();total=0
 for x in d['chunks']:
  b=(p.parent/x['path']).read_bytes();assert len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256'];h.update(b);total+=len(b)
 assert h.hexdigest()==row['sha256']==d['sha256']and total==row['bytes']==d['bytes']
m=dict(actualCompletedUpdates=7553,requestedUpdates=10000,completedRun=False,remainingUpdates=2447,userRequestedStop=True,finalFullLanguageAssessmentPending=True,files=files,inputs=read(R/'source-manifest.json')['files'],assembledCheckpoints=assembled,userPauseVerificationSha256=sha(E/'user-pause-verification.json'),originalFrozenSourceManifestSha256=sha(R/'source-manifest.json'),currentPausedTreeOnly=True,supersededAfterAnyFutureAuthorizedResume=True,publicModelChanged=False,newTest=False)
manifest.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(files=len(files),inputs=len(m['inputs']),fullStates=len(assembled),actualUpdates=7553)))
