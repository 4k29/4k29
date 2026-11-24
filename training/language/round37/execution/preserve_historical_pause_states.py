"""Rewrap historical pause manifests; no weights, optimizer or training changes."""
import pathlib,json,hashlib,subprocess,copy
R=pathlib.Path(__file__).resolve().parents[1];repo=R.parents[2];revision='aa60811827d5adf4de1602cbe1e71f13ebe6b9a8';sha=lambda b:hashlib.sha256(b).hexdigest();records=[]
for original,filename,step in [('checkpoint.pt','checkpoint-user-pause-7553.pt',7553),('best-aligned-checkpoint.pt','checkpoint-user-pause-selected-7500.pt',7500)]:
 gitpath=str((R/'continue-10000'/(original+'.chunks.json')).relative_to(repo));raw=subprocess.check_output(['git','show',revision+':'+gitpath],cwd=repo);old=json.loads(raw);m=copy.deepcopy(old);m['filename']=filename;h=hashlib.sha256();total=0
 for x in m['chunks']:
  p=R/'continue-10000'/x['path'];b=p.read_bytes();assert len(b)==x['bytes']and sha(b)==x['sha256'];h.update(b);total+=len(b)
 assert h.hexdigest()==m['sha256']and total==m['bytes'];out=R/'continue-10000'/(filename+'.chunks.json');out.write_text(json.dumps(m,indent=2)+'\n');assert {k:v for k,v in m.items()if k!='filename'}=={k:v for k,v in old.items()if k!='filename'}
 records.append(dict(historicalActualUpdates=step,optimizerCounter=20000+step,path=str((out.parent/filename).relative_to(R)),sha256=m['sha256'],bytes=m['bytes'],chunksManifest=str(out.relative_to(R)),historicalPauseOnly=True,sourceGitRevision=revision,sourceGitManifest=gitpath,sourceGitManifestSha256=sha(raw),rewrappedManifestSha256=sha(out.read_bytes()),onlyManifestFilenameChanged=True,allOriginalChunkBytesVerified=True))
(R/'execution/historical-pause-state-integrity.json').write_text(json.dumps(dict(states=records,noRawCheckpointOverwrite=True,noModelOrOptimizerCalls=True,additionalOptimizerUpdates=0,codeSha256=sha(pathlib.Path(__file__).read_bytes())),indent=2)+'\n');print(json.dumps(records))
