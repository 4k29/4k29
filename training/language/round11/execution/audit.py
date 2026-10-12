"""Audit actual updates, RNG, selection, weights and immutable experiment identity."""
import pathlib,sys,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from train import *
torch.set_num_threads(1)
folder=ROOT/'continue-10000';cp=torch.load(folder/'checkpoint.pt',map_location='cpu',weights_only=False);zero=torch.load(folder/'checkpoint-0.pt',map_location='cpu',weights_only=False);result=read(folder/'result.json')
assert cp['step']==result['completedSteps']
assert result['completedRun']==(cp['step']==10000)
assert cp['settings']==zero['settings']==read(folder/'config.json')['settings']
assert result['checkpointSha256']==sha(folder/'checkpoint.pt')
assert zero['step']==0 and not zero['optimizer']['state'] and zero['seen_tokens']==zero['seen_bytes']==0
parent=torch.load(PARENT/'word-512-continue-10000/checkpoint.pt',weights_only=False,map_location='cpu')
assert all(torch.equal(v,parent['beststate'][k]) for k,v in zero['model'].items())
counters=sorted(set(int(s['step']) for s in cp['optimizer']['state'].values()));assert counters==[cp['step']]
assert len(cp['optimizer']['state'])==len(cp['model'])
assert all(torch.isfinite(t).all() and t.dtype==torch.float32 for key in ['model','beststate'] for t in cp[key].values())
assert all(torch.isfinite(s[k]).all() and s[k].dtype==torch.float32 for s in cp['optimizer']['state'].values() for k in ['exp_avg','exp_avg_sq'])
assert cp['torchRng'].dtype==torch.uint8 and isinstance(cp['pythonRng'],tuple)
rng=random.Random();rng.setstate(cp['pythonRng']);torch.set_rng_state(cp['torchRng'])
assert cp['bestloss']==min(x['validation']['nllPerUtf8Byte'] for x in cp['history'])
assert cp['beststep']==result['bestStep']
for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
assert cp['settings']['trainerSourceSha256']==sha(ROOT/'train.py')
assert cp['settings']['experimentPolicySha256']==sha(ROOT/'policy.json')
assert not list(ROOT.glob('*/test.tokens.bin'))
export=json.loads((folder/'model.js').read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
assert export['training']==result
assert all(export['tensors'][k]['data']==[round(float(x),7) for x in t.flatten()] for k,t in cp['beststate'].items())
# Retain latest raw weights separately from the likelihood-selected inference export.
torch.save(dict(config=cp['config'],state=cp['beststate'],selectedStep=cp['beststep'],actualUpdates=cp['step'],parentCheckpointSha256=cp['settings']['parentCheckpointSha256']),folder/'selected-weights.pt')
record=dict(actualCompletedUpdates=cp['step'],requestedUpdates=10000,completedRun=result['completedRun'],selectedStep=cp['beststep'],selectedWeightLineageUpdates=39000+cp['beststep'],latestWeightLineageUpdates=39000+cp['step'],optimizerCounters=counters,allParametersHaveOptimizerState=True,finiteFp32WeightsAndMoments=True,pythonAndTorchRngRestored=True,numpyRandomNotUsed=True,exactParentInitialWeights=True,sourceManifestVerified=True,checkpointSha256=sha(folder/'checkpoint.pt'),initialCheckpointSha256=sha(folder/'checkpoint-0.pt'),selectedWeightsSha256=sha(folder/'selected-weights.pt'),modelSha256=sha(folder/'model.js'),bestWeightedDevelopmentNllPerByte=cp['bestloss'],initialWeightedDevelopmentNllPerByte=cp['history'][0]['validation']['nllPerUtf8Byte'],elapsedTrainingSeconds=cp['elapsed'],seenTargetTokens=cp['seen_tokens'],seenTargetUtf8Bytes=cp['seen_bytes'],testEncodedOrGenerated=False,publicModelReplaced=False)
write(ROOT/'execution/optimizer-audit.json',record);print(json.dumps(record))
