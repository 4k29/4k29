"""Standard-library evidence checks, no inference and no optimizer."""
import collections,gzip,hashlib,json,pathlib,unittest
N=pathlib.Path(__file__).resolve().parent;V=N.parent;H=V/'foundation-stage';ROOT=N.parents[3]
read=lambda p:json.loads(p.read_text())
class Evidence(unittest.TestCase):
 def test_call_counts_and_completed_budget(self):
  for arm in ['control','boundary','clip5']:
   folder=N/'run'/arm;r=read(folder/'receipt.json');events=list(map(json.loads,(folder/'updates.jsonl').read_text().splitlines()));intent=collections.Counter((e['phase'],e['step'])for e in events if e['event']=='intent');done=collections.Counter((e['phase'],e['step'])for e in events if e['event']=='completed');self.assertEqual(intent,done);self.assertEqual(sum(done.values()),r['actual_optimizer_updates']);self.assertEqual([e['step']for e in events if e['event']=='completed'and e['phase']=='retained'],list(range(1,513)));self.assertEqual(r['retained_targets'],379767);self.assertEqual(r['retained_updates'],512);self.assertEqual(sum(e['phase']!='retained'for e in events if e['event']=='completed'),r['replay_updates']);self.assertTrue(read(folder/'RESUME_AUDIT.json')['real_updates_3_to4_exact_after_process_restart'])
 def test_actual_recovery_traces(self):
  events=list(map(json.loads,(N/'run/boundary/updates.jsonl').read_text().splitlines()));ret={e['step']:e['trace']for e in events if e['event']=='completed'and e['phase']=='retained'};rec=[e for e in events if e['event']=='completed'and e['phase']=='recovery-replay'];self.assertEqual([e['step']for e in rec],list(range(129,209)))
  for e in rec:self.assertEqual(e['trace'],ret[e['step']])
  self.assertEqual(read(N/'run/boundary/receipt.json')['actual_optimizer_updates'],594)
 def test_frozen_source_hashes_and_conditional_clip(self):
  p=read(N/'PLAN.json')
  for path,d in p['input_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),d,path)
  gate=read(N/'CLIP5_GO.json');self.assertTrue(gate['go']);self.assertFalse(gate['learning_comparison_primary_success']);self.assertEqual(gate['boundary_run_receipt_sha256'],hashlib.sha256((N/'run/boundary/receipt.json').read_bytes()).hexdigest())
 def test_complete_original_paragraphs_and_byte_identity(self):
  paragraphs=read(N/'paragraphs.json');wanted={r['provenance']['id']:{}for r in paragraphs['train']+paragraphs['dev']}
  for r in paragraphs['train']+paragraphs['dev']:wanted[r['provenance']['id']][r['paragraph_ordinal']]=r
  pieces=[bytes.fromhex(b)for b in read(V/'data/tokenizer.json')['bytes']];found=0
  for doc in map(json.loads,gzip.open(V/'foundation-data/corpus/documents.jsonl.gz','rt')):
   if doc['id']not in wanted:continue
   for p in doc['paragraphs']:
    if p['ordinal']in wanted[doc['id']]:
     r=wanted[doc['id']][p['ordinal']];self.assertEqual(r['text'],p['normalizedText']);self.assertTrue(p['keepForCandidateTraining']);self.assertEqual(b''.join(pieces[t]for t in r['body_tokens']).decode(),r['text']);self.assertEqual(r['tokens'],[1]+r['body_tokens']+[2]);found+=1
  self.assertEqual(found,1027)
 def test_exact_validated_prefixes_and_raw_generated_bytes(self):
  expected=read(H/'TOKEN_BOUNDARY_PROTOCOL.json')['cases'];pieces=[bytes.fromhex(b)for b in read(V/'data/tokenizer.json')['bytes']]
  for name in ['control','boundary','clip5']:
   rows=read(N/'evaluation'/(name+'.json'))['prose_dev'];self.assertEqual([r['prefix']for r in rows],[r['prefix']for r in expected]);self.assertTrue(all(len(r['prefix'])+128<=256 for r in rows))
  def walk(x):
   if isinstance(x,dict):
    if 'nonEosTokens'in x and 'rawBytesHex'in x:
     b=b''.join(pieces[t]for t in x['nonEosTokens']);self.assertEqual(b.hex(),x['rawBytesHex'])
     if x['strictUtf8']:self.assertEqual(b.decode(),x['text'])
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  for p in(N/'evaluation').glob('*.json'):walk(read(p))
 def test_parity_limits_are_honest(self):
  for r in read(N/'parity-summary.json').values():self.assertEqual(r['optimizer_updates'],0);self.assertFalse(r['complete_reply_parity_established']);self.assertEqual(r['same_history_argmax_disagreements'],0);self.assertLessEqual(r['max_absolute_logit_error'],r['tolerance'])
if __name__=='__main__':unittest.main()
