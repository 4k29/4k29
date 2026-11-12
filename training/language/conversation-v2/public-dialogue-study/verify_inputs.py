"""Validate frozen licensed input and shifted CE masks without model construction."""
import pathlib,json,hashlib,sys,unittest,os
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get("V2_ROOT",str(P.parent)));sys.path.insert(0,str(V));from new_tokenizer import Encoder
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads((P/'DATA.json').read_text());cls.t=json.loads((V/'data/tokenizer.json').read_text());cls.enc=Encoder(cls.t);cls.pieces=[bytes.fromhex(s)for s in cls.t['bytes']]
 def test_bijection_and_shift(self):
  for r in self.d['parts']['train']+self.d['parts']['dev']:
   t=[1]
   for u in r['history']+[dict(role='agent',text=r['response'])]:
    ids=self.enc(u['text']);self.assertEqual(b''.join(self.pieces[i]for i in ids),u['text'].encode());t+=[4 if u['role']=='agent'else 3]+ids+[2]
   self.assertEqual(t,r['tokens']);self.assertLessEqual(len(t),257);s=r['response_body_start'];self.assertEqual(t[s-1],4);self.assertEqual(t[-1],2);self.assertEqual(len(t)-s,r['body_tokens']+1);self.assertTrue(all(x>5 for x in t[s:-1]));self.assertNotIn(0,t)
 def test_order_and_counts(self):
  indices=sum(self.d['batch_order'],[]);self.assertEqual(sorted(indices),list(range(66)));self.assertEqual(len(indices),len(set(indices)));self.assertEqual(self.d['updates_per_arm'],17)
  self.assertEqual(sum(len(r['tokens'])-1 for r in self.d['parts']['train']),4880);self.assertEqual(sum(r['body_tokens']+1 for r in self.d['parts']['train']),2124)
 def test_split_and_role(self):
  a,b=self.d['parts']['train'],self.d['parts']['dev'];self.assertFalse({r['family']for r in a}&{r['family']for r in b});self.assertEqual(len({r['document']for r in a}),66)
  self.assertTrue(all(r['source_roles_preserved']and r['license']=='CC-BY-4.0'and not r['retrieval_proxy_only']for r in a+b));self.assertTrue(all(r['response_body_start']+64<=256 for r in b))
 def test_plan_sha(self):
  q=json.loads((P/'PLAN.json').read_text());root=V.parents[2]
  for n,h in q['sha256'].items():
   path=P/pathlib.Path(n).name if '/public-dialogue-study/' in n else root/n
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),h,n)
if __name__=='__main__':unittest.main()
