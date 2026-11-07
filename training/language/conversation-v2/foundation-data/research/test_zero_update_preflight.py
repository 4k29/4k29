"""Contract tests protect genuine TRAIN targets, EOS and no-update behavior."""
import ast,copy,hashlib,io,json,pathlib,tempfile,unittest
import torch
import zero_update_preflight as pf

def native():
    return dict(id='original',partition='train',format='native-prose-bos-body-eos',
        documentTokenOffset=0,documentTokenCount=257,tokens=[1]+[6]*255+[2])

class PreflightContractTests(unittest.TestCase):
    def test_full_genuine_body_eos_dose_without_padding(self):
        x,y,r=pf.pack_batch([native()for _ in range(4)],16)
        self.assertEqual(tuple(x.shape),(4,256));self.assertEqual(tuple(y.shape),(4,256))
        self.assertEqual(r['targetTokens'],1024);self.assertEqual(r['bodyTargets'],1020)
        self.assertEqual(r['eosTargets'],4);self.assertEqual(r['paddingTargets'],0)
    def test_dev_is_rejected_before_model_access(self):
        x=native();x['partition']='dev'
        with self.assertRaisesRegex(ValueError,'TRAIN'):pf.pack_batch([x]*4,16)
    def test_fake_window_end_or_role_is_rejected(self):
        for index,value in [(128,2),(50,3),(20,0),(20,5)]:
            x=native();x['tokens'][index]=value
            with self.assertRaises(ValueError):pf.pack_batch([x]*4,16)
    def test_no_optimizer_step_call_in_audit_source(self):
        tree=ast.parse(pathlib.Path(pf.__file__).read_text())
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='step']
        self.assertEqual(calls,[])
    def test_corrupt_checkpoint_part_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm')as directory:
            d=pathlib.Path(directory);buffer=io.BytesIO();torch.save({'ownTensor':torch.tensor([1.,2.])},buffer);raw=buffer.getvalue()
            (d/'part.bin').write_bytes(raw+b'corrupt')
            record=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),chunks=[dict(path='part.bin',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())])
            m=d/'manifest.json';m.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'part mismatch'):pf.load_checkpoint(m,record['sha256'])

if __name__=='__main__':unittest.main()
