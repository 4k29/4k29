"""Back up an already captured aligned selected-step state; never alter live training."""
import argparse,pathlib,json,hashlib,io,sys,random,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));from checkpoint_chunks import pack
torch.set_num_threads(1);p=argparse.ArgumentParser();p.add_argument('--step',type=int,required=True);a=p.parse_args();O=E/f'retained-selected-{a.step}';sha=lambda b:hashlib.sha256(b).hexdigest()
def verify_parts(manifest):
 j=json.loads(manifest.read_text());h=hashlib.sha256();n=0
 for r in j['chunks']:
  b=(manifest.parent/r['path']).read_bytes();assert len(b)==r['bytes']and sha(b)==r['sha256'];h.update(b);n+=len(b)
 assert n==j['bytes']and h.hexdigest()==j['sha256'];return j
if O.exists():
 j=verify_parts(O/'checkpoint.pt.chunks.json');s=json.loads((O/'snapshot.json').read_text());assert s['selectedStep']==a.step and j['sha256']==s['checkpointSha256'];print('Existing selected state verified',a.step);raise SystemExit
raw=(R/'continue-10000/best-aligned-checkpoint.pt').read_bytes();c=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=False);assert c['step']==c['beststep']==a.step
assert all(torch.equal(v,c['beststate'][k])for k,v in c['model'].items());counters=sorted({int(v['step'])for v in c['optimizer']['state'].values()});assert counters==[20000+a.step];assert c['settings']['experimentPolicySha256']==sha((R/'policy.json').read_bytes())
for s in c['optimizer']['state'].values():assert all(torch.isfinite(s[k]).all()for k in ['exp_avg','exp_avg_sq'])
rng=random.Random();rng.setstate(c['pythonRng']);assert rng.getstate()==c['pythonRng'];assert c['torchRng'].dtype==torch.uint8
O.mkdir();target=O/'checkpoint.pt';target.write_bytes(raw);parts=verify_parts(pack(target));assert parts['sha256']==sha(raw);target.unlink()
s=dict(selectedStep=a.step,actualUpdatesInThisSelectedState=a.step,optimizerCounters=counters,weightLineageUpdates=59000+a.step,checkpointSha256=sha(raw),checkpointBytes=len(raw),fullAlignedModelMomentsAndRng=True,modelEqualsBeststate=True,selectedWeightsNeverMixedWithLatestMoments=True,allPartsReassembledShaVerified=True,additionalOptimizerUpdates=0,liveTrainerNotModified=True,recovery='Inspect or fork this selected full state only. For exact resumption of the existing trial use its newest checkpoint; never roll back newer work or attach these moments to later weights.')
(O/'snapshot.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s))
