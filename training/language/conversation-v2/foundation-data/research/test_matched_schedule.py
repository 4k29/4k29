"""Partial-window pairing preserves real targets/EOS and original PAD masking."""
import copy,pathlib,sys,unittest
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from schedule_batches import sequences_for_step,pack_sequences
from core import pack

def fixture():
    seqs=[[1,3,6,2,4,7,2],[1,3,8,2],[8,2,4,9,2],[7,7,2]];flat=[];windows=[]
    for seq in seqs:windows.append(dict(offset=len(flat),length=len(seq)));flat+=seq
    native=np.array([1,6,6,6,2,1,6,2],dtype=np.uint32)
    index=[dict(partition='train',tokenFileOffset=0,length=5,trueDocumentEnd=True,offset=0,documentTokenCount=5),
        dict(partition='train',tokenFileOffset=5,length=3,trueDocumentEnd=True,offset=0,documentTokenCount=3)]
    row=dict(sharedRpWindowIndices=[0,1],controlReplacementRpWindowIndices=[2,3],treatmentNativeWindowPositions=[0,1],activeTargetCountBoth=15)
    return row,np.array(flat,dtype=np.uint32),windows,native,index

class MatchedScheduleTests(unittest.TestCase):
    def test_partial_inputs_have_equal_targets_and_padding_without_equal_eos(self):
        row,rp,windows,native,index=fixture();control,treatment=sequences_for_step(row,rp,windows,native,index)
        self.assertEqual(control[:2],treatment[:2]);self.assertEqual([len(x)for x in control],[len(x)for x in treatment])
        a=pack_sequences(control,16,pack);b=pack_sequences(treatment,16,pack)
        self.assertTrue((a[1]!=-100).equal(b[1]!=-100));self.assertEqual(int((a[1]!=-100).sum()),15)
        self.assertEqual(int((a[1]==-100).sum()),1009);self.assertNotEqual(a[2]['eosPositions'],b[2]['eosPositions'])
    def test_nontrain_native_is_rejected(self):
        args=fixture();args[-1][0]['partition']='dev'
        with self.assertRaisesRegex(ValueError,'non-TRAIN'):sequences_for_step(*args)
    def test_active_target_budget_tampering_is_rejected(self):
        args=fixture();args[0]['activeTargetCountBoth']=16
        with self.assertRaisesRegex(ValueError,'budget'):sequences_for_step(*args)
    def test_false_native_ending_is_rejected(self):
        args=fixture();args[-1][0]['trueDocumentEnd']=False
        with self.assertRaisesRegex(ValueError,'ending'):sequences_for_step(*args)

if __name__=='__main__':unittest.main()
