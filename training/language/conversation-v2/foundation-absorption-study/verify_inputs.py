import pathlib,json,gzip,hashlib,unittest,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2];sys.path.insert(0,str(V));from new_tokenizer import Encoder
class Inputs(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.r=[json.loads(x)for x in gzip.decompress((P/'corpus.jsonl.gz').read_bytes()).splitlines()];c.s=json.loads((P/'SCHEDULE.json').read_text());c.f=json.loads((V/'faq-ce-verified-study/DATA.json').read_text());c.e=Encoder(json.loads((V/'data/tokenizer.json').read_text()));c.p=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
 def test_body_reconstruction_and_boundaries(self):
  for r in self.r:
   raw=b''.join(self.p[t]for t in r['tokens']if t>=6)
   if r['source']=='realpersona':self.assertEqual(raw,('\n'.join([])).encode()if False else ''.join(u['text']for u in r['utterances']).replace('\n\n','\n').encode())
   else:self.assertEqual(raw,r['text'].encode())
   self.assertFalse(any(a==b==16 for a,b in zip(r['tokens'],r['tokens'][1:])));self.assertEqual(r['tokens'][-1]==2,bool(r['EOS']))
   if r['source']=='jaquad':self.assertNotIn(2,r['tokens'])
 def test_active_target_coverage_and_shift(self):
  seen=set()
  for b in self.s['batches']:
   for z in b:
    t=self.r[z['record']]['tokens'];a=z['input_start'];end=z['end'];self.assertLessEqual(end-a-1,256);x=t[a:end-1];y=t[a+1:end];self.assertEqual(x[1:],y[:-1]);mask=[i>=z['target_start']for i in range(a+1,end)];self.assertEqual(sum(mask),z['targets'])
    for k in range(z['target_start'],end):self.assertNotIn((z['record'],k),seen);seen.add((z['record'],k))
  self.assertEqual(len(seen),991448);self.assertEqual(len(self.s['batches']),1064);self.assertEqual(len(seen),sum(len(r['tokens'])-1 for r in self.r))
 def test_FAQ_unchanged_and_loss(self):
  self.assertEqual(len(self.f['parts']['train']),372);self.assertEqual(len(self.f['batch_order']),93);self.assertEqual(sum(self.f['batch_order'],[]),list(range(372)));self.assertEqual(sum(r['body_tokens']for r in self.f['parts']['train']),34766)
  for r in self.f['parts']['train']:
   a=r['response_body_start'];self.assertEqual(r['tokens'][a:-1],self.e(r['response']));self.assertEqual(r['tokens'][-1],2);self.assertEqual(len(r['tokens'][a:]),r['body_tokens']+1);self.assertLessEqual(len(r['tokens']),256)
 def test_new_DEV_exact_prefix(self):
  d=json.loads((P/'PROSE_DEV.json').read_text())['cases'];self.assertEqual(len(d),12)
  for r in d:self.assertEqual(r['prefix'],r['tokens'][:len(r['prefix'])]);self.assertLessEqual(len(r['prefix'])+r['maxNewTokens'],256);self.assertEqual(r['teacher_continuation'],r['tokens'][len(r['prefix']):len(r['prefix'])+len(r['teacher_continuation'])]);self.assertFalse(any(r['family']==x['family']for x in self.r))
 def test_audit(self):
  a=json.loads((P/'POSITION_AUDIT.json').read_text());self.assertTrue(a['passed']);self.assertEqual(a['FAQ_and_PROSE_DEV_near_cross'],[]);self.assertEqual(a['internal_near_pairs'],[]);self.assertEqual(a['repeated_active_teacher_positions'],0)
 def test_frozen_SHA(self):
  p=json.loads((P/'PLAN.json').read_text())
  for n,h in p['sha256'].items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
if __name__=='__main__':unittest.main()
