import copy, unittest
from intake import intake,validate

def fixture():
    return {'schema_version':1,'consent_version':'response-consent-v1','submission_id':'SYNTHETIC-TEST-NOT-REAL',
      'participants':[{'id':x,'private_evidence_sha256':'a'*64,'withdrawal_terms_acknowledged':True,
        'owns_submitted_utterances':True,'dataset_license':'CC-BY-SA-4.0',
        'grants':{k:True for k in ['acquisition','storage','processing','model_training','public_redistribution']}} for x in ['a','b']],
      'review':{'status':'approved','reviewer':'SYNTHETIC-TEST','evidence_manually_checked':True},
      'messages':[{'id':'1','author':'a','parent_id':None,'text':'明日は雨ですか。','third_party_material_cleared':True},
                  {'id':'2','author':'b','parent_id':'1','text':'予報では雨なので傘が必要ですね。','third_party_material_cleared':True}]}
class Consent(unittest.TestCase):
    def test_zero_real_submissions(self):
        rows,r=intake([]);self.assertEqual(rows,[]);self.assertEqual(r['submissions_received'],0)
    def test_all_authors_must_consent(self):
        d=fixture();d['participants'].pop();self.assertIn('author-consent-missing',validate(d))
    def test_public_and_private_are_separate(self):
        d=fixture();d['participants'][0]['grants']['public_redistribution']=False
        self.assertEqual(validate(d),[]);self.assertIn('public-license-not-granted-by-every-author',validate(d,True))
    def test_missing_manual_proof_fails_closed(self):
        d=fixture();d['review']['evidence_manually_checked']=False
        self.assertIn('actual-consent-evidence-needs-manual-review',validate(d))
    def test_no_admission_from_consent_alone(self):
        rows,r=intake([fixture()],True);self.assertFalse(rows[0]['training_admitted']);self.assertEqual(r['training_admitted'],0)
    def test_broken_parent_and_contact_hold(self):
        d=fixture();d['messages'][1]['parent_id']='missing';d['messages'][1]['text']='contact@example.com'
        self.assertIn('missing-or-future-parent',validate(d));self.assertIn('contact-information-needs-private-review',validate(d))
    def test_duplicate_intake_not_extra_volume(self):
        rows,r=intake([fixture(),copy.deepcopy(fixture())]);self.assertEqual(len(rows),1)
if __name__=='__main__':unittest.main()
