import unittest,json,pathlib,collections
from masks import make_pair,padded_pair,masked_ce
P=pathlib.Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_review_complete(self):
  r=json.loads((P/'REVIEW.json').read_text());self.assertEqual(len(r['cases']),216);self.assertTrue(all(x['full_history_and_reply_read']for x in r['cases']));self.assertFalse(r['formal_TRAIN_admission'])
 def test_no_held_payload(self):
  r=json.loads((P/'REVIEW.json').read_text());r['cases']+=json.loads((P/'SUPPLEMENT_REVIEW.json').read_text())['cases'];allowed={(x['partition'],x['id'])for x in r['cases']if x['decision']=='conditional_candidate'};p=json.loads((P/'CANDIDATE_SPANS.json').read_text());self.assertFalse(p['training_authorized'])
  self.assertEqual({(k,r['id'])for k,rr in p['parts'].items()for r in rr},allowed)
 def test_all_span_teacher_positions(self):
  p=json.loads((P/'CANDIDATE_SPANS.json').read_text())
  for rows in p['parts'].values():
   for r in rows:
    q=make_pair(r['tokens'],r['response_body_start']);self.assertEqual(q['teacher_ids'],r['tokens'][1:]);self.assertEqual(q['input_ids'],r['tokens'][:-1]);self.assertEqual(q['response_ce_mask'],r['response_ce_mask']);self.assertEqual(sum(q['response_ce_mask']),len(r['tokens'])-r['response_body_start']);self.assertTrue(q['response_ce_mask'][-1]);self.assertFalse(q['response_ce_mask'][r['response_body_start']-2])
 def test_original_roles_BOS_EOS(self):
  p=json.loads((P/'CANDIDATE_SPANS.json').read_text())
  for rows in p['parts'].values():
   for r in rows:self.assertEqual(r['tokens'][0],1);self.assertEqual(r['tokens'][-1],2);self.assertEqual(r['tokens'][r['response_body_start']-1],r['role']);self.assertIn(r['role'],[3,4]);self.assertLessEqual(len(r['tokens'])-1,256)
 def test_padding_never_teacher(self):
  x=padded_pair([1,3,40,2,4,41,42,2],5);self.assertEqual(x['input_ids'][:7],[1,3,40,2,4,41,42]);self.assertTrue(all(t==-100 for t in x['teacher_ids'][7:]));self.assertFalse(any(x['response_ce_mask'][7:]));self.assertFalse(any(x['attention_valid'][7:]))
 def test_reject_silent_truncation(self):
  self.assertEqual(len(make_pair([1,3]+[40]*254+[2],2)['input_ids']),256)
  with self.assertRaises(ValueError):make_pair([1,3]+[40]*255+[2],2)
 def test_zero_optimizer_gate_and_one_pass(self):
  s=json.loads((P/'PREPARATION_SCHEDULE.json').read_text());self.assertFalse(s['executable']);self.assertEqual(s['actual_updates'],0);v=[i for b in s['batches']for i in b];self.assertEqual(len(v),196);self.assertEqual(len(set(v)),196)
 def test_train_dev_independence(self):
  p=json.loads((P/'CANDIDATE_SPANS.json').read_text())['parts'];self.assertFalse({s for r in p['train']for s in r['speakers']}&{s for r in p['dev']for s in r['speakers']});self.assertFalse({r['family']for r in p['train']}&{r['family']for r in p['dev']})
 def test_supplement_fixed_and_read(self):
  a=json.loads((P/'SUPPLEMENT_SELECTION.json').read_text());b=json.loads((P/'SUPPLEMENT_REVIEW.json').read_text());self.assertEqual(len(a['selected']),64);self.assertEqual(len(b['cases']),64);self.assertEqual({r['id']for r in a['selected']},{r['id']for r in b['cases']});self.assertTrue(all(r['full_history_and_reply_read']for r in b['cases']));self.assertFalse(a['model_predictions_seen'])
 def test_source_and_total_counts(self):
  x=json.loads((P/'DATA_SUMMARY.json').read_text());self.assertFalse(x['training_go']);self.assertEqual(x['parts']['train']['response_tokens'],2730);self.assertEqual(x['parts']['train']['teacher_counts']['A_loss_teachers'],16396);self.assertEqual(x['parts']['train']['teacher_counts']['B_loss_teachers'],2926);self.assertEqual(x['optimizer_calls'],0);self.assertEqual(x['model_forwards'],0)
 def test_synthetic_gradient_mask_and_normalization(self):
  import torch
  torch.set_num_threads(2);g=torch.Generator().manual_seed(271828)
  x=padded_pair([1,3,40,2,4,41,42,2],5,width=10);y=torch.tensor([x['teacher_ids']]);a=torch.tensor([x['all_ce_mask']]);b=torch.tensor([x['response_ce_mask']]);logits=torch.randn(1,10,3997,generator=g,requires_grad=True)
  la=masked_ce(logits,y,a);self.assertTrue(torch.isfinite(la));la.backward();self.assertTrue(torch.isfinite(logits.grad).all());logits.grad=None
  lb=masked_ce(logits,y,b);expected=torch.nn.functional.cross_entropy(logits[b],y[b],reduction='mean');self.assertTrue(torch.equal(lb,expected));lb.backward();self.assertTrue(torch.isfinite(logits.grad).all());self.assertEqual(float(logits.grad[~b].abs().sum()),0.);self.assertGreater(float(logits.grad[b].abs().sum()),0.)
 def test_empty_response_batch_stops(self):
  import torch
  with self.assertRaises(ValueError):masked_ce(torch.zeros(1,2,3997),torch.tensor([[2,-100]]),torch.tensor([[False,False]]))
if __name__=='__main__':unittest.main()
