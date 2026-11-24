"""Zero-update runtime, manifest and gradient audit; no TEST text access."""
import pathlib,sys,platform,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from train import *
from objective import causal_unlikelihood
from sequence_objective import rollout_unlikelihood
for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
torch.set_num_threads(2);torch.manual_seed(2049)
saved=torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt',weights_only=False,map_location='cpu')
m=Decoder(saved['config']);initialize(m,read(ROOT.parent/'round11'/'multiview/tokenizer.json'))
i,v=load_partition(ROOT/'multiview','train');rows=[next(x for x in i['rows'] if x['variant']==k) for k in range(3)]
x,y=pack(rows,v,256);m.train();logits=m(x);ce=F.cross_entropy(logits.reshape(-1,m.config['vocabulary']),y.reshape(-1));ul,count=causal_unlikelihood(logits,x,y);seq,record=rollout_unlikelihood(m,x[:1,:32],max_new_tokens=read(ROOT/'policy.json')['sequenceUnlikelihood']['maxNewTokens']);loss=ce+1.0*ul+.1*seq;loss.backward()
assert all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in m.parameters())
optimizer=torch.optim.AdamW(m.parameters(),lr=read(ROOT/'policy.json')['learningRate'],weight_decay=.05);optimizer.load_state_dict(saved['optimizer'])
assert optimizer.state_dict()['param_groups']==saved['optimizer']['param_groups']
for key,state in optimizer.state_dict()['state'].items():
 for name,t in state.items():assert torch.equal(t,saved['optimizer']['state'][key][name])
torch.set_rng_state(saved['torchRng']);rng=random.Random();rng.setstate(saved['pythonRng'])
assert torch.equal(torch.get_rng_state(),saved['torchRng']) and rng.getstate()==saved['pythonRng']
record=dict(parentOptimizerStateExactlyLoaded=True,parentTorchAndPythonRngRestorable=True,python=sys.version,torch=torch.__version__,numpy=np.__version__,platform=platform.platform(),cuda=torch.cuda.is_available(),threads=2,sourceManifestVerified=True,gradientLoss=loss.item(),crossEntropyLoss=ce.item(),unlikelihoodLoss=ul.item(),negativeCandidates=count,allParametersFiniteNonzeroGradients=True,sequenceUnlikelihoodLoss=float(seq.detach()),rolloutGeneratedTokens=record['generatedTokens'],rolloutNegativePositions=record['negativePositions'],preflightOptimizerUpdates=0,parentStep=saved['step'],parentBestStep=saved['beststep'],parentOptimizerCounters=sorted(set(int(s['step']) for s in saved['optimizer']['state'].values())),sourceHashes={f:sha(ROOT/f) for f in ['train.py','policy.json','source-manifest.json','../model.py','batching.py']},precision='float32',compile=False)
write(ROOT/'execution/preflight-runtime.json',record);print(json.dumps(record))
