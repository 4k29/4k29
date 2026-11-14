"""Lightweight evidence integrity checks. Never imports model/Torch or updates weights."""
import json,pathlib,hashlib,unittest,collections
P=pathlib.Path(__file__).resolve().parent
load=lambda f:json.loads((P/f).read_text())
class Evidence(unittest.TestCase):
 def test_actual_ledgers(self):
  for name,total in [('UPDATES.jsonl',1259),('OPTIMIZER_CALLS.jsonl',1259),('FORWARDS.jsonl',47033)]:
   rows=[json.loads(s)for s in(P/name).read_text().splitlines()];c=collections.Counter(r['event']for r in rows);self.assertEqual(c,{'intent':total,'returned':total})
  self.assertEqual(load('RESULT.json')['by_phase'],{'discarded-original':6,'resume-replay':3,'retained':1250})
 def test_optimizer_and_rng(self):
  a=load('PREFLIGHT-SFT-A.json');b=load('PREFLIGHT-SFT-B.json');self.assertEqual(a['initial'],b['initial']);self.assertEqual(a['initial']['initial_Adam_steps'],[])
  for x in [a,b,load('PREFLIGHT-LM.json')]:self.assertTrue(x['passed']and x['update_resume_exact']and x['Adam_storage_nonshared'])
  self.assertTrue(load('SUMMARY.json')['training']['SFT_all_93_input_mask_RNG_before_equal'])
 def test_complete_cold_states(self):
  for tag,steps in [('LM',[4,532,1064]),('SFT-A',[47,93]),('SFT-B',[47,93])]:
   for step in steps:
    c=load(f'COLD-{tag}-{step}.json');m=load(f'artifacts/{tag}-{step}/checkpoint.json');self.assertTrue(c['passed']and c['all_state_equal']and c['remote_only_no_alternates']);self.assertEqual(c['sha256'],m['sha256']);self.assertEqual(c['optimizer_calls'],0);self.assertEqual(m['plan_sha256'],(P/'PLAN.sha256').read_text().strip());self.assertEqual(m['cursor'],step)
 def test_raw_outputs_and_readings(self):
  for state in ['A-base','B-base','SFT-A-93','SFT-B-93']:
   f=f'evaluation/{state}.json';d=load(f);r=load(f'evaluation/{state}-READING.json');self.assertEqual(r['evidence_sha256'],hashlib.sha256((P/f).read_bytes()).hexdigest());self.assertEqual(len(d['cases']),183);self.assertEqual(len(r['cases']),183);self.assertEqual(len(d['self_history']),4);self.assertFalse(d['independent_human_evaluation']);self.assertTrue(d['whole_vocabulary_greedy']and d['raw_unmodified'])
   for x,y in zip(d['cases'],r['cases']):
    self.assertEqual(x['id'],y['id']);self.assertEqual(y['raw_case_sha256'],hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest())
    if x['text']is not None:self.assertEqual(x['text'].encode(),bytes.fromhex(x['rawBytesHex']))
 def test_targets_and_caption(self):
  s=load('SUMMARY.json');self.assertEqual([s[k]['panels']['new-caption32']['strict_success']for k in ['A-base','B-base','SFT-A-93','SFT-B-93']],[21,21,19,17]);self.assertEqual(s['training']['by_tag']['LM']['active_teachers'],991448)
  for k in ['A-base','B-base','SFT-A-93','SFT-B-93']:
   self.assertEqual(s[k]['panels']['FAQ-dev']['strict_success'],0);self.assertEqual(s[k]['panels']['source-heldout-prose12']['strict_success'],0)
  for k in ['SFT-A','SFT-B']:self.assertEqual(s['training']['by_tag'][k]['active_teachers'],35138)
if __name__=='__main__':unittest.main()
