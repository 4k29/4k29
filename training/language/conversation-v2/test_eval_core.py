"""Toy invariant tests only: no own checkpoints, optimizer or training."""
import unittest
import torch
from eval_core import aggregate,byte_payload,greedy,response_scores,window_scores
from evaluate import selfplay

PIECES=[b'']*6+[b'a',b'\xff',b'b',b'c']
class Toy(torch.nn.Module):
    def __init__(self,end_after=0,chosen=6):
        super().__init__();self.config={'context':256,'vocabulary':10};self.end_after=end_after;self.chosen=chosen
    def forward(self,x):
        out=torch.full((*x.shape,10),-5.)
        for i,row in enumerate(x):
            last=-1
            for j,t in enumerate(row.tolist()):
                if t in [3,4]:last=j
                chosen=2 if last>=0 and j-last>=self.end_after else self.chosen
                out[i,j,chosen]=5.
        return out
class Tests(unittest.TestCase):
    def test_strict_invalid_utf8_is_not_repaired(self):
        r=byte_payload([7],PIECES);self.assertIsNone(r['text']);self.assertEqual(r['rawBytesHex'],'ff');self.assertFalse(r['strictUtf8'])
    def test_role_and_eos_metric_not_body_bytes(self):
        r=window_scores(Toy(),[1,3,6,2],PIECES)['metrics']
        self.assertEqual(r['body']['tokens'],1);self.assertEqual(r['role']['tokens'],1);self.assertEqual(r['eos']['tokens'],1)
        self.assertEqual(r['body']['utf8Bytes'],1)
    def test_empty_termination_retained_not_hidden(self):
        r=greedy(Toy(0),[1,3],PIECES,max_new=8)
        self.assertEqual(r['tokensIncludingEos'],[2]);self.assertEqual(r['text'],'');self.assertTrue(r['eos'])
    def test_no_eos_limit_keeps_all_raw_tokens(self):
        r=greedy(Toy(1000,7),[1,3],PIECES,max_new=8)
        self.assertEqual(r['tokensIncludingEos'],[7]*8);self.assertFalse(r['eos']);self.assertIsNone(r['text'])
    def test_generation_never_uses_gold_to_select(self):
        a=greedy(Toy(2),[1,3],PIECES,[8,9],None,max_new=8)
        b=greedy(Toy(2),[1,3],PIECES,[6,6],None,max_new=8)
        self.assertEqual(a['tokensIncludingEos'],b['tokensIncludingEos'])
    def test_context_overflow_does_not_crop(self):
        with self.assertRaises(ValueError):greedy(Toy(),[1]+[6]*100,PIECES,max_new=192)
    def test_response_metrics_exclude_end_eos(self):
        logits,r=response_scores(Toy(2),[1,3],[6,6],PIECES)
        self.assertEqual(r['body']['tokens'],2);self.assertTrue(r['eosExcludedFromBodyNll']);self.assertEqual(r['eosAtGoldEnd']['token'],2)
    def test_selfplay_no_eos_does_not_advance(self):
        cases=[dict(id=str(i),document=str(i),prefixTokens=[1,3,6,2,4],targetLocalRoleToken=4,history=[],prefixText='a\n')for i in range(4)]
        out=selfplay(Toy(1000),cases,PIECES,{})
        self.assertTrue(all(len(e['rows'])==1 and e['completedTurns']==0 for e in out))
    def test_selfplay_uses_real_history_and_whole_turn_drop(self):
        source=[3]+[6]*14+[2]+[4]+[6]*14+[2]+[3]+[6]*13+[2]+[4]+[6]*13+[2]
        cases=[dict(id=str(i),document=str(i),prefixTokens=[1]+source+[3],targetLocalRoleToken=3,history=[],prefixText='a\n')for i in range(4)]
        out=selfplay(Toy(63),cases,PIECES,{})
        self.assertTrue(all(e['completedTurns']==3 for e in out))
        for e in out:
            self.assertEqual([r['localRoleToken']for r in e['rows']],[3,4,3])
            self.assertTrue(all(len(r['inputTokens'])+64<=256 for r in e['rows']))
            self.assertTrue(e['allDroppedWholeTurns'])
            self.assertTrue(all(t['tokens'][-1]==2 for t in e['allDroppedWholeTurns']))
if __name__=='__main__':unittest.main()
