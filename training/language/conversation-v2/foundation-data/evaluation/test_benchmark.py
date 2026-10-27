"""Contract tests protect against benchmark leakage and fabricated golds."""
import copy,json,pathlib,sys,unittest
from benchmark_core import HERE,BASE,read,encode_history,prepare_cases,check_final_split,Encoder

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok=read(BASE/'data/tokenizer.json');cls.enc=Encoder(cls.tok)
    def test_complete_human_history_keeps_eos_and_body(self):
        texts=['明日は図書館です。','何時ですか？'];p=encode_history(texts,self.enc)
        self.assertEqual(p[0:2],[1,3]);self.assertEqual(p.count(2),2);self.assertEqual(p[-1],3)
        pieces=[bytes.fromhex(x)for x in self.tok['bytes']]
        self.assertEqual(b''.join(pieces[t]for t in p),''.join(texts).encode())
    def test_train_component_leak_cannot_be_hidden_by_dev_label(self):
        h={'cases':[{'family':'dev-a','component':'joint'}],'proseCases':[]}
        split={'articles':[{'family':'dev-a','component':'joint','split':'dev'},
                           {'family':'train-b','component':'joint','split':'train'}]}
        with self.assertRaisesRegex(ValueError,'leaked'):check_final_split(h,split)
    def test_changed_component_needs_rebuild_before_freeze(self):
        h={'cases':[{'family':'a','component':'old'}],'proseCases':[]}
        with self.assertRaisesRegex(ValueError,'changed'):check_final_split(h,{'articles':[{'family':'a','component':'new','split':'dev'}]})
    def test_generated_reference_cannot_enter_researcher_inputs(self):
        synthetic={'cases':[{'referenceAnswer':'作られた正解','humanReference':False,'trainingAllowed':False}]}
        with self.assertRaisesRegex(ValueError,'cannot become'):prepare_cases({'cases':[],'proseCases':[]},synthetic,self.tok)
    def test_context_overflow_is_reported_without_cropping(self):
        s={'cases':[dict(id='long',history=['あ'*500],referenceAnswer=None,humanReference=False,trainingAllowed=False)]}
        r=prepare_cases({'cases':[],'proseCases':[]},s,self.tok)[0]
        self.assertFalse(r['generationSupported']);self.assertGreater(len(r['prefixTokens'])+64,256)
        self.assertEqual(r['prefixTokens'],encode_history(s['cases'][0]['history'],self.enc))
    def test_bad_source_labels_are_quarantined_without_replacement(self):
        history=read(HERE/'selection-history.json');cases=read(HERE/'human-dev.json')['cases']
        qids={r['source']['questionId']for r in cases}
        self.assertEqual(history['initialSelectionCount'],34);self.assertEqual(len(cases),32)
        self.assertFalse(history['replacementsAdded']);self.assertEqual(set(history['removedQuestionIds']),{'tr-597-09-003','tr-247-20-001'})
        self.assertFalse(qids&set(history['removedQuestionIds']))
        bad=read(HERE/'quarantined-source-cases.json')['cases']
        by_id={r['questionId']:r for r in bad}
        self.assertEqual(by_id['tr-597-09-003']['originalHumanAnswers'][0]['text'],'1873年')
        self.assertIn('1870年',by_id['tr-597-09-003']['context'])

if __name__=='__main__':unittest.main()
