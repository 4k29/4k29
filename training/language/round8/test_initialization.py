"""Validate own warm start, exact old logits and trainable added capacity."""
import pathlib,sys,unittest
import torch
sys.path.insert(1,str(pathlib.Path(__file__).resolve().parent.parent))
from model import Decoder
from initialization import initialize,read,ROOT,PARENT
class InitializationTests(unittest.TestCase):
    def test_identity_warm_start_and_gradient_flow(self):
        torch.set_num_threads(1);torch.manual_seed(1829)
        saved=torch.load(PARENT/'character-continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
        old=Decoder(saved['config']);old.load_state_dict(saved['beststate']);old.eval()
        tok=read(ROOT/'unicode-bpe-4578/tokenizer.json');config=dict(saved['config'],layers=8,vocabulary=len(tok['bytes']))
        model=Decoder(config);info=initialize(model,tok);model.eval()
        self.assertEqual(info['parentSelectedWeightLineageUpdates'],18000)
        self.assertEqual(info['parentSelectedChildSteps'],8000)
        self.assertTrue(torch.equal(model.token.weight[:4765],old.token.weight))
        self.assertEqual(int(model.token.weight[4765:].count_nonzero()),0)
        refs=read(PARENT/'character-continue-10000/validation.json')['references']
        with torch.no_grad():
            for ref in refs:
                t=torch.tensor([ref['tokens']]);a=old(t)[0,-1];b=model(t)[0,-1]
                torch.testing.assert_close(a,b[:4765],rtol=0,atol=2e-4)
                self.assertEqual(int(a.argmax()),int(b.argmax()))
            x=torch.randn(1,12,192)
            for block in model.blocks[4:]:self.assertTrue(torch.equal(block(x),x))
        self.assertTrue(all(p.requires_grad for p in model.parameters()))
        from train import load_partition,pack
        data,values=load_partition(ROOT/'unicode-bpe-4578','train');x,y=pack(data['rows'][:2],values,256)
        loss=torch.nn.functional.cross_entropy(model(x).reshape(-1,4840),y.reshape(-1));loss.backward()
        for block in model.blocks[4:]:
            self.assertGreater(float(block.proj.weight.grad.abs().sum()),0)
            self.assertGreater(float(block.fc2.weight.grad.abs().sum()),0)
        self.assertEqual(sum(p.numel() for p in model.parameters()),4537728)
        print('Own initial8-layer old logit/argmax parity and TRAIN gradient flow verified; optimizer updates0',flush=True)
if __name__=='__main__':unittest.main()
