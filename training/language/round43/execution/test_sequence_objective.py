import sys,pathlib,unittest,copy,random
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import torch
from train import Decoder
from sequence_objective import repeated_generated_positions,sequence_unlikelihood,rollout_unlikelihood
torch.set_num_threads(1)
class Tests(unittest.TestCase):
 def test_independent_mask_reference_and_gradient(self):
  tokens=torch.tensor([[1,6,7,8,9,6,7,8,9,6,7,8,10,6,7,8,9,2]])
  prefix=6;mask,generated=repeated_generated_positions(tokens,prefix,8)
  expected=torch.zeros_like(mask)
  for t in range(prefix-1,tokens.shape[1]-1):
   gram=tokens[0,max(0,t-2):t+2].tolist()
   if len(gram)!=4 or min(gram)<6:continue
   expected[0,t]=any(tokens[0,j-3:j+1].tolist()==gram for j in range(max(3,t-7),t+1))
  self.assertTrue(torch.equal(mask,expected));self.assertGreater(int(mask.sum()),0)
  torch.manual_seed(5);z=torch.randn(1,tokens.shape[1]-1,16,dtype=torch.float64,requires_grad=True)
  loss,count,total=sequence_unlikelihood(z,tokens,prefix,8)
  p=z.softmax(-1);ref=z.sum()*0
  for t in range(z.shape[1]):
   if expected[0,t]:ref-=torch.log1p(-p[0,t,tokens[0,t+1]].clamp(max=1-1e-6))
  ref/=tokens.shape[1]-prefix
  torch.testing.assert_close(loss,ref,rtol=1e-12,atol=1e-12)
  torch.testing.assert_close(torch.autograd.grad(loss,z,retain_graph=True)[0],torch.autograd.grad(ref,z)[0],rtol=1e-12,atol=1e-12)
  self.assertEqual(total,tokens.shape[1]-prefix);self.assertEqual(count,int(expected.sum()))
 def test_causal_prefix_special_and_empty(self):
  tokens=torch.tensor([[1,6,7,8,9,6,7,8,9,2]])
  a,_=repeated_generated_positions(tokens,5);changed=tokens.clone();changed[:,9:]=10;b,_=repeated_generated_positions(changed,5)
  self.assertTrue(torch.equal(a[:,:8],b[:,:8]));self.assertFalse(a[:,:4].any());self.assertFalse(a[0,-1])
  z=torch.zeros(1,9,16,requires_grad=True);loss,count,_=sequence_unlikelihood(z,tokens,9)
  self.assertEqual(count,0);self.assertEqual(float(loss.detach()),0);loss.backward();self.assertTrue(torch.isfinite(z.grad).all())
 def test_actual_repeated_target_is_negative(self):
  tokens=torch.tensor([[6,6,6,6,6]]);z=torch.zeros(1,4,12,requires_grad=True)
  loss,count,total=sequence_unlikelihood(z,tokens,4);loss.backward()
  self.assertEqual(count,1);self.assertEqual(total,1);self.assertGreater(float(z.grad[0,3,6]),0)
  self.assertEqual(float(z.grad[0,:3].abs().sum()),0)
 def test_rollout_rng_mode_and_no_optimizer_updates(self):
  cfg=dict(vocabulary=16,dim=8,layers=1,heads=2,hidden=32,context=16,dropout=.1,epsilon=1e-5)
  torch.manual_seed(10);m=Decoder(cfg);m.train();rng=torch.get_rng_state().clone();before=copy.deepcopy(m.state_dict())
  loss,record=rollout_unlikelihood(m,torch.tensor([[1,6,7]]),8);self.assertTrue(m.training);self.assertTrue(torch.equal(rng,torch.get_rng_state()))
  self.assertTrue(all(torch.equal(v,m.state_dict()[k]) for k,v in before.items()));self.assertFalse(record['tokens'].requires_grad);loss.backward()
  self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters()))
  again,other=rollout_unlikelihood(m,torch.tensor([[1,6,7]]),8)
  self.assertTrue(torch.equal(record['tokens'],other['tokens']));self.assertTrue(torch.equal(loss.detach(),again.detach()))
 def test_long_horizon_prefix_rng_and_late_negative_gradients(self):
  class AlwaysRepeat(torch.nn.Module):
   config={'context':256}
   def __init__(self):super().__init__();self.strength=torch.nn.Parameter(torch.tensor(2.))
   def forward(self,x):
    scores=torch.zeros((*x.shape,16));scores[:,:,6]=self.strength;return scores
  m=AlwaysRepeat();m.train();before=torch.get_rng_state().clone();prefix=torch.full((1,32),6)
  short,a=rollout_unlikelihood(m,prefix,max_new_tokens=64)
  long,b=rollout_unlikelihood(m,prefix,max_new_tokens=128)
  self.assertEqual(a['generatedTokens'],64);self.assertEqual(b['generatedTokens'],128)
  self.assertTrue(torch.equal(a['tokens'],b['tokens'][:,:96]))
  self.assertGreater(b['negativePositions'],a['negativePositions']);long.backward()
  self.assertTrue(torch.isfinite(m.strength.grad));self.assertGreater(float(m.strength.grad),0)
  self.assertTrue(torch.equal(before,torch.get_rng_state()));self.assertTrue(m.training)
  with self.assertRaises(ValueError):rollout_unlikelihood(m,prefix,max_new_tokens=225)
 def test_exact_next_optimizer_update_with_rollout_after_resume(self):
  cfg=dict(vocabulary=16,dim=8,layers=1,heads=2,hidden=32,context=16,dropout=.1,epsilon=1e-5)
  torch.manual_seed(9);rng=random.Random(9);m=Decoder(cfg)
  with torch.no_grad():m.token.weight[6]*=20
  opt=torch.optim.AdamW(m.parameters(),lr=.0001)
  def step(model,optimizer,index):
   x=torch.tensor([[6,6,6,6,rng.randrange(7,12),8,9,10]])
   y=x.roll(-1,1);y[:,-1]=-100;model.train();optimizer.zero_grad()
   ce=torch.nn.functional.cross_entropy(model(x).flatten(0,1),y.flatten());loss=ce;record=None
   if index%2==0:
    ul,record=rollout_unlikelihood(model,torch.tensor([[6,6,6,6]]),8);loss=loss+.1*ul
   loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step();return loss.detach(),record
  step(m,opt,1);snap=copy.deepcopy(dict(model=m.state_dict(),optimizer=opt.state_dict(),torch=torch.get_rng_state(),python=rng.getstate()))
  expected,trace=step(m,opt,2);self.assertGreater(trace['negativePositions'],0);trng=torch.get_rng_state().clone();prng=rng.getstate()
  n=Decoder(cfg);no=torch.optim.AdamW(n.parameters(),lr=.0001);n.load_state_dict(snap['model']);no.load_state_dict(snap['optimizer']);torch.set_rng_state(snap['torch']);rng.setstate(snap['python'])
  actual,other=step(n,no,2);self.assertTrue(torch.equal(expected,actual));self.assertTrue(torch.equal(trace['tokens'],other['tokens']))
  self.assertTrue(all(torch.equal(v,n.state_dict()[k]) for k,v in m.state_dict().items()))
  for k,state in opt.state_dict()['state'].items():
   self.assertTrue(all(torch.equal(v,no.state_dict()['state'][k][name]) for name,v in state.items()))
  self.assertTrue(torch.equal(trng,torch.get_rng_state()) and prng==rng.getstate())

if __name__=='__main__':unittest.main()
