import tempfile,pathlib,unittest,json,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rollout_trace import reconcile_trace
class TraceTests(unittest.TestCase):
 def test_retain_checkpoint_and_archive_later_work(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'training-rollouts.jsonl'
   rows=[dict(step=s,generatedTokens=8,negativePositions=2) for s in [10,20,30]]
   p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
   reconcile_trace(p,20,2,16,4)
   self.assertEqual([json.loads(x)['step'] for x in p.read_text().splitlines()],[10,20])
   archives=list(pathlib.Path(d).glob('unretained-*'));self.assertEqual(len(archives),1)
   self.assertEqual(json.loads(archives[0].read_text())['step'],30)
   reconcile_trace(p,20,2,16,4)
 def test_missing_or_wrong_retained_counts_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'training-rollouts.jsonl'
   with self.assertRaises(AssertionError):reconcile_trace(p,10,1,8,2)
   p.write_text(json.dumps(dict(step=10,generatedTokens=8,negativePositions=2))+'\n')
   with self.assertRaises(AssertionError):reconcile_trace(p,10,1,7,2)
if __name__=='__main__':unittest.main()
