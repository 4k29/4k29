"""Data-mixture treatment: compare actual exposures without asserting equal draws/RNG."""
import pathlib,json,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());torch.set_num_threads(1)
control=read(E/'creation-context.json')['scientificControl'];old=torch.load(R.parent/control/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);new=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
assert old['step']==new['step']==10000 and old['config']==new['config']
assert old['settings']['unlikelihood']==new['settings']['unlikelihood']
assert old['settings'].get('sequenceUnlikelihood')==new['settings'].get('sequenceUnlikelihood')
assert old['history'][0]['validation']==new['history'][0]['validation']
assert new['settings']['genreSampling']['human-chat']==.3
for k,v in old['settings']['genreSampling'].items():assert abs(new['settings']['genreSampling'][k]-.7*v)<1e-15
for k in ['trainingViews','validationViews','parentCheckpointSha256','lr','batch','threads','precision','seed']:assert old['settings'][k]==new['settings'][k]
record=dict(actualUpdatesEach=10000,sameInitialDevelopmentExactly=True,sameModelObjectiveAndParent=True,oneCorpusMixtureFactor=True,sameFinalPythonSamplerRng=old['pythonRng']==new['pythonRng'],sameFinalTorchRng=torch.equal(old['torchRng'],new['torchRng']),actualExposures={k:dict(targetTokens=x['seen_tokens'],targetBytes=x['seen_bytes']) for k,x in [('old',old),('new',new)]},exposureEqualityRequired=False,reason='Adding corpus mass changes rows/bucket widths/positives and naturally dropout RNG consumption; independent own sampler replay verifies actual counts. Do not label data comparison an equal-exposure objective intervention.')
(E/'paired-exposure.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
