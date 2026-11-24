"""Real-size zero-update capacity state, lossless chunks and exact restoration.
Staging only: this is not a resumable or completed Round27 trial checkpoint.
"""
import pathlib,sys,json,copy,hashlib,shutil,random
ROOT=pathlib.Path('/workspace/capacity-integration-sandbox/language/round27')
sys.path.insert(0,str(ROOT))
import train as t
from capacity import expand_optimizer_moments
from capacity_audit import verify_initial_expansion
from checkpoint_chunks import pack,restore,digest
OUT=pathlib.Path('/workspace/capacity-storage-preflight');OUT.mkdir(exist_ok=True)
t.torch.set_num_threads(1);t.torch.manual_seed(2049)
parent=t.torch.load(ROOT.parent/'round11/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
config=dict(parent['config'],hidden=1536);model=t.Decoder(config)
t.initialize(model,t.read(ROOT/'multiview/tokenizer.json'))
optimizer=t.torch.optim.AdamW(model.parameters(),lr=2.2499999999999998e-05,weight_decay=.05)
optimizer.load_state_dict(parent['optimizer']);expand_optimizer_moments(optimizer,model,parent)
t.torch.set_rng_state(parent['torchRng']);rng=random.Random();rng.setstate(parent['pythonRng'])
state=dict(step=0,config=config,model=model.state_dict(),beststate=copy.deepcopy(model.state_dict()),optimizer=optimizer.state_dict(),torchRng=t.torch.get_rng_state(),pythonRng=rng.getstate(),preparationOnly=True,notAResumableTrialCheckpoint=True)
verification=verify_initial_expansion(state,parent)
raw=OUT/'zero-update-storage-preflight.pt';assert not raw.exists();t.torch.save(state,raw)
assert raw.stat().st_size>100*1024*1024
manifest=pack(raw);record=json.loads(manifest.read_text());assert len(record['chunks'])==3 and all(x['bytes']<=40*1024*1024 for x in record['chunks'])
dest=OUT/'restore-check';dest.mkdir();shutil.copyfile(manifest,dest/manifest.name)
for part in record['chunks']:
 target=dest/part['path'];target.parent.mkdir(exist_ok=True);shutil.copyfile(raw.parent/part['path'],target)
restored=restore(dest/manifest.name);assert digest(restored)==digest(raw)==record['sha256']
loaded=t.torch.load(restored,map_location='cpu',weights_only=False)
assert loaded['step']==0 and loaded['preparationOnly'] and loaded['notAResumableTrialCheckpoint']
assert all(t.torch.equal(v,loaded['model'][k]) for k,v in state['model'].items())
assert all(t.torch.equal(v,loaded['beststate'][k]) for k,v in state['beststate'].items())
for key,values in state['optimizer']['state'].items():
 for name,value in values.items():assert t.torch.equal(value,loaded['optimizer']['state'][key][name])
assert t.torch.equal(state['torchRng'],loaded['torchRng']) and state['pythonRng']==loaded['pythonRng']
result=dict(preparationOnly=True,actualExperimentalOptimizerUpdates=0,optimizerStepExecuted=False,actualRound27TrainingStarted=False,capacityParameters=7021248,originalBytes=raw.stat().st_size,originalSha256=record['sha256'],restoredSha256=digest(restored),chunkCount=len(record['chunks']),maximumChunkBytes=max(p['bytes'] for p in record['chunks']),allRawBytesWeightsMomentsAndRngRestoredExactly=True,originalRawKept=True,initialExpansionAudit=verification,chunkerSha256=t.sha(ROOT/'checkpoint_chunks.py'),scriptSha256=t.sha(pathlib.Path(__file__)))
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
