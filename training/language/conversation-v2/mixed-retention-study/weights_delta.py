"""Layer-group parameter displacement from same initial weights, not a forgetting proof."""
from mix_runtime import *
import argparse,collections,math
ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);ap.add_argument('--name',required=True);a=ap.parse_args();dest=P/('WEIGHTS-'+a.name+'.json');assert not dest.exists();torch.set_num_threads(2);base=torch.load(SCRATCH/'initial.pt',map_location='cpu',weights_only=False)['trajectory']['model'];end=torch.load(a.checkpoint,map_location='cpu',weights_only=False)['trajectory']['model'];groups=collections.defaultdict(lambda:[0.,0.,0,0.])
for k,w in base.items():
 z=end[k].double()-w.double();g='.'.join(k.split('.')[:2]) if k.startswith('blocks.') else k.split('.')[0];r=groups[g];r[0]+=float(z.square().sum());r[1]+=float(w.double().square().sum());r[2]+=w.numel();r[3]=max(r[3],float(z.abs().max()))
write(dest,dict(initial_SHA=sha(SCRATCH/'initial.pt'),terminal_SHA=sha(a.checkpoint),groups={k:dict(delta_L2=math.sqrt(v[0]),initial_L2=math.sqrt(v[1]),relative_L2=math.sqrt(v[0]/v[1]),RMS_delta=math.sqrt(v[0]/v[2]),parameters=v[2],max_absolute_delta=v[3]) for k,v in groups.items()},not_independent_evidence_of_forgetting=True,model_forwards=0,optimizer_calls=0));print(a.name,'weight displacements recorded')
