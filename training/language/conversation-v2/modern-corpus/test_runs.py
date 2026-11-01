import unittest
from build_prose_runs import runs
class RunTests(unittest.TestCase):
 def row(self,a,p,b):return dict(article_id=a,source_paragraph_index=p,source_block_index=b)
 def test_consecutive(self):
  self.assertEqual([len(x)for x in runs([self.row(1,0,1),self.row(1,1,2)])],[2])
 def test_excluded_paragraph_barrier(self):
  self.assertEqual([len(x)for x in runs([self.row(1,0,1),self.row(1,2,3)])],[1,1])
 def test_heading_barrier(self):
  self.assertEqual([len(x)for x in runs([self.row(1,0,1),self.row(1,1,3)])],[1,1])
 def test_article_barrier(self):
  self.assertEqual([len(x)for x in runs([self.row(1,0,1),self.row(2,1,2)])],[1,1])
 def test_empty(self):self.assertEqual(list(runs([])),[])
if __name__=='__main__':unittest.main()
