import unittest
from newline_top_candidates import candidate_summary

class CandidateReportingContracts(unittest.TestCase):
    def test_excludes_only_newline_and_keeps_special(self):
        r=candidate_summary([1.,2.,4.],[.1,.3,.6],[b'',b'a',b'\n'],2,1)
        self.assertEqual(r['top_non_newline']['token'],1)
        self.assertEqual(r['top_non_newline']['probability'],.3)
        self.assertAlmostEqual(r['top_non_newline']['conditional_probability_given_not_newline'],.75)
        self.assertTrue(r['top_non_newline']['special'])
    def test_spaces_are_not_silently_skipped(self):
        r=candidate_summary([3.,2.,4.],[.3,.1,.6],[b' ',b'a',b'\n'],2,1)
        self.assertEqual(r['top_non_newline']['token'],0)
        self.assertTrue(r['top_non_newline']['whitespace_only'])
    def test_tie_rank_and_incomplete_utf8_are_explicit(self):
        r=candidate_summary([2.,2.,4.],[.2,.2,.6],[b'\xe3',b'a',b'\n'],2,1)
        self.assertEqual(r['gold']['full_vocabulary_rank'],2)
        self.assertTrue(r['top_non_newline']['incomplete_UTF8_piece'])

if __name__=='__main__':unittest.main()
