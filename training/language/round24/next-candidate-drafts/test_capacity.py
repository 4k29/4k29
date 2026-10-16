import sys,unittest,copy
sys.path.insert(0,'/workspace/4k29/training/language')
import torch
from model import Decoder
from capacity import expand_ffn_weights,expand_optimizer_moments
torch.set_num_threads(1)
class Tests(unittest.TestCase):
 def test_function_moments_and_new_features_learn(self):
  torch.manual_seed(11);cfg=dict(vocabulary=20,dim=8,layers=2,heads=2,hidden=16,context=16,dropout=.1,epsilon=1e-5)
  old=Decoder(cfg);opt=torch.optim.AdamW(old.parameters(),lr=.001);x=torch.tensor([[1,6,7,8,9,6,7,8]]);y=x.roll(-1,1)
  opt.zero_grad();torch.nn.functional.cross_entropy(old(x).flatten(0,1),y.flatten()).backward();opt.step()
  parent=copy.deepcopy(dict(config=cfg,model=old.state_dict(),optimizer=opt.state_dict()))
  new=Decoder(dict(cfg,hidden=32));expand_ffn_weights(new,parent)
  old.eval();new.eval();torch.testing.assert_close(old(x),new(x),rtol=1e-6,atol=1e-6)
  no=torch.optim.AdamW(new.parameters(),lr=.001);no.load_state_dict(parent['optimizer']);expand_optimizer_moments(no,new,parent)
  by_name=dict(old.named_parameters())
  for name,p in new.named_parameters():
   a=opt.state[by_name[name]];b=no.state[p];self.assertTrue(torch.equal(a['step'],b['step']))
   for key in ['exp_avg','exp_avg_sq']:
    q=b[key]
    if name.endswith(('fc1.weight','fc1.bias')):
     self.assertTrue(torch.equal(a[key],q[:16]));self.assertEqual(float(q[16:].abs().sum()),0)
    elif name.endswith('fc2.weight'):
     self.assertTrue(torch.equal(a[key],q[:,:16]));self.assertEqual(float(q[:,16:].abs().sum()),0)
    else:self.assertTrue(torch.equal(a[key],q))
  new.train();no.zero_grad();torch.nn.functional.cross_entropy(new(x).flatten(0,1),y.flatten()).backward()
  for block in new.blocks:
   self.assertEqual(float(block.fc1.weight.grad[16:].abs().sum()),0)
   self.assertGreater(float(block.fc2.weight.grad[:,16:].abs().sum()),0)
  no.step();no.zero_grad();torch.nn.functional.cross_entropy(new(x).flatten(0,1),y.flatten()).backward()
  for block in new.blocks:self.assertGreater(float(block.fc1.weight.grad[16:].abs().sum()),0)
 def test_expanded_optimizer_exact_resume(self):
  torch.manual_seed(22);cfg=dict(vocabulary=20,dim=8,layers=1,heads=2,hidden=16,context=16,dropout=.1,epsilon=1e-5)
  old=Decoder(cfg);oo=torch.optim.AdamW(old.parameters(),lr=.001);x=torch.tensor([[1,6,7,8,9,10,11,12]]);y=x.roll(-1,1)
  def step(m,o):
   m.train();o.zero_grad();loss=torch.nn.functional.cross_entropy(m(x).flatten(0,1),y.flatten());loss.backward();o.step();return loss.detach()
  step(old,oo);parent=copy.deepcopy(dict(config=cfg,model=old.state_dict(),optimizer=oo.state_dict()));newcfg=dict(cfg,hidden=32);m=Decoder(newcfg);expand_ffn_weights(m,parent);o=torch.optim.AdamW(m.parameters(),lr=.001);o.load_state_dict(parent['optimizer']);expand_optimizer_moments(o,m,parent)
  step(m,o);saved=copy.deepcopy(dict(model=m.state_dict(),optimizer=o.state_dict(),rng=torch.get_rng_state()));expected=step(m,o);end=torch.get_rng_state().clone()
  n=Decoder(newcfg);no=torch.optim.AdamW(n.parameters(),lr=.001);n.load_state_dict(saved['model']);no.load_state_dict(saved['optimizer']);torch.set_rng_state(saved['rng']);actual=step(n,no)
  self.assertTrue(torch.equal(expected,actual));self.assertTrue(torch.equal(end,torch.get_rng_state()));self.assertTrue(all(torch.equal(v,n.state_dict()[k]) for k,v in m.state_dict().items()))
  for key,state in o.state_dict()['state'].items():self.assertTrue(all(torch.equal(v,no.state_dict()['state'][key][name]) for name,v in state.items()))
 def test_reject_other_architecture_change(self):
  cfg=dict(vocabulary=20,dim=8,layers=1,heads=2,hidden=16,context=16,dropout=.1,epsilon=1e-5);old=Decoder(cfg)
  new=Decoder(dict(cfg,hidden=32,context=32))
  with self.assertRaises(AssertionError):expand_ffn_weights(new,dict(config=cfg,model=old.state_dict()))
if __name__=='__main__':unittest.main()
