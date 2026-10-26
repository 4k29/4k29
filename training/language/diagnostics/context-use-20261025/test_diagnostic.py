"""Toy-only tests: no own checkpoint loads, optimizers, updates or corpus reads."""
import unittest

import torch

from diagnostic_core import (aggregate, byte_payload, content_spans, fence,
    generated_history_probe, greedy, macro_and_token_weighted,
    repeated_ngram_onset, score_positions, teacher_forced)


class ToyCausal(torch.nn.Module):
    def __init__(self, eos=False):
        super().__init__(); self.config={'context':256}; self.eos=eos; self.calls=[]

    def forward(self,tokens):
        self.calls.append(tokens.tolist())
        batch,steps=tokens.shape
        logits=torch.zeros(batch,steps,16)
        chosen=torch.full_like(tokens,2) if self.eos else tokens.cumsum(-1)%8+6
        logits.scatter_(-1,chosen.unsqueeze(-1),4.)
        return logits


def pieces():
    return [b'']*6+[bytes([97+i]) for i in range(10)]


class DiagnosticContracts(unittest.TestCase):
    def test_gold_rank_probability_margin_ties(self):
        logits=torch.tensor([[2.,2.,0.],[0.,1.,3.]])
        rows=score_positions(logits,[1,2])
        self.assertEqual(rows[0]['goldRank'],2)
        self.assertFalse(rows[0]['goldIsTop1'])
        self.assertEqual(rows[0]['goldMinusBestOtherLogit'],0.)
        self.assertEqual(rows[1]['goldRank'],1)
        self.assertEqual(rows[1]['goldMinusBestOtherLogit'],2.)
        self.assertAlmostEqual(rows[1]['goldProbability'],float(torch.softmax(logits[1],0)[2]),places=7)
        self.assertAlmostEqual(rows[1]['nll'],-float(torch.log_softmax(logits[1],0)[2]),places=7)

    def test_tf_scores_first_gold_at_prefix_last_and_eos_separate(self):
        model=ToyCausal().eval(); logits,result=teacher_forced(model,[1],[7,8,9])
        self.assertEqual([r['top1Token'] for r in result['tokens']],[7,6,6])
        self.assertEqual(logits.shape,(3,16))
        self.assertEqual(result['tokens'][0]['goldToken'],7)
        self.assertTrue(result['eosAtGoldEnd']['excludedFromGoldTokenMetrics'])
        self.assertEqual(len(result['tokens']),3)

    def test_counterfactual_single_causal_forward_and_departure_regions(self):
        model=ToyCausal().eval(); prefix=[1];gold=[7,8,9,10]
        tf_logits,tf=teacher_forced(model,prefix,gold)
        generation=greedy(model,prefix,gold,tf_logits,pieces(),max_new=4)
        self.assertEqual(generation['nonEosTokens'],[7,6,12,8])
        self.assertEqual(generation['firstGoldDeparturePosition'],1)
        before=len(model.calls)
        probe=generated_history_probe(model,prefix,gold,generation,tf['tokens'])
        self.assertEqual(len(model.calls)-before,1)
        self.assertEqual(model.calls[-1],[[1,7,6,12]])
        self.assertEqual(probe['K'],4)
        self.assertEqual([r['region'] for r in probe['rows']],['before-departure','at-departure','after-departure','after-departure'])
        self.assertEqual(probe['rows'][1]['nllDifferenceFromTeacherForced'],0.)
        self.assertNotEqual(probe['rows'][2]['top1Token'],probe['rows'][2]['teacherForced']['top1Token'])
        self.assertEqual(generation['numericalReference']['comparedPositions'],2)
        self.assertEqual(generation['numericalReference']['argmaxDisagreements'],0)

    def test_immediate_eos_probe_never_feeds_eos(self):
        model=ToyCausal(eos=True).eval();prefix=[1];gold=[7,8,9]
        tf_logits,tf=teacher_forced(model,prefix,gold)
        generation=greedy(model,prefix,gold,tf_logits,pieces(),max_new=4)
        self.assertEqual(generation['tokensIncludingEos'],[2])
        self.assertEqual(generation['nonEosTokens'],[])
        before=len(model.calls)
        probe=generated_history_probe(model,prefix,gold,generation,tf['tokens'])
        self.assertEqual(probe['K'],1)
        self.assertEqual(model.calls[-1],[[1]])
        self.assertEqual(len(model.calls)-before,1)
        self.assertEqual(probe['fedGeneratedTokenCount'],0)

    def test_no_eos_cap_does_not_probe_unavailable_next_position(self):
        model=ToyCausal().eval();gold=[7]*8
        logits,tf=teacher_forced(model,[1],gold)
        generation=greedy(model,[1],gold,logits,pieces(),max_new=3)
        probe=generated_history_probe(model,[1],gold,generation,tf['tokens'])
        self.assertEqual(probe['K'],3)
        self.assertEqual(probe['fedGeneratedTokenCount'],2)

    def test_no_context_rolling_or_overflow(self):
        model=ToyCausal().eval();gold=[7]
        with self.assertRaises(ValueError): teacher_forced(model,[1]*256,gold)
        logits,_=teacher_forced(model,[1],gold)
        with self.assertRaises(ValueError):greedy(model,[1]*65,gold,logits,pieces())
        with self.assertRaises(ValueError):greedy(model,[1],gold,logits,pieces(),max_new=256)

    def test_strict_utf8_preserves_invalid_original_bytes(self):
        p=[b'']*6+[b'\xe3',b'\x81\x82']
        bad=byte_payload([6],p)
        self.assertEqual(bad['rawBytesHex'],'e3');self.assertFalse(bad['strictUtf8']);self.assertIsNone(bad['text'])
        good=byte_payload([6,7],p)
        self.assertTrue(good['strictUtf8']);self.assertEqual(good['text'],'あ')

    def test_content_span_byte_alignment_not_character_heuristics(self):
        p=[b'']*6+['あ'.encode()[:1],'あ'.encode()[1:],b'b']
        tf=score_positions(torch.zeros(3,9),[6,7,8])
        spans=content_spans('あb',[6,7,8],p,[{'text':'あ','startCharacter':0,'endCharacter':1}],tf)
        self.assertTrue(spans[0]['fullyTokenAligned'])
        self.assertEqual(spans[0]['touchedTokenPositions'],[0,1])
        self.assertEqual(spans[0]['endUtf8Byte'],3)
        merged=[b'']*6+['あb'.encode()]
        tf2=score_positions(torch.zeros(1,7),[6])
        span2=content_spans('あb',[6],merged,[{'text':'あ','startCharacter':0,'endCharacter':1}],tf2)[0]
        self.assertFalse(span2['fullyTokenAligned'])
        self.assertIsNone(span2['wholeSpanTeacherTop1Exact'])
        self.assertEqual(span2['fullyContainedTokenPositions'],[])

    def test_macro_and_token_weighted_are_distinct(self):
        rows=score_positions(torch.zeros(4,3),[0,1,1,1])
        summary=macro_and_token_weighted([rows[:1],rows[1:]])
        self.assertEqual(summary['equalCaseMacro']['top1Rate'],.5)
        self.assertEqual(summary['tokenWeighted']['top1Rate'],.25)

    def test_repeat_onset_reports_completion_and_not_semantics(self):
        report=repeated_ngram_onset([6,7,8,9,6,7,8,9],4)
        self.assertEqual(report['repeatedStartPosition'],4)
        self.assertEqual(report['repeatCompletionPosition'],7)
        self.assertIn('not semantic',report['interpretation'])

    def test_markdown_fence_cannot_be_closed_by_raw_generation(self):
        result=fence('text\n```\n<script>raw</script>\n````')
        self.assertTrue(result.startswith('`````text\n'))
        self.assertTrue(result.endswith('\n`````'))

    def test_inference_keeps_rng_and_eval_mode(self):
        model=ToyCausal().eval();before=torch.get_rng_state().clone()
        logits,tf=teacher_forced(model,[1],[7,8])
        generation=greedy(model,[1],[7,8],logits,pieces(),max_new=4)
        generated_history_probe(model,[1],[7,8],generation,tf['tokens'])
        self.assertFalse(model.training)
        self.assertTrue(torch.equal(before,torch.get_rng_state()))

    def test_all_primary_and_auxiliary_context_lengths_must_match(self):
        from run_diagnostic import validate_cases
        def case(index):
            return {'id':str(index),'targetText':'a','goldTokens':[6], 'contentSpans':[],
                    'conditions':{'correct':{'prefixText':'a','prefixTokens':[1,6]},
                                  'mismatched':{'prefixText':'b','prefixTokens':[1,7]},
                                  'none':{'prefixText':'','prefixTokens':[1]}}}
        panel={'cases':[case(i) for i in range(25)],
               'auxiliaryTfOnly':[case(i) for i in range(25,1049)]}
        validate_cases(panel,pieces(),256)
        for cohort,index in [('cases',0),('auxiliaryTfOnly',1023)]:
            condition=panel[cohort][index]['conditions']['mismatched']
            condition['prefixTokens']=[1,7,7];condition['prefixText']='bb'
            with self.assertRaisesRegex(ValueError,'exactly equal token lengths'):
                validate_cases(panel,pieces(),256)
            condition['prefixTokens']=[1,7];condition['prefixText']='b'


if __name__=='__main__':unittest.main()
