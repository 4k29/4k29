"""Independent source/partition/target-position invariants, stdlib only."""
import unittest,collections,hashlib,gzip,json,pathlib
P=pathlib.Path(__file__).resolve().parent;V=P.parent;ROOT=V.parents[2]
def load(p):return json.loads(p.read_text())
def gz(p):return list(map(json.loads,gzip.open(p,'rt')))
class CorpusTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.plan=load(P/'PLAN.json');cls.rows=gz(P/'corpus.jsonl.gz');cls.windows=json.load(gzip.open(P/'schedule.json.gz','rt'))['batches'];cls.sources={r['id']:r for r in gz(V/'foundation-data/corpus/documents.jsonl.gz')}
 def test_source_bytes_and_attribution(self):
  for r in self.rows:
   d=self.sources[r['provenance']['id']];p=d['paragraphs'][r['paragraph_ordinal']];self.assertEqual(r['text'],p['normalizedText']);self.assertTrue(p['keepForCandidateTraining']);self.assertEqual(r['component'],d['component']);self.assertEqual(r['provenance']['license'],d['license']);self.assertTrue(d['url'].startswith('https://'))
 def test_roundtrip_all_and_no_special_body(self):
  pieces=[bytes.fromhex(t)for t in load(V/'data/tokenizer.json')['bytes']]
  for r in self.rows:
   self.assertTrue(all(i>=6 for i in r['body_tokens']));self.assertEqual(b''.join(pieces[t]for t in r['body_tokens']),r['text'].encode())
 def test_no_dev_source_or_family_train_leak(self):
  train=[r for r in self.rows if r['split']=='train'];protected={d['component']for d in self.sources.values()if d['split']=='dev'};self.assertFalse({r['component']for r in train}&protected)
  eval_ids={r['source_id']for r in load(P/'DEV_PROTOCOL.json')['cases']};self.assertFalse(eval_ids&{r['id']for r in train});self.assertEqual(len(eval_ids),9)
 def test_no_repeated_target_or_fabricated_cut(self):
  by={r['id']:r for r in self.rows};seen=set();counts=collections.Counter()
  for batch in self.windows:
   for w in batch:
    seq=by[w['unit_id']]['tokens'];self.assertEqual(w['tokens'],seq[w['start']:w['start']+257]);self.assertLessEqual(len(w['tokens']),257)
    for j,t in enumerate(w['tokens'][1:],w['start']+1):
     key=(w['unit_id'],j);self.assertNotIn(key,seen);seen.add(key);counts[t]+=1
  self.assertEqual(len(seen),self.plan['full_pass_targets']);self.assertEqual(counts[1],0);self.assertEqual(counts[0],0);self.assertEqual(counts[2],577);self.assertEqual(sum(counts[i]for i in [3,4,5]),0)
 def test_jaquad_excerpts_no_eos_or_bos(self):
  for r in self.rows:
   if r['source']=='jaquad':self.assertEqual(r['tokens'],r['body_tokens']);self.assertFalse(r['BOS']);self.assertFalse(r['EOS'])
 def test_input_sha_frozen(self):
  for name,want in self.plan['input_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),want,name)
 def test_novelty_not_new_acquisition(self):
  tr=[r for r in self.rows if r['split']=='train'];self.assertEqual(sum(len(r['body_tokens'])for r in tr),2046277);self.assertEqual(sum(len(r['body_tokens'])for r in tr if r['new_vs_PR101']),1308024);self.assertEqual(load(P/'CORPUS_AUDIT.json')['newly_acquired_tokens'],0)
if __name__=='__main__':unittest.main()
