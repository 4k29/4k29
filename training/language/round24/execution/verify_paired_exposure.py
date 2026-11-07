"""Only objective differs; verify paired exposure and RNG consumption exactly."""
import pathlib,json,torch
R=pathlib.Path(__file__).resolve().parents[1];torch.set_num_threads(1)
old=torch.load(R.parent/'round23/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
new=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
assert old['step']==new['step']==10000
assert old['config']==new['config']
a=old['settings']['unlikelihood'];b=new['settings']['unlikelihood'];assert a['coefficient']==.1 and b['coefficient']==1.0
assert {k:v for k,v in a.items() if k!='coefficient'}=={k:v for k,v in b.items() if k!='coefficient'}
assert old['pythonRng']==new['pythonRng'] and torch.equal(old['torchRng'],new['torchRng'])
assert old['seen_tokens']==new['seen_tokens'] and old['seen_bytes']==new['seen_bytes']
assert old['history'][0]['validation']==new['history'][0]['validation']
for k in ['genreSampling','trainingViews','validationViews','parentCheckpointSha256','preparedDataSha256']:
 assert old['settings'][k]==new['settings'][k],k
record=dict(actualUpdatesEach=10000,sameInitialDevelopmentExactly=True,sameDataAndParent=True,sameFinalPythonSamplerRng=True,sameFinalTorchRng=True,exactlySameTargetTokens=new['seen_tokens'],exactlySameTargetBytes=new['seen_bytes'],objectiveOnlyIntervention=True)
(R/'execution/paired-exposure.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
