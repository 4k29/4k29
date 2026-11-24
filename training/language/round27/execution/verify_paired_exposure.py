"""Capacity only: data/objective and both actual positive streams remain matched."""
import pathlib,json,torch
R=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text());C=R.parent/read(R/'execution/creation-context.json')['scientificControl'];torch.set_num_threads(1)
a=torch.load(C/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);b=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
assert a['step']==b['step']==10000 and a['config']['hidden']==768 and b['config']['hidden']==1536
assert {k:v for k,v in a['config'].items() if k!='hidden'}=={k:v for k,v in b['config'].items() if k!='hidden'}
for k in ['unlikelihood','sequenceUnlikelihood','genreSampling','trainingViews','validationViews','parentCheckpointSha256','preparedDataSha256','lr','batch','threads','precision','seed']:
 assert a['settings'].get(k)==b['settings'].get(k),k
assert a['pythonRng']==b['pythonRng'] and torch.equal(a['torchRng'],b['torchRng'])
assert a['seen_tokens']==b['seen_tokens'] and a['seen_bytes']==b['seen_bytes']
initial_delta=abs(a['history'][0]['validation']['nllPerUtf8Byte']-b['history'][0]['validation']['nllPerUtf8Byte']);assert initial_delta<=5e-7
record=dict(actualUpdatesEach=10000,onlyFfnHiddenChanged=True,sameDataObjectiveAndParent=True,sameFinalPythonSamplerRng=True,sameFinalTorchRng=True,exactlySameTargetTokens=b['seen_tokens'],exactlySameTargetBytes=b['seen_bytes'],initialNllDifference=initial_delta,initialFunctionTolerance=5e-7)
(R/'execution/paired-exposure.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
