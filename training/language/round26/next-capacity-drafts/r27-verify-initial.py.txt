"""Verify function-preserving own-FFN expansion at zero additional updates."""
import pathlib,sys,json,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from capacity_audit import verify_initial_expansion
torch.set_num_threads(1);a=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);b=torch.load(R.parent/'round11/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
record=verify_initial_expansion(a,b);assert a['seen_tokens']==a['seen_bytes']==0
new=a['history'][0]['validation'];old=b['history'][-1]['validation'];deltas=[abs(new['nllPerUtf8Byte']-old['nllPerUtf8Byte'])]
for view in ['0','1','2']:
 deltas.append(abs(new['views'][view]['nllPerUtf8Byte']-old['views'][view]['nllPerUtf8Byte']))
 for site,value in old['views'][view]['sites'].items():
  assert new['views'][view]['sites'][site]['tokens']==value['tokens'] and new['views'][view]['sites'][site]['utf8Bytes']==value['utf8Bytes']
  deltas.append(abs(new['views'][view]['sites'][site]['nllPerUtf8Byte']-value['nllPerUtf8Byte']))
assert max(deltas)<=5e-7
record.update(initialDevelopmentExactlyEqual=new==old,maxInitialDevelopmentNllPerByteDifference=max(deltas),initialFunctionNumericalTolerance=5e-7,optimizerCountersAtSnapshot=[10000],additionalOptimizerUpdatesAtSnapshot=0,latestStateNotBestStateMixedWithLatestOptimizer=True)
(R/'execution/initial-equivalence.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
