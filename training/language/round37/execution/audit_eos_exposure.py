"""Replay original positive draws for exact EOS eligibility counters, no forwards/updates."""
import pathlib,sys,json,hashlib,random,collections,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from train import load_partition,pack,read,sha,sampler,draw
from utterance_end_objective import eligible_mask
torch.set_num_threads(1);a=torch.load(R/'continue-10000/checkpoint-0.pt',weights_only=False,map_location='cpu');b=torch.load(R/'continue-10000/checkpoint.pt',weights_only=False,map_location='cpu');assert a['step']==0 and b['step']==10000
info,v=load_partition(R/'multiview','train');ends=read(R/'human-turn-token-boundaries.json')['boundariesByUnit'];rng=random.Random();rng.setstate(a['pythonRng']);strata,weights,masses=sampler(info['rows'],read(R/'policy.json')['genreSampling']);positions=batches=targets=0;views=collections.Counter()
for step in range(1,10001):
 width,rows=draw(rng,8,strata,weights,masses);x,y=pack(rows,v,width);mask=eligible_mask(rows,y,ends);positions+=int(mask.sum());batches+=int(mask.any());targets+=int(y.ne(-100).sum())
 for i,r in enumerate(rows):views[r['variant']]+=int(mask[i].sum())
assert positions==b['endEosPositions']and batches==b['endEosBatches']and targets==b['seen_tokens']and rng.getstate()==b['pythonRng']
assert positions==161241 and batches==9163 and targets==15584824,'Prospective fixed draw replay differs'
report=dict(actualCompletedUpdates=10000,eligibleAuxiliaryEosPositions=positions,batchesWithEligibleTargets=batches,originalGoldTargets=targets,byView=dict(views),privateRngExactlyMatchesActualTerminal=True,checkpointCountersExactlyMatchIndependentReplay=True,noModelForwardOrOptimizer=True,checkpointSha256=sha(R/'continue-10000/checkpoint.pt'),codeSha256=sha(pathlib.Path(__file__)))
(R/'execution/eos-exposure-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
