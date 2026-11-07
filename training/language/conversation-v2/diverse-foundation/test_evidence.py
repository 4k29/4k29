"""Independent checks on recorded exposure, probability alignment and evidence claims (stdlib)."""
import pathlib,json,gzip,math,unittest,csv
D=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
class Evidence(unittest.TestCase):
 def test_recorded_updates_match_original_teacher_schedule(self):
  schedule=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];plan=read(D/'PLAN.json')
  for arm in ['A','B']:
   done=[json.loads(l)for l in(D/'run'/arm/'updates.jsonl').read_text().splitlines()if json.loads(l)['event']=='completed'and json.loads(l)['phase']=='retained']
   self.assertEqual([r['step']for r in done],list(range(1,len(done)+1)))
   for r,batch in zip(done,schedule):
    targets=[t for w in batch for t in w['tokens'][1:]];z=r['trace'];self.assertEqual(z['targets'],len(targets));self.assertEqual(z['EOS_targets'],targets.count(2));self.assertEqual(z['role_targets'],targets.count(3)+targets.count(4))
    self.assertTrue(math.isfinite(z['loss']));self.assertTrue(math.isfinite(z['gradient_norm_before_clip']))
    step=r['step'];lr=plan['lr'];expected=lr['peak']*step/lr['warmup']if step<=lr['warmup']else lr['end']+(lr['peak']-lr['end'])*.5*(1+math.cos(math.pi*(step-lr['warmup'])/(plan['full_pass_updates']-lr['warmup'])))
    self.assertAlmostEqual(z['lr'],expected,places=14)
 def test_teacher_and_generated_histories_share_first_distribution(self):
  for p in(D/'probabilities').glob('*.json'):
   if p.name.endswith('-summary.json'):continue
   r=read(p);self.assertEqual(r['summary']['rescoring_argmax_disagreements'],0)
   for c in r['cases']:
    self.assertEqual([s['position0']for s in c['steps']],list(range(len(c['steps']))));z=c['steps'][0]
    self.assertAlmostEqual(z['p_gold_correct'],z['p_gold_self'],places=6)
    self.assertEqual(z['token'],z['correct_history_argmax'])
 def test_context_targets_are_aligned(self):
  protocol=read(D/'CONTEXT_ABLATION_PROTOCOL.json')
  for c in protocol['cases']:self.assertEqual(len(c['prefix']),len(c['wrong_prefix']));self.assertEqual(c['scored_target_positions'],list(range(1,64)))
  for p in(D/'context').glob('*.json'):
   r=read(p);self.assertEqual(r['summary']['paired_targets'],567)
   for row in r['rows']:
    for z in row['conditions'].values():self.assertEqual(z['target_count'],63);self.assertEqual(len(z['per_target_NLL']),63)
 def test_review_cannot_turn_eos_into_content_success(self):
  for model,r in read(D/'CAPABILITY_REVIEW.json').items():
   panel=read(D/'panels'/f'{model}.json');self.assertFalse(r['formal_human_evaluation']);self.assertEqual(len(r['cases']),95)
   for key,n in [('native24',24),('provided23',23),('grounded36',36),('context12',12)]:
    subset=[c for c in r['cases']if c['panel']==key];self.assertEqual(len(subset),n);self.assertEqual(sum(c['success']for c in subset),r['success'][key]);self.assertTrue(all(c['reason']for c in subset))
   self.assertEqual(sum(e['successful_episode']for e in r['self_history']),r['self_history_success'])
   self.assertEqual([e['actual_turns']for e in r['self_history']],[len(e['turns'])for e in panel['self_history']])
 def test_human_review_package_remains_unscored(self):
  p=D/'blind-review/worksheet.csv'
  if not p.exists():self.skipTest('terminal pair package not yet prepared')
  rows=list(csv.DictReader(p.open()));self.assertEqual(len(rows),90)
  for r in rows:self.assertTrue(all(v==''for k,v in r.items()if k!='sample_id'))
if __name__=='__main__':unittest.main()
