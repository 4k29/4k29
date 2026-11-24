import pathlib,sys,unittest,json,hashlib,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from context_preference import preference_loss,load_pool
sys.path.insert(0,str(R.parent));from model import Decoder
class Contracts(unittest.TestCase):
 def setUp(self):
  torch.set_num_threads(1);torch.manual_seed(7);self.m=Decoder(dict(vocabulary=32,dim=8,layers=1,heads=2,hidden=16,context=32,dropout=.3,epsilon=1e-5));self.pool=[dict(prefixTokens=[6,7,8],wrongPrefixTokens=[9,10,11],targetTokens=[12,13,14])]
 def test_rng_mode_targets_and_gradient(self):
  self.m.train();before=torch.get_rng_state().clone();copy=json.dumps(self.pool);loss,rec=preference_loss(self.m,self.pool,0);loss.backward();self.assertTrue(self.m.training);self.assertTrue(torch.equal(before,torch.get_rng_state()));self.assertEqual(json.dumps(self.pool),copy);self.assertTrue(torch.isfinite(loss));self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in self.m.parameters()));self.assertGreater(sum(float(p.grad.abs().sum()) for p in self.m.parameters()),0)
 def test_identical_context_cancels(self):
  self.pool[0]['wrongPrefixTokens']=self.pool[0]['prefixTokens'][:];self.m.eval();loss,rec=preference_loss(self.m,self.pool,0);loss.backward();self.assertAlmostEqual(float(loss.detach()),0.69314718,places=6);self.assertAlmostEqual(rec['meanContextGain'],0,places=7);self.assertLess(sum(float(p.grad.abs().sum()) for p in self.m.parameters()),1e-5);self.assertFalse(self.m.training)
 def test_swapping_changes_gain_sign(self):
  _,a=preference_loss(self.m,self.pool,0);r=self.pool[0];r['prefixTokens'],r['wrongPrefixTokens']=r['wrongPrefixTokens'],r['prefixTokens'];_,b=preference_loss(self.m,self.pool,0);self.assertAlmostEqual(a['meanContextGain'],-b['meanContextGain'],places=6)
 def test_pool_hash_binding(self):
  policy=json.loads((R/'policy.json').read_text())['contextPreference'];rows=load_pool(R/policy['pool'],policy['poolSha256']);self.assertEqual(len(rows),256)
  with self.assertRaises(AssertionError):load_pool(R/policy['pool'],'0'*64)
if __name__=='__main__':unittest.main()
