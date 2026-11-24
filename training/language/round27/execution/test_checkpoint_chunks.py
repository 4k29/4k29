import unittest,tempfile,pathlib,json
from checkpoint_chunks import pack,restore,digest
class Tests(unittest.TestCase):
 def test_roundtrip_multiple_parts_and_existing_guard(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'checkpoint.pt';raw=bytes(range(256))*1000;p.write_bytes(raw);manifest=pack(p,40000);r=json.loads(manifest.read_text());self.assertEqual(len(r['chunks']),7);self.assertTrue(all(x['bytes']<=40000 for x in r['chunks']))
   expected=digest(p);p.unlink();self.assertEqual(restore(manifest).read_bytes(),raw);self.assertEqual(digest(p),expected);self.assertEqual(restore(manifest),p)
   p.write_bytes(b'different')
   with self.assertRaises(ValueError):restore(manifest)
   self.assertEqual(p.read_bytes(),b'different')
 def test_corruption_fails_before_output(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'checkpoint.pt';p.write_bytes(b'original checkpoint bytes'*100);m=pack(p,1000);r=json.loads(m.read_text());part=pathlib.Path(d)/r['chunks'][0]['path'];part.write_bytes(b'corrupt');p.unlink()
   with self.assertRaises(ValueError):restore(m)
   self.assertFalse(p.exists());self.assertFalse(p.with_name(p.name+'.restore.tmp').exists())
if __name__=='__main__':unittest.main()
