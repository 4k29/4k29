import gzip,hashlib,json,pathlib,unittest
from build import HERE,Union,anon,flags
class Contracts(unittest.TestCase):
 def test_source_local_identity(self):
  self.assertNotEqual(anon('a','writer'),anon('b','writer'));self.assertEqual(anon('a','writer'),anon('a','writer'))
 def test_colloquial_not_removed(self):
  self.assertEqual(flags('うん😊')['japanese'],'script-evidence');self.assertEqual(flags('ｗｗ')['japanese'],'ambiguous-not-automatically-rejected')
 def test_ack_not_content(self):
  self.assertTrue(flags('そうですね。')['acknowledgement_proxy']);self.assertFalse(flags('そうですね。')['substantive_proxy']);self.assertTrue(flags('雨の日なので、傘を持っていきましょう。')['substantive_proxy'])
 def test_contact_review(self):
  self.assertIn('email',flags('hello@example.com')['pii_review']);self.assertIn('phone',flags('090-1234-5678')['pii_review'])
 def test_union_transitive(self):
  u=Union('abcd');u.join('a','b');u.join('c','d');u.join('b','d');self.assertEqual({u.get(x)for x in 'abcd'},{'a'})
 def test_real_data_no_invented_parent(self):
  p=HERE/'derived/conversations.jsonl.gz'
  if not p.exists():self.skipTest('MRMPC acquisition pending')
  for line in gzip.open(p,'rt'):
   d=json.loads(line)
   for row in d['utterances']:self.assertIsNone(row['parent_id']);self.assertIn(row['speaker_id'],d['speakers'])
 def test_oasst_whole_ancestry_source_roles(self):
  for line in gzip.open(HERE/'derived/oasst-conversations.jsonl.gz','rt'):
   d=json.loads(line);turns=d['utterances'];self.assertIsNone(turns[0]['parent_id']);self.assertEqual(turns[0]['source_role'],'prompter');self.assertEqual(turns[-1]['source_role'],'assistant')
   for a,b in zip(turns,turns[1:]):self.assertEqual(b['parent_id'],a['id']);self.assertNotEqual(a['source_role'],b['source_role'])
 def test_no_source_or_author_cross_split(self):
  owners={}
  for name in ['conversations.jsonl.gz','oasst-conversations.jsonl.gz']:
   p=HERE/'derived'/name
   if not p.exists():continue
   for line in gzip.open(p,'rt'):
    d=json.loads(line)
    for key in [d['conversation_family']]+d['speakers']:
     self.assertEqual(owners.setdefault(key,d['split']),d['split'])
 def test_withheld_tree_not_public(self):
  audit=json.loads((HERE/'raw/privacy-oasst2.json').read_text());bad={x['source_tree_id']for x in audit['withheld']}
  for line in gzip.open(HERE/'raw/oasst2-ja-original.jsonl.gz','rt'):
   d=json.loads(line)['source_record'];self.assertNotIn(d['message_tree_id'],bad);self.assertFalse(d['deleted'])
 def test_no_optimizer_or_admission(self):
  for name in ['metrics.json','oasst-metrics.json']:
   p=HERE/'derived'/name
   if not p.exists():continue
   d=json.loads(p.read_text());self.assertEqual(d['training_admitted_dialogues'],0);self.assertEqual(d['actual_optimizer_updates'],0);self.assertFalse(d['sealed_test_created_or_read'])
if __name__=='__main__':unittest.main()
