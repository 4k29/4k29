"""Frozen validation selection never consumes test rows or training RNG."""
import unittest
from train_curriculum import select_validation

class ValidationSelectionTests(unittest.TestCase):
    def rows(self):
        return [dict(id=str(i),kind='unknown' if i<60 else 'profile',history=[] if i%2 else [dict(question='MERは？',answer='TOKYO MERです。')],semantic=dict(subject='unverified' if i<60 else 'owner',attribute='unknown' if i<60 else 'field:'+str(i%6))) for i in range(180)]
    def test_default_keeps_identity_and_order(self):
        rows=self.rows();self.assertIs(select_validation(rows,0),rows);self.assertIs(select_validation(rows,200),rows)
    def test_strata_and_boundaries_are_deterministic_without_duplicate_rows(self):
        rows=self.rows();selected=select_validation(rows,64)
        self.assertEqual(selected,select_validation(rows[::-1],64)[::-1])
        self.assertEqual(len(selected),64);self.assertEqual(len({r['id'] for r in selected}),64)
        self.assertGreaterEqual(sum(r['kind']=='unknown' for r in selected),8)
        self.assertEqual({(r['semantic']['attribute'],bool(r['history'])) for r in selected},{(r['semantic']['attribute'],bool(r['history'])) for r in rows})

if __name__=='__main__':unittest.main()
