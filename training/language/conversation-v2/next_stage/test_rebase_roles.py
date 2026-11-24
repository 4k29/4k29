import json,pathlib,unittest
from rebase_roles import rebase_human_prefix
H=pathlib.Path(__file__).resolve().parents[1]
class HumanRoleContract(unittest.TestCase):
    def test_identity_and_swap_agree(self):
        a=[1,3,10,11,2,4,12,2,3];b=[1,4,10,11,2,3,12,2,4]
        self.assertEqual(rebase_human_prefix(a)[0],rebase_human_prefix(b)[0])
        self.assertEqual(a,[1,3,10,11,2,4,12,2,3])
    def test_no_missing_end_or_same_speaker(self):
        for bad in [[1,4,10,3],[1,3,10,2,3],[1,4,10,1,3]]:
            with self.assertRaises(ValueError):rebase_human_prefix(bad)
    def test_all_original_cases_preserve_body_and_boundaries(self):
        p=H/'data/benchmark-dev.json';cases=json.loads(p.read_text())['cases'];changed=0
        for c in cases:
            before=c['prefixTokens'];after,meta=rebase_human_prefix(before)
            self.assertEqual(after[1],3);self.assertEqual(after[0],1)
            self.assertEqual([t for t in before if t>=6],[t for t in after if t>=6])
            self.assertEqual([i for i,t in enumerate(before)if t==2],[i for i,t in enumerate(after)if t==2])
            changed+=before!=after
        self.assertEqual(changed,19)
if __name__=='__main__':unittest.main()
