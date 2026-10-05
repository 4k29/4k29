"""Behavioral raw causal/compute/checkpoint verification, no implementation-mirror QA tests."""
import copy,importlib.util,pathlib,random,tempfile,unittest
import torch
from torch.nn import functional as F
from model import Decoder

class RawModelTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1);torch.manual_seed(429)
        self.config=dict(vocabulary=300,dim=24,layers=2,heads=3,hidden=96,context=32,dropout=.1)
    def test_future_tokens_do_not_change_earlier_predictions(self):
        model=Decoder(self.config).eval();a=torch.tensor([[1,45,60,70,80]]);b=torch.tensor([[1,45,60,170,180]])
        with torch.no_grad():x=model(a);y=model(b)
        torch.testing.assert_close(x[:,:3],y[:,:3],rtol=0,atol=0);self.assertFalse(torch.equal(x[:,3:],y[:,3:]))
    def test_fused_causal_operator_matches_original_own_explicit_attention(self):
        spec=importlib.util.spec_from_file_location('original',pathlib.Path(__file__).resolve().parents[1]/'train-transformer.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        ours=Decoder(self.config).eval();reference=module.Decoder(self.config).eval();reference.load_state_dict(ours.state_dict());tokens=torch.tensor([[1,22,65,129,250]])
        torch.testing.assert_close(ours(tokens),reference(tokens),rtol=1e-5,atol=1e-6)
    def test_optimizer_and_rng_checkpoint_resumes_identical_next_update(self):
        model=Decoder(self.config);optimizer=torch.optim.AdamW(model.parameters(),lr=.0005);rng=random.Random(429)
        def update(model,opt):
            tokens=torch.randint(6,300,(2,16));opt.zero_grad();loss=F.cross_entropy(model(tokens).reshape(-1,300),tokens.roll(-1,1).reshape(-1));loss.backward();opt.step();return loss.detach()
        update(model,optimizer)
        with tempfile.TemporaryDirectory() as folder:
            path=pathlib.Path(folder)/'checkpoint.pt';torch.save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()),path)
            expected=update(model,optimizer);expected_random=rng.random();expected_state=copy.deepcopy(model.state_dict())
            restored=torch.load(path,weights_only=False);other=Decoder(self.config);other.load_state_dict(restored['model']);opt=torch.optim.AdamW(other.parameters());opt.load_state_dict(restored['optimizer']);torch.set_rng_state(restored['torchRng']);rng.setstate(restored['pythonRng'])
            actual=update(other,opt);self.assertEqual(float(actual),float(expected));self.assertEqual(rng.random(),expected_random)
            for name,t in other.state_dict().items():torch.testing.assert_close(t,expected_state[name],rtol=0,atol=0)
if __name__=='__main__':unittest.main()
