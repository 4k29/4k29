import unittest
from newline_separator_probe import conditions, rank

class SeparatorProbeContracts(unittest.TestCase):
    def test_only_last_lf_removed_without_retokenizing(self):
        c=conditions([9,22,16,16],16)
        self.assertEqual(c['LF2'],([9,22,16,16],[0,1,2,3]))
        self.assertEqual(c['LF1'],([9,22,16],[0,1,2]))
        self.assertEqual(c['LF1_same_final_position'],([9,22,16],[0,1,3]))
    def test_requires_actual_double_lf(self):
        with self.assertRaises(AssertionError):conditions([9,16,22],16)
    def test_minimum_tie_rank(self):
        self.assertEqual(rank([2.,4.,4.,1.],1),1)
        self.assertEqual(rank([2.,4.,4.,1.],0),3)

if __name__=='__main__':unittest.main()
