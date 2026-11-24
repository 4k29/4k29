import unittest,pathlib,json,gzip,hashlib,collections
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l)for l in gzip.open(p,'rt')]
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.p=read(D/'PLAN.json');c.c=rows(D/'corpus.jsonl.gz');c.by={r['id']:r for r in c.c};c.b=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];c.pieces=[bytes.fromhex(s)for s in read(D.parent/'data/tokenizer.json')['bytes']]
 def test_all_source_utf8(self):
  for r in self.c:
   expected=''.join(u['text']for u in r['utterances'])if r['kind']=='human_dialogue'else r['text'];self.assertEqual(b''.join(self.pieces[t]for t in r['body_tokens']),expected.encode())
 def test_no_duplicate_target_or_invented_boundary(self):
  positions=set();count=0
  for b in self.b:
   self.assertLessEqual(len(b),4)
   for w in b:
    r=self.by[w['unit_id']];self.assertEqual(w['tokens'],r['tokens'][w['start']:w['start']+257]);self.assertNotIn(1,w['tokens'][1:]);self.assertNotIn(0,w['tokens']);self.assertNotIn(5,w['tokens'])
    for p in range(w['start']+1,w['start']+len(w['tokens'])):
     k=(r['id'],p);self.assertNotIn(k,positions);positions.add(k);count+=1
  self.assertEqual(count,self.p['full_pass_targets']);self.assertEqual(len(self.b),self.p['full_pass_updates'])
 def test_no_jaquad_false_eos(self):
  for r in self.c:
   if r['source']=='jaquad':self.assertNotIn(2,r['tokens']);self.assertNotIn(1,r['tokens'])
 def test_splits_and_source_holds(self):
  tr={r['component']for r in self.c if r['split']=='train'};dv={r['component']for r in self.c if r['split']=='dev'};self.assertFalse(tr&dv);self.assertFalse(tr&set(read(D/'QUALITY_REVIEW.json')['held_components']));self.assertFalse(any(r['source']=='jmrd'for r in self.c));self.assertEqual(len(read(D/'NEW_DEV_SOURCES.json')),12)
 def test_turn_contract(self):
  for r in self.c:
   if r['kind']!='human_dialogue':continue
   at=1;self.assertEqual(r['tokens'][0],1)
   for u in r['utterances']:
    self.assertEqual(r['tokens'][at],u['localRoleToken']);end=r['tokens'].index(2,at);self.assertEqual(b''.join(self.pieces[t]for t in r['tokens'][at+1:end]),u['text'].encode());at=end+1
   self.assertEqual(at,len(r['tokens']))
 def test_predeclared_budget_and_health_information(self):
  hs=read(D/'HEALTH_SOURCES.json');self.assertEqual(len({tuple(r['prefix'])for r in hs}),3)
  for r in hs:self.assertEqual(r['tokens'],r['prefix']+r['reference'])
  self.assertEqual(sum(len(w['tokens'])-1 for b in self.b[:self.p['comparison_updates']]for w in b),self.p['comparison_targets']);self.assertEqual(self.p['maximum_main_epochs'],1)
 def test_frozen_shas(self):
  for f,h in self.p['input_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),h,f)
 def test_no_sealed_or_public_adoption(self):self.assertFalse(self.p['limits']['sealed_TEST']);self.assertFalse(self.p['limits']['public_replacement']);self.assertFalse(self.p['limits']['subagents'])
if __name__=='__main__':unittest.main()
