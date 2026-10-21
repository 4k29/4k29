"""Synthetic mathematical checks only; not model training or language evidence."""
import json,pathlib,hashlib,torch
from utterance_end_objective import eligible_mask,end_eos_loss
D=pathlib.Path(__file__).resolve().parent
torch.set_num_threads(1)
rows=[dict(site='human-chat',unit='a',start=0,length=7,prefixLength=1),dict(site='human-chat',unit='a',start=0,length=7,prefixLength=3),dict(site='other',unit='b',start=0,length=7,prefixLength=1),dict(site='human-chat',unit='a',start=2,length=5,prefixLength=2)]
y=torch.tensor([[9,16,10,17,11,16],[-100,-100,10,17,11,16],[9,16,10,17,11,16],[-100,17,11,16,-100,-100]])
boundaries={'a':[3,5,7]};y_before=y.clone();mask=eligible_mask(rows,y,boundaries)
assert torch.equal(y,y_before)
assert mask.nonzero().tolist()==[[0,1],[0,5],[1,5],[3,3]]
logits=torch.zeros(4,6,20,dtype=torch.float64,requires_grad=True)
rng=torch.get_rng_state().clone();loss=end_eos_loss(logits,y,mask)
assert abs(loss.item()-4*torch.log(torch.tensor(20.,dtype=torch.float64)).item()/19)<1e-14
loss.backward();assert torch.isfinite(logits.grad).all()
assert not logits.grad[~mask].any()
assert (logits.grad[mask][:,2]<0).all()
assert torch.equal(rng,torch.get_rng_state())
empty=torch.zeros_like(mask);z=end_eos_loss(logits,y,empty);assert z.item()==0;z.backward()
bad=mask.clone();bad[1,0]=True
try:end_eos_loss(logits,y,bad)
except ValueError:pass
else:raise AssertionError('Masked target accepted')
report=dict(syntheticChecksPassed=True,lossAtUniformLogits=loss.item(),originalNonmaskedTargets=int(y.ne(-100).sum()),eligibleTargets=int(mask.sum()),allOtherGradientsZero=True,eosGradientLowersEosNll=True,originalTargetsUnmodified=True,rngUnchanged=True,zeroEligibleCaseDifferentiable=True,maskedOriginalTargetsRejected=True,noModelOrOptimizerUsed=True,noHeldoutOpened=True,actualNewRoundUpdates=0,notLanguageEvidence=True,objectiveSha256=hashlib.sha256((D/'utterance_end_objective.py').read_bytes()).hexdigest())
(D/'synthetic-objective-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
