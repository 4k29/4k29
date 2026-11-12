"""Standard-library/own-tokenizer tests only; no optimizer, model, or NC raw download."""
import unittest,pathlib,json,hashlib,gzip,base64,sys,os
from data_contract import object_spans,serialize,masks,start_reasons,pack_lists
P=pathlib.Path(__file__).resolve().parent
read=lambda f:json.loads((P/f).read_text())
class Study(unittest.TestCase):
 def test_object_boundaries_preserve_raw(self):
  s='[{"x":"brace } and escaped \\\" quote"},{"x":"日本語"}]';rows=list(object_spans(s));self.assertEqual(len(rows),2)
  for a,b,t in rows:self.assertEqual(s[a:b],t);json.loads(t)
 def test_invalid_escape_not_repaired(self):
  s='[{"x":"bad\\q"},{"x":"valid"}]';r=list(object_spans(s));self.assertEqual(len(r),2)
  with self.assertRaises(json.JSONDecodeError):json.loads(r[0][2])
  self.assertEqual(json.loads(r[1][2]),{'x':'valid'})
 def test_unterminated_refused(self):
  with self.assertRaises(ValueError):list(object_spans('[{"x":"unfinished'))
 def test_real_acquisition_pinned(self):
  m=read('ACQUISITION.json');self.assertEqual(len(m['files']),8)
  for f in m['files']:self.assertEqual(len(f['sha256']),64);self.assertTrue(f['revision'])
  self.assertFalse(m['original_provider_form_submitted']);self.assertFalse(m['personal_details_fabricated'])
 def test_metadata_no_raw_text_or_tokens(self):
  rows=read('CANDIDATE_METADATA.json');forbidden={'tokens','question','answer','text','output','history','utterances'}
  for r in rows:self.assertFalse(forbidden&set(r));self.assertFalse(r['training_authorized'])
 def test_question_family_disjoint(self):
  rows=read('CANDIDATE_METADATA.json');a={r['family']for r in rows if r['partition']=='train'};b={r['family']for r in rows if r['partition']=='dev'};self.assertFalse(a&b)
  by={}
  for r in rows:
   q=r['question_sha256']
   if q in by:self.assertEqual(by[q],r['partition'])
   by[q]=r['partition']
 def test_upstream_test_not_eligible(self):
  rows=read('CANDIDATE_METADATA.json');z=[r for r in rows if 'upstream_public_TEST_reference_not_train'in r['mechanical_holds']];self.assertEqual(len(z),117);self.assertTrue(all(not r['mechanically_eligible']for r in z))
 def test_reviewed_source_authorship_separate(self):
  review=read('REVIEW.json');self.assertEqual(len(review['cases']),107)
  self.assertEqual(review['summary']['ichikara:train']['conditional_quality_body_tokens'],1685);self.assertEqual(review['summary']['instruction_ja:train']['conditional_quality_body_tokens'],793)
  self.assertFalse(any(r['training_authorized']for r in review['cases']))
 def test_mask_shift_EOS_role(self):
  enc=lambda s:[6+ord(c)%200 for c in s];t,s=serialize(enc,'質問','回答');a,b=masks(t,s);self.assertEqual(len(a),len(t)-1);self.assertEqual(sum(b),3);self.assertTrue(a[s-2]);self.assertFalse(b[s-2]);self.assertTrue(b[s-1]);self.assertEqual(t[-1],2)
  with self.assertRaises(ValueError):serialize(enc,'a'*260,'b')
 def test_padding_and_no_cross_document_join(self):
  enc=lambda s:[6+ord(c)%200 for c in s];r=[serialize(enc,'q','short'),serialize(enc,'long question','a')];packed=pack_lists(r)
  for (t,start),z in zip(r,packed):
   n=z['valid'];self.assertEqual(z['x'][:n],t[:-1]);self.assertEqual(z['y'][:n],t[1:]);self.assertTrue(all(y==-100 for y in z['y'][n:]));self.assertFalse(any(z['response_mask'][n:]));self.assertEqual(sum(z['response_mask']),len(t)-start)
 def test_own_BPE_roundtrip(self):
  v=pathlib.Path(os.environ.get('CE_V2_ROOT',str(P.parent)));sys.path.insert(0,str(v));from new_tokenizer import Encoder
  tok=json.loads((v/'data/tokenizer.json').read_text());enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']]
  for text in ['質問と回答。\n\n別の段落。','文字境界🙂𠮷の検査']:
   self.assertEqual(b''.join(pieces[x]for x in enc(text)),text.encode())
 def test_NC_public_checkpoint_blocked(self):
  s=dict(rights_training_confirmed=True,source_revision_confirmed=True,source_original_distribution_confirmed=True,input_and_mask_fixed=True,DEV_fixed=True,durable_checkpoint_storage_confirmed=True,schedule_fixed=True,verified_train_response_body_tokens=10000,NC_data_used=True,private_model_storage_confirmed=False)
  self.assertIn('NC_model_publication_prohibited',start_reasons(s));s['private_model_storage_confirmed']=True;self.assertEqual(start_reasons(s),[])
 def test_current_gate_closed(self):
  p=read('PLAN.json');self.assertFalse(p['learning_authorized']);self.assertEqual(p['actual_optimizer_calls'],0);self.assertTrue(start_reasons(p['start_state']))
 def test_DEV_is_draft_not_independent_TEST(self):
  d=read('DEV_DESIGN.json');self.assertEqual(len(d['cases']),6);self.assertFalse(d['sealed_TEST_used']);self.assertFalse(d['coverage']['previous_conversation_turns']);self.assertFalse(d['independent_native_human_evaluation'])
if __name__=='__main__':unittest.main()
