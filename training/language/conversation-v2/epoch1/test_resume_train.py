import importlib.util,pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('resume_fix',HERE/'resume_train.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ResumeTests(unittest.TestCase):
    def test_exact_single_assignment(self):
        source=(HERE/'continue_train.py').read_text();changed,audit=m.transform(source)
        self.assertTrue(audit['allOtherAstNodesIdentical']);self.assertTrue(audit['onlyPfpathAssignmentChanged'])
        self.assertEqual(changed.replace(m.NEW,m.OLD),source)
    def test_missing_target_rejected(self):
        with self.assertRaises(ValueError):m.transform('x=3\n')
    def test_duplicate_target_rejected(self):
        with self.assertRaises(ValueError):m.transform(m.OLD+'\n'+m.OLD)
if __name__=='__main__':unittest.main()
