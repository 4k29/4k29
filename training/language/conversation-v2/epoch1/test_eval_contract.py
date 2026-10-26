import json,pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE/'next_stage'));from rebase_roles import rebase_human_prefix
class ContractTests(unittest.TestCase):
 def test_all_frozen_panels(self):
  for name in ['unified32-dev.json','content-dev.json']:
   for c in json.loads((HERE/name).read_text())['cases']:
    with self.subTest(name=name,id=c['id']):
     q,_=rebase_human_prefix(c['originalPrefixTokens']);self.assertEqual(q,c['prefixTokens']);self.assertEqual(q[:2],[1,3]);self.assertEqual(q[-1],c['targetLocalRoleToken']);self.assertLessEqual(len(q)+192,256)
     self.assertEqual([t for t in q if t not in(3,4)],[t for t in c['originalPrefixTokens']if t not in(3,4)])
     self.assertEqual(rebase_human_prefix(q)[0],q)
 def test_swap_restores(self):
  q=[1,4,7,8,2,3,9,2,4];a,_=rebase_human_prefix(q);self.assertEqual(a,[1,3,7,8,2,4,9,2,3])
 def test_bad_boundary_rejected(self):
  for q in [[1,3,8,4],[1,3,8,2,3],[1,5,8,2,4]]:
   with self.assertRaises(ValueError):rebase_human_prefix(q)
 def test_unique_disjoint(self):
  a=json.loads((HERE/'unified32-dev.json').read_text())['cases'];b=json.loads((HERE/'content-dev.json').read_text())['cases'];self.assertEqual(len(b),24);self.assertEqual(len({c['document']for c in b}),24);self.assertFalse(set(c['document']for c in a)&set(c['document']for c in b));self.assertTrue(all(c['contentRequired']for c in b))
if __name__=='__main__':unittest.main()
