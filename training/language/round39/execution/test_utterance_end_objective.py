"""Mathematical targets/gradients and exact no-eligible control, never optimizer updates."""
import unittest,pathlib,sys,copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import torch
from torch.nn import functional as F
from train import Decoder
from objective import causal_unlikelihood
from utterance_end_objective import eligible_mask,end_eos_loss
torch.set_num_threads(1)
class Tests(unittest.TestCase):
 def fixture(self):
  rows=[dict(site='human-chat',unit='a',start=0,length=7,prefixLength=1),dict(site='human-chat',unit='a',start=0,length=7,prefixLength=3),dict(site='other',unit='b',start=0,length=7,prefixLength=1),dict(site='human-chat',unit='a',start=2,length=5,prefixLength=2)]
  y=torch.tensor([[9,16,10,17,11,16],[-100,-100,10,17,11,16],[9,16,10,17,11,16],[-100,17,11,16,-100,-100]])
  return rows,y,{'a':[3,5,7]}
 def test_original_position_and_compound_newline_exclusion(self):
  rows,y,ends=self.fixture();before=y.clone();rng=torch.get_rng_state().clone();mask=eligible_mask(rows,y,ends)
  self.assertEqual(mask.nonzero().tolist(),[[0,1],[0,5],[1,5],[3,3]]);self.assertTrue(torch.equal(y,before));self.assertTrue(torch.equal(rng,torch.get_rng_state()))
 def test_normalization_and_local_eos_gradient(self):
  rows,y,ends=self.fixture();mask=eligible_mask(rows,y,ends);z=torch.zeros(4,6,20,dtype=torch.float64,requires_grad=True);loss=end_eos_loss(z,y,mask);self.assertAlmostEqual(loss.item(),4*torch.log(torch.tensor(20.,dtype=torch.float64)).item()/19,places=14);loss.backward();self.assertFalse(z.grad[~mask].any());self.assertTrue((z.grad[mask][:,2]<0).all());self.assertTrue(torch.isfinite(z.grad).all())
 def test_masked_gold_rejected(self):
  rows,y,ends=self.fixture();mask=eligible_mask(rows,y,ends);mask[1,0]=True
  with self.assertRaises(ValueError):end_eos_loss(torch.zeros(4,6,20),y,mask)
 def test_no_eligible_exact_model_loss_and_gradients(self):
  torch.manual_seed(123);m=Decoder(dict(vocabulary=24,dim=8,layers=1,heads=2,hidden=32,context=8,dropout=.1,epsilon=1e-5));n=copy.deepcopy(m);x=torch.tensor([[1,6,7,8,6,7,8,9]]);y=torch.tensor([[6,7,8,6,7,8,9,2]]);state=torch.get_rng_state().clone()
  z=m(x);ce=F.cross_entropy(z.reshape(-1,24),y.reshape(-1));ul,_=causal_unlikelihood(z,x,y);a=ce+ul;a.backward();endstate=torch.get_rng_state().clone();torch.set_rng_state(state)
  z=n(x);ce=F.cross_entropy(z.reshape(-1,24),y.reshape(-1));ul,_=causal_unlikelihood(z,x,y);aux=end_eos_loss(z,y,torch.zeros_like(y,dtype=torch.bool));b=ce+ul+aux;b.backward()
  self.assertTrue(torch.equal(a,b));self.assertTrue(torch.equal(endstate,torch.get_rng_state()))
  for p,q in zip(m.parameters(),n.parameters(),strict=True):self.assertTrue(torch.equal(p.grad,q.grad))
 def test_bad_shapes_rejected(self):
  with self.assertRaises(ValueError):end_eos_loss(torch.zeros(1,2,20),torch.zeros(1,2,dtype=torch.long),torch.zeros(1,2))
if __name__=='__main__':unittest.main()
