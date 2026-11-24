"""Small raw-FP32 transport and immutable-trajectory schema checks only."""
import pathlib,tempfile,unittest,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import torch,numpy as np
from parity_epoch import checkpoint,emit_binary

class RawParityContract(unittest.TestCase):
 def test_exact_f32_transport_sorted_extents(self):
  weights={'z':torch.tensor([[1.0000001192092896,-3.1415927410125732]],dtype=torch.float32),'a':torch.tensor([0.,-0.,1.e-30],dtype=torch.float32)}
  with tempfile.TemporaryDirectory(dir='/dev/shm') as tmp:
   p=pathlib.Path(tmp)/'test.f32';specs,n=emit_binary(weights,p);raw=np.frombuffer(p.read_bytes(),dtype='<f4')
   self.assertEqual(n,5);self.assertEqual(specs['a']['floatOffset'],0);self.assertEqual(specs['z']['floatOffset'],3)
   for name,t in weights.items():
    row=specs[name];part=raw[row['floatOffset']:row['floatOffset']+row['floatCount']].reshape(row['shape'])
    self.assertEqual(part.tobytes(),t.numpy().tobytes())
 def test_authoritative_trajectory_schema(self):
  s={'trajectory':{'config':{'context':256},'model':{'sample':torch.tensor([1.])},'uniqueUpdates':3470},'config':{'wrong':True}}
  c,w,n=checkpoint(s);self.assertEqual(c,{'context':256});self.assertEqual(n,3470);self.assertTrue(torch.equal(w['sample'],torch.tensor([1.])))
 def test_nonfinite_transport_rejected(self):
  with tempfile.TemporaryDirectory(dir='/dev/shm') as tmp:
   with self.assertRaises(ValueError):emit_binary({'bad':torch.tensor([float('nan')])},pathlib.Path(tmp)/'test.f32')

if __name__=='__main__':unittest.main()
