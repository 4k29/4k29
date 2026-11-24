import pathlib,json,torch,hashlib,sys
repo=pathlib.Path('/workspace/4k29');R=repo/'training/language/round46';E=R/'execution';P=R.parent/'round44';sys.path.insert(0,str(R));from checkpoint_chunks import pack
torch.set_num_threads(1);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();f=E/'retained-snapshots/5000/checkpoint.pt';g=P/'execution/retained-snapshots/5000/checkpoint.pt';a=torch.load(g,map_location='cpu',weights_only=False);b=torch.load(f,map_location='cpu',weights_only=False)
assert a['step']==b['step']==5000 and {int(s['step'])for s in b['optimizer']['state'].values()}=={25000}
assert a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert a['seen_tokens']==b['seen_tokens'] and a['seen_bytes']==b['seen_bytes']
assert a['config']==b['config'] and a['history'][0]['validation']==b['history'][0]['validation']
assert a['settings']['contextPreference']['coefficient']==b['settings']['contextPreference']['coefficient']==.1
for ga,gb in zip(a['optimizer']['param_groups'],b['optimizer']['param_groups'],strict=True):
 assert ga['lr']==2.2499999999999998e-5 and gb['lr']==4.4999999999999996e-5
 ga,gb=dict(ga),dict(gb);gb['lr']=ga['lr'];assert ga==gb
assert all(torch.isfinite(v).all()for v in b['model'].values())
assert all(torch.isfinite(s[k]).all()for s in b['optimizer']['state'].values()for k in ['exp_avg','exp_avg_sq'])
for row in read(R/'source-manifest.json')['files']:assert (R/row['path']).stat().st_size==row['bytes'] and sha(R/row['path'])==row['sha256'],row['path']
for cp in [f]:pack(cp)
out=dict(actualCompletedUpdatesAtSnapshot=5000,adamCounter=25000,scientificControl='round44',oldLearningRate=2.2499999999999998e-5,newLearningRate=4.4999999999999996e-5,onlyOptimizerGroupLrDiffers=True,initialFullStateEquivalenceVerified=read(E/'initial-equivalence.json'),mainTargetsAndBytesExactlyMatch=True,targetTokens=b['seen_tokens'],targetBytes=b['seen_bytes'],pythonAndTorchRngExactlyMatch=True,finiteWeightsAndMoments=True,changedModelTensors=sum(not torch.equal(v,b['model'][k])for k,v in a['model'].items()),newSnapshotSha256=sha(f),controlSnapshotSha256=sha(g),frozenInputsVerified=len(read(R/'source-manifest.json')['files']),additionalOptimizerUpdatesByAudit=0,languageAssessmentNotYetPerformed=True)
(E/'paired-5000-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
