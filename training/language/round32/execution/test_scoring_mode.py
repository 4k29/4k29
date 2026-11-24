"""Meaningful guard: inference-consistent negative scoring still backpropagates,
restores caller mode/global RNG, and restores mode even on scoring failure.
"""
import pathlib,sys,unittest,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from sequence_objective import rollout_unlikelihood
class Probe(torch.nn.Module):
 def __init__(self,fail=False):
  super().__init__();self.config={'context':128};self.logits=torch.nn.Parameter(torch.tensor([0.,0.,-10.,0.,0.,0.,4.,0.]));self.modes=[];self.fail=fail
 def forward(self,x):
  self.modes.append((self.training,torch.is_grad_enabled()))
  if self.fail and torch.is_grad_enabled():raise RuntimeError('scoring failure')
  return self.logits.view(1,1,-1).expand(x.shape[0],x.shape[1],-1)
class Tests(unittest.TestCase):
 def test_eval_gradient_mode_rng(self):
  m=Probe();m.train();torch.manual_seed(2049);before=torch.get_rng_state().clone();loss,record=rollout_unlikelihood(m,torch.tensor([[1,6,6,6,6]]),8)
  self.assertTrue(m.training);self.assertTrue(torch.equal(before,torch.get_rng_state()));self.assertTrue(all(not train for train,grad in m.modes));self.assertEqual(m.modes[-1],(False,True));self.assertGreater(record['negativePositions'],0);loss.backward();self.assertTrue(torch.isfinite(m.logits.grad).all());self.assertGreater(float(m.logits.grad.abs().sum()),0)
 def test_eval_caller_preserved(self):
  m=Probe();m.eval();rollout_unlikelihood(m,torch.tensor([[1,6,6,6,6]]),8);self.assertFalse(m.training)
 def test_exception_restores_training_mode_rng(self):
  m=Probe(True);m.train();before=torch.get_rng_state().clone()
  with self.assertRaisesRegex(RuntimeError,'scoring failure'):rollout_unlikelihood(m,torch.tensor([[1,6,6,6,6]]),8)
  self.assertTrue(m.training);self.assertTrue(torch.equal(before,torch.get_rng_state()))
if __name__=='__main__':unittest.main()
