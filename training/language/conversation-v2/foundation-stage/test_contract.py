import gzip,json,pathlib,tempfile,unittest
from unittest.mock import patch
from runtime import H,torch,pack,save
class Contract(unittest.TestCase):
 def test_all_boundary_and_target_accounting(self):
  rows={r['id']:r for r in map(json.loads,gzip.open(H/'data.jsonl.gz','rt'))};d=json.load(gzip.open(H/'schedule.json.gz','rt'));covered={k:[]for k,r in rows.items()if r['split']=='train'}
  for b in d['batches']:
   x,y=pack(b)
   for i,w in enumerate(b):
    r=rows[w['unit_id']];s=w['offset'];self.assertEqual(w['tokens'],r['tokens'][s:s+257]);covered[r['id']]+=list(range(s+1,s+len(w['tokens'])))
    self.assertEqual(y[i,:len(w['tokens'])-1].tolist(),w['tokens'][1:]);self.assertTrue(y[i,len(w['tokens'])-1:].eq(-100).all())
  for key,positions in covered.items():self.assertEqual(positions,list(range(1,len(rows[key]['tokens']))))
 def test_no_known_source_component_or_canonical_overlap(self):
  d=list(map(json.loads,gzip.open(H/'data.jsonl.gz','rt')));tr=[r for r in d if r['split']=='train'];de=[r for r in d if r['split']=='dev']
  for key in ['component','family']:self.assertFalse({r[key]for r in tr}&{r[key]for r in de})
  self.assertFalse({''.join(r['text'].split())for r in tr}&{''.join(r['text'].split())for r in de})
 def test_atomic_failure_keeps_previous(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'model.pt';save(p,{'saved':1});before=p.read_bytes()
   with patch.object(torch,'save',side_effect=OSError('injected storage failure')):
    with self.assertRaises(OSError):save(p,{'saved':2})
   self.assertEqual(p.read_bytes(),before)
if __name__=='__main__':unittest.main()
