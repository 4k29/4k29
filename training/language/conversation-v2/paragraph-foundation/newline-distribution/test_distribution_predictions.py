import math,unittest
from distribution_predictions import summarize
class PredictionSummaryContracts(unittest.TestCase):
 def test_probabilities_ranks_and_entropy(self):
  p=[.5,.3,.2];s=summarize([math.log(x)for x in p],2,mata=1,nl=0)
  self.assertAlmostEqual(s['newline']['P'],.5)
  self.assertEqual(s['mata']['rank'],2);self.assertEqual(s['gold']['rank'],3)
  self.assertAlmostEqual(s['entropy_nats'],-sum(x*math.log(x)for x in p))
 def test_ties_are_min_rank_without_filtering(self):
  s=summarize([0.,0.,0.],2,mata=1,nl=0)
  self.assertEqual(s['argmax'],0)
  self.assertEqual([x['token']for x in s['top5']],[0,1,2])
  self.assertEqual(s['gold']['rank'],1)
if __name__=='__main__':unittest.main()
