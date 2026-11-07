import gzip,json,unittest
from runtime import H
from response_train import batch
class Response(unittest.TestCase):
 def test_exact_position_and_budget_match(self):
  d=json.load(gzip.open(H/'response-schedule.json.gz','rt'));seen=set()
  for b in d:
   xa,ya=batch(b['control']);xb,yb=batch(b['treatment']);self.assertEqual(ya.ne(-100).tolist(),yb.ne(-100).tolist());self.assertEqual(xa.ne(0).tolist(),xb.ne(0).tolist())
   for arm in ['control','treatment']:
    for i,r in enumerate(b[arm]):self.assertEqual((ya if arm=='control'else yb)[i][(ya if arm=='control'else yb)[i].ne(-100)].tolist(),r['answer_ids'])
   for r in b['control']:self.assertNotIn(r['id'],seen);seen.add(r['id'])
 def test_no_rehearsal_boundary_fabrication(self):
  units={r['id']:r for r in map(json.loads,gzip.open(H/'data.jsonl.gz','rt'))};d=json.load(gzip.open(H/'response-schedule.json.gz','rt'));seen=set()
  for b in d:
   for r in b['treatment'][2:]:
    self.assertNotIn(r['source_unit'],seen);seen.add(r['source_unit']);u=units[r['source_unit']];self.assertEqual(u['split'],'train');self.assertEqual(r['sequence'],u['tokens'][r['offset']:r['offset']+len(r['sequence'])])
 def test_QA_DEV_is_not_foundation_or_response_TRAIN(self):
  d=json.loads((H/'qa-data.json').read_text());train={r['component']for r in d['train']};dev={r['component']for r in d['dev']};self.assertFalse(train&dev)
  native={r['component']for r in map(json.loads,gzip.open(H/'data.jsonl.gz','rt'))if r['split']=='train'};self.assertFalse(native&dev)
  for r in d['train']+d['dev']:self.assertEqual(r['context'][r['normalized_answer_start']:r['normalized_answer_start']+len(r['answer'])],r['answer'])
if __name__=='__main__':unittest.main()
