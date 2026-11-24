import gzip,json,unittest
from common import *
from mixed_runtime import pack
class DataContract(unittest.TestCase):
 def test_exact_per_slot_teacher_and_input_budget(self):
  d=json.load(gzip.open(N/'schedule.json.gz','rt'))
  for a,b in zip(d['control'],d['boundary']):
   xa,ya=pack(a);xb,yb=pack(b);self.assertEqual(ya.ne(-100).tolist(),yb.ne(-100).tolist());self.assertEqual(xa.ne(0).tolist(),xb.ne(0).tolist());self.assertEqual(a[0],b[0]);self.assertEqual(a[-1],b[-1])
 def test_native_EOS_whole_original_paragraphs_only(self):
  d=json.loads((N/'paragraphs.json').read_text());train=d['train'];self.assertEqual(len(train),1024);self.assertEqual(len({r['id']for r in train}),1024)
  for r in train:self.assertNotEqual(r['source'],'jaquad');self.assertTrue(r['text'].endswith('。'));self.assertEqual(r['tokens'],[1]+r['body_tokens']+[2]);self.assertEqual(r['boundary'].split(',')[0],'Original processed paragraph')
  self.assertFalse({r['component']for r in train}&{r['component']for r in d['dev']})
 def test_no_original_target_position_repeats(self):
  d=json.load(gzip.open(N/'schedule.json.gz','rt'))
  for arm in ['control','boundary']:
   seen=set();rp=[]
   for b in d[arm]:
    for w in b:
     if 'unit_id'in w:
      for j in range(w['offset']+1,w['offset']+len(w['tokens'])):
       key=(w['unit_id'],j);self.assertNotIn(key,seen);seen.add(key)
     if 'rp_offset'in w:rp.append((w['rp_offset']+1,w['rp_offset']+len(w['tokens'])))
   rp.sort();self.assertTrue(all(a[1]<=b[0]for a,b in zip(rp,rp[1:])))
if __name__=='__main__':unittest.main()
