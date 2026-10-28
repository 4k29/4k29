import gzip,json,unittest
import numpy as np
from runtime import H,V,pack as pure
from mixed_runtime import pack
class Mixture(unittest.TestCase):
 def test_shared_data_and_all_teacher_lengths_match(self):
  a=json.load(gzip.open(H/'schedule.json.gz','rt'));b=json.load(gzip.open(H/'mixed-schedule.json.gz','rt'));self.assertEqual(a['targets'],b['targets']);self.assertEqual(a['updates'],b['updates'])
  for x,y in zip(a['batches'],b['batches']):
   self.assertEqual(x[:2],y[:2]);xa,ya=pure(x);xb,yb=pack(y);self.assertEqual(ya.ne(-100).tolist(),yb.ne(-100).tolist());self.assertEqual(xa.ne(0).tolist(),xb.ne(0).tolist())
 def test_RP_original_positions_unique_and_no_invented_marker(self):
  meta=json.loads((V/'data/data.json').read_text());values=np.fromfile(H.parents[3]/meta['trainTokensPath'],dtype='<u4');d=json.load(gzip.open(H/'mixed-schedule.json.gz','rt'));intervals=[]
  for b in d['batches']:
   for r in b[2:]:
    w=meta['trainWindows'][r['rp_window']];self.assertEqual(w['document'],r['document']);self.assertEqual(values[w['offset']:w['offset']+r['rp_length']].tolist(),r['tokens']);intervals.append((r['rp_offset']+1,r['rp_offset']+r['rp_length']))
  intervals.sort();self.assertTrue(all(a[1]<=b[0]for a,b in zip(intervals,intervals[1:])))
if __name__=='__main__':unittest.main()
