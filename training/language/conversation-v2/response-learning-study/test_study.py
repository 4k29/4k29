"""Light evidence checks. No model construction, training, or checkpoint mutation."""
import unittest,pathlib,json,hashlib,gzip,base64,collections
P=pathlib.Path(__file__).resolve().parent
read=lambda f:json.loads((P/f).read_text())
class Study(unittest.TestCase):
 def test_fixed_plan(self):
  self.assertEqual((P/'PLAN.sha256').read_text().split()[0],hashlib.sha256((P/'PLAN.json').read_bytes()).hexdigest())
  plan=read('PLAN.json')
  for rel in ['engine.py','PILOT_DATA.json','PROTOCOL.json']:
   h=next(v for k,v in plan['sha256'].items()if k.endswith('/response-learning-study/'+rel));self.assertEqual(h,hashlib.sha256((P/rel).read_bytes()).hexdigest())
 def test_immutable_prior_and_pilot(self):
  prior=P.parent/'response-ce-study';idx=json.loads((prior/'PACKED_INDEX.json').read_text());ref=next(x for x in idx['files']if x['name']=='CANDIDATE_SPANS.json');b=gzip.decompress(base64.b64decode((prior/ref['packed']).read_text()));self.assertEqual(hashlib.sha256(b).hexdigest(),ref['sha256']);old=json.loads(b);data=read('PILOT_DATA.json');by={r['id']:r for rs in old['parts'].values()for r in rs}
  self.assertEqual(len(old['parts']['train']),196)
  for r in data['pilot_train']+data['dev']:
   self.assertEqual(r['tokens'],by[r['id']]['tokens']);self.assertEqual(r['response_body_start'],by[r['id']]['response_body_start'])
  self.assertEqual(sorted(i for batch in data['batch_order']for i in batch),list(range(16)))
  self.assertEqual(sum(len(r['tokens'])-1 for r in data['pilot_train']),907)
  self.assertEqual(sum(len(r['tokens'])-r['response_body_start']-1 for r in data['pilot_train']),252)
 def test_additional_annotations(self):
  labels=read('ANNOTATIONS.json')['cases'];parts=read('ADDITIONAL_DATA.json')['parts']
  for part,n,good in [('train',118,66),('dev',10,6)]:
   rr=[r for r in labels if r['partition']==part];self.assertEqual(len(rr),n);approved={r['id']for r in rr if r['status']=='conditional_candidate'};self.assertEqual(len(approved),good);self.assertEqual(approved,{r['id']for r in parts[part]})
  self.assertEqual(read('DATA_SUMMARY.json')['combined']['total_response_body_tokens'],4590)
  audit=read('SOURCE_AUDIT.json')
  for name in ['train_dev_speaker_intersection','train_dev_family_intersection','train_dev_document_intersection','train_dev_exact_body_intersection']:self.assertEqual(audit[name],0)
 def test_grounded_DEV_not_human_questions(self):
  rows=read('GROUNDED_DEV.json')['rows'];self.assertEqual(len(rows),7)
  for r in rows:
   self.assertLessEqual(len(r['prefix'])+32,256);self.assertEqual(r['prefix'][:len(r['source_full_tokens'])],r['source_full_tokens']);self.assertFalse(r['answer_teacher_generated']);self.assertIn('main assistant',r['query_author']);self.assertTrue(r['required_facts'])
 def test_real_optimizer_ledger(self):
  result=read('RESULT.json');self.assertTrue(result['passed']);rows=[json.loads(l)for l in (P/'UPDATES.jsonl').read_text().splitlines()];ret=[r for r in rows if r['event']=='returned'];self.assertEqual(len(ret),14);self.assertEqual(collections.Counter(r['phase']for r in ret),{'pilot-retained':8,'preflight-original':4,'preflight-replay':2})
  for arm,teachers in [('A',907),('B',268)]:
   rr=[r for r in ret if r['phase']=='pilot-retained'and r['arm']==arm];self.assertEqual([r['trace']['step']for r in rr],[1,2,3,4]);self.assertEqual(sum(r['trace']['active_teachers']for r in rr),teachers);self.assertEqual(sum(r['trace']['input_tokens']for r in rr),907)
  pf=read('PREFLIGHT.json');self.assertTrue(pf['initial_forward_identical'])
  for a in pf['arms'].values():self.assertTrue(a['separate_process_full_state_resume_exact']);self.assertGreater(a['first_update_audit']['question_body_activation_gradient_L2'],0);self.assertEqual(a['first_update_audit']['masked_out_logit_gradient_abs_sum'],0)
 def test_cold_checkpoint_receipts(self):
  for arm in ['A','B']:
   for n in [2,4]:
    receipt=read(f'COLD-{arm}-{n}.json');meta=read(f'artifacts/{arm}-PILOT{n}/checkpoint.json');self.assertTrue(receipt['passed']);self.assertTrue(receipt['remote_only_no_alternates']);self.assertEqual(receipt['sha256'],meta['sha256']);self.assertEqual(meta['Adam_steps'],[6940+n])
 def test_raw_generations_and_forward_accounting(self):
  tok=json.loads((P.parent/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(t)for t in tok['bytes']]
  fs=[json.loads(l)for l in gzip.decompress((P/'FORWARDS.jsonl.gz').read_bytes()).decode().splitlines()];self.assertEqual(sum(r['event']=='returned'for r in fs),read('RESULT.json')['model_forward_returns'])
  for name in ['initial','A-pilot4','B-pilot4']:
   x=read(f'evaluation/{name}.json');self.assertTrue(x['raw_unmodified']);self.assertEqual(x['optimizer_calls'],0)
   for row in x['cases']:
    raw=b''.join(pieces[t]for t in row['tokensIncludingEos']if t>5)
    self.assertEqual(raw.hex(),row['rawBytesHex'])
if __name__=='__main__':unittest.main()
