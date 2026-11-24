"""Targeted data/schedule guards, no model dependencies or external access."""
import unittest,json,hashlib,pathlib,collections,gzip
import prepare
P=prepare.P;V=prepare.V
class Study(unittest.TestCase):
 def test_legacy_fixture_unchanged(self):
  self.assertEqual(prepare.sha(V/'novel-continuous-study/REVIEWED_PROSE.jsonl.gz'),'e1cd3b0000c0d8abb8ca8687f6c929b3c95416040b2199cb5ffe3596acaf79c4')
  self.assertEqual(prepare.sha(V/'novel-continuous-study/NEW_PROSE_DEV.json'),'9b499701bcb5b497b9a9f66856abc1862a045dd6ec58287ab58dca9ce2468951')
 def test_individual_selection(self):
  d=prepare.read(P/'READING.json');rr=d['cases'];self.assertEqual(len(rr),191);self.assertEqual(len({r['id']for r in rr}),191)
  admitted={r['id']:r for r in rr if r['decision']=='admit_language_candidate'};rows=prepare.rows(P/'ADDITIONAL_PROSE.jsonl.gz');self.assertEqual(len(rows),55)
  for r in rows:self.assertEqual(r['text_SHA'],admitted[r['id']]['text_SHA']);self.assertTrue(r['admission']['individual_original_text_read'])
  self.assertFalse(d['independent_human_review'])
 def test_no_original_paragraph_repetition(self):
  seen=set()
  for r in prepare.combined():
   for h in r['original_paragraph_hashes']:self.assertNotIn(h,seen);seen.add(h)
 def test_context_and_teacher_budget(self):
  s=prepare.read(P/'SCHEDULE.json');self.assertEqual(s['teachers'],13027)
  a=prepare.read(P/'TEACHER_AUDIT.json')
  for arm in ['B','C']:
   self.assertEqual(a[arm]['targets'],13027);self.assertEqual(a[arm]['batches'],13);self.assertEqual(a[arm]['per_batch_targets'],[1024]*12+[739]);self.assertEqual(a[arm]['duplicate_teacher_positions'],0);self.assertLessEqual(a[arm]['input_length']['max'],256)
  self.assertEqual(a['C']['types'].get('EOS',0),0)
 def test_byte_exact_and_no_false_ending(self):
  import sys
  sys.path.insert(0,str(V));from new_tokenizer import Encoder
  t=prepare.read(V/'data/tokenizer.json');enc=Encoder(t);pieces=[bytes.fromhex(x)for x in t['bytes']]
  for r in prepare.combined():
   self.assertEqual([1]+enc(r['text']),r['tokens']);self.assertEqual(b''.join(pieces[k]for k in r['tokens']if k>=6),r['text'].encode());self.assertFalse(r['EOS']);self.assertNotIn(2,r['tokens'])
 def test_dev_and_known_old_family_held(self):
  d={r['family']for r in prepare.read(V/'novel-continuous-study/NEW_PROSE_DEV.json')['cases']};self.assertFalse(d&{r['family']for r in prepare.combined()})
  for r in prepare.read(P/'READING.json')['cases']:
   if r['batch']=='extra-private.json' and 17<=r['index']<=32:self.assertEqual(r['decision'],'hold')
 def test_no_model_execution_claim(self):
  a=prepare.read(P/'OPTIMIZER_LEDGER.json');self.assertTrue(all(a[k]==0 for k in ['actual_optimizer_calls','model_forwards','retained_updates','discarded_updates','replay_updates','failed_model_updates']));self.assertFalse(prepare.read(P/'PLAN.json')['training_GO']);self.assertEqual(prepare.read(P/'CHECKPOINT_INDEX.json')['new_checkpoints'],[])
 def test_plan_sha(self):
  p=prepare.read(P/'PLAN.json');self.assertEqual(prepare.sha(P/'PLAN.json'),(P/'PLAN.sha256').read_text().strip())
  for f,h in p['sha256'].items():self.assertEqual(prepare.sha(V.parents[2]/f),h)
 def test_reference_masks_survive_batch_split(self):
  # Synthetic IDs/tokens only, never teacher corpus; same position may appear in history
  # but must not acquire a second loss when a 1024-target boundary splits a window.
  r=[dict(id='fixture',tokens=[1]+[7]*1400)];refs=list(prepare.windows(r));bs=prepare.pack(refs);a=prepare.audit_schedule(r,bs)
  self.assertEqual(a['targets'],1400);self.assertEqual(a['per_batch_targets'],[1024,376]);self.assertEqual(a['duplicate_teacher_positions'],0)
if __name__=='__main__':unittest.main()
