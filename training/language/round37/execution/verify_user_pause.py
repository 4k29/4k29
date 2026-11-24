"""Verify an explicitly requested partial stop without any optimizer or model forward."""
import pathlib,json,hashlib,random,datetime,importlib.util,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1)
p=R/'continue-10000/checkpoint.pt';c=torch.load(p,map_location='cpu',weights_only=False);result=read(R/'continue-10000/result.json');step=c['step'];assert step==7553==result['completedSteps']and not result['completedRun'];assert result['checkpointSha256']==sha(p);assert sorted({int(v['step'])for v in c['optimizer']['state'].values()})==[20000+step]
for key in ['model','beststate']:assert all(t.dtype==torch.float32 and torch.isfinite(t).all()for t in c[key].values())
for x in c['optimizer']['state'].values():assert all(torch.isfinite(x[k]).all()for k in ['exp_avg','exp_avg_sq'])
torch.Generator().set_state(c['torchRng']);random.Random().setstate(c['pythonRng']);events=[]
for line in (E/'train.log').read_text().splitlines():
 try:events.append(json.loads(line))
 except ValueError:pass
assert events[-2]==dict(event='interrupted',confirmedUpdates=step)and events[-1]['event']=='suspended'and events[-1]['completedUpdates']==step
spec=importlib.util.spec_from_file_location('resume_guard_for_pause',E/'execute.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);kept=m.retained_log((E/'train.log').read_text(),step);assert len([x for x in kept.splitlines()if 'trainingLoss'in json.loads(x)])==75
trace=[json.loads(s)for s in (R/'continue-10000/training-rollouts.jsonl').read_text().splitlines()];assert [x['step']for x in trace]==list(range(10,step+1,10));assert len(trace)==c['rolloutCalls']==755
for key,field in [('rolloutGeneratedTokens','generatedTokens'),('rolloutNegativePositions','negativePositions')]:assert c[key]==sum(x[field]for x in trace)
source=read(R/'source-manifest.json')
for x in source['files']:
 f=R/x['path'];assert f.stat().st_size==x['bytes']and sha(f)==x['sha256'],x['path']
assembled=[]
for name in ['checkpoint.pt','checkpoint-0.pt','best-aligned-checkpoint.pt']:
 raw=R/'continue-10000'/name;partsfile=raw.with_name(name+'.chunks.json');parts=read(partsfile);h=hashlib.sha256();total=0
 for x in parts['chunks']:
  data=(partsfile.parent/x['path']).read_bytes();assert len(data)==x['bytes']and hashlib.sha256(data).hexdigest()==x['sha256'];h.update(data);total+=len(data)
 assert total==raw.stat().st_size==parts['bytes']and h.hexdigest()==sha(raw)==parts['sha256'];assembled.append(dict(path=str(raw.relative_to(R)),sha256=sha(raw),bytes=total,chunksManifest=str(partsfile.relative_to(R))))
selected=read(E/'selected-optimizer-audit.json');assert selected['actualRetainedTrialUpdates']==step and selected['selectedStep']==c['beststep']==7500 and selected['selectedWeightsExactlyMatchLatestCheckpointBestState']
active=[]
for pid in [1562,1575,1564,1565,1566,1567,1569,1570,1646]:
 f=pathlib.Path(f'/proc/{pid}/stat')
 if f.exists()and f.read_text().rsplit(')',1)[1].strip().split()[0]!='Z':active.append(pid)
assert not active,active
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),userRequestedStop=True,actualCompletedUpdates=step,requestedUpdates=10000,remainingUpdates=10000-step,completedRun=False,optimizerCounters=[20000+step],selectedStep=c['beststep'],lastValidatedStep=c['history'][-1]['step'],bestCommonDevNll=c['bestloss'],checkpointSha256=sha(p),assembledCheckpoints=assembled,allWeightsAndMomentsFinite=True,torchAndPrivatePythonRngRestorable=True,allFrozenInputsUnmodified=len(source['files']),sourceManifestSha256=sha(R/'source-manifest.json'),retainedLogResumeGuardPassed=True,rolloutCalls=c['rolloutCalls'],rolloutGeneratedTokens=c['rolloutGeneratedTokens'],rolloutNegativePositions=c['rolloutNegativePositions'],seenTargetTokens=c['seen_tokens'],seenTargetUtf8Bytes=c['seen_bytes'],endEosPositions=c['endEosPositions'],activeOriginalMainCeTargetPositions=c['seen_tokens']-c['endEosPositions'],lastUpdateFinishedBeforeSignalStop=True,uncheckpointedPhysicalUpdatesUnknown=False,noTrainingOrWaitingProcessStillRunning=True,downstreamPipelineExitReason='10000-only replay_sampler completion guard rejected intentionally partial run; no full final generation assessment executed',genericMechanicalStatusUnknownFlagSupersededByConfirmedTrainerStop=True,finalFullGenerationAssessmentPending=True,publicModelChanged=False,newTest=False,additionalOptimizerUpdatesByThisAudit=0,resumeCommand='python training/language/round37/execution/supervise.py --resume',resumeStartsAt=step+1,doNotRestartWithoutResume=True,noResumeAuthorizedByCurrentStop=True,codeSha256=sha(pathlib.Path(__file__)))
(E/'user-pause-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
