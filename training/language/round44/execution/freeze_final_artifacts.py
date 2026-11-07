"""Freeze final actual results, all six aligned full states and immutable inputs."""
import pathlib,json,hashlib,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));from checkpoint_chunks import pack
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=read(E/'final-assessment.json');assert a['actualCompletedUpdates']==10000 and not a['fullOutputReviewPending'];inputs=read(R/'source-manifest.json')['files']
for row in inputs:assert sha(R/row['path'])==row['sha256'],row['path']
checkpoints=[]
for name,path,step in [('initial',R/'continue-10000/checkpoint-0.pt',0),('retained200',E/'retained-snapshots/200/checkpoint.pt',200),('retained1000',E/'retained-snapshots/1000/checkpoint.pt',1000),('retained5000',E/'retained-snapshots/5000/checkpoint.pt',5000),('selected',R/'continue-10000/best-aligned-checkpoint.pt',a['selectedStep']),('latest',R/'continue-10000/checkpoint.pt',10000)]:
 manifest=pack(path);record=read(manifest);checkpoints.append(dict(role=name,path=str(path.relative_to(R)),actualSnapshotUpdates=step,optimizerCounter=20000+step,sha256=record['sha256'],bytes=record['bytes'],chunksManifest=str(manifest.relative_to(R))))
data=R/'multiview/train.tokens.bin';dm=data.with_name(data.name+'.chunks.json');assert read(dm)['sha256']==sha(data);assembled_data=[dict(path=str(data.relative_to(R)),sha256=sha(data),bytes=data.stat().st_size,chunksManifest=str(dm.relative_to(R)))];raw={x['path']for x in checkpoints+assembled_data};files=[]
for p in sorted(R.rglob('*')):
 if not p.is_file()or '__pycache__'in p.parts or p.name in ['artifact-manifest.json','.training.lock','.controller.lock']or p.name.endswith('.tmp'):continue
 rel=str(p.relative_to(R))
 if rel in raw:continue
 files.append(dict(path=rel,sha256=sha(p),bytes=p.stat().st_size))
manifest=dict(schemaVersion=2,actualCompletedUpdates=10000,requestedUpdates=10000,selectedStep=a['selectedStep'],semanticAssessmentComplete=True,adopted=a['adopted'],newTestGenerated=False,publicModelChanged=False,files=files,inputs=inputs,assembledCheckpoints=checkpoints,assembledData=assembled_data,finalAssessmentSha256=sha(E/'final-assessment.json'),fullTextAssemblySha256=sha(E/'ALL_FOUR_STATE_GENERATIONS.md'))
(E/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(files=len(files),frozenInputs=len(inputs),fullAlignedStates=len(checkpoints),actualUpdates=10000)))
