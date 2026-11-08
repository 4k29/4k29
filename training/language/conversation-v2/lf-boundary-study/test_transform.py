import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from build import collapse
class TransformTests(unittest.TestCase):
 def test_boundary_mapping(self):
  t=[1,600,16,16,700,2];a,k=collapse(t);self.assertEqual(a,[1,600,16,700,2]);self.assertEqual(k,[0,1,2,4,5]);self.assertEqual([t[i] for i in k],a)
 def test_no_other_changes(self):
  t=[1,600,16,700,2];self.assertEqual(collapse(t),(t,list(range(len(t)))))
 def test_unapproved_run_rejected(self):
  with self.assertRaises(AssertionError):collapse([600,16,16,16,700])
 def test_deleted_input_predecessor(self):
  t=[1,600,16,16,700,701,2];a,k=collapse(t);targets=[j for j in range(4,7) if j in k];start=k.index(targets[0])-1;self.assertEqual(a[start:],[16,700,701,2]);self.assertEqual([k[j] for j in range(start+1,len(a))],targets)
if __name__=='__main__':unittest.main()
