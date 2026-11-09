import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from build import collapse
class Contract(unittest.TestCase):
 def test_LF_only(self):self.assertEqual(collapse([1,600,16,16,700,2]),([1,600,16,700,2],[0,1,2,4,5]))
 def test_multiple_layout(self):self.assertEqual(collapse([1,16,16,16,600,2])[0],[1,16,600,2])
 def test_RP_roles(self):
  t=[1,3,600,16,16,601,2,4,700,2];n,k=collapse(t);self.assertEqual([v for v in n if v<6],[1,3,2,4,2]);self.assertEqual([t[i] for i in k],n)
 def test_true_end_not_fabricated(self):self.assertEqual(collapse([600,16,16,700])[0],[600,16,700])
if __name__=='__main__':unittest.main()
