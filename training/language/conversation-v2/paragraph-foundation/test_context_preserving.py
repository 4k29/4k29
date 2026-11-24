import unittest
from context_preserving import row
class Context(unittest.TestCase):
 def test_batch_split_restores_prefix_and_masks_it(self):
  corpus=[dict(tokens=[1]+list(range(10,310))+[2])];ref=dict(record=0,start=188,length=69);x,y,m=row(corpus,ref);self.assertEqual(len(x),256);self.assertEqual(y[:188],[-100]*188);self.assertEqual(y[188:],corpus[0]['tokens'][189:257]);self.assertEqual(m['real_targets'],68)
 def test_original_window_boundary_keeps_existing_contract(self):
  corpus=[dict(tokens=[1]+list(range(10,610))+[2])];r=dict(record=0,start=256,length=257);x,y,m=row(corpus,r);self.assertEqual(x,corpus[0]['tokens'][256:512]);self.assertEqual(y,corpus[0]['tokens'][257:513]);self.assertEqual(m['prefix_only_positions'],0)
if __name__=='__main__':unittest.main()
