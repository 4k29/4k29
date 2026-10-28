import unittest
from runtime import torch
from eval_core import greedy as original
from prose_decode import greedy as fragment
class FixedLogits(torch.nn.Module):
 config={'context':256}
 def __init__(self):super().__init__();self.inputs=[]
 def forward(self,x):
  self.inputs.append(x.tolist()[0]);v=torch.zeros((1,x.shape[1],100));v[:,:,(90 if x.shape[1]<3 else 2)]=10;return v
class Decoder(unittest.TestCase):
 def test_same_BOS_paths_and_no_vocab_mask(self):
  p=[b'']*6+[bytes([i])for i in range(94)]
  self.assertEqual(original(FixedLogits(),[1,7],p,max_new=4),fragment(FixedLogits(),[1,7],p,max_new=4))
 def test_no_fake_BOS_inserted(self):
  m=FixedLogits();p=[b'']*6+[bytes([i])for i in range(94)];fragment(m,[90,91],p,max_new=4);self.assertEqual(m.inputs[0],[90,91])
if __name__=='__main__':unittest.main()
