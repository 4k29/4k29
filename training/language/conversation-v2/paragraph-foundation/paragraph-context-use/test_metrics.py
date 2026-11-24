import unittest,math,tempfile,pathlib,gzip,struct,hashlib
from metrics import summarize,js,distribution,teacher_input,archive_logits,input_hash,aggregate
class PairedDiagnosticContracts(unittest.TestCase):
 def test_log_probability_delta_and_rank(self):
  c=[-100.]*3997;u=c.copy();c[16]=0;c[400]=math.log(4);u[16]=math.log(4);u[400]=0
  a,_=summarize(c,400);b,_=summarize(u,400)
  self.assertAlmostEqual(a['gold']['logP']-b['gold']['logP'],math.log(4))
  self.assertEqual(a['gold']['rank'],1);self.assertEqual(b['gold']['rank'],2)
 def test_js_bounds_and_entropy(self):
  self.assertAlmostEqual(js([1,0],[0,1]),math.log(2))
  self.assertEqual(js([.25,.75],[.25,.75]),0)
  a,_=summarize([0.]*3997,8);self.assertAlmostEqual(a['entropy_nats'],math.log(3997))
 def test_signs_distribution_not_success(self):
  d=distribution([-1,.0,.2,.4]);self.assertEqual((d['positive'],d['zero'],d['negative']),(2,1,1));self.assertAlmostEqual(d['median'],.1)
 def test_teacher_shift_and_context_bound(self):
  x,positions=teacher_input([9,16,16],list(range(30,38)))
  self.assertEqual(x,[9,16,16]+list(range(30,37)));self.assertEqual(positions,list(range(2,10)))
  with self.assertRaises(AssertionError):teacher_input([9]*250,list(range(30,38)))
 def test_raw_float32_lossless_archive(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'a.gz';m=archive_logits(p,[[1.25,2.,-3.],[4.,5.,6.]])
   b=gzip.decompress(p.read_bytes());self.assertEqual(struct.unpack('<6f',b),(1.25,2.,-3.,4.,5.,6.));self.assertEqual(hashlib.sha256(b).hexdigest(),m['raw_sha256']);self.assertEqual(m['shape'],[2,3])
 def test_cache_hash_is_exact_token_order(self):
  self.assertEqual(input_hash([5,16,16]),input_hash([5,16,16]));self.assertNotEqual(input_hash([5,16]),input_hash([5,16,16]))
if __name__=='__main__':unittest.main()
