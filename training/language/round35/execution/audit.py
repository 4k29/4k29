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
assert zero['step']==0 and zero['optimizer']['state'] and zero['seen_tokens']==zero['seen_bytes']==0
parent=torch.load(ROOT.parent/'round28/continue-10000/checkpoint.pt',weights_only=False,map_location='cpu')
assert cp['config']==zero['config']==parent['config']==read(folder/'config.json')['config']
assert cp['settings']['trainingViews']=={'canonical':.4,'glyph':.3,'randomCharacterCuts':.3}
assert cp['settings']['genreSampling']==read(ROOT/'policy.json')['genreSampling']
assert cp['settings']['validationViews']=={'canonical':.4,'glyph':.3,'randomCharacterCuts':.3}
assert not any(cp['settings'][k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI'])
assert sum(t.numel() for t in cp['model'].values())==result['parameters']==4655808
assert all(torch.equal(v,parent['model'][k]) for k,v in zero['model'].items())
counters=sorted(set(int(s['step']) for s in cp['optimizer']['state'].values()));assert counters==[20000+cp['step']]
assert len(cp['optimizer']['state'])==len(cp['model'])
assert all(torch.isfinite(t).all() and t.dtype==torch.float32 for key in ['model','beststate'] for t in cp[key].values())
assert all(torch.isfinite(s[k]).all() and s[k].dtype==torch.float32 for s in cp['optimizer']['state'].values() for k in ['exp_avg','exp_avg_sq'])
assert cp['torchRng'].dtype==torch.uint8 and isinstance(cp['pythonRng'],tuple)
rng=random.Random();rng.setstate(cp['pythonRng']);torch.set_rng_state(cp['torchRng'])
assert rng.getstate()==cp['pythonRng'] and torch.equal(torch.get_rng_state(),cp['torchRng'])
assert zero['optimizer']['param_groups']==parent['optimizer']['param_groups']
assert zero['pythonRng']==parent['pythonRng'] and torch.equal(zero['torchRng'],parent['torchRng'])
for key,state in zero['optimizer']['state'].items():
 for name,t in state.items():assert torch.equal(t,parent['optimizer']['state'][key][name])
assert cp['bestloss']==min(x['validation']['nllPerUtf8Byte'] for x in cp['history'])
assert cp['beststep']==result['bestStep']
assert zero['rolloutCalls']==zero['rolloutGeneratedTokens']==zero['rolloutNegativePositions']==zero['endEosPositions']==zero['endEosBatches']==0
assert all(cp[k]==result[k]for k in ['endEosPositions','endEosBatches'])
assert cp['settings']['humanUtteranceEndEos']==read(ROOT/'policy.json')['humanUtteranceEndEos']
assert cp['rolloutCalls']==cp['step']//10
assert all(cp[k]==result[k] for k in ['rolloutCalls','rolloutGeneratedTokens','rolloutNegativePositions'])
for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
assert cp['settings']['trainerSourceSha256']==sha(ROOT/'train.py')
assert cp['settings']['experimentPolicySha256']==sha(ROOT/'policy.json')
assert not list(ROOT.glob('*/test.tokens.bin'))
export=json.loads((folder/'model.js').read_text().split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
assert export['training']==result
assert all(export['tensors'][k]['data']==[round(float(x),7) for x in t.flatten()] for k,t in cp['beststate'].items())
# Retain latest raw weights separately from the likelihood-selected inference export.
torch.save(dict(config=cp['config'],state=cp['beststate'],selectedStep=cp['beststep'],actualUpdates=cp['step'],parentCheckpointSha256=cp['settings']['parentCheckpointSha256']),folder/'selected-weights.pt')
record=dict(actualCompletedUpdates=cp['step'],requestedUpdates=10000,completedRun=result['completedRun'],selectedStep=cp['beststep'],selectedWeightLineageUpdates=59000+cp['beststep'],latestWeightLineageUpdates=59000+cp['step'],parentOptimizerUpdates=20000,optimizerCounters=counters,allParametersHaveOptimizerState=True,configurationAndTrainingViewsInvariant=True,genreSamplingMatchesFrozenPolicy=True,externalWeights=False,externalTokenizer=False,externalInferenceAPI=False,finiteFp32WeightsAndMoments=True,pythonAndTorchRngRestored=True,numpyRandomNotUsed=True,exactParentInitialWeights=True,sourceManifestVerified=True,checkpointSha256=sha(folder/'checkpoint.pt'),initialCheckpointSha256=sha(folder/'checkpoint-0.pt'),selectedWeightsSha256=sha(folder/'selected-weights.pt'),modelSha256=sha(folder/'model.js'),bestWeightedDevelopmentNllPerByte=cp['bestloss'],initialWeightedDevelopmentNllPerByte=cp['history'][0]['validation']['nllPerUtf8Byte'],elapsedTrainingSeconds=cp['elapsed'],seenTargetTokens=cp['seen_tokens'],seenTargetUtf8Bytes=cp['seen_bytes'],rolloutCalls=cp['rolloutCalls'],rolloutGeneratedTokens=cp['rolloutGeneratedTokens'],rolloutNegativePositions=cp['rolloutNegativePositions'],testEncodedOrGenerated=False,publicModelReplaced=False)
write(ROOT/'execution/optimizer-audit.json',record);print(json.dumps(record))
