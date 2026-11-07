"""Zero-update real expanded model/optimizer/gradient preflight; no heldout text."""
import pathlib,sys,platform,json
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from train import *
from capacity import expand_optimizer_moments
from capacity_audit import verify_initial_expansion,new_region
for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
torch.set_num_threads(2);torch.manual_seed(2049);saved=torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt',weights_only=False,map_location='cpu');config=dict(saved['config'],hidden=1536);m=Decoder(config);initialize(m,read(ROOT/'multiview/tokenizer.json'));optimizer=torch.optim.AdamW(m.parameters(),lr=read(ROOT/'policy.json')['learningRate'],weight_decay=.05);optimizer.load_state_dict(saved['optimizer']);expand_optimizer_moments(optimizer,m,saved);torch.set_rng_state(saved['torchRng']);rng=random.Random();rng.setstate(saved['pythonRng'])
zero=dict(config=config,step=0,model=m.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate());preserved=verify_initial_expansion(zero,saved)
i,v=load_partition(ROOT/'multiview','train');rows=[next(x for x in i['rows'] if x['variant']==k) for k in range(3)]
if any(x['site']=='wiki2019' for x in i['rows']):rows.extend(next(x for x in i['rows'] if x['variant']==k and x['site']=='wiki2019') for k in range(3))
x,y=pack(rows,v,256);m.train();z=m(x);ce=F.cross_entropy(z.reshape(-1,config['vocabulary']),y.reshape(-1));ul,count=causal_unlikelihood(z,x,y);loss=ce+read(ROOT/'policy.json')['unlikelihood']['coefficient']*ul;seq=None
if 'sequenceUnlikelihood' in read(ROOT/'policy.json'):
 from sequence_objective import rollout_unlikelihood
 seq,rollout=rollout_unlikelihood(m,x[:1,:min(32,rows[0]['length']-1)]);loss=loss+read(ROOT/'policy.json')['sequenceUnlikelihood']['coefficient']*seq
loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in m.parameters());new_input=[];new_output=[]
for name,p in m.named_parameters():
 if name.endswith(('fc1.weight','fc1.bias')):
  assert torch.count_nonzero(new_region(name,p.grad,saved['model'][name]))==0;new_input.append(name)
 elif name.endswith('fc2.weight'):
  assert new_region(name,p.grad,saved['model'][name]).abs().sum()>0;new_output.append(name)
assert len(new_input)==16 and len(new_output)==8
record=dict(**preserved,python=sys.version,torch=torch.__version__,numpy=np.__version__,platform=platform.platform(),cuda=torch.cuda.is_available(),threads=2,sourceManifestVerified=True,gradientLoss=float(loss.detach()),crossEntropyLoss=float(ce.detach()),unlikelihoodLoss=float(ul.detach()),sequenceUnlikelihoodLoss=float(seq.detach()) if seq is not None else None,negativeCandidates=count,allParametersFiniteNonzeroGradients=True,newIncomingInitiallyZeroGradExpected=True,newOutgoingFiniteNonzeroGradients=True,preflightOptimizerUpdates=0,preflightDataSites=sorted({x['site'] for x in rows}),preflightRows=len(rows),parentStep=saved['step'],parentBestStep=saved['beststep'],parentOptimizerCounters=[10000],parameters=sum(p.numel() for p in m.parameters()),config=config,sourceHashes={f:sha(ROOT/f) for f in ['train.py','policy.json','source-manifest.json','../model.py','capacity.py','initialization.py','batching.py']},precision='float32',compile=False)
write(ROOT/'execution/preflight-runtime.json',record);print(json.dumps(record))
