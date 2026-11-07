"""Real optimizer-call accounting, recovery and complete-state evidence; no Torch required in CI."""
import unittest,pathlib,json,hashlib
P=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def events(p):return list(map(json.loads,p.read_text().splitlines()))
class FinalEvidence(unittest.TestCase):
 def test_real_resume_and_uncontaminated_recovery(self):
  proof=read(P/'CLEAN_RECOVERY_PROOF.json');self.assertEqual(proof['recomputed_updates'],247);self.assertTrue(proof['all_loss_gradient_lr_teacher_trace_exact']);self.assertTrue(proof['original759_tensor_state_direct_hash_not_available']);a=read(P/'run/A/CLEAN_RESUME_AUDIT.json');self.assertEqual(a['actual_reference_resume_steps'],[515,516]);self.assertTrue(a['model_Adam_RNG_cursor_trace_exact_after_actual_restart'])
  old={r['step']:r['trace']for r in events(P/'run/A/updates-v2.jsonl')if r['event']=='completed'and r['phase']=='retained'};replay=[r for r in events(P/'run/A/updates-clean.jsonl')if r['event']=='completed'and r['phase']=='recovery-replay'];self.assertEqual(len(replay),247)
  for r in replay:self.assertEqual(r['trace'],old[r['step']])
 def test_complete_actual_call_ledger_and_receipt(self):
  if not(P/'run/A/receipt.json').exists():self.skipTest('Finite one-pass still running; final accounting not yet complete')
  paths=[P/'run/A/updates-v2.jsonl',P/'run/A/updates-clean.jsonl',P/'run/B/updates.jsonl',P/'run/C/updates.jsonl',P/'excluded-pilot/run/A/updates.jsonl',P/'overfit/updates.jsonl'];total=0
  for p in paths:
   es=events(p);intents=[r for r in es if r['event']=='intent'];done=[r for r in es if r['event']=='completed'];self.assertEqual(len(intents),len(done));total+=len(done)
  receipt=read(P/'run/A/receipt.json');self.assertEqual(receipt['retained_updates'],2966);self.assertEqual(receipt['retained_targets'],2039162);self.assertEqual(receipt['recovery_replay_calls'],247);self.assertEqual(receipt['excluded_v2_tail_updates'],28);self.assertEqual(total,receipt['actual_optimizer_calls']+514+514+326+64)
 def test_matched_comparison_sources_and_fixed_rule(self):
  selection=read(P/'SELECTION.json');self.assertEqual(selection['chosen_arm'],'A');self.assertFalse(selection['natural_language_superiority_demonstrated']);self.assertTrue(read(P/'STATE_AUDIT.json')['pass_all'])
  for a in ['A','B','C']:
   d=read(P/'run'/a/'receipt-0512.json');self.assertEqual(d['retained_targets'],351219);self.assertEqual(d['retained_updates'],512);self.assertEqual(d['actual_optimizer_calls'],514)
 def test_actual_BOS_full_original_paragraph_memorization_is_not_generalization(self):
  r=read(P/'overfit/receipt.json');self.assertEqual(r['actual_optimizer_calls'],64);self.assertEqual(r['unique_body_tokens'],79);self.assertEqual(r['targets'],5120);self.assertFalse(r['unknown_generalization_proven']);g=read(P/'overfit/evaluations.json')[-1]['cases'][0];self.assertEqual(g['prefix'],[1]);self.assertEqual(g['tokensIncludingEos'],g['reference']);self.assertTrue(g['eos'])
if __name__=='__main__':unittest.main()
