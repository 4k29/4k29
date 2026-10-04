"""Train-only semantic heads cannot observe teacher-forced future answers."""
import unittest
import torch
from train import DialogueDecoder,generate

class SemanticTrainingTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1);torch.manual_seed(429)
        self.model=DialogueDecoder(dict(vocabulary=33,dim=16,heads=4,hidden=32,layers=2,context=20,dropout=0.0,epsilon=1e-5,semanticTasks=dict(subject=['device','owner'],attribute=['weight','name','unknown'])))
        self.model.eval()
    def test_heads_are_causal_at_question_boundary(self):
        left=torch.tensor([[1,3,12,13,4,16,17,18]])
        right=torch.tensor([[1,3,12,13,4,21,22,23]])
        position=torch.tensor([4])
        _,a=self.model(left,semantic_positions=position)
        _,b=self.model(right,semantic_positions=position)
        for name in a:torch.testing.assert_close(a[name],b[name],rtol=0,atol=0)
    def test_semantic_weights_do_not_choose_language_output(self):
        tokens=torch.tensor([[1,3,12,13,4]])
        original=self.model(tokens)
        with torch.no_grad():
            for head in self.model.semantic.values():head.weight.fill_(1000);head.bias.fill_(-1000)
        torch.testing.assert_close(original,self.model(tokens),rtol=0,atol=0)
    def test_auxiliary_loss_updates_shared_question_representation(self):
        tokens=torch.tensor([[1,3,12,13,4]])
        _,heads=self.model(tokens,semantic_positions=torch.tensor([4]))
        loss=sum(torch.nn.functional.cross_entropy(head,torch.tensor([0])) for head in heads.values())
        loss.backward()
        self.assertGreater(self.model.token.weight.grad.abs().sum().item(),0)
        self.assertGreater(self.model.blocks[0].qkv.weight.grad.abs().sum().item(),0)
    def test_ragged_generation_never_emits_past_each_rows_context_budget(self):
        class NeverEnds(torch.nn.Module):
            config={'context':8}
            def forward(self,tokens):
                logits=torch.zeros((*tokens.shape,262));logits[:,:,71]=1;return logits
        tokenizer=dict(bytes=['']*6+[bytes([i]).hex() for i in range(256)])
        rows=[dict(id=str(n),kind='test',question='test',history=[],answer='unused',prefixLength=n,tokens=[1]+[3]*(n-2)+[4,71,2]) for n in [3,7]]
        result=generate(NeverEnds(),rows,tokenizer)
        self.assertEqual([r['answer'] for r in result],['A'*5,'A'])
        self.assertTrue(all(not r['eos'] for r in result))

if __name__=='__main__':unittest.main()
