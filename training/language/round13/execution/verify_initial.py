import pathlib,json,hashlib,torch
ROOT=pathlib.Path(__file__).resolve().parents[1];torch.set_num_threads(1)
a=torch.load(ROOT/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);b=torch.load(ROOT.parent/'round11/continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False)
assert a['step']==b['step']==0 and not a['optimizer']['state']
assert a['config']==b['config'] and a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert all(torch.equal(v,b['model'][k]) for k,v in a['model'].items())
assert a['history'][0]['validation']==b['history'][0]['validation']
(ROOT/'execution/initial-equivalence.json').write_text(json.dumps(dict(initialWeightsExactlyEqualToRound11=True,initialTorchAndPythonRngExactlyEqual=True,allDevelopmentViewsAndSitesExactlyEqual=True,freshOptimizer=True,optimizerUpdatesAtSnapshot=0),indent=2)+'\n')
print('Initial weights, RNG and all development measurements match Round11')
