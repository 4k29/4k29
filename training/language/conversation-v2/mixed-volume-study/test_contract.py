import unittest,json,gzip,pathlib
P=pathlib.Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_targets(self):
  a=json.loads((P/'SOURCE_AUDIT.json').read_text());self.assertEqual(a['additional_unique_teacher_positions'],409856);self.assertEqual(a['overlap'],0);self.assertEqual(a['cumulative_unique_teacher_positions'],1000000)
 def test_JMA(self):
  a=json.loads((P/'SOURCE_AUDIT.json').read_text());self.assertEqual(a['availability']['jma']['raw_unused_upper_bound'],6730);self.assertEqual(a['source_stats']['jma']['actual'],6149)
 def test_budgets(self):
  s=json.load(gzip.open(P/'schedule.json.gz','rt'));self.assertEqual(len(s),401);self.assertEqual(sum(r['length']-1 for b in s[:205] for r in b),209856);self.assertEqual(sum(r['length']-1 for b in s for r in b),409856)
 def test_teacher_and_prefix(self):
  a=json.loads((P/'TEACHER_AUDIT.json').read_text());self.assertTrue(a['passed']);self.assertTrue(a['all_byte_roundtrips']);self.assertEqual(a['prefix_positions'],590144)
if __name__=='__main__':unittest.main()
