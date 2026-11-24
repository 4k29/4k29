import unittest
from admission import rights_gate, withdrawal_plan


class GovernanceTest(unittest.TestCase):
    def test_public_is_not_permission(self):
        self.assertFalse(rights_gate({'public_api': True}, '2026-10-27')['rights_qualified'])

    def test_all_grants_still_not_admission(self):
        s = dict(evidence=['official-license'], reviewed_on='2026-10-27',
                 recheck_by='2026-11-27', license='CC-BY-SA-4.0', attribution='authors',
                 permissions={k: 'allowed' for k in ('acquisition','storage','training','redistribution')})
        result = rights_gate(s, '2026-10-27')
        self.assertTrue(result['rights_qualified'])
        self.assertFalse(result['final_training_admitted'])
        self.assertFalse(rights_gate(s, '2026-12-01')['rights_qualified'])

    def test_withdrawal_source_scope_and_transitive_descendants(self):
        records = [dict(source=s,id='thread',speakers=['speaker']) for s in ['one','two']]
        artifacts = [dict(id='raw',record_ids=['one/thread']),
                     dict(id='tokens',parents=['raw']),dict(id='weights',parents=['tokens']),
                     dict(id='other',record_ids=['two/thread'])]
        r = withdrawal_plan(records,[dict(source='one',kind='speaker',id='speaker')],artifacts)
        self.assertEqual(r['excluded_records'], ['one/thread'])
        self.assertEqual(r['invalidate_artifacts'], ['raw','tokens','weights'])
        self.assertFalse(r['model_unlearning_performed'])

    def test_invalid_lineage_rejected(self):
        with self.assertRaises(ValueError):
            withdrawal_plan([],[],[dict(id='x',parents=['missing'])])


if __name__ == '__main__':
    unittest.main()
