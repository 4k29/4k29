"""Read-only audit of already-retained immutable equal-update snapshots."""
import pathlib,sys,json,torch,hashlib
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round42';step=int(sys.argv[1]);torch.set_num_threads(1)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ap=P/f'execution/retained-snapshots/{step}/checkpoint.pt';bp=R/f'execution/retained-snapshots/{step}/checkpoint.pt';control_manifest=json.loads((P/'execution/artifact-manifest.json').read_text());expected=next(x for x in control_manifest['assembledCheckpoints']if x['path']==str(ap.relative_to(P)));assert sha(ap)==expected['sha256'];a=torch.load(ap,map_location='cpu',weights_only=False);b=torch.load(bp,map_location='cpu',weights_only=False)
assert a['step']==b['step']==step and a['config']==b['config']
assert a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert a['seen_tokens']==b['seen_tokens'] and a['seen_bytes']==b['seen_bytes']
assert a['settings']['genreSampling']==b['settings']['genreSampling']
assert a['contextPreferenceCalls']==b['contextPreferenceCalls']==step//10 and a['contextPreferencePairs']==b['contextPreferencePairs']==2*(step//10)
assert all(torch.isfinite(t).all()for t in b['model'].values())
assert {int(v['step'])for v in b['optimizer']['state'].values()}=={20000+step}
assert all(torch.isfinite(v[k]).all()for v in b['optimizer']['state'].values()for k in ['exp_avg','exp_avg_sq'])
if step<=1280:
 assert all(torch.equal(v,a['model'][k]) for k,v in b['model'].items())
 for k,v in b['optimizer']['state'].items():
  for name,t in v.items():assert torch.equal(t,a['optimizer']['state'][k][name])
record=dict(actualUpdatesEach=step,mainPythonAndTorchRngExactlyMatch=True,mainPositiveTargetTokensExactlyMatch=b['seen_tokens'],mainPositiveTargetBytesExactlyMatch=b['seen_bytes'],auxCallsEach=step//10,auxPairsEach=2*(step//10),allWeightsAndMomentsFinite=True,maxWeightAbsoluteDifference=max(float((v-a['model'][k]).abs().max())for k,v in b['model'].items()),scientificControl='round42',weightDifferenceIsNotLanguageImprovement=True,additionalOptimizerUpdates=0,oldCheckpointSha256=sha(ap),newCheckpointSha256=sha(bp))
(R/f'execution/paired-{step}-state-audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
