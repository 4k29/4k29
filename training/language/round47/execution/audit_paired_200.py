"""Read-only paired saved-state audit; restore/reclaim archived old raw duplicate only."""
import pathlib,json,torch,hashlib,sys
repo=pathlib.Path('/workspace/4k29');R=repo/'training/language/round47';E=R/'execution';P=R.parent/'round46';sys.path.insert(0,str(R));from checkpoint_chunks import pack,restore
torch.set_num_threads(1);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();f=E/'retained-snapshots/200/checkpoint.pt';g=P/'execution/retained-snapshots/200/checkpoint.pt';assert f.exists();temporary_restore=not g.exists()
if temporary_restore:restore(g.with_name(g.name+'.chunks.json'))
a=torch.load(g,map_location='cpu',weights_only=False);b=torch.load(f,map_location='cpu',weights_only=False)
assert a['step']==b['step']==200 and {int(s['step'])for s in b['optimizer']['state'].values()}=={20200}
assert a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert a['seen_tokens']==b['seen_tokens'] and a['seen_bytes']==b['seen_bytes']
assert a['config']==b['config'] and a['history'][0]['validation']==b['history'][0]['validation']
assert a['settings']['contextPreference']['coefficient']==b['settings']['contextPreference']['coefficient']==.1
assert a['settings']['sequenceUnlikelihood']['coefficient']==.1 and b['settings']['sequenceUnlikelihood']['coefficient']==.2
assert a['optimizer']['param_groups']==b['optimizer']['param_groups'] and all(g['lr']==4.4999999999999996e-5 for g in b['optimizer']['param_groups'])
assert all(torch.isfinite(v).all()for v in b['model'].values()) and all(torch.isfinite(s[k]).all()for s in b['optimizer']['state'].values()for k in ['exp_avg','exp_avg_sq'])
for row in read(R/'source-manifest.json')['files']:assert (R/row['path']).stat().st_size==row['bytes'] and sha(R/row['path'])==row['sha256'],row['path']
for cp in [R/'continue-10000/checkpoint-0.pt',f]:pack(cp)
out=dict(actualCompletedUpdatesAtSnapshot=200,adamCounter=20200,scientificControl='round46',oldSequenceUlCoefficient=.1,newSequenceUlCoefficient=.2,learningRateBoth=4.4999999999999996e-5,optimizerParamGroupsExactlyEqual=True,initialFullStateEquivalenceVerified=read(E/'initial-equivalence.json'),mainTargetsAndBytesExactlyMatch=True,targetTokens=b['seen_tokens'],targetBytes=b['seen_bytes'],pythonAndTorchRngExactlyMatch=True,finiteWeightsAndMoments=True,changedModelTensors=sum(not torch.equal(v,b['model'][k])for k,v in a['model'].items()),newSnapshotSha256=sha(f),controlSnapshotSha256=sha(g),frozenInputsVerified=len(read(R/'source-manifest.json')['files']),oldControlRawTemporarilyRestoredFromVerifiedLosslessParts=temporary_restore,oldControlRawDuplicateReclaimedAfterAudit=temporary_restore,additionalOptimizerUpdatesByAudit=0,languageAssessmentNotYetPerformed=True)
if temporary_restore:assert sha(g)==out['controlSnapshotSha256'];g.unlink()
(E/'paired-200-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
