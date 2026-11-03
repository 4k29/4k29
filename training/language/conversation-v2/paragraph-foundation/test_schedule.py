import unittest
from schedule import references,batches,verify
class Schedule(unittest.TestCase):
 def test_teacher_once_across_cuts(self):
  corpus=[dict(id='a',tokens=[1]+list(range(10,610))+[2]),dict(id='b',tokens=[1,10,11,2])];refs=references(corpus,[0,1]);bs=batches(corpus,refs,604,64);audit=verify(corpus,bs);self.assertEqual(audit['targets'],604);self.assertEqual(audit['EOS_targets'],2);self.assertEqual(audit['duplicate_teacher_positions'],0)
 def test_equal_budget_different_lengths(self):
  a=[dict(id=str(i),tokens=[1]+[10]*9+[2])for i in range(100)];b=[dict(id=str(i),tokens=[1]+[10]*299+[2])for i in range(4)]
  aa=verify(a,batches(a,references(a,range(100)),777,128));bb=verify(b,batches(b,references(b,range(4)),777,128));self.assertEqual(aa['target_counts'],bb['target_counts']);self.assertEqual(aa['targets'],777)
if __name__=='__main__':unittest.main()
