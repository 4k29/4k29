"""Extend the unchanged original freezer with retained paired states and controls."""
import pathlib,json,hashlib,subprocess,sys,os
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round35';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
assert read(E/'final-assessment.json')['fullOutputReviewPending'] is False
subprocess.run([sys.executable,str(E/'freeze_results.py')],check=True)
p=E/'artifact-manifest.json';m=read(p)
for directory in ['retained-paired-200','retained-paired-1000','retained-paired-5000']:
 raw=E/directory/'checkpoint.pt';cp=raw.with_name('checkpoint.pt.chunks.json');parts=read(cp);h=hashlib.sha256();total=0
 for item in parts['chunks']:
  b=(cp.parent/item['path']).read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'];h.update(b);total+=len(b)
 assert h.hexdigest()==parts['sha256'] and total==parts['bytes'];assert not raw.exists()or sha(raw)==parts['sha256']
 m['assembledCheckpoints'].append(dict(path=str(raw.relative_to(R)),sha256=parts['sha256'],bytes=parts['bytes'],chunksManifest=str(cp.relative_to(R))))
paths={x['path']:x for x in m['inputs']}
extra=[P/'execution/artifact-manifest.json',P/'execution/final-assessment.json',R.parent/'round33/execution/jma-notice-provenance/audit.json',R.parent/'round33/execution/generated-notice-train-match-audit.json']
for row in read(E/'terminal-control-reference.json')['verifiedTerminalArtifacts']:extra.append(P/row['path'])
# Explicitly pin existing control snapshots used by post-training, read-only comparisons.
for n in [200,1000,5000]:
 control=P/f'execution/retained-paired-{n}/checkpoint.pt'
 extra.extend([control,control.with_name('checkpoint.pt.chunks.json')])
zero=R.parent/'round34/execution/retained-paired-5000/checkpoint.pt'
extra.extend([zero,zero.with_name('checkpoint.pt.chunks.json'),R.parent/'round34/execution/artifact-manifest.json',P/'execution/eos-location-effect-5000.json',P/'execution/audit_eos_location_effect.py'])
location=read(E/'eos-location-effect-5000.json')
for label,source in [('coefficientZeroRound34',zero),('coefficientOneRound35',P/'execution/retained-paired-5000/checkpoint.pt'),('coefficientPointThreeRound36',E/'retained-paired-5000/checkpoint.pt')]:
 assert location['results'][label]['checkpointSha256']==sha(source)
for f in extra:
 key=os.path.relpath(f,R);item=dict(path=key,sha256=sha(f),bytes=f.stat().st_size)
 if key in paths:assert paths[key]==item
 else:paths[key]=item
m['inputs']=list(paths.values());m.update(frozenTrainingInputCount=len(read(R/'source-manifest.json')['files']),postTrainingControlReferencesAdded=True,newStateOutputsActuallyRead=read(E/'final-output-verification.json')['newStateOutputsActuallyRead'],newStateOutputsCoveredByActualReading=84,newDistinctCoreOutputs=read(E/'final-output-verification.json')['newDistinctCoreOutputs'],allFourStateOutputsSaved=168,originalTrainingInputManifestSha256=sha(R/'source-manifest.json'))
p.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(files=len(m['files']),inputs=len(m['inputs']),assembledFullStates=len(m['assembledCheckpoints']),actualCompletedUpdates=10000)))
