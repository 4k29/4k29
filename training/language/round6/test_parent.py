"""Verify exact own-character lineage and reject mismatched data/config."""
import pathlib,sys,unittest
import torch
from train import read,load_own_parent,OWN_PARENT,ROOT,Decoder
class ParentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.data=read(OWN_PARENT/'unicode-bpe-4503/data.json')
        cls.config=read(OWN_PARENT/'characters-10000/config.json')['config']
    def test_own_parent_and_actual_counters(self):
        saved=load_own_parent(self.data,self.config)
        model=Decoder(self.config);model.load_state_dict(saved['beststate'])
        self.assertTrue(all(torch.equal(model.state_dict()[k],v) for k,v in saved['beststate'].items()))
        self.assertEqual(saved['step'],10000)
        self.assertEqual(sorted({int(s['step']) for s in saved['optimizer']['state'].values()}),[10000])
        self.assertEqual(saved['beststep'],10000)
        original=read(OWN_PARENT/'generation-policy.json');current=read(ROOT/'generation-policy.json')
        for key in ['probes','rubric','acceptance','generation']:self.assertEqual(original[key],current[key])
        self.assertEqual((ROOT/'batching.py').read_bytes(),(OWN_PARENT/'batching.py').read_bytes())
    def test_mismatched_config_and_data_rejected(self):
        with self.assertRaisesRegex(ValueError,'config/selection'):load_own_parent(self.data,dict(self.config,dim=128))
        with self.assertRaisesRegex(ValueError,'source/fold/tokenizer'):load_own_parent(dict(self.data,tokenizerSha256='0'*64),self.config)
if __name__=='__main__':unittest.main()
