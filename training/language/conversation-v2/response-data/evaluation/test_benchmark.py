import copy
import unittest
from benchmark import validate_case, prepare


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.source = {'split':'DEV','dialogue_name':'unit-fixture',
                       'turns':[{'turn_id':0,'utterance':'試験用の項目は三つです。'}]}
        self.case = {'id':'unit-fixture-not-a-benchmark',
                     'source':{'split':'DEV','dialogue_id':'unit-fixture'},
                     'evidence':[{'kind':'utterance','turn_id':0,'start':7,'end':9,'quote':'三つ'}],
                     'required_content':[{'source_values':['三つ'],'evidence_indices':[0]}],
                     'gold_authorship':'no-generated-gold-verbatim-source-slots'}

    def test_exact_source_span_required(self):
        self.assertTrue(validate_case(self.case,self.source))
        self.case['evidence'][0]['quote']='五つ'
        with self.assertRaises(ValueError):validate_case(self.case,self.source)

    def test_unknown_dialogue_rejected(self):
        self.case['source']['dialogue_id']='other'
        with self.assertRaises(ValueError):validate_case(self.case,self.source)

    def test_train_is_not_dev(self):
        self.source['split']='TRAIN'
        with self.assertRaises(ValueError):validate_case(self.case,self.source)

    def test_ack_only_rubric_rejected(self):
        self.case['required_content']=[]
        with self.assertRaises(ValueError):validate_case(self.case,self.source)

    def test_no_generated_gold(self):
        self.case['gold_authorship']='model-generated'
        with self.assertRaises(ValueError):validate_case(self.case,self.source)


if __name__=='__main__':unittest.main()
