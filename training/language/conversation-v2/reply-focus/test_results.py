import collections,hashlib,json,pathlib,unittest
H=pathlib.Path(__file__).resolve().parent;V=H.parent
R=lambda p:json.loads(p.read_text())
class Results(unittest.TestCase):
 def test_actual_update_ledger_including_invalid_trial(self):
  total=0
  for folder in ['invalid-execution14','execution14']:
   events=[json.loads(l)for l in(H/folder/'updates.jsonl').open()];counts=collections.Counter(x['event']for x in events);self.assertEqual(counts,{'intent':42,'completed':42});total+=counts['completed']
  s=R(H/'SUMMARY.json');self.assertEqual(s['actual_optimizer_updates_total'],total);self.assertEqual(total,84);self.assertEqual(s['valid_retained_updates_total']+s['actual_updates_discarded_total'],total)
 def test_real_replay_and_alias_repair(self):
  for arm in ['control','treatment']:
   self.assertEqual(R(H/'execution14'/(arm+'-reference.json')),R(H/'execution14'/(arm+'-replay-proof.json')));r=R(H/'execution14'/(arm+'-recovery.json'));self.assertEqual(r['process_exit'],73);self.assertTrue(r['partial_file_not_promoted']);self.assertTrue(r['resume7_to14_trace_and_full_state_exact'])
   self.assertEqual(R(H/'terminal-state-audit.json')[arm]['actual_terminal_adam_steps'],[3484])
  self.assertEqual(R(H/'invalid-trial-incident.json')['terminal_checks']['treatment']['adam_steps'],[3498])
  self.assertEqual(hashlib.sha256((H/'EXECUTED_RUNNER.py').read_bytes()).hexdigest(),R(H/'PLAN14.json')['runner_sha256'])
 def test_diagnostic_dev_not_changed(self):
  self.assertEqual(hashlib.sha256((V/'response-data/final/active-dev.json').read_bytes()).hexdigest(),R(H/'PLAN14.json')['generation']['dev_sha256'])
  self.assertEqual(hashlib.sha256((V/'epoch1/content-dev.json').read_bytes()).hexdigest(),R(H/'EVAL24_PLAN.json')['source_sha256'])
 def test_all_unmodified_outputs_and_tokens_retained(self):
  tok=R(V/'data/tokenizer.json');pieces=[bytes.fromhex(x)for x in tok['bytes']];n=0
  for name in ['initial3470','control3484','treatment3484']:
   for suffix,key,expected in [('.json','generations',23),('-native24.json','cases',24)]:
    rows=R(H/'evaluation14'/(name+suffix))[key];self.assertEqual(len(rows),expected)
    for r in rows:
     ids=r['tokensIncludingEos'];self.assertEqual(ids[-1],2);raw=b''.join(pieces[t]for t in ids[:-1]);self.assertEqual(raw.hex(),r['rawBytesHex']);self.assertEqual(raw.decode('utf8'),r['text']);n+=1
  self.assertEqual(n,141)
 def test_candidate_only_larger_schedule(self):
  s=R(H/'large-candidate-schedule.json');self.assertFalse(s['optimizer_updates_authorized']);a=R(H/'LARGE_CANDIDATE_AUDIT.json');self.assertEqual(len(s['rows']),a['candidate_steps_per_arm']);self.assertEqual(a['control']['targets'],a['treatment']['targets']);self.assertEqual(a['control']['genre_proxy'],a['treatment']['genre_proxy']);self.assertEqual(a['actual_optimizer_updates'],0)
  ws=R(V/'data/data.json')['trainWindows']
  for arm in ['control','treatment']:
   ids=[i for row in s['rows']for i in row[arm+'_window_ids']];self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(ids),len({ws[i]['document']for i in ids}))
 def test_mid_write_failure_uses_full_post_update_state(self):
  a=R(H/'SAVE_FAILURE_AUDIT.json');self.assertTrue(a['mid_serialization_ENOSPC_injected']);self.assertTrue(a['committed_checkpoint_unchanged']);self.assertEqual(a['committed_state_recovered_at_step'],14);self.assertFalse(a['real_disk_exhaustion_performed'])
 def test_archive_chunk_hashes(self):
  for arm in ['control','treatment']:
   base=H/'execution14'/arm/'archive';m=R(base/'checkpoint.json');full=hashlib.sha256();size=0
   for c in m['chunks']:
    p=base/c['path'];b=p.read_bytes();self.assertEqual(len(b),c['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),c['sha256']);self.assertLessEqual(len(b),32*1024**2);full.update(b);size+=len(b)
   self.assertEqual(full.hexdigest(),m['sha256']);self.assertEqual(size,m['bytes'])
if __name__=='__main__':unittest.main()
