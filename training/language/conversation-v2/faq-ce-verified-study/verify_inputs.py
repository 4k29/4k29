import pathlib,json,sys,hashlib,unittest,os,re
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('V2_ROOT',str(P.parent)));sys.path.insert(0,str(V));from new_tokenizer import Encoder
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.d=json.loads((P/'DATA.json').read_text());c.t=json.loads((V/'data/tokenizer.json').read_text());c.enc=Encoder(c.t);c.p=[bytes.fromhex(s)for s in c.t['bytes']]
 def test_serialization(self):
  for r in self.d['parts']['train']+self.d['parts']['dev']:
   q,a=self.enc(r['question']),self.enc(r['response']);self.assertEqual([1,3]+q+[2,4]+a+[2],r['tokens']);self.assertEqual(b''.join(self.p[t]for t in a),r['response'].encode());self.assertEqual(r['response_body_start'],len(q)+4);self.assertLessEqual(len(r['tokens']),257);self.assertNotIn(0,r['tokens'])
 def test_teacher_shift(self):
  for r in self.d['parts']['train']:
   y=r['tokens'][1:];s=r['response_body_start']-1;self.assertEqual(y[s:-1],self.enc(r['response']));self.assertEqual(y[-1],2);self.assertEqual(len(y[s:]),r['body_tokens']+1)
 def test_no_repeat_or_leak(self):
  self.assertEqual(sum(self.d['batch_order'],[]),list(range(372)));self.assertEqual(self.d['updates_per_arm'],93);self.assertFalse({r['split_family']for r in self.d['parts']['train']}&{r['split_family']for r in self.d['parts']['dev']});self.assertEqual(len({r['id']for r in self.d['parts']['train']}),372)
 def test_counts(self):
  r=self.d['parts']['train'];self.assertEqual(sum(x['body_tokens']for x in r),34766);self.assertEqual(sum(len(x['tokens'])-1 for x in r),49856);self.assertEqual(len(self.d['parts']['dev']),19);self.assertFalse(any(x['source']=='農林水産省'for x in r))
 def test_plan(self):
  plan=json.loads((P/'PLAN.json').read_text());root=V.parents[2]
  for n,h in plan['sha256'].items():
   path=P/pathlib.Path(n).name if '/faq-ce-verified-study/'in n else P.parent/'faq-ce-clean-study'/n.split('/faq-ce-clean-study/')[1] if '/faq-ce-clean-study/'in n else root/n
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),h,n)
 def test_complete_source_answer(self):
  a=json.loads((P/'ANSWER_BOUNDARY_STRICT_AUDIT.json').read_text());ok=set(a['pass_ids']);self.assertTrue(all(r['id']in ok for r in self.d['parts']['train']));self.assertNotIn('jagov:12541',ok);self.assertFalse(any(r['index']==12461 for r in self.d['parts']['train']))
 def test_risk_gate_regression(self):
  pat='(?<!愛)がん|癌|被ばく|被曝|放射線|線量|甲状腺|健康影響';self.assertIsNone(re.search(pat,'愛がん目的のペット'));self.assertIsNotNone(re.search(pat,'甲状腺がんのリスク'))
if __name__=='__main__':unittest.main()
