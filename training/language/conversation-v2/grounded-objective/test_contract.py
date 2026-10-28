import copy,json,pathlib,unittest
from train import batch
H=pathlib.Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_teacher_shift_and_EOS(self):
  r={'sequence':[1,3,10,2,4,20,21,2],'answer_start':5,'answer_ids':[20,21,2]};x,y,d=batch([r],'response');self.assertEqual(y[0,:7].tolist(),[-100,-100,-100,-100,20,21,2]);self.assertEqual(x[0,4].item(),4);self.assertEqual(d['supervised_targets'],3)
 def test_same_inputs_different_only_teacher_mask(self):
  d=json.loads((H/'data.json').read_text())['train'][:4];a,y,_=batch(d,'full');b,z,_=batch(d,'response');self.assertTrue(a.equal(b));self.assertTrue(y[z!=-100].equal(z[z!=-100]))
 def test_entity_and_oldDEV_disjoint(self):
  d=json.loads((H/'data.json').read_text());self.assertFalse({r['entity']for r in d['train']}&{r['entity']for r in d['dev']});old={c['source']['entity_family']for c in json.loads((H.parent/'response-data/final/active-dev.json').read_text())['cases']};self.assertFalse(old&{r['entity']for rows in d.values()for r in rows})
 def test_no_teacher_or_context_truncation(self):
  d=json.loads((H/'data.json').read_text())
  for rows in d.values():
   for r in rows:self.assertEqual(r['sequence'],r['prefix']+r['answer_ids']);self.assertLessEqual(len(r['sequence']),257);self.assertEqual(r['answer_ids'][-1],2)
if __name__=='__main__':unittest.main()
