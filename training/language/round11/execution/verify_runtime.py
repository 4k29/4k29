"""Zero-update runtime, manifest and gradient audit; no TEST text access."""
import pathlib,sys,platform,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from train import *
for row in read(ROOT/'source-manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
torch.set_num_threads(2);torch.manual_seed(2049)
saved=torch.load(PARENT/'word-512-continue-10000/checkpoint.pt',weights_only=False,map_location='cpu')
m=Decoder(saved['config']);initialize(m,read(ROOT/'multiview/tokenizer.json'))
i,v=load_partition(ROOT/'multiview','train');rows=[next(x for x in i['rows'] if x['variant']==k) for k in range(3)]
x,y=pack(rows,v,256);m.train();loss=F.cross_entropy(m(x).reshape(-1,m.config['vocabulary']),y.reshape(-1));loss.backward()
assert all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in m.parameters())
record=dict(python=sys.version,torch=torch.__version__,numpy=np.__version__,platform=platform.platform(),cuda=torch.cuda.is_available(),threads=2,sourceManifestVerified=True,gradientLoss=loss.item(),allParametersFiniteNonzeroGradients=True,preflightOptimizerUpdates=0,parentStep=saved['step'],parentBestStep=saved['beststep'],parentOptimizerCounters=sorted(set(int(s['step']) for s in saved['optimizer']['state'].values())),sourceHashes={f:sha(ROOT/f) for f in ['train.py','policy.json','source-manifest.json','../model.py','batching.py']},precision='float32',compile=False)
write(ROOT/'execution/preflight-runtime.json',record);print(json.dumps(record))
