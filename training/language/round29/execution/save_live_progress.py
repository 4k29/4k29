"""Read-only copy of one atomic retained full state; never stop or mutate live training.
Added operationally after launch, not used by the frozen training/evaluation core.
"""
import datetime,hashlib,io,json,pathlib,sys,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));from checkpoint_chunks import pack
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();torch.set_num_threads(1)
raw=(R/'continue-10000/checkpoint.pt').read_bytes();cp=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);step=cp['step'];assert 0<step<10000,'Requires partial positive retained actual updates'
assert sorted({int(s['step']) for s in cp['optimizer']['state'].values()})==[10000+step]
assert cp['settings']['experimentPolicySha256']==sha(R/'policy.json') and cp['settings']['trainerSourceSha256']==sha(R/'train.py')
for key in ['model','beststate']:assert all(torch.isfinite(v).all() for v in cp[key].values())
for s in cp['optimizer']['state'].values():assert all(torch.isfinite(s[k]).all() for k in ['exp_avg','exp_avg_sq'])
trace=[]
for line in (R/'continue-10000/training-rollouts.jsonl').read_text().splitlines(keepends=True):
 if line.endswith('\n'):
  row=json.loads(line)
  if row['step']<=step:trace.append(row)
assert [r['step'] for r in trace]==list(range(10,step+1,10));assert len(trace)==cp['rolloutCalls'];assert sum(r['generatedTokens'] for r in trace)==cp['rolloutGeneratedTokens'];assert sum(r['negativePositions'] for r in trace)==cp['rolloutNegativePositions']
logs=[]
for line in (E/'train.log').read_text().splitlines(keepends=True):
 if line.endswith('\n'):
  row=json.loads(line)
  if row.get('step',10001)<=step:logs.append(row)
assert [r['step'] for r in logs if 'trainingLoss' in r]==list(range(100,step+1,100)),'Retry after matching log event is flushed'
out=E/f'retained-progress-{step}';out.mkdir(exist_ok=False);path=out/'checkpoint.pt';path.write_bytes(raw);manifest=pack(path);assert json.loads(manifest.read_text())['sha256']==hashlib.sha256(raw).hexdigest();path.unlink()
for filename,rows in [('train.log',logs),('training-rollouts.jsonl',trace)]:
 (out/filename).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualRetainedUpdates=step,requestedUpdates=10000,trainingCompleted=False,liveTrainingContinues=True,liveTrainerNotSignaledOrModified=True,optimizerCounters=[10000+step],fullAlignedLatestModelOptimizerAndRngSaved=True,selectedWeightsNeverMixedWithLatestMoments=True,checkpointSha256=hashlib.sha256(raw).hexdigest(),checkpointBytes=len(raw),checkpointChunksManifest='checkpoint.pt.chunks.json',policySha256=sha(R/'policy.json'),sourceManifestSha256=sha(R/'source-manifest.json'),saveHelperSha256=sha(pathlib.Path(__file__)),bestSelectedStep=cp['beststep'],bestDevelopmentNll=cp['bestloss'],seenTargetTokens=cp['seen_tokens'],seenTargetUtf8Bytes=cp['seen_bytes'],rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],semanticReviewOfFinalModelPending=True,recovery='Only if original controller/trainer is absent and no newer checkpoint exists: restore these chunks with checkpoint_chunks.py, copy restored checkpoint.pt and retained trace/log to the original run paths, restore original checkpoint-0 parts, then persistent.sh --resume. Never overwrite newer retained work or restore only selected weights. Reconstructed source data/manifest must still match.')
(out/'snapshot.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
