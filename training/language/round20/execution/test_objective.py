"""Numerical/reference, causality, gold exclusion and exact resume tests."""
import pathlib,sys,unittest,random,copy,json
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import torch
from torch.nn import functional as F
from objective import negative_candidates,causal_unlikelihood
from train import Decoder
torch.set_num_threads(1)

class ObjectiveTests(unittest.TestCase):
 def test_sparse_equals_independent_reference(self):
  x=torch.tensor([[6,7,6,8,9,9],[0,6,7,8,0,0]])
  y=torch.tensor([[7,6,-100,9,6,9],[-100,7,8,9,-100,-100]])
  torch.manual_seed(41);z=torch.randn(2,6,16,dtype=torch.float64,requires_grad=True)
  actual,count=causal_unlikelihood(z,x,y,3);reference=z.sum()*0;expected=0
  probs=z.softmax(-1)
  for b in range(2):
   for t in range(6):
    if y[b,t]==-100:continue
    for token in set(x[b,max(0,t-2):t+1].tolist()):
     if token>=6 and token!=int(y[b,t]):
      reference=reference-torch.log1p(-probs[b,t,token].clamp(max=1-1e-6));expected+=1
  reference/=y.ne(-100).sum()
  self.assertEqual(count,expected);torch.testing.assert_close(actual,reference,rtol=1e-12,atol=1e-12)
  a=torch.autograd.grad(actual,z,retain_graph=True)[0];b=torch.autograd.grad(reference,z)[0]
  torch.testing.assert_close(a,b,rtol=1e-12,atol=1e-12)
 def test_causal_and_gold_exclusion(self):
  x=torch.tensor([[6,7,6,8,9,10]]);y=torch.tensor([[7,6,8,9,10,-100]])
  ids,mask=negative_candidates(x,y,64)
  self.assertFalse(((ids==y.unsqueeze(-1)) & mask).any())
  self.assertFalse(((ids<6) & mask).any());self.assertFalse(mask[:,-1].any())
  changed=x.clone();changed[:,3:]=11
  j,m=negative_candidates(changed,y,64)
  self.assertTrue(torch.equal(ids[:,:3],j[:,:3]) and torch.equal(mask[:,:3],m[:,:3]))
 def test_rng_mask_stability_extreme_and_gradient_direction(self):
  x=torch.tensor([[6,6]]);y=torch.tensor([[7,-100]])
  z=torch.zeros(1,2,12,requires_grad=True);rng=torch.get_rng_state().clone()
  loss,count=causal_unlikelihood(z,x,y);loss.backward()
  self.assertEqual(count,1);self.assertGreater(float(z.grad[0,0,6]),0)
  self.assertEqual(float(z.grad[0,1].abs().sum()),0);self.assertTrue(torch.equal(rng,torch.get_rng_state()))
  extreme=torch.full((1,2,12),-1000.);extreme[:,:,6]=1000.;extreme.requires_grad_()
  loss,_=causal_unlikelihood(extreme,x,y);loss.backward()
  self.assertTrue(torch.isfinite(loss) and torch.isfinite(extreme.grad).all())
  empty,_=causal_unlikelihood(z,x,torch.full_like(y,-100));self.assertEqual(float(empty.detach()),0)
 def test_objective_exact_next_update_after_resume(self):
  torch.manual_seed(2049);rng=random.Random(2049)
  cfg=dict(vocabulary=20,dim=8,layers=1,heads=2,hidden=32,context=8,dropout=.1,epsilon=1e-5)
  model=Decoder(cfg);opt=torch.optim.AdamW(model.parameters(),lr=.001)
  def step(m,o):
   x=torch.tensor([[rng.randrange(6,20) for _ in range(8)]]);y=x.roll(-1,1);y[:,-1]=-100
   m.train();o.zero_grad();z=m(x);ce=F.cross_entropy(z.flatten(0,1),y.flatten());ul,_=causal_unlikelihood(z,x,y)
   loss=ce+.1*ul;loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1.);o.step()
   return loss.detach()
  step(model,opt);snap=copy.deepcopy(dict(model=model.state_dict(),opt=opt.state_dict(),torch=torch.get_rng_state(),python=rng.getstate()))
  expected=step(model,opt);expected_rng=torch.get_rng_state().clone();expected_py=rng.getstate()
  resumed=Decoder(cfg);ropt=torch.optim.AdamW(resumed.parameters(),lr=.001);resumed.load_state_dict(snap['model']);ropt.load_state_dict(snap['opt']);torch.set_rng_state(snap['torch']);rng.setstate(snap['python'])
  self.assertTrue(torch.equal(expected,step(resumed,ropt)))
  self.assertTrue(all(torch.equal(t,resumed.state_dict()[k]) for k,t in model.state_dict().items()))
  for k,s in opt.state_dict()['state'].items():
   self.assertTrue(all(torch.equal(v,ropt.state_dict()['state'][k][n]) for n,v in s.items()))
  self.assertTrue(torch.equal(expected_rng,torch.get_rng_state()) and expected_py==rng.getstate())

if __name__=='__main__':unittest.main()
