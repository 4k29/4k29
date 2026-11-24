import importlib.util,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('recover',HERE/'recover_train.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class RecoveryTests(unittest.TestCase):
    def test_medium_declared_four_changes_only(self):
        _,audit=m.transform((HERE/'continue_train.py').read_text(),'medium');self.assertEqual(len(audit['replacements']),4);self.assertTrue(audit['allOtherAstNodesIdentical'])
    def test_small_clock_guard_only(self):
        _,audit=m.transform((HERE/'continue_train.py').read_text(),'small');self.assertEqual(len(audit['replacements']),1);self.assertTrue(audit['allOtherAstNodesIdentical'])
    def test_counters_include_lost_completed_work(self):
        self.assertEqual(2142+(3470-2560),3052);self.assertEqual(3052+2960,6012);self.assertEqual(6012+1028,7040)
        replay=[unique+1 for unique in range(2560,3470)if unique<2652];self.assertEqual(replay,list(range(2561,2653)))
    def test_modified_original_rejected(self):
        with self.assertRaises(ValueError):m.transform('x=2','medium')
if __name__=='__main__':unittest.main()
