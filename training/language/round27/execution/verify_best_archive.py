"""Verify a captured selected-step full state; never fabricate missing moments/RNG."""
import hashlib,json,pathlib,random,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R/'continue-10000';torch.set_num_threads(1)
cp=torch.load(P/'checkpoint.pt',map_location='cpu',weights_only=False);path=P/'best-aligned-checkpoint.pt';meta=E/'best-aligned-archive.json'
record=dict(actualRetainedTrialUpdates=cp['step'],selectedStep=cp['beststep'],selectedFullStateAvailable=False,additionalOptimizerUpdates=0,existingTrialResumeCheckpoint='continue-10000/checkpoint.pt',selectedWeightsNeverMixedWithLatestMoments=True)
if path.exists() and meta.exists():
 info=json.loads(meta.read_text());raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==info['checkpointSha256']
 best=torch.load(path,map_location='cpu',weights_only=False)
 if best['step']==cp['beststep']:
  assert best['beststep']==best['step'] and best['settings']==cp['settings'] and best['config']==cp['config']
  assert all(torch.equal(v,cp['beststate'][k]) and torch.equal(v,best['beststate'][k]) for k,v in best['model'].items())
  counters=sorted({int(s['step']) for s in best['optimizer']['state'].values()});assert counters==[10000+best['step']]
  names=list(best['model']);groups=best['optimizer']['param_groups'];assert len(groups)==1 and len(groups[0]['params'])==len(names)
  for name,ident in zip(names,groups[0]['params'],strict=True):
   s=best['optimizer']['state'][ident]
   for key in ['exp_avg','exp_avg_sq']:assert s[key].shape==best['model'][name].shape and torch.isfinite(s[key]).all()
  rng=random.Random();rng.setstate(best['pythonRng']);assert rng.getstate()==best['pythonRng'];torch.set_rng_state(best['torchRng']);assert torch.equal(torch.get_rng_state(),best['torchRng'])
  record.update(selectedFullStateAvailable=True,selectedSnapshotActualUpdates=best['step'],selectedOptimizerCounters=counters,selectedWeightsExactlyMatchLatestCheckpointBestState=True,allMomentShapesAndValuesFinite=True,torchAndPrivatePythonRngRestorable=True,selectedCheckpointSha256=hashlib.sha256(raw).hexdigest())
 else:record['limitation']='Captured older selected state does not match final selected step; do not use it as final selected optimizer state.'
else:record['limitation']='Selected-step optimizer/RNG was not captured; use latest aligned checkpoint for exact continuation, not selected weights plus latest moments.'
(E/'selected-optimizer-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
