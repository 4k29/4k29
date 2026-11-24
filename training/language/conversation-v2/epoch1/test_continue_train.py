import importlib.util,json,pathlib,tempfile,unittest
import torch
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('epoch1_train',HERE/'continue_train.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ContinuationTests(unittest.TestCase):
    def test_chunk_atomic_replacement_and_tensor_roundtrip(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm')as d:
            p=pathlib.Path(d)/'checkpoint.pt.chunks.json'
            first={'state':torch.arange(20),'order':[5,3,1],'rng':(1,2,3)}
            m.save_chunks(first,p);old=m.read(p);self.assertTrue(m.exact(first,m.load_chunks(p)))
            second={'state':torch.ones(100),'order':[1,3,5],'rng':(4,5,6)}
            m.save_chunks(second,p);self.assertTrue(m.exact(second,m.load_chunks(p)))
            self.assertFalse((p.parent/old['chunks'][0]['path']).exists())
    def test_chunk_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory(dir='/dev/shm')as d:
            p=pathlib.Path(d)/'checkpoint.pt.chunks.json';m.save_chunks({'value':3},p)
            part=p.parent/m.read(p)['chunks'][0]['path'];part.write_bytes(b'corrupted')
            with self.assertRaises(ValueError):m.load_chunks(p)
    def test_first_epoch_dose_final_batch_two(self):
        order=list(range(13878));cursor=2048;seen=[];batches=[]
        while cursor<len(order):
            selected=order[cursor:min(cursor+4,len(order))];batches.append(len(selected));seen.extend(selected);cursor+=len(selected)
        self.assertEqual(len(batches),2958);self.assertEqual(batches[-1],2)
        self.assertEqual(seen,order[2048:]);self.assertEqual(len(set(seen)),11830)
if __name__=='__main__':unittest.main()
