import array,json,pathlib,unittest
H=pathlib.Path(__file__).resolve().parent;V=H.parent
class Allocation(unittest.TestCase):
 def test_preserved_old_dev(self):
  import hashlib
  import subprocess
  p=V/'response-data/final/active-dev.json';relative=str(p.relative_to(V.parents[2]));old=subprocess.check_output(['git','show','HEAD:'+relative]);self.assertEqual(p.read_bytes(),old)
 def test_target_and_position_integrity(self):
  m=json.loads((V/'data/data.json').read_text());ws=m['trainWindows'];s=json.loads((H/'schedule.json').read_text())['rows'];seen={'control':set(),'treatment':set()}
  for row in s:
   a=row['control_window_ids'];b=row['treatment_window_ids'];self.assertEqual(a[:2],b[:2]);self.assertEqual([ws[k]['length']for k in a],[ws[k]['length']for k in b])
   for arm,ids in [('control',a),('treatment',b)]:
    self.assertEqual(len(ids),len(set(ids)));self.assertFalse(seen[arm].intersection(ids));seen[arm].update(ids)
 def test_no_non_train_focus(self):
  docs={d['id']:d for d in map(json.loads,(V/'data/train.docs.jsonl').open())};cases=json.loads((H/'rp-reading.json').read_text())['cases'];self.assertEqual(len(cases),20)
  for c in cases:self.assertIn(c['id'],docs);self.assertTrue(c['whole_dialogue_read'])
 def test_zero_update_real_audit(self):
  r=json.loads((H/'NUMERICAL_AUDIT.json').read_text());self.assertEqual(r['actual_optimizer_updates'],0);self.assertEqual(r['optimizer_step_attempts'],0);self.assertEqual(r['initial_trajectory_digest'],r['final_trajectory_digest']);self.assertTrue(r['recovered_after_partial_write_exact'])
class TrainingGate(unittest.TestCase):
 def test_current_plan_blocks_all_updates(self):
  import hashlib,subprocess,sys,tempfile
  plan=H/'EXPERIMENT.json';sha=hashlib.sha256(plan.read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as td:
   r=subprocess.run([sys.executable,str(H/'run_comparison.py'),'--plan-sha256',sha,'--output',str(pathlib.Path(td)/'output')],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertIn('optimizer updates prohibited',r.stderr);self.assertFalse((pathlib.Path(td)/'output').exists())
if __name__=='__main__':unittest.main()

