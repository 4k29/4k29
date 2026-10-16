import sys,pathlib,unittest,copy,random
sys.path.insert(0,'/workspace/4k29/training/language/round24')
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
if __name__=='__main__':unittest.main()
