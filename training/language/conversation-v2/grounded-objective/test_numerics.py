"""Real parameters, no optimizer updates; publication and restart safeguards."""
import copy, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
from unittest.mock import patch
H=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent))
import torch
spec=importlib.util.spec_from_file_location('grounded_train',H/'train.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
from checkpoint_io import load
from core import restore, digest

class Numerical(unittest.TestCase):
    def test_completed_runners_cannot_silently_add_updates(self):
        paths=[H/'run/updates.jsonl',H/'run/contrast-updates.jsonl'];before=[p.read_bytes()for p in paths]
        for script in ['train.py','contrast.py']:
            p=subprocess.run([sys.executable,str(H/script)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('Completed',p.stderr)
        self.assertEqual(before,[p.read_bytes()for p in paths])

    def test_archive_real_state_and_isolated_adam(self):
        torch.set_num_threads(2)
        state=load('response-32')['trajectory']; baseline=digest(state)
        settings=json.loads((H.parent/'PLAN.json').read_text())['training']
        m1,o1,r1=restore(copy.deepcopy(state),settings)
        m2,o2,r2=restore(copy.deepcopy(state),settings)
        for a,b in zip(o1.state.values(),o2.state.values()):
            self.assertNotEqual(a['exp_avg'].data_ptr(),b['exp_avg'].data_ptr())
            self.assertTrue(torch.equal(a['exp_avg'],b['exp_avg']))
        rows=json.loads((H/'data.json').read_text())['train'][:4]
        x,y,_=runner.batch(rows,'response');loss=runner.causal_ce(m1(x),y);loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all()for p in m1.parameters()))
        self.assertEqual(digest(state),baseline)

    def test_failed_atomic_write_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'snapshot.pt';runner.save(p,{'complete':1});original=p.read_bytes()
            def failure(obj,f):
                f.write(b'incomplete');raise OSError('simulated disk-full/process failure before replace')
            with patch.object(torch,'save',side_effect=failure):
                with self.assertRaises(OSError):runner.save(p,{'complete':2})
            self.assertEqual(p.read_bytes(),original)
            self.assertTrue(p.with_suffix('.pending').exists())

if __name__=='__main__':unittest.main()
