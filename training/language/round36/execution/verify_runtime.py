"""Zero-update runtime, manifest and gradient audit; no TEST text access."""
import pathlib,sys,platform,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from train import *
from objective import causal_unlikelihood
from sequence_objective import rollout_unlikelihood
for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
torch.set_num_threads(2);torch.manual_seed(2049)
saved=torch.load(ROOT.parent/'round28/continue-10000/checkpoint.pt',weights_only=False,map_location='cpu')
m=Decoder(saved['config']);initialize(m,read(ROOT.parent/'round11'/'multiview/tokenizer.json'))
i,v=load_partition(ROOT/'multiview','train');rows=[next(x for x in i['rows'] if x['variant']==k and x['site']==site) for site in ['aozora','human-chat'] for k in range(3)]
selector=load_selector(ROOT/'human-turn-token-boundaries.json',read(ROOT/'multiview/tokenizer.json'),i,read(ROOT/'policy.json')['humanNegativePrefix']['featureMapSha256'],sha(ROOT/'multiview/tokenizer.json'),sha(ROOT/'multiview/train.index.json'),sha(ROOT/'sources/documents.jsonl'))
rows[3:]=[next(r for r in i['rows']if r['site']=='human-chat'and r['variant']==k and selector.length(r,int(v[r['offset']]))!=min(32,r['length']-1))for k in range(3)]
x,y=pack(rows,v,256);original_y=y.clone();end_mask=eligible_mask(rows,y,selector.ends);assert end_mask.any() and not end_mask[:3].any();m.train();logits=m(x);ce=F.cross_entropy(logits.reshape(-1,m.config['vocabulary']),y.reshape(-1));ul,count=causal_unlikelihood(logits,x,y);seq,record=rollout_unlikelihood(m,x[3:4,:selector.length(rows[3],int(x[3,0]))]);aux=end_eos_loss(logits,y,end_mask);assert torch.equal(y,original_y);loss=ce+1.0*ul+.1*seq+read(ROOT/'policy.json')['humanUtteranceEndEos']['coefficient']*aux;loss.backward()
assert record['prefixLength']>=8 and record['prefixLength']<min(32,rows[3]['length']-1),'Preflight must exercise a changed true-boundary prefix'
assert all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in m.parameters())
optimizer=torch.optim.AdamW(m.parameters(),lr=read(ROOT/'policy.json')['learningRate'],weight_decay=.05);optimizer.load_state_dict(saved['optimizer'])
assert optimizer.state_dict()['param_groups']==saved['optimizer']['param_groups']
for key,state in optimizer.state_dict()['state'].items():
 for name,t in state.items():assert torch.equal(t,saved['optimizer']['state'][key][name])
torch.set_rng_state(saved['torchRng']);rng=random.Random();rng.setstate(saved['pythonRng'])
assert torch.equal(torch.get_rng_state(),saved['torchRng']) and rng.getstate()==saved['pythonRng']
record=dict(parentOptimizerStateExactlyLoaded=True,parentTorchAndPythonRngRestorable=True,python=sys.version,torch=torch.__version__,numpy=np.__version__,platform=platform.platform(),cuda=torch.cuda.is_available(),threads=2,sourceManifestVerified=True,gradientLoss=loss.item(),endEosLoss=float(aux.detach()),endEosCoefficient=read(ROOT/'policy.json')['humanUtteranceEndEos']['coefficient'],eligibleHumanEndPositions=int(end_mask.sum()),originalGoldTargetsExactlyPreserved=True,crossEntropyLoss=ce.item(),unlikelihoodLoss=ul.item(),negativeCandidates=count,allParametersFiniteNonzeroGradients=True,sequenceUnlikelihoodLoss=float(seq.detach()),negativePrefixLength=record['prefixLength'],preflightHumanPrefixActuallyChanged=record['prefixLength']!=min(32,rows[3]['length']-1),rolloutGeneratedTokens=record['generatedTokens'],rolloutNegativePositions=record['negativePositions'],preflightDataSites=['aozora','human-chat'],preflightRows=6,preflightOptimizerUpdates=0,parentStep=saved['step'],parentBestStep=saved['beststep'],parentOptimizerCounters=sorted(set(int(s['step']) for s in saved['optimizer']['state'].values())),sourceHashes={f:sha(ROOT/f) for f in ['train.py','policy.json','source-manifest.json','../model.py','batching.py']},precision='float32',compile=False)
control=read(ROOT.parent/'round35/execution/preflight-runtime.json')
for term in ['crossEntropyLoss','unlikelihoodLoss','sequenceUnlikelihoodLoss','endEosLoss','eligibleHumanEndPositions']:assert record[term]==control[term],term
expected=control['gradientLoss']-.7*control['endEosLoss'];assert abs(record['gradientLoss']-expected)<1e-6
record.update(initialRawObjectiveTermsExactlyMatchRound35=True,onlyCoefficientChangesInitialCombinedObjective=True,expectedCombinedObjectiveFromRound35=expected)
write(ROOT/'execution/preflight-runtime.json',record);print(json.dumps(record))
