import unittest
from distribution_stats import CounterSet,lf_run_before,reference_sequences
def vocabulary():
 p=[b'']*3750
 p[6]=b'a';p[7]=b'.';p[8]='または'.encode();p[16]=b'\n';p[3749]='また'.encode()
 return p
class DistributionContracts(unittest.TestCase):
 def test_run_context_is_not_teacher_identity(self):
  t=[1,6,16,16,3749,7,2]
  self.assertEqual(lf_run_before(t,4),2)
  self.assertEqual(lf_run_before(t,4,3),1)
  c=CounterSet(3749,vocabulary())
  c.add(dict(tokens=t,text='a\n\nまた.',BOS=True),[dict(start=0,length=4),dict(start=3,length=4)])
  self.assertEqual(c.bins['after_LF_exact1'][16],1)
  self.assertEqual(c.bins['after_LF_exact2'][3749],1)
  self.assertEqual(c.bins['teacher_source_after_LF_exact2'][3749],1)
  self.assertEqual(c.bins['teacher_visible_after_LF_exact1'][3749],1)
 def test_duplicate_teacher_positions_rejected(self):
  c=CounterSet(3749,vocabulary())
  with self.assertRaises(AssertionError):
   c.add(dict(tokens=[1,6,7,2],text='a.',BOS=True),[dict(start=0,length=4),dict(start=0,length=3)])
 def test_literal_mata_is_not_exact_BPE_mata(self):
  c=CounterSet(3749,vocabulary());c.add(dict(tokens=[1,8,2],text='または',BOS=True))
  self.assertEqual(c.scalar['token_mata'],0);self.assertEqual(c.literal['all'],1)
  self.assertEqual(c.literal_next['は'],1)
 def test_no_invented_dialogue_display_newlines(self):
  r=dict(id='conversation',source='realpersona',text='a\n.',tokens=[1,3,6,2,4,7,2],
         utterances=[dict(text='a'),dict(text='.')])
  u=list(reference_sequences(r,vocabulary()))
  self.assertEqual([x['text']for x in u],['a','.'])
  self.assertTrue(u[0]['document_start']);self.assertFalse(u[1]['document_start'])
  c=CounterSet(3749,vocabulary())
  for x in u:c.add(x)
  self.assertEqual(c.bins['all_body_tokens'][16],0)
if __name__=='__main__':unittest.main()
