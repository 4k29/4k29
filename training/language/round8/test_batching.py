"""Verify that shorter padding changes neither causal logits nor target data."""
import collections,json,pathlib,random,sys,unittest
sys.path.insert(1,str(pathlib.Path(__file__).resolve().parent.parent))
import torch
from batching import sampler,draw,WIDTHS,VIEWS
from train import Decoder,load_partition,pack,read,ROOT

class BatchingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1);torch.manual_seed(929)
        cls.info,cls.values=load_partition(ROOT/'unicode-bpe-4578','train')
        cls.genres={'aozora':.35,'mic':.1,'env':.1,'mdn':.25,'jma':.15,'maff':.05}
        cls.strata,cls.weights,cls.masses=sampler(cls.info['rows'],cls.genres)
        cls.views=VIEWS;cls.draw=staticmethod(draw)
    def test_sampling_marginals_and_every_row_probability(self):
        counts=collections.Counter((r['site'],r['variant']) for r in self.info['rows'])
        for key,rows in self.strata.items():
            actual=self.masses[key[2]]*(self.weights[key]/self.masses[key[2]])/len(rows)
            expected=self.genres[key[0]]*self.views[key[1]]/counts[key[:2]]
            self.assertAlmostEqual(actual,expected,places=15)
        rng=random.Random(10429);observed=collections.Counter();views=collections.Counter()
        for _ in range(5000):
            width,rows=self.draw(rng,8,self.strata,self.weights,self.masses)
            self.assertTrue(all(r['length']-1<=width for r in rows))
            for r in rows:observed[r['site']]+=1;views[r['variant']]+=1
        for k,p in self.genres.items():self.assertLess(abs(observed[k]/40000-p),.012)
        for k,p in self.views.items():self.assertLess(abs(views[k]/40000-p),.015)
    @torch.no_grad()
    def test_causal_logits_and_targets_identical_after_removing_future_padding(self):
        tok=read(ROOT/'unicode-bpe-4578/tokenizer.json')
        model=Decoder(dict(vocabulary=len(tok['bytes']),dim=192,layers=8,heads=4,hidden=768,context=256,dropout=.1,epsilon=1e-5));model.eval()
        for width in WIDTHS:
            key=next(k for k in self.strata if k[2]==width);r=self.strata[key][0]
            a,ya=pack([r],self.values,256);b,yb=pack([r],self.values,width)
            self.assertTrue(torch.equal(ya[:,:width],yb));self.assertTrue(ya[:,width:].eq(-100).all())
            logits_a=model(a)[:,:width];logits_b=model(b)
            self.assertTrue(torch.allclose(logits_a,logits_b,atol=1e-5,rtol=1e-5))

if __name__=='__main__':unittest.main()
