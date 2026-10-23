"""Verify intended source/view marginals and unbiased conditional row sampling."""
import pathlib,sys,unittest,collections,random,json
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from batching import sampler,draw,VIEWS
class SourceSampling(unittest.TestCase):
 def test_real_data_marginals_and_each_row_probability(self):
  p=json.loads((R/'policy.json').read_text());rows=json.loads((R/'multiview/train.index.json').read_text())['rows'];ss,w,m=sampler(rows,p['genreSampling']);by=collections.defaultdict(float);rates=collections.defaultdict(list)
  for k,prob in w.items():
   by[k[0],k[1],k[3]]+=prob;rates[k[0],k[1],k[3]].append(prob/len(ss[k]))
  for k,prob in by.items():
   expected=(p['humanSourceSampling'][k[2]]if k[0]=='human-chat'else p['genreSampling'][k[0]])*VIEWS[k[1]]
   self.assertAlmostEqual(prob,expected,places=12);self.assertLess(max(rates[k])-min(rates[k]),1e-14)
  self.assertAlmostEqual(sum(w.values()),1,places=12)
  a=random.Random(7);b=random.Random(7)
  for _ in range(100):
   x=draw(a,8,ss,w,m);self.assertEqual(x,draw(b,8,ss,w,m));self.assertTrue(all(r['length']-1<=x[0] for r in x[1]))
 def test_missing_human_source_rejected(self):
  with self.assertRaises(AssertionError):sampler([dict(site='human-chat',variant=0,length=30,document='jmrd:1')],{'human-chat':.3})
if __name__=='__main__':unittest.main()
