"""Scientific contracts for the sole main-CE exclusion, including gradients."""
import pathlib,sys,unittest,torch
from torch.nn import functional as F
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]));from end_main_ce import main_ce_without_end_newline
class MainCeExclusion(unittest.TestCase):
 def setUp(self):
  torch.set_num_threads(1);torch.manual_seed(3701);self.z=torch.randn(2,4,32,requires_grad=True);self.y=torch.tensor([[16,3,5,-100],[7,16,2,4]]);self.mask=self.y.eq(16)
 def test_empty_loss_gradient_and_rng_exact(self):
  rng=torch.get_rng_state().clone();a=F.cross_entropy(self.z.reshape(-1,32),self.y.reshape(-1));b,o,r=main_ce_without_end_newline(self.z,self.y,torch.zeros_like(self.mask));assert torch.equal(a,b)and b is o and r.item()==0
  assert torch.equal(torch.autograd.grad(a,self.z,retain_graph=True)[0],torch.autograd.grad(b,self.z)[0]);assert torch.equal(rng,torch.get_rng_state())
 def test_explicit_retained_loss_original_denominator(self):
  b,o,r=main_ce_without_end_newline(self.z,self.y,self.mask);per=F.cross_entropy(self.z.reshape(-1,32),self.y.reshape(-1),reduction='none').reshape_as(self.y);valid=self.y.ne(-100);assert torch.allclose(b,per[valid & ~self.mask].sum()/valid.sum(),atol=1e-6,rtol=0)
 def test_masked_gradient_zero_nonmasked_gradient_same(self):
  b,o,r=main_ce_without_end_newline(self.z,self.y,self.mask);a=torch.autograd.grad(o,self.z,retain_graph=True)[0];g=torch.autograd.grad(b,self.z)[0];assert torch.allclose(g[self.mask],torch.zeros_like(g[self.mask]),atol=1e-7,rtol=0);assert torch.equal(g[~self.mask],a[~self.mask])
 def test_subtraction_and_original_labels(self):
  before=self.y.clone();b,o,r=main_ce_without_end_newline(self.z,self.y,self.mask);assert torch.equal(b,o-r)and torch.equal(self.y,before)and r.item()>0
 def test_aux_only_gradient_at_eligible_end(self):
  b,o,r=main_ce_without_end_newline(self.z,self.y,self.mask);aux=.3*F.cross_entropy(self.z[self.mask],torch.full_like(self.y[self.mask],2),reduction='sum')/self.y.ne(-100).sum();g=torch.autograd.grad(b+aux,self.z,retain_graph=True)[0];h=torch.autograd.grad(aux,self.z)[0];assert torch.allclose(g[self.mask],h[self.mask],atol=1e-7,rtol=0)
 def test_all_eligible_main_ce_and_gradient_zero(self):
  y=torch.full((2,4),16);m=torch.ones_like(y,dtype=torch.bool);b,o,r=main_ce_without_end_newline(self.z,y,m);assert abs(b.item())<1e-6;assert torch.autograd.grad(b,self.z)[0].abs().max()<1e-7
 def test_invalid_mask_dtype(self):
  with self.assertRaises(ValueError):main_ce_without_end_newline(self.z,self.y,self.mask.long())
 def test_invalid_mask_shape(self):
  with self.assertRaises(ValueError):main_ce_without_end_newline(self.z,self.y,self.mask[:1])
 def test_reject_other_gold_or_ignored_position(self):
  for index in [(0,1),(0,3)]:
   m=torch.zeros_like(self.mask);m[index]=True
   with self.assertRaises(ValueError):main_ce_without_end_newline(self.z,self.y,m)
 def test_zero_valid_targets_rejected(self):
  y=torch.full_like(self.y,-100)
  with self.assertRaises(ValueError):main_ce_without_end_newline(self.z,y,torch.zeros_like(self.mask))
if __name__=='__main__':unittest.main()
