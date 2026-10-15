"""Verify zero additional updates retain the exact latest parent trajectory state."""
import pathlib,json,torch
ROOT=pathlib.Path(__file__).resolve().parents[1];torch.set_num_threads(1)
a=torch.load(ROOT/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False)
b=torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
assert a['step']==0 and b['step']==10000 and a['seen_tokens']==a['seen_bytes']==0
assert a['config']==b['config'] and a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert all(torch.equal(v,b['model'][k]) for k,v in a['model'].items())
assert a['optimizer']['param_groups']==b['optimizer']['param_groups']
for key,state in a['optimizer']['state'].items():
 for name,t in state.items():assert torch.equal(t,b['optimizer']['state'][key][name])
assert a['history'][0]['validation']==b['history'][-1]['validation']
record=dict(initialWeightsExactlyEqualToRound11Latest=True,initialTorchAndPythonRngExactlyEqual=True,initialAdamWMomentsAndGroupsExactlyEqual=True,allDevelopmentViewsAndSitesExactlyEqual=True,optimizerCountersAtSnapshot=[10000],additionalOptimizerUpdatesAtSnapshot=0,latestStateNotBestStateMixedWithLatestOptimizer=True)
(ROOT/'execution/initial-equivalence.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
